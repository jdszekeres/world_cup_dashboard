import sys

import pygame
import io
import requests
import data_formatter

CARD_GAP = 20
BOARD_PADDING = 10
MAX_CARD_SIZE = 200
MIN_CARD_SIZE = 110


def compute_game_layout(screen_width, screen_height, sidebar_width, game_count):
    """Compute wrapped card positions that fit in the board area."""
    if game_count <= 0:
        return []

    board_width = screen_width - sidebar_width - BOARD_PADDING
    board_height = screen_height - BOARD_PADDING
    max_cols = max(1, (board_width + CARD_GAP) // (MIN_CARD_SIZE + CARD_GAP))

    best_layout = None
    for cols in range(min(game_count, max_cols), 0, -1):
        rows = (game_count + cols - 1) // cols
        card_width = (board_width - (cols - 1) * CARD_GAP) // cols
        card_height = (board_height - (rows - 1) * CARD_GAP) // rows
        card_size = min(card_width, card_height, MAX_CARD_SIZE)
        if card_size >= MIN_CARD_SIZE:
            best_layout = (cols, rows, card_size)
            break

    if best_layout is None:
        cols = max(1, board_width // (MIN_CARD_SIZE + CARD_GAP))
        rows = (game_count + cols - 1) // cols
        card_width = (board_width - (cols - 1) * CARD_GAP) // cols
        card_height = (board_height - (rows - 1) * CARD_GAP) // rows
        card_size = max(90, min(card_width, card_height))
        best_layout = (cols, rows, card_size)

    cols, rows, card_size = best_layout
    grid_width = cols * card_size + (cols - 1) * CARD_GAP
    grid_height = rows * card_size + (rows - 1) * CARD_GAP
    offset_x = BOARD_PADDING + max(0, (board_width - grid_width) // 2)
    offset_y = BOARD_PADDING + max(0, (board_height - grid_height) // 2)

    positions = []
    for index in range(game_count):
        row = index // cols
        col = index % cols
        x = offset_x + col * (card_size + CARD_GAP)
        y = offset_y + row * (card_size + CARD_GAP)
        positions.append((x, y, card_size))
    return positions


def draw_match_data(screen, game, position=(10, 10), card_size=200):
    """Draw match data on the screen"""
    data = data_formatter.DataFormatter(game)
    logo1, logo2 = data.get_country_logo(game)
    name1, name2 = data.get_country_name(game)
    score1, score2 = data.get_score(game)
    time = data.get_time(game)
    card_width = card_height = card_size
    scale = card_size / MAX_CARD_SIZE

    pygame.draw.rect(screen, (0, 160, 0), pygame.Rect(position[0], position[1], card_width, card_height))

    if not name1 and not name2:
        return

    name1 = name1 or "TBD"
    name2 = name2 or "TBD"
    score1 = "-" if score1 is None else str(score1)
    score2 = "-" if score2 is None else str(score2)
    time = time or data.get_status(game) or ""

    margin = max(6, int(10 * scale))
    logo_y = position[1] + margin + int(10 * scale)
    logo_size = max(40, int(90 * scale))
    score_y = position[1] + card_height - margin - int(24 * scale)

    _draw_text(
        screen,
        name1,
        (position[0] + margin, position[1] + margin),
        (255, 255, 255),
        font_size=max(16, int(24 * scale)),
    )
    _draw_text(
        screen,
        name2,
        (position[0] + card_width - margin, position[1] + margin),
        (255, 255, 255),
        right_align=True,
        font_size=max(16, int(24 * scale)),
    )
    if logo1:
        _draw_logo(screen, logo1, (position[0] + margin, logo_y), size=(logo_size, logo_size))
    if logo2:
        _draw_logo(
            screen,
            logo2,
            (position[0] + card_width - margin, logo_y),
            size=(logo_size, logo_size),
            right_align=True,
        )
    _draw_text(
        screen,
        score1,
        (position[0] + margin + int(40 * scale), score_y),
        (255, 255, 255),
        font_size=max(16, int(24 * scale)),
    )
    _draw_text(
        screen,
        score2,
        (position[0] + card_width - margin - int(40 * scale), score_y),
        (255, 255, 255),
        right_align=True,
        font_size=max(16, int(24 * scale)),
    )
    if time:
        _draw_text(
            screen,
            time,
            (position[0] + len(time) * (20/6) +  card_width // 2, score_y),
            (255, 255, 255),
            right_align=True,
            font_size=max(16, int(24 * scale)),
        )

def draw_event_data(screen, event, position=(10, 10)):
    print(f"Drawing event data: {event}")
    size = (200, 100)
    pygame.draw.rect(screen, (0, 160, 0), pygame.Rect(position[0], position[1], size[0], size[1]))
    data = data_formatter.DataFormatter(event)
    details = data.get_event_details(event)
    if not details:
        return
    
    _draw_text(screen, details["name"], (position[0] + 10, position[1] + 10), (255, 255, 255))
    _draw_text(screen, details["athletes"], (position[0] + 10, position[1] + 40), (255, 255, 255))
    if details["is_scoring_play"]:
        ## draw a white border around the card if it's a scoring play
        pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(position[0], position[1], size[0], size[1]), 3)

def draw_status_change(screen, status, position=(10, 10)):
    print(f"Drawing status change: {status}")
    size = (200, 50)
    data = data_formatter.DataFormatter({})
    status_text = data.get_status_change_text(status)
    pygame.draw.rect(screen, (0, 160, 0), pygame.Rect(position[0], position[1], size[0], size[1]))
    _draw_text(screen, status_text, (position[0] + 10, position[1] + 10), (255, 255, 255))

def draw_sidebar(screen, events, position=(0, 0), size=(300, 740)):
    """Draw a sidebar with recent updates."""
    panel_rect = pygame.Rect(position[0], position[1], size[0], size[1])
    pygame.draw.rect(screen, (0, 160, 0), panel_rect)
    # pygame.draw.rect(screen, (90, 90, 90), panel_rect, 2)

    header_font = pygame.font.SysFont(None, 30)
    body_font = pygame.font.SysFont(None, 22)
    small_font = pygame.font.SysFont(None, 18)

    header = header_font.render("Recent Updates", True, (255, 255, 255))
    screen.blit(header, (position[0] + 14, position[1] + 14))

    # if not events:
    #     empty = body_font.render("No updates yet.", True, (200, 200, 200))
    #     screen.blit(empty, (position[0] + 14, position[1] + 54))
    #     return

    y = position[1] + 14
    max_width = size[0] - 28

    for event in events:
        block_height = 48
        block_rect = pygame.Rect(position[0] + 10, y, size[0] - 20, block_height)
        pygame.draw.rect(screen, (35, 35, 35), block_rect, border_radius=8)
        pygame.draw.rect(screen, (70, 70, 70), block_rect, 1, border_radius=8)

        game_name = event.get("game_name", "Unknown")
        event_type = event.get("type", "")
        data = event.get("data")

        title = _fit_text(body_font, f"{game_name}", max_width)
        subtitle_text = _sidebar_event_summary(event_type, data)
        subtitle = _fit_text(small_font, subtitle_text, max_width)

        title_surface = body_font.render(title, True, (255, 255, 255))
        subtitle_surface = body_font.render(subtitle, True, (200, 220, 200))

        screen.blit(title_surface, (position[0] + 18, y + 10))
        # screen.blit(type_surface, (position[0] + 18, y + 36))
        screen.blit(subtitle_surface, (position[0] + 18, y + 25))

        y += block_height + 10
        if y + block_height > position[1] + size[1]:
            break

def _draw_text(screen, text, position, color=(255, 255, 255), right_align=False, font_size=24):
    """Helper function to draw text on the screen"""
    font = pygame.font.SysFont(None, font_size)
    text_surface = font.render(text, True, color)
    if right_align:
        position = (position[0] - text_surface.get_width(), position[1])
    screen.blit(text_surface, position)

def _draw_logo(screen, logo_url, position, size=(80, 80), right_align=False):
    """Helper function to draw a logo on the screen"""
    if not logo_url:
        return
    try:
        response = requests.get(logo_url, timeout=5)
        image_bytes = io.BytesIO(response.content)
        logo_image = pygame.image.load(image_bytes)
        logo_image = pygame.transform.scale(logo_image, size)
        if right_align:
            position = (position[0] - logo_image.get_width(), position[1])
        screen.blit(logo_image, position)
    except Exception as e:
        print(f"Error loading logo from {logo_url}: {e}")
    pass


def _sidebar_event_summary(event_type, data):
    if event_type == "game_status_changed":
        return f"{data}"
    if event_type == "game_score_changed":
        if isinstance(data, tuple) and len(data) == 2:
            return f"Goal update: {data[0]} - {data[1]}"
        return f"Goal update: {data}"
    if event_type == "game_detail_updated":
        if isinstance(data, dict):
            name = data.get("name", "Update")
            athletes = data.get("athletes", "")
            if athletes:
                return f"{name}: {athletes}"
            return name
        return str(data)
    return str(data)


def _fit_text(font, text, max_width):
    if font.size(text)[0] <= max_width:
        return text

    ellipsis = "..."
    while text and font.size(text + ellipsis)[0] > max_width:
        text = text[:-1]
    return text + ellipsis if text else ellipsis


def load_sharp_scaled_svg(filename, scale_factor):
    # Read the raw SVG text
    with open(filename, "rt") as f:
        svg_string = f.read()
        
    # Inject a scale matrix into the SVG tag
    start = svg_string.find('<svg')
    if start >= 0:
        insertion = f' transform="scale({scale_factor})"'
        svg_string = svg_string[:start+4] + insertion + svg_string[start+4:]
        
    # Load the modified string via bytes
    return pygame.image.load(io.BytesIO(svg_string.encode()))


def draw_pitch(screen, board_width=None):
    board_width = board_width or screen.get_width()
    main_mod = sys.modules.get("main") or sys.modules["__main__"]
    football_pitch = load_sharp_scaled_svg(main_mod.resource_path("Football_field.svg"), 10)
    football_pitch = pygame.transform.rotate(football_pitch, 90)
    football_pitch = pygame.transform.scale(
        football_pitch,
        (board_width, screen.get_height()),
    )

    screen.blit(football_pitch, (0, 0))