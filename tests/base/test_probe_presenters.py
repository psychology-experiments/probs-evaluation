import itertools
import logging
from typing import Dict, List, Tuple

import pytest

from base import probe_presenters


# TODO: for each probe add test to check that they work correctly

class TestProbe:
    PROBE_TYPES = {
        "TwoAlternatives":
            {"probes": ["green", "red"],
             "answers": ["right", "left"]},
    }
    EQUIVALENCY_VERIFICATION = [(["one", "two"], ["up"]), (["one"], ["left", "right"])]
    UNIQUENESS_VERIFICATION = [(["one", "one"], ["up"] * 2),
                               (["one", "two", "three", "one"], ["left"] * 4)]

    TRIALS_TO_CONCLUDE = 15

    @pytest.mark.parametrize("probes, answers", EQUIVALENCY_VERIFICATION)
    def test_equivalency_verification_probe_answers(self, probes, answers):
        expected_message = f"But there are {len(probes)} probes and {len(answers)} answers"
        with pytest.raises(ValueError, match=expected_message):
            probe_presenters.Probe(probes=probes, answers=answers)

    def test_empty_probe_verification(self):
        with pytest.raises(ValueError, match=r"Empty Probe is prohibited"):
            probe_presenters.Probe(probes=[], answers=[])

    @pytest.mark.parametrize("probes, answers", UNIQUENESS_VERIFICATION)
    def test_uniqueness_probe_verification(self, probes, answers):
        expected_message = f"But there are {len(probes) - len(set(probes))} repeats in probes"
        with pytest.raises(ValueError, match=expected_message):
            probe_presenters.Probe(probes=probes, answers=answers)

    @pytest.mark.parametrize("probe_type", PROBE_TYPES.items())
    def test_only_one_correct_answer(self, probe_type: Tuple[str, Dict[str, List[str]]]):
        probe_name = probe_type[0]
        probes = probe_type[1]["probes"]
        answers = probe_type[1]["answers"]

        current_probe = probe_presenters.Probe(probes=probes, answers=answers)
        trials = self.TRIALS_TO_CONCLUDE

        results = []
        for trial in range(trials):
            result = sum(current_probe.get_press_correctness(key_name) for key_name in answers)
            results.append(result)
            current_probe.next_probe()

        message = f"For {probe_name} there is more than one correct answer"
        assert sum(results) == trials, message

    @pytest.mark.parametrize("probe_type", PROBE_TYPES.items())
    def test_correct_answer_is_correct(self, probe_type: Tuple[str, Dict[str, List[str]]]):
        probe_name = probe_type[0]
        probes = probe_type[1]["probes"]
        answers = probe_type[1]["answers"]

        current_probe = probe_presenters.Probe(probes=probes, answers=answers)
        trials = self.TRIALS_TO_CONCLUDE

        results = []
        for trial in range(trials):
            current_probe_idx = current_probe.get_probe_number()
            correct_answer = answers[current_probe_idx]
            is_considered_correct = current_probe.get_press_correctness(correct_answer)
            results.append(is_considered_correct)
            current_probe.next_probe()

        message = f"For {probe_name} correct answers was not accepted"
        assert sum(results) == trials, message

    @pytest.mark.parametrize("probe_type", PROBE_TYPES.items())
    def test_probe_changes(self, probe_type: Tuple[str, Dict[str, List[str]]]):
        probe_name = probe_type[0]
        probes = probe_type[1]["probes"]
        answers = probe_type[1]["answers"]

        current_probe = probe_presenters.Probe(probes=probes, answers=answers, probe_type=probe_name)

        trials = self.TRIALS_TO_CONCLUDE
        start_probe_number = current_probe.get_probe_number()

        probe_changed = False
        for trial in range(trials):
            current_probe.next_probe()
            current_probe_number = current_probe.get_probe_number()

            if current_probe_number != start_probe_number:
                probe_changed = True
                break

        message = f"for {probe_name} there was no probe change"
        assert probe_changed, message

    @pytest.mark.parametrize("probe_type", PROBE_TYPES.items())
    def test_all_probes_can_be_chosen(self, probe_type: Tuple[str, Dict[str, List[str]]]):
        probe_name = probe_type[0]
        probes = probe_type[1]["probes"]
        answers = probe_type[1]["answers"]

        current_probe = probe_presenters.Probe(probes=probes, answers=answers, probe_type=probe_name)

        trials = self.TRIALS_TO_CONCLUDE * len(probes)
        start_probe_number = current_probe.get_probe_number()

        probes_chosen = [start_probe_number]
        qty_probes_have_to_be_chosen = len(probes)

        are_all_chosen = False
        for trial in range(trials):
            current_probe.next_probe()
            current_probe_number = current_probe.get_probe_number()
            probes_chosen.append(current_probe_number)

            if len(set(probes_chosen)) == qty_probes_have_to_be_chosen:
                are_all_chosen = True
                break

        message = f"For {probe_name} not all probes can be chosen"
        assert are_all_chosen, message

    @pytest.mark.parametrize("probe_type", PROBE_TYPES.items())
    def test_no_probe_chosen_beyond_possible(self, probe_type: Tuple[str, Dict[str, List[str]]]):
        probe_name = probe_type[0]
        probes = probe_type[1]["probes"]
        answers = probe_type[1]["answers"]

        qty_probes = len(probes)

        current_probe = probe_presenters.Probe(probes=probes, answers=answers, probe_type=probe_name)
        trials = self.TRIALS_TO_CONCLUDE * qty_probes

        results = []
        probe_idx = []
        for trial in range(trials):
            result = current_probe.get_probe_number()
            probe_idx.append(result)
            results.append(0 <= result < qty_probes)
            current_probe.next_probe()

        message = f"{probe_name} contains impossible values:\n" \
                  f"{[idx for idx, result in zip(probe_idx, results) if not result]}"
        assert all(results), message


