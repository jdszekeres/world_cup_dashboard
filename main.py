import aiohttp
import asyncio
import contextlib
from typing import Optional, List, Dict, Any, Callable
import inspect 

import data_formatter
from world_cup_dashboard import WorldCupDashboard
import drawing
import pygame






async def main() -> None:
    """Main entry point"""
    pygame.init()

    screen = pygame.display.set_mode((1110, 740))

    

    drawing.draw_match_data(screen, {})

    async def status_handler(event: Dict[str, Any]) -> None:
        """Default event handler"""
        event_type = event.get("type")
        game = event.get("game", {})
        data = event.get("data")
        
        game_name = game.get("name", "Unknown")
        game_id = game.get("id")
        games = dashboard.get_current_games() or []

        if game_id:
            dashboard.cache_game_annotation(game_id, event_type, data)
            games = [game if current_game.get("id") == game_id else current_game for current_game in games]
            dashboard.games = games

        dashboard.add_feed_event(game, event_type, data)

        await load_handler(games)  # Refresh the display on any event for simplicity
        
        if event_type == "game_detail_updated":
            print(f"Detail updated for {game_name}: {data}")
        elif event_type == "game_status_changed":
            print(f"Status changed for {game_name}: {data}")


    async def load_handler(data: List[Dict[str, Any]]) -> None:
        """Handler for when games are loaded"""
        game_count = len(data)
        # Fixed card size with wrapping: cards are 200x200, calculate how many fit per row, but center them
        card_width, card_height = 200, 200
        sidebar_width = 300
        board_width = max(card_width + 20, screen.get_width() - sidebar_width - 20)
        cards_per_row = max(1, board_width // (card_width + 20))
        offset_x = (board_width - (cards_per_row * (card_width + 20) - 20)) // 2

        screen.fill((0, 0, 0))
        drawing.draw_pitch(screen)

        
        for i, game in enumerate(data):
            row = i // cards_per_row
            col = i % cards_per_row
            x = col * (card_width + 20) + offset_x
            y = row * (card_height + 20) + 10
            drawing.draw_match_data(screen, game, position=(x, y))

        drawing.draw_sidebar(screen, dashboard.event_feed, position=(screen.get_width() - sidebar_width, 0), size=(sidebar_width, screen.get_height()))
        pygame.display.flip()

    dashboard = WorldCupDashboard()
    dashboard.on_games_loaded(load_handler)
    dashboard.on_game_change(status_handler)

    
    try:
        await dashboard.start(poll_interval=1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        await dashboard.stop()


if __name__ == "__main__":
    asyncio.run(main())
