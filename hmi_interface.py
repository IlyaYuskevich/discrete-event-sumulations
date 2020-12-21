import simpy

from machine import Machine
from road_conditions import RoadConditionsState
from task_list import TaskList
from user_memory import UserMemory


class HmiInterface(object):
    def __init__(self, env: simpy.Environment, machine: Machine, road_conditions: RoadConditionsState,
                 user_memory: UserMemory, task_list: TaskList):
        self.env = env
        self.machine = machine
        self.road_conditions = road_conditions
        self.user_memory = user_memory
        self.task_list = task_list
        self.env.process(self.run_change_machine_state())

    def run_change_machine_state(self):
        while True:
            yield simpy.AnyOf(self.env, [x.finished_control for x in self.task_list.control_tasks])
            task = [tsk for tsk in self.task_list.control_tasks if tsk.finished_control.processed][0]
            command = task.finished_control.value
            if self.road_conditions.tor60.processed and int(task.finished_control.value[1]) == 4:
                command = 'TOR60'
            if int(task.finished_control.value[1]) <= self.road_conditions.get_state():
                self.machine.on_event(self.env.timeout(0, value=command))
                self.user_memory.update_machine_state(self.machine.get_state_index())
                # task.update_awareness_param()
                self.task_list.run_machine_triggered_tasks(command=command)
            else:
                print("WARNING: USER TAKE WRONG DECISION ON ",
                      str(int(self.env.now / 60)) + ':' + str(int(self.env.now % 60)).zfill(2))
                previous_state = str(self.machine.state)
                self.machine.on_event(self.env.timeout(0, value='Error'))
                self.task_list.run_machine_triggered_tasks('Error')
                yield self.env.timeout(2)
                if previous_state == 'TOR10' or previous_state == 'TOR60':
                    self.machine.on_event(self.env.timeout(0, value='L0_switch'))
                else:
                    self.machine.on_event(self.env.timeout(0, value=previous_state + '_switch'))
            # print('switch_callback' + callback + ' ' + str(self.env.now))

            task.finished_control = self.env.event()
