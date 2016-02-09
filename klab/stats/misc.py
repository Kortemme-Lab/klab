#!/usr/bin/env python2
# encoding: utf-8

# The MIT License (MIT)
#
# Copyright (c) 2015 Shane O'Connor, Roland A. Pache
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
"""
misc.py
A place for miscellaneous statistical functions to live until there is a suitable place for them.

Created by Shane O'Connor 2014
"""


import math
import numpy
import scipy
from scipy.stats import pearsonr, spearmanr, normaltest, ks_2samp, kstest, norm

from klab.unmerged.rpache.functions_lib import gamma_CC
from klab.fs.fsio import write_temp_file


class FrequencyCounter(object):

    def __init__(self):
        self.items = {}

    def add(self, item):
        self.items[item] = self.items.get(item, 0)
        self.items[item] += 1


def stability_classification_accuracy(experimental_values, predicted_values):
    pass


def fraction_correct_values(indices, x_values, y_values, x_cutoff = 1.0, y_cutoff = 1.0, ignore_null_values = False):
    '''
    An approximation to the metric used in the Kellogg et al. paper: "The fraction correct is defined as the number of mutations categorized correctly divided by the total number of mutations in the benchmark set."
    '''
    num_points = len(indices)
    assert(num_points == len(x_values) == len(y_values))
    correct = []
    for i in range(num_points):
        index = indices[i]
        x = x_values[i]
        y = y_values[i]
        if (x == None or y == None or numpy.isnan(x) or numpy.isnan(y)) and ignore_null_values: # If we are missing values then we either discount the case or consider it as incorrect depending on ignore_null_values
            correct.append(numpy.nan)
        elif (x >= x_cutoff) and (y >= y_cutoff): # both positive
            correct.append(1.0)
        elif (x <= -x_cutoff) and (y <= -y_cutoff): # both negative
            correct.append(1.0)
        elif (-x_cutoff < x < x_cutoff) and (-y_cutoff < y < y_cutoff): # both neutral
            correct.append(1.0)
        else:
            correct.append(0.0)
    return correct


def fraction_correct(x_values, y_values, x_cutoff = 1.0, y_cutoff = 1.0, ignore_null_values = False):
    '''My version of the metric used in the Kellogg et al. paper.
       "Role of conformational sampling in computing mutation-induced changes in protein structure and stability", Proteins, Volume 79, Issue 3, pages 830–838, March 2011.
       http://dx.doi.org/10.1002/prot.22921
       Description: "The fraction correct is defined as the number of mutations categorized correctly divided by the total number of mutations in the benchmark set."
    '''

    expected_types, xtypes, ytypes = set([type(None), type(1.0), numpy.float64]), set(map(type, x_values)), set(map(type, x_values))
    assert(not(xtypes.difference(expected_types)) and not(ytypes.difference(expected_types)))

    num_points = len(x_values)
    considered_points = num_points
    assert(num_points == len(y_values))
    correct = 0.0
    for i in range(num_points):
        x = x_values[i]
        y = y_values[i]
        if (x == None or y == None or numpy.isnan(x) or numpy.isnan(y)) and ignore_null_values: # If we are missing values then we either discount the case or consider it as incorrect depending on ignore_null_values
            considered_points -= 1
        elif (x >= x_cutoff) and (y >= y_cutoff): # both positive
            correct += 1.0
        elif (x <= -x_cutoff) and (y <= -y_cutoff): # both negative
            correct += 1.0
        elif (-x_cutoff < x < x_cutoff) and (-y_cutoff < y < y_cutoff): # both neutral
            correct += 1.0
    return correct / float(considered_points)


def fraction_correct_pandas(dataframe, x_series, y_series, x_cutoff = 1.0, y_cutoff = 1.0, ignore_null_values = False):
    '''A little (<6%) slower than fraction_correct due to the data extraction overhead.'''
    return fraction_correct(dataframe[x_series].values.tolist(), dataframe[y_series].values.tolist(), x_cutoff = x_cutoff, y_cutoff = y_cutoff, ignore_null_values = ignore_null_values)


def add_fraction_correct_values_to_dataframe(dataframe, x_series, y_series, new_label, x_cutoff = 1.0, y_cutoff = 1.0, ignore_null_values = False):
    '''Adds a new column (new_label) to the dataframe with the fraction correct computed over X and Y values.'''
    new_series_values = fraction_correct_values(dataframe.index.values.tolist(), dataframe[x_series].values.tolist(), dataframe[y_series].values.tolist(), x_cutoff = x_cutoff, y_cutoff = y_cutoff, ignore_null_values = ignore_null_values)
    dataframe.insert(len(dataframe.columns), new_label, new_series_values)


