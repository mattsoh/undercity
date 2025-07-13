import os
from dotenv import load_dotenv
import pygame
from wrap_text import wrap_text
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime
import requests
from io import BytesIO

load_dotenv()

# 🔐 Spotify Auth Setup
sp = Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
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
            album = current["item"]["album"]["name"]
            image_url = current["item"]["album"]["images"][0]["url"]  # usually highest res
            return {
                "track": track,
                "artist": artist,
                "album": album,
                "image_url": image_url
            }
    except Exception as e:
        print("Spotify error:", e)
    return None

def load_image_from_url(url):
    try:
        response = requests.get(url)
        img_data = BytesIO(response.content)
        return pygame.image.load(img_data)
    except Exception as e:
        print("Image load error:", e)
        return None

def spotify_like_track():
    try:
        current = sp.current_playback()
        if current and current["is_playing"]:
            track_id = current["item"]["id"]
            sp.current_user_saved_tracks_add([track_id])
            print("Liked track.")
    except Exception as e:
        print("Like error:", e)

def spotify_next():
    try:
        sp.next_track()
        print("Skipped to next track.")
    except Exception as e:
        print("Next error:", e)

def spotify_previous():
    try:
        sp.previous_track()
        print("Went to previous track.")
    except Exception as e:
        print("Previous error:", e)

def spotify_toggle_play_pause():
    try:
        playback = sp.current_playback()
        if playback:
            if playback["is_playing"]:
                sp.pause_playback()
                print("Paused.")
            else:
                sp.start_playback()
                print("Playing.")
    except Exception as e:
        print("Toggle error:", e)


def draw_tft():
    tft_x = 117
    tft_y = 5
    pygame.draw.rect(screen, (255, 255, 255), (tft_x, tft_y, 320, 240))

    # 🎵 Display Spotify track
    track_info = get_current_spotify_track()
    screen.blit(font_xl.render("Now Playing:", True, (100, 100, 100)), (tft_x + 10, 10))

    if track_info:
        # 🎨 Album Art
        image_url = track_info.get("image_url")
        if image_url:
            album_img = load_image_from_url(image_url)
            if album_img:
                album_img = pygame.transform.scale(album_img, (64, 64))  # resize for UI
                screen.blit(album_img, (tft_x + 240, 10))

        # 📝 Text Info
        track_str = f"{track_info['track']} — {track_info['artist']}"
        album_str = f"Album: {track_info['album']}"
        wrapped_track = wrap_text(track_str, font_large, 220)  # narrower for room
        wrapped_album = wrap_text(album_str, font_small, 220)

        y_spotify = 50
        for line in wrapped_track:
            screen.blit(font_large.render(line, True, (0, 120, 0)), (tft_x + 10, y_spotify))
            y_spotify += font_large.get_height() + 4

        for line in wrapped_album:
            screen.blit(font_small.render(line, True, (50, 50, 50)), (tft_x + 10, y_spotify))
            y_spotify += font_small.get_height() + 2
        album_str = f"Album: {track_info['album']}"
        wrapped_track = wrap_text(track_str, font_large, 310)
        wrapped_album = wrap_text(album_str, font_small, 310)
    else:
        screen.blit(font_large.render("Nothing playing", True, (120, 0, 0)), (tft_x + 10, 50))

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

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                spotify_next()
            elif event.key == pygame.K_LEFT:
                spotify_previous()

            elif event.key == pygame.K_DOWN:
                down_key_pressed_time = pygame.time.get_ticks()  # store press time

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_DOWN:
                if down_key_pressed_time:
                    duration = pygame.time.get_ticks() - down_key_pressed_time
                    if duration >= 1000:  # 1 second = like
                        spotify_like_track()
                    else:  # short tap = play/pause
                        spotify_toggle_play_pause()
                    down_key_pressed_time = None

    render_ui()
    pygame.time.wait(1000)  # refresh every 1s
