import random
from typing import List

import xlrd
import simpy
import numpy as np

from machine import Machine
from road_conditions import RoadConditionsState
from task import Task
from user_memory import UserMemory


class TaskList(object):
    def __init__(self, env: simpy.Environment, sheet: xlrd.sheet, machine: Machine,
                 conditions: RoadConditionsState, user_memory: UserMemory, persona: str,
                 max_mental: int, max_perc: int):
        self.visual = simpy.PreemptiveResource(env, capacity=1)
        self.visual_peripheral = simpy.PreemptiveResource(env, capacity=1)
        self.sound_vocal = simpy.PreemptiveResource(env, capacity=1)
        self.sound_non_vocal = simpy.PreemptiveResource(env, capacity=1)
        self.haptic_hands = simpy.PreemptiveResource(env, capacity=1)
        self.haptic_seat = simpy.PreemptiveResource(env, capacity=1)
        self.psychomotor = simpy.PreemptiveResource(env, capacity=1)
        self.cognitive_workload = simpy.Container(env, capacity=max_mental)
        self.perceptional_workload = simpy.Container(env, capacity=max_perc)
        self.machine = machine
        self.road_conditions = conditions
        self.user_memory = user_memory

        # cognitive resources of human
        self.tasks = [Task(env=env, row=sheet.row_values(i),
                           resources=[self.visual, self.visual_peripheral, self.sound_vocal, self.sound_non_vocal,
                                      self.haptic_hands, self.haptic_seat,
                                      self.psychomotor, self.cognitive_workload, self.perceptional_workload],
                           machine=machine, user_memory=user_memory,
                           road_conditions=conditions) for i in np.arange(1, sheet.nrows)]
        self.tasks = [task for task in self.tasks if task.persona == persona or task.persona == '']
        self.control_tasks = [task for task in self.tasks if 'user_switch_regime' in task.trigger]
        self.env = env
        self.tasks_to_execute: List[Task] = []
        self.interrupted_tasks = []
        self.finished_tasks = []
        self.env.process(self.interrupted_tasks_monitor())
        # self.tasks_to_trigger = [(self.find_tasks_to_trigger(self.tasks, task.trigger), task.total_time) for task in
        #                          self.tasks]

    @staticmethod
    def find_tasks_to_trigger(lst1, name):
        return [task for task in lst1 for nm in name if nm == task.name]

    def execute_chained_tasks(self, choice=None):
        random.shuffle(self.tasks_to_execute)
        [self.env.process(task.task_execution(choice)) for task in self.tasks_to_execute]
        while len(self.tasks_to_execute) != 0:
            # self.tasks_to_execute.sort(key=lambda tsk: tsk.total_time)
            yield simpy.events.AnyOf(self.env, [tsk.finished_general for tsk in self.tasks_to_execute])
            try:
                index = [tsk.finished_general.processed for tsk in self.tasks].index(True)
            except ValueError:
                continue

            # print(
            #     str(self.tasks_to_execute[index].finished.processed) + ' ' + str(self.tasks_to_execute[index].name))
            chained_tasks = self.find_tasks_to_trigger(self.tasks, self.tasks[index].trigger)
            [self.tasks_to_execute.append(tsk) for tsk in chained_tasks]
            [self.env.process(tsk.task_execution(choice)) for tsk in chained_tasks]
            self.tasks[index].finished_general = self.env.event()
            self.finished_tasks.append(self.tasks[index].name)
            try:
                self.tasks_to_execute.remove(self.tasks[index])
            except ValueError:
                continue

    def run_monitoring_task(self, awareness_parameter: str):
        self.tasks_to_execute = [task for task in self.tasks if
                                 any([i == 'situation_awareness' for i in task.command]) and
                                 any([i == 'user' for i in task.triggered_by]) and
                                 any([i == awareness_parameter for i in task.awareness_parameter])]
        try:
            self.tasks_to_execute = [random.choice(self.tasks_to_execute)]
            self.env.process(self.execute_chained_tasks())
        except IndexError:
            pass

    def run_machine_triggered_tasks(self, command: str):
        self.tasks_to_execute = [task for task in self.tasks if
                                 any([i == command for i in task.command]) and
                                 any([i == 'machine' for i in task.triggered_by])]
        try:
            self.env.process(self.execute_chained_tasks())
        except IndexError:
            pass

    def run_control_task(self, choice: str):
        if choice != 'Steer':
            print('Control task', choice)
        self.tasks_to_execute = [task for task in self.tasks if
                                 any([i == 'user' for i in task.triggered_by]) and
                                 any([i == choice for i in task.command])]
        self.tasks_to_execute = [random.choice(self.tasks_to_execute)]
        self.env.process(self.execute_chained_tasks(choice))
        # self.env.process(self.user_switch_monitor(choice))

    def interrupted_tasks_monitor(self):
        while True:
            yield simpy.events.AnyOf(self.env, [tsk.task_interrupted for tsk in self.tasks])
            index = [tsk.task_interrupted.processed for tsk in self.tasks].index(True)
            print('{} is interrupted at {}'.format(self.tasks[index].name, str(int(self.env.now / 60)) + ':' + str(
                int(self.env.now % 60)).zfill(2)))
            self.interrupted_tasks.append(self.tasks[index].name)
            self.tasks[index].task_interrupted = self.env.event()
