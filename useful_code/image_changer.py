import logging
import os
import sys
from typing import Optional

from PIL import Image

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

START_FOLDER = "../images"
WIDTH = 128
HEIGHT = 128


def get_name_and_ext(name):
    return os.path.splitext(os.path.basename(name))


def save_as_png(image: Image,
                width: Optional[int] = None,
                height: Optional[int] = None,
                convert_from: str = "jpg",
                convert_to: str = "png"):
    file_path = image.filename
    dir_path = os.path.dirname(file_path)
    name, extension = get_name_and_ext(file_path)

    if height is None and width is None:
        raise ValueError

    if height is None:
        height = int(width * image.height / image.width)

    if width is None:
        width = int(height * image.width / image.height)

    resized_image = image.resize((width, height), Image.ANTIALIAS)
    resized_image.save(f"{dir_path}/{name}.{convert_to}", convert_to)
    resized_image.close()
    image.close()

    if extension == convert_from:
        os.remove(path=file_path)
    elif extension.endswith(convert_to):
        pass
    else:
        raise ValueError(f"Unaccounted extension: {extension}")

    logging.info(f"File {name}{extension} converted")
    return name


for address, _, files in os.walk(START_FOLDER):
    if address not in ("../images\Обновление", "../images\Переключение"):
        continue
    for file in files:
        fp = os.path.join(address, file)

        save_as_png(Image.open(fp),
                    width=WIDTH,
                    height=HEIGHT)

# TODO: падает качество при уменьшении. Сильно
# DIRECTORY_TO_CHANGE_SIZE = "../images/Tower of London"
# for file in os.listdir(DIRECTORY_TO_CHANGE_SIZE):
#     fp = os.path.join(DIRECTORY_TO_CHANGE_SIZE, file)
#     save_as_png(Image.open(fp),
#                 height=512,
#                 convert_from="png")
