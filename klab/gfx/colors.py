#!/usr/bin/python
# encoding: utf-8
"""
colors.py
Color-related functions.

Created by Shane O'Connor 2013
"""

import colorsys

from klab.pymath.discrete import dumb_relative_half_prime


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


def ggplot_color_wheel(n, start = 15, saturation_adjustment = None, saturation = 0.65, lightness = 1.0, prefix = ''):
    '''Returns a list of colors with the same distributed spread as used in ggplot2.
       A saturation of 0.5 will leave the input color at the usual saturation e.g. if start is 240 (240/360 = 0.66 = blue) and saturation is 0.5 then #0000ff will be returned.
    '''
    hues = range(start, start + 360, 360/n)
    rgbcolors = ['%.2x%.2x%.2x' % (255 * hlscol[0], 255 * hlscol[1], 255 * hlscol[2]) for hlscol in [colorsys.hls_to_rgb(float(h % 360) / 360.0, saturation, lightness) for h in hues]]
    if saturation_adjustment:
        return [saturate_hex_color(prefix + rgbcol, saturation_adjustment) for rgbcol in rgbcolors]
    else:
        return rgbcolors


def get_spaced_plot_colors(n, start = 45, saturation_adjustment = 0.7, saturation = 0.65, lightness = 1.0, prefix = ''):
    '''Returns a list of colors with the same distributed spread as used in ggplot2 (color wheel) but shaken up a little
       so that adjacent series have differing hues for larger values of n.'''

    assert (n > 0)
    if n <= 5:
        # For small n, the color wheel will generate colors which naturally differ
        return ggplot_color_wheel(n, start = start, saturation_adjustment = saturation_adjustment, saturation = saturation, lightness = lightness, prefix = prefix)
    else:
        # For larger values of n, generate n colors spaced
        plot_colors = ggplot_color_wheel(n, start = start, saturation_adjustment = saturation_adjustment, saturation = saturation, lightness = lightness, prefix = prefix)
        hp = dumb_relative_half_prime(n)
        color_wheel = [plot_colors[x % n] for x in range(0, hp * n, hp)]
        if not len(color_wheel) == len(set(color_wheel)):
            raise Exception('The color wheel was not generated correctly. Are {0} and {1} relatively prime?'.format(n, hp))
        return color_wheel