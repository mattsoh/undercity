import os
from dotenv import load_dotenv
import pygame
from wrap_text import wrap_text
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime
import requests
from io import BytesIO

# Load environment
load_dotenv()

sp = Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri="http://127.0.0.1:8080/callback",
    scope="user-read-playback-state user-read-currently-playing user-modify-playback-state user-library-modify playlist-read-private",
    cache_path=os.path.join(os.path.dirname(__file__), ".spotipy_cache")
))

# Initialize pygame
pygame.init()
WIDTH, HEIGHT = 320, 240
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Spotify UI")

# Fonts
font = pygame.font.SysFont("monospace", 18)
font_small = pygame.font.SysFont("Arial", 16)
font_large = pygame.font.SysFont("Arial", 26)
font_xl = pygame.font.SysFont("Arial", 40)

# UI State
ui = {
    "mode": "playlists",  # default to library
    "playlist_tracks": [],
    "user_playlists": sp.current_user_playlists(limit=50)["items"],  # load immediately
    "selected_index": 0,
    "current_playlist_id": None,
    "down_key_time": None,
    "slider_drag": False,
    "slider_value": 0.0,
    "slider_just_moved": False,
}

# Constants
SLIDER_X = 10
SLIDER_Y = HEIGHT - 25
SLIDER_WIDTH = 300
SLIDER_HEIGHT = 10


# Spotify Logic

def get_current_track():
    try:
        current = sp.current_playback()
        if current and current["is_playing"]:
            item = current["item"]
            return {
                "track": item["name"],
                "artist": item["artists"][0]["name"],
                "album": item["album"]["name"],
                "image_url": item["album"]["images"][0]["url"]
            }
    except: pass
    return None

def load_image(url):
    try:
        r = requests.get(url)
        return pygame.transform.scale(pygame.image.load(BytesIO(r.content)), (64, 64))
    except: return None

def get_tracks_from_playlist(playlist_id):
    return sp.playlist_items(playlist_id, limit=100)["items"]


# UI Drawing

def draw_slider(items):
    if not items: return
    pygame.draw.rect(screen, (180, 180, 180), (SLIDER_X, SLIDER_Y, SLIDER_WIDTH, SLIDER_HEIGHT), border_radius=5)
    pos_x = SLIDER_X + int(ui["slider_value"] * SLIDER_WIDTH)
    pygame.draw.rect(screen, (50, 150, 220), (pos_x - 6, SLIDER_Y - 4, 12, SLIDER_HEIGHT + 8), border_radius=4)

def draw_tft():
    screen.fill((255, 255, 255))

    if ui["mode"] == "music":
        track_info = get_current_track()
        screen.blit(font_xl.render("Now Playing", True, (50, 50, 50)), (10, 10))
        if track_info:
            img = load_image(track_info["image_url"])
            if img: screen.blit(img, (240, 10))
            text = f"{track_info['track']} — {track_info['artist']}"
            for i, line in enumerate(wrap_text(text, font_large, 220)):
                screen.blit(font_large.render(line, True, (0, 100, 0)), (10, 60+i*28))
            screen.blit(font_small.render(f"Album: {track_info['album']}", True, (80, 80, 80)), (10, 150))
        else:
            screen.blit(font.render("Nothing playing", True, (120, 0, 0)), (10, 60))

    elif ui["mode"] == "playlists":
        items = ui["user_playlists"]
        screen.blit(font_large.render("Your Playlists", True, (30, 30, 30)), (10, 10))
        per_page = 6
        start = int(ui["slider_value"] * max(1, (len(items) - per_page)))
        visible = items[start:start+per_page]
        for i, pl in enumerate(visible):
            name = pl["name"]
            idx = start + i
            bg = (0, 120, 200) if idx == ui["selected_index"] else (230, 230, 230)
            fg = (255, 255, 255) if idx == ui["selected_index"] else (80, 80, 80)
            pygame.draw.rect(screen, bg, (10, 50+i*26, 300, 24))
            screen.blit(font_small.render(name[:35], True, fg), (14, 52+i*26))
        draw_slider(items)

    elif ui["mode"] == "songs":
        items = ui["playlist_tracks"]
        screen.blit(font_large.render("Songs", True, (30, 30, 30)), (10, 10))
        per_page = 7
        start = int(ui["slider_value"] * max(1, (len(items) - per_page)))
        visible = items[start:start+per_page]
        for i, item in enumerate(visible):
            track = item.get("track")
            if not track: continue
            text = f"{track.get('name', 'Unknown')} — {track['artists'][0]['name']}"
            idx = start + i
            bg = (0, 200, 100) if idx == ui["selected_index"] else (220, 220, 220)
            fg = (255, 255, 255) if idx == ui["selected_index"] else (70, 70, 70)
            pygame.draw.rect(screen, bg, (10, 50+i*22, 300, 20))
            screen.blit(font_small.render(text[:40], True, fg), (14, 50+i*22))
        draw_slider(items)


