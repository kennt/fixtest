# FIXTest - FIX Protocol Test tool
The purpose of this tool is to provide a way to test networking components
using the FIX level at the system level, not unit test.  Initially, I
wanted a way to reproduce and document specific test cases so that I
could perform regression tests at a later date.

This tool provides a way of creating test cases that can act as FIX clients
or as FIX servers.  But this is not a simulator, the test case author is
responsible for generating the actual messages and checking their correctness.

## What this is not
* This is not a simulator. This tool was made to help document specific
test cases (thus ensuring that I could repro and verify a test case).
* This is not meant for unit testing, but component level testing.
* This currently only supports FIX-based protocols.  In theory this 
could support other protocols, but I haven't tried to make it more protocol agnostic.

## What is supported
* Groups
* Binary fields
* TestRequest/Heartbeat processing

## How to use
1. Write a configuration file
2. Write a testcase
3. Run the testcase

### Configuration
The configuration is gathered from a config file.  The default name for the
file is my_config.py.  A full description of the contents of the file may be
found in sample_config.py

Here is a sample configuration file.
```python

ROLES = {
    'client': {},
    'test-server': {},
}

FIX_4_2 = {
    # The values here are examples only.  They should be customized
    # for your particular needs/implementation.
    'protocol_version': 'FIX.4.2',
    'header_fields': [8, 9],
    'binary_fields': [],
    'required_fields': [8, 9, 10, 35],
    'group_fields': {},
    'max_length': 2048,
}

CONNECTIONS = [
    {
        # connection information
        'name': 'client-FIX-test-server',
        'protocol': 'FIX',
        'host': 'localhost',
        'port': 9000,

        'client': 'FixClient',
        'test-server': 'FixServer',
        'acts-as-server': 'test-server',

        # protocol information
        'protocol_version': FIX_4_2['protocol_version'],
        'binary_fields': FIX_4_2['binary_fields'],
        'header_fields': FIX_4_2['header_fields'],
        'required_fields': FIX_4_2['required_fields'],
        'group_fields': FIX_4_2['group_fields'],
    },
]

```


### Sample test code

Here is an example of a test.  This test sends a logon message and
then a logout message.  In this case, the test tool is running as a
server and a client (thus all messages are logged twice, once on the
sending side and once on the receiving side).

In a more typical test case, this code would be hidden inside of a base
class.  Logon/logout are usually performed within the setup/teardown rather
than part of the test proper.

```python

import logging

from fixtest.base.asserts import assert_is_not_none, assert_tag
from fixtest.base.controller import TestCaseController
from fixtest.fix.constants import FIX
from fixtest.fix.messages import logon_message, logout_message
from fixtest.fix.transport import FIXTransportFactory


class LogonController(TestCaseController):
    """ The base class for FIX-based TestCaseControllers.

        This creates a client and a server that will
        communicate with each other.  So they will use
        the same link config.
    """
    # pylint: disable=too-many-instance-attributes

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.testcase_id = 'Simple-1'
        self.description = 'Test of the command-line tool'

        config = kwargs['config']

        self.server_config = config.get_role('test-server')
        self.server_config.update({'name': 'server-9940'})

        self.server_link_config = config.get_link('client', 'test-server')
        self.server_link_config.update({
            'sender_compid': self.server_link_config['test-server'],
            'target_compid': self.server_link_config['client'],
            })

        self.client_config = config.get_role('client')
        self.client_config.update({'name': 'client-9940'})

        self.client_link_config = config.get_link('client', 'test-server')
        self.client_link_config.update({
            'sender_compid': self.client_link_config['client'],
            'target_compid': self.client_link_config['test-server'],
            })

        self._servers = {}
        self._clients = {}

        factory = FIXTransportFactory('server-9940',
                                      self.server_config,
                                      self.server_link_config)
        factory.filter_heartbeat = False

        server = {
            'name': 'server-9940',
            'port': self.server_link_config['port'],
            'factory': factory,
        }
        self._servers[server['name']] = server

        # In the client case we do not need to provide a
        # factory, Just need a transport.
        client = {
            'name': 'client-9940',
            'host': self.client_link_config['host'],
            'port': self.client_link_config['port'],
            'node': factory.create_transport('client-9940',
                                             self.client_config,
                                             self.client_link_config),
        }
        self._clients[client['name']] = client

        self._logger = logging.getLogger(__name__)

    def clients(self):
        """ The clients that need to be started """
        return self._clients

    def servers(self):
        """ The servers that need to be started """
        return self._servers

    def setup(self):
        """ For this case, wait until our servers are all
            connected before continuing with the test.
        """
        # at this point the servers should be waiting
        # so startup the clients
        self.wait_for_client_connections(10)
        self.wait_for_server_connections(10)

    def teardown(self):
        pass

    def run(self):
        """ This test is a demonstration of logon and
            heartbeat/TestRequest processing.  Usually
            the logon process should be done from setup().
        """
        client = self._clients['client-9940']['node']
        client.protocol.heartbeat = 5
        # We only have a single server connection
        server = self._servers['server-9940']['factory'].servers[0]
        server.protocol.heartbeat = 5

        # client -> server
        client.send_message(logon_message(client))

        # server <- client
        message = server.wait_for_message(title='waiting for logon')
        assert_is_not_none(message)
        assert_tag(message, [(35, FIX.LOGON)])

        # server -> client
        server.send_message(logon_message(server))
        server.start_heartbeat(True)

        # client <- server
        message = client.wait_for_message(title='waiting for logon ack')
        client.start_heartbeat(True)
        assert_is_not_none(message)
        assert_tag(message, [(35, FIX.LOGON)])

        # Logout
        client.send_message(logout_message(client))
        message = server.wait_for_message(title='waiting for logout')
        assert_is_not_none(message)
        assert_tag(message, [(35, FIX.LOGOUT)])

        server.send_message(logout_message(server))
        server.start_heartbeat(False)

        message = client.wait_for_message('waiting for logout ack')
        client.start_heartbeat(False)
        assert_is_not_none(message)
        assert_tag(message, [(35, FIX.LOGOUT)])

```
### Running the test

