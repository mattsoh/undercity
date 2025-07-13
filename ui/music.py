import pygame
from wrap_text import wrap_text
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime
import os

# 🔐 Spotify Auth Setup
sp = Spotify(auth_manager=SpotifyOAuth(
    client_id="e65f95fd576f4ddd9acbf502cdf117b2",
    client_secret="762122ffebab4cbc98f4e5cf3c7757f3",
    redirect_uri="http://127.0.0.1:8080/callback",
    scope="user-read-playback-state user-read-currently-playing",
    cache_path=os.path.join(os.path.dirname(__file__), ".spotipy_cache")
))

pygame.init()

# Set up window
WIDTH, HEIGHT = 442, 250
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dual-Screen UI Simulator")

# Fonts
font = pygame.font.SysFont("monospace", 18)
font_small = pygame.font.SysFont("Ariel", 16)
font_medium = pygame.font.SysFont("monospace", 24)
font_large = pygame.font.SysFont("Ariel", 36)
font_xl = pygame.font.SysFont("Ariel", 45)
font_2xl = pygame.font.SysFont("Ariel", 100)

# UI State
ui = {
    "mode": "music",
    "tasks": ["Play something!"],
    "selected_task_index": 0,
    "countdown_seconds": 30 * 60,
    "countdown_running": False,
    "countdown_start": pygame.time.get_ticks(),
}

def get_current_spotify_track():
    try:
        current = sp.current_playback()
        if current and current["is_playing"]:
            track = current["item"]["name"]
            artist = current["item"]["artists"][0]["name"]
            return f"{track} — {artist}"
    except Exception as e:
        print("Spotify error:", e)
    return "Nothing playing"

def draw_tft():
    tft_x = 117
    tft_y = 5
    pygame.draw.rect(screen, (255, 255, 255), (tft_x, tft_y, 320, 240))

    # 🎵 Display Spotify track
    track_info = get_current_spotify_track()
    wrapped = wrap_text(track_info, font_large, 310)
    y_spotify = 50
    screen.blit(font_xl.render("Now Playing:", True, (100, 100, 100)), (tft_x + 10, 10))
    for line in wrapped:
        screen.blit(font_large.render(line, True, (0, 120, 0)), (tft_x + 10, y_spotify))
        y_spotify += font_large.get_height() + 4

    # 🕒 Countdown (even though it's not used for now, kept for UI consistency)
    if ui["countdown_running"]:
        elapsed_ms = pygame.time.get_ticks() - ui["countdown_start"]
        remaining_sec = max(0, ui["countdown_seconds"] - elapsed_ms // 1000)
    else:
        remaining_sec = ui["countdown_seconds"]

    mins, secs = divmod(remaining_sec, 60)
    countdown_str = f"{mins:02d}:{secs:02d}"
    screen.blit(font_2xl.render(countdown_str, True, (0, 0, 0)), (tft_x + 110, 140))

def draw_epaper():
    epd_x = 0
    pygame.draw.rect(screen, (230, 230, 230), (epd_x, 0, 112, 250))
    screen.blit(font.render(datetime.now().strftime("%H:%M"), True, (0, 0, 0)), (10, 10))
    screen.blit(font.render("Spotify", True, (0, 0, 0)), (10, 40))

def render_ui():
    screen.fill((100, 100, 100))  # background
    draw_epaper()
    draw_tft()
    pygame.display.flip()

# 🌀 Main Loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    render_ui()
    pygame.time.wait(1000)  # refresh every 1s
