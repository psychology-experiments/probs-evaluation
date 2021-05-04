import csv
from itertools import cycle
import os
from typing import Optional, Iterator, Dict, List

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
    """
    Class used in first part of experiment to get necessary info about participant
    """

    def __init__(self):
        info = dict(ФИО="", Возраст="", Пол=["Ж", "М"])
        self._dialog = gui.DlgFromDict(dictionary=info, order=["ФИО", "Возраст", "Пол"])
        self.filled_info = self._dialog.dictionary

    @property
    def is_canceled(self):
        return not self._dialog.OK


class ParticipantInfoLinker:
    """
    Class used in second part of experiment to link data from first and second part of experiment
    """

    def __init__(self, participants_info_fp: str):
        self._participant_info_to_save_by = []
        self._participant_name_ids = []
        self._participants_info_to_show = self._load_info(participants_info_fp)
        info = dict(Испытуемый=self._participants_info_to_show)
        dialog_title = "Выберите имя испытуемого из первой части эксперимента"
        self._filled_info = gui.DlgFromDict(dictionary=info, title=dialog_title).dictionary

        index = self._participants_info_to_show.index(self._filled_info["Испытуемый"])
        participant_wm_file = self._participant_info_to_save_by[index]
        participant_info = self._extract_participant_info(self._participant_name_ids[index])
        participant_info.update(dict(wm_file_name=participant_wm_file))
        self.filled_info = participant_info

    def _load_info(self, fp) -> List[str]:
        with open(fp, mode="r", encoding="UTF-8") as csv_file:
            csv_reader = csv.DictReader(csv_file)

            only_finished_first_part_to_choose_from = []
            for row in csv_reader:
                name_age_gender, wm_file, insight_file = row["participant"], row["WM_name"], row["Insight_name"]

                self._check_data(name_age_gender, wm_file)

                if insight_file != "":
                    continue

                only_finished_first_part_to_choose_from.append(f"{name_age_gender} (файл {wm_file})")
                self._participant_info_to_save_by.append(wm_file)
                self._participant_name_ids.append(name_age_gender)
        return only_finished_first_part_to_choose_from

    @staticmethod
    def _check_data(name, wm_file):
        if name == "" or wm_file == "":
            raise ValueError(f"В файле с идентификторами испытуемых ошибка:\n"
                             f"должны быть заполнены первый и второй столбец, а вместо этого\n"
                             f"[{name}, {wm_file}]")

    @staticmethod
    def _extract_participant_info(name_age_gender):
        name, age, gender = name_age_gender.rsplit(maxsplit=2)
        return dict(ФИО=name, Возраст=age, Пол=gender)