To run this, use the command line

```
	fixtest -c fixtest/simple/simple_config.py fixtest/simple/logon_controller.py

```


### Sample output

```
$ fixtest -c fixtest/simple/simple_config.py fixtest/simple/logon_controller.py

20:43:40.622253: ================
20:43:40.622346: Starting test: 2022-06-27
20:43:40.622380:   Module: fixtest/simple/logon_controller.py
20:43:40.622409:   Controller: LogonController
20:43:40.622435:   Config: fixtest/simple/simple_config.py
20:43:40.622607:
20:43:40.622641:   Test case: Simple-1
20:43:40.622668:   Description: Test of the command-line tool
20:43:40.622692: ================
20:43:40.622718: server:server-9940 starting on port 9940
20:43:40.623119: fixtest.fix.transport: server:server-9940 listening on port 9940
20:43:40.623590: client:client-9940 attempting localhost:9940
20:43:40.626348: client-9940: Connection made
20:43:40.626417: fixtest.fix.transport: client:client-9940 connected to localhost:9940
20:43:40.626520: Connected: <class 'fixtest.fix.transport.FIXTransportFactory'> : server-9940
20:43:40.626706: server-9940: Connection made
20:43:40.825728: client-9940: message sent
    Logon : 8=FIX.4.2, 9=68, 35=A, 49=FixClient, 56=FixServer, 98=0, 108=5, 34=1, 52=20220627-20:43:40, 10=044

20:43:40.826382: server-9940: message received
    Logon : 8=FIX.4.2, 9=68, 35=A, 49=FixClient, 56=FixServer, 98=0, 108=5, 34=1, 52=20220627-20:43:40, 10=044

20:43:40.828124: server-9940: message sent
    Logon : 8=FIX.4.2, 9=68, 35=A, 49=FixServer, 56=FixClient, 98=0, 108=5, 34=1, 52=20220627-20:43:40, 10=044

20:43:40.828550: client-9940: message received
    Logon : 8=FIX.4.2, 9=68, 35=A, 49=FixServer, 56=FixClient, 98=0, 108=5, 34=1, 52=20220627-20:43:40, 10=044

20:43:40.828837: client-9940: message sent
    Logout : 8=FIX.4.2, 9=57, 35=5, 49=FixClient, 56=FixServer, 34=2, 52=20220627-20:43:40, 10=052

20:43:40.829239: server-9940: message received
    Logout : 8=FIX.4.2, 9=57, 35=5, 49=FixClient, 56=FixServer, 34=2, 52=20220627-20:43:40, 10=052

20:43:40.829514: server-9940: message sent
    Logout : 8=FIX.4.2, 9=57, 35=5, 49=FixServer, 56=FixClient, 34=2, 52=20220627-20:43:40, 10=052

20:43:40.829935: client-9940: message received
    Logout : 8=FIX.4.2, 9=57, 35=5, 49=FixServer, 56=FixClient, 34=2, 52=20220627-20:43:40, 10=052

20:43:40.830365: client-9940: Connection lost
20:43:40.830687: server-9940: Connection lost
20:43:40.830949: ================
20:43:40.831028: Test status: ok


```

### More sample code

This is a sample of what the code would like if the logon/logout
code were removed and placed in the base class setup/teardown functions.

Thus leaving run() to perform the real test work.

```python

import logging

from fixtest.base.asserts import assert_is_not_none
from fixtest.fix.messages import new_order_message, execution_report

from fixtest.simple.simple_base import BaseClientServerController


class SimpleClientServerController(BaseClientServerController):
    """ The base class for FIX-based TestCaseControllers.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.testcase_id = 'Simple NewOrder test'
        self.description = 'Test of the command-line tool'

        self._logger = logging.getLogger(__name__)

    def run(self):
        """ Run the test.  Here we send a new_order and
            then a modify.
        """
        # client -> server
        self.client.send_message(
            new_order_message(self.client,
                              symbol='abc',
                              side='0',
                              order_type='1',
                              extra_tags=[(38, 100),      # orderQty
                                          (44, 10), ]))   # price

        # server <- client
        message = self.server.wait_for_message('waiting for new order')
        assert_is_not_none(message)

        # server -> client
        self.server.send_message(
            execution_report(self.server,
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

```

