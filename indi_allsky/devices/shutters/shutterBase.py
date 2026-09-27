class ShutterBase(object):
    OPEN = 'open'
    CLOSED = 'closed'

    def __init__(self, *args, **kwargs):
        self.config = args[0]
        self._state = None

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state):
        raise NotImplementedError

    def deinit(self):
        pass
