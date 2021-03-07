import logging
import os
import sys

from PIL import Image

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

START_FOLDER = "../images"
WIDTH = 100


def get_name_and_ext(name):
    return os.path.splitext(os.path.basename(name))


def save_as_png(image: Image,
                width: int,
                convert_from: str = "jpg",
                convert_to: str = "png"):
    file_path = image.filename
    dir_path = os.path.dirname(file_path)
    name, extension = get_name_and_ext(file_path)

    new_height = int(width * image.height / image.width)

    resized_image = image.resize((width, new_height), Image.ANTIALIAS)
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
    for file in files:
        fp = os.path.join(address, file)
        save_as_png(Image.open(fp),
                    width=WIDTH)


# TODO: падает качество при уменьшении. Сильно
# DIRECTORY_TO_CHANGE_SIZE = "../images/Tower of London"
# for file in os.listdir(DIRECTORY_TO_CHANGE_SIZE):
#     fp = os.path.join(DIRECTORY_TO_CHANGE_SIZE, file)
#     save_as_png(Image.open(fp),
#                 width=int(1920 * 0.8),
#                 convert_from="png")
