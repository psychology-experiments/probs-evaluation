from abc import ABC, abstractmethod
import csv
import itertools
from typing import List, Optional, Tuple, Dict
from random import choice, randrange


# TODO: проверить, что во всех зондах есть проверка, что правильный ответ - правильный

class AbstractProbeInformationHandler(ABC):
    @abstractmethod
    def next_probe(self) -> None:
        pass

    @abstractmethod
    def get_press_correctness(self, pressed_key_name: str) -> bool:
        pass

    @abstractmethod
    def prepare_for_new_task(self) -> None:
        pass


class ProbeInformationHandler(AbstractProbeInformationHandler):
    def __init__(self, probes: List[str]):
        if not probes:
            raise ValueError("Empty Probe is prohibited")

        if len(probes) != len(set(probes)):
            not_unique_probes_error_message = f"Every probe must be unique.\n\
                                                But there are {len(probes) - len(set(probes))} repeats in probes"
            raise ValueError("Probes must be unique!", not_unique_probes_error_message)

        self.current_probe_idx: Optional[int] = None
        self.probes: List[str] = probes

    def next_probe(self):
        self.current_probe_idx = choice(range(len(self.probes)))

    def get_press_correctness(self, pressed_key_name: str) -> bool:
        raise NotImplementedError

    def prepare_for_new_task(self):
        pass


class ProbeInformationMapper(ProbeInformationHandler):
    def __init__(self,
                 probes: List[str],
                 answers: List[str],
                 custom_choice_rule: Optional[str] = None):
        super().__init__(probes)

        if len(probes) != len(answers):
            not_enough_answers_error_message = f"Every probe must have the answer.\n\
                                                 But there are {len(probes)} probes and {len(answers)} answers"
            raise ValueError(not_enough_answers_error_message)

        self.answers: List[str] = answers
        self._custom_choice_rule = custom_choice_rule

        if custom_choice_rule == "Switch":
            times_repeat = 2  # по умолчанию дважды каждый стимул берётся из одной группы
            black = ((0, 1, 4, 5),) * times_repeat
            blue = ((2, 3, 6, 7),) * times_repeat
            self._right_sequence = itertools.cycle(black + blue)
        elif self._custom_choice_rule == "Inhibition":
            # to ensure that congruent word and color are shown in 1/6 ratio
            self._ratio = [0] * 5 + [1]

            congruent_probes = [idx for idx, probe in enumerate(probes) if probe[0] == probe[1]]
            incongruent_probes = [idx for idx, probe in enumerate(probes) if probe[0] != probe[1]]
            self._probes_groups = (incongruent_probes, congruent_probes)

    def get_press_correctness(self, pressed_key_name: str) -> bool:
        return self.answers[self.current_probe_idx] == pressed_key_name

    def next_probe(self):
        if self._custom_choice_rule == "Switch":
            self.current_probe_idx = choice(next(self._right_sequence))
        elif self._custom_choice_rule == "Inhibition":
            group = choice(self._ratio)
            self.current_probe_idx = choice(self._probes_groups[group])
        else:
            super(ProbeInformationMapper, self).next_probe()


class ProbeInformationSequence(ProbeInformationHandler):
    def __init__(self, probes: List[str]):
        super().__init__(probes)

        self.previous_probe_idx: Optional[int] = None

    def next_probe(self):
        self.previous_probe_idx = self.current_probe_idx
        super(ProbeInformationSequence, self).next_probe()

    def get_press_correctness(self, pressed_key_name: str) -> bool:
        if self.previous_probe_idx is None:
            return True

        if pressed_key_name == "right":
            return self.previous_probe_idx == self.current_probe_idx
        elif pressed_key_name == "left":
            return self.previous_probe_idx != self.current_probe_idx
        else:
            raise ValueError(f"Key {pressed_key_name} is prohibited for this UpdateProbe")

    def prepare_for_new_task(self):
        self.previous_probe_idx = None


class Probe:
    def __init__(self,
                 probes: List[str],
                 answers: Optional[List[str]] = None,
                 probe_type: str = "TwoAlternatives"):

        if probe_type == "TwoAlternatives":
            self._information_handler = ProbeInformationMapper(probes, answers)
        elif probe_type == "Update":
            self._information_handler = ProbeInformationSequence(probes)
        elif probe_type == "Switch":
            self._information_handler = ProbeInformationMapper(probes, answers, custom_choice_rule="Switch")
        elif probe_type == "Inhibition":
            self._information_handler = ProbeInformationMapper(probes, answers, custom_choice_rule="Inhibition")
        else:
            raise NotImplementedError(f"{probe_type} is not implemented")

        # prepare ProbeInformationHandler for use, i.e. choose first probe
        self._information_handler.next_probe()

    def get_press_correctness(self, pressed_key_name: str) -> bool:
        return self._information_handler.get_press_correctness(pressed_key_name)

    def next_probe(self):
        self._information_handler.next_probe()

    def get_probe_number(self):
        return self._information_handler.current_probe_idx

    def prepare_for_new_task(self):
        self._information_handler.prepare_for_new_task()


# TODO: change tests to accept Probe as UpdateProbe
UpdateProbe = Probe
