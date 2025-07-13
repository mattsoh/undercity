from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os

sp = Spotify(auth_manager=SpotifyOAuth(
    client_id="e65f95fd576f4ddd9acbf502cdf117b2",
    client_secret="762122ffebab4cbc98f4e5cf3c7757f3",
    redirect_uri="http://127.0.0.1:8080/callback",
    scope="user-read-playback-state user-read-currently-playing",
    cache_path=os.path.join(os.path.dirname(__file__), ".spotipy_cache"),
    open_browser=True
))

print(sp.current_playback())
