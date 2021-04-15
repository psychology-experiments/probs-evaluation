import csv
from itertools import count, product
from random import shuffle
from typing import List, Union, Iterator, Dict, Optional, Tuple, NamedTuple


class ProbeInfo(NamedTuple):
    name: str
    instruction: str
    trials: Iterator


class TaskInfo(NamedTuple):
    name: str
    instruction: Optional[str]
    trained: bool


FilePath = str


class TrainingSequence:
    def __init__(self,
                 probes_sequence: Tuple[str, ...],
                 trials: Optional[Union[List[int], int]] = 30,
                 probe_instructions_path: FilePath = "text/probe instructions.csv"):

        if trials is None:
            trials = [count() for _ in range(len(probes_sequence))]
        elif isinstance(trials, int):
            trials = [range(trials) for _ in range(len(probes_sequence))]
        elif isinstance(trials, list):
            trials = [range(trial) for trial in trials]
        else:
            raise ValueError(f"trials has wrong value: {trials}. Can be None, List[int] or int")

        self._probe_number_of_trials_sequence: List[Iterator] = trials
        self._probes: Tuple[str, ...] = probes_sequence

        if len(self._probe_number_of_trials_sequence) != len(self._probes):
            raise ValueError(f"QTY of probes ({probes_sequence}) "
                             f"must match QTY of trials {self._probe_number_of_trials_sequence}")

        self._probes_info: List[ProbeInfo] = []
        self._load_probe_instructions(probe_instructions_path)

    def _load_probe_instructions(self, path: str) -> None:
        with open(path, mode="r", encoding="UTF-8") as instructions_file:
            reader = csv.DictReader(instructions_file)
            probes_instructions: Dict[str, str] = {row["probe"]: row["instruction"]
                                                   for row in reader}

        for probe_name, trials in zip(self._probes, self._probe_number_of_trials_sequence):
            probe_info = ProbeInfo(name=probe_name,
                                   instruction=probes_instructions[probe_name],
                                   trials=trials)
            self._probes_info.append(probe_info)

    def __getitem__(self, item) -> ProbeInfo:
        return self._probes_info[item]


class ExperimentWMSequence:
    """
    Create sequence to evaluate relationship between WM probes and tasks
    """

    def __init__(self,
                 tasks: Tuple[str, ...],
                 probes: Tuple[str, ...],
                 task_instructions_path: FilePath = "text/task instructions.csv",
                 probe_instructions_path: FilePath = "text/probe instructions.csv"):
        tasks_and_probes = list(product(tasks, probes))
        shuffle(tasks_and_probes)

        self._tasks_sequence, probes = zip(*tasks_and_probes)

        self._probes_sequence = TrainingSequence(probes_sequence=probes,
                                                 trials=None,
                                                 probe_instructions_path=probe_instructions_path)

        self._task_instructions: Dict[str, str] = {}
        self._load_instructions(task_instructions_path)

        self._task_showed = {task: False for task in tasks}

    def _load_instructions(self, path: str):
        with open(path, mode="r", encoding="UTF-8") as instructions_file:
            reader = csv.DictReader(instructions_file)
            for row in reader:
                self._task_instructions[row["task"]] = row["instruction"]

    def __getitem__(self, item):
        probe = self._probes_sequence[item]

        task_name = self._tasks_sequence[item]
        task_instruction = self._task_instructions[task_name]
        showed = self._task_showed[task_name]

        if not self._task_showed[task_name]:
            self._task_showed[task_name] = True

        task = TaskInfo(name=task_name,
                        instruction=task_instruction,
                        trained=showed)

        return task, probe


class ExperimentInsightTaskSequence:
    """
    Create sequence of insight task and probes
    """

    def __init__(self,
                 tasks: FilePath,
                 probes: Tuple[str, ...],
                 probe_instructions_path: FilePath = "text/probe instructions.csv"):
        self._tasks = {}

    def _load_tasks(self, path: str):
        with open(path, mode="r", encoding="UTF-8") as instructions_file:
            reader = csv.DictReader(instructions_file)
            for row in reader:
                self._tasks[row["ID"]] = (row["many"], row["few"])
