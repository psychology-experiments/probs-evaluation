import csv
from enum import Enum
import os
from typing import List, Optional, Dict

from psychopy import data


class ExperimentPart(Enum):
    WM = "WM"
    INSIGHT = "Insight"


class ExperimentFirstPartParticipantInfoSaver:
    def __init__(self,
                 participant_data_filename: str,
                 participants_info_fp: str,
                 participant_name: str,
                 participant_age: str,
                 participant_gender: str):
        self._participant_data_filename = os.path.basename(participant_data_filename) + ".csv"
        self._participants_info_fp = participants_info_fp

        self._participant_id = f"{participant_name} {participant_age} {participant_gender}"

    def save(self):
        with open(self._participants_info_fp, mode="a", encoding="UTF-8", newline="") as csv_file:
            csv_writer = csv.DictWriter(csv_file, fieldnames=["participant", "WM_name", "Insight_name"])
            row_info = dict(participant=self._participant_id,
                            WM_name=self._participant_data_filename,
                            Insight_name="")
            csv_writer.writerow(row_info)


class ExperimentSecondPartParticipantInfoSaver:
    def __init__(self,
                 chosen_wm_file_name: str,
                 insight_file_name: str,
                 participants_info_fp: str):
        self._chosen_wm_file_name = chosen_wm_file_name
        self._insight_file_name = insight_file_name
        self._participants_info_fp = participants_info_fp

    def save(self):
        updated_data = self._read_and_add_info()
        header = list(updated_data[0].keys())
        with open(file=self._participants_info_fp, mode="w", encoding="UTF-8", newline="") as csv_file:
            csv_writer = csv.DictWriter(csv_file, fieldnames=header)
            csv_writer.writeheader()
            csv_writer.writerows(updated_data)

    def _read_and_add_info(self) -> List[Dict[str, str]]:
        with open(file=self._participants_info_fp, mode="r", encoding="UTF-8", newline="") as csv_file:
            csv_reader = csv.DictReader(csv_file)

            updated_data = []
            for row in csv_reader:
                if row["WM_name"] == self._chosen_wm_file_name:
                    row["Insight_name"] = self._insight_file_name

            updated_data.append(row)

        return updated_data


class DataSaver:
    def __init__(self,
                 save_fp: str,
                 experiment_part: ExperimentPart):
        if experiment_part not in ExperimentPart:
            parts = [part for part in ExperimentPart.__members__.keys()]
            raise ValueError(f'experiment_part must be one of {parts}')

        self._saver = data.ExperimentHandler(dataFileName=save_fp,
                                             version="2020.2.10",  # TODO: указать правильную версию
                                             autoLog=False,
                                             savePickle=False)

        # TODO: find a way to implement data_to_save cleaner
        data_to_save = ["experiment_part",
                        "stage",
                        "task",
                        "task_solution_time",
                        "probe_trial",
                        "probe",
                        "RT",
                        "is_correct",
                        "time_from_experiment_start",
                        ]
        if experiment_part is ExperimentPart.WM:
            # TODO: add info about subtasks
            data_to_save.insert(2, "combination_number")
            data_to_save.insert(4, "task_trial")
        else:
            data_to_save.insert(3, "task_type")

        self._saver.dataNames = data_to_save

        self._experiment_part: ExperimentPart = experiment_part
        self._task_type: Optional[str] = None
        self._combination_number: int = 0

        self._task: Optional[str] = None
        self._task_trial: int = 0

        self._probe: Optional[str] = None
        self._probe_trial: int = 0

    def new_task(self, task_name: str, stage: str, task_type: Optional[str] = None):
        self._task_trial: int = 0
        self._task = task_name

        if stage == "experimental":
            self._combination_number += 1

        if task_type is not None:
            self._task_type = task_type

    def new_probe(self):
        self._probe_trial: int = 0

    def save_probe_practice(self,
                            probe_name: str,
                            is_correct: bool,
                            rt: float,
                            time_from_experiment_start: float
                            ):
        self._probe_trial += 1
        self._saver.addData("experiment_part", self._experiment_part.value)
        self._saver.addData("stage", "probe training")
        self._saver.addData("probe_trial", self._probe_trial)
        self._saver.addData("probe", probe_name)
        self._saver.addData("RT", rt)
        self._saver.addData("is_correct", int(is_correct))
        self._saver.addData("time_from_experiment_start", time_from_experiment_start)
        self._saver.nextEntry()

    def save_task_practice(self,
                           task_name: str,
                           solution_time: float,
                           time_from_experiment_start: float
                           ):
        self._task_trial += 1
        self._saver.addData("experiment_part", self._experiment_part.value)
        self._saver.addData("stage", "task training")
        self._saver.addData("task_trial", self._task_trial)
        self._saver.addData("task", task_name)
        self._saver.addData("task_solution_time", solution_time)
        self._saver.addData("time_from_experiment_start", time_from_experiment_start)
        self._saver.nextEntry()

    def save_experimental_probe_data(self,
                                     probe_name: str,
                                     is_correct: bool,
                                     rt: float,
                                     time_from_experiment_start: float,
                                     ):
        self._probe_trial += 1

        self._saver.addData("experiment_part", self._experiment_part.value)
        self._saver.addData("stage", "experimental")
        if self._experiment_part == ExperimentPart.WM:
            self._saver.addData("combination_number", self._combination_number)

        self._saver.addData("task", self._task)
        if self._experiment_part == ExperimentPart.INSIGHT:
            self._saver.addData("task_type", self._task_type)

        self._saver.addData("probe_trial", self._probe_trial)
        self._saver.addData("probe", probe_name)
        self._saver.addData("RT", rt)
        self._saver.addData("is_correct", int(is_correct))

        self._saver.addData("time_from_experiment_start", time_from_experiment_start)
        self._saver.nextEntry()

    def save_experimental_task_data(self,
                                    solution_time: Optional[float],
                                    time_from_experiment_start: float
                                    ):
        self._task_trial += 1

        self._saver.addData("experiment_part", self._experiment_part.value)
        self._saver.addData("stage", "experimental")
        if self._experiment_part == ExperimentPart.WM:
            self._saver.addData("combination_number", self._combination_number)

        self._saver.addData("task_trial", self._task_trial)
        self._saver.addData("task", self._task)
        if self._experiment_part == ExperimentPart.INSIGHT:
            self._saver.addData("task_type", self._task_type)
        self._saver.addData("task_solution_time", solution_time)

        self._saver.addData("time_from_experiment_start", time_from_experiment_start)
        self._saver.nextEntry()

    def close(self):
        self._saver.close()
