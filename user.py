import random

import simpy

from machine import Machine
from road_conditions import RoadConditionsState
from task_list import TaskList
from user_memory import UserMemory


def exponential_process(mean, minimal):
    """Return time until next regime will change."""
    return (minimal + random.expovariate(1. / (mean - minimal))) * 60


def uniform_process(min, max):
    """Return time until next regime will change."""
    return random.uniform(min, max)


class User(object):
    def __init__(self, env: simpy.Environment, user_memory: UserMemory, machine: Machine,
                 road_conditions: RoadConditionsState, task_list: TaskList, params: dict):
        self.env = env
        self.env.process(self.run_shift_regime())
        self.env.process(self.run_check_ad_status())
        self.env.process(self.run_check_ad_status_and_time())
        self.env.process(self.run_check_road_conditions())
        self.env.process(self.run_check_machine_state())
        self.env.process(self.run_check_ad_activated())
        self.env.process(self.run_tor60())
        self.env.process(self.run_check_speed())
        self.env.process(self.run_steer())
        # self.env.process(self.run_tor10())
        self.CHANGE_REGIME_MEAN = params.get('CHANGE_REGIME_MEAN') / 60
        self.CHECK_AD_STATUS_MEAN = params.get('CHECK_AD_STATUS_MEAN') / 60
        self.CHECK_AD_STATUS_AND_TIME_MEAN = params.get('CHECK_AD_STATUS_AND_TIME_MEAN') / 60
        self.CHECK_CONDITIONS_MEAN = params.get('CHECK_CONDITIONS_MEAN') / 60
        self.CHECK_MACHINE_STATE = params.get('CHECK_MACHINE_STATE') / 60
        self.CHECK_AD_ACTIVATED = params.get('CHECK_AD_ACTIVATED') / 60
        self.CHECK_SPEED = params.get('CHECK_SPEED') / 60
        self.STEER = params.get('STEER') / 60
        self.TOR60_SWITCH = eval(params.get('TOR60_SWITCH'))
        self.TOR10_SWITCH = eval(params.get('TOR10_SWITCH'))
        self.USER_PREFERENCES = eval(params.get('USER_PREFERENCES'))
        self.user_memory = user_memory
        self.machine = machine
        self.road_conditions = road_conditions
        self.task_list = task_list

    def reload(self):
        self.user_memory.tor60 = self.env.event()
        self.env.process(self.run_tor60())

    def run_shift_regime(self):
        while True:
            yield self.env.timeout(exponential_process(self.CHANGE_REGIME_MEAN, 0.2 * self.CHANGE_REGIME_MEAN))
            if self.user_memory.machine_state < self.user_memory.available_levels:
                if not self.road_conditions.tor10.processed and not self.road_conditions.tor60.processed:
                    levels_available = [x for x in [0, 1, 2, 4] if x <= self.user_memory.available_levels]
                    pref = [self.USER_PREFERENCES[i] for i in range(len(levels_available))]
                    choice = random.choices([x for x in levels_available], pref)[
                        0]
                    # print(str(levels_available) + ' ' + str(choice))
                    if choice != self.user_memory.machine_state:
                        self.task_list.run_control_task(choice='L' + str(choice) + '_user_switch')

    def run_tor60(self):
        yield self.user_memory.tor60
        tau = uniform_process(self.TOR60_SWITCH[0], self.TOR60_SWITCH[1])
        print('----- user will change the level at' + str(int(self.env.now / 60)) + ':' + str(int(self.env.now % 60)).zfill(2))
        yield self.env.timeout(tau)

        levels_available = [x for x in [0, 1, 2, 4] if x <= self.user_memory.available_levels]
        pref = [self.USER_PREFERENCES[i] for i in range(len(levels_available))]
        choice = random.choices([x for x in levels_available], pref)[0]

        if self.machine.get_state_index() == 3.8 or self.machine.get_state_index() == 3.5:
            self.task_list.run_control_task(choice='L' + str(choice) + '_user_switch')
            # self.machine.on_event(self.env.timeout(0, value='L2' + '_switch'))
        self.reload()

    # def run_tor10(self):
    #     while True:
    #         yield self.user_memory.tor10
    #         tau = uniform_process(self.TOR10_SWITCH[0], self.TOR10_SWITCH[1])
    #         if tau > 10:
    #             tau = 10
    #         yield self.env.timeout(tau)
    #         if self.machine.get_state_index() == 3.5:
    #             self.task_list.run_control_task(choice='L2' + '_user_switch')
                # self.machine.on_event(self.env.timeout(0, value='L2' + '_switch'))

    def run_check_ad_status(self):
        while True:
            yield self.env.timeout(exponential_process(self.CHECK_AD_STATUS_MEAN, 0.2 * self.CHECK_AD_STATUS_MEAN))
            self.check_ad_status()

    def run_check_ad_status_and_time(self):
        while True:
            yield self.env.timeout(
                exponential_process(self.CHECK_AD_STATUS_AND_TIME_MEAN, 0.2 * self.CHECK_AD_STATUS_AND_TIME_MEAN))
            self.check_ad_status_and_time()

    def run_check_road_conditions(self):
        while True:
            yield self.env.timeout(exponential_process(self.CHECK_CONDITIONS_MEAN, 0.2 * self.CHECK_CONDITIONS_MEAN))
            self.check_conditions()

    def run_check_machine_state(self):
        while True:
            yield self.env.timeout(exponential_process(self.CHECK_MACHINE_STATE, 0.2 * self.CHECK_CONDITIONS_MEAN))
            self.check_machine_state()

    def run_check_ad_activated(self):
        while True:
            yield self.env.timeout(exponential_process(self.CHECK_AD_ACTIVATED, 0.2 * self.CHECK_AD_ACTIVATED))
            self.check_ad_activated()

    def run_check_speed(self):
        while True:
            yield self.env.timeout(exponential_process(self.CHECK_SPEED, 0.2 * self.CHECK_SPEED))
            if self.machine.get_state_index() <= 3:
                self.check_speed()

    def run_steer(self):
        while True:
            yield self.env.timeout(exponential_process(self.STEER, 0.2 * self.STEER))
            if self.machine.get_state_index() <= 3:
                self.steer()

    def check_conditions(self):
        self.task_list.run_monitoring_task(awareness_parameter='road_conditions')
        self.user_memory.update_conditions(self.road_conditions.get_state())

    def check_ad_status(self):
        self.task_list.run_monitoring_task(awareness_parameter='ad_status')
        self.user_memory.update_ad_status(self.road_conditions.get_state())

    def check_ad_status_and_time(self):
        self.task_list.run_monitoring_task(awareness_parameter='ad_status_time')
        self.user_memory.update_ad_status(self.road_conditions.get_state())

    def check_machine_state(self):
        self.task_list.run_monitoring_task(awareness_parameter='machine_state')
        self.user_memory.update_machine_state(self.machine.get_state_index())

    def check_ad_activated(self):
        self.task_list.run_monitoring_task(awareness_parameter='ad_activated')
        self.user_memory.update_ad_activated(self.machine.get_state_index())

    def check_speed(self):
        self.task_list.run_monitoring_task(awareness_parameter='speed')

    def steer(self):
        self.task_list.run_control_task(choice='Steer')

        
