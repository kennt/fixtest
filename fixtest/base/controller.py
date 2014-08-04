""" The base class for all test case controllers.

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import logging

from twisted.internet import reactor

from fixtest.base.utils import log_text


class TestCaseController(object):
    """ This is the base class that is used to run an individual
        test case.

        Attributes:
            testcase_id:
            description:
    """
    def __init__(self, **kwargs):
        """ TestCaseController initialization

            Args:
                config:
        """
        # pylint: disable=unused-argument

        self.testcase_id = 'Enter your testcase id'
        self.description = 'Enter your testcase description'
        self.test_status = 'test: not-started'

        self._logger = logging.getLogger(__name__)

    def servers(self):
        """ Returns the dict of servers that need to be started
            indexed by server name.

            This is the responsiblity of the subclass.
        """
        raise NotImplementedError()

    def clients(self):
        """ Returns the dict of clients that need to be started
            indexed by client name.

            This is the responsibility of the subclass.
        """
        raise NotImplementedError()

    def _start_test(self):
        """ Runs the test.  This is the entrypoint from the
            TestCaseController.
        """
        try:
            if not self.pre_test():
                self.test_status = 'test: failed pre-test conditions'
                return
            self.test_status = 'test: in-progress'

            self.setup()
            self.run()
            self.teardown()

            self.test_status = 'ok'
        except Exception:
            self.test_status = 'fail: exception'
        finally:
            if reactor.running:
                reactor.callFromThread(reactor.stop)

    def pre_test(self):
        """ Override for any pre test checks.

            Returns: Return True if everything is ok.  Return
                False to stop the test.
        """
        # pylint: disable=no-self-use
        return True

    def setup(self):
        """ Override this to implement any setup
        """
        # pylint: disable=no-self-use

    def run(self):
        """ Override this to implement the actual test.

            This is the responsibility of the subclass.
        """
        raise NotImplementedError()

    def teardown(self):
        """ Override this to implement any cleanup

            Note that this only runs in the normal case.  In the
            case of an exception, the connections will be torn
            down by shutting the reactor down.
        """
        # pylint: disable=no-self-use

    # Callbacks from Twisted upon server startup
    def server_connect(self, result, *args):
        """ This is called when a server starts listening """
        server = args[0]
        server['listener'] = result

        log_text(self._logger.info, __name__,
                 'server:{0} listening on port {1}'.format(server['name'],
                                                           server['port']))

    def server_failure(self, error, *args):
        """ This is called when a client fails to connect """
        log_text(self._logger.error, __name__,
                 'server:{0} failed to start: {1}'.format(args[0]['name'],
                                                          error))
        reactor.callFromThread(reactor.stop)
