import sys

import aiohttp
import asyncio
import contextlib
from typing import Optional, List, Dict, Any, Callable
import inspect 

import data_formatter
from world_cup_dashboard import WorldCupDashboard
import drawing
import pygame

import os


def resource_path(relative_path: str) -> str:
    """Absolute path to a bundled asset (dev, script, or PyInstaller exe)."""
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


async def main() -> None:
    """Main entry point"""
    pygame.init()


    pygame.mixer.init()
    pygame.mixer.music.set_volume(0.5)
    pygame.display.set_caption("World Cup Dashboard")

    logo = pygame.image.load(resource_path( "icon.ico"))
    pygame.display.set_icon(logo)


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
            pygame.mixer.music.load(resource_path(os.path.join("sounds", "info.mp3")))
            pygame.mixer.music.play()
        if event_type == "game_score_changed":
            print(f"Score changed for {game_name}: {data}")
            pygame.mixer.music.load(resource_path(os.path.join("sounds", "goooooaall.mp3")))
            pygame.mixer.music.play()
        elif event_type == "game_status_changed":
            print(f"Status changed for {game_name}: {data}")
            pygame.mixer.music.load(resource_path(os.path.join("sounds", "referee-whistle.mp3")))
            pygame.mixer.music.play()


    async def load_handler(data: List[Dict[str, Any]]) -> None:
        """Handler for when games are loaded"""
        sidebar_width = 300
        board_width = screen.get_width() - sidebar_width
        layout = drawing.compute_game_layout(
            screen.get_width(),
            screen.get_height(),
            sidebar_width,
            len(data),
        )

        screen.fill((0, 0, 0))
        drawing.draw_pitch(screen, board_width=board_width)

        for game, (x, y, card_size) in zip(data, layout):
            drawing.draw_match_data(screen, game, position=(x, y), card_size=card_size)

        drawing.draw_sidebar(
            screen,
            dashboard.event_feed,
            position=(screen.get_width() - sidebar_width, 0),
            size=(sidebar_width, screen.get_height()),
        )
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
