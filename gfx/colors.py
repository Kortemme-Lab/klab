#!/usr/bin/python
# encoding: utf-8
"""
colors.py
Color-related functions.

Created by Shane O'Connor 2013
"""

import colorsys


def saturate_hex_color(hexcolor, adjustment = 1.0):
    '''Takes in an RGB color in 6-character hexadecimal with an optional preceding hash character.
       Returns the RGB color in the same format adjusted by saturation by the second parameter.'''
    assert(adjustment >= 0 and len(hexcolor) >= 1)
    prefix = ""
    if hexcolor[0] == '#':
        hexcolor = hexcolor[1:]
        prefix = "#"
    assert(len(hexcolor) == 6)

    if adjustment == 1.0:
        return "%s%s" % (prefix, hexcolor)
    else:
        hsvColor = list(colorsys.rgb_to_hsv(int(hexcolor[0:2], 16)/255.0, int(hexcolor[2:4], 16)/255.0, int(hexcolor[4:6], 16)/255.0))
        hsvColor[1] = min(1.0, hsvColor[1] * adjustment)
        rgbColor = [min(255, 255 * v) for v in colorsys.hsv_to_rgb(hsvColor[0], hsvColor[1], hsvColor[2])]
        return "%s%.2x%.2x%.2x" % (prefix, rgbColor[0], rgbColor[1], rgbColor[2])


def ggplot_color_wheel(n, start = 15, saturation_adjustment = None):
    '''Returns a list of colors with the same distributed spread as used in ggplot2.'''
    hues = range(start, start + 360, 360/n)
    rgbcolors = ['%x%x%x' % (255 * hlscol[0], 255 * hlscol[1], 255 * hlscol[2]) for hlscol in [colorsys.hls_to_rgb(float(h % 360) / 360.0, 0.65, 1.00) for h in hues]]
    if saturation_adjustment:
        return [saturate_hex_color(rgbcol, saturation_adjustment) for rgbcol in rgbcolors]
    else:
        return rgbcolors