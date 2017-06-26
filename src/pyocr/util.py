#!/usr/bin/env python

import os

import re
import six


def digits_only(string):
    """Return all digits that the given string starts with."""
    match = re.match(r'(?P<digits>\d+)', string)
    if match:
        return int(match.group('digits'))
    return 0


def to_unicode(string):
    try:
        return six.u(string)
    except:
        # probably already decoded
        return string


def is_on_path(exec_name):
    """
    Indicates if the command 'exec_name' appears to be installed.

    Returns:
        True --- if it is installed
        False --- if it isn't
    """
    for dirpath in os.environ["PATH"].split(os.pathsep):
        path = os.path.join(dirpath, exec_name)
        if os.path.exists(path) and os.access(path, os.X_OK):
            return True
    return False
