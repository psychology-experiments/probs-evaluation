import collections
import configparser
import itertools

from psychopy import core, event, visual
from psychopy.hardware import keyboard

from base import data_save, experiment_organization_logic, experiment_organization_stimuli, probe_views, task_views

MODE = "TEST"

SETTINGS_FP = f"configurations/settings.ini"
SETTINGS_PARSER = configparser.ConfigParser()
SETTINGS_PARSER.read(SETTINGS_FP, encoding="UTF-8")
SETTINGS = SETTINGS_PARSER[MODE]

FULL_SCREEN = SETTINGS.getboolean("full_screen")
SKIP_INSTRUCTION = SETTINGS.getboolean("skip_instruction")
SKIP_PROBE_TRAINING = SETTINGS.getboolean("skip_probe_training")
SKIP_TASK_TRAINING = SETTINGS.getboolean("skip_task_training")
SKIP_EXPERIMENTAL_TASK = SETTINGS.getboolean("skip_experimental_task")

FRAME_TOLERANCE = 0.001  # how close to onset before 'same' frame TODO: проверить что используется правильно
PROBE_START = 0.1
# EXPERIMENTAL_PROBE_POSITION = dict(Торможение=(0, -300), Обновление=(0, -209), Переключение=(0, -275))
EXPERIMENTAL_PROBE_POSITION = (0, -300)
PROBES_TRAINING_POSITION = (0, 0)
INSIGHT_TASK_POSITION = (0, 100)

QUIT_KEYS = ["escape"]


def skip_all_tasks_except(task_name: str, show: str, mode=MODE) -> bool:
    return mode == "TEST" and task_name != show and show != "all"


def skip_all_probes_except(_probe_name: str, show: str, mode=MODE) -> bool:
    return mode == "TEST" and _probe_name != show and show != "all"


def finish_experiment(window: visual.Window):
    """
    PsychoPy выдаёт ошибки при завершении скрипта, которые никак не мешают исполнению, но мешают отладке.
    Данный код попытка их игнорировать
    """
    from contextlib import suppress

    with suppress(Exception):
        window.close()
        core.quit()


win = visual.Window(size=(1200, 800), color="white", units="pix", fullscr=FULL_SCREEN)
data_saver = data_save.DataSaver(save_fp="data/insight/test", experiment_part=data_save.ExperimentPart.INSIGHT)
instruction = experiment_organization_stimuli.InstructionImage(window=win, skip=SKIP_INSTRUCTION)
organisation_message = experiment_organization_stimuli.GeneralInstructions(fp="images/Инструкции/Общие/Insight",
                                                                           window=win,
                                                                           skip=SKIP_INSTRUCTION)

# Подготовка зондов для эксперимента
probe_two_alternatives = probe_views.ProbeView(window=win,
                                               probes=["green", "red"],
                                               answers=["right", "left"],
                                               probe_type="TwoAlternatives",
                                               start_time=PROBE_START,
                                               image_path_dir="images/Выбор из 2 альтернатив/",
                                               position=PROBES_TRAINING_POSITION)

probes_update = probe_views.ProbeView(window=win,
                                      probes=["1", "2", "3"],
                                      answers=None,
                                      probe_type="Update",
                                      start_time=PROBE_START,
                                      image_path_dir="images/Обновление/",
                                      position=PROBES_TRAINING_POSITION)

probe_switch = probe_views.ProbeView(window=win,
                                     probes=list("12345678"),
                                     answers=["right", "right", "left", "right", "left", "left", "left", "right"],
                                     probe_type="Switch",
                                     start_time=PROBE_START,
                                     image_path_dir="images/Переключение/",
                                     position=PROBES_TRAINING_POSITION)

inhibition_probes = ["".join(colorful_word) for colorful_word in itertools.product("RGBY", repeat=2)]
inhibition_right_answers = dict(R="right", Y="right", G="left", B="left")
inhibition_answers = [inhibition_right_answers[probe[1]] for probe in inhibition_probes]

probe_inhibition = probe_views.ProbeView(window=win,
                                         probes=inhibition_probes,
                                         answers=inhibition_answers,
                                         probe_type="Inhibition",
                                         start_time=PROBE_START,
                                         image_path_dir="images/Торможение/",
                                         position=PROBES_TRAINING_POSITION)

all_probes = collections.OrderedDict((
    ("Выбор из 2 альтернатив", probe_two_alternatives),
    ("Обновление", probes_update),
    ("Переключение", probe_switch),
    ("Торможение", probe_inhibition),
))

experimental_probes = collections.OrderedDict((
    ("Обновление", probes_update),
    ("Переключение", probe_switch),
    ("Торможение", probe_inhibition),
))

# Подготовка устройств ввода
single_keyboard = keyboard.Keyboard()
quit_keyboard = keyboard.Keyboard()
mouse = event.Mouse(visible=False, win=win)

# Подготовка заданий для эксперимента

# экспериментальная серия
insight_task = task_views.InsightTask(window=win,
                                      position=INSIGHT_TASK_POSITION,
                                      text_size=40)

# Начало эксперимента?
# подготовка часов

training_probe_sequence = experiment_organization_logic.TrainingSequence(probes_sequence=tuple(all_probes),
                                                                         trials=50,
                                                                         instruction_type="one")
experiment_sequence = experiment_organization_logic.ExperimentInsightTaskSequence(id_column="ID",
                                                                                  tasks_fp="text/insight tasks.csv",
                                                                                  probes=tuple(experimental_probes),
                                                                                  instruction_type="two")