class TestUpdateProbe:
    UNIQUENESS_VERIFICATION = [(["red", "green", "red"]), (["one", "one"])]
    DEMO_KEY_ANSWERS = dict(correct="right", incorrect="left")
    DEMO_PROBES = ["circle", "square", "triangle"]

    TRIALS_TO_CONCLUDE = 15

    def test_empty_probe_verification(self):
        with pytest.raises(ValueError, match=r"Empty Probe is prohibited"):
            probe_presenters.UpdateProbe(probes=[], probe_type="Update")

    @pytest.mark.parametrize("probes", UNIQUENESS_VERIFICATION)
    def test_uniqueness_probe_verification(self, probes):
        expected_message = f"But there are {len(probes) - len(set(probes))} repeats in probes"
        with pytest.raises(ValueError, match=expected_message):
            probe_presenters.UpdateProbe(probes=probes, probe_type="Update")

    def test_probe_changes(self):
        current_probe = probe_presenters.UpdateProbe(probes=["circle", "square", "triangle"], probe_type="Update")

        trials = self.TRIALS_TO_CONCLUDE
        start_probe_number = current_probe.get_probe_number()

        probe_changed = False
        for trial in range(trials):
            current_probe.next_probe()
            current_probe_number = current_probe.get_probe_number()

            if current_probe_number != start_probe_number:
                probe_changed = True
                break

        message = "For UpdateProbe there was no probe change"
        assert probe_changed, message

    def test_the_same_probe_sequence_return_true(self):
        current_probe = probe_presenters.UpdateProbe(probes=self.DEMO_PROBES, probe_type="Update")
        key_for_correct = self.DEMO_KEY_ANSWERS["correct"]

        trials = self.TRIALS_TO_CONCLUDE
        previous_probe_number = current_probe.get_probe_number()

        correctness_results = []
        probes_numbers = [previous_probe_number]
        for trial in range(trials):
            current_probe.next_probe()
            current_probe_number = current_probe.get_probe_number()

            if current_probe_number == previous_probe_number:
                correctness = current_probe.get_press_correctness(key_for_correct)
                correctness_results.append(correctness)
                probes_numbers.append(current_probe_number)

            previous_probe_number = current_probe_number

        if not correctness_results:
            logging.warning("There was no sequence of single probe")
        message = "UpdateProbe did not mark correct sequence as correct." \
                  f"\nSequence: {probes_numbers}\nResults: {correctness_results}"
        assert all(correctness_results), message

    def test_various_probe_sequence_return_false(self):
        current_probe = probe_presenters.UpdateProbe(probes=self.DEMO_PROBES, probe_type="Update")
        key_for_incorrect = self.DEMO_KEY_ANSWERS["incorrect"]

        trials = self.TRIALS_TO_CONCLUDE
        previous_probe_number = current_probe.get_probe_number()

        correctness_results = []
        probes_numbers = []
        for trial in range(trials):
            current_probe.next_probe()
            current_probe_number = current_probe.get_probe_number()

            if current_probe_number != previous_probe_number:
                correctness = current_probe.get_press_correctness(key_for_incorrect)
                correctness_results.append(correctness)
                probes_numbers.append(current_probe_number)

            previous_probe_number = current_probe_number

        if not correctness_results:
            logging.warning("There was no sequence of single probe")
        message = "UpdateProbe marked incorrect sequence as correct." \
                  f"\nSequence: {probes_numbers}\nResults: {correctness_results}"
        assert all(correctness_results), message

    def test_only_one_correct_answer(self):
        current_probe = probe_presenters.UpdateProbe(probes=self.DEMO_PROBES, probe_type="Update")
        current_probe.next_probe()  # skip first trial because it always correct
        trials = self.TRIALS_TO_CONCLUDE

        results = []
        for trial in range(trials):
            result = sum(current_probe.get_press_correctness(key_name)
                         for key_name in self.DEMO_KEY_ANSWERS.values())
            results.append(result)
            current_probe.next_probe()

        message = f"For UpdateProbe there is more than one correct answer"
        assert sum(results) == trials, message


