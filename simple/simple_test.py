""" Base client/server controller for testing.

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import logging

from fixtest.base.asserts import *
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
        self.client.send_message(new_order_message(self.client,
            symbol='abc',
            side='0',
            order_type='1',
            extra_tags=[(38, 100),      # orderQty
                        (44, 10),       # price
                       ]))

        # server <- client
        message = self.server.wait_for_message('waiting for new order')
        assert_is_not_none(message)

        # server -> client
        self.server.send_message(execution_report(self.server,
            message,
            exec_trans_type='0',
            exec_type='0',
            ord_status='0',
            symbol='abc',
            side='0',
            leaves_qty='100',
            cum_qty='0',
            avg_px='0'))

        # client <- server
        message = self.client.wait_for_message('waiting for new order ack')
        assert_is_not_none(message)
