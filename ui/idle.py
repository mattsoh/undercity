import pygame
from datetime import datetime
from PIL import Image, ImageSequence

pygame.init()

# Set up combined window: e-paper (left) + TFT (right)
WIDTH, HEIGHT = 442, 250
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dual-Screen UI Simulator")
font = pygame.font.SysFont("monospace", 18)
font_small = pygame.font.SysFont("Ariel", 16)
font_medium = pygame.font.SysFont("monospace", 24)
font_large = pygame.font.SysFont("Ariel", 36)
font_xl = pygame.font.SysFont("Ariel", 45)
font_2xl = pygame.font.SysFont("Ariel", 100)
# UI State
ui = {
    "mode": "idle",
}

def load_gif_frames(path):
    gif = Image.open(path)
    frames = []

    for frame in ImageSequence.Iterator(gif):
        frame = frame.convert("RGBA")
        mode = frame.mode
        size = frame.size
        data = frame.tobytes()

        py_image = pygame.image.fromstring(data, size, mode)
        frames.append(py_image)

    return frames

epaper_gif_frames = load_gif_frames("cat.gif")
gif_frame_index = 0
gif_frame_timer = 0  # in milliseconds


def draw_epaper():
    global gif_frame_index, gif_frame_timer

    epd_x = 0
    pygame.draw.rect(screen, (230, 230, 230), (epd_x, 0, 112, 250))  # e-paper background

    black = (0, 0, 0)

    # ⏰ Get current time
    current_time_str = datetime.now().strftime("%H:%M")  # e.g. "13:45"
    time_surface = font_xl.render(current_time_str, True, black)
    time_pos = (20, 50)
    screen.blit(time_surface, time_pos)

    # calculate where to place the GIF (below time)
    gif_top = time_pos[1] + font_xl.get_height() + 10  # 10px padding under time

    if epaper_gif_frames:
        frame = epaper_gif_frames[gif_frame_index]

        # Optional: scale the frame to fit within 92px width (e-paper margin)
        frame = pygame.transform.scale(frame, (92, 92))  # adjust height as needed

        screen.blit(frame, (10, gif_top))



def draw_tft():
    tft_x = 117
    tft_y = 5
    pygame.draw.rect(screen, (0, 0, 0), (tft_x, tft_y, 320, 240))



def render_ui():
    screen.fill((100, 100, 100))  # background behind screens
    draw_epaper()
    draw_tft()
    pygame.display.flip()

# Main loop
running = True
while running:
    current_time = pygame.time.get_ticks()
    if current_time - gif_frame_timer > 500:  # change frame every 100ms
        gif_frame_timer = current_time
        gif_frame_index = (gif_frame_index + 1) % len(epaper_gif_frames)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    render_ui()

