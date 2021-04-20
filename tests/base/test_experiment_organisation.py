import csv
from typing import Tuple, Dict

import pytest

from base import experiment_organisation_logic


class TestTrainingSequence:
    INSTRUCTION_TEST_FILE = "test_files/tables/probe_instructions.csv"

    @pytest.fixture
    def probe_instructions(self):
        instruction_test_file = self.INSTRUCTION_TEST_FILE

        probes_info = []
        with open(instruction_test_file, mode="r") as instructions_file:
            reader = csv.DictReader(instructions_file)
            for row in reader:
                probes_info.append(row)

        return probes_info

    @pytest.fixture
    def default_training_settings(self):
        instruction_path = "test_files/tables/probe_instructions.csv"
        default_probe_sequence = ("Выбор из 2 альтернатив", "Обновление", "Переключение", "Торможение")
        return dict(probes_sequence=default_probe_sequence, probe_instructions_path=instruction_path)

    @pytest.mark.parametrize("trials", [10, 20, 30])
    def test_equal_number_of_finite_trials_for_probes(self,
                                                      trials,
                                                      default_training_settings):
        sequence = experiment_organisation_logic.TrainingSequence(**default_training_settings,
                                                                  trials=trials)

        quantity_of_trials = []
        for _, _, number_of_trials in sequence:
            quantity_of_trials.append(len(number_of_trials))

        wrong_number_message = f"In TrainingSequence all probe must have {trials} but instead had {quantity_of_trials}"
        assert all(probe_trials == trials for probe_trials in quantity_of_trials), wrong_number_message

    @pytest.mark.parametrize("trials", [[10, 20, 30, 40], [1, 1, 1, 1], [14, 11, 3, 22]])
    def test_custom_number_of_trials_for_probes(self,
                                                trials,
                                                default_training_settings):
        sequence = experiment_organisation_logic.TrainingSequence(**default_training_settings,
                                                                  trials=trials)

        quantity_of_trials = []
        for _, _, number_of_trials in sequence:
            quantity_of_trials.append(len(number_of_trials))

        wrong_number_message = f"In TrainingSequence all probe must have {trials} but instead had {quantity_of_trials}"
        assert quantity_of_trials == trials, wrong_number_message

    @pytest.mark.parametrize("training_trials", [[10, 20, 30, 40], None, 5])
    def test_independence_of_trials_for_probes(self,
                                               training_trials,
                                               default_training_settings):
        sequence = experiment_organisation_logic.TrainingSequence(**default_training_settings,
                                                                  trials=training_trials)

        for _, _, trials in sequence:
            for correct_trial_idx, real_trial_idx in zip(range(6), trials):

                if correct_trial_idx == 0 and real_trial_idx != 0:
                    dependant_trials_error_message = f"For training trials: {training_trials} trial {trials} was " \
                                                     f"dependant on the previous with value {real_trial_idx}"
                    assert False, dependant_trials_error_message

                assert correct_trial_idx == real_trial_idx, f"For trials {trials} trial has incorrect count"

    def test_chosen_correct_instructions(self, default_training_settings, probe_instructions):
        right_probes_info = probe_instructions
        sequence = experiment_organisation_logic.TrainingSequence(**default_training_settings,
                                                                  trials=1)

        for idx, (probe_name, instruction, number_of_trials) in enumerate(sequence):
            right_probe = right_probes_info[idx]["probe"]
            wrong_probe_message = f"In TrainingSequence {idx + 1} must be {right_probe} probe but instead {probe_name}"
            assert probe_name == right_probe, wrong_probe_message

            right_instruction = right_probes_info[idx]["instruction"]
            wrong_instruction_message = f"In TrainingSequence {idx + 1} must be\n" \
                                        f"{right_instruction}\ninstruction but instead\n{instruction}"
            assert instruction == right_instruction, wrong_instruction_message


