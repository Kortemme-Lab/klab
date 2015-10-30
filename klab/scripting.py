#!/usr/bin/env python2

import os, shutil, glob
from contextlib import contextmanager

def print_warning(message, *args, **kwargs):
    import colortext
    if args or kwargs: message = message.format(*args, **kwargs)
    colortext.write(message + '\n', color='red')

def print_error_and_die(message, *args, **kwargs):
    print_warning(message + "  Aborting...", *args, **kwargs)
    raise SystemExit(1)

@contextmanager
def catch_and_print_errors():
    try:
        yield

    except KeyboardInterrupt:
        print

    except Exception as error:
        if hasattr(error, 'no_stack_trace'): print_warning(str(error))
        else: raise

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
