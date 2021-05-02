from typing import NamedTuple

from PIL import Image, ImageFont, ImageDraw

INSTRUCTION_SIZE = (1920, 1080)
INSTRUCTION_COLOR_MODE = "RGBA"
BASE_COLOR = (0, 0, 0, 0)
INSTRUCTION_COLOR = (0, 0, 0)

INSTRUCTION_TEXT_FONT_INFO = dict(font='C:/Windows/fonts/Arial.ttf', size=25)

TASK_INSTRUCTIONS_FP = "instructions/task instructions.txt"
PROBE_INSTRUCTIONS_WM_FP = "instructions/probe WM instructions.txt"
GENERAL_INSTRUCTIONS_FP = "instructions/general instructions.txt"

SAVE_TASK_INSTRUCTIONS_FP = "../images/Инструкции/Задания/WM/"
SAVE_PROBE_INSTRUCTIONS_WM_FP = "../images/Инструкции/Зонды/WM/"
SAVE_GENERAL_INSTRUCTIONS_FP = "../images/Инструкции/Общие/"


class InstructionPart(NamedTuple):
    content: str
    content_type: str


def get_text_dimensions(text_string, font, obj):
    # https://stackoverflow.com/a/46220683/9263761
    ascent, descent = font.getmetrics()

    text_width = font.getmask(text_string).getbbox()[2]
    text_height = font.getmask(text_string).getbbox()[3] + descent

    print("new", text_width, text_height)

    text_width, text_height = obj.textsize(text_string, font)
    print("old", text_width, text_height)
    return text_width, text_height


def create_instruction_image(instruction_name, instruction_info, fp):
    shift_multiplier = 1.15

    instruction_image = Image.new(INSTRUCTION_COLOR_MODE, INSTRUCTION_SIZE, BASE_COLOR)
    instruction_font = ImageFont.truetype(**INSTRUCTION_TEXT_FONT_INFO)
    instruction_text_draw = ImageDraw.Draw(instruction_image)

    if len(instruction_info) == 1:
        use_screen_center = True
    else:
        y = int(INSTRUCTION_SIZE[1] * 0.03) * 4.5
        use_screen_center = False

    screen_middle_x = INSTRUCTION_SIZE[0] // 2
    screen_middle_y = INSTRUCTION_SIZE[1] // 2

    for part in instruction_info:
        if part.content_type == "text":
            x_size, y_size = get_text_dimensions(text_string=part.content,
                                                 font=instruction_font,
                                                 obj=instruction_text_draw)

            if use_screen_center:
                y = screen_middle_y - y_size // 2

            instruction_text_draw.text(xy=(screen_middle_x - x_size // 2, y),
                                       text=part.content,
                                       font=instruction_font,
                                       fill=INSTRUCTION_COLOR,
                                       align="center")

            y += int(y_size * shift_multiplier)
        elif part.content_type == "img":
            instruction_image_part = Image.open(part.content, mode="r")
            instruction_image_part = instruction_image_part.resize((400, 400), Image.ANTIALIAS)
            x_size, y_size = instruction_image_part.size

            offset = (screen_middle_x - x_size // 2, int(y * 1.1))
            instruction_image.paste(instruction_image_part, offset)

            y += int(y_size * shift_multiplier)
        else:
            raise ValueError(f"Can work only with text and images, get {part.content_type}")
    instruction_image.save(fp + f"{instruction_name}.png", format="PNG")


def _get_instruction_name(line: str):
    line = line.strip()
    if line.endswith(":"):
        return line[:-1]
    raise ValueError(f"Line must have name for instruction, but get {line}")


def _find_tag(line: str):
    if not line.startswith("<"):
        raise ValueError(f"Every line must start with tag, but instead get {line}")

    for idx, symbol in enumerate(line):
        if symbol == ">":
            break
    else:
        raise ValueError(f"Tag was not closed {line}")

    return line[1:idx]


def _get_part(instructions):
    raw_first_line = instructions.readline()

    if raw_first_line == "\n" or raw_first_line == "":
        raise StopIteration

    content_type = _find_tag(raw_first_line)
    close_tag = f"</{content_type}>\n"
    line = raw_first_line[len(content_type) + 2:]

    line_context = []
    while True:
        if line.endswith((close_tag, close_tag[:-1])):
            line = line[:-len(close_tag)]
            line_context.append(line)
            part = InstructionPart(content="".join(line_context),
                                   content_type=content_type)
            return part

        line_context.append(line)
        line = instructions.readline()


def _get_instruction_parts(instructions):
    instruction_parts = []

    while True:
        try:
            part = _get_part(instructions)
            instruction_parts.append(part)
        except StopIteration:
            return instruction_parts


def load_instructions(fp):
    instructions = {}
    with open(fp, mode="r") as fin:
        for line in fin:
            instruction_name = _get_instruction_name(line)
            instruction_parts = _get_instruction_parts(fin)
            instructions[instruction_name] = instruction_parts

    return instructions


def convert_instructions_to_image(instructions_fp, save_folder):
    instructions = load_instructions(instructions_fp)
    for name in instructions:
        instruction = instructions[name]

        create_instruction_image(instruction_name=name,
                                 instruction_info=instruction,
                                 fp=save_folder)


convert_instructions_to_image(TASK_INSTRUCTIONS_FP, SAVE_TASK_INSTRUCTIONS_FP)
convert_instructions_to_image(PROBE_INSTRUCTIONS_WM_FP, SAVE_PROBE_INSTRUCTIONS_WM_FP)
convert_instructions_to_image(GENERAL_INSTRUCTIONS_FP, SAVE_GENERAL_INSTRUCTIONS_FP)

if __name__ == '__main__':
    from random import shuffle
    import os

    from psychopy import visual, event, core

    win = visual.Window(size=INSTRUCTION_SIZE, color="white", units="pix", fullscr=True)
    explanation_message = visual.TextStim(win,
                                          pos=(-win.size[0] * 0.45, 0),
                                          ori=270,
                                          text="Демонстрация результата. Нажатие на ПРОБЕЛ выбирает следующий пример",
                                          color="red")
    images_paths = [os.path.join(SAVE_TASK_INSTRUCTIONS_FP, fp) for fp in os.listdir(SAVE_TASK_INSTRUCTIONS_FP)] + \
                   [os.path.join(SAVE_PROBE_INSTRUCTIONS_WM_FP, fp) for fp in
                    os.listdir(SAVE_PROBE_INSTRUCTIONS_WM_FP)] + \
                   [os.path.join(SAVE_GENERAL_INSTRUCTIONS_FP, fp) for fp in os.listdir(SAVE_GENERAL_INSTRUCTIONS_FP)]
    shuffle(images_paths)
    images_paths = iter(images_paths)
    image = visual.ImageStim(win, image=next(images_paths))

    while True:
        if event.getKeys(keyList=["escape"]):
            core.quit()

        if event.getKeys(keyList=["space"]):
            try:
                image.image = next(images_paths)
            except StopIteration:
                core.quit()

        explanation_message.draw()
        image.draw()
        win.flip()
