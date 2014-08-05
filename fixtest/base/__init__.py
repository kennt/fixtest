""" Root module for the basic modules of the fixtest tool.

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""


class TimeoutError(Exception):
    """ Exception: MessageQueue wait_for_message timeout. """
    def __init__(self, text):
        super(TimeoutError, self).__init__()
        self.text = text

    def __str__(self):
        return self.text


class TestInterruptedError(Exception):
    """ Exception: The user has manually cancelled the test. """
    def __init__(self, text):
        super(TestInterruptedError, self).__init__()
        self.text = text

    def __str__(self):
        return self.text


class ConnectionError(Exception):
    """ Exception: A problem with a server or client connection. """
    def __init__(self, text):
        super(ConnectionError, self).__init__()
        self.text = text

    def __str__(self):
        return self.text
