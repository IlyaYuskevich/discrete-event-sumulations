from state import State


# Start of our states


class L0(State):
    """
    Zero automation level (MD)
    """

    def on_event(self, event):
        if event.value == 'L1_switch' or event.value == 'L1_user_switch':
            return L1()
        elif event.value == 'L2_switch' or event.value == 'L2_user_switch':
            return L2()
        elif event.value == 'L4_switch' or event.value == 'L4_user_switch':
            return L4()
        elif event.value == 'TOR60_switch':
            return TOR60()
        elif event.value == 'TOR10_switch':
            return TOR10()
        elif event.value == 'Error':
            return ERROR()

        return self

    @property
    def value(self):
        return 0


class L1(State):
    """
    First automation level (MD)
    """

    def on_event(self, event):
        if event.value == 'L0_switch' or event.value == 'L0_user_switch':
            return L0()
        elif event.value == 'L2_switch' or event.value == 'L2_user_switch':
            return L2()
        elif event.value == 'L4_switch' or event.value == 'L4_user_switch':
            return L4()
        elif event.value == 'TOR60_switch':
            return TOR60()
        elif event.value == 'Error':
            return ERROR()

        return self

    @property
    def value(self):
        return 1


class L2(State):
    """
    Second automation level (MD)
    """

    def on_event(self, event):
        if event.value == 'L0_switch' or event.value == 'L0_user_switch':
            return L0()
        elif event.value == 'L1_switch' or event.value == 'L1_user_switch':
            return L1()
        elif event.value == 'L4_switch' or event.value == 'L4_user_switch':
            return L4()
        elif event.value == 'TOR60' or event.value == 'TOR60_user_switch':
            return TOR60()
        elif event.value == 'Error':
            return ERROR()

        return self

    @property
    def value(self):
        return 2


class L4(State):
    """
    Fourth automation level (AD)
    """

    def on_event(self, event):
        if event.value == 'L0_switch' or event.value == 'L0_user_switch':
            return L0()
        elif event.value == 'L1_switch' or event.value == 'L1_user_switch':
            return L1()
        elif event.value == 'L2_switch' or event.value == 'L2_user_switch':
            return L2()
        elif event.value == 'TOR60':
            return TOR60()
        elif event.value == 'TOR10':
            return TOR10()
        elif event.value == 'Error':
            return ERROR()

        return self

    @property
    def value(self):
        return 4


class TOR60(State):
    """
    TOR60
    """

    def on_event(self, event):
        if event.value == 'L0_switch' or event.value == 'L0_user_switch':
            return L0()
        elif event.value == 'L1_switch' or event.value == 'L1_user_switch':
            return L1()
        elif event.value == 'L2_switch' or event.value == 'L2_user_switch':
            return L2()
        elif event.value == 'TOR10':
            return TOR10()
        elif event.value == 'Error':
            return ERROR()

        return self

    @property
    def value(self):
        return 3.8


class TOR10(State):
    """
    TOR10
    """

    def on_event(self, event):
        if event.value == 'L0_switch' or event.value == 'L0_user_switch':
            return L0()
        elif event.value == 'L1_switch' or event.value == 'L1_user_switch':
            return L1()
        elif event.value == 'L2_switch' or event.value == 'L2_user_switch':
            return L2()
        elif event.value == 'Error':
            return ERROR()

        return self

    @property
    def value(self):
        return 3.5


class ERROR(State):
    """
    TOR10
    """

    def on_event(self, event):
        if event.value == 'L0_switch':
            return L0()
        elif event.value == 'L1_switch':
            return L1()
        elif event.value == 'L2_switch':
            return L2()
        elif event.value == 'TOR60':
            return TOR60()
        elif event.value == 'TOR10':
            return TOR10()

        return self

    @property
    def value(self):
        return -1
