#!/usr/bin/env python2

import os, shutil

def print_warning(message, *args, **kwargs):
    import colortext
    if args or kwargs: message = message.format(*args, **kwargs)
    colortext.write(message + '\n', color='red')

def print_error_and_die(message, *args, **kwargs):
    print_warning(message + "  Aborting...", *args, **kwargs)
    raise SystemExit(1)

def clear_directory(directory):
    if os.path.exists(directory): shutil.rmtree(directory)
    os.makedirs(directory)

