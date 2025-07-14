import pygame
from wrap_text import wrap_text

pygame.init()

# Set up TFT screen only
WIDTH, HEIGHT = 320, 240
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TFT UI Only")
font = pygame.font.SysFont("monospace", 18)
font_small = pygame.font.SysFont("Ariel", 16)
font_medium = pygame.font.SysFont("monospace", 24)
font_large = pygame.font.SysFont("Ariel", 36)
font_xl = pygame.font.SysFont("Ariel", 45)
font_2xl = pygame.font.SysFont("Ariel", 70)

# UI State
ui = {
    "mode": "study",
    "tasks": ["do math", "read notes", "breathe", "ask out maybe idk", "where is ??", "wow maybe i got :(("],
    "selected_task_index": 0,
    "countdown_seconds": 30 * 60,
    "countdown_running": False,
    "countdown_start": pygame.time.get_ticks(),
}

def draw_tft():
    screen.fill((255, 255, 255))

    # Tasks list (left side)
    x_margin = 10
    y_start = 10
    line_spacing = 20
    max_width = 100

    for i, task in enumerate(ui["tasks"]):
        is_selected = (i == ui["selected_task_index"])
        color_bg = (0, 0, 0) if is_selected else (255, 255, 255)
        color_fg = (255, 255, 255) if is_selected else (0, 0, 0)

        wrapped_lines = wrap_text(task, font_small, max_width)
        line_y = y_start

        for j, line in enumerate(wrapped_lines):
            display_line = line
            if j == 0 and is_selected:
                display_line = "> " + display_line

            if is_selected:
                pygame.draw.rect(screen, color_bg, (x_margin - 5, line_y, max_width + 10, line_spacing))
            screen.blit(font_small.render(display_line, True, color_fg), (x_margin, line_y))

            line_y += line_spacing

        y_start = line_y + 5  # add space after each task

    # Current task label + text (top right)
    selected_task = ui["tasks"][ui["selected_task_index"]]
    screen.blit(font_xl.render("Now:", True, (200, 200, 200)), (125, 10))

    wrapped_lines = wrap_text(selected_task, font_medium, 195)
    y_text = 60
    for line in wrapped_lines[:2]:
        screen.blit(font_medium.render(line, True, (0, 0, 0)), (125, y_text))
        y_text += font_medium.get_height() + 2

    # Countdown (bottom right)
    if ui["countdown_running"]:
        elapsed_ms = pygame.time.get_ticks() - ui["countdown_start"]
        remaining_sec = max(0, ui["countdown_seconds"] - elapsed_ms // 1000)
    else:
        remaining_sec = ui["countdown_seconds"]

    mins, secs = divmod(remaining_sec, 60)
    countdown_str = f"{mins:02d}:{secs:02d}"
    screen.blit(font_2xl.render(countdown_str, True, (0, 0, 0)), (135, 170))

def render_ui():
    draw_tft()
    pygame.display.flip()

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                ui["selected_task_index"] = (ui["selected_task_index"] + 1) % len(ui["tasks"])
                ui["countdown_running"] = False
                ui["countdown_seconds"] = 30 * 60

            elif event.key == pygame.K_UP:
                ui["selected_task_index"] = (ui["selected_task_index"] - 1) % len(ui["tasks"])
                ui["countdown_running"] = False
                ui["countdown_seconds"] = 30 * 60

            elif event.key == pygame.K_w:
                ui["countdown_running"] = False
                ui["countdown_seconds"] += 10 * 60

            elif event.key == pygame.K_s:
                ui["countdown_running"] = False
                ui["countdown_seconds"] = max(0, ui["countdown_seconds"] - 5 * 60)

            elif event.key == pygame.K_RETURN:
                ui["countdown_running"] = not ui["countdown_running"]
                ui["countdown_start"] = pygame.time.get_ticks()

    render_ui()
