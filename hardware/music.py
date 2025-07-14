from machine import Pin, ADC, SPI, PWM
import time
import neopixel
import ili9341
import urequests as requests
import ujson as json

def color565(r, g, b):
    return (r & 0xf8) << 8 | (g & 0xfc) << 3 | b >> 3

# Spotify Configuration
ACCESS_TOKEN = "BQAubm96RrSsWrrJnKx1mZmFL_8kTEfq2ke68lXepXtgQ2QsQcFNM-u5DuKUOM5FVV-QCCeKV9VR88zjA4a2S57-sI3T5Lg2qn1gLDurWiMsFgAdii4qPU07Sw6CCTi41Gv_mHfdBr6YTHDN0NeAUnIHEJQGJBeahfQKwIoRcDbV_XdJQekjo1-Va8hd3NDSssRat-IYhn8_oUqaMsBKI5sIbF3786T4nwMNlDcsvoKNZ9xy94-vCML-x28isXy2QA"
REFRESH_TOKEN = "AQBf928SJdnsiryCOvcUOd2sQtb9h3zWixeTqlxi-RflIp5CtaO7T-VUyqYSGH3YcvsBZ389shre-_EgwviaziIqviXgHIWOyqDdMh1t1W7pxlICPzdAnqbqNNZ82UpQD2s"
CLIENT_ID = "9e6f851fc0b647368e36e852e3ddbbc8"
CLIENT_SECRET = "91fafba2229e437bb311bbf9257d9364"

# WiFi Configuration
WIFI_SSID = "GitHub Guest"
WIFI_PASSWORD = "octocat11"

# Debug Configuration
DEBUG_NETWORK = True  # Enable verbose network debugging
USE_HTTP_FALLBACK = True  # Use HTTP instead of HTTPS for testing
DNS_TEST_ENABLED = True  # Test DNS resolution

