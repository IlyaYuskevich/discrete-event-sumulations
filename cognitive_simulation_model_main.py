import tkinter as tk
from tkinter import filedialog
from typing import List

import simpy
import matplotlib

from hmi_interface import HmiInterface

matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
from matplotlib.widgets import MultiCursor, SpanSelector

from machine import Machine
from road_conditions import RoadConditions, RoadConditionsState
from road_conditions_generator import RoadConditionsGenerator
from user import User
from user_memory import UserMemory
from task_list import TaskList
import numpy as np
import xlrd
import os


def yes_or_no(question):
    while "the answer is invalid":
        reply = str(input(question + ' (Y/n): ')).lower().strip()
        if reply[:1] == 'y' or reply[:1] == '':
            return True
        if reply[:1] == 'n':
            return False


def file_dialog(default_path):
    root = tk.Tk()
    root.withdraw()

    loc = (filedialog.askopenfilename(initialdir=default_path))
    try:
        xlrd.open_workbook(loc)
    except FileNotFoundError:
        print('Error. Input .xlsx file not found. Reload application and try again.')
        loc = ''
    finally:
        return loc


default_path = os.path.dirname(__file__)
print("HMI cognitive workload simulation model v.0.0.1")
if yes_or_no('Use default ./data folder for .xlsx input?'):
    try:
        loc = (os.path.abspath(os.path.join(default_path, '..', 'data\\funcReq.xlsx')))
        wb = xlrd.open_workbook(loc)
    except FileNotFoundError:
        try:
            loc = (os.path.abspath(os.path.join(default_path, 'data\\funcReq.xlsx')))
            wb = xlrd.open_workbook(loc)
        except FileNotFoundError:
            print('Default data directory is empty. Specify path of .xlsx file.')
            loc = file_dialog(default_path)
            wb = xlrd.open_workbook(loc)
else:
    loc = file_dialog(default_path)
    wb = xlrd.open_workbook(loc)

sheet = wb.sheet_by_name('Tasks')
sheet.cell_value(0, 0)
for i in range(sheet.nrows):
    print(sheet.row_values(i))

scenario = []
sheet_sc = wb.sheet_by_name('Scenario')
sheet_sc.cell_value(0, 0)
for i in range(sheet_sc.nrows):
    scenario.append(sheet_sc.row_values(i))

env = simpy.Environment()

# RANDOM_SEED = 42
params = wb.sheet_by_name('SimulationParameters').get_rows()
params = {x[0].value: x[1].value for x in params}

SIM_TIME = params.get('SIM_TIME')  # simulation time in minutes
DISCRIMINATION_INTERVAL = params.get('DISCRIMINATION_INTERVAL')  # discrimination interval (delta T) in seconds
PERSON = params.get('PERSON')
MAX_PERCEPT_WORKLOAD = params.get('MAX_PERCEPT_WORKLOAD')
MAX_COGNITIVE_WORKLOAD = params.get('MAX_COGNITIVE_WORKLOAD')


