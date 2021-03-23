from abc import ABCMeta, abstractmethod
from collections import namedtuple
from typing import List, Tuple
from pathlib import Path

import numpy as np
from psychopy import core, event, visual

from base import task_presenters


def _ensure_creation_of_element(obj_creation_function: visual.basevisual):
    """
    That function ensure creation of psychopy.visual element (primarily used for visual.ElementArrayStim)
    :param obj_creation_function: visual.basevisual
    :return: function wrapper
    """

    def wrapper(self, position):
        while True:
            try:
                return obj_creation_function(self, position)
            except ValueError:
                pass

    return wrapper


class AbstractTaskView(metaclass=ABCMeta):
    @abstractmethod
    def next_task(self) -> None:
        pass

    @abstractmethod
    def get_data(self) -> dict:
        # TODO: додумать что должно возвращать
        pass

    @abstractmethod
    def finish_trial(self) -> None:
        pass

    @abstractmethod
    def is_trial_finished(self) -> bool:
        pass

    @abstractmethod
    def is_task_finished(self) -> bool:
        pass

    @abstractmethod
    def draw(self, t_to_next_flip: float) -> None:
        pass

    @staticmethod
    def is_valid_click() -> bool:
        return True


class InhibitionTaskView(AbstractTaskView):
    def __init__(self,
                 window: visual.Window,
                 position: Tuple[int, int],
                 stimuli_fp: str,
                 trials_finishing_task: int):
        self._presenter = task_presenters.InhibitionTask(fp=stimuli_fp,
                                                         trials_before_task_finished=trials_finishing_task)

        # TODO: заменить на нормальные изображения
        self._current_task: visual.ImageStim = visual.ImageStim(window, size=(600, 600 * 1.0784), pos=position)

        self._is_next_task = False  # TODO: подумать здесь ли место этой логике

    def __len__(self):
        return len(self._presenter)

    def finish_trial(self) -> None:
        self._is_next_task = True

    def next_task(self):
        self._is_next_task = False
        self._current_task.image = self._presenter.next_subtask()

    def is_trial_finished(self):
        return self._is_next_task

    def is_task_finished(self) -> bool:
        return self._presenter.is_task_finished()

    def get_data(self):
        return

    def draw(self, t_to_next_flip):
        self._current_task.draw()


class UpdateTaskView(AbstractTaskView):
    def __init__(self,
                 window: visual.Window,
                 position: Tuple[int, int],
                 stimuli_fp: str,
                 word_show_time: float,
                 blocks_finishing_task: int,
                 possible_task_sequences: Tuple[int, ...],
                 ):
        self._word_presenter_timer = core.CountdownTimer()
        self._word_show_time = word_show_time
        self._ask_to_name_words = False
        self._is_next_task = False  # TODO: подумать здесь ли место этой логике
        self._reset_word_timer = False

        if any(not isinstance(sequence, int) for sequence in possible_task_sequences):
            raise ValueError('For task "Обновление" sequence must include only int groups')

        self._presenter = task_presenters.UpdateTask(stimuli_fp=stimuli_fp,
                                                     possible_sequences=possible_task_sequences,
                                                     blocks_before_task_finished=blocks_finishing_task)

        self._word_stimuli: visual.TextStim = visual.TextStim(win=window,
                                                              pos=position,
                                                              text="",
                                                              color="black")
        self._example_stimuli: visual.TextStim = visual.TextStim(win=window,
                                                                 pos=position,
                                                                 text="",
                                                                 color="black")
        self._answer_time_text: visual.TextStim = visual.TextStim(win=window,
                                                                  pos=position,
                                                                  text="Назовите запомненные слова",
                                                                  color="black")

    def __len__(self):
        return len(self._presenter)

    def is_trial_finished(self) -> bool:
        # Если на экране слово отоброжается - пример ещё не закончен
        if self._word_presenter_timer.getTime() > 0 or self._reset_word_timer:
            return False

        # если не было команды для перехода к следующей задаче - пример ещё не решен
        return self._is_next_task

    def is_task_finished(self) -> bool:
        return self._presenter.is_task_finished()

    def is_valid_click(self) -> bool:
        return self._word_presenter_timer.getTime() <= 0

    def get_data(self):
        return

    def finish_trial(self) -> None:
        self._is_next_task = True

        # TODO: нужно или поправку внести или переделать, так как меньше, чем 750 мс предъявление
        if not self._presenter.is_answer_time():
            self._reset_word_timer = True

    def next_task(self):
        self._is_next_task = False
        self._presenter.next_subtask()

        if not self._presenter.is_answer_time():
            self._word_stimuli.text = self._presenter.word
            self._example_stimuli.text = self._presenter.example

    def draw(self, next_flip_time):
        if self._reset_word_timer:
            self._reset_word_timer = False
            self._word_presenter_timer.reset(t=self._word_show_time + next_flip_time)

        if self._word_presenter_timer.getTime() > 0:
            self._word_stimuli.draw()
            # print(self._timer.getTime())
            return

        if not self._presenter.is_answer_time():
            self._example_stimuli.draw()
        else:
            self._answer_time_text.draw()


