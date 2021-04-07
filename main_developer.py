import collections
import configparser
import itertools

from psychopy import core, event, visual
from psychopy.hardware import keyboard

from base import data_save, experiment_organisation_logic, experiment_organisation_stimuli, probe_views, task_views

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

TRAINING_TRAILS_QTY = dict(Обновление=1, Переключение=10, Торможение=2)
EXPERIMENTAL_TASK_ONE_SOLUTION_SETTINGS = dict(Обновление=dict(blocks_finishing_task=5),
                                               Переключение=dict(trials_finishing_task=20,
                                                                 rule_changes_finishing_task=4),
                                               Торможение=dict(trials_finishing_task=5),
                                               )

FRAME_TOLERANCE = 0.001  # how close to onset before 'same' frame TODO: проверить что используется правильно
PROBE_START = 0.1
EXPERIMENTAL_PROBE_POSITION = (0, -200)
PROBES_TRAINING_POSITION = (0, 0)
EXPERIMENTAL_TASK_POSITION = (0, 300)
TRAINING_TASK_POSITION = (0, 0)

FIRST_DOUBLE_TASK_PREPARATION_MESSAGE = "Сейчас вам нужно будет выполнять два задания одновременно.\n" \
                                        "Для перехода к инструкции первого заданию нажмите ПРОБЕЛ"
SECOND_DOUBLE_TASK_PREPARATION_MESSAGE = "Для перехода к инструкции второго заданию нажмите ПРОБЕЛ"
LAST_PREPARATION_MESSAGE = "После нажатия на ПРОБЕЛ необходимо будет выполнять описанные ранее задания одновременно"

QUIT_KEYS = ["escape"]


def change_mouse_visibility(mouse_component: event.Mouse,
                            task_name: str,
                            trial_task):
    if task_name == "Переключение":
        trial_task.prepare_mouse()
    elif mouse_component.visible:
        mouse_component.setVisible(False)


def skip_all_tasks_except(task_name: str, show: str, mode=MODE) -> bool:
    return mode == "TEST" and task_name != show


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
data_saver = data_save.DataSaver(save_fp="data/test")
# data_saver = data.ExperimentHandler(dataFileName="data/test", version="2020.2.10", autoLog=False, savePickle=False)
instruction = experiment_organisation_stimuli.InstructionImage(window=win, skip=SKIP_INSTRUCTION)
organisation_message = experiment_organisation_stimuli.InstructionText(window=win, skip=SKIP_INSTRUCTION)

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

experimental_probes = all_probes.copy()
del experimental_probes["Выбор из 2 альтернатив"]

# Подготовка устройств ввода
single_keyboard = keyboard.Keyboard()
quit_keyboard = keyboard.Keyboard()
mouse = event.Mouse(visible=False, win=win)

# Подготовка заданий для эксперимента

# тренировочная серия
task_update = task_views.UpdateTaskView(window=win,
                                        stimuli_fp="text/Operation span task practice.csv",
                                        word_show_time=0.750,
                                        blocks_finishing_task=TRAINING_TRAILS_QTY["Обновление"],
                                        possible_task_sequences=(4,),
                                        position=TRAINING_TASK_POSITION)

task_switch = task_views.WisconsinTestTaskView(window=win,
                                               image_path_dir="images/Висконсинский тест",
                                               mouse=mouse,
                                               max_streak=8,
                                               trials_finishing_task=TRAINING_TRAILS_QTY["Переключение"],
                                               rule_changes_finishing_task=TRAINING_TRAILS_QTY["Переключение"],
                                               position=TRAINING_TASK_POSITION)

task_inhibition = task_views.InhibitionTaskView(window=win,
                                                stimuli_fp="images/Tower of London/training",
                                                trials_finishing_task=TRAINING_TRAILS_QTY["Торможение"],
                                                position=TRAINING_TASK_POSITION)

training_tasks = collections.OrderedDict((
    ("Обновление", task_update),
    ("Переключение", task_switch),
    ("Торможение", task_inhibition),
))

# экспериментальная серия
task_update = task_views.UpdateTaskView(window=win,
                                        stimuli_fp="text/Operation span task experimental.csv",
                                        word_show_time=0.750,
                                        possible_task_sequences=(3, 4),
                                        position=EXPERIMENTAL_TASK_POSITION,
                                        **EXPERIMENTAL_TASK_ONE_SOLUTION_SETTINGS["Обновление"]
                                        )

task_switch = task_views.WisconsinTestTaskView(window=win,
                                               image_path_dir="images/Висконсинский тест",
                                               mouse=mouse,
                                               max_streak=8,
                                               position=EXPERIMENTAL_TASK_POSITION,
                                               **EXPERIMENTAL_TASK_ONE_SOLUTION_SETTINGS["Переключение"])

