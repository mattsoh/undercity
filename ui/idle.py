import pygame
from datetime import datetime
from PIL import Image, ImageSequence

pygame.init()

# Set up TFT screen only
WIDTH, HEIGHT = 320, 240
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TFT Idle Screen")
font_xl = pygame.font.SysFont("Ariel", 45)
font_2xl = pygame.font.SysFont("Ariel", 70)

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

# Load cat gif frames
tft_gif_frames = load_gif_frames("cat.gif")
gif_frame_index = 0
gif_frame_timer = 0  # in milliseconds

def draw_tft_idle():
    global gif_frame_index, gif_frame_timer

    # Background
    screen.fill((255, 255, 255))

    # 🕒 Time display
    current_time_str = datetime.now().strftime("%H:%M")
    time_surface = font_2xl.render(current_time_str, True, (0, 0, 0))
    time_rect = time_surface.get_rect(center=(WIDTH // 2, 70))
    screen.blit(time_surface, time_rect)

    # 🐱 Cat GIF display
    if tft_gif_frames:
        frame = tft_gif_frames[gif_frame_index]
        frame = pygame.transform.scale(frame, (120, 120))  # Resize to fit nicely
        gif_rect = frame.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
        screen.blit(frame, gif_rect)

def render_ui():
    if ui["mode"] == "idle":
        draw_tft_idle()
    pygame.display.flip()

# Main loop
running = True
clock = pygame.time.Clock()

while running:
    current_time = pygame.time.get_ticks()

    # Advance GIF frame every 500ms
    if current_time - gif_frame_timer > 500:
        gif_frame_timer = current_time
        gif_frame_index = (gif_frame_index + 1) % len(tft_gif_frames)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    render_ui()
    clock.tick(60)
