from machine import Pin, SPI
import time
import ili9341
import neopixel
global selected_task_index, countdown_seconds, countdown_running, countdown_start
# --- Hardware Setup ---
NUM_LEDS = 64
np = neopixel.NeoPixel(Pin(22), NUM_LEDS)
spi = SPI(1, baudrate=32000000, sck=Pin(10), mosi=Pin(11), miso=Pin(12))
tft = ili9341.Display(spi=spi, cs=Pin(17), dc=Pin(15), rst=Pin(16), width=320, height=240)

def color565(r, g, b):
    return (r & 0xf8) << 8 | (g & 0xfc) << 3 | b >> 3

# --- Study State ---
tasks = [
    "do math", "read notes", "breathe", "ask out maybe idk",
    "where is ??", "wow maybe i got :(("
]
selected_task_index = 0
countdown_seconds = 30 * 60
countdown_running = False
countdown_start = time.ticks_ms()

def wrap_text(text, max_width=16):
    # Simple word wrap for 8x8 font, max_width in chars
    words = text.split(' ')
    lines = []
    current = ""
    for word in words:
        if len(current + " " + word) <= max_width:
            if current:
                current += " " + word
            else:
                current = word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def draw_study():
    tft.clear()
    # Tasks list (left side)
    x_margin = 10
    y_start = 10
    line_spacing = 18
    max_width = 16  # chars for 8x8 font

    for i, task in enumerate(tasks):
        is_selected = (i == selected_task_index)
        bg = color565(0, 0, 0) if is_selected else color565(255, 255, 255)
        fg = color565(255, 255, 255) if is_selected else color565(0, 0, 0)
        lines = wrap_text(task, max_width)
        line_y = y_start
        for j, line in enumerate(lines):
            display_line = line
            if j == 0 and is_selected:
                display_line = "> " + display_line
            if is_selected:
                tft.fill_rect(x_margin - 2, line_y, 8 * max_width + 4, line_spacing, bg)
            tft.draw_text8x8(x_margin, line_y, display_line, fg)
            line_y += line_spacing
        y_start = line_y + 2

    # Current task label + text (top right)
    tft.draw_text8x8(140, 10, "Now:", color565(180, 180, 180))
    lines = wrap_text(tasks[selected_task_index], 22)
    y_text = 35
    for line in lines[:2]:
        tft.draw_text8x8(140, y_text, line, color565(0, 0, 0))
        y_text += 14

    # Countdown (bottom right)
    if countdown_running:
        elapsed_ms = time.ticks_diff(time.ticks_ms(), countdown_start)
        remaining_sec = max(0, countdown_seconds - elapsed_ms // 1000)
    else:
        remaining_sec = countdown_seconds
    mins, secs = divmod(remaining_sec, 60)
    countdown_str = "{:02d}:{:02d}".format(mins, secs)
    tft.draw_text8x8(180, 180, countdown_str, color565(0, 0, 0))

def update_leds():
    # Idle blue/cyan effect
    color = (0, 40, 80) if countdown_running else (0, 10, 30)
    np.fill(color)
    np.write()

# --- Button/Joystick Setup (optional, for navigation) ---
# Example: Use 4 switches for up/down/start/stop (adjust pins as needed)
btn_up = Pin(2, Pin.IN, Pin.PULL_DOWN)
btn_down = Pin(3, Pin.IN, Pin.PULL_DOWN)
btn_start = Pin(4, Pin.IN, Pin.PULL_DOWN)
btn_reset = Pin(5, Pin.IN, Pin.PULL_DOWN)

def debounce(pin):
    # Simple debounce for mechanical switches
    stable = pin.value()
    time.sleep_ms(10)
    return stable and pin.value()

# --- Main Loop ---

last_btn_up = last_btn_down = last_btn_start = last_btn_reset = 0

while True:
    # Button handling (simple polling)
    if btn_down.value() and not last_btn_down:
        if debounce(btn_down):
            selected_task_index = (selected_task_index + 1) % len(tasks)
            countdown_running = False
            countdown_seconds = 30 * 60
            draw_study()
    last_btn_down = btn_down.value()

    if btn_up.value() and not last_btn_up:
        if debounce(btn_up):
            selected_task_index = (selected_task_index - 1) % len(tasks)
            countdown_running = False
            countdown_seconds = 30 * 60
            draw_study()
    last_btn_up = btn_up.value()

    if btn_start.value() and not last_btn_start:
        if debounce(btn_start):
            countdown_running = not countdown_running
            countdown_start = time.ticks_ms()
            draw_study()
    last_btn_start = btn_start.value()

    if btn_reset.value() and not last_btn_reset:
        if debounce(btn_reset):
            countdown_running = False
            countdown_seconds = 30 * 60
            draw_study()
    last_btn_reset = btn_reset.value()

    # Redraw timer every second if running
    if countdown_running:
        elapsed_ms = time.ticks_diff(time.ticks_ms(), countdown_start)
        remaining_sec = max(0, countdown_seconds - elapsed_ms // 1000)
        if remaining_sec == 0:
            countdown_running = False
        draw_study()

    update_leds()
    time.sleep(0.1)