#!/usr/bin/python
# encoding: utf-8
"""
misc.py
A place for miscellaneous statistical functions to live until there is a suitable place for them.

Created by Shane O'Connor 2014
"""

import math
from scipy.stats import pearsonr, spearmanr, normaltest, ks_2samp, kstest, norm
from tools.unmerged.rpache.functions_lib import gammaCC


def stability_classification_accuracy(experimental_values, predicted_values):
    pass


def fraction_correct(x_values, y_values, x_cutoff = 1.0, y_cutoff = 1.0):
    '''My version of the metric used in the Kellogg et al. paper.
       "Role of conformational sampling in computing mutation-induced changes in protein structure and stability", Proteins, Volume 79, Issue 3, pages 830–838, March 2011.
       http://dx.doi.org/10.1002/prot.22921
       Description: "The fraction correct is defined as the number of mutations categorized correctly divided by the total number of mutations in the benchmark set."
    '''
    num_points = len(x_values)
    assert(num_points == len(y_values))
    correct = 0.0
    for i in range(num_points):
        x = x_values[i]
        y = y_values[i]
        if (x >= x_cutoff) and (y >= y_cutoff): # both positive
            correct += 1.0
        elif (x <= -x_cutoff) and (y <= -y_cutoff): # both negative
            correct += 1.0
        elif (-x_cutoff < x < x_cutoff) and (-y_cutoff < y < y_cutoff): # both neutral
            correct += 1.0
    return correct / float(num_points)


def fraction_correct_fuzzy_linear_create_vector(z, z_cutoff, z_fuzzy_range):
    '''Helper function for fraction_correct_fuzzy_linear.'''
    import numpy
    assert(z_fuzzy_range * 2 < z_cutoff)
    if (z >= z_cutoff + z_fuzzy_range): # positive e.g. z >= 1.1
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
       is 1 for some range of values, 0 for a separate range, and between 0 and 1 for the in between range i.e.
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
    for i in range(num_points):
        x = x_values[i]
        y = y_values[i]
        y_cutoff = x_cutoff * y_scalar
        y_fuzzy_range = x_fuzzy_range * y_scalar
        xvec = fraction_correct_fuzzy_linear_create_vector(x, x_cutoff, x_fuzzy_range)
        yvec = fraction_correct_fuzzy_linear_create_vector(y, y_cutoff, y_fuzzy_range)
        correct += numpy.dot(xvec, yvec)
    return correct / float(num_points)


def mae(x_values, y_values):
    '''Mean absolute/unsigned error.'''
    import numpy
    num_points = len(x_values)
    assert(num_points == len(y_values) and num_points > 0)
    return numpy.sum(numpy.apply_along_axis(numpy.abs, 0, numpy.subtract(x_values, y_values))) / float(num_points)

# this was renamed from get_xy_dataset_correlations to match the DDG benchmark capture repository
def _get_xy_dataset_statistics(x_values, y_values, fcorrect_x_cutoff = 1.0, fcorrect_y_cutoff = 1.0, x_fuzzy_range = 0.1, y_scalar = 1.0):
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
    from scipy.stats import pearsonr, spearmanr, normaltest, ks_2samp, kstest, norm
    assert(len(x_values) == len(y_values))
    return dict(
        pearsonr = pearsonr(x_values, y_values),
        spearmanr = spearmanr(x_values, y_values),
        gamma_CC = gammaCC(x_values, y_values),
        MAE = mae(x_values, y_values),
        normaltestx = normaltest(x_values),
        normaltesty = normaltest(y_values),
        kstestx = kstest(x_values, 'norm'),
        kstesty = kstest(y_values, 'norm'),
        ks_2samp = ks_2samp(x_values, y_values),
        fraction_correct = fraction_correct(x_values, y_values, x_cutoff = fcorrect_x_cutoff, y_cutoff = fcorrect_y_cutoff),
        fraction_correct_fuzzy_linear = fraction_correct_fuzzy_linear(x_values, y_values, x_cutoff = fcorrect_x_cutoff, x_fuzzy_range = x_fuzzy_range, y_scalar = y_scalar),
    )


def get_xy_dataset_statistics(analysis_table, fcorrect_x_cutoff = 1.0, fcorrect_y_cutoff = 1.0, x_fuzzy_range = 0.1, y_scalar = 1.0):
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
    return _get_xy_dataset_statistics(x_values, y_values, fcorrect_x_cutoff = fcorrect_x_cutoff, fcorrect_y_cutoff = fcorrect_y_cutoff, x_fuzzy_range = x_fuzzy_range, y_scalar = y_scalar)


keymap = dict(
    pearsonr = "Pearson's R",
    spearmanr = "Spearman's R",
    gamma_CC = "Gamma correlation coef.",
    fraction_correct = "Fraction correct",
    fraction_correct_fuzzy_linear = "Fraction correct (fuzzy)",
    ks_2samp = "Kolmogorov-Smirnov test (XY)",
    kstestx = "X-axis Kolmogorov-Smirnov test",
    kstesty = "Y-axis Kolmogorov-Smirnov test",
    normaltestx = "X-axis normality test",
    normaltesty = "Y-axis normality test",
)


def format_stats_for_printing(stats):
    s = []
    newstats = {}
    for k, v in stats.iteritems():
        key = keymap.get(k, k)
        if k == 'ks_2samp':
            newstats[key] = '%0.3f (2-tailed p-value=%s)' % (v[0], str(v[1]))
        elif k == 'kstestx':
            newstats[key] = '%0.3f (p-value=%s)' % (v[0], str(v[1]))
        elif k == 'kstesty':
            newstats[key] = '%0.3f (p-value=%s)' % (v[0], str(v[1]))
        elif k == 'normaltestx':
            newstats[key] = '%0.3f (2-sided chi^2 p-value=%s)' % (v[0], str(v[1]))
        elif k == 'normaltesty':
            newstats[key] = '%0.3f (2-sided chi^2 p-value=%s)' % (v[0], str(v[1]))
        elif k == 'pearsonr':
            newstats[key] = '%0.3f (2-tailed p-value=%s)' % (v[0], str(v[1]))
        elif k == 'spearmanr':
            newstats[key] = '%0.3f (2-tailed p-value=%s)' % (v[0], str(v[1]))
        else:
            newstats[key] = '%0.3f' % v
    for k, v in sorted(newstats.iteritems()):
        s.append('%s: %s' % (str(k).ljust(32), str(v)))
    return '\n'.join(s)


def histogram(values, out_filepath, num_bins = 50):
    import matplotlib.pyplot as plt
    hist, bins = numpy.histogram(values, bins=num_bins)
    width = 0.7 * (bins[1] - bins[0])
    center = (bins[:-1] + bins[1:]) / 2
    plt.bar(center, hist, align='center', width=width)
    fig, ax = plt.subplots()
    ax.bar(center, hist, align='center', width=width)
    fig.savefig(out_filepath)
