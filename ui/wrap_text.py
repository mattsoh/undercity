def wrap_text(text, font, max_width):
    """
    Splits `text` into a list of lines that fit within `max_width`.
    Each line will be rendered with the provided `font`.
    """
    words = text.split(" ")
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] > max_width:
            if current_line:  # push current line first
                lines.append(current_line.strip())
            current_line = word + " "
        else:
            current_line = test_line

    if current_line:
        lines.append(current_line.strip())

    return lines
