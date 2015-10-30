#!/usr/bin/env python2

def get_git_root():
    import shlex
    from . import process
    command = shlex.split('git rev-parse --show-toplevel')
    directory = process.check_output(command)
    return directory.strip()

