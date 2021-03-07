import csv
import random

import pytest

from base import data_save


class TestDataSaver:
    TRIALS_TO_SAVE = 100

    @pytest.fixture
    def prepared_data(self):
        rt = [random.uniform(a=0.1, b=3) for _ in range(self.TRIALS_TO_SAVE)]
        is_correct = random.choices(population=(True, False), k=self.TRIALS_TO_SAVE)
        probe = [probe_name
                 for probe_name in ("TwoAlternatives", "Update", "Switch", "Inhibition")
                 for _ in range(self.TRIALS_TO_SAVE // 4)]

        return dict(rt=rt, is_correct=is_correct, probe_name=probe)

    def test_save_probe_practice(self, tmpdir, prepared_data):
        rt = prepared_data["rt"]
        is_correct = prepared_data["is_correct"]
        probe_name = prepared_data["probe_name"]

        data_output_fp = tmpdir.join("test_save/test")
        data_saver = data_save.DataSaver(save_fp=data_output_fp)

        for trial in range(self.TRIALS_TO_SAVE):
            data_saver.save_probe_practice(probe_name=probe_name[trial],
                                           is_correct=is_correct[trial],
                                           rt=rt[trial])

        data_saver.close()

        with open(f"{data_output_fp}.csv", mode="r") as fin:
            csv_reader = csv.DictReader(f=fin)

            all_values_saved_correct = True
            for row_idx, row_data in enumerate(csv_reader):
                if any([rt[row_idx] != row_data["RT"],
                        is_correct[row_idx] != row_data["is_correct"],
                        probe_name[row_idx] != row_data["probe_name"],
                        "probe training" != row_data["stage"]]):
                    all_values_saved_correct = False
                    wrong_save_message = f"In row {row_idx + 1} should be " \
                                         f"{'probe training', [rt[row_idx], is_correct[row_idx], probe_name[row_idx]]}" \
                                         "but instead was " \
                                         f"{[row_data['stage'], row_data['rt'], row_data['is_correct'], row_data['probe_name']]}"

            assert all_values_saved_correct, wrong_save_message

    def test_save_experimental_trials(self):
        pass


if __name__ == '__main__':
    pytest.main()
