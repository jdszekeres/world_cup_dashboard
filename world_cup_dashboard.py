import aiohttp
import asyncio
import contextlib
from typing import Optional, List, Dict, Any, Callable
import inspect 
import pygame


class WorldCupDashboard:
    def __init__(self):
        self.games: Optional[List[Dict[str, Any]]] = None
        self.game_annotations: Dict[str, Dict[str, Any]] = {}
        self.event_feed: List[Dict[str, Any]] = []
        self.last_announced_status: Dict[str, str] = {}
        self.status_listeners: List[Callable] = []
        self.games_loaded_listeners: List[Callable] = []
        self.loaded = False
        self.running = False
    
    def on_game_change(self, callback: Callable) -> None:
        """Register a callback for game changes"""
        self.status_listeners.append(callback)

    def on_games_loaded(self, callback: Callable) -> None:
        """Register a callback for when games are loaded"""
        self.games_loaded_listeners.append(callback)  

    def get_current_games(self) -> Optional[List[Dict[str, Any]]]:
        """Get the current list of games"""
        return self.games  

    def cache_game_annotation(self, game_id: str, annotation_type: str, data: Any) -> None:
        """Cache the latest visual annotation for a game."""
        if not game_id:
            return

        annotation = self.game_annotations.setdefault(game_id, {})
        annotation[annotation_type] = data

    def get_game_annotation(self, game_id: str) -> Dict[str, Any]:
        """Get cached annotations for a game."""
        if not game_id:
            return {}

        return self.game_annotations.get(game_id, {})

    def add_feed_event(self, game: Dict[str, Any], event_type: str, data: Any) -> None:
        """Store the latest update for the sidebar feed."""
        game_id = game.get("id", "")
        game_name = self._format_display_name(game.get("name", "Unknown"))

        if event_type == "game_status_changed":
            status_text = self._format_status_label(data)
            if game_id and self.last_announced_status.get(game_id) == status_text:
                return
            if game_id:
                self.last_announced_status[game_id] = status_text
            data = status_text

        entry = {
            "game_name": game_name,
            "type": event_type,
            "data": data,
        }
        self.event_feed.insert(0, entry)
        self.event_feed = self.event_feed[:6]

    def _format_display_name(self, text: str) -> str:
        """Format a display name for the sidebar."""
        if not text:
            return "Unknown"
        return text.replace("_", " ").title()

    def _format_status_label(self, text: Any) -> str:
        """Normalize ESPN status labels for display."""
        if text is None:
            return ""
        status_text = str(text).replace("STATUS_", "").replace("_", " ").strip()
        return status_text.title()
    
    async def _fetch_scoreboard(self) -> List[Dict[str, Any]]:
        """Fetch current scoreboard from API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    scoreboard = await resp.json()
                    return scoreboard.get("events", [])
        except Exception as e:
            print(f"Error fetching scoreboard: {e}")
            return []
        
    
    async def _emit_event(self, event_type: str, game: Dict[str, Any], data: Any) -> None:
        """Emit event to all listeners"""
        for listener in self.status_listeners:
            try:
                if inspect.iscoroutinefunction(listener):
                    await listener({"type": event_type, "game": game, "data": data})
                else:
                    listener({"type": event_type, "game": game, "data": data})
            except Exception as e:
                print(f"Error in listener: {e}")
                
    
    async def _check_changes(self, games_new: List[Dict[str, Any]]) -> None:
        """Detect and emit changes"""
        if self.games is None:
            self.games = games_new
            return
        
        for game in games_new:
            game_id = game.get("id")
            old_game = next((g for g in self.games if g.get("id") == game_id), None)
            
            if old_game is None:
                # New game
                await self._emit_event("game_added", game, None)
                continue
            
            # Check details
            new_details = game.get("details", [])
            old_details = old_game.get("details", [])
            if new_details != old_details:
                new_items = [d for d in new_details if d not in old_details]
                for detail in new_items:
                    await self._emit_event("game_detail_updated", game, detail)
            
            # Check status
            new_status = game.get("status", {}).get("type", {}).get("name", "")
            old_status = old_game.get("status", {}).get("type", {}).get("name", "")
            if new_status != old_status:
                await self._emit_event("game_status_changed", game, new_status)

            # Check scores so goal updates redraw immediately.
            new_scores = self._get_scores(game)
            old_scores = self._get_scores(old_game)
            if new_scores != old_scores:
                await self._emit_event("game_score_changed", game, new_scores)
        
        self.games = games_new

    def _get_scores(self, game: Dict[str, Any]) -> tuple[str, str]:
        """Extract the current competitor scores from a game."""
        try:
            competitors = game.get("competitions", [])[0].get("competitors", [])
            if len(competitors) >= 2:
                return competitors[0].get("score", ""), competitors[1].get("score", "")
        except Exception:
            pass
        return "", ""

    async def _pump_pygame_events(self) -> None:
        """Keep the window responsive while polling in the background."""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
            await asyncio.sleep(0.05)
    
    async def start(self, poll_interval: int = 10) -> None:
        """Start polling for updates"""
        self.running = True
        print(f"Dashboard started, polling every {poll_interval}s...")
        event_task = asyncio.create_task(self._pump_pygame_events())
        
        try:
            while self.running:
                games_new = await self._fetch_scoreboard()
                if games_new:
                    if not self.loaded:
                        self.loaded = True
                        for listener in self.games_loaded_listeners:
                            try:
                                if inspect.iscoroutinefunction(listener):
                                    await listener(games_new)
                                else:
                                    listener(games_new)
                            except Exception as e:
                                print(f"Error in games loaded listener: {e}")
                    await self._check_changes(games_new)
                await asyncio.sleep(poll_interval)
        except Exception as e:
            print(f"Error in dashboard: {e}")
        finally:
            self.running = False
            event_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await event_task
    
    async def stop(self) -> None:
        """Stop polling"""
        self.running = False
        print("Dashboard stopped")