Here is the resulting output:

```
$ fixtest -c fixtest/simple/simple_config.py fixtest/simple/simple_test.py

20:47:29.508560: ================
20:47:29.508693: Starting test: 2022-06-27
20:47:29.508736:   Module: fixtest/simple/simple_test.py
20:47:29.508771:   Controller: SimpleClientServerController
20:47:29.508802:   Config: fixtest/simple/simple_config.py
20:47:29.509024:
20:47:29.509069:   Test case: Simple NewOrder test
20:47:29.509104:   Description: Test of the command-line tool
20:47:29.509135: ================
20:47:29.509168: server:server-9940 starting on port 9940
20:47:29.509656: fixtest.fix.transport: server:server-9940 listening on port 9940
20:47:29.510099: client:client-9940 attempting localhost:9940
20:47:29.512695: Connected: <class 'fixtest.fix.transport.FIXTransportFactory'> : server-9940
20:47:29.512901: server-9940: Connection made
20:47:29.513074: client-9940: Connection made
20:47:29.513142: fixtest.fix.transport: client:client-9940 connected to localhost:9940
20:47:29.714841: client-9940: message sent
    Logon : 8=FIX.4.2, 9=68, 35=A, 49=FixClient, 56=FixServer, 98=0, 108=5, 34=1, 52=20220627-20:47:29, 10=055

20:47:29.717093: server-9940: message received
    Logon : 8=FIX.4.2, 9=68, 35=A, 49=FixClient, 56=FixServer, 98=0, 108=5, 34=1, 52=20220627-20:47:29, 10=055

20:47:29.717503: server-9940: message sent
    Logon : 8=FIX.4.2, 9=68, 35=A, 49=FixServer, 56=FixClient, 98=0, 108=5, 34=1, 52=20220627-20:47:29, 10=055

20:47:29.718031: client-9940: message received
    Logon : 8=FIX.4.2, 9=68, 35=A, 49=FixServer, 56=FixClient, 98=0, 108=5, 34=1, 52=20220627-20:47:29, 10=055

20:47:29.718405: client-9940: message sent
    NewOrderSingle : 8=FIX.4.2, 9=139, 35=D, 49=FixClient, 56=FixServer, 11=client-9940/20220627/1, 21=1, 55=abc, 54=0, 60=20220627-20:47:29, 40=1, 38=100, 44=10, 34=2, 52=20220627-20:47:29, 10=098

20:47:29.718884: server-9940: message received
    NewOrderSingle : 8=FIX.4.2, 9=139, 35=D, 49=FixClient, 56=FixServer, 11=client-9940/20220627/1, 21=1, 55=abc, 54=0, 60=20220627-20:47:29, 40=1, 38=100, 44=10, 34=2, 52=20220627-20:47:29, 10=098

20:47:29.719284: server-9940: message sent
    ExecutionReport : (New) : 8=FIX.4.2, 9=224, 35=8, 49=FixServer, 56=FixClient, 11=client-9940/20220627/1, 21=1, 55=abc, 54=0, 60=20220627-20:47:29, 40=1, 38=100, 44=10, 34=2, 52=20220627-20:47:29, 37=server-9940/20220627/2, 17=server-9940/20220627/1, 20=0, 150=0, 39=0, 151=100, 14=0, 6=0, 10=167

20:47:29.719792: client-9940: message received
    ExecutionReport : (New) : 8=FIX.4.2, 9=224, 35=8, 49=FixServer, 56=FixClient, 11=client-9940/20220627/1, 21=1, 55=abc, 54=0, 60=20220627-20:47:29, 40=1, 38=100, 44=10, 34=2, 52=20220627-20:47:29, 37=server-9940/20220627/2, 17=server-9940/20220627/1, 20=0, 150=0, 39=0, 151=100, 14=0, 6=0, 10=167

20:47:29.720099: client-9940: message sent
    Logout : 8=FIX.4.2, 9=57, 35=5, 49=FixClient, 56=FixServer, 34=3, 52=20220627-20:47:29, 10=064

20:47:29.720481: server-9940: message received
    Logout : 8=FIX.4.2, 9=57, 35=5, 49=FixClient, 56=FixServer, 34=3, 52=20220627-20:47:29, 10=064

20:47:29.720759: server-9940: message sent
    Logout : 8=FIX.4.2, 9=57, 35=5, 49=FixServer, 56=FixClient, 34=3, 52=20220627-20:47:29, 10=064

20:47:29.721129: client-9940: message received
    Logout : 8=FIX.4.2, 9=57, 35=5, 49=FixServer, 56=FixClient, 34=3, 52=20220627-20:47:29, 10=064

20:47:29.721526: server-9940: Connection lost
20:47:29.721824: client-9940: Connection lost
20:47:29.722088: ================
20:47:29.722160: Test status: ok

```

## Changelog

### 0.2.0
Upgraded code to Python 3
Moved simple to fixtest/simple (use fixtest.simple instead of simple)

### 0.1.1
Fixed Issue #1.  Need to append the current directory to sys.path to load
modules correctly.
