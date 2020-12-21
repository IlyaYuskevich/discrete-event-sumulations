from machine_states import L0


class Machine(object):
    """
    A simple state machine that mimics the functionality of a device from a
    high level.
    """

    def __init__(self):
        """ Initialize the components. """

        # Start with a default state.
        self.state = L0()

    def on_event(self, event):
        """
        This is the bread and butter of the state machine. Incoming events are
        delegated to the given states which then handle the event. The result is
        then assigned as the new state.
        """

        # The next state will be the result of the on_event function.
        self.state = self.state.on_event(event)

    def get_state_index(self):
        if self.state.__repr__() == 'L0':
            return 0
        elif self.state.__repr__() == 'L1':
            return 1
        elif self.state.__repr__() == 'L2':
            return 2
        elif self.state.__repr__() == 'L4':
            return 4
        elif self.state.__repr__() == 'TOR60':
            return 3.8
        elif self.state.__repr__() == 'TOR10':
            return 3.5
        elif self.state.__repr__() == 'ERROR':
            return -1
