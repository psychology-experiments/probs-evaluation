from abc import ABC, abstractmethod
import csv
from pathlib import Path
from random import choice, shuffle
from typing import List, Optional, Tuple, Iterator, Union


class Task(ABC):
    @abstractmethod
    def next_subtask(self):
        pass

    @abstractmethod
    def new_task(self):
        pass


class UpdateTask(Task):
    def __init__(self,
                 stimuli_fp: str,
                 possible_sequences: Tuple[int, ...],
                 blocks_before_task_finished: int):

        if any(group < 1 for group in possible_sequences):
            raise ValueError("Sequence of groups with length less than one are prohibited")

        self._all_examples: List[str, ...] = []
        self._all_words: List[str, ...] = []

        self._possible_sequences: Tuple[int, ...] = possible_sequences
        self._before_answer: int = self._choose_group_size()
        self._blocks_before_task_finished: int = blocks_before_task_finished
        self._blocks_finished: int = 0
        self._previous_trial_was_answer: bool = False

        self.example: Optional[str] = None
        self.word: Optional[str] = None

        self._load_stimuli(stimuli_fp)
        self._length = len(self._all_examples)

        shuffle(self._all_examples)
        shuffle(self._all_words)

        self._examples_sequence: Iterator[str] = iter(self._all_examples)
        self._words_sequence: Iterator[str] = iter(self._all_words)

        self._task_was_initialized_before_first_trial = False

    def __len__(self):
        return self._length

    def _load_stimuli(self, stimuli_fp):
        with open(stimuli_fp, mode="r", encoding="UTF-8") as fin:
            csv_file = csv.DictReader(fin, fieldnames=["examples", "words"])

            next(csv_file)  # ignore line with headers
            for row in csv_file:
                self._all_examples.append(row["examples"])
                self._all_words.append(row["words"])

    def _choose_group_size(self):
        return choice(self._possible_sequences) + 1

    def is_answer_time(self):
        return self._before_answer == 0

    def is_task_finished(self) -> bool:
        return self._blocks_before_task_finished == self._blocks_finished

    def _is_task_first_trial(self):
        return self.example is None or self.word is None

    def next_subtask(self) -> None:
        if not self._task_was_initialized_before_first_trial:
            raise RuntimeError("Call to next_subtask before new_task call is prohibited on first task")

        if self.is_answer_time():
            self._blocks_finished += 1
            self._before_answer = self._choose_group_size()

        if self.is_task_finished():
            return

        self._before_answer -= 1
        if not self.is_answer_time():
            self.example = next(self._examples_sequence)
            self.word = next(self._words_sequence)
            self._length -= 1

    def new_task(self):
        if not self.is_task_finished() and self._task_was_initialized_before_first_trial:
            raise RuntimeError("Call to new_task is prohibited for unfinished task")

        if not self._task_was_initialized_before_first_trial:
            self._task_was_initialized_before_first_trial = True
            return

        self._blocks_finished = 0


class InhibitionTask(Task):
    def __init__(self,
                 fp: str,
                 trials_before_task_finished: int):
        stimuli = self._load_stimuli(fp)

        if not stimuli:
            raise ValueError(f"Did not find png files in {fp}")

        self._length = len(stimuli)
        self._trials_before_task_finished = trials_before_task_finished
        self._trial = 0

        shuffle(stimuli)
        self._unused_stimuli = iter(stimuli)

        self._the_first_trial = True

    def __len__(self):
        return self._length

    @staticmethod
    def _load_stimuli(fp) -> List[str]:
        return [image_path.absolute().as_posix() for image_path in Path(fp).glob(pattern="*.png")]

    def next_subtask(self) -> Optional[str]:
        self._trial += 1

        if self._is_more_trials_than_subtasks():
            raise RuntimeError("Call to next_subtask on finished task is prohibited. Call new_task before")

        if self.is_task_finished():
            return

        self._length -= 1
        image_path = next(self._unused_stimuli)
        return image_path

    def is_task_finished(self) -> bool:
        return self._trial == self._trials_before_task_finished + 1

    def _is_more_trials_than_subtasks(self):
        return self._trial > self._trials_before_task_finished + 1

    def new_task(self):
        if self._the_first_trial:
            self._the_first_trial = False
            return

        if not self.is_task_finished():
            raise RuntimeError("Call to new task is prohibited for unfinished task")

        self._trial = 0


class WisconsinCard:
    def __init__(self, features):
        self._features = tuple(features)

    def get_rule_feature(self, rule):
        return self._features[rule]


class WisconsinTest(Task):  # SwitchTask
    def __init__(self, max_streak: int, max_trials: Optional[int], max_rules_changed: Optional[int]):
        self._max_streak: int = max_streak
        self._rules: Tuple[str, ...] = ("color", "shape", "quantity")
        self.previous_rule: Optional[int] = None
        self.rule: Optional[int] = None
        self.rule_name: Optional[str] = None
        self._first_trial_after_rule_change: bool = False
        self.streak: int = 0
        self._trial_correctness: Optional[bool] = None

        if max_trials is None:
            max_trials = float("inf")
        self._max_trials: Union[int, float] = max_trials
        self._trial: int = 0

        if max_rules_changed is None:
            max_rules_changed = float("inf")
        self._max_rules_changed: Union[int, float] = max_rules_changed
        self._rules_changed: int = 0

        self._the_first_trial = True

    def _choose_rule(self) -> None:
        possible_rules = list(range(len(self._rules)))

        if self.rule is not None:
            self.previous_rule = self.rule
            possible_rules.remove(self.rule)

        self.rule = choice(possible_rules)
        self.rule_name = self._rules[self.rule]

    def is_correct(self, chosen_card: WisconsinCard, target_card: WisconsinCard) -> bool:
        if self._trial_correctness is None:
            chosen_card_feature = chosen_card.get_rule_feature(self.rule)
            target_card_feature = target_card.get_rule_feature(self.rule)
            self._trial_correctness = chosen_card_feature == target_card_feature
            return self._trial_correctness

        raise ValueError("WisconsinTest must be asked about correctness only once per trial")

    def is_first_trial_after_rule_change(self) -> bool:
        return self._first_trial_after_rule_change

    def _is_finished_by_trial(self):
        return self._trial == self._max_trials + 1

    def _is_finished_by_rule_change(self):
        return self._rules_changed == self._max_rules_changed

    def _next_subtask_with_new_rule(self):
        self.streak = 0
        self._first_trial_after_rule_change = True
        self._choose_rule()

    def _update_streak(self):
        if self._trial_correctness:
            self.streak += 1
            return

        self.streak = 0

    def is_task_finished(self) -> bool:
        return self._is_finished_by_trial() or self._is_finished_by_rule_change()

    def next_subtask(self) -> None:
        if self._trial_correctness is None and not self.is_task_finished():
            raise RuntimeError("WisconsinTest must be used in next sequence: is_correct, next_task")

        if self._first_trial_after_rule_change:
            self._first_trial_after_rule_change = False

        self._update_streak()
        self._trial_correctness = None

        self._trial += 1
        if self.streak == self._max_streak:
            self._rules_changed += 1

            if not self.is_task_finished():
                self._next_subtask_with_new_rule()

    def new_task(self):
        if not self.is_task_finished() and not self._the_first_trial:
            raise RuntimeError("WisconsinTest new_task must be called on finished task")

        if self._the_first_trial:
            self._the_first_trial = False

        self._next_subtask_with_new_rule()
        self._trial = 0
        self._rules_changed = 0
