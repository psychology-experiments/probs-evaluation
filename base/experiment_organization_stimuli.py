from itertools import cycle
import os
from typing import Optional, Iterator, Dict

from psychopy.hardware import keyboard
from psychopy import core, gui, visual


class InstructionImage:
    def __init__(self, window: visual.Window, skip: bool):
        self._win = window
        self._image_stimulus = visual.ImageStim(win=self._win)
        self._keyboard = keyboard.Keyboard()
        self._skip = skip

    def show(self, path: Optional[str]) -> None:
        """
        Show instruction if there is any. Otherwise do nothing.

        :param path: path to instruction image file
        :return:
        """
        if path is None or self._skip:
            return

        self._image_stimulus.image = path
        self._keyboard.clearEvents()

        while True:
            self._image_stimulus.draw()
            self._win.flip()

            keys = self._keyboard.getKeys(keyList=["escape", "space"])

            if "escape" in keys:
                core.quit()

            if "space" in keys:
                break


class GeneralInstructions:
    def __init__(self,
                 fp: str,
                 window: visual.Window,
                 skip: bool):
        self._win = window
        self._images_fp = self._find_images(fp)
        self._image_stimulus = visual.ImageStim(win=self._win)
        self._keyboard = keyboard.Keyboard()
        self._skip = skip

    @staticmethod
    def _find_images(fp: str) -> Iterator[str]:
        images_fp = [os.path.join(fp, image)
                     for image in os.listdir(fp)
                     if image.endswith(".png")]

        if not images_fp:
            raise ValueError(f"There is not png images in the directory {fp}")

        return cycle(images_fp)

    def show(self) -> None:
        """
        Show instruction if there is any. Otherwise do nothing.

        :return:
        """
        if self._skip:
            return

        self._image_stimulus.image = next(self._images_fp)
        self._keyboard.clearEvents()

        while True:
            self._image_stimulus.draw()
            self._win.flip()

            keys = self._keyboard.getKeys(keyList=["escape", "space"])

            if "escape" in keys:
                core.quit()

            if "space" in keys:
                break


class SingleMousePress:  # TODO: добавить в код main или убрать
    def __init__(self, mouse):
        self._released = False
        self._mouse = mouse

    def is_press(self):
        left_button_pressed = self._mouse.isPressed()[0]

        self._released = not left_button_pressed

        return self._mouse.isPressed()


class EndMessage:
    def __init__(self,
                 window: visual.Window,
                 end_phrase: str):
        from psychopy import sound
        self._win = window
        self._end_message = visual.TextStim(window,
                                            color="black",
                                            height=40,
                                            wrapWidth=window.size[0] * 0.9)

        self._end_phrase = sound.Sound(value=end_phrase)
        self._timer = core.CountdownTimer()

    @staticmethod
    def _show_time(clock: core.Clock):
        total_seconds = clock.getTime()
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        return f"{minutes:02} минут {seconds:.2f} секунд"

    def show(self,
             time_to_show: float,
             experiment_clock: core.Clock):
        self._timer.reset(time_to_show)
        self._end_phrase.play()

        while self._end_phrase.status != -1 or self._timer.getTime() >= 0:
            self._end_message.text = f"Спасибо за участие!\nЭксперимент шёл: {self._show_time(experiment_clock)}"
            self._end_message.draw()
            self._win.flip()


class ParticipantInfoGetter:
    def __init__(self):
        info = dict(ФИО="", Возраст="", Пол=["Ж", "М"])
        self._filled_info = gui.DlgFromDict(dictionary=info, order=["ФИО", "Возраст", "Пол"]).dictionary

    def get_info(self) -> Dict[str, str]:
        return self._filled_info