class Visualization:
    def __init__(self, env, tasks, road_conditions: RoadConditionsState, machine: Machine, user_memory: UserMemory):
        self.env = env
        self.machine = machine
        self.user_memory = user_memory
        self.tasks = tasks
        self.road_conditions = road_conditions
        # Start the run process everytime an instance is created.
        self.t_data = []
        self.regime_data = []
        self.road_conditions_data = []
        self.perception_wl_data = []
        self.cognitive_wl_data = []
        self.eye_off_the_road = []
        self.active_tasks = []
        self.sa_parameters_correct = []
        self.sa_parameters_wrong = []
        self.situation_awareness = []
        self.fig, (self.ax2, self.ax3, self.ax1) = plt.subplots(nrows=3, gridspec_kw={'height_ratios': [3, 3, 1]})
        self.ax1.set_ylim(-0.1, 5)
        self.ax2.set_ylim(-0.1, 5)
        self.ax3.set_ylim(-0.1, 10)
        self.ax1.set_xlim(0, SIM_TIME)
        self.ax2.set_xlim(0, SIM_TIME)
        self.ax3.set_xlim(0, SIM_TIME)
        self.fig.canvas.mpl_connect('motion_notify_event', self.onmove)
        self.summary = ''

        self.sscale = SpanSelector(self.ax1, self.onselect, 'horizontal', useblit=False, span_stays=True,
                                   rectprops=dict(alpha=0.2, facecolor='red'))
        # cursor1 = MultiCursor(self.fig.canvas, (self.ax1, self.ax2), color='r', lw=1,
        #             horizOn=False, vertOn=True)
        self.ax1.grid()
        self.ax2.grid()
        self.ax3.grid()
        # self.ax1.set_ylim(-0.1, 1.1)
        self.ln11, = self.ax1.plot(self.t_data, self.regime_data, 'r-', lw=2)
        self.ln12, = self.ax2.plot(self.t_data, self.regime_data, '.r-', lw=2, label='Machine State', alpha=0.8)
        self.ln2, = self.ax3.plot(self.t_data, self.perception_wl_data, 'b-', lw=5, label='Perceptual workload',
                                  alpha=0.5)
        self.ln3, = self.ax3.plot(self.t_data, self.cognitive_wl_data, 'k-', lw=2, label='Cognitive workload',
                                  alpha=0.8)
        self.ln41, = self.ax1.plot(self.t_data, self.road_conditions_data, 'g-', lw=2)
        self.ln42, = self.ax2.plot(self.t_data, self.road_conditions_data, 'g-', lw=4, label='Road conditions',
                                   alpha=0.5)
        self.eotr_line, = self.ax3.plot(self.t_data, self.eye_off_the_road, 'gray', lw=4, label='Eye-off-the-road',
                                        alpha=0.2)
        self.ax3.fill_between(self.t_data, 0, self.eye_off_the_road, facecolor='gray')
        self.ann1 = self.ax3.annotate('', (0, 0))
        self.ann2 = self.ax2.text(0, 4, '')
        self.ann3 = self.ax2.text(0, 3, '')
        self.ax2.legend()
        self.ax3.legend()
        # env.process(self.regime_controller())
        env.process(self.update_values(tasks))
        # [env.process(task.task_execution()) for task in self.tasks]

    def update_values(self, task_list: TaskList):
        while True:
            yield self.env.timeout(DISCRIMINATION_INTERVAL)
            self.t_data.append(env.now / 60)
            self.regime_data.append(self.machine.get_state_index())
            self.perception_wl_data.append(task_list.perceptional_workload.level)
            self.cognitive_wl_data.append(task_list.cognitive_workload.level)
            self.eye_off_the_road.append(any([task.visual != '' for task in task_list.tasks if task.status]))
            self.road_conditions_data.append(self.road_conditions.get_state())
            names = [str(int(self.env.now / 60)) + ':' + str(int(self.env.now % 60)).zfill(2)]
            [names.append(task.name) for task in task_list.tasks if task.status]
            self.active_tasks.append("\n".join(names))

            awareness_correct = ['Correct:']
            awareness_wrong = ['Wrong:']
            aw = [0, 0]
            if self.machine.get_state_index() == self.user_memory.machine_state:
                awareness_correct.append('Machine state: ' + str(self.user_memory.machine_state))
                aw[0] = aw[0] + 1
            else:
                awareness_wrong.append('Machine state: ' + str(self.user_memory.machine_state))
                aw[1] = aw[1] + 1

            if (self.machine.get_state_index() <= 3 and not self.user_memory.ad_activated) or (
                    self.machine.get_state_index() > 3 and self.user_memory.ad_activated):
                awareness_correct.append('AD activated: ' + str(self.user_memory.ad_activated))
                aw[0] = aw[0] + 1
            else:
                awareness_wrong.append('AD activated: ' + str(self.user_memory.ad_activated))
                aw[1] = aw[1] + 1

            if self.road_conditions.get_state() == self.user_memory.available_levels:
                awareness_correct.append('Road conditions: ' + str(self.user_memory.available_levels))
                aw[0] = aw[0] + 1
            else:
                awareness_wrong.append('Road conditions: ' + str(self.user_memory.available_levels))
                aw[1] = aw[1] + 1

            if (self.road_conditions.get_state() == RoadConditions.L4_ENV and self.user_memory.ad_status) or (
                    self.road_conditions.get_state() != RoadConditions.L4_ENV and not self.user_memory.ad_status):
                awareness_correct.append('AD status: ' + str(self.user_memory.ad_status))
                aw[0] = aw[0] + 1
            else:
                awareness_wrong.append('AD status: ' + str(self.user_memory.ad_status))
                aw[1] = aw[1] + 1

            if (
                    self.machine.get_state_index() == 3.8 or self.machine.get_state_index() == 3.5) and self.user_memory.tor60.processed:
                awareness_correct.append('TOR60')
                aw[0] = aw[0] + 1

            if self.machine.get_state_index() == 3.5 and self.user_memory.tor10.processed:
                awareness_correct.append('TOR10')
                aw[0] = aw[0] + 1

            if (
                    self.machine.get_state_index() == 3.8 or self.machine.get_state_index() == 3.5) and not self.user_memory.tor60.processed:
                awareness_wrong.append('TOR60')
                aw[1] = aw[1] + 1

            if self.machine.get_state_index() == 3.5 and not self.user_memory.tor10.processed:
                awareness_wrong.append('TOR10')
                aw[1] = aw[1] + 1

            self.sa_parameters_correct.append("\n".join(awareness_correct))
            self.sa_parameters_wrong.append("\n".join(awareness_wrong))
            self.situation_awareness.append(aw[0] / (aw[0] + aw[1]))

    def update_fig(self, i):
        self.ln11.set_data(self.t_data[0:i], self.regime_data[0:i])
        self.ln12.set_data(self.t_data[0:i], self.regime_data[0:i])
        self.ln2.set_data(self.t_data[0:i], self.perception_wl_data[0:i])
        self.ln3.set_data(self.t_data[0:i], self.cognitive_wl_data[0:i])
        self.ln41.set_data(self.t_data[0:i], self.road_conditions_data[0:i])
        self.ln42.set_data(self.t_data[0:i], self.road_conditions_data[0:i])
        self.eotr_line.set_data(self.t_data[0:i], self.eye_off_the_road[0:i])
        return self.ln11, self.ln12, self.ln2, self.ln3, self.ln41, self.ln42, self.eotr_line

    def onselect(self, xmin, xmax):
        indmin, indmax = np.searchsorted(self.t_data, (xmin, xmax))
        indmax = min(len(self.t_data) - 1, indmax)

        thisx = self.t_data[indmin:indmax]
        this_perc = self.perception_wl_data[indmin:indmax]
        this_cogn = self.cognitive_wl_data[indmin:indmax]
        self.ln12.set_data(thisx, self.regime_data[indmin:indmax])
        self.ln2.set_data(thisx, this_perc)
        self.ln3.set_data(thisx, this_cogn)
        self.ln42.set_data(thisx, self.road_conditions_data[indmin:indmax])
        self.eotr_line.set_data(thisx, self.eye_off_the_road[indmin:indmax])
        ymax = max(max(this_cogn, this_perc))
        self.ax2.set_xlim(thisx[0], thisx[-1])
        self.ax3.set_xlim(thisx[0], thisx[-1])
        self.ax3.set_ylim(0, ymax + 1)
        self.ax3.fill_between(thisx, 0, [(ymax + 1) * x for x in self.eye_off_the_road[indmin:indmax]],
                              facecolor='gray', alpha=0.3)
        # self.ax2.text(thisx[0], 5, self.summary, style='italic',
        #               bbox={'facecolor': 'lavender', 'alpha': 1, 'pad': 10})
        self.fig.canvas.draw()

    def onmove(self, event):
        if event.xdata is not None:
            try:
                self.ann1.remove()
            except ValueError:
                pass
            try:
                self.ann2.remove()
            except ValueError:
                pass
            try:
                self.ann3.remove()
            except ValueError:
                pass
            index = np.searchsorted(self.t_data, event.xdata)
            self.ann1 = self.ax3.annotate(self.active_tasks[index], (event.xdata, 0),
                                          bbox=dict(boxstyle="round,pad=0.3", fc="lightgray", ec=None, alpha=0.9,
                                                    lw=0.1))
            self.ann2 = self.ax2.text(event.xdata, 4., self.sa_parameters_correct[index],
                                      bbox=dict(boxstyle="round,pad=0.3", fc="honeydew", ec=None, alpha=0.7,
                                                lw=0.1), verticalalignment='top')
            self.ann3 = self.ax2.text(event.xdata, 2., self.sa_parameters_wrong[index],
                                      bbox=dict(boxstyle="round,pad=0.3", fc="mistyrose", ec=None, alpha=0.7,
                                                lw=0.1), verticalalignment='top')
            self.fig.canvas.draw()

    @staticmethod
    def find_changes(time_serie: List):
        return np.array([True] + [time_serie[i] != time_serie[i + 1] or time_serie[i - 1] != time_serie[i] for i in
                                  np.arange(1, len(time_serie) - 1)] + [True])

    def reduce_timeserie(self):
        mask1 = self.find_changes(self.regime_data)
        # mask2 = self.find_changes([x[x.find('\n'):] for x in self.active_tasks])
        mask2 = self.find_changes(self.situation_awareness)
        mask3 = self.find_changes(self.road_conditions_data)
        mask4 = self.find_changes(self.cognitive_wl_data)
        mask5 = self.find_changes(self.perception_wl_data)

        mask = mask1 | mask2 | mask3 | mask4 | mask5

        self.perception_wl_data = list(np.array(self.perception_wl_data)[mask])
        self.t_data = list(np.array(self.t_data)[mask])
        self.regime_data = list(np.array(self.regime_data)[mask])
        self.cognitive_wl_data = list(np.array(self.cognitive_wl_data)[mask])
        self.road_conditions_data = list(np.array(self.road_conditions_data)[mask])
        self.eye_off_the_road = list(np.array(self.eye_off_the_road)[mask])
        self.active_tasks = list(np.array(self.active_tasks)[mask])
        self.sa_parameters_wrong = list(np.array(self.sa_parameters_wrong)[mask])
        self.sa_parameters_correct = list(np.array(self.sa_parameters_correct)[mask])
        self.situation_awareness = list(np.array(self.situation_awareness)[mask])

    def calculate_summary(self):
        overload_cogn = sum([x > 8 for x in self.cognitive_wl_data]) / len(self.cognitive_wl_data) * 100
        overload_perc = sum([x > 8 for x in self.perception_wl_data]) / len(self.perception_wl_data) * 100
        average_cogn = sum(self.cognitive_wl_data) / MAX_COGNITIVE_WORKLOAD / len(self.cognitive_wl_data) * 100
        average_perc = sum(self.perception_wl_data) / MAX_PERCEPT_WORKLOAD / len(self.perception_wl_data) * 100

        self.summary = 'Eye-of-the-road time: {:2.2f}%'.format(
            sum(self.eye_off_the_road) / len(self.eye_off_the_road) * 100) + '\n' + \
                       'Overloaded (cognitive): {:2.2f}%'.format(
                           overload_cogn) + '\n' + \
                       'Overloaded (perceptual) {:2.2f}%'.format(overload_perc) + '\n' + \
                       'Average situation awareness: {:2.2f}%'.format(
                           sum(self.situation_awareness) / len(self.situation_awareness) * 100)


