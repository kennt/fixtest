""" Base client/server controller for testing.

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import logging

from fixtest.base.asserts import *
from fixtest.fix.constants import FIX
from fixtest.fix.messages import new_order_message, execution_report

from simple_base import BaseClientServerController


class SimpleClientServerController(BaseClientServerController):
    """ The base class for FIX-based TestCaseControllers.
    """
    def __init__(self, **kwargs):
        super(SimpleClientServerController, self).__init__(**kwargs)

        self.testcase_id = 'Simple NewOrder test'
        self.description = 'Test of the command-line tool'

        self._logger = logging.getLogger(__name__)

    def run(self):
        """ Run the test.  Here we send a new_order and
            then a modify.
        """
        # client -> server
        self.client.send_message(new_order_message(self.client))

        # server <- client
        message = self.server.wait_for_message('waiting for new order')
        self.assert_is_not_none(message)

        # server -> client
        self.server.send_message(execution_report(self.server, message))

        # client <- server
        message = self.client.wait_for_message('waiting for new order ack')
        self.assert_is_not_none(message)
