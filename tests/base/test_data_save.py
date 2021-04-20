import csv
import random
from typing import List

import pytest

from base import data_save


class TestDataSaver:
    TRIALS_TO_SAVE = 100

    @pytest.fixture
    def prepared_data(self) -> dict:
        rt = [random.uniform(a=0.1, b=3) for _ in range(self.TRIALS_TO_SAVE)]
        is_correct = random.choices(population=(True, False), k=self.TRIALS_TO_SAVE)
        time_from_experiment_start = []
        previous_time = random.uniform(0.1, 3)
        for single_rt in rt:
            time_from_experiment_start.append(single_rt + previous_time)
            previous_time += random.uniform(0.1, 3)
        probe = [probe_name
                 for probe_name in ("TwoAlternatives", "Update", "Switch", "Inhibition")
                 for _ in range(self.TRIALS_TO_SAVE // 4)]

        return dict(RT=rt,
                    is_correct=is_correct,
                    probe_name=probe,
                    time_from_experiment_start=time_from_experiment_start)

    def test_save_probe_practice(self, tmpdir, prepared_data):
        rt = prepared_data["RT"]
        is_correct = prepared_data["is_correct"]
        probe_name = prepared_data["probe_name"]
        time_from_experiment_start = prepared_data["time_from_experiment_start"]

        data_output_fp = tmpdir.join("test_save/test")
        data_saver = data_save.DataSaver(save_fp=data_output_fp)

        for trial in range(self.TRIALS_TO_SAVE):
            data_saver.save_probe_practice(probe_name=probe_name[trial],
                                           is_correct=is_correct[trial],
                                           rt=rt[trial],
                                           time_from_experiment_start=time_from_experiment_start[trial])

        data_saver.close()

        with open(f"{data_output_fp}.csv", mode="r", encoding="utf-8-sig") as fin:
            csv_reader = csv.DictReader(f=fin)

            all_values_saved_correct = True
            for row_idx, row_data in enumerate(csv_reader):
                formatted_correctness = str(int(is_correct[row_idx]))
                formatted_rt = str(rt[row_idx])
                formatted_time_from_start = str(time_from_experiment_start[row_idx])
                if any([formatted_rt != row_data["RT"],
                        formatted_correctness != row_data["is_correct"],
                        probe_name[row_idx] != row_data["probe"],
                        formatted_time_from_start != row_data["time_from_experiment_start"],
                        "probe training" != row_data["stage"]]):
                    all_values_saved_correct = False
                    correct_info = ['probe training',
                                    formatted_rt,
                                    formatted_correctness,
                                    probe_name[row_idx],
                                    formatted_time_from_start]
                    saved_info = [row_data['stage'],
                                  row_data['RT'],
                                  row_data['is_correct'],
                                  row_data['probe'],
                                  row_data['time_from_experiment_start']]
                    wrong_save_message = f"In row {row_idx + 1} should be " \
                                         f"{correct_info}" \
                                         " but instead was " \
                                         f"{saved_info}"
                    break

            assert all_values_saved_correct, wrong_save_message

    def test_save_experimental_trials(self):
        pass


if __name__ == '__main__':
    pytest.main()
