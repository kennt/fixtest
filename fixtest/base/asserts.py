""" Assertions for use within the test controllers.

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import os
import sys


def assert_equals(condition_a, condition_b):
    """ Assert that both sides are equal """
    caller = sys._getframe(1)
    if condition_a != condition_b:
        raise AssertionError(
            '{2} != {3}, expected equal at {0} line {1}'.format(
                os.path.basename(caller.f_code.co_filename),
                caller.f_lineno,
                condition_a,
                condition_b))


def assert_not_equals(condition_a, condition_b):
    """ Assert that the sides are not equal """
    caller = sys._getframe(1)
    if condition_a == condition_b:
        raise AssertionError(
            '{2} == {3}, expected not equal at {0} line {1}'.format(
                os.path.basename(caller.f_code.co_filename),
                caller.f_lineno,
                condition_a,
                condition_b))


def assert_is_none(condition):
    """ Assert the condition is None """
    caller = sys._getframe(1)
    if condition is not None:
        raise AssertionError(
            '{2} is not None, expected None at {0} line {1}'.format(
                os.path.basename(caller.f_code.co_filename),
                caller.f_lineno,
                condition))


def assert_is_not_none(condition):
    """ Assert the condition is not None """
    caller = sys._getframe(1)
    if condition is None:
        raise AssertionError(
            '{2} is None, expected not None at {0} line {1}'.format(
                os.path.basename(caller.f_code.co_filename),
                caller.f_lineno,
                condition))


def assert_true(condition):
    """ Assert the condition is True """
    caller = sys._getframe(1)
    if condition is not True:
        raise AssertionError(
            '{2} is not True, expected True at {0} line {1}'.format(
                os.path.basename(caller.f_code.co_filename),
                caller.f_lineno,
                condition))


def assert_false(condition):
    """ Assert the condition is False """
    caller = sys._getframe(1)
    if condition is True:
        raise AssertionError(
            '{2} is True, expected False at {0} line {1}'.format(
                os.path.basename(caller.f_code.co_filename),
                caller.f_lineno,
                condition))


def assert_tag_exists(message, tags):
    """ Check to see that the tags exist in the message """
    caller = sys._getframe(1)
    for tag in tags:
        if tag not in message:
            raise AssertionError(
                '{2} not in message at {0} line {1}'.format(
                    os.path.basename(caller.f_code.co_filename),
                    caller.f_lineno,
                    tag))


def assert_tag(message, tags):
    """ Check to see that the tag and values are in the message """
    caller = sys._getframe(1)
    for tag in tags:
        if tag[0] not in message:
            raise AssertionError(
                '{2} not in message at {0} line {1}'.format(
                    os.path.basename(caller.f_code.co_filename),
                    caller.f_lineno,
                    tag[0]))
        if tag[1] != message[tag[0]]:
            raise AssertionError(
                'message[{2}] is {3}, expected {4} at {0} line {1}'.format(
                    os.path.basename(caller.f_code.co_filename),
                    caller.f_lineno,
                    tag[0],
                    message[tag[0]],
                    tag[1]))