class TestExperimentWMSequence:
    TASK_INSTRUCTIONS_TEST_FILE = "test_files/tables/task_instructions.csv"
    PROBE_INSTRUCTIONS_TEST_FILE = "test_files/tables/probe_instructions.csv"

    @staticmethod
    def _load_instructions(fp: str):
        with open(fp, mode="r") as instruction_file:
            reader = csv.DictReader(instruction_file)
            rows = [row for row in reader]
        return rows

    @pytest.fixture
    def instructions(self) -> Tuple[Dict[str, str], ...]:
        task_info = {row["task"]: row["instruction"]
                     for row in self._load_instructions(self.TASK_INSTRUCTIONS_TEST_FILE)}

        probe_info = {row["probe"]: row["instruction"]
                      for row in self._load_instructions(self.PROBE_INSTRUCTIONS_TEST_FILE)}

        return task_info, probe_info

    @pytest.fixture
    def default_experiment_settings(self):
        tasks_instruction_path = self.TASK_INSTRUCTIONS_TEST_FILE
        default_tasks = ("Обновление", "Переключение", "Торможение")

        probes_instruction_path = "test_files/tables/probe_instructions.csv"
        default_probes = ("Обновление", "Переключение", "Торможение")

        return dict(task_instructions_path=tasks_instruction_path, tasks=default_tasks,
                    probe_instructions_path=probes_instruction_path, probes=default_probes)

    def test_tasks_and_probes_randomized(self, default_experiment_settings):
        trials_to_check_randomisation = 10
        randomization_tolerance = 8
        actual_probes_task_sequences = []

        for trial in range(trials_to_check_randomisation):
            sequence = experiment_organisation_logic.ExperimentWMSequence(**default_experiment_settings)
            single_result = tuple((task.name, probe.name) for task, probe in sequence)
            actual_probes_task_sequences.append(single_result)

        unique_sequences_of_probes_and_tasks = len(set(actual_probes_task_sequences))
        randomisation_error_message = f"There must be more than {randomization_tolerance} different sequences of" \
                                      f"task and probe, but got {unique_sequences_of_probes_and_tasks}\n" \
                                      f"{actual_probes_task_sequences}"
        assert unique_sequences_of_probes_and_tasks > randomization_tolerance, randomisation_error_message

    def test_tasks_and_probe_instructions_are_correct(self, default_experiment_settings, instructions):
        right_task_instructions, right_probe_instructions = instructions
        sequence = experiment_organisation_logic.ExperimentWMSequence(**default_experiment_settings)

        tasks_instructions_showed = {task: 0 for task in default_experiment_settings["tasks"]}
        for idx, (task, probe) in enumerate(sequence):
            if task.instruction is not None:
                right_task_instruction = right_task_instructions[task.name]
                wrong_task_instruction_message = f"In ExperimentSequence {idx + 1} must be instruction for {task.name}" \
                                                 f" task but instead get\n{task.instruction}"
                assert task.instruction == right_task_instruction, wrong_task_instruction_message

                tasks_instructions_showed[task.name] += 1

            right_probe_instruction = right_probe_instructions[probe.name]
            wrong_probe_instruction_message = f"In ExperimentSequence {idx + 1} must be instruction for {probe.name}" \
                                              f" probe but instead get:\n{probe.instruction}"
            assert probe.instruction == right_probe_instruction, wrong_probe_instruction_message

        showed_too_many_times_error_message = f"ExperimentSequence must show task instruction on every " \
                                              f"presentation. But showed:\n{tasks_instructions_showed}"
        assert all(times_showed != 3
                   for times_showed in tasks_instructions_showed.values()), showed_too_many_times_error_message


class TestExperimentInsightTaskSequence:
    PROBE_INSTRUCTIONS_TEST_FILE = "test_files/tables/probe_instructions.csv"

    @pytest.fixture
    def default_tasks(self, tmpdir):
        task_fp = tmpdir / "tasks"
        task_fp.makedir()

        return task_fp

    def test_smth(self, default_tasks):
        print(default_tasks)


if __name__ == '__main__':
    pytest.main()
