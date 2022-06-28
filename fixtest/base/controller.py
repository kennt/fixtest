""" The base class for all test case controllers.

    Copyright (c) 2014-2022 Kenn Takara
    See LICENSE for details

"""

import logging
import time

from twisted.internet import reactor
from twisted.internet.endpoints import connectProtocol, clientFromString

from fixtest.base import FixtestTestInterruptedError, FixtestTimeoutError
from fixtest.base.utils import log_text


class TestCaseController:
    """ This is the base class that is used to run an individual
        test case.

        Attributes:
            testcase_id:
            description:
            exit_value: The value returned when exiting from the
                command line.
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
        self.exit_value = 1

        self._is_cancelled = False

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

    def _execute_test(self):
        """ Runs the test.  This is the entrypoint from the
            TestCaseController.
        """
        # pylint: disable=broad-except
        try:
            if not self.pre_test():
                self.test_status = 'test: failed pre-test conditions'
                return
            self.test_status = 'test: in-progress'

            self.setup()
            self.run()
            self.teardown()

            self.test_status = 'ok'
            self.exit_value = 0
        except AssertionError as err:
            self.test_status = 'fail: assert failed : ' + str(err)
        except FixtestTestInterruptedError:
            self.test_status = 'fail: test cancelled'
        except FixtestTimeoutError as err:
            self.test_status = 'fail: timeout : ' + str(err)
        except Exception:
            self.test_status = 'fail: exception'
            self._logger.exception('fail: exception')
        finally:
            if reactor.running:
                reactor.callFromThread(reactor.stop)

    def pre_test(self):
        """ Override for any pre test checks.

            Returns: Return True if everything is ok.  Return
                False to stop the test.
        """
        return True

    def setup(self):
        """ Override this to implement any setup
        """

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

    def cancel_test(self):
        """ Cancels the test.  Cancels any operations.

            Override this to take care of any cleanup/cancelling
            that needs to be done.
        """
        self._is_cancelled = True
        for node in self.clients().values():
            node['node'].cancel()
        for node in self.servers().values():
            node['factory'].cancel()

    def _start_client(self, client):
        """ This is a helper function that needs to get called
            on the reactor thread.

            Arguments:
                client: The client dict().
        """
        # pylint: disable=consider-using-f-string
        log_text(self._logger.info, None,
                 'client:{0} attempting {1}:{2}'.format(
                     client['name'],
                     client['host'],
                     client['port']))

        str_send = f"tcp:{client['host']}:{client['port']}:timeout=10"
        endpoint = clientFromString(reactor, str_send)

        node = client['node']
        deferred = connectProtocol(endpoint, node)
        deferred.addCallbacks(node.client_success,
                              callbackArgs=(client,),
                              errback=node.client_failure,
                              errbackArgs=(client,))

    def wait_for_client_connections(self, timeout):
        """ Initiate and wait for all client connections to connect.

            Arguments:
                timeout:

            Raises:
                FixtestTimeoutError
                FixtestTestInterruptedError
        """
        for client in self.clients().values():
            reactor.callFromThread(self._start_client, client)

        # Now have to wait until all clients are connected
        per_sec = 5
        success = True
        for _ in range(timeout * per_sec):
            if self._is_cancelled:
                raise FixtestTestInterruptedError('test cancelled')

            success = True
            for client in self.clients().values():
                if client.get('error', None) is not None:
                    raise client['error']
                if client.get('connected', '') == '':
                    success = False
                    break
            if success:
                break
            time.sleep(1.0/per_sec)
        if not success:
            raise FixtestTimeoutError('waiting for clients to connect')

    def wait_for_server_connections(self, timeout):
        """ Wait for all server connections to connect.

            Raises:
                FixtestTestInterruptedError
                FixtestTimeoutError
        """
        per_sec = 5
        for _ in range(timeout * per_sec):
            if self._is_cancelled:
                raise FixtestTestInterruptedError('test cancelled')

            success = True
            for server in self.servers().values():
                if server.get('error', None) is not None:
                    raise server['error']
                if len(server['factory'].servers) == 0:
                    success = False
                    break
            if success:
                break
            time.sleep(1.0/per_sec)

        if not success:
            raise FixtestTimeoutError("waitng for servers to connect")