class SpotifyClient:
    def __init__(self, access_token, refresh_token=None, client_id=None, client_secret=None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret
        # Allow HTTP fallback for testing
        if USE_HTTP_FALLBACK:
            self.base_url = "http://api.spotify.com/v1"  # WARNING: Insecure, for testing only
            self.token_url = "http://accounts.spotify.com/api/token"
        else:
            self.base_url = "https://api.spotify.com/v1"
            self.token_url = "https://accounts.spotify.com/api/token"
        self.token_expires_at = 0
        
    def _refresh_access_token(self):
        """Refresh the access token using refresh token"""
        if DEBUG_NETWORK:
            print(f"[NET] Attempting to refresh access token...")
            print(f"[NET] Has refresh_token: {bool(self.refresh_token)}")
            print(f"[NET] Has client credentials: {bool(self.client_id and self.client_secret)}")
            
        if not self.refresh_token or not self.client_id or not self.client_secret:
            print("[NET] ERROR: Missing refresh token or credentials")
            return False
            
        data = (
            f"grant_type=refresh_token&"
            f"refresh_token={self.refresh_token}&"
            f"client_id={self.client_id}&"
            f"client_secret={self.client_secret}"
        )
        
        if DEBUG_NETWORK:
            print(f"[NET] Token refresh URL: https://accounts.spotify.com/api/token")
            print(f"[NET] Request data length: {len(data)} bytes")
        
        try:
            if DEBUG_NETWORK:
                print(f"[NET] Sending POST request for token refresh...")
                print(f"[NET] Token URL: {self.token_url}")
                
            response = requests.post(
                self.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if DEBUG_NETWORK:
                print(f"[NET] Token refresh response status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                self.token_expires_at = time.time() + token_data["expires_in"]
                response.close()
                if DEBUG_NETWORK:
                    print(f"[NET] ✓ Token refreshed successfully")
                    print(f"[NET] New token expires in: {token_data['expires_in']} seconds")
                return True
            else:
                if DEBUG_NETWORK:
                    print(f"[NET] ✗ Token refresh failed with status: {response.status_code}")
                    try:
                        error_text = response.text
                        print(f"[NET] Error response: {error_text[:200]}...")
                    except:
                        print(f"[NET] Could not read error response")
                print(f"Token refresh failed: {response.status_code}")
                response.close()
                return False
                
        except Exception as e:
            if DEBUG_NETWORK:
                print(f"[NET] ✗ Token refresh exception: {type(e).__name__}: {e}")
            print(f"Token refresh error: {e}")
            return False
    
    def _make_request(self, endpoint, method="GET", data=None):
        """Make authenticated request to Spotify API"""
        if DEBUG_NETWORK:
            print(f"[NET] Making {method} request to: {endpoint}")
            print(f"[NET] Has data payload: {bool(data)}")
            if data:
                print(f"[NET] Payload size: {len(json.dumps(data))} bytes")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": "MicroPython-Spotify/1.0"
        }
        
        payload = None
        if data:
            payload = json.dumps(data)
            headers["Content-Type"] = "application/json"
            headers["Content-Length"] = str(len(payload))
            if DEBUG_NETWORK:
                print(f"[NET] Content-Type: application/json")
                print(f"[NET] Content-Length: {len(payload)}")
        elif method in ["POST", "PUT"]:
            headers["Content-Length"] = "0"
            if DEBUG_NETWORK:
                print(f"[NET] Empty {method} request")
        
        url = f"{self.base_url}{endpoint}"
        if DEBUG_NETWORK:
            print(f"[NET] Full URL: {url}")
            print(f"[NET] Headers: {len(headers)} items")
        
        try:
            if DEBUG_NETWORK:
                print(f"[NET] Sending request...")
                start_time = time.ticks_ms()
                
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)  # Increased timeout
            elif method == "POST":
                response = requests.post(url, headers=headers, data=payload, timeout=10)
            elif method == "PUT":
                response = requests.put(url, headers=headers, data=payload, timeout=10)
            
            if DEBUG_NETWORK:
                elapsed = time.ticks_diff(time.ticks_ms(), start_time)
                print(f"[NET] Response received in {elapsed}ms")
                print(f"[NET] Status code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    response.close()
                    if DEBUG_NETWORK:
                        print(f"[NET] ✓ JSON response parsed successfully")
                        if isinstance(result, dict):
                            print(f"[NET] Response keys: {list(result.keys())}")
                    return result
                except ValueError as e:
                    if DEBUG_NETWORK:
                        print(f"[NET] ✗ JSON decode error: {e}")
                    print(f"JSON decode error: {e}")
                    response.close()
                    return None
            elif response.status_code == 204:
                response.close()
                if DEBUG_NETWORK:
                    print(f"[NET] ✓ Success with no content (204)")
                return {"success": True}
            elif response.status_code == 401:
                if DEBUG_NETWORK:
                    print(f"[NET] ⚠ Authentication failed (401), attempting token refresh...")
                response.close()
                if self._refresh_access_token():
                    if DEBUG_NETWORK:
                        print(f"[NET] Retrying request with new token...")
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    if method == "GET":
                        response = requests.get(url, headers=headers, timeout=10)
                    elif method == "POST":
                        response = requests.post(url, headers=headers, data=payload, timeout=10)
                    elif method == "PUT":
                        response = requests.put(url, headers=headers, data=payload, timeout=10)
                    
                    if DEBUG_NETWORK:
                        print(f"[NET] Retry response status: {response.status_code}")
                    
                    if response.status_code in [200, 204]:
                        try:
                            result = response.json() if response.status_code == 200 : {"success": True}
                            response.close()
                            if DEBUG_NETWORK:
                                print(f"[NET] ✓ Retry successful")
                            return result
                        except ValueError:
                            response.close()
                            if DEBUG_NETWORK:
                                print(f"[NET] ✓ Retry successful (no JSON)")
                            return {"success": True}
                
                if DEBUG_NETWORK:
                    print(f"[NET] ✗ Authentication failed after token refresh")
                print("Authentication failed")
                response.close()
                return None
            else:
                if DEBUG_NETWORK:
                    print(f"[NET] ✗ Request failed with status: {response.status_code}")
                    try:
                        error_text = response.text
                        print(f"[NET] Error response: {error_text[:200]}...")
                    except:
                        print(f"[NET] Could not read error response")
                print(f"Request failed: {response.status_code}")
                response.close()
                return None
        except Exception as e:
            if DEBUG_NETWORK:
                print(f"[NET] ✗ Request exception: {type(e).__name__}: {e}")
                print(f"[NET] Exception details:")
                print(f"[NET]   - URL: {url}")
                print(f"[NET]   - Method: {method}")
                print(f"[NET]   - Error code: {getattr(e, 'errno', 'unknown')}")
                
                # Try to diagnose the specific error
                if hasattr(e, 'errno'):
                    if e.errno == -2:
                        print(f"[NET] Diagnosis: DNS resolution failure or SSL handshake error")
                        print(f"[NET] Suggestion: Check internet connectivity or try USE_HTTP_FALLBACK=True")
                    elif e.errno == -3:
                        print(f"[NET] Diagnosis: Connection timeout")
                    elif e.errno == -4:
                        print(f"[NET] Diagnosis: Connection refused")
                    elif e.errno == -8:
                        print(f"[NET] Diagnosis: Host unreachable")
                        
            print(f"Request error: {e}")
            return None
    
    def get_current_track(self):
        """Get currently playing track"""
        return self.get_current_track_with_state()
    
    def next_track(self):
        """Skip to next track"""
        if DEBUG_NETWORK:
            print(f"[NET] Requesting next track...")
        result = self._make_request("/me/player/next", "POST")
        if DEBUG_NETWORK:
            print(f"[NET] Next track result: {bool(result)}")
        return result
    
    def previous_track(self):
        """Skip to previous track"""
        if DEBUG_NETWORK:
            print(f"[NET] Requesting previous track...")
        result = self._make_request("/me/player/previous", "POST")
        if DEBUG_NETWORK:
            print(f"[NET] Previous track result: {bool(result)}")
        return result
    
    def toggle_playback(self):
        """Toggle play/pause"""
        if DEBUG_NETWORK:
            print(f"[NET] Getting current playback state for toggle...")
        current = self._make_request("/me/player")
        if current and current.get("is_playing"):
            if DEBUG_NETWORK:
                print(f"[NET] Currently playing, pausing...")
            result = self._make_request("/me/player/pause", "PUT")
        else:
            if DEBUG_NETWORK:
                print(f"[NET] Not playing, starting playback...")
            result = self._make_request("/me/player/play", "PUT")
        if DEBUG_NETWORK:
            print(f"[NET] Toggle playback result: {bool(result)}")
        return result
    
    def set_volume(self, volume_percent):
        """Set volume (0-100)"""
        volume_percent = max(0, min(100, volume_percent))
        if DEBUG_NETWORK:
            print(f"[NET] Setting volume to {volume_percent}%...")
        result = self._make_request(f"/me/player/volume?volume_percent={volume_percent}", "PUT")
        if DEBUG_NETWORK:
            print(f"[NET] Set volume result: {bool(result)}")
        return result
    
    def get_playback_state(self):
        """Get current playback state including volume"""
        if DEBUG_NETWORK:
            print(f"[NET] Getting playback state...")
        result = self._make_request("/me/player")
        if DEBUG_NETWORK and result:
            device = result.get('device', {})
            print(f"[NET] ✓ Playback state - Volume: {device.get('volume_percent', 'unknown')}%, Playing: {result.get('is_playing', False)}")
        return result
    
    def get_current_track_with_state(self):
        """Get currently playing track with playback state"""
        if DEBUG_NETWORK:
            print(f"[NET] Getting current track with state...")
        data = self._make_request("/me/player/currently-playing")
        if data:
            if data.get("item"):
                item = data["item"]
                track_info = {
                    "track": item["name"],
                    "artist": item["artists"][0]["name"],
                    "album": item["album"]["name"],
                    "image_url": item["album"]["images"][0]["url"] if item["album"]["images"] else None,
                    "uri": item["uri"],
                    "id": item["id"],
                    "progress_ms": data.get("progress_ms", 0),
                    "duration_ms": item.get("duration_ms", 0),
                    "is_playing": data.get("is_playing", False)  # Include playback state
                }
                if DEBUG_NETWORK:
                    print(f"[NET] ✓ Current track: {track_info['track']} by {track_info['artist']}")
                    print(f"[NET] Progress: {track_info['progress_ms']}ms / {track_info['duration_ms']}ms")
                    print(f"[NET] Playing: {track_info['is_playing']}")
                return track_info
            elif data.get("is_playing") is not None:
                # Return basic state info even without track details
                return {"is_playing": data.get("is_playing", False)}
        elif data:
            if DEBUG_NETWORK:
                print(f"[NET] Track data received but not playing")
        else:
            if DEBUG_NETWORK:
                print(f"[NET] No track data received")
        return None

# Create Spotify client instance
spotify = SpotifyClient(
    access_token=ACCESS_TOKEN,
    refresh_token=REFRESH_TOKEN,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
)

# WiFi connection function
def connect_wifi(ssid=WIFI_SSID, password=WIFI_PASSWORD):
    """Connect to WiFi network"""
    if DEBUG_NETWORK:
        print(f"[WIFI] Starting WiFi connection to '{ssid}'...")
        print(f"[WIFI] Password length: {len(password)} characters")
        
    try:
        import network
        wlan = network.WLAN(network.STA_IF)
        
        if DEBUG_NETWORK:
            print(f"[WIFI] WLAN interface created")
            print(f"[WIFI] Current active state: {wlan.active()}")
            
        wlan.active(True)
        
        if DEBUG_NETWORK:
            print(f"[WIFI] Interface activated")
            print(f"[WIFI] Checking if already connected...")
        
        if wlan.isconnected():
            config = wlan.ifconfig()
            if DEBUG_NETWORK:
                print(f"[WIFI] ✓ Already connected!")
                print(f"[WIFI] IP: {config[0]}")
                print(f"[WIFI] Subnet: {config[1]}")
                print(f"[WIFI] Gateway: {config[2]}")
                print(f"[WIFI] DNS: {config[3]}")
                
                # Fix DNS if it's not Google's DNS
                if config[3] != '8.8.8.8':
                    print(f"[WIFI] Applying DNS fix (current DNS: {config[3]})...")
                    try:
                        wlan.ifconfig((config[0], config[1], config[2], '8.8.8.8'))
                        new_config = wlan.ifconfig()
                        print(f"[WIFI] ✓ DNS updated to: {new_config[3]}")
                    except Exception as dns_e:
                        print(f"[WIFI] ⚠ DNS fix failed: {dns_e}")
                        
            print(f"Already connected: {wlan.ifconfig()}")
            return True
        
        if DEBUG_NETWORK:
            print(f"[WIFI] Not connected, scanning networks...")
            try:
                networks = wlan.scan()
                print(f"[WIFI] Found {len(networks)} networks")
                for net in networks[:5]:  # Show first 5 networks
                    ssid_name = net[0].decode('utf-8')
                    signal_strength = net[3]
                    print(f"[WIFI]   - {ssid_name} (signal: {signal_strength})")
                    if ssid_name == ssid:
                        print(f"[WIFI]   ✓ Target network found!")
            except Exception as scan_e:
                print(f"[WIFI] Network scan failed: {scan_e}")
        
        print(f"Connecting to {ssid}...")
        if DEBUG_NETWORK:
            print(f"[WIFI] Initiating connection...")
            
        wlan.connect(ssid, password)
        
        timeout = 15
        start_time = time.time()
        connection_attempts = 0
        
        if DEBUG_NETWORK:
            print(f"[WIFI] Waiting for connection (timeout: {timeout}s)...")
        
        while not wlan.isconnected():
            if time.time() - start_time > timeout:
                if DEBUG_NETWORK:
                    print(f"[WIFI] ✗ Connection timeout after {timeout} seconds!")
                    print(f"[WIFI] Connection attempts: {connection_attempts}")
                    print(f"[WIFI] Current status: {wlan.status()}")
                print("Connection timeout!")
                return False
            time.sleep(1)
            connection_attempts += 1
            if DEBUG_NETWORK and connection_attempts % 3 == 0:
                print(f"[WIFI] Still trying... ({connection_attempts}s elapsed, status: {wlan.status()})")
            print(".", end="")
        
        config = wlan.ifconfig()
        if DEBUG_NETWORK:
            print(f"\n[WIFI] ✓ Successfully connected!")
            print(f"[WIFI] Connection time: {time.time() - start_time:.1f} seconds")
            print(f"[WIFI] IP Address: {config[0]}")
            print(f"[WIFI] Subnet Mask: {config[1]}")
            print(f"[WIFI] Gateway: {config[2]}")
            print(f"[WIFI] DNS Server: {config[3]}")
            print(f"[WIFI] Signal strength: {wlan.status('rssi')} dBm")
            
            # Fix DNS issues by setting Google's DNS
            print(f"[WIFI] Applying DNS fix (setting to Google DNS 8.8.8.8)...")
            try:
                wlan.ifconfig((config[0], config[1], config[2], '8.8.8.8'))
                new_config = wlan.ifconfig()
                print(f"[WIFI] ✓ DNS updated to: {new_config[3]}")
            except Exception as dns_e:
                print(f"[WIFI] ⚠ DNS fix failed: {dns_e}")
            
        print(f"\n✓ WiFi connected!")
        print(f"IP: {config[0]}")
        return True
        
    except Exception as e:
        if DEBUG_NETWORK:
            print(f"[WIFI] ✗ WiFi connection exception: {type(e).__name__}: {e}")
        print(f"WiFi connection error: {e}")
        return False

# Network diagnostic functions
def test_dns_resolution():
    """Test DNS resolution for common domains"""
    if not DEBUG_NETWORK or not DNS_TEST_ENABLED:
        return
        
    print(f"[DNS] Testing DNS resolution...")
    test_domains = [
        "google.com",
        "api.spotify.com", 
        "accounts.spotify.com",
        "8.8.8.8"  # Google's DNS
    ]
    
    try:
        import socket
        for domain in test_domains:
            try:
                if DEBUG_NETWORK:
                    print(f"[DNS] Resolving {domain}...")
                addr = socket.getaddrinfo(domain, 80)[0][-1][0]
                print(f"[DNS] ✓ {domain} -> {addr}")
            except Exception as e:
                print(f"[DNS] ✗ {domain} failed: {e}")
    except ImportError:
        print(f"[DNS] socket module not available")
    except Exception as e:
        print(f"[DNS] DNS test error: {e}")

def test_basic_connectivity():
    """Test basic HTTP connectivity"""
    if not DEBUG_NETWORK:
        return
        
    print(f"[CONN] Testing basic connectivity...")
    test_urls = [
        "http://httpbin.org/get",  # Simple HTTP test
        "http://google.com",       # Basic HTTP
    ]
    
    for url in test_urls:
        try:
            if DEBUG_NETWORK:
                print(f"[CONN] Testing {url}...")
            response = requests.get(url, timeout=10)
            print(f"[CONN] ✓ {url} -> Status: {response.status_code}")
            response.close()
        except Exception as e:
            print(f"[CONN] ✗ {url} failed: {e}")

# Alternative network functions for when DNS fails
def try_direct_ip_connection():
    """Try connecting to Spotify using direct IP addresses"""
    if not DEBUG_NETWORK:
        return False
        
    print(f"[FALLBACK] Attempting direct IP connection...")
    
    # Try to resolve api.spotify.com to IP manually
    # Note: This is a simplified approach - IPs can change
    spotify_ips = [
        "35.186.224.25",   # Common Spotify API server
        "104.154.127.126", # Another Spotify server
        "104.196.168.148"  # Backup server
    ]
    
    for ip in spotify_ips:
        try:
            print(f"[FALLBACK] Testing connection to {ip}...")
            # Create a simple HTTP request to test connectivity
            test_url = f"http://{ip}"
            response = requests.get(test_url, timeout=5)
            print(f"[FALLBACK] ✓ {ip} responded with status {response.status_code}")
            response.close()
            return ip
        except Exception as e:
            print(f"[FALLBACK] ✗ {ip} failed: {e}")
    
    return False

def force_dns_refresh():
    """Force refresh DNS settings"""
    if not DEBUG_NETWORK:
        return
        
    print(f"[DNS] Forcing DNS refresh...")
    try:
        import network
        wlan = network.WLAN(network.STA_IF)
        
        # Get current config
        current = wlan.ifconfig()
        print(f"[DNS] Current config: {current}")
        
        # Try different DNS servers
        dns_servers = ['8.8.8.8', '1.1.1.1', '8.8.4.4']
        
        for dns in dns_servers:
            try:
                print(f"[DNS] Trying DNS server: {dns}")
                wlan.ifconfig((current[0], current[1], current[2], dns))
                
                # Test DNS resolution
                import socket
                addr = socket.getaddrinfo("google.com", 80)[0][-1][0]
                print(f"[DNS] ✓ DNS {dns} works! google.com -> {addr}")
                return True
            except Exception as e:
                print(f"[DNS] ✗ DNS {dns} failed: {e}")
                
    except Exception as e:
        print(f"[DNS] DNS refresh error: {e}")
    
    return False

# Display functions
def draw_rectangle(x, y, width, height, color):
    """Draw a filled rectangle on the TFT display"""
    try:
        # Try using built-in fill_rect method if available
        tft.fill_rect(x, y, width, height, color)
    except:
        try:
            # Try using built-in draw_rectangle method if available
            tft.draw_rectangle(x, y, width, height, color)
        except:
            # Fallback: draw line by line
            for i in range(height):
                tft.draw_hline(x, y + i, width, color)

def clear_area(x, y, width, height):
    """Clear a specific area of the screen without full refresh"""
    draw_rectangle(x, y, width, height, color565(0, 0, 0))  # Black background

def update_volume_display(volume):
    """Update only the volume display area"""
    global last_displayed_volume
    if last_displayed_volume != volume:
        clear_area(220, 5, 95, 15)  # Wider clear area for slider indicator
        volume_text = f"Vol:{volume}%"
        # Add slider indicator
        slider_pos = int((volume / 100) * 10)  # 0-10 position
        slider_bar = "[" + "=" * slider_pos + "-" * (10 - slider_pos) + "]"
        tft.draw_text8x8(220, 5, volume_text, color565(255,255,255))
        last_displayed_volume = volume

def update_time_display(current_track):
    """Update only the time display (not progress bar)"""
    global last_displayed_time
    if current_track and current_track.get('duration_ms', 0) > 0:
        current_time = current_track.get('progress_ms', 0) // 1000
        total_time = current_track['duration_ms'] // 1000
        time_key = f"{current_time//60}:{current_time%60:02d}"
        
        if last_displayed_time != time_key:
            # Only update the time text area (not the progress bar)
            time_str = f"{current_time//60}:{current_time%60:02d} / {total_time//60}:{total_time%60:02d}"
            
            # Clear only the time text area (below progress bar)
            clear_area(10, 155, 200, 15)  # Clear just the time text line
            tft.draw_text8x8(10, 155, time_str, color565(200, 200, 200))
            
            last_displayed_time = time_key

def update_progress_bar(current_track):
    """Update only the progress bar"""
    if current_track and current_track.get('duration_ms', 0) > 0:
        progress = current_track.get('progress_ms', 0) / current_track['duration_ms']
        bar_width = 200
        bar_height = 6
        y_pos = 145  # Adjusted to match layout after title/artist/album
        
        # Background bar
        draw_rectangle(10, y_pos, bar_width, bar_height, color565(50, 50, 50))
        # Progress bar
        progress_width = max(0, min(int(bar_width * progress), bar_width))
        if progress_width > 0:
            draw_rectangle(10, y_pos, progress_width, bar_height, color565(0, 255, 100))  # Green progress
def wrap_text(text, max_width=25):
    """Wrap text to fit display width"""
    if len(text) <= max_width:
        return [text]
    
    words = text.split(' ')
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line + " " + word) <= max_width:
            if current_line:
                current_line += " " + word
            else:
                current_line = word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines

def draw_playback_icon(x, y, size=40, is_playing=True):
    """Draw play/pause icon based on playback state"""
    # Draw background
    draw_rectangle(x, y, size, size, color565(30, 30, 30))
    # Draw border
    draw_rectangle(x+2, y+2, size-4, size-4, color565(100, 100, 255))
    
    center_x = x + size // 2
    center_y = y + size // 2
    
    if is_playing:
        # Draw pause icon (two vertical bars)
        bar_width = 4
        bar_height = 16
        bar_spacing = 4
        
        # Left bar
        draw_rectangle(center_x - bar_spacing - bar_width, center_y - bar_height//2, 
                      bar_width, bar_height, color565(0, 255, 0))
        # Right bar  
        draw_rectangle(center_x + bar_spacing, center_y - bar_height//2,
                      bar_width, bar_height, color565(0, 255, 0))
    else:
        # Draw play icon (triangle pointing right)
        triangle_size = 12
        # Simple triangle using filled rectangles
        for i in range(triangle_size):
            line_length = i + 1
            if i < triangle_size // 2:
                draw_rectangle(center_x - triangle_size//2 + i, 
                             center_y - line_length//2, 
                             1, line_length, color565(0, 255, 0))
            else:
                line_length = triangle_size - i
                draw_rectangle(center_x - triangle_size//2 + i, 
                             center_y - line_length//2, 
                             1, line_length, color565(0, 255, 0))

def draw_music_info(current_track):
    """Draw current music information on TFT (without progress bar)"""
    if not current_track:
        tft.draw_text8x8(10, 60, "No music playing", color565(255, 255, 255))
        return
    
    # Colors for different elements
    title_color = color565(255, 255, 255)   # White for title
    artist_color = color565(0, 255, 255)    # Cyan for artist
    album_color = color565(255, 255, 0)     # Yellow for album
    
    y_pos = 50
    
    # Track title (wrapped)
    title_lines = wrap_text(current_track['track'], 30)
    for i, line in enumerate(title_lines[:2]):  # Max 2 lines
        tft.draw_text8x8(10, y_pos + i * 15, line, title_color)
    y_pos += len(title_lines[:2]) * 15 + 5
    
    # Artist name
    artist_lines = wrap_text(f"by {current_track['artist']}", 30)
    for i, line in enumerate(artist_lines[:1]):  # Max 1 line
        tft.draw_text8x8(10, y_pos + i * 15, line, artist_color)
    y_pos += 20
    
    # Album name
    album_lines = wrap_text(current_track['album'], 30)
    for i, line in enumerate(album_lines[:1]):  # Max 1 line
        tft.draw_text8x8(10, y_pos + i * 15, line, album_color)
    
    # Note: Progress bar and time are now handled by separate update functions

def get_music_reactive_color(current_track, slider_value):
    """Generate music-reactive LED colors"""
    if current_track and current_track.get('duration_ms', 0) > 0:
        # Create a music-reactive light show
        progress = current_track.get('progress_ms', 0) / current_track['duration_ms']
        beat_intensity = int(progress * 255)
        return (beat_intensity, slider_value >> 8, 255 - beat_intensity)
    else:
        # Default color based on slider
        color = slider_value >> 8
        return (color, 0, 255 - color)

# Music state tracking variables
last_track_id = None
current_music_info = None
music_update_counter = 0
last_joystick_action = 0
last_button_press = 0  # Separate tracking for button presses
last_display_update = 0
display_needs_refresh = True
local_start_time = 0
local_track_offset = 0
last_network_update = 0
last_timer_second = 0
current_volume = 50  # Track current volume (0-100)
display_refresh_interval = 33  # Display refresh interval in ms (30 FPS - less flickering)

# Button hold tracking for directional movements
button_hold_start = 0
button_currently_held = False
button_hold_duration_required = 1000  # 1 second in milliseconds

# Track what needs updating to avoid full screen refresh
last_displayed_volume = None
last_displayed_time = None
last_displayed_track = None
last_displayed_playing_state = None  # Track playback state changes
screen_initialized = False

def update_playback_icon(current_track):
    """Update only the playback icon when state changes"""
    global last_displayed_playing_state
    if current_track:
        is_playing = current_track.get('is_playing', False)
        if last_displayed_playing_state != is_playing:
            # Clear the icon area and redraw
            clear_area(270, 35, 45, 45)
            draw_playback_icon(270, 35, 45, is_playing)
            last_displayed_playing_state = is_playing

def update_music_info():
    """Update music information (call periodically)"""
    global last_track_id, current_music_info, music_update_counter, display_needs_refresh
    global local_start_time, local_track_offset, last_network_update, last_timer_second, current_volume
    
    music_update_counter += 1
    if music_update_counter >= 188:  # Update from network every 188 iterations (~3 seconds with 16ms loop)
        forced_update = music_update_counter >= 188  # Check if this was a forced update
        music_update_counter = 0
        
        if DEBUG_NETWORK:
            print(f"[MUSIC] Network update cycle (forced: {forced_update})")
            
        try:
            if DEBUG_NETWORK:
                print(f"[MUSIC] Fetching current track...")
            new_track = spotify.get_current_track()
            
            # Also get playback state for volume info (less frequently or on forced updates)
            if music_update_counter % 5 == 0 or forced_update:  # Every 5th network update OR when forced
                if DEBUG_NETWORK:
                    print(f"[MUSIC] Getting playback state for volume...")
                playback_state = spotify.get_playback_state()
                if playback_state and playback_state.get('device'):
                    current_volume = playback_state['device'].get('volume_percent', current_volume)
            
            if new_track and new_track.get('id') != last_track_id:
                # New track started
                if DEBUG_NETWORK:
                    print(f"[MUSIC] ✓ New track detected: {new_track.get('track', 'Unknown')}")
                    print(f"[MUSIC] Track ID: {new_track['id']}")
                current_music_info = new_track
                last_track_id = new_track['id']
                display_needs_refresh = True
                # Reset local timer for new track
                local_start_time = time.ticks_ms()
                local_track_offset = new_track.get('progress_ms', 0)
                last_network_update = time.ticks_ms()

            elif new_track:
                current_music_info = new_track
                # Update our local timer base occasionally
                if music_update_counter % 10 == 0:  # Every 10th update
                    local_track_offset = new_track.get('progress_ms', 0)
                    local_start_time = time.ticks_ms()
                last_network_update = time.ticks_ms()
            else:
                if DEBUG_NETWORK:
                    print(f"[MUSIC] No track currently playing")
        except Exception as e:
            print(f"[MUSIC] Error updating music info: {e}")
    
    # Update display more frequently for smooth timer
    if current_music_info and time.ticks_diff(time.ticks_ms(), last_network_update) < 60000:  # Within last minute
        # Calculate current progress using local timer
        current_local_progress = local_track_offset + time.ticks_diff(time.ticks_ms(), local_start_time)
        
        # Update the music info with local progress
        current_music_info_copy = current_music_info.copy()
        current_music_info_copy['progress_ms'] = current_local_progress
        
        # Check if we should refresh display (every second)
        if time.ticks_diff(time.ticks_ms(), last_network_update) % 1000 < 100:
            display_needs_refresh = True
        
        return current_music_info_copy
    
    return current_music_info

def handle_joystick_music_controls(x_val, y_val, sw_val):
    """Handle joystick input for music controls and playlist navigation"""
    global last_joystick_action, last_button_press, display_needs_refresh, local_start_time, local_track_offset, current_volume, music_update_counter
    global button_hold_start, button_currently_held, ui_mode, current_playlists, current_playlist_tracks
    global selected_playlist_index, selected_track_index, current_playlist_id, playlist_view_active, playlist_view_timeout
    current_time = time.ticks_ms()
    
    # Separate debounce for directional movements and button presses
    direction_debounce = 200  # 200ms for directional movements
    button_debounce = 300     # 300ms for button presses (more reliable)
    
    # Convert joystick values to directions
    x_center = 32768
    y_center = 32768
    threshold = 10000  # Lower threshold for more sensitive detection
    
    action_taken = False
    track_skip_action = False
    
    if DEBUG_NETWORK:
        pass  # Reduced logging for performance
    
    # Handle button hold state for directional movements
    if sw_val:
        if not button_currently_held:
            button_hold_start = current_time
            button_currently_held = True
    else:
        if button_currently_held:
            # Button released - check for short press vs hold
            hold_duration = time.ticks_diff(current_time, button_hold_start)
            if hold_duration < button_hold_duration_required:
                # Short press - toggle playbook
                if time.ticks_diff(current_time, last_button_press) > button_debounce:
                    if DEBUG_NETWORK:
                        print(f"[JOY] Short button press - toggle playback")
                    try:
                        spotify.toggle_playback()
                        display_needs_refresh = True
                    except Exception as e:
                        print(f"Toggle playback error: {e}")
                    last_button_press = current_time
        button_currently_held = False
        button_hold_start = 0
    
    # Only process directional movements if button is held
    if button_currently_held and time.ticks_diff(current_time, button_hold_start) >= button_hold_duration_required:
        # Button held long enough - check for directional movements
        if time.ticks_diff(current_time, last_joystick_action) > direction_debounce:
            
            # Playlist navigation mode
            if ui_mode == "playlists":
                if y_val < (y_center - threshold):  # Up - previous playlist
                    if selected_playlist_index > 0:
                        selected_playlist_index -= 1
                        display_needs_refresh = True
                        action_taken = True
                elif y_val > (y_center + threshold):  # Down - next playlist
                    if selected_playlist_index < len(current_playlists) - 1:
                        selected_playlist_index += 1
                        display_needs_refresh = True
                        action_taken = True
                elif x_val > (x_center + threshold):  # Right - enter playlist
                    if current_playlists and selected_playlist_index < len(current_playlists):
                        playlist = current_playlists[selected_playlist_index]
                        current_playlist_id = playlist['id']
                        load_playlist_tracks(current_playlist_id)
                        ui_mode = "playlist_tracks"
                        selected_track_index = 0
                        display_needs_refresh = True
                        action_taken = True
                elif x_val < (x_center - threshold):  # Left - back to music view
                    ui_mode = "music"
                    display_needs_refresh = True
                    action_taken = True
                    
            elif ui_mode == "playlist_tracks":
                if y_val < (y_center - threshold):  # Up - previous track
                    if selected_track_index > 0:
                        selected_track_index -= 1
                        display_needs_refresh = True
                        action_taken = True
                elif y_val > (y_center + threshold):  # Down - next track
                    if selected_track_index < len(current_playlist_tracks) - 1:
                        selected_track_index += 1
                        display_needs_refresh = True
                        action_taken = True
                elif x_val > (x_center + threshold):  # Right - play selected track
                    if current_playlist_tracks and selected_track_index < len(current_playlist_tracks):
                        try:
                            track = current_playlist_tracks[selected_track_index]['track']
                            playlist_uri = f"spotify:playlist:{current_playlist_id}"
                            spotify.play_playlist(playlist_uri, selected_track_index)
                            ui_mode = "music"
                            display_needs_refresh = True
                            action_taken = True
                        except Exception as e:
                            print(f"Play track error: {e}")
                elif x_val < (x_center - threshold):  # Left - back to playlists
                    ui_mode = "playlists"
                    display_needs_refresh = True
                    action_taken = True
                    
            else:  # Music mode - traditional controls
                if x_val < (x_center - threshold):  # Left - Previous track
                    if DEBUG_NETWORK:
                        print(f"[JOY] Previous track")
                    try:
                        spotify.previous_track()
                        music_update_counter = 180  # Force music update soon
                        display_needs_refresh = True
                        track_skip_action = True
                        action_taken = True
                    except Exception as e:
                        print(f"Previous track error: {e}")
                        
                elif x_val > (x_center + threshold):  # Right - Next track
                    if DEBUG_NETWORK:
                        print(f"[JOY] Next track")
                    try:
                        spotify.next_track()
                        music_update_counter = 180  # Force music update soon
                        display_needs_refresh = True
                        track_skip_action = True
                        action_taken = True
                    except Exception as e:
                        print(f"Next track error: {e}")
                
                elif y_val < (y_center - threshold):  # Up - Enter playlist mode
                    ui_mode = "playlists"
                    if not current_playlists:
                        load_playlists()
                    display_needs_refresh = True
                    action_taken = True
                elif y_val > (y_center + threshold):  # Down - Volume down
                    new_volume = max(0, current_volume - 10)
                    if DEBUG_NETWORK:
                        print(f"[JOY] Volume down: {current_volume} -> {new_volume}")
                    try:
                        spotify.set_volume(new_volume)
                        current_volume = new_volume
                        display_needs_refresh = True
                        action_taken = True
                    except Exception as e:
                        print(f"Volume control error: {e}")
            
            # Record action time
            if action_taken:
                last_joystick_action = current_time
                if track_skip_action:
                    # Reset local timer for track changes
                    local_start_time = current_time
                    local_track_offset = 0

def handle_slider_volume_control(slider_value):
    """Handle volume control using physical slider"""
    global last_slider_value, slider_debounce_time, current_volume, display_needs_refresh
    
    current_time = time.ticks_ms()
    slider_debounce = 300  # 300ms debounce for slider changes
    
    # Initialize last_slider_value if this is the first reading
    if last_slider_value is None:
        last_slider_value = slider_value
        return
    
    # Check if slider has moved significantly
    slider_diff = abs(slider_value - last_slider_value)
    
    if slider_diff > slider_change_threshold and time.ticks_diff(current_time, slider_debounce_time) > slider_debounce:
        # Convert slider value (0-65535) to volume percentage (0-100)
        new_volume = int((slider_value / 65535) * 100)
        new_volume = max(0, min(100, new_volume))  # Clamp to 0-100 range
        
        if abs(new_volume - current_volume) >= 2:  # Only update if volume changes by at least 2%
            if DEBUG_NETWORK:
                print(f"[SLIDER] Volume change: {current_volume}% -> {new_volume}% (slider: {slider_value})")
            
            try:
                spotify.set_volume(new_volume)
                current_volume = new_volume
                display_needs_refresh = True
                last_slider_value = slider_value
                slider_debounce_time = current_time
                
                # Optional: Play a short tone to confirm volume change
                play_tone(440 + (new_volume * 4), 0.05)  # Higher pitch for higher volume
                
            except Exception as e:
                print(f"Slider volume control error: {e}")

# Missing playlist functions (stubs to fix compile errors)
def load_playlists():
    """Load user playlists (stub)"""
    global current_playlists
    print("Loading playlists... (not implemented)")
    current_playlists = []

def load_playlist_tracks(playlist_id):
    """Load tracks from a playlist (stub)"""
    global current_playlist_tracks
    print(f"Loading tracks for playlist {playlist_id}... (not implemented)")
    current_playlist_tracks = []

# Missing variables for playlist functionality
current_playlists = []
current_playlist_tracks = []
selected_playlist_index = 0
selected_track_index = 0
current_playlist_id = None
playlist_view_active = False
playlist_view_timeout = 0
ui_mode = "music"  # "music", "playlists", "playlist_tracks"

# --- Existing Setup ---
NUM_LEDS = 64
np = neopixel.NeoPixel(Pin(22), NUM_LEDS)
spi = SPI(1, baudrate=32000000, sck=Pin(10), mosi=Pin(11), miso=Pin(12))
tft = ili9341.Display(spi=spi, cs=Pin(17), dc=Pin(15), rst=Pin(16), width=320, height=240)
switches = [Pin(pin, Pin.IN, Pin.PULL_DOWN) for pin in [2, 3, 4, 5]]
slider = ADC(Pin(26))  # GP26 = ADC0

# --- Joystick Setup ---
joy_vrx = ADC(Pin(27))   # GP27 = ADC1 (X-axis)
joy_vry = ADC(Pin(28))   # GP28 = ADC2 (Y-axis)
joy_sw = Pin(6, Pin.IN, Pin.PULL_UP)  # GP6 = button (active low)

# --- Speaker Setup ---
speaker = PWM(Pin(7))    # GP7

def play_tone(freq, duration=0.2):
    speaker.freq(freq)
    speaker.duty_u16(2000)  # Volume (0-65535)
    time.sleep(duration) 
    speaker.duty_u16(0)

while True:
    # Read switches and slider
    switch_states = [sw.value() for sw in switches]
    slider_value = slider.read_u16()
    # Joystick
    x_val = joy_vrx.read_u16()
    y_val = joy_vry.read_u16()
    sw_val = not joy_sw.value()  # Pressed = True

    # Handle slider volume control
    handle_slider_volume_control(slider_value)

    # Handle joystick music controls FIRST (for fastest response)
    handle_joystick_music_controls(x_val, y_val, sw_val)

    # Update music info periodically
    current_music = update_music_info()

    # Check if we need to refresh display for timer updates (every ~1 second)
    if current_music and local_start_time > 0:
        current_second = (local_track_offset + time.ticks_diff(time.ticks_ms(), local_start_time)) // 1000
        if current_second != last_timer_second:
            display_needs_refresh = True
            last_timer_second = current_second

    # WS2812B update - sync with music
    led_color = get_music_reactive_color(current_music, slider_value)
    np.fill(led_color)
    np.write()

    # Speaker: play tone if joystick button pressed (backup control)
    # Only beep if button is pressed but hasn't been held for 1+ seconds
    if sw_val and button_currently_held:
        hold_duration = time.ticks_diff(current_time_ms, button_hold_start)
        if hold_duration < button_hold_duration_required:
            play_tone(880, 0.05)  # Shorter tone for faster response

    # TFT Display - Smart partial updates to prevent flickering
    current_time_ms = time.ticks_ms()
    if display_needs_refresh and time.ticks_diff(current_time_ms, last_display_update) >= display_refresh_interval:
        display_needs_refresh = False
        last_display_update = current_time_ms
        
        # Full screen refresh only when needed (new track or first time)
        if not screen_initialized or (current_music and last_displayed_track != current_music.get('id')):
            screen_initialized = True
            last_displayed_track = current_music.get('id') if current_music else None
            
            tft.clear()
            
            # Header
            tft.draw_text8x8(10, 5, "UNDERCITY MUSIC CTRL", color565(255, 100, 255))
            
            # System status (compact, top right)
            tft.draw_text8x8(220, 5, f"Vol:{current_volume}%", color565(255,255,255))
            tft.draw_text8x8(220, 20, f"SW:{sum(switch_states)}", color565(255,255,0))
            
            # Reset volume display tracking so it gets updated
            last_displayed_volume = current_volume
            
            # Playback status icon (top right)
            if current_music:
                is_playing = current_music.get('is_playing', False)
                draw_playback_icon(270, 35, 45, is_playing)
            
            # Music information display
            if current_music:
                draw_music_info(current_music)
            
            # Joystick info (bottom) - Fix coordinate display to stay within screen bounds
            joy_x_display = max(0, min(x_val >> 8, 255))  # Limit to 0-255 range
            joy_y_display = max(0, min(y_val >> 8, 255))  # Limit to 0-255 range
            tft.draw_text8x8(10, 200, f"Joy: X{joy_x_display} Y{joy_y_display}", color565(0,255,255))
            tft.draw_text8x8(10, 215, "Hold btn + move joy", color565(100, 100, 100))
            tft.draw_text8x8(150, 215, "to control", color565(100, 100, 100))

        else:
            # Partial updates for frequently changing elements
            update_volume_display(current_volume)
            if current_music:
                update_progress_bar(current_music)  # Update progress bar smoothly
                update_time_display(current_music)   # Update time text when seconds change
    
    time.sleep(0.016)  # 16ms = 60 FPS max refresh rate