# env = simpy.rt.RealtimeEnvironment(initial_time=0, factor=1 / 60 * 0.010, strict=False)
env = simpy.Environment()

# [env.process(task.task_execution()) for task in task_list]
user_memory = UserMemory(env)
machine = Machine()
road_conditions = RoadConditionsState(env)

task_list = TaskList(env, sheet, machine, road_conditions, user_memory, persona=PERSON,
                     max_mental=params.get('MAX_COGNITIVE_WORKLOAD'), max_perc=params.get('MAX_PERCEPT_WORKLOAD'))
user = User(env, user_memory, machine, road_conditions, task_list, params)
road_conditions_generator = RoadConditionsGenerator(env, machine, user_memory, road_conditions, task_list, params, scenario)

hmi_interface = HmiInterface(env, machine, road_conditions, user_memory, task_list)

visualization = Visualization(env, task_list, road_conditions, machine, user_memory)
# machine.on_event(env.timeout(0, value='TOR60_switch'))
env.run(until=SIM_TIME * 60)

visualization.calculate_summary()
visualization.reduce_timeserie()
# anim = FuncAnimation(visualization.fig, visualization.update_fig,
#                      interval=DISCRIMINATION_INTERVAL*1e3/TIME_MULT)  ## interval - delay in ms
visualization.update_fig(len(visualization.t_data) - 1)
cursor1 = MultiCursor(visualization.fig.canvas, (visualization.ax2, visualization.ax3), color='r', lw=1,
                      horizOn=False, vertOn=True)
visualization.onselect(0, len(visualization.t_data))

# Histogram of tasks
fig = plt.figure(10)
ind = np.arange(len(task_list.tasks)-2)
interrupted = [(x.name, task_list.interrupted_tasks.count(x.name)) for x in task_list.tasks
               if (x.name != 'SYS_REQ_FUNC_19_04_25' and x.name != 'SYS_REQ_FUNC_19_04_26')]
processed = [(x.name, task_list.finished_tasks.count(x.name)) for x in task_list.tasks
             if (x.name != 'SYS_REQ_FUNC_19_04_25' and x.name != 'SYS_REQ_FUNC_19_04_26')]
p2 = plt.bar(ind, [x[1] for x in interrupted], color='red')
p1 = plt.bar(ind, [x[1] for x in processed], color='blue')
ax = plt.gca()
ax.text(0.75, 0.8, visualization.summary, style='italic',
              bbox={'facecolor': 'lavender', 'alpha': 1, 'pad': 10}, transform=ax.transAxes)
plt.xticks(ind, [x[0] for x in processed])
fig.autofmt_xdate(bottom=0.16, rotation=45, ha='right')
plt.legend((p1[0], p2[0]), ('Accomplished', 'Missed'))
plt.grid()
plt.show()
