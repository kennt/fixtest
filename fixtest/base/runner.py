""" The main script that starts up twisted and runs the tests.

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import argparse
import datetime
import importlib
import inspect
import logging
import logging.config
import os
import signal
import sys
import threading

from twisted.internet import reactor
from twisted.internet.endpoints import serverFromString
from twisted.python import log

from fixtest.base.controller import TestCaseController
from fixtest.base.config import FileConfig
from fixtest.base.utils import log_text

VERSION_STRING = '0.1'


def _parse_command_line_args():
    """ Parse the argument iist via the argparse module.

        Returns: an argparse results object.
    """
    parser = argparse.ArgumentParser(description='FIX system test tool')
    parser.add_argument(
        'test_name',
        help='Name of the test file to run. ' +
             'This file must contain an instance of TestCaseController.')
    parser.add_argument(
        '-c', '--config-file',
        help='use this config file (default: "my_config.py")',
        default='my_config.py')
    parser.add_argument(
        '-v', '--version',
        help='Display the version number',
        action='store_true')
    parser.add_argument(
        '-d', '--debug',
        help='enable debug output',
        action='store_true',
        default=False)
    parser.add_argument(
        'args',
        help='Additional arguments will be passed onto the TestCaseController',
        nargs=argparse.REMAINDER)

    return parser.parse_args()


def _setup_logging_config():
    """ Sets up the logging configuration.  Placed here mainly
        to reduce the amount of clutter in main()
    """
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                # 'format': '%(thread)d %(message)s',
                'format': '%(message)s',
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            '': {
                'handlers': ['console'],
                'level': 'INFO',
            },
        },
    })


def _find_controller(module_name):
    """ Looks up the module and then looks for the TestController
        instance within the module.

        Arguments:
            module_name: The name of the module to load.  There should
                be a TestController-derived class within this module.
                Only the first one will be loaded and run.
    """
    if not os.path.isfile(module_name):
        print "Cannot find the file:" + module_name
        sys.exit(2)

    module_path = module_name.replace('/', '.')
    if module_path.endswith('.py'):
        module_path = module_path[:-3]
    module = importlib.import_module(module_path)

    cls = None

    for entry in dir(module):
        if entry == 'TestController':
            continue

        obj = getattr(module, entry)

        # The path to the module must be where we specified it.
        if obj.__module__ != module_path:
            continue

        # We are looking for a class
        if not inspect.isclass(obj):
            continue

        # The class must be a subclass of TestCaseController
        if not issubclass(obj, TestCaseController):
            continue

        # Victory!
        cls = obj
        break

    if cls is None:
        print "Cannot find the TestCaseController in the file:" + module_name
        sys.exit(2)
    return cls


def main():
    """ Main entrypoint for the tool.  This will be called from the
        command-line script.
    """
    _setup_logging_config()
    logger = logging.getLogger(__name__)

    test_thread = None
    controller = None

    def term_signal_handler(num, frame):
        """ The signal-handler for the Twisted reactor.
            We assume that all signals are to shutdown the reactor and cancel
            the running tests.
        """
        # pylint: disable=unused-argument
        if controller is not None:
            controller.cancel_test()

        # The actual stop gets called in the finally portion
        # of the run loop.
        # reactor.callInThread(reactor.stop)

    def start_test_thread(call_function):
        """ This will be called on the reactor thread to start up the
            testcase thread.
        """
        test_thread = threading.Thread(target=call_function)
        test_thread.start()

    arg_results = _parse_command_line_args()
    if arg_results.version is True:
        print "{0}, version {1}".format(sys.argv[0], VERSION_STRING)
        sys.exit(2)

    if arg_results.debug is True:
        logger.setLevel(logging.DEBUG)

        # Twisted logging
        observer = log.PythonLoggingObserver()
        observer.start()

    file_name = arg_results.config_file
    if not os.path.isfile(file_name):
        print "Cannot find the configuration file: {0}".format(file_name)
        sys.exit(2)
    config_file = FileConfig(file_name)

    # load/create the TestCaseController
    controller_class = _find_controller(arg_results.test_name)

    log_text(logger.info, None, '================')
    log_text(logger.info, None, 'Starting test: ' +
                                str(datetime.datetime.now().date()))
    log_text(logger.info, None, '  Module: ' + arg_results.test_name)
    log_text(logger.info, None, '  Controller: ' + controller_class.__name__)
    log_text(logger.info, None, '  Config: ' + file_name)

    controller = controller_class(config=config_file,
                                  test_params=arg_results.args)

    log_text(logger.info, None, '')
    log_text(logger.info, None, '  Test case: ' + controller.testcase_id)
    log_text(logger.info, None, '  Description: ' + controller.description)
    log_text(logger.info, None, '================')

    # startup the servers (they don't really startup until reactor.run())
    for server in controller.servers().values():
        log_text(logger.info, None,
                 'server:{0} starting on port {1}'.format(server['name'],
                                                          server['port']))
        endpoint = serverFromString(reactor,
                                    b"tcp:{0}".format(server['port']))
        factory = server['factory']
        deferred = endpoint.listen(factory)
        deferred.addCallbacks(factory.server_success,
                              callbackArgs=(server,),
                              errback=factory.server_failure,
                              errbackArgs=(server,))

    for sig in [signal.SIGINT, signal.SIGHUP, signal.SIGTERM, signal.SIGQUIT]:
        signal.signal(sig, term_signal_handler)

    reactor.callWhenRunning(start_test_thread, controller._execute_test)
    reactor.run()

    if test_thread is not None:
        test_thread.join()

    log_text(logger.info, None, '================')
    log_text(logger.info, None,
             "Test status: {0}\n".format(controller.test_status))
    sys.exit(controller.exit_value)
