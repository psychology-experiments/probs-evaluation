from itertools import product

from PIL import Image, ImageFont, ImageDraw

TEXT_SIZE = (200, 128)
COLOR_MODE = "RGBA"
TEXT_FONT_INFO = dict(font='C:/Windows/fonts/Arial.ttf', size=50)
BASE_COLOR = (0, 0, 0, 0)


def get_text_dimensions(text_string, font, obj):
    # https://stackoverflow.com/a/46220683/9263761
    ascent, descent = font.getmetrics()

    (width, baseline), (offset_x, offset_y) = font.font.getsize(text_string)

    return width, ascent + offset_y


colors_rgb = dict(R=(255, 0, 0), G=(0, 255, 0), B=(0, 0, 255), Y=(255, 255, 0))
colors_text = dict(R='красный', G='зеленый', B='синий', Y='желтый')

for word, color in product("RGBY", "RGBY"):
    instruction_image = Image.new(COLOR_MODE, TEXT_SIZE, BASE_COLOR)
    instruction_font = ImageFont.truetype(**TEXT_FONT_INFO)
    instruction_text_draw = ImageDraw.Draw(instruction_image)

    word_text = colors_text[word]

    x_size, y_size = get_text_dimensions(text_string=word_text,
                                         font=instruction_font,
                                         obj=instruction_text_draw)
    image_middle_x = TEXT_SIZE[0] / 2 - x_size / 2
    image_middle_y = TEXT_SIZE[1] / 2 - y_size / 2
    instruction_text_draw.text(xy=(image_middle_x, image_middle_y),
                               text=word_text,
                               font=instruction_font,
                               fill=colors_rgb[color],
                               align="center")

    instruction_image.save('../images/Торможение/' + f"{word}{color}.png", format="PNG")