class TestSwitchProbe:
    TRIALS_TO_CONCLUDE = 8

    def test_probe_chosen_according_to_rule(self):
        # TODO: проверить что переключается после 2 одного цвета (2с, 2ч, 2с, 2ч) (черное или синее в начале случайно)
        current_probe = probe_presenters.Probe(probes=list("12345678"),
                                               answers=["left"] * 8,
                                               probe_type="Switch")
        trials = self.TRIALS_TO_CONCLUDE

        times_repeat = 2  # по умолчанию дважды каждый стимул берётся из одной группы
        right_sequence = ([[0, 1, 4, 5]] * times_repeat + [[2, 3, 6, 7]] * times_repeat) * (trials // 2)
        results = []
        probe_idx = []
        for trial in range(trials):
            result = current_probe.get_probe_number()
            probe_idx.append(result)
            results.append(result in right_sequence[trial])
            current_probe.next_probe()

        message = "SwitchProbe does not choose from correct groups\n" \
                  f"Groups {right_sequence}\n" \
                  f"Indexes {probe_idx}"
        assert sum(results) == trials, message

    def test_all_probes_can_be_chosen(self):
        probes = list("12345678")
        current_probe = probe_presenters.Probe(probes=probes,
                                               answers=["left"] * 8,
                                               probe_type="Switch")

        trials = self.TRIALS_TO_CONCLUDE * len(probes)
        start_probe_number = current_probe.get_probe_number()

        probes_chosen = [start_probe_number]
        qty_probes_have_to_be_chosen = len(probes)

        are_all_chosen = False
        for trial in range(trials):
            current_probe.next_probe()
            current_probe_number = current_probe.get_probe_number()
            probes_chosen.append(current_probe_number)

            if len(set(probes_chosen)) == qty_probes_have_to_be_chosen:
                are_all_chosen = True
                break

        message = f"For SwitchProbe not all probes can be chosen"
        assert are_all_chosen, message

    def test_no_probe_chosen_beyond_possible(self):
        probes = list("12345678")
        qty_probes = len(probes)
        current_probe = probe_presenters.Probe(probes=probes,
                                               answers=["left"] * 8,
                                               probe_type="Switch")
        trials = self.TRIALS_TO_CONCLUDE * qty_probes

        results = []
        probe_idx = []
        for trial in range(trials):
            result = current_probe.get_probe_number()
            probe_idx.append(result)
            results.append(0 <= result < qty_probes)
            current_probe.next_probe()

        message = "SwitchProbe contains impossible values:\n" \
                  f"{[idx for idx, result in zip(probe_idx, results) if not result]}"
        assert all(results), message


class TestInhibitionProbe:
    def test_probe_chosen_according_to_ratio_rule(self):
        probes = ["".join(colorful_word) for colorful_word in itertools.product("RGBY", repeat=2)]
        right_answers = dict(R="right", Y="right", G="left", B="left")
        answers = [right_answers[probe[1]] for probe in probes]

        current_probe = probe_presenters.Probe(probes=probes,
                                               answers=answers,
                                               probe_type="Inhibition")

        trials = 100
        percent_tolerance = 0.07

        probes_to_count_ratio = [idx for idx, probe in enumerate(probes) if probe[0] == probe[1]]
        results = []
        for trial in range(trials):
            result = current_probe.get_probe_number()
            results.append(result in probes_to_count_ratio)
            current_probe.next_probe()

        congruent_percent = sum(results) / trials
        message = "InhibitionProbe does not choose probes in wanted ratio\n" \
                  f"Percent for congruent probes {congruent_percent:.3%}"
        assert congruent_percent == pytest.approx(1 / 6, abs=percent_tolerance), message


if __name__ == '__main__':
    pytest.main()
