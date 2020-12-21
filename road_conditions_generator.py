import random

from machine import Machine
from road_conditions import RoadConditions, RoadConditionsState
from task_list import TaskList
from user_memory import UserMemory
from machine_states import TOR60, TOR10


class RoadConditionsGenerator(object):
    """
    """

    def __init__(self, env, machine: Machine, user_memory: UserMemory, road_conditions: RoadConditionsState,
                 task_list: TaskList, params: dict, scenario: any):
        self.L0_MEAN = params.get('L0_MEAN') / 60  # mean time of L0 availability in minutes (+1)
        self.L1_MEAN = params.get('L1_MEAN') / 60  # mean time of L1 availability in minutes (+1)
        self.L2_MEAN = params.get('L2_MEAN') / 60  # mean time of L2 availability in minutes (+1)
        self.L4_MEAN = params.get('L4_MEAN') / 60  # mean time of L4 availability in minutes (+1)
        self.FROM_L1_TO_L0_OR_L2 = eval(params.get('FROM_L1_TO_L0_OR_L2')) # probability of shift L1 -> L0 and L1 -> L2
        self.FROM_L2_TO_L1_OR_L4 = eval(params.get('FROM_L2_TO_L1_OR_L4')) # probability of shift L2 -> L1 and L2 -> L4
        self.env = env
        self.env.process(self.l0_run())
        self.road_conditions = road_conditions
        self.machine = machine
        self.user_memory = user_memory
        self.task_list = task_list
        self.RUN_SCENARIO = bool(params.get('RUN_SCENARIO'))
        # self.time_table = [['L0', 0], ['L4', 1*60], ['L0', 7*60], ['L0', params.get('L0_MEAN')*60]]
        self.time_table = scenario
        self.time_table.append(['L0', params.get('L0_MEAN')*60])
        self.time_table_index = 1
        # random.seed(101)

    @staticmethod
    def time_to_change_the_regime(mean, minimal):
        """Return time until next regime will change."""
        return (minimal + random.expovariate(1. / (mean - minimal))) * 60

    def l0_run(self):
        self.road_conditions.set_state(RoadConditions.L0_ENV)
        if self.RUN_SCENARIO:
            tau = self.time_table[self.time_table_index][1] - self.time_table[self.time_table_index-1][1]
            choice = self.time_table[self.time_table_index][0]
            self.time_table_index += 1
        else:
            tau = self.time_to_change_the_regime(self.L0_MEAN, 0.5)
            choice = random.choices(['L1'], [1])[0]
        print("L0 mode is available (in min)", str(int(self.env.now / 60)) + ':' + str(int(self.env.now % 60)).zfill(2))
        yield self.env.timeout(tau)
        if choice == 'L0':
            self.env.process(self.l0_run())
        if choice == 'L1':
            self.env.process(self.l1_run())
        elif choice == 'L2':
            self.env.process(self.l2_run())
        # elif choice == 'L3':
        #     self.env.process(self.l3_run())
        elif choice == 'L4':
            self.env.process(self.l4_run())

    def l1_run(self):
        self.road_conditions.set_state(RoadConditions.L1_ENV)
        print("L1 mode is available (in min)", str(int(self.env.now / 60)) + ':' + str(int(self.env.now % 60)).zfill(2))
        if self.RUN_SCENARIO:
            tau = self.time_table[self.time_table_index][1] - self.time_table[self.time_table_index-1][1]
            choice = self.time_table[self.time_table_index][0]
            self.time_table_index += 1
        else:
            tau = self.time_to_change_the_regime(self.L1_MEAN, 0.5)
            choice = random.choices(['L0', 'L2'], self.FROM_L1_TO_L0_OR_L2)[0]
        yield self.env.timeout(tau)
        if choice == 'L0':
            self.env.process(self.l0_run())
            self.machine.on_event(self.env.timeout(0, 'L0_switch'))
        elif choice == 'L1':
            self.env.process(self.l1_run())
        elif choice == 'L2':
            self.env.process(self.l2_run())
        # elif choice == 'L3':
        #     self.env.process(self.l3_run())
        elif choice == 'L4':
            self.env.process(self.l4_run())


    def l2_run(self):
        self.road_conditions.set_state(RoadConditions.L2_ENV)
        print("L2 mode is available (in min)", str(int(self.env.now / 60)) + ':' + str(int(self.env.now % 60)).zfill(2))
        if self.RUN_SCENARIO:
            tau = self.time_table[self.time_table_index][1] - self.time_table[self.time_table_index-1][1]
            choice = self.time_table[self.time_table_index][0]
            self.time_table_index += 1
        else:
            tau = self.time_to_change_the_regime(self.L2_MEAN, 0.5)
            choice = random.choices(['L1', 'L4'], self.FROM_L2_TO_L1_OR_L4)[0]
        yield self.env.timeout(tau)
        if choice == 'L0':
            self.env.process(self.l0_run())
            self.machine.on_event(self.env.timeout(0, 'L0_switch'))
        elif choice == 'L1':
            self.env.process(self.l1_run())
            self.machine.on_event(self.env.timeout(0, 'L1_switch'))
        elif choice == 'L2':
            self.env.process(self.l2_run())
        # elif choice == 'L3':
        #     self.env.process(self.l3_run())
        elif choice == 'L4':
            self.env.process(self.l4_run())

    def l4_run(self):
        self.road_conditions.set_state(RoadConditions.L4_ENV)
        self.task_list.run_machine_triggered_tasks(command='L4')
        print("L4 mode is available (in min)", str(int(self.env.now / 60)) + ':' + str(int(self.env.now % 60)).zfill(2))
        if self.RUN_SCENARIO:
            tau = self.time_table[self.time_table_index][1] - self.time_table[self.time_table_index-1][1]
            choice = self.time_table[self.time_table_index][0]
            self.time_table_index += 1
        else:
            tau = self.time_to_change_the_regime(self.L4_MEAN, 10 / 60)
            choice = 'L2'
        # self.task_list.run_control_task(choice='L4_switch')
        if tau > 60:
            yield self.env.timeout(tau - 60)
            if self.machine.get_state_index() != 3.8:
                print("TOR60 (in min)", str(int(self.env.now / 60)) + ':' + str(int(self.env.now % 60)).zfill(2))
                self.machine.on_event(self.env.timeout(0, 'TOR60'))
                self.road_conditions.tor60.succeed()
                self.task_list.run_machine_triggered_tasks(command='TOR60')
            yield self.env.timeout(30)
            if self.machine.get_state_index() != 3.8:
                self.road_conditions.tor60_30.succeed()
                print("TOR60-30 (in min)", str(int(self.env.now / 60)) + ':' + str(int(self.env.now % 60)).zfill(2))
                self.task_list.run_machine_triggered_tasks(command='TOR60_30')
            yield self.env.timeout(20)
        elif tau > 30:
            self.road_conditions.tor60.succeed()
            self.machine.on_event(self.env.timeout(0, 'TOR60'))
            self.task_list.run_machine_triggered_tasks(command='TOR60')
            # if self.machine.get_state_index() == 3.8:
            yield self.env.timeout(tau - 30)
            print("TOR60-30 (in min)", str(int(self.env.now / 60)) + ':' + str(int(self.env.now % 60)).zfill(2))
            self.road_conditions.tor60_30.succeed()
            self.task_list.run_machine_triggered_tasks(command='TOR60_30')
            yield self.env.timeout(20)
        elif tau > 10:
            self.machine.on_event(self.env.timeout(0, 'TOR60'))
            print("TOR60-30 (in min)", str(int(self.env.now / 60)) + ':' + str(int(self.env.now % 60)).zfill(2))
            # if self.machine.get_state_index() == 3.8:
            self.road_conditions.tor60.succeed()
            self.task_list.run_machine_triggered_tasks(command='TOR60_30')
            yield self.env.timeout(tau - 10)

        self.road_conditions.tor10.succeed()
        self.task_list.run_machine_triggered_tasks(command='TOR10')
        print("TOR10 (in min)", str(int(self.env.now / 60)) + ':' + str(int(self.env.now % 60)).zfill(2))
        self.machine.on_event(self.env.timeout(0, 'TOR10'))
        yield self.env.timeout(10)

        self.road_conditions.tor60 = self.env.event()
        self.road_conditions.tor60_30 = self.env.event()
        self.road_conditions.tor10 = self.env.event()

        if self.machine.state.__repr__() == TOR10().__repr__():
            self.machine.on_event(self.env.timeout(0, choice + '_switch'))

        if choice == 'L0':
            self.env.process(self.l0_run())
            self.machine.on_event(self.env.timeout(0, 'L0_switch'))
        elif choice == 'L1':
            self.env.process(self.l1_run())
            self.machine.on_event(self.env.timeout(0, 'L1_switch'))
        elif choice == 'L2':
            self.env.process(self.l2_run())
            self.machine.on_event(self.env.timeout(0, 'L2_switch'))
        elif choice == 'L4':
            self.env.process(self.l4_run())