# TODO: create instructions for type two

trial_clock = core.Clock()
task_solution_clock = core.Clock()
experiment_clock = core.Clock()
# тренировка с зондами
if not SKIP_PROBE_TRAINING:
    for probe_name, instruction_text, number_of_trials in training_probe_sequence:
        data_saver.new_probe()
        probe = all_probes[probe_name]

        instruction.show(path=instruction_text)

        print(number_of_trials)
        for trial in number_of_trials:
            # сейчас RT - от времени отрисовки зонда

            print(f"\n{probe_name}")

            probe_started = False

            _timeToFirstFrame = win.getFutureFlipTime(clock="now")
            trial_clock.reset(-_timeToFirstFrame)
            while True:
                tThisFlip = win.getFutureFlipTime(clock=trial_clock)

                if probe_started:
                    keys = single_keyboard.getKeys(keyList=["right", "left"],
                                                   waitRelease=False)
                    if keys:
                        button = keys[0]
                        key_name, key_rt = button.name, button.rt
                        is_correct = probe.get_press_correctness(key_name)
                        print(is_correct, key_name, key_rt)

                        data_saver.save_probe_practice(probe_name=probe_name,
                                                       is_correct=is_correct,
                                                       rt=key_rt,
                                                       time_from_experiment_start=experiment_clock.getTime())
                        probe.next_probe()
                        break

                if not probe_started and tThisFlip >= PROBE_START - FRAME_TOLERANCE:
                    probe_started = True
                    win.callOnFlip(single_keyboard.clock.reset)  # t=0 on next screen flip
                    win.callOnFlip(single_keyboard.clearEvents,
                                   eventType='keyboard')  # clear events on next screen flip

                probe.draw(tThisFlip + FRAME_TOLERANCE)

                win.flip()

                if quit_keyboard.getKeys(keyList=QUIT_KEYS):
                    finish_experiment(window=win)

# ЭКСПЕРИМЕНТАЛЬНАЯ ЧАСТЬ
for task_info, probe_info in experiment_sequence:
    # Часть с инструкциями
    organisation_message.show()
    instruction.show(path=task_info.instruction)

    if skip_all_tasks_except(task_info.name, SETTINGS.get("show_task")):
        continue

    if skip_all_probes_except(probe_info.name, SETTINGS.get("show_probe")):
        continue

    organisation_message.show()
    instruction.show(path=probe_info.instruction)
    organisation_message.show()

    # часть с экспериментальными заданиями
    data_saver.new_task(task_info.name, stage="experimental", task_type=task_info.type)
    data_saver.new_probe()

    probe = experimental_probes[probe_info.name]
    probe.prepare_for_new_task()
    # Подготовить позицию с зондами для задачи
    # probe.position = EXPERIMENTAL_PROBE_POSITION[task_info.name]
    probe.position = EXPERIMENTAL_PROBE_POSITION

    previous_buttons_state = mouse.getPressed()
    win.callOnFlip(function=mouse.clickReset)  # TODO: попробовать сделать решения задачи ближе к реальному
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    task_solution_clock.reset(-_timeToFirstFrame)
    print(task_info.name)
    print("before finished", insight_task.is_task_finished())
    insight_task.new_task(text=task_info.content)
    print("after finished", insight_task.is_task_finished())
    while not insight_task.is_task_finished():
        probe_started = False

        trial_clock.reset(-_timeToFirstFrame)
        while True:
            tThisFlip = win.getFutureFlipTime(clock=trial_clock)

            # probe code
            if probe_started:
                keys = single_keyboard.getKeys(keyList=["right", "left"],
                                               waitRelease=False)
                if keys:
                    button = keys[0]
                    key_name, key_rt = button.name, button.rt
                    is_correct = probe.get_press_correctness(key_name)
                    print(is_correct, key_name, key_rt)

                    data_saver.save_experimental_probe_data(probe_name=probe_info.name,
                                                            is_correct=is_correct,
                                                            rt=key_rt,
                                                            time_from_experiment_start=experiment_clock.getTime())
                    probe.next_probe()
                    break

            if not probe_started and tThisFlip >= PROBE_START - FRAME_TOLERANCE:
                probe_started = True
                win.callOnFlip(single_keyboard.clock.reset)  # t=0 on next screen flip
                win.callOnFlip(single_keyboard.clearEvents,
                               eventType='keyboard')  # clear events on next screen flip

            probe.draw(tThisFlip + FRAME_TOLERANCE)

            # task code
            buttons_pressed, times = mouse.getPressed(getTime=True)

            if buttons_pressed != previous_buttons_state:
                previous_buttons_state = buttons_pressed

                if buttons_pressed[0]:
                    insight_task.finish_task()
                    press_time = times[0]
                    print("saved", press_time)
                    data_saver.save_experimental_task_data(solution_time=task_solution_clock.getTime(),
                                                           time_from_experiment_start=experiment_clock.getTime())

            if insight_task.is_task_finished():
                print("experiment: is_task_finished")
                print("\n\n")
                break

            insight_task.draw()
            win.flip()

            if quit_keyboard.getKeys(keyList=QUIT_KEYS):
                finish_experiment(window=win)

            keys = single_keyboard.getKeys(keyList=["w"])
            if keys and keys[0] == "w":
                task_finished = True
                break

experiment_organization_stimuli.EndMessage(win).show(5, experiment_clock)
data_saver.close()
finish_experiment(window=win)
