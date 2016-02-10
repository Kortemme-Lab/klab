#!/usr/bin/env python2

# The MIT License (MIT)
#
# Copyright (c) 2015 Kyle Barlow
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

import re

latex_chars_to_escape = ['_']
spaced_chars_to_escape = []

def make_latex_safe(text, make_prettier = True):
    for char in latex_chars_to_escape:
        text = text.replace(char, '\\%s' % char)
    for char in spaced_chars_to_escape:
        text = text.replace(' %s ' % char, ' \\%s ' % char)
    if make_prettier:
        # Make exponent text prettier
        if '^' in text:
            text = re.sub(r'(\^)(\d+)', r'$\1{\2}$', text)
        # Convert to latex right arrows
        text = text.replace(' -> ', ' $\\rightarrow$\\ ')
        # Convert to prettier exponent scientific notation format
        text = re.sub(r'(\d+[.]\d+)(E)([+-]\d+)', r'$\1\\times10^{\3}$', text)
    return text
