from typing import Optional

from psychopy.hardware import keyboard
from psychopy import core, visual


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


class InstructionText:
    def __init__(self, window: visual.Window, skip: bool):
        self._win = window
        self._image_stimulus = visual.TextStim(win=self._win, color="black", height=30, wrapWidth=1000)
        self._keyboard = keyboard.Keyboard()
        self._skip = skip

    def show(self, text: Optional[str]) -> None:
        """
        Show instruction if there is any. Otherwise do nothing.

        :param text: text of instruction
        :return:
        """
        if text is None or self._skip:
            return

        self._image_stimulus.text = text
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