def fraction_correct_fuzzy_linear_create_vector(z, z_cutoff, z_fuzzy_range):
    '''A helper function for fraction_correct_fuzzy_linear.'''
    assert(z_fuzzy_range * 2 < z_cutoff)

    if (z == None or numpy.isnan(z)): # todo: and ignore_null_values: # If we are missing values then we either discount the case or consider it as incorrect depending on ignore_null_values
        return None
    elif (z >= z_cutoff + z_fuzzy_range): # positive e.g. z >= 1.1
        return [0, 0, 1]
    elif (z <= -z_cutoff - z_fuzzy_range):  # negative e.g. z <= -1.1
        return [1, 0, 0]
    elif (-z_cutoff + z_fuzzy_range <= z <= z_cutoff - z_fuzzy_range): # neutral e.g. -0.9 <= z <= 0.9
        return [0, 1, 0]
    elif (-z_cutoff - z_fuzzy_range < z < -z_cutoff + z_fuzzy_range): # negative/neutral e.g. -1.1 < z < 0.9
        neutrality = (z + z_cutoff + z_fuzzy_range) / (z_fuzzy_range * 2)
        zvec = [1 - neutrality, neutrality, 0]
    elif (z_cutoff - z_fuzzy_range < z < z_cutoff + z_fuzzy_range): # neutral/positive e.g. 0.9 < z < 1.1
        positivity = (z - z_cutoff + z_fuzzy_range) / (z_fuzzy_range * 2)
        zvec = [0, 1 - positivity, positivity]
    else:
        raise Exception('Logical error.')
    # normalize the vector
    length = math.sqrt(numpy.dot(zvec, zvec))
    return numpy.divide(zvec, length)


def fraction_correct_fuzzy_linear(x_values, y_values, x_cutoff = 1.0, x_fuzzy_range = 0.1, y_scalar = 1.0):
    '''A version of fraction_correct which is more forgiving at the boundary positions.
       In fraction_correct, if the x value is 1.01 and the y value is 0.99 (with cutoffs of 1.0) then that pair evaluates
       to zero despite the results being very close to each other.
       This function corrects for the boundary by overlapping the ranges and attenuating the endpoints.
       This version of the function uses a linear approach - a classification (positive, negative, neutral resp. P, N, X)
       is 1 for some range of values, 0 for a separate range, and between 0 and 1 for the in-between range i.e.
           N       X        P
          ----\  /----\  /-----
               \/      \/
               /\      /\
          ----/  \----/  \----
       This approach was suggested by Kale Kundert.
    '''
    num_points = len(x_values)
    assert(num_points == len(y_values))
    correct = 0.0
    considered_points = 0
    for i in range(num_points):
        x = x_values[i]
        y = y_values[i]
        y_cutoff = x_cutoff * y_scalar
        y_fuzzy_range = x_fuzzy_range * y_scalar
        xvec = fraction_correct_fuzzy_linear_create_vector(x, x_cutoff, x_fuzzy_range)
        yvec = fraction_correct_fuzzy_linear_create_vector(y, y_cutoff, y_fuzzy_range)
        if xvec != None and yvec != None:
            correct += numpy.dot(xvec, yvec)
            considered_points += 1
    return correct / float(considered_points)


def mae(x_values, y_values):
    '''Mean absolute/unsigned error.'''
    num_points = len(x_values)
    assert(num_points == len(y_values) and num_points > 0)
    return numpy.sum(numpy.apply_along_axis(numpy.abs, 0, numpy.subtract(x_values, y_values))) / float(num_points)


# this was renamed from get_xy_dataset_correlations to match the DDG benchmark capture repository
def _get_xy_dataset_statistics(x_values, y_values, fcorrect_x_cutoff = 1.0, fcorrect_y_cutoff = 1.0, x_fuzzy_range = 0.1, y_scalar = 1.0, ignore_null_values = False):
    '''
    A function which takes two lists of values of equal length with corresponding entries and returns a dict containing
    a variety of metrics.
    :param x_values: A list of values for the X-axis (experimental values).
    :param y_values: A list of values for the X-axis (predicted values).
    :param fcorrect_x_cutoff: See get_xy_dataset_statistics.
    :param fcorrect_y_cutoff: See get_xy_dataset_statistics.
    :param x_fuzzy_range: See get_xy_dataset_statistics.
    :param y_scalar: See get_xy_dataset_statistics.
    :return: A table of statistics.
    '''
    assert(len(x_values) == len(y_values))
    return dict(
        pearsonr = pearsonr(x_values, y_values),
        spearmanr = spearmanr(x_values, y_values),
        gamma_CC = gamma_CC(x_values, y_values),
        MAE = mae(x_values, y_values),
        normaltestx = normaltest(x_values),
        normaltesty = normaltest(y_values),
        kstestx = kstest(x_values, 'norm'),
        kstesty = kstest(y_values, 'norm'),
        ks_2samp = ks_2samp(x_values, y_values),
        fraction_correct = fraction_correct(x_values, y_values, x_cutoff = fcorrect_x_cutoff, y_cutoff = fcorrect_y_cutoff, ignore_null_values = ignore_null_values),
        fraction_correct_fuzzy_linear = fraction_correct_fuzzy_linear(x_values, y_values, x_cutoff = fcorrect_x_cutoff, x_fuzzy_range = x_fuzzy_range, y_scalar = y_scalar),
    )


