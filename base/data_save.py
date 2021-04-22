from typing import List, Optional

from psychopy import data


class DataSaver:
    def __init__(self,
                 save_fp: str,
                 experiment_part: str):
        if experiment_part not in ("WM", "Insight"):
            raise ValueError(f'experiment_part must be "WM" or "Insight"')

        self._saver = data.ExperimentHandler(dataFileName=save_fp,
                                             version="2020.2.10",  # TODO: указать правильную версию
                                             autoLog=False,
                                             savePickle=False)

        # TODO: find a way to implement data_to_save cleaner
        data_to_save = ["experiment_part",
                        "stage",
                        "task",
                        "task_trial",
                        "task_solution_time",
                        "probe_trial",
                        "probe",
                        "RT",
                        "is_correct",
                        "time_from_experiment_start",
                        ]
        if experiment_part == "WM":
            # TODO: add info about subtasks
            data_to_save.insert(2, "combination_number")
        else:
            data_to_save.insert(3, "task_type")

        self._saver.dataNames = data_to_save

        self._experiment_part: str = experiment_part
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
        self._saver.addData("experiment_part", self._experiment_part)
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
        self._saver.addData("experiment_part", self._experiment_part)
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

        self._saver.addData("experiment_part", self._experiment_part)
        self._saver.addData("stage", "experimental")
        if self._experiment_part == "WM":
            self._saver.addData("combination_number", self._combination_number)

        self._saver.addData("task", self._task)
        if self._experiment_part == "Insight":
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

        self._saver.addData("experiment_part", self._experiment_part)
        self._saver.addData("stage", "experimental")
        if self._experiment_part == "WM":
            self._saver.addData("combination_number", self._combination_number)

        self._saver.addData("task_trial", self._task_trial)
        self._saver.addData("task", self._task)
        if self._experiment_part == "Insight":
            self._saver.addData("task_type", self._task_type)
        self._saver.addData("task_solution_time", solution_time)

        self._saver.addData("time_from_experiment_start", time_from_experiment_start)
        self._saver.nextEntry()

    def close(self):
        self._saver.close()
