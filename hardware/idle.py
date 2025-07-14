from machine import Pin, SPI
import time
import ili9341
import neopixel

# --- Hardware Setup (reuse from music.py) ---
NUM_LEDS = 64
np = neopixel.NeoPixel(Pin(22), NUM_LEDS)
spi = SPI(1, baudrate=32000000, sck=Pin(10), mosi=Pin(11), miso=Pin(12))
tft = ili9341.Display(spi=spi, cs=Pin(17), dc=Pin(15), rst=Pin(16), width=320, height=240)

def color565(r, g, b):
    return (r & 0xf8) << 8 | (g & 0xfc) << 3 | b >> 3

# --- Idle Animation State ---
circle_x = 160
circle_y = 160
circle_dx = 2
circle_dy = 2
circle_radius = 40

def draw_time():
    """Draw the current time in the center top."""
    t = time.localtime()
    time_str = "{:02}:{:02}".format(t[3], t[4])
    tft.draw_text8x8(110, 40, time_str, color565(0, 0, 0))

def draw_animation():
    """Draw a simple bouncing circle as a placeholder for the cat GIF."""
    global circle_x, circle_y, circle_dx, circle_dy

    # Clear previous animation area
    tft.fill_rect(100, 100, 120, 120, color565(255, 255, 255))

    # Draw the circle
    tft.fill_circle(circle_x, circle_y, circle_radius, color565(200, 100, 255))

    # Move circle
    circle_x += circle_dx
    circle_y += circle_dy
    if circle_x - circle_radius < 100 or circle_x + circle_radius > 220:
        circle_dx = -circle_dx
    if circle_y - circle_radius < 100 or circle_y + circle_radius > 220:
        circle_dy = -circle_dy

def update_leds():
    """Idle LED effect (soft purple pulsing)."""
    color = (30, 0, 60)
    np.fill(color)
    np.write()

def idle_loop():
    tft.clear()
    last_time = -1
    while True:
        # Only update time if minute changes
        t = time.localtime()
        if t[4] != last_time:
            tft.fill_rect(0, 0, 320, 100, color565(255, 255, 255))
            draw_time()
            last_time = t[4]

        draw_animation()
        update_leds()
        time.sleep(0.05)  # ~20 FPS

if __name__ == "__main__":
    idle_loop()