""" Root module for the basic modules of the fixtest tool.

    Copyright (c) 2014-2022 Kenn Takara
    See LICENSE for details

"""


class FixtestTimeoutError(Exception):
    """ Exception: MessageQueue wait_for_message timeout. """
    def __init__(self, text):
        super().__init__()
        self.text = text

    def __str__(self):
        return self.text


class FixtestTestInterruptedError(Exception):
    """ Exception: The user has manually cancelled the test. """
    def __init__(self, text):
        super().__init__()
        self.text = text

    def __str__(self):
        return self.text


class FixtestConnectionError(Exception):
    """ Exception: A problem with a server or client connection. """
    def __init__(self, text):
        super().__init__()
        self.text = text

    def __str__(self):
        return self.text
