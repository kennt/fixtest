""" Message queue - responsible for managing a queue of Messages.

    Copyright (c) 2014-2022 Kenn Takara
    See LICENSE for details

"""

import datetime
import logging
import queue

from fixtest.base import FixtestTimeoutError, FixtestTestInterruptedError


class MessageQueue(queue.Queue):
    """ Provides a thread-safe message queue.
    """

    def __init__(self, name):
        super().__init__()

        self._name = name

        self._is_cancelled = False
        self._logger = logging.getLogger(__name__)

    def add(self, message):
        """ Adds a message onto the queue
        """
        self.put(message, False)

    def cancel(self):
        """ Cancels any operations on this queue.  This will
            cause the wait_for_message() to throw a
            TestInterruptedError exception.
        """
        self._is_cancelled = True

    def wait_for_message(self, title='', timeout=10):
        """ Waits until a message has been added to the queue

            Makes the asynchronous interface into a synchronous
            interface.

            Arguments:
                title: A string to be used when logging or
                    on errors to identify the operation we are
                    performing.
                timeout: The timeout period (in seconds) to wait
                    for.  If a message has not been received in
                    timeout seconds, a FixtestTimeoutError will be
                    raised.

            Returns: a message

            Raises:
                FixtestTimeoutError:
                TestInterruptedError
        """
        start = datetime.datetime.now()
        message = None

        while message is None:
            if (datetime.datetime.now() - start).seconds > timeout:
                raise FixtestTimeoutError(f'message timeout: {title}')
            if self._is_cancelled:
                raise FixtestTestInterruptedError('test cancelled')

            try:
                message = self.get(True, timeout=1.0)
            except queue.Empty:
                # if empty keep on cycling
                pass

        return message