def get_xy_dataset_statistics(analysis_table, fcorrect_x_cutoff = 1.0, fcorrect_y_cutoff = 1.0, x_fuzzy_range = 0.1, y_scalar = 1.0, ignore_null_values = False):
    '''
    A version of _get_xy_dataset_statistics which accepts a list of dicts rather than X- and Y-value lists.
    :param analysis_table: A list of dict where each dict has Experimental and Predicted float elements
    :param fcorrect_x_cutoff: The X-axis cutoff value for the fraction correct metric.
    :param fcorrect_y_cutoff: The Y-axis cutoff value for the fraction correct metric.
    :param x_fuzzy_range: The X-axis fuzzy range value for the fuzzy fraction correct metric.
    :param y_scalar: The Y-axis scalar multiplier for the fuzzy fraction correct metric (used to calculate y_cutoff and y_fuzzy_range in that metric)
    :return: A table of statistics.
    '''

    x_values = [record['Experimental'] for record in analysis_table]
    y_values = [record['Predicted'] for record in analysis_table]
    return _get_xy_dataset_statistics(x_values, y_values, fcorrect_x_cutoff = fcorrect_x_cutoff, fcorrect_y_cutoff = fcorrect_y_cutoff, x_fuzzy_range = x_fuzzy_range, y_scalar = y_scalar, ignore_null_values = ignore_null_values)


def get_xy_dataset_statistics_pandas(dataframe, x_series, y_series, fcorrect_x_cutoff = 1.0, fcorrect_y_cutoff = 1.0, x_fuzzy_range = 0.1, y_scalar = 1.0, ignore_null_values = False):
    '''
    A version of _get_xy_dataset_statistics which accepts a pandas dataframe rather than X- and Y-value lists.
    :param dataframe: A pandas dataframe
    :param x_series: The column name of the X-axis series
    :param y_series: The column name of the Y-axis series
    :param fcorrect_x_cutoff: The X-axis cutoff value for the fraction correct metric.
    :param fcorrect_y_cutoff: The Y-axis cutoff value for the fraction correct metric.
    :param x_fuzzy_range: The X-axis fuzzy range value for the fuzzy fraction correct metric.
    :param y_scalar: The Y-axis scalar multiplier for the fuzzy fraction correct metric (used to calculate y_cutoff and y_fuzzy_range in that metric)
    :return: A table of statistics.
    '''

    x_values = dataframe[x_series].tolist()
    y_values = dataframe[y_series].tolist()
    return _get_xy_dataset_statistics(x_values, y_values, fcorrect_x_cutoff = fcorrect_x_cutoff, fcorrect_y_cutoff = fcorrect_y_cutoff, x_fuzzy_range = x_fuzzy_range, y_scalar = y_scalar, ignore_null_values = ignore_null_values)


keymap = dict(
    # Dictionary matches stat name (key) with ('full string description', 'value information format string')
    pearsonr = ("Pearson's R", '(2-tailed p-value=%s)'),
    spearmanr = ("Spearman's R", '(2-tailed p-value=%s)'),
    gamma_CC = ("Gamma correlation coef.", ''),
    fraction_correct = ("Fraction correct", ''),
    fraction_correct_fuzzy_linear = ("Fraction correct (fuzzy)", ''),
    ks_2samp = ("Kolmogorov-Smirnov test (XY)", '(2-tailed p-value=%s)'),
    kstestx = ("X-axis Kolmogorov-Smirnov test", '(p-value=%s)'),
    kstesty = ("Y-axis Kolmogorov-Smirnov test", '(p-value=%s)'),
    normaltestx = ("X-axis normality test", '(2-sided chi^2 p-value=%s)'),
    normaltesty = ("Y-axis normality test", '(2-sided chi^2 p-value=%s)'),
)

def format_stats_for_printing(stats, floating_point_format = '%0.3f', sci_notation_format = '%.3E'):
    s = []
    newstats = {}
    for k, v in stats.iteritems():
        key, value_format_str = keymap.get(k, (k, ''))
        if len(value_format_str) > 0:
            value_str = floating_point_format + ' ' + value_format_str % sci_notation_format
            newstats[key] = value_str % (v[0], v[1])
        else:
            value_str = floating_point_format
            newstats[key] = floating_point_format % float(v)

    max_k_len = max([len(x) for x in newstats.keys()])
    for k, v in sorted(newstats.iteritems()):
        s.append('%s: %s' % (str(k).ljust(max_k_len), str(v)))
    return '\n'.join(s)

def format_stats_for_latex(stats, floating_point_format = '%0.3f'):
    raise Exception('Not yet implemented')
    s = []
    newstats = {}
    for k, v in stats.iteritems():
        key, value_format_str = keymap.get(k, (k, ''))
        if len(value_format_str) > 0:
            value_str = floating_point_format + ' ' + value_format_str
            newstats[key] = value_str % (v[0], str(v[1]))
        else:
            value_str = floating_point_format
            newstats[key] = floating_point_format % v[0]

    max_k_len = max([len(x) for x in newstats.keys()])
    for k, v in sorted(newstats.iteritems()):
        s.append('%s: %s' % (str(k).ljust(max_k_len), str(v)))
    return '\n'.join(s)
