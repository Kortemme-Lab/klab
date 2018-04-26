#!/usr/bin/env python2

# The MIT License (MIT)
#
# Copyright (c) 2015 Shane O'Connor
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import sys

COLOR_OFF = '\033[0m'
BOLD = 1
UNDERLINE = 4
FLASHING = 5
INVERTED = 7
EFFECTS_ = [BOLD, UNDERLINE, FLASHING, INVERTED] 
EMPTY_TUPLE = (None, None)

colors = {
    # [Color code, dark]
    'lightblue'     : (34, False),
    'blue'          : (34, True),
    'lightgreen'    : (32, False),
    'green'         : (32, True),
    'yellow'        : (33, False),
    'orange'        : (33, True),
    'pink'          : (31, False),
    'red'           : (31, True),
    'cyan'          : (36, False),
    'aqua'          : (36, True),
    'lightpurple'   : (35, False),
    'purple'        : (35, True),
    'grey'          : (30, False),
    'black'         : (30, True),
    'white'         : (37, False),
    'silver'        : (37, True),
}


the_clinton = ['lightblue', 'lightgreen', 'yellow', 'orange', 'pink', 'lightpurple', 'cyan', 'blue', 'aqua', 'green', 'red', 'purple']


purple_revolution = ['lightpurple', 'white', 'purple'] # 2016-04-21


colors_to_html = {
    #'lightblue'        : (34, False),
    'blue'          : '00005f',
    'lightgreen'    : '00ff00',
    'green'         : '005f00',
    'yellow'        : 'cccc00',
    #'orange'       : (33, True),
    'pink'          : 'ff0000',
    #'red'          : (31, True),
    'cyan'          :'00ffff',
    #'aqua'         : (36, True),
    'lightpurple'   : 'd75fff',
    #'purple'       : (35, True),
    'grey'          : '666',
    'darkgrey'      : '222',
    #'black'            : (30, True),
    #'white'            : (37, False),
    'silver'        : 'eeeeee',
}
rainbow_ = ['blue', 'green', 'yellow', 'orange', 'red', 'purple', 'lightblue']
rasta_ = ['red', 'yellow', 'green']

def flush():
    sys.stdout.flush()

def make(s, color = 'silver', bgcolor = None, suffix = "", effect = None):
    color = color or 'white' # Handier than optional arguments when using compound calls
    colorcode, dark = colors.get(color, EMPTY_TUPLE)
    bgcolorcode, bgdark = colors.get(bgcolor, EMPTY_TUPLE)

    if colorcode:
        if dark == (effect == BOLD):
            colorcode += 60
        if effect in EFFECTS_:
            colorcode = "%d;%s" % (effect, colorcode)
        bgcolor = bgcolor or ""
        if bgcolor:
            bgcolorcode += 10
            if not bgdark:
                bgcolorcode += 60
            bgcolor = "\033[%sm" % bgcolorcode
        return '%s\033[%sm%s%s%s' % (bgcolor, colorcode, s, COLOR_OFF, suffix)
    else:
        return '%s%s' % (s, suffix)

def write(s, color = 'silver', bgcolor = None, suffix = "", effect = None, flush = False):
    sys.stdout.write(make(s, color = color, bgcolor = bgcolor, suffix = suffix, effect = effect))
    if flush:
        sys.stdout.flush()

def printf(s, color = 'silver', bgcolor = None, suffix = "", effect = None):
    sys.stdout.write(make(s, color = color, bgcolor = bgcolor, suffix = "%s\n" % suffix, effect = effect))

def bar(bgcolor, length, suffix = None):
    str = " " * length
    write(str, bgcolor = bgcolor, suffix = suffix)

def make_error(s):
    return make(s, color='red')

def error(s, suffix = "\n"):
    write(s, color = 'red', suffix = suffix)

def warning(s, suffix = "\n"):
    write(s, color = 'yellow', suffix = suffix)

def message(s, suffix = "\n"):
    write(s, color = 'green', suffix = suffix)

def rainbowprint(s, bgcolor = None, suffix = "\n", effect = None, rainbow = rainbow_):
    wrap = len(rainbow)
    count = 0
    for c in s:
        write(c, color = rainbow[count], bgcolor = bgcolor, effect = effect)
        count += 1
        if count >= wrap:
            count -= wrap
    write(suffix)

def rastaprint(s, bgcolor = None, suffix = "\n", effect = None):
    rainbowprint(s, bgcolor = bgcolor, suffix = suffix, effect = effect, rainbow = rasta_)

# I added these functions to make it easier to print with different colors
# The are shorthand for the write, printf, and make functions above
# e.g. colortext.pcyan('test') prints in cyan, colortext.wlightpurple('test') writes in light purple, colortext.mblue('test') returns a blue string
# Note: Python does not close the scope in for-loops so the closure definition looks odd - we need to explicitly capture the state of the c variable ("c=c")
# Note: we should handle kwargs here in the future
def sprint(str): print(str)
def xprint(*args): print(args)
def xjoin(*args): return ''.join(map(str, args))
for c in colors:
    allow_colors = False
    try:
        from sys import platform as _platform
        if _platform == "linux" or _platform == "linux2" or _platform == "darwin":
            allow_colors = True
    except: pass
    if allow_colors:
        setattr(sys.modules[__name__], 'w'  + c, lambda s, c=c : write(s, color = c, flush = True))
        setattr(sys.modules[__name__], 'p'  + c, lambda s, c=c : printf(s, color = c))
        setattr(sys.modules[__name__], 'm'  + c, lambda s, c=c : make(s, color = c))
    else:
        setattr(sys.modules[__name__], 'w'  + c, lambda s, c=c : sys.stdout(s))
        setattr(sys.modules[__name__], 'p'  + c, lambda s, c=c : xprint(s))
        setattr(sys.modules[__name__], 'm'  + c, lambda s, c=c : xjoin(s))


class Exception(Exception):
    def __init__(self, msg):
        self.message = make_error(msg)
    def __str__(self):
        return self.message


