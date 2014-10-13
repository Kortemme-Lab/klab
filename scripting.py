#!/usr/bin/env python2

import os, shutil

def print_warning(message, *args, **kwargs):
    import colortext
    if args or kwargs: message = message.format(*args, **kwargs)
    colortext.write(message, color='red')

def print_error_and_die(message, *args, **kwargs):
    print_warning(message + "  Aborting...", *args, **kwargs)
    raise SystemExit(1)

def clear_directory(directory):
    if os.path.exists(directory): shutil.rmtree(directory)
    os.makedirs(directory)

def mkdir(newdir):
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired " \
                      "dir, '%s', already exists." % newdir)
    else:
        os.makedirs(newdir)