def render_ui():
    draw_tft()
    pygame.display.flip()


# Input Handling

def handle_mouse(event):
    if event.type == pygame.MOUSEBUTTONDOWN:
        mx, my = event.pos
        if SLIDER_X <= mx <= SLIDER_X + SLIDER_WIDTH and SLIDER_Y <= my <= SLIDER_Y + SLIDER_HEIGHT:
            ui["slider_drag"] = True
    elif event.type == pygame.MOUSEBUTTONUP:
        ui["slider_drag"] = False
    elif event.type == pygame.MOUSEMOTION and ui["slider_drag"]:
        mx = max(SLIDER_X, min(event.pos[0], SLIDER_X + SLIDER_WIDTH))
        new_val = (mx - SLIDER_X) / SLIDER_WIDTH
        if abs(new_val - ui["slider_value"]) > 0.01:
            ui["slider_just_moved"] = True
        ui["slider_value"] = new_val

def handle_key(event):
    current_items = ui["playlist_tracks"] if ui["mode"] == "songs" else ui["user_playlists"]
    visible_count = 7 if ui["mode"] == "songs" else 6

    if event.key == pygame.K_w:
        if ui["slider_just_moved"]:
            start = int(ui["slider_value"] * max(1, len(current_items) - visible_count))
            ui["selected_index"] = start
            ui["slider_just_moved"] = False
        else:
            if ui["selected_index"] > 0:
                ui["selected_index"] -= 1
            else:
                # already at top -> scroll up
                ui["slider_value"] = max(0.0, ui["slider_value"] - 0.1)
                start = int(ui["slider_value"] * max(1, len(current_items) - visible_count))
                ui["selected_index"] = start  # <- force selection to top of new visible list

    elif event.key == pygame.K_s:
        if ui["slider_just_moved"]:
            start = int(ui["slider_value"] * max(1, len(current_items) - visible_count))
            ui["selected_index"] = min(start + visible_count - 1, len(current_items) - 1)
            ui["slider_just_moved"] = False
        else:
            if ui["selected_index"] < len(current_items) - 1:
                ui["selected_index"] += 1
            else:
                # already at bottom -> scroll down
                ui["slider_value"] = min(1.0, ui["slider_value"] + 0.1)
                start = int(ui["slider_value"] * max(1, len(current_items) - visible_count))
                ui["selected_index"] = min(start + visible_count - 1, len(current_items) - 1)



    elif event.key == pygame.K_RETURN:
        if ui["mode"] == "playlists":
            selected = ui["user_playlists"][ui["selected_index"]]
            ui["playlist_tracks"] = get_tracks_from_playlist(selected["id"])
            ui["current_playlist_id"] = selected["id"]
            ui["selected_index"] = 0
            ui["slider_value"] = 0
            ui["mode"] = "songs"
        elif ui["mode"] == "songs":
            track = ui["playlist_tracks"][ui["selected_index"]]["track"]
            sp.start_playback(
                context_uri=f"spotify:playlist:{ui['current_playlist_id']}",
                offset={"uri": track["uri"]}
            )
            ui["mode"] = "music"

    elif event.key == pygame.K_UP:
        if ui["mode"] == "songs":
            ui["mode"] = "playlists"
            ui["selected_index"] = 0
            ui["slider_value"] = 0
        elif ui["mode"] == "music":
            ui["mode"] = "playlists"

    elif event.key == pygame.K_DOWN:
        ui["down_key_time"] = pygame.time.get_ticks()

    elif event.key == pygame.K_RIGHT:
        sp.next_track()
    elif event.key == pygame.K_LEFT:
        sp.previous_track()

def check_down_release():
    if ui["down_key_time"]:
        held = pygame.time.get_ticks() - ui["down_key_time"]
        try:
            track_id = sp.current_playback()["item"]["id"]
            if held > 600:
                sp.current_user_saved_tracks_add([track_id])
                print("Liked track")
            else:
                p = sp.current_playback()
                if p["is_playing"]: sp.pause_playback()
                else: sp.start_playback()
        except: pass
        ui["down_key_time"] = None

# Main Loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            handle_key(event)
        elif event.type == pygame.KEYUP and event.key == pygame.K_DOWN:
            check_down_release()
        handle_mouse(event)
    render_ui()
    pygame.time.wait(100)
