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

sp = Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri="http://127.0.0.1:8080/callback",
    scope="user-read-playback-state user-read-currently-playing user-modify-playback-state user-library-modify",
    cache_path=os.path.join(os.path.dirname(__file__), ".spotipy_cache")
))

pygame.init()
WIDTH, HEIGHT = 442, 250
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Spotify UI")

font = pygame.font.SysFont("monospace", 18)
font_small = pygame.font.SysFont("Arial", 16)
font_large = pygame.font.SysFont("Arial", 26)
font_xl = pygame.font.SysFont("Arial", 40)
font_2xl = pygame.font.SysFont("Arial", 80)

ui = {
    "mode": "music",
    "playlist_tracks": [],
    "user_playlists": [],
    "selected_index": 0,
    "current_playlist_id": None,
    "down_key_time": None,
    "slider_drag": False,
    "slider_value": 0.0
}

SLIDER_X = 117 + 10
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

def get_user_playlists():
    return sp.current_user_playlists(limit=50)["items"]

def get_tracks_from_playlist(playlist_id):
    return sp.playlist_items(playlist_id, limit=100)["items"]

# UI

def draw_slider(items):
    if not items: return
    pygame.draw.rect(screen, (180, 180, 180), (SLIDER_X, SLIDER_Y, SLIDER_WIDTH, SLIDER_HEIGHT), border_radius=5)
    pos_x = SLIDER_X + int(ui["slider_value"] * SLIDER_WIDTH)
    pygame.draw.rect(screen, (50, 150, 220), (pos_x - 6, SLIDER_Y - 4, 12, SLIDER_HEIGHT + 8), border_radius=4)

def draw_tft():
    tft_x = 117
    pygame.draw.rect(screen, (255, 255, 255), (tft_x, 5, 320, 240))

    if ui["mode"] == "music":
        track_info = get_current_track()
        screen.blit(font_xl.render("Now Playing", True, (50, 50, 50)), (tft_x+10, 10))
        if track_info:
            img = load_image(track_info["image_url"])
            if img: screen.blit(img, (tft_x+240, 10))
            text = f"{track_info['track']} — {track_info['artist']}"
            for i, line in enumerate(wrap_text(text, font_large, 220)):
                screen.blit(font_large.render(line, True, (0, 100, 0)), (tft_x+10, 60+i*28))
            screen.blit(font_small.render(f"Album: {track_info['album']}", True, (80, 80, 80)), (tft_x+10, 150))
        else:
            screen.blit(font.render("Nothing playing", True, (120, 0, 0)), (tft_x+10, 60))

    elif ui["mode"] == "playlists":
        items = ui["user_playlists"]
        total = len(items)
        per_page = 6
        start = int(ui["slider_value"] * max(1, (total - per_page)))
        visible = items[start:start+per_page]
        screen.blit(font_large.render("Your Playlists", True, (30, 30, 30)), (tft_x+10, 10))
        for i, pl in enumerate(visible):
            name = pl["name"]
            global_index = start + i
            color = (255, 255, 255) if global_index == ui["selected_index"] else (80, 80, 80)
            bg = (0, 120, 200) if global_index == ui["selected_index"] else (230, 230, 230)
            pygame.draw.rect(screen, bg, (tft_x+10, 50+i*26, 300, 24))
            screen.blit(font_small.render(name[:35], True, color), (tft_x+14, 52+i*26))
        draw_slider(items)

    elif ui["mode"] == "songs":
        items = ui["playlist_tracks"]
        total = len(items)
        per_page = 7
        start = int(ui["slider_value"] * max(1, (total - per_page)))
        visible = items[start:start+per_page]
        screen.blit(font_large.render("Songs", True, (30, 30, 30)), (tft_x+10, 10))
        for i, item in enumerate(visible):
            track = item.get("track")
            if not track:
                continue  # skip invalid track entries

            text = f"{track.get('name', 'Unknown')} — {track['artists'][0]['name'] if track.get('artists') else 'Unknown'}"
            global_index = start + i
            color = (255, 255, 255) if global_index == ui["selected_index"] else (70, 70, 70)
            bg = (0, 200, 100) if global_index == ui["selected_index"] else (220, 220, 220)
            pygame.draw.rect(screen, bg, (tft_x+10, 50+i*22, 300, 20))
            screen.blit(font_small.render(text[:40], True, color), (tft_x+14, 50+i*22))
        draw_slider(items)

def draw_epaper():
    pygame.draw.rect(screen, (230, 230, 230), (0, 0, 112, 250))
    screen.blit(font.render(datetime.now().strftime("%H:%M"), True, (0, 0, 0)), (10, 10))
    screen.blit(font.render("Spotify", True, (0, 0, 0)), (10, 40))

def render_ui():
    screen.fill((100, 100, 100))
    draw_epaper()
    draw_tft()
    pygame.display.flip()

# Interaction

def handle_mouse(event):
    if event.type == pygame.MOUSEBUTTONDOWN:
        mx, my = event.pos
        if SLIDER_X <= mx <= SLIDER_X + SLIDER_WIDTH and SLIDER_Y <= my <= SLIDER_Y + SLIDER_HEIGHT:
            ui["slider_drag"] = True
    elif event.type == pygame.MOUSEBUTTONUP:
        ui["slider_drag"] = False
    elif event.type == pygame.MOUSEMOTION and ui["slider_drag"]:
        mx = max(SLIDER_X, min(event.pos[0], SLIDER_X + SLIDER_WIDTH))
        ui["slider_value"] = (mx - SLIDER_X) / SLIDER_WIDTH


def handle_key(event):
    if event.key == pygame.K_w:
        ui["selected_index"] = max(0, ui["selected_index"] - 1)
    elif event.key == pygame.K_s:
        items = ui["playlist_tracks"] if ui["mode"] == "songs" else ui["user_playlists"]
        ui["selected_index"] = min(len(items)-1, ui["selected_index"] + 1)
    elif event.key == pygame.K_RETURN:
        if ui["mode"] == "playlists":
            selected = ui["user_playlists"][ui["selected_index"]]
            ui["playlist_tracks"] = get_tracks_from_playlist(selected["id"])
            ui["current_playlist_id"] = selected["id"]
            ui["selected_index"] = 0
            ui["slider_value"] = 0
            ui["mode"] = "songs"
        elif ui["mode"] == "songs":
            uri = ui["playlist_tracks"][ui["selected_index"]]["track"]["uri"]
            sp.start_playback(uris=[uri])
            ui["mode"] = "music"
    elif event.key == pygame.K_UP:
        if ui["mode"] == "music":
            current = sp.current_playback()
            if current and current.get("context") and "playlist" in current["context"]["type"]:
                playlist_id = current["context"]["uri"].split(":")[-1]
                ui["playlist_tracks"] = get_tracks_from_playlist(playlist_id)
                ui["current_playlist_id"] = playlist_id
                ui["selected_index"] = 0
                ui["slider_value"] = 0
                ui["mode"] = "songs"
        elif ui["mode"] == "songs":
            ui["user_playlists"] = get_user_playlists()
            ui["selected_index"] = 0
            ui["slider_value"] = 0
            ui["mode"] = "playlists"
        elif ui["mode"] == "playlists":
            ui["mode"] = "music"
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
