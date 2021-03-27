import itertools
from collections import Counter
from random import choice, choices, randrange
from pathlib import Path
from typing import Dict, Iterator, Tuple, Union

import pytest

from base import task_presenters


class TestUpdateTask:
    TRIALS_TO_CONCLUDE = 15
    DEFAULT_STIMULI_FP = "test_files/tables/test_tasks.csv"
    DEFAULT_STIMULI_SHORT_FP = "test_files/tables/test_tasks_short.csv"

    @pytest.fixture
    def default_stimuli_quantity(self) -> int:
        with open(self.DEFAULT_STIMULI_FP, mode="r") as fin:
            fin.readline()  # skip header
            stimuli = len(fin.readlines())

        return stimuli

    @pytest.fixture
    def task_settings(self) -> Dict[str, Union[str, Tuple[int, ...], int]]:
        return dict(stimuli_fp=self.DEFAULT_STIMULI_FP,
                    possible_sequences=(3, 4),
                    blocks_before_task_finished=5)

    @pytest.fixture
    def default_task(self, task_settings: dict) -> task_presenters.UpdateTask:
        return task_presenters.UpdateTask(**task_settings)

    @staticmethod
    def iterate_over_all_stimuli(task: task_presenters.UpdateTask) -> Iterator[Tuple[str, str]]:
        """Implemented this way to ensure that even if is_task_finished work incorrectly other test do not crash"""
        task.new_task()
        while True:
            try:
                task.next_subtask()

                if task.is_task_finished():
                    task.new_task()
                elif not task.is_answer_time():
                    yield task.example, task.word

            except StopIteration:
                break

    @pytest.mark.parametrize("sequences", [(0,), (3, 4, -1), (5, 7, 9, 0)])
    def test_error_on_zero_and_negative_sequence(self, sequences: Tuple[int, ...], task_settings):
        task_settings["possible_sequences"] = sequences
        with pytest.raises(ValueError, match=r"Sequence of groups with length less than one are prohibited"):
            task_presenters.UpdateTask(**task_settings)

    def test_no_error_on_call_to_new_task_on_first_trial(self, default_task):
        try:
            default_task.new_task()
        except RuntimeError:
            pytest.fail("Raised RuntimeError on first trial for the task")

    def test_error_on_call_to_new_task_for_unfinished_task(self, default_task):
        default_task.new_task()
        default_task.next_subtask()
        with pytest.raises(RuntimeError, match="Call to new_task is prohibited for unfinished task"):
            default_task.new_task()

    def test_error_on_next_subtask_before_new_task_for_first_trial(self, default_task):
        with pytest.raises(RuntimeError, match="Call to next_subtask before new_task call is prohibited on first task"):
            default_task.next_subtask()

    @pytest.mark.parametrize("stimulus", ["example", "word"])
    def test_trial_stimuli_change(self, stimulus, default_task):
        task = default_task

        previous_stimulus = None
        results = []
        trials = 0
        task.new_task()
        while not task.is_task_finished():
            task.next_subtask()

            if not task.is_answer_time() and not task.is_task_finished():
                current_stimulus = getattr(task, stimulus)
                results.append(current_stimulus != previous_stimulus)
                previous_stimulus = current_stimulus
                trials += 1

        message = f"UpdateTask's {stimulus} do not change. Changed {sum(results)} times from {trials} trials"
        assert all(results), message

    @pytest.mark.parametrize("method_name", ["is_answer_time", "is_task_finished"])
    def test_is_methods_result_does_not_change_after_n_calls(self, method_name, default_task):
        task = default_task
        method = getattr(task, method_name)

        result = []
        task.new_task()
        while not task.is_task_finished():
            task.next_subtask()
            first_result = method()
            result.append(all(method() == first_result for _ in range(randrange(2, 10))))

        side_effect_error_message = f"UpdateTask's {method_name} return different result after several calls"
        assert all(result), side_effect_error_message

    def test_len_of_new_task(self, default_task, default_stimuli_quantity):
        task = default_task

        all_examples_read = len(task._all_examples)
        all_words_read = len(task._all_words)

        wrong_load_of_stimuli_message = f"UpdateTask get different quantity of words ({all_words_read})" \
                                        f" and equations ({all_examples_read})"
        assert all_words_read == all_examples_read, wrong_load_of_stimuli_message

        current_tasks_number = len(task)
        wrong_qty_of_stimuli = f"UpdateTask has different quantity of read equation ({all_examples_read})," \
                               f"len method result ({current_tasks_number}) and real number of stimuli " \
                               f"({default_stimuli_quantity})"
        assert current_tasks_number == all_examples_read == default_stimuli_quantity, wrong_qty_of_stimuli

    def test_len_changes_on_trial(self, default_task):
        task = default_task
        trials = self.TRIALS_TO_CONCLUDE * 5
        current_tasks_number = len(task) - 1

        error_message = "UpdateTask changed did not change length. It should be " \
                        "{}, but was {}"
        task.new_task()
        for _ in range(trials):
            task.next_subtask()

            if not task.is_answer_time() and not task.is_task_finished():
                assert current_tasks_number == len(task), error_message.format(current_tasks_number, len(task))
                current_tasks_number -= 1

            if task.is_task_finished():
                task.new_task()

    def test_len_does_not_change_on_answer_or_finish(self, default_task):
        task = default_task
        trials = self.TRIALS_TO_CONCLUDE * 5
        current_tasks_number = len(task) - 1

        task.new_task()
        for _ in range(trials):
            task.next_subtask()

            if task.is_answer_time():
                assert current_tasks_number != len(task), "UpdateTask length changed on answer"
            elif task.is_task_finished():
                assert current_tasks_number != len(task), "UpdateTask length changed on finish"
                task.new_task()
            else:
                current_tasks_number -= 1

    @pytest.mark.parametrize("method_name", ["is_answer_time", "is_task_finished"])
    def test_is_method_on_first_trial_is_false(self, method_name, default_task):
        task = default_task
        method = getattr(task, method_name)
        is_answer_time = method()

        message = f"UpdateTask' {method_name} return True on the first trial"
        assert not is_answer_time, message

    def test_is_there_answer_time(self, default_task):
        task = default_task

        was_answer_time = False
        task.new_task()
        while not task.is_task_finished():
            task.next_subtask()

            if task.is_answer_time():
                was_answer_time = True
                break

        message = f"UpdateTask did not have answer time before finish"
        assert was_answer_time, message

    @pytest.mark.parametrize("possible_sequences", [(1,), (3, 4), (2,), (5, 7, 11), (3, 10, 18, 32)])
    def test_is_right_sequence_of_solving_and_remembering(self,
                                                          possible_sequences: Tuple[int, ...],
                                                          task_settings):
        task_settings["possible_sequences"] = possible_sequences
        task = task_presenters.UpdateTask(**task_settings)
        trials = self.TRIALS_TO_CONCLUDE * sum(possible_sequences)

        possible_sequences_set = set(possible_sequences)

        qty_before_answer = 0
        sequence_length_before_answer = set()
        all_sequences_used = False
        task.new_task()
        for trial in range(trials):
            task.next_subtask()

            if task.is_answer_time():
                sequence_length_before_answer.add(qty_before_answer)
                qty_before_answer = 0
            else:
                qty_before_answer += 1

            if sequence_length_before_answer == possible_sequences_set:
                all_sequences_used = True
                break

            if task.is_task_finished():
                qty_before_answer = 0
                task.new_task()

        message = f"For sequence {possible_sequences} were used {sorted(sequence_length_before_answer)}"
        assert all_sequences_used, message

    @pytest.mark.parametrize("possible_sequences", [(1,), (3, 4), (2,), (9, 11, 3), tuple(range(1, 15))])
    def test_is_all_sequences_are_from_possible(self, possible_sequences: Tuple[int], task_settings):
        task_settings["possible_sequences"] = possible_sequences
        task = task_presenters.UpdateTask(**task_settings)
        trials = self.TRIALS_TO_CONCLUDE * sum(possible_sequences)

        qty_before_answer = 0
        sequences_are_in_possible_sequences = []
        task.new_task()
        for trial in range(trials):
            task.next_subtask()

            if task.is_answer_time():
                correctness_of_sequence_length = qty_before_answer in possible_sequences
                sequences_are_in_possible_sequences.append(correctness_of_sequence_length)

                if not correctness_of_sequence_length:
                    break

                qty_before_answer = 0
            else:
                qty_before_answer += 1

            if task.is_task_finished():
                qty_before_answer = 0
                task.new_task()

        message = f"For sequence {possible_sequences} were used sequence with length {qty_before_answer}"
        at_least_one_new_sequence = len(sequences_are_in_possible_sequences) != 0
        assert all(sequences_are_in_possible_sequences) and at_least_one_new_sequence, message

    def test_uniqueness_of_words(self, task_settings):
        task_settings["stimuli_fp"] = self.DEFAULT_STIMULI_SHORT_FP
        task = task_presenters.UpdateTask(**task_settings)

        used_words = set()
        word = None

        duplicated_word_found = False

        all_words_iterator = (word for _, word in self.iterate_over_all_stimuli(task))

        for word in all_words_iterator:
            if word in used_words:
                duplicated_word_found = True
                break

            used_words.add(word)

        message = f"UpdateTask have duplicated words {word}"
        assert not duplicated_word_found, message

    def test_uniqueness_of_equations(self, task_settings):
        task_settings["stimuli_fp"] = self.DEFAULT_STIMULI_SHORT_FP
        task = task_presenters.UpdateTask(**task_settings)

        used_examples = set()
        example = None

        duplicated_example_found = False

        all_examples_iterator = (example for example, _ in self.iterate_over_all_stimuli(task))

        for example in all_examples_iterator:
            if example in used_examples:
                duplicated_example_found = True
                break

            used_examples.add(example)

        message = f"UpdateTask have duplicated examples {example}"
        assert not duplicated_example_found, message

    def test_randomization_of_stimuli_per_task(self, task_settings):
        words_order = []
        examples_order = []

        for attempt in range(self.TRIALS_TO_CONCLUDE):
            task = task_presenters.UpdateTask(**task_settings)

            all_stimuli_iterator = ((example, word)
                                    for example, word in self.iterate_over_all_stimuli(task))

            current_words_order = []
            current_examples_order = []

            for example, word in all_stimuli_iterator:
                current_words_order.append(word)
                current_examples_order.append(example)

            words_order.append(",".join(current_words_order))
            examples_order.append(",".join(current_examples_order))

        word, w_reps = Counter(words_order).most_common(1)[0]
        words_order_check = w_reps == 1
        example, e_reps = Counter(examples_order).most_common(1)[0]
        examples_order_check = e_reps == 1

        message = f"There are repeats.\nFor words {word} repeats {w_reps}.\nFor examples {example} repeats {e_reps}"
        assert words_order_check and examples_order_check, message

    @pytest.mark.parametrize("blocks", [1, 2, 3, 4, 5, 6, 7])
    def test_is_task_finished_after_n_answers(self, blocks, task_settings):
        task_settings["blocks_before_task_finished"] = blocks
        task = task_presenters.UpdateTask(**task_settings)

        repeat = 7
        trials = self.TRIALS_TO_CONCLUDE * repeat

        answers = []
        result = []
        task.new_task()
        for trial in range(trials):
            task.next_subtask()
            answers.append(task.is_answer_time())
            result.append(task.is_task_finished())

            if task.is_task_finished():
                task.new_task()

        blocks_indexes = [idx + 1 for idx, answer in enumerate(answers[:-1]) if answer]
        # за последним ответом не будет завершения, так как одиннаковое количество запросов

        task_expected_finishes = len(blocks_indexes) // blocks
        task_actual_finished = sum(result)
        qty_error_message = f"UpdateTask should been finished {task_expected_finishes} times, " \
                            f"but was finished {task_actual_finished}"
        assert task_actual_finished == task_expected_finishes, qty_error_message

        finish_only_on_answers = [result[block_idx] for block_idx in blocks_indexes[blocks - 1::blocks]]
        incongruent_error_message = f"UpdateTask should finish only on answers, but was incongruent " \
                                    f"{finish_only_on_answers}"

        assert all(finish_only_on_answers), incongruent_error_message

    def test_task_finish_and_reset(self, default_task):
        task = default_task
        repeat = 7

        prev, cur = None, task.is_answer_time()
        incorrect_order = False
        for _ in range(repeat):
            task.new_task()
            while not task.is_task_finished():
                task.next_subtask()

                prev = cur
                cur = task.is_answer_time()

            if not prev and cur:
                incorrect_order = True
                break

        error_message = f"UpdateTask should finish after answer time, i.e. is_answer_time for " \
                        f"previous and current trial should be [True, False]" \
                        f"but get {[prev, cur]}"
        assert not incorrect_order, error_message

    def test_word_and_equation_do_not_change_at_answer_time(self, default_task):
        task = default_task

        is_changed = False

        previous_word = None
        answer_word = None
        previous_equation = None
        answer_equation = None

        task.new_task()
        while not task.is_task_finished():
            task.next_subtask()

            if task.is_answer_time():
                if previous_word != task.word:
                    answer_word = task.word
                    is_changed = True

                if previous_equation != task.example:
                    answer_equation = task.example
                    is_changed = True

                if is_changed:
                    break

            previous_word = task.word
            previous_equation = task.example

        error_message = f"UpdateTask should not change word and equation on answer. " \
                        f"Word should be {previous_word}, but was {answer_word}\n" \
                        f"Equation should be {previous_equation}, but was {answer_equation}"
        assert not is_changed, error_message

    def test_word_and_equation_do_not_change_when_task_finished(self, default_task):
        task = default_task
        trials = self.TRIALS_TO_CONCLUDE * 5

        is_changed = False

        previous_word = None
        answer_word = None
        previous_equation = None
        answer_equation = None

        task.new_task()
        for _ in range(trials):
            task.next_subtask()

            if task.is_task_finished():
                if previous_word != task.word:
                    answer_word = task.word
                    is_changed = True

                if previous_equation != task.example:
                    answer_equation = task.example
                    is_changed = True

                if is_changed:
                    break

                task.new_task()

            previous_word = task.word
            previous_equation = task.example

        error_message = f"UpdateTask should not change word and equation when finished. " \
                        f"Word should be {previous_word}, but was {answer_word}\n" \
                        f"Equation should be {previous_equation}, but was {answer_equation}"
        assert not is_changed, error_message

    def test_all_steps_of_default_use_yield_correct_result(self, task_settings):  # TODO: возможно излишне так проверять
        blocks = 3
        sequence_len = 3
        one_block_trials = sequence_len + 1

        task_settings["blocks_before_task_finished"] = blocks
        task_settings["possible_sequences"] = (sequence_len,)
        task = task_presenters.UpdateTask(**task_settings)

        trial = 1
        answers = 0
        word = None
        equation = None

        assert task.word is None
        assert task.example is None

        task.new_task()
        task.next_subtask()
        while not task.is_task_finished():
            if trial % one_block_trials != 0:
                assert task.word != word, f"UpdateTask word did not change on trial {trial}. " \
                                          f"Previous word {word}, current {task.word}"

                assert task.example != equation, f"UpdateTask equation did not change on trial {trial}. " \
                                                 f"Previous equation {equation}, current {task.example}"

                assert not task.is_answer_time(), f"UpdateTask should have answer_time on every 4 trial, " \
                                                  f"but had at {trial}"
                assert not task.is_task_finished(), f"UpdateTask should not be finished at {trial} trial"

            if trial % one_block_trials == 0:
                assert task.is_answer_time(), f"UpdateTask did not had answer_time at {trial} trial"
                assert task.word == word, f"word should not be changed at answer"
                assert task.example == equation, f"equation should not be changed at answer"
                answers += 1

            word = task.word
            equation = task.example

            task.next_subtask()
            trial += 1

            if trial % (one_block_trials * blocks + 1) == 0:
                assert task.is_task_finished(), f"UpdateTask must be finished at {one_block_trials * blocks}, " \
                                                f"but it is not"
                assert task.word == word, f"word should not be changed at final"
                assert task.example == equation, f"equation should not be changed at final"

        assert answers == blocks
        assert trial == one_block_trials * blocks + 1, f"For UpdateTask should be {one_block_trials * blocks} " \
                                                       f"but was {trial}"


