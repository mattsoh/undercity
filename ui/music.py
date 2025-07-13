import pygame
from wrap_text import wrap_text

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
    "mode": "study",
    "tasks": ["do math", "read notes", "breathe", "ask out maybe idk", "where ??", "i :(("],
    "selected_task_index": 0,
    "countdown_seconds": 30 * 60,  # configurable total time in seconds
    "countdown_running": False,
    "countdown_start": pygame.time.get_ticks(),  # for the 30-minute timer
}

def draw_epaper():
    epd_x = 0
    pygame.draw.rect(screen, (230, 230, 230), (epd_x, 0, 112, 250))  # e-paper background

    black = (0, 0, 0)
    screen.blit(font_large.render("Tasks", True, black), (10, 10))

    max_tasks = 8
    x_margin = 10
    y_start = 40
    line_break_height = 20
    line_accidental_break_height = 15
    max_width = 92  # WIDTH of e-paper panel - margin

    y_pos = y_start
    task_count = 0

    for i, task in enumerate(ui["tasks"][:max_tasks]):
        is_selected = (i == ui["selected_task_index"])
        color_bg = (0, 0, 0) if is_selected else (230, 230, 230)
        color_fg = (255, 255, 255) if is_selected else (0, 0, 0)

        wrapped_lines = wrap_text(task, font_small, max_width)
        line_y = y_pos

        for j, line in enumerate(wrapped_lines):
            display_line = line
            if j == 0 and is_selected:
                display_line = "> " + display_line

            if is_selected:
                pygame.draw.rect(
                    screen,
                    color_bg,
                    (x_margin - 5, line_y, max_width + 10, line_break_height),
                )
            screen.blit(
                font_small.render(display_line, True, color_fg),
                (x_margin, line_y),
            )
            line_y += line_accidental_break_height if j < len(wrapped_lines) - 1 else line_break_height

        y_pos = line_y



def draw_tft():
    tft_x = 117
    tft_y = 5
    pygame.draw.rect(screen, (255, 255, 255), (tft_x, tft_y, 320, 240))

    # Show current task in large font
    selected_task = ui["tasks"][ui["selected_task_index"]]
    screen.blit(font_xl.render("Now:", True, (200, 200, 200)), (tft_x + 10, 10))
    wrapped_lines = wrap_text(selected_task, font_xl, 310)
    y_text = 50
    for line in wrapped_lines[:2]:  # Limit to 2 lines maybe
        screen.blit(font_xl.render(line, True, (0, 0, 0)), (tft_x + 10, y_text))
        y_text += font_xl.get_height() + 4

    # Countdown
    if ui["countdown_running"]:
        elapsed_ms = pygame.time.get_ticks() - ui["countdown_start"]
        remaining_sec = max(0, ui["countdown_seconds"] - elapsed_ms // 1000)
    else:
        remaining_sec = ui["countdown_seconds"]  # just show the raw value if not running

    mins, secs = divmod(remaining_sec, 60)
    countdown_str = f"{mins:02d}:{secs:02d}"
    screen.blit(font_2xl.render(countdown_str, True, (0, 0, 0)), (tft_x + 110, 140))



def render_ui():
    screen.fill((100, 100, 100))  # background behind screens
    draw_epaper()
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
                ui["countdown_running"] = False  # pause
                ui["countdown_seconds"] = 30 * 60  # reset if you want

            elif event.key == pygame.K_UP:
                ui["selected_task_index"] = (ui["selected_task_index"] - 1) % len(ui["tasks"])
                ui["countdown_running"] = False
                ui["countdown_seconds"] = 30 * 60

            elif event.key == pygame.K_w:
                ui["countdown_running"] = False  # pause timer
                ui["countdown_seconds"] += 10 * 60

            elif event.key == pygame.K_s:
                ui["countdown_running"] = False  # pause timer
                ui["countdown_seconds"] = max(0, ui["countdown_seconds"] - 5 * 60)

            elif event.key == pygame.K_RETURN:
                ui["countdown_running"] = not ui["countdown_running"]
                ui["countdown_start"] = pygame.time.get_ticks()

    render_ui()