task_inhibition = task_views.InhibitionTaskView(window=win,
                                                stimuli_fp="images/Tower of London",
                                                position=EXPERIMENTAL_TASK_POSITION,
                                                **EXPERIMENTAL_TASK_ONE_SOLUTION_SETTINGS["Торможение"])

experimental_tasks = collections.OrderedDict((
    ("Обновление", task_update),
    ("Переключение", task_switch),
    ("Торможение", task_inhibition),
))

# Начало эксперимента?
# подготовка часов

training_probe_sequence = experiment_organisation_logic.TrainingSequence(probes_sequence=tuple(all_probes),
                                                                         trials=30)
experiment_sequence = experiment_organisation_logic.ExperimentWMSequence(tasks=tuple(experimental_tasks),
                                                                         probes=tuple(experimental_probes))

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
for probe in experimental_probes:
    probe.pos = EXPERIMENTAL_PROBE_POSITION

for task_info, probe_info in experiment_sequence:
    # Часть с инструкциями
    organisation_message.show(FIRST_DOUBLE_TASK_PREPARATION_MESSAGE)
    instruction.show(path=task_info.instruction)

    if skip_all_tasks_except(task_info.name, SETTINGS.get("show_task")):
        continue

    # тренировка с задачами
    if task_info.instruction is not None and not SKIP_TASK_TRAINING:
        data_saver.new_task(task_info.name)
        training_task = training_tasks[task_info.name]

        change_mouse_visibility(mouse, task_info.name, training_task)

        print(task_info.name)
        trial = 1  # testing variable
        training_task.new_task()
        while not training_task.is_task_finished():
            previous_buttons_state = mouse.getPressed()
            _timeToFirstFrame = win.getFutureFlipTime(clock="now")
            win.callOnFlip(function=mouse.clickReset)  # TODO: попробовать сделать решения задачи ближе к реальному
            task_solution_clock.reset(-_timeToFirstFrame)  # TODO: различается сохранение в столбец с экспериментальным
            while True:
                training_task.draw(win.getFutureFlipTime(clock="now"))

                buttons_pressed, times = mouse.getPressed(getTime=True)

                if buttons_pressed != previous_buttons_state:
                    previous_buttons_state = buttons_pressed

                    if buttons_pressed[0]:
                        if training_task.is_valid_click():  # only first mouse press is used
                            training_task.finish_trial()
                            press_time = times[0]
                            print("saved", press_time)
                            data_saver.save_task_practice(task_name=task_info.name,
                                                          solution_time=task_solution_clock.getTime(),
                                                          time_from_experiment_start=experiment_clock.getTime())

                if training_task.is_trial_finished():
                    training_task.next_subtask()
                    print("trial", trial)
                    trial += 1
                    break

                win.flip()

                if quit_keyboard.getKeys(keyList=QUIT_KEYS):
                    finish_experiment(window=win)

    if SKIP_EXPERIMENTAL_TASK:  # для отладки скрипта
        continue

    organisation_message.show(SECOND_DOUBLE_TASK_PREPARATION_MESSAGE)
    instruction.show(path=probe_info.instruction)
    organisation_message.show(LAST_PREPARATION_MESSAGE)

    # часть с экспериментальными заданиями
    data_saver.new_task(task_info.name)
    data_saver.new_probe()

    task = experimental_tasks[task_info.name]
    task_finished = False
    task_trial_finished = True
    change_mouse_visibility(mouse, task_info.name, task)

    probe = experimental_probes[probe_info.name]

    previous_buttons_state = mouse.getPressed()
    win.callOnFlip(function=mouse.clickReset)  # TODO: попробовать сделать решения задачи ближе к реальному
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    task_solution_clock.reset(-_timeToFirstFrame)
    print(task_info.name)
    print("before finished", task.is_task_finished())
    task.new_task()
    print("after finished", task.is_task_finished())
    while not task_finished:
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
                    if task.is_valid_click():  # only first mouse press is used
                        task.finish_trial()
                        press_time = times[0]
                        print("saved", press_time)
                        data_saver.save_experimental_task_data(solution_time=task_solution_clock.getTime(),
                                                               time_from_experiment_start=experiment_clock.getTime())

            if task.is_trial_finished():
                task.next_subtask()

            if task.is_task_finished():
                task_finished = True
                break

            task.draw(win.getFutureFlipTime(clock="now"))
            win.flip()

            if quit_keyboard.getKeys(keyList=QUIT_KEYS):
                finish_experiment(window=win)

            keys = single_keyboard.getKeys(keyList=["w"])
            if keys and keys[0] == "w":
                task_finished = True
                break
