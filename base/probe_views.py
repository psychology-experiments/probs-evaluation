from abc import ABCMeta, abstractmethod
from typing import List, Optional, Tuple
from pathlib import Path

from psychopy import visual

from base import probe_presenters


class AbstractProbeViw(metaclass=ABCMeta):
    @abstractmethod
    def next_probe(self) -> None:
        pass

    @abstractmethod
    def get_press_correctness(self, pressed_key_name: str) -> bool:
        pass

    @abstractmethod
    def draw(self, t: float) -> None:
        pass


class ProbeView(AbstractProbeViw):
    def __init__(self,
                 window: visual.Window,
                 probes: List[str],
                 answers: Optional[List[str]],
                 image_path_dir: str,
                 probe_type: str,
                 position: Tuple[int, int] = (0, 0),
                 start_time: float = 0.1,
                 image_ext: str = "png"
                 ):
        self._presenter_probe: Optional[probe_presenters.Probe] = None
        self._start_time: float = start_time
        self.visual_probes: List[visual.basevisual] = []
        self._current_probe: Optional[visual.basevisual] = None
        self._window: visual.Window = window

        self._presenter_probe = probe_presenters.Probe(probes, answers, probe_type)

        path: Path = Path(image_path_dir)
        for probe_name in probes:
            image_path = path.joinpath(f"{probe_name}.{image_ext}")
            probe = visual.ImageStim(win=self._window,
                                     image=image_path,
                                     pos=position,
                                     )
            self.visual_probes.append(probe)

        self._current_probe = self.visual_probes[self._presenter_probe.get_probe_number()]

    def next_probe(self) -> None:
        self._presenter_probe.next_probe()
        self._current_probe = self.visual_probes[self._presenter_probe.get_probe_number()]

    def get_press_correctness(self, pressed_key_name: str) -> bool:
        return self._presenter_probe.get_press_correctness(pressed_key_name)

    def draw(self, t: float) -> None:
        if t >= self._start_time:
            self._current_probe.draw()
