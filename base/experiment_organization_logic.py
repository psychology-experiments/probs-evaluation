import csv
import random
from itertools import count, product
from random import choice, shuffle
from typing import List, Union, Iterator, Dict, Optional, Tuple, NamedTuple, Any


class ProbeInfo(NamedTuple):
    name: str
    instruction: str
    trials: Iterator


class WMTaskInfo(NamedTuple):
    name: str
    instruction: str
    trained: bool


class InsightTaskInfo(NamedTuple):
    name: str
    type: str
    instruction: str
    content: str


FilePath = str


class TrainingSequence:
    def __init__(self,
                 probes_sequence: Tuple[str, ...],
                 trials: Optional[Union[List[int], int]] = 30,
                 probe_instructions_path: FilePath = "text/probe instructions one.csv", ):

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
                 probe_instructions_path: FilePath = "text/probe instructions one.csv"):
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

    def __getitem__(self, item) -> Tuple[WMTaskInfo, ProbeInfo]:
        probe = self._probes_sequence[item]

        task_name = self._tasks_sequence[item]
        task_instruction = self._task_instructions[task_name]
        showed = self._task_showed[task_name]

        if not self._task_showed[task_name]:
            self._task_showed[task_name] = True

        task = WMTaskInfo(name=task_name,
                          instruction=task_instruction,
                          trained=showed)

        return task, probe


class ExperimentInsightTaskSequence:
    """
    Create sequence of insight tasks and probes
    """

    def __init__(self,
                 id_column: str,
                 tasks_fp: FilePath,
                 probes: Tuple[str, ...],
                 tasks_conditions_per_probe: int = 2,
                 task_instruction_path: FilePath = "images/????????????????????/??????????????/?????????????????? ????????????.png",
                 probe_instructions_path: FilePath = "text/probe instructions two.csv"):
        self._task_instruction_path = task_instruction_path
        self._tasks: Dict[str, Dict[str, str]] = {}
        self._load_tasks(tasks_fp, id_column)

        probes_for_tasks = self._generate_probes(probes)
        self._probes_sequence = TrainingSequence(probes_sequence=probes_for_tasks,
                                                 trials=None,
                                                 probe_instructions_path=probe_instructions_path)
        self._probes_conditions = self._generate_probe_conditions(probes, tasks_conditions_per_probe)
        self._participants_data: Optional[Dict[str, Tuple[float]]] = None
        self._load_participants_data()

    def _generate_probes(self, probes) -> Tuple[Any, ...]:
        number_of_each_probe_use = len(self._tasks) / len(probes)

        if not number_of_each_probe_use.is_integer():
            raise ValueError(f"Quantity of tasks {self._tasks} is not multiple to probes {len(probes)}")

        number_of_each_probe_use = int(number_of_each_probe_use)
        probes_for_tasks = list(probes * number_of_each_probe_use)
        shuffle(probes_for_tasks)
        return tuple(probes_for_tasks)

    def _generate_probe_conditions(self, probes, repeat):
        conditions = tuple(choice(tuple(self._tasks.values())).keys())
        return {probe: list(conditions * repeat) for probe in probes}

    def _load_tasks(self,
                    path: str,
                    id_column: str) -> None:
        with open(path, mode="r", encoding="UTF-8") as instructions_file:
            reader = csv.DictReader(instructions_file)
            for row in reader:
                self._tasks[row[id_column]] = {task_type: task_text
                                               for task_type, task_text in row.items()
                                               if task_type != id_column}

    def _load_participants_data(self):  # TODO: ?????????????? ?????? ?????????? ???????????????????? ?? ?????? ?????????????????????? ?????????? ??????????
        pass

    def _get_task_type_based_on_participants_data(self, conditions, task):
        if self._participants_data is None:
            return random.choices(population=list(set(conditions)), weights=[0.5, 0.5])[0]

        return random.choices(population=list(set(conditions)), weights=self._participants_data[task])[0]

    def _choose_task(self, probe_name: str) -> Tuple[str, str, str]:
        possible_conditions = self._probes_conditions[probe_name]
        chosen_task_id, task_types = choice(list(self._tasks.items()))
        del self._tasks[chosen_task_id]

        task_type = possible_conditions[0]
        if self._is_task_type_can_be_chosen(possible_conditions):
            task_type = self._get_task_type_based_on_participants_data(possible_conditions, chosen_task_id)

        self._probes_conditions[probe_name].remove(task_type)
        task_content = task_types[task_type]
        return chosen_task_id, task_type, task_content

    @staticmethod
    def _is_task_type_can_be_chosen(conditions):
        return len(set(conditions)) == 2

    def __getitem__(self, item) -> Tuple[InsightTaskInfo, ProbeInfo]:
        probe = self._probes_sequence[item]

        task_name, task_type, content = self._choose_task(probe_name=probe.name)
        task = InsightTaskInfo(name=task_name,
                               type=task_type,
                               instruction=self._task_instruction_path,
                               content=content)

        return task, probe