class TestInhibitionTask:
    @pytest.fixture
    def create_files_for_fp(self, tmpdir):
        number_of_files = choice([33, 52])

        files = [f"file_{number}.png" for number in range(number_of_files)]

        for file in files:
            Path(tmpdir / file).touch()

        yield tmpdir, files

    @pytest.fixture
    def task_settings(self) -> Dict[str, Union[int]]:
        return dict(trials_before_task_finished=5)

    def test_does_not_raise_error_on_first_call(self, create_files_for_fp, task_settings):
        tmpdir, _ = create_files_for_fp
        try:
            task = task_presenters.InhibitionTask(fp=tmpdir.strpath, **task_settings)
            task.new_task()
        except RuntimeError:
            pytest.fail("InhibitionTask raised error on first call to new_task")

    def test_raise_error_on_call_to_new_task_for_unfinished_task(self, create_files_for_fp, task_settings):
        tmpdir, _ = create_files_for_fp
        task = task_presenters.InhibitionTask(fp=tmpdir.strpath, **task_settings)
        task.new_task()
        task.next_subtask()
        with pytest.raises(RuntimeError, match="Call to new task is prohibited for unfinished task"):
            task.new_task()

    def test_raise_error_if_finished_task_called_with_next_subtask(self, create_files_for_fp, task_settings):
        tmpdir, _ = create_files_for_fp
        task = task_presenters.InhibitionTask(fp=tmpdir.strpath, **task_settings)

        task.new_task()
        while not task.is_task_finished():
            task.next_subtask()

        with pytest.raises(RuntimeError, match="Call to next_subtask on finished task is prohibited. "
                                               "Call new_task before"):
            task.next_subtask()

    def test_task_is_not_finished_on_first_trial(self, create_files_for_fp, task_settings):
        tmpdir, _ = create_files_for_fp
        task = task_presenters.InhibitionTask(fp=tmpdir.strpath, **task_settings)

        assert not task.is_task_finished(), "InhibitionTask is finished on the first trial"

    def test_only_one_use_of_stimulus(self, create_files_for_fp, task_settings):
        tmpdir, files = create_files_for_fp
        task_settings["trials_before_task_finished"] = 999  # ensure that finished trials do not interfere

        task = task_presenters.InhibitionTask(fp=tmpdir.strpath, **task_settings)

        current_stimulus = None
        used_stimulus = []

        task.new_task()
        for _ in files:
            current_stimulus = task.next_subtask()

            if current_stimulus in used_stimulus:
                duplicated_stimulus_found = True
                break
            used_stimulus.append(current_stimulus)

            if task.is_task_finished():
                task.new_task()
        else:
            duplicated_stimulus_found = False

        duplication_message = f"In InhibitionTask stimulus was repeated {current_stimulus} in {used_stimulus}"
        assert not duplicated_stimulus_found, duplication_message

        unused_stimulus = set(files) - set(Path(fp).name for fp in used_stimulus)
        partial_usage_message = f"InhibitionTask did not used all stimuli {unused_stimulus}"
        assert not unused_stimulus, partial_usage_message

    @pytest.mark.parametrize("trials_to_finish", [1, 2, 5, 7])
    def test_is_task_finished_correctly(self, trials_to_finish, create_files_for_fp, task_settings):
        tmpdir, _ = create_files_for_fp

        task_settings["trials_before_task_finished"] = trials_to_finish
        task = task_presenters.InhibitionTask(fp=tmpdir.strpath, **task_settings)
        repeat = 4
        trials = trials_to_finish * repeat

        result = []
        task.new_task()
        for trial in range(trials):
            stimulus = task.next_subtask()
            is_finished = task.is_task_finished()

            if is_finished:
                stimulus_file_name = None if stimulus is None else stimulus.split('/')[-1]
                assert stimulus_file_name is None, f"InhibitionTask return {stimulus_file_name} instead of None"
                task.new_task()

            result.append(is_finished)

        task_expected_finishes = trials // (trials_to_finish + 1)
        task_actual_finished = sum(result)
        qty_error_message = f"InhibitionTask should been finished {task_expected_finishes}, " \
                            f"but was finished {task_actual_finished}"
        assert task_actual_finished == task_expected_finishes, qty_error_message

        finish_only_on_answers = result[trials_to_finish::trials_to_finish + 1]
        incongruent_error_message = f"InhibitionTask should finish only on answers, but was incongruent " \
                                    f"{finish_only_on_answers}"

        assert all(finish_only_on_answers), incongruent_error_message


