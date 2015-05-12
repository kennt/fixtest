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
import time

from fixtest.base.asserts import *
from fixtest.base.controller import TestCaseController
from fixtest.base.queue import TestInterruptedError
from fixtest.base.utils import log_text
from fixtest.fix.constants import FIX
from fixtest.fix.messages import logon_message, logout_message
from fixtest.fix.transport import FIXTransportFactory


class LogonController(TestCaseController):
    """ The base class for FIX-based TestCaseControllers.

        This creates a client and a server that will 
        communicate with each other.  So they will use
        the same link config.
    """
    def __init__(self, **kwargs):
        super(LogonController, self).__init__(**kwargs)

        self.testcase_id = 'Simple-1'
        self.description = 'Test of the command-line tool'

        config = kwargs['config']

        self.server_config = config.get_role('test-server')
        self.server_config.update({'name': 'server-9000'})

        self.server_link_config = config.get_link('client', 'test-server')
        self.server_link_config.update({
            'sender_compid': self.server_link_config['test-server'],
            'target_compid': self.server_link_config['client'],
            })

        self.client_config = config.get_role('client')
        self.client_config.update({'name': 'client-9000'})

        self.client_link_config = config.get_link('client', 'test-server')
        self.client_link_config.update({
            'sender_compid': self.client_link_config['client'],
            'target_compid': self.client_link_config['test-server'],
            })

        self._servers = dict()
        self._clients = dict()

        factory = FIXTransportFactory('server-9000',
                                      self.server_config,
                                      self.server_link_config)
        factory.filter_heartbeat = False

        server = {
            'name': 'server-9000',
            'port': self.server_link_config['port'],
            'factory': factory,
        }
        self._servers[server['name']] = server

        # In the client case we do not need to provide a
        # factory, Just need a transport.
        client = {
            'name': 'client-9000',
            'host': self.client_link_config['host'],
            'port': self.client_link_config['port'],
            'node': factory.create_transport('client-9000',
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
        client = self._clients['client-9000']['node']
        client.protocol.heartbeat = 5
        # We only have a single server connection
        server = self._servers['server-9000']['factory'].servers[0]
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
	fixtest -c simple_config.py testcases/logon_test.py

```


### Sample output

```
(fixtest)~/dev/src/fixtest > fixtest -c simple/simple_config.py simple/logon_controller.py 
12:52:10.468172: ================
12:52:10.468496: Starting test: 2014-08-06
12:52:10.468643:   Module: simple/logon_controller.py
12:52:10.468778:   Controller: LogonController
12:52:10.468908:   Config: simple/simple_config.py
12:52:10.470420: 
12:52:10.470547:   Test case: Simple-1
12:52:10.470657:   Description: Test of the command-line tool
12:52:10.470761: ================
12:52:10.470868: server:server-9000 starting on port 9000
12:52:10.472101: fixtest.fix.transport: server:server-9000 listening on port 9000
12:52:10.472997: client:client-9000 attempting localhost:9000
12:52:12.810111: client-9000: Connection made
12:52:12.810329: fixtest.fix.transport: client:client-9000 connected to localhost:9000
12:52:12.810626: Connected: fixtest.fix.transport.FIXTransportFactory : server-9000
12:52:12.811074: server-9000: Connection made
12:52:13.010270: client-9000: message sent
    Logon : 8=FIX.4.2, 9=68, 35=A, 49=FixClient, 56=FixServer, 98=0, 108=5, 34=1, 52=20140806-12:52:13, 10=045

12:52:13.012275: server-9000: message received
    Logon : 8=FIX.4.2, 9=68, 35=A, 49=FixClient, 56=FixServer, 98=0, 108=5, 34=1, 52=20140806-12:52:13, 10=045

12:52:13.015563: server-9000: message sent
    Logon : 8=FIX.4.2, 9=68, 35=A, 49=FixServer, 56=FixClient, 98=0, 108=5, 34=1, 52=20140806-12:52:13, 10=045

12:52:13.016854: client-9000: message received
    Logon : 8=FIX.4.2, 9=68, 35=A, 49=FixServer, 56=FixClient, 98=0, 108=5, 34=1, 52=20140806-12:52:13, 10=045

12:52:13.017925: client-9000: message sent
    Logout : 8=FIX.4.2, 9=57, 35=5, 49=FixClient, 56=FixServer, 34=2, 52=20140806-12:52:13, 10=053

12:52:13.019156: server-9000: message received
    Logout : 8=FIX.4.2, 9=57, 35=5, 49=FixClient, 56=FixServer, 34=2, 52=20140806-12:52:13, 10=053

12:52:13.020144: server-9000: message sent
    Logout : 8=FIX.4.2, 9=57, 35=5, 49=FixServer, 56=FixClient, 34=2, 52=20140806-12:52:13, 10=053

12:52:13.021321: client-9000: message received
    Logout : 8=FIX.4.2, 9=57, 35=5, 49=FixServer, 56=FixClient, 34=2, 52=20140806-12:52:13, 10=053

12:52:13.022400: server-9000: Connection lost
12:52:13.022687: client-9000: Connection lost
12:52:13.023373: ================
12:52:13.023508: Test status: ok

```

### More sample code

This is a sample of what the code would like if the logon/logout
code were removed and placed in the base class setup/teardown functions.

Thus leaving run() to perform the real test work.

```python
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
        assert_is_not_none(message)```
```

Here is the resulting output:

```
17:48:15.066436: ================
17:48:15.066607: Starting test: 2014-08-07
17:48:15.066684:   Module: simple/simple_test.py
17:48:15.066757:   Controller: SimpleClientServerController
17:48:15.066827:   Config: simple/simple_config.py
17:48:15.067619: 
17:48:15.067700:   Test case: Simple NewOrder test
17:48:15.067772:   Description: Test of the command-line tool
17:48:15.067841: ================
17:48:15.067912: server:server-9940 starting on port 9940
17:48:15.068883: fixtest.fix.transport: server:server-9940 listening on port 9940
17:48:15.069471: client:client-9940 attempting localhost:9940
17:48:15.112361: Connected: fixtest.fix.transport.FIXTransportFactory : server-9940
17:48:15.112912: server-9940: Connection made
17:48:15.113281: client-9940: Connection made
17:48:15.113377: fixtest.fix.transport: client:client-9940 connected to localhost:9940
17:48:15.270715: client-9940: message sent
    Logon : 8=FIX.4.2, 9=68, 35=A, 49=FixClient, 56=FixServer, 98=0, 108=5, 34=1, 52=20140807-17:48:15, 10=058

17:48:15.271588: server-9940: message received
    Logon : 8=FIX.4.2, 9=68, 35=A, 49=FixClient, 56=FixServer, 98=0, 108=5, 34=1, 52=20140807-17:48:15, 10=058

17:48:15.272481: server-9940: message sent
    Logon : 8=FIX.4.2, 9=68, 35=A, 49=FixServer, 56=FixClient, 98=0, 108=5, 34=1, 52=20140807-17:48:15, 10=058

17:48:15.273204: client-9940: message received
    Logon : 8=FIX.4.2, 9=68, 35=A, 49=FixServer, 56=FixClient, 98=0, 108=5, 34=1, 52=20140807-17:48:15, 10=058

17:48:15.274292: client-9940: message sent
    NewOrderSingle : 8=FIX.4.2, 9=139, 35=D, 49=FixClient, 56=FixServer, 11=client-9940/20140807/1, 21=1, 55=abc, 54=0, 60=20140807-17:48:15, 40=1, 38=100, 44=10, 34=2, 52=20140807-17:48:15, 10=105

17:48:15.275188: server-9940: message received
    NewOrderSingle : 8=FIX.4.2, 9=139, 35=D, 49=FixClient, 56=FixServer, 11=client-9940/20140807/1, 21=1, 55=abc, 54=0, 60=20140807-17:48:15, 40=1, 38=100, 44=10, 34=2, 52=20140807-17:48:15, 10=105

17:48:15.276382: server-9940: message sent
    ExecutionReport : (New) : 8=FIX.4.2, 9=224, 35=8, 49=FixServer, 56=FixClient, 11=client-9940/20140807/1, 21=1, 55=abc, 54=0, 60=20140807-17:48:15, 40=1, 38=100, 44=10, 34=2, 52=20140807-17:48:15, 37=server-9940/20140807/2, 17=server-9940/20140807/1, 20=0, 150=0, 39=0, 151=100, 14=0, 6=0, 10=176

17:48:15.277720: client-9940: message received
    ExecutionReport : (New) : 8=FIX.4.2, 9=224, 35=8, 49=FixServer, 56=FixClient, 11=client-9940/20140807/1, 21=1, 55=abc, 54=0, 60=20140807-17:48:15, 40=1, 38=100, 44=10, 34=2, 52=20140807-17:48:15, 37=server-9940/20140807/2, 17=server-9940/20140807/1, 20=0, 150=0, 39=0, 151=100, 14=0, 6=0, 10=176

17:48:15.280502: client-9940: message sent
    Logout : 8=FIX.4.2, 9=57, 35=5, 49=FixClient, 56=FixServer, 34=3, 52=20140807-17:48:15, 10=067

17:48:15.281089: server-9940: message received
    Logout : 8=FIX.4.2, 9=57, 35=5, 49=FixClient, 56=FixServer, 34=3, 52=20140807-17:48:15, 10=067

17:48:15.282183: server-9940: message sent
    Logout : 8=FIX.4.2, 9=57, 35=5, 49=FixServer, 56=FixClient, 34=3, 52=20140807-17:48:15, 10=067

17:48:15.282773: client-9940: message received
    Logout : 8=FIX.4.2, 9=57, 35=5, 49=FixServer, 56=FixClient, 34=3, 52=20140807-17:48:15, 10=067

17:48:15.284066: server-9940: Connection lost
17:48:15.284246: client-9940: Connection lost
17:48:15.284561: ================
17:48:15.284648: Test status: ok
```

## Changelog

### 0.1.1
Fixed Issue #1.  Need to append the current directory to sys.path to load
modules correctly.
