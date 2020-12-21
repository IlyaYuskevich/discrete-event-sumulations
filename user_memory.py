import simpy

from road_conditions import RoadConditions


class UserMemory(object):
    def __init__(self, env):
        self.env = env
        self.tor60: simpy.Event = env.event()
        self.tor60_30: simpy.Event = env.event()
        self.tor10: simpy.Event = env.event()
        self.available_levels = RoadConditions.L0_ENV
        self.ad_status = False
        self.ad_status_time_till = 0
        self.ad_status_duration = 0
        self.machine_state = 0
        self.ad_activated = False

    def update_conditions(self, road_conditions):
        self.available_levels = road_conditions
        self.update_ad_status(road_conditions)

    def update_ad_status(self, road_conditions):
        self.ad_status = road_conditions == RoadConditions.L4_ENV
        if self.ad_status:
            self.available_levels = 4

    def update_ad_activated(self, machine_state):
        self.ad_activated = machine_state > 3

    def update_ad_status_and_time(self, road_conditions):
        self.ad_status = road_conditions == RoadConditions.L4_ENV
        self.ad_status_time_till = 0
        self.ad_status_duration = 0
        if self.ad_status:
            self.available_levels = 4

    def update_machine_state(self, machine_state):
        self.machine_state = machine_state
        self.update_ad_activated(machine_state)
        if self.tor60.processed and machine_state != 3.8:
            self.tor60 = self.env.event()
        if self.tor10.processed and machine_state != 3.5:
            self.tor10 = self.env.event()

    def update_tor_status(self, machine_state):
        self.available_levels = RoadConditions.L2_ENV
        if machine_state == 3.8:
            try:
                self.tor60.succeed()
            except RuntimeError:
                pass
            self.tor10 = self.env.event()
            self.machine_state = 3.8
            self.ad_activated = True
            self.ad_status = True
        elif machine_state == 3.5:
            try:
                self.tor10.succeed()
            except RuntimeError:
                pass
            self.machine_state = 3.5
            self.ad_activated = True
            self.ad_status = True
        # else:
            # self.tor10 = self.env.event()
            # self.tor60 = self.env.event()
