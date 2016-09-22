#!/usr/bin/env python2

import os, shutil, glob
from functools import wraps

def print_warning(message, *args, **kwargs):
    import colortext
    if args or kwargs: message = message.format(*args, **kwargs)
    colortext.write(message + '\n', color='red')

def print_error_and_die(message, *args, **kwargs):
    aborting = "Aborting..."
    if not message.endswith('\n'):
        aborting = '  ' + aborting
    print_warning(message + aborting, *args, **kwargs)
    raise SystemExit(1)

class catch_and_print_errors:

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type == KeyboardInterrupt:
            print
            return True
        if getattr(exc_value, 'no_stack_trace', False):
            print_warning(str(exc_value))
            return True

    def __call__(self, function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            with self:
                return function(*args, **kwargs)
        return wrapper


def use_path_completion():
    import readline
    readline.set_completer_delims(' \t\n;')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(path_completer)

def path_completer(text, state):
    globs = glob.glob(os.path.expanduser(text) + '*') + [None]
    add_slash = lambda x: x + '/' if os.path.isdir(x) else x
    return add_slash(globs[state])

def clear_directory(directory):
    if os.path.exists(directory): shutil.rmtree(directory)
    os.makedirs(directory)

def relative_symlink(target, link_name):
    """Make a symlink to target using the shortest possible relative path."""
    link_name = os.path.abspath(link_name)
    abs_target = os.path.abspath(target)
    rel_target = os.path.relpath(target, os.path.dirname(link_name))

    if os.path.exists(link_name):
        os.remove(link_name)
    os.symlink(rel_target, link_name)
    

# Bread'n'butter shell commands.

def mkdir(newdir):
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired " \
                      "dir, '%s', already exists." % newdir)
    else:
        os.makedirs(newdir)

def touch(path):
    with open(path, 'w'):
        pass
