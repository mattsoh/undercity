from machine import Pin, ADC
import time

# Import your mode modules
import ili9341
import neopixel

import idle
import music
import study

# --- Hardware Setup (reuse from music.py) ---
joy_vrx = ADC(Pin(27))   # GP27 = ADC1 (X-axis)
joy_vry = ADC(Pin(28))   # GP28 = ADC2 (Y-axis)
joy_sw = Pin(6, Pin.IN, Pin.PULL_UP)  # GP6 = button (active low)

# Mode list and state
modes = ["idle", "music", "study"]
mode_funcs = {
    "idle": idle.idle_loop,
    "music": music.main_loop if hasattr(music, "main_loop") else music.__main__,  # adapt as needed
    "study": study.main_loop if hasattr(study, "main_loop") else study.__main__,
}
current_mode_index = 0

def switch_mode(new_index):
    global current_mode_index
    current_mode_index = new_index % len(modes)
    print("Switching to mode:", modes[current_mode_index])

def main():
    global current_mode_index
    last_switch_time = 0
    debounce_time = 500  # ms
    x_center = 32768
    threshold = 10000

    while True:
        # Read joystick
        x_val = joy_vrx.read_u16()
        sw_val = not joy_sw.value()  # Pressed = True

        # Check for mode switch (hold button + left/right)
        now = time.ticks_ms()
        if sw_val and time.ticks_diff(now, last_switch_time) > debounce_time:
            if x_val < (x_center - threshold):
                switch_mode(current_mode_index - 1)
                last_switch_time = now
            elif x_val > (x_center + threshold):
                switch_mode(current_mode_index + 1)
                last_switch_time = now

        # Run the current mode's main loop or update function
        mode_name = modes[current_mode_index]
        mode_func = mode_funcs[mode_name]
        mode_func()  # This should be non-blocking or return on mode change

        # Small delay to avoid busy loop
        time.sleep(0.05)

if __name__ == "__main__":
    main()