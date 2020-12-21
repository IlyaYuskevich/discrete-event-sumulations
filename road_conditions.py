import simpy


class RoadConditions:
    L0_ENV, L1_ENV, L2_ENV, L4_ENV = [0, 1, 2, 4]


class RoadConditionsState:
    def __init__(self, env: simpy.Environment):
        self.state = RoadConditions.L0_ENV
        self.tor60: simpy.Event = env.event()
        self.tor60_30: simpy.Event = env.event()
        self.tor10: simpy.Event = env.event()

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state
