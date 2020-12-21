from typing import List

import numpy
import simpy

from machine import Machine
from road_conditions import RoadConditionsState
from user_memory import UserMemory


class Task(object):
    def __init__(self, env: simpy.Environment, row: List, resources,
                 machine: Machine,
                 road_conditions: RoadConditionsState, user_memory: UserMemory):
        """
        :param name:
        :param cognitive_workload:
        :param perceptional_workload:
        :param done_in:
        :param priority:
        """
        self.name = row[0]
        self.description = row[1]
        self.location = row[2]
        self.cognitive_workload = row[6]
        self.visual = row[7]
        self.visual_peripheral = row[8]
        self.sound_vocal = row[9]
        self.sound_non_vocal = row[10]
        self.haptic_hands = row[11]
        self.haptic_seat = row[12]
        self.psychomotor = row[13]
        self.duration = row[14]
        self.gaze_time = row[15]
        self.total_time = row[16]
        self.triggered_by = [x.strip() for x in row[17].split(',')]
        self.awareness_parameter = [x.strip() for x in row[18].split(',')]
        self.command = [x.strip() for x in row[19].split(',')]
        self.trigger = [x.strip() for x in row[20].split(',')]
        self.priority = row[21]
        self.persona = row[22]
        self.perceptional_workload = int(self.visual or 0) + int(self.visual_peripheral or 0) + int(
            self.sound_vocal or 0) + int(self.sound_non_vocal or 0) + int(self.haptic_hands or 0) + int(
            self.haptic_seat or 0) + int(self.psychomotor or 0)

        if self.priority == 'Highest':
            self.priority = 1
        elif self.priority == 'High':
            self.priority = 2
        elif self.priority == 'Middle':
            self.priority = 3
        elif self.priority == 'Low':
            self.priority = 4
        elif self.priority == 'Lowest':
            self.priority = 5

        if self.total_time == '':
            self.total_time = 0

        self.env = env
        self.resources = resources
        self.status = False
        self.user_memory = user_memory
        self.road_conditions = road_conditions
        self.machine = machine
        self.finished_general: simpy.Event = self.env.event()
        self.finished_control: simpy.Event = self.env.event()
        self.task_interrupted: simpy.Event = self.env.event()

    def task_execution(self, choice):
        if self.visual != '':
            with self.resources[0].request(priority=self.priority, preempt='machine' in self.triggered_by) as req1:
                yield req1
                # if 'machine' in self.triggered_by:
                #     yield simpy.AllOf(self.env, [req1, req2, req3]) | self.env.timeout(0.1)
                # else:
                #     yield simpy.AllOf(self.env, [req1, req2, req3]) | self.env.timeout(5)
                # if not all([x.processed for x in [req1, req2, req3]]):
                #     if req2.processed:
                #         self.resources[7]._level = self.resources[7].level - self.cognitive_workload
                #     if req3.processed:
                #         self.resources[8]._level = self.resources[8].level - self.perceptional_workload
                #     try:
                #         self.task_interrupted.succeed()
                #     except RuntimeError:
                #         pass
                #     self.env.exit()

        elif self.visual_peripheral != '':
            with self.resources[1].request(priority=self.priority, preempt='machine' in self.triggered_by) as req1:
                yield req1
                # if 'machine' in self.triggered_by:
                #     yield simpy.AllOf(self.env, [req1, req2, req3]) | self.env.timeout(0.1)
                # else:
                #     yield simpy.AllOf(self.env, [req1, req2, req3]) | self.env.timeout(5)
                # if not all([x.processed for x in [req1, req2, req3]]):
                #     if req2.processed:
                #         self.resources[7]._level = self.resources[7].level - self.cognitive_workload
                #     if req3.processed:
                #         self.resources[8]._level = self.resources[8].level - self.perceptional_workload
                #     try:
                #         self.task_interrupted.succeed()
                #     except RuntimeError:
                #         pass
                #     self.env.exit()

        elif self.sound_vocal != '':
            with self.resources[2].request(priority=self.priority, preempt='machine' in self.triggered_by) as req1:
                yield req1
                #     yield simpy.AllOf(self.env, [req1, req2, req3]) | self.env.timeout(0.1)
                # else:
                #     yield simpy.AllOf(self.env, [req1, req2, req3]) | self.env.timeout(5)
                # if not all([x.processed for x in [req1, req2, req3]]):
                #     if req2.processed:
                #         self.resources[7]._level = self.resources[7].level - self.cognitive_workload
                #     if req3.processed:
                #         self.resources[8]._level = self.resources[8].level - self.perceptional_workload
                #     try:
                #         self.task_interrupted.succeed()
                #     except RuntimeError:
                #         pass
                #     self.env.exit()

        elif self.sound_non_vocal != '':
            with self.resources[3].request(priority=self.priority, preempt='machine' in self.triggered_by) as req1:
                yield req1
                # if 'machine' in self.triggered_by:
                #     yield simpy.AllOf(self.env, [req1, req2, req3]) | self.env.timeout(0.1)
                # else:
                #     yield simpy.AllOf(self.env, [req1, req2, req3]) | self.env.timeout(5)
                # if not all([x.processed for x in [req1, req2, req3]]):
                #     if req2.processed:
                #         self.resources[7]._level = self.resources[7].level - self.cognitive_workload
                #     if req3.processed:
                #         self.resources[8]._level = self.resources[8].level - self.perceptional_workload
                #     try:
                #         self.task_interrupted.succeed()
                #     except RuntimeError:
                #         pass
                #     self.env.exit()

        elif self.haptic_hands != '':
            with self.resources[4].request(priority=self.priority, preempt='machine' in self.triggered_by) as req1:
                yield req1
                # if 'machine' in self.triggered_by:
                #     yield simpy.AllOf(self.env, [req1, req2, req3]) | self.env.timeout(0.1)
                # else:
                #     yield simpy.AllOf(self.env, [req1, req2, req3]) | self.env.timeout(5)
                # if not all([x.processed for x in [req1, req2, req3]]):
                #     if req2.processed:
                #         self.resources[7]._level = self.resources[7].level - self.cognitive_workload
                #     if req3.processed:
                #         self.resources[8]._level = self.resources[8].level - self.perceptional_workload
                #     try:
                #         self.task_interrupted.succeed()
                #     except RuntimeError:
                #         pass
                #     self.env.exit()


        elif self.haptic_seat != '':
            with self.resources[5].request(priority=self.priority, preempt='machine' in self.triggered_by) as req1:
                yield req1
                # if 'machine' in self.triggered_by:
                #     yield simpy.AllOf(self.env, [req1, req2, req3]) | self.env.timeout(0.1)
                # else:
                #     yield simpy.AllOf(self.env, [req1, req2, req3]) | self.env.timeout(5)
                # if not all([x.processed for x in [req1, req2, req3]]):
                #     if req2.processed:
                #         self.resources[7]._level = self.resources[7].level - self.cognitive_workload
                #     if req3.processed:
                #         self.resources[8]._level = self.resources[8].level - self.perceptional_workload
                #     try:
                #         self.task_interrupted.succeed()
                #     except RuntimeError:
                #         pass
                #     self.env.exit()

        elif self.psychomotor != '':
            with self.resources[6].request(priority=self.priority, preempt='machine' in self.triggered_by) as req1:
                yield req1
                # if 'machine' in self.triggered_by:
                #     yield simpy.AllOf(self.env, [req1, req2, req3]) | self.env.timeout(0.1)
                # else:
                #     yield simpy.AllOf(self.env, [req1, req2, req3]) | self.env.timeout(5)
                # if not all([x.processed for x in [req1, req2, req3]]):
                #     if req2.processed:
                #         self.resources[7]._level = self.resources[7].level - self.cognitive_workload
                #     if req3.processed:
                #         self.resources[8]._level = self.resources[8].level - self.perceptional_workload
                #     try:
                #         self.task_interrupted.succeed()
                #     except RuntimeError:
                #         pass
                #     self.env.exit()

        if (self.resources[7].level + self.cognitive_workload > self.resources[7].capacity) or (
                self.resources[8].level + self.perceptional_workload > self.resources[8].capacity) and (
                'machine' in self.triggered_by):
            try:
                self.task_interrupted.succeed()
            except RuntimeError:
                pass
        else:
            yield self.resources[7].put(self.cognitive_workload) & self.resources[8].put(self.perceptional_workload)
            self.resources[7]._level = numpy.round(self.resources[7]._level, 3)
            self.resources[8]._level = numpy.round(self.resources[8]._level, 3)
            try:
                self.status = True
                yield self.env.timeout(self.total_time)
                yield self.resources[7].get(self.cognitive_workload) & self.resources[8].get(self.perceptional_workload)
                self.resources[8]._level = numpy.round(self.resources[8]._level, 3)
                self.resources[7]._level = numpy.round(self.resources[7]._level, 3)
                self.status = False
            except simpy.Interrupt:
                try:
                    self.task_interrupted.succeed()
                except RuntimeError:
                    pass

            if 'user_switch_regime' in self.trigger:
                if choice is None:
                    self.env.exit()
                try:
                    self.finished_control.succeed(choice)
                    self.finished_general.succeed()
                except RuntimeError:
                    pass
            else:
                self.update_awareness_param()
                try:
                    self.finished_general.succeed()
                except RuntimeError:
                    pass

        # self.resources[7]._level = self.resources[7].level - self.cognitive_workload
        # self.resources[8]._level = self.resources[8].level - self.perceptional_workload

        # if not self.finished.processed:
        # print('---' + str(self.name))

        # self.finished = self.env.event()

    def update_awareness_param(self):
        if 'road_conditions' in self.awareness_parameter:
            self.user_memory.update_conditions(self.road_conditions.get_state())
        elif 'ad_status' in self.awareness_parameter:
            self.user_memory.update_ad_status(self.road_conditions.get_state())
        elif 'ad_status_time' in self.awareness_parameter:
            self.user_memory.update_ad_status_and_time(self.road_conditions.get_state())
        elif 'machine_state' in self.awareness_parameter:
            self.user_memory.update_machine_state(self.machine.get_state_index())
        elif 'ad_activated' in self.awareness_parameter:
            self.user_memory.update_ad_activated(self.machine.get_state_index())
        elif 'tor_status' in self.awareness_parameter:
            self.user_memory.update_tor_status(self.machine.get_state_index())
        elif 'speed' in self.awareness_parameter:
            pass