class TestSwitchTask:  # WisconsinTest
    TRIALS_TO_CONCLUDE = 15

    @pytest.fixture
    def task_settings(self):
        return dict(max_streak=8, max_trials=144, max_rules_changed=8)

    @pytest.fixture
    def possible_answers(self):
        card_features = (0, 1, 2)
        wrong_card_features = (2, 0, 1)

        first_card = task_presenters.WisconsinCard(card_features)
        second_card = task_presenters.WisconsinCard(wrong_card_features)
        return dict(card_1=first_card, card_2=second_card)

    @staticmethod
    def _remove_task_finish_threshold(settings, remove: str):
        threshold_settings = dict(all=["max_trials", "max_rules_changed"],
                                  rule=["max_rules_changed"],
                                  trial=["max_trials"])
        change_settings = threshold_settings[remove]
        unreachable_threshold = 1e500

        for setting in change_settings:
            settings[setting] = unreachable_threshold

        return settings

    def test_task_is_not_finished_on_first_trial(self, task_settings):
        task = task_presenters.WisconsinTest(**task_settings)
        assert not task.is_task_finished()

    @pytest.mark.parametrize("max_streak", [1, 4, 8, 12])
    def test_all_rule_types_used(self, max_streak, task_settings):
        # TODO: правило меняется, выбирается из списка, меняется через N
        task_settings = self._remove_task_finish_threshold(task_settings, remove="all")
        task_settings["max_streak"] = max_streak
        rule_types = (0, 1, 2)
        task = task_presenters.WisconsinTest(**task_settings)
        trials = max_streak * self.TRIALS_TO_CONCLUDE

        rules = set()
        current_streak = task.streak

        assert max_streak == task._max_streak, f"SwitchTask (WisconsinTest) max streak {max_streak} != " \
                                               f"task streak {task._max_streak}"

        target_card = task_presenters.WisconsinCard(features=(0, 1, 2))

        previous_rule = task.rule
        task.new_task()
        for trial in range(trials):
            current_rule = task.rule
            rules.add(current_rule)
            task.is_correct(chosen_card=target_card, target_card=target_card)
            task.next_subtask()
            current_streak += 1

            if current_streak < max_streak:
                if current_rule != previous_rule:
                    changed_before_error_message = f"SwitchTask (WisconsinTest) rule changed earlier:\n" \
                                                   f"max streak {max_streak}, but changed on {current_streak} " \
                                                   f"correct answer"
                    assert False, changed_before_error_message
            elif current_streak == max_streak:
                streak_reset_error_message = f"SwitchTask (WisconsinTest) did not reset streak. " \
                                             f"Current streak {task.streak}"
                assert task.streak == 0, streak_reset_error_message

                rule_change_error_message = f"SwitchTask (WisconsinTest) did not change the rule. " \
                                            f"Current rule: {current_rule}, previous: {previous_rule}"
                assert task.rule != previous_rule, rule_change_error_message

                previous_rule = task.rule
                current_streak = 0

        used_rules = len(rules)
        not_all_used_message = f"SwitchTask (WisconsinTest) used {used_rules}, but have to use {len(rule_types)}\n" \
                               f"rules used {'; '.join(str(rule) for rule in rules)}"
        assert used_rules == 3, not_all_used_message

    def test_single_correct_answer(self, task_settings):
        max_streak = 3
        task_settings["max_streak"] = max_streak
        task = task_presenters.WisconsinTest(**task_settings)
        trials = self.TRIALS_TO_CONCLUDE

        results = []

        card_features = (0, 1, 2)
        wrong_card_features = (2, 0, 1)

        target_card = task_presenters.WisconsinCard(card_features)
        reset_card = task_presenters.WisconsinCard(wrong_card_features)  # 100% wrong card to reset streak
        permutation_correction = 2  # permutation create 2 correct answers

        task.new_task()
        for trial in range(trials):
            current_result = []
            for possible_chosen_card_features in itertools.permutations(card_features):
                chosen_card = task_presenters.WisconsinCard(possible_chosen_card_features)
                current_result.append(task.is_correct(chosen_card=chosen_card, target_card=target_card))
                task.next_subtask()

            results.append(sum(current_result) / permutation_correction)

            if trial % max_streak == 0:  # change rule every max streak to ensure that test is correct
                task.is_correct(chosen_card=reset_card, target_card=target_card)
                task.next_subtask()
                for _ in range(max_streak):
                    task.is_correct(chosen_card=target_card, target_card=target_card)
                    task.next_subtask()

        message = f"SwitchTask (WisconsinTest) has more (or less) correct answers than 1\n{results}"
        assert all(result == 1 for result in results), message

    def test_incorrect_answer_reset_streak(self, task_settings):
        max_streak = self.TRIALS_TO_CONCLUDE
        task_settings["max_streak"] = max_streak
        task = task_presenters.WisconsinTest(**task_settings)

        number_of_wrong_steps = randrange(1, max_streak)
        wrong_answer_steps = choices(range(1, max_streak), k=number_of_wrong_steps)
        trials = self.TRIALS_TO_CONCLUDE

        correct_card_features = (0, 1, 2)
        wrong_card_features = (1, 2, 0)
        target_card = task_presenters.WisconsinCard(correct_card_features)
        correct_card = target_card
        wrong_card = task_presenters.WisconsinCard(wrong_card_features)

        results = []
        task.new_task()
        for trial in range(trials):
            if trial in wrong_answer_steps:
                chosen_card = wrong_card
            else:
                chosen_card = correct_card

            task.is_correct(chosen_card=chosen_card, target_card=target_card)
            task.next_subtask()
            current_result = task.streak
            results.append(current_result)

        correct_answer_steps = sorted(set(range(trials)) - set(wrong_answer_steps))
        raise_streak_error_message = f"SwitchTask (WisconsinTest) streak did not rise on correct answers\n" \
                                     f"correct indexes: {correct_answer_steps}\nresults: {results}\n" \
                                     f"max streak: {max_streak}"
        streak_raise_on_correct = all(result > 0
                                      for trial, result in enumerate(results)
                                      if trial not in wrong_answer_steps)
        assert streak_raise_on_correct, raise_streak_error_message

        wrong_streak_error_message = f"SwitchTask (WisconsinTest) streak did not reset on wrong  answers\n" \
                                     f"wrong indexes:{wrong_answer_steps}\nresults: {results}\nmax streak: {max_streak}"
        streak_zero_on_wrong = all(result == 0
                                   for trial, result in enumerate(results)
                                   if trial in wrong_answer_steps
                                   )
        assert streak_zero_on_wrong, wrong_streak_error_message

    def test_first_trial_after_change_is_detected(self, task_settings):
        trials = 60
        number_of_detections = 12
        task_settings["max_streak"] = trials // number_of_detections
        task_settings = self._remove_task_finish_threshold(task_settings, remove="all")
        task = task_presenters.WisconsinTest(**task_settings)

        correct_card_features = (0, 1, 2)
        target_card = task_presenters.WisconsinCard(correct_card_features)

        is_first_trial_after_rule_change = []
        task.new_task()
        for trial in range(trials):
            task.is_correct(chosen_card=target_card, target_card=target_card)
            task.next_subtask()
            is_first_trial_after_rule_change.append(task.is_first_trial_after_rule_change())

        real_number_of_detections = sum(is_first_trial_after_rule_change)
        wrong_number_of_detections_message = f"SwitchTask (WisconsinTest) has {real_number_of_detections}" \
                                             f"but correct is {number_of_detections}"
        assert real_number_of_detections == number_of_detections, wrong_number_of_detections_message

        correct_sequence_of_detections = [False if x % 5 != 0 else True
                                          for x in range(1, trials + 1)]
        wrong_sequence_of_detections_message = f"SwitchTask (WisconsinTest) has {is_first_trial_after_rule_change}" \
                                               f"but correct is {correct_sequence_of_detections}"
        assert correct_sequence_of_detections == is_first_trial_after_rule_change, wrong_sequence_of_detections_message

    def test_after_rule_change_no_ambiguity_that_previous_rule_is_not_working(self):
        # TODO: я думаю, что presenter должен думать о том, что отрисовывать и чтобы не было накладок
        pass

    @pytest.mark.parametrize("max_trials", [10, 30, 144])
    def test_is_task_finished_correctly_trial_threshold_with_wrong_answers(self, task_settings, max_trials):
        task_settings["max_trials"] = max_trials
        task = task_presenters.WisconsinTest(**task_settings)

        correct_card_features = (0, 1, 2)
        wrong_card_features = (1, 2, 0)

        # to check that streak did not interfere with calculation -> use only wrong cards
        target_card = task_presenters.WisconsinCard(correct_card_features)
        wrong_card = task_presenters.WisconsinCard(wrong_card_features)

        repeat = 3
        result = []
        previous_rule = None
        next_trial_after_finished = False
        task.new_task()
        for trial in range(max_trials * repeat):
            if next_trial_after_finished:
                assert task.rule != previous_rule, "WisconsinTest must change rule when task is finished"
                next_trial_after_finished = False

            if task.is_task_finished():
                next_trial_after_finished = True

            previous_rule = task.rule
            task.is_correct(chosen_card=wrong_card, target_card=target_card)
            task.next_subtask()
            is_finished = task.is_task_finished()

            if is_finished:
                task.new_task()

            result.append(is_finished)

        is_finished_qty = sum(result)
        wrong_quantity_message = f"WisconsinTest should return {repeat} True results for is_task_finished " \
                                 f"but returned {is_finished_qty} (check by TRIALS)"
        assert is_finished_qty == repeat, wrong_quantity_message

        finished_trials = result[max_trials - 1::max_trials]
        wrong_trial_message = f"WisconsinTest should return {repeat} True results for is_task_finished " \
                              f"according to max_trial but instead has discrepancy {finished_trials} (check by TRIALS)"
        assert all(finished_trials), wrong_trial_message

    @pytest.mark.parametrize("max_trials", [10, 30, 144])
    def test_is_task_finished_correctly_trial_threshold_with_correct_answers(self, task_settings, max_trials):
        task_settings["max_streak"] = 999  # ensure that is_task_finished would not be reset by RULE_CHANGE
        task_settings["max_trials"] = max_trials
        task = task_presenters.WisconsinTest(**task_settings)

        correct_card_features = (0, 1, 2)
        target_card = task_presenters.WisconsinCard(correct_card_features)

        repeat = 3
        result = []
        previous_rule = None
        next_trial_after_finished = False
        task.new_task()
        for trial in range(max_trials * repeat):
            if next_trial_after_finished:
                # 1 - because next trial was with correct card thus streak will be one
                assert task.streak == 1, "WisconsinTest must reset streak when task is finished"
                assert task.rule != previous_rule, "WisconsinTest must change rule when task is finished"
                next_trial_after_finished = False

            if task.is_task_finished():
                next_trial_after_finished = True

            previous_rule = task.rule
            task.is_correct(chosen_card=target_card, target_card=target_card)
            task.next_subtask()
            is_finished = task.is_task_finished()

            if is_finished:
                task.new_task()

            result.append(is_finished)

        is_finished_qty = sum(result)
        wrong_quantity_message = f"WisconsinTest should return {repeat} True results for is_task_finished " \
                                 f"but returned {is_finished_qty} (check by TRIALS)"
        assert is_finished_qty == repeat, wrong_quantity_message

        finished_trials = result[max_trials - 1::max_trials]
        wrong_trial_message = f"WisconsinTest should return {repeat} True results for is_task_finished " \
                              f"according to max_trial but instead has discrepancy {finished_trials} (check by TRIALS)"
        assert all(finished_trials), wrong_trial_message

    @pytest.mark.parametrize("max_rules_changed", [3, 5, 8])
    def test_is_task_finished_correctly_rule_threshold(self, task_settings, max_rules_changed):
        max_streak = task_settings["max_streak"]
        task_settings["max_rules_changed"] = max_rules_changed
        task_settings["max_trials"] = 999  # ensure that is_task_finished would not be reset by TRIAL
        task = task_presenters.WisconsinTest(**task_settings)

        correct_card_features = (0, 1, 2)
        target_card = task_presenters.WisconsinCard(correct_card_features)

        repeat = 6
        result = []
        previous_rule = None
        next_task_after_finished = False
        task.new_task()
        for trial in range(max_rules_changed * max_streak * repeat + 1):
            if next_task_after_finished:
                # 1 - because next trial was with correct card thus streak will be one
                assert task.streak == 1, "WisconsinTest must reset streak after task was finished"
                assert task.rule != previous_rule, "WisconsinTest must change rule after task was finished"
                next_task_after_finished = False

            if task.is_task_finished():
                next_task_after_finished = True

            previous_rule = task.rule
            task.is_correct(chosen_card=target_card, target_card=target_card)
            task.next_subtask()
            is_finished = task.is_task_finished()

            if is_finished:
                task.new_task()

            result.append(is_finished)

        is_finished_qty = sum(result)
        wrong_quantity_message = f"WisconsinTest should return {repeat} True results for is_task_finished " \
                                 f"but returned {is_finished_qty} (check by RULES)"
        assert is_finished_qty == repeat, wrong_quantity_message

        finished_trials = result[max_rules_changed * max_streak - 1::max_rules_changed * max_streak]
        wrong_trial_message = f"WisconsinTest should return {repeat} True results for is_task_finished " \
                              f"according to max_trial but instead has discrepancy {finished_trials} (check by RULES)"
        assert all(finished_trials), wrong_trial_message


if __name__ == '__main__':
    pytest.main()
