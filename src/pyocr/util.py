#!/usr/bin/env python

import os


def to_unicode(string):
    if hasattr(string, 'decode'):
        return string.decode('utf-8')
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