SuitFeatures = namedtuple("SuitFeatures", "color shape figures_place")


class WisconsinTestTaskView(AbstractTaskView):

    def __init__(self,
                 window: visual.Window,
                 position: Tuple[int, int],
                 image_path_dir: str,
                 mouse: event.Mouse,
                 trials_finishing_task: int,
                 rule_changes_finishing_task: int,
                 max_streak: int = 8,
                 feedback_time: float = 1.0):
        self._win = window
        self._center_position_x, self._center_position_y = position
        self._test_presenter = task_presenters.WisconsinTest(max_streak=max_streak,
                                                             max_trials=trials_finishing_task,
                                                             max_rules_changed=rule_changes_finishing_task)

        self._shapes: List[visual.basevisual] = []
        self._load_shapes(path=image_path_dir)
        self._calculate_correct_size()

        self._cards = []
        self._suit_elements = []

        self._feedback_text = visual.TextStim(self._win, pos=self.feedback_text_pos, height=30)
        self._feedback_countdown = core.CountdownTimer(start=feedback_time)
        self._mouse = mouse
        self._clock = core.Clock()

        self._fill_cards()
        self._target_card = self._cards[-1]
        self._presentation_cards = self._cards[:-1]
        self._chosen_card = None

        self._next_trial()

        self._show_feedback = False
        self._trial_start = None
        self._answer_time = None
        self._is_next_task = False  # TODO: подумать здесь ли место этой логике

    def _load_shapes(self, path: str) -> None:
        # TODO: ПОМЕНЯТЬ ТРЕУГОЛЬНИК НА КРЕСТ
        shapes = ("circle", "square", "star", "triangle")
        image_dir_path = Path(path)

        for shape in shapes:
            image_path = image_dir_path / f"{shape}.png"
            self._shapes.append(image_path)

    def _calculate_correct_size(self):
        self.card_x = self._win.size[1] * 0.1  # horizontal space between choice cards
        self.card_w = self._win.size[1] * 0.1  # card width
        self.card_h = self._win.size[1] * 0.15  # card height
        self.card_y = -self.card_h * 0.33 + self._center_position_y  # vertical position of choice cards
        self.target_pos = (0, self.card_y - self.card_h * 1.75)  # position of the target card
        self.feedback_text_pos = (0, (self.target_pos[1] + self.card_y) / 2)
        self.colors = ['red', 'green', 'blue', 'orange']
        self.suit_pos = [
            # one symbol
            [
                [0, 0],
                [np.nan, np.nan],
                [np.nan, np.nan],
                [np.nan, np.nan]
            ],
            # two symbols
            [
                [0, self.card_h / 4.0],
                [0, -self.card_h / 4.0],
                [np.nan, np.nan],
                [np.nan, np.nan]],
            # three symbols
            [
                [-self.card_w / 4.0, self.card_h / 3.0],
                [-self.card_w / 4.0, -self.card_h / 3.0],
                [self.card_w / 4.0, 0], [np.nan, np.nan]
            ],
            # four symbols
            [
                [-self.card_w / 4.0, self.card_h / 4.0],
                [-self.card_w / 4.0, -self.card_h / 4.0],
                [self.card_w / 4.0, -self.card_h / 4.0],
                [self.card_w / 4.0, self.card_h / 4.0]
            ]
        ]

    def _fill_cards(self):
        choice_cards = 4
        card_positions = [((i - 1.5) * (self.card_x + self.card_w), self.card_y)
                          for i in range(choice_cards)] + [self.target_pos]

        for position in card_positions:
            card = self._create_card(position)
            suit_elements = self._create_suit(position)

            self._cards.append(card)
            self._suit_elements.append(suit_elements)

    def _create_card(self, position):
        x, y = position
        card = visual.Rect(self._win,
                           width=self.card_w, height=self.card_h,
                           fillColor='white', lineColor='black',
                           pos=(x + self._center_position_x, y),
                           interpolate=False,
                           )
        return card

    @_ensure_creation_of_element
    def _create_suit(self, position):
        x, y = position
        suit = visual.ElementArrayStim(self._win,
                                       nElements=4,
                                       sizes=self.card_h / 4,
                                       fieldPos=(x + self._center_position_x, y),
                                       elementTex=None,
                                       elementMask=None,
                                       )
        return suit

    def _is_card_features_with_target_ambiguous(self, card_features, previous_rule, current_rule):
        return card_features[previous_rule] == self._target_card_features[previous_rule] \
               and card_features[current_rule] == self._target_card_features[current_rule]

    def _next_trial(self):
        current_rule = self._test_presenter.rule
        previous_rule = self._test_presenter.previous_rule

        self._trial_start = None
        self._answer_time = None
        self._show_feedback = False

        choice_cards = 4
        stimuli_features_randomization = [np.random.permutation(choice_cards) for _ in self._cards[:-1]]
        presentation_chosen_features = np.array(stimuli_features_randomization).T.tolist()
        self._target_card_features = list(np.random.randint(4, size=choice_cards))
        self._presentation_cards_features = [features[:-1] for features in presentation_chosen_features]
        all_features = presentation_chosen_features + [self._target_card_features]
        all_features = [SuitFeatures(*features[:-1]) for features in all_features]

        if self._test_presenter.is_first_trial_after_rule_change():
            for idx, card_features in enumerate(all_features[:-1]):
                # TODO: убедиться, что действительно не может совпасть правило (код работает,
                #  но надо подумать всё ли ловит)
                if self._is_card_features_with_target_ambiguous(card_features=card_features,
                                                                previous_rule=previous_rule,
                                                                current_rule=current_rule):
                    card_to_switch_idx = np.random.choice(a=[card_idx
                                                             for card_idx in range(choice_cards)
                                                             if card_idx != idx])

                    card_to_switch = list(all_features[card_to_switch_idx])
                    card_features = list(card_features)

                    card_to_switch[previous_rule], card_features[previous_rule] = \
                        card_features[previous_rule], card_to_switch[previous_rule]
                    all_features[idx] = SuitFeatures(*card_features)
                    all_features[card_to_switch_idx] = SuitFeatures(*card_to_switch)
                    break

        for suit, card_features in zip(self._suit_elements, all_features):
            suit.setColors(self.colors[card_features.color])
            suit.setTex(self._shapes[card_features.shape])
            suit.setXYs(self.suit_pos[card_features.figures_place])

    def finish_trial(self) -> None:
        if self._chosen_card is not None:
            self._check_answer(chosen_card_idx=self._chosen_card)
            self._mouse.setPos(newPos=self.target_pos)
            self._is_next_task = True
            self._chosen_card = None

    def is_trial_finished(self):
        if not self._is_next_task:
            return False

        if self._show_feedback:
            return False

        self._is_next_task = False
        return True

    def is_task_finished(self) -> bool:
        return self._test_presenter.is_task_finished()

    def get_data(self):
        return

    def prepare_mouse(self):
        self._mouse.setPos(newPos=self.target_pos)
        self._mouse.setVisible(True)

    def next_task(self):
        self._next_trial()
        self._test_presenter.next_subtask()

    def _prepare_feedback(self, is_correct_answer):
        if is_correct_answer:
            self._feedback_text.text = u"ВЕРНО"
            self._feedback_text.color = "green"
        else:
            self._feedback_text.text = u"НЕВЕРНО"
            self._feedback_text.color = "red"

    def _check_answer(self, chosen_card_idx):
        chosen_card = task_presenters.WisconsinCard(self._presentation_cards_features[chosen_card_idx])
        target_card = task_presenters.WisconsinCard(self._target_card_features)

        answer_correctness = self._test_presenter.is_correct(chosen_card=chosen_card, target_card=target_card)

        self._prepare_feedback(is_correct_answer=answer_correctness)

        self._feedback_countdown.reset()
        self._show_feedback = True

    def is_valid_click(self) -> bool:
        is_valid_click = False
        if not self._show_feedback:
            for idx, card in enumerate(self._presentation_cards):
                if self._mouse.isPressedIn(shape=card, buttons=[0]):
                    self._answer_time = self._clock.getTime()
                    self._chosen_card = idx
                    is_valid_click = True
                    break

        return is_valid_click

    def draw(self, t_to_next_flip):  # TODO: Возможно стоит добавить использование времени
        if self._show_feedback:
            if self._feedback_countdown.getTime() >= 0:
                self._feedback_text.draw()
            else:
                self._show_feedback = False

        for card, suit in zip(self._cards, self._suit_elements):
            card.draw()
            suit.draw()

        if self._trial_start is None:
            self._trial_start = self._clock.getTime()

    def get_trial_data(self):
        if self._answer_time is not None and self._trial_start is not None:
            trial_data = dict(rt=self._answer_time - self._trial_start,
                              # TODO: при изменении правила, возвращает новое правило, а не информацию о последнем
                              # и говорит, что ответ неправильный, когда он правильный
                              rule=self._test_presenter.rule_name,
                              correctness=int(self._test_presenter.streak > 0))
            return trial_data
