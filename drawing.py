import pygame
import io
import requests
import data_formatter

def draw_match_data(screen, game, position=(10, 10)):
    """Draw match data on the screen"""
    data = data_formatter.DataFormatter(game)
    logo1, logo2 = data.get_country_logo(game)
    name1, name2 = data.get_country_name(game)
    score1, score2 = data.get_score(game)
    time = data.get_time(game)
    card_width, card_height = 200, 200

    pygame.draw.rect(screen, (0, 160, 0), pygame.Rect(position[0], position[1], card_width, card_height))

    logo_y = position[1] + 20

    if not name1 or not logo1 or not score1 or not time:
        return
        
   
    _draw_text(screen, name1, (position[0] + 10, position[1] + 10), (255, 255, 255))
    _draw_text(screen, name2, (position[0] + card_width - 10, position[1] + 10), (255, 255, 255), right_align=True)
    _draw_logo(screen, logo1, (position[0] + 10, logo_y), size=(90, 90))
    _draw_logo(screen, logo2, (position[0] + card_width - 10, logo_y), size=(90, 90), right_align=True)
    _draw_text(screen, score1, (position[0] + 10 + 40, position[1] + 150), (255, 255, 255))
    _draw_text(screen, score2, (position[0] + card_width - 10 - 40, position[1] + 150), (255, 255, 255), right_align=True)
    _draw_text(screen, time, (position[0] + card_width // 2 + (len(time) // 2 * 10), position[1] + 150), (255, 255, 255), right_align=True)

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

def _draw_text(screen, text, position, color=(255, 255, 255), right_align=False):
    """Helper function to draw text on the screen"""
    font = pygame.font.SysFont(None, 24)
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


def draw_pitch(screen):
    football_pitch = load_sharp_scaled_svg("football_field.svg", 10)
    football_pitch = pygame.transform.rotate(football_pitch, 90)
    football_pitch = pygame.transform.scale(football_pitch, (screen.get_width(), screen.get_height()))
    
    screen.blit(football_pitch, (0, 0))

    pygame.display.flip()