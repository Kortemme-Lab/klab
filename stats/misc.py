#!/usr/bin/python
# encoding: utf-8
"""
misc.py
A place for miscellaneous statistical functions to live until there is a suitable place for them.

Created by Shane O'Connor 2014
"""

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


def mae(x_values, y_values):
    '''Mean absolute/unsigned error.'''
    import numpy
    num_points = len(x_values)
    assert(num_points == len(y_values) and num_points > 0)
    return numpy.sum(numpy.apply_along_axis(numpy.abs, 0, numpy.subtract(x_values, y_values))) / float(num_points)


def get_xy_dataset_correlations(x_values, y_values, fcorrect_x_cutoff = 1.0, fcorrect_y_cutoff = 1.0):
    from scipy.stats import pearsonr, spearmanr, normaltest, ks_2samp, kstest, norm
    assert(len(x_values) == len(y_values))
    return dict(
        pearsonr = pearsonr(x_values, y_values),
        spearmanr = spearmanr(x_values, y_values),
        gammaCC = gammaCC(x_values, y_values),
        MAE = mae(x_values, y_values),
        normaltestx = normaltest(x_values),
        normaltesty = normaltest(y_values),
        kstestx = kstest(x_values, 'norm'),
        kstesty = kstest(y_values, 'norm'),
        ks_2samp = ks_2samp(x_values, y_values),
        fraction_correct = fraction_correct(x_values, y_values, x_cutoff = fcorrect_x_cutoff, y_cutoff = fcorrect_y_cutoff),
    )


def histogram(values, out_filepath, num_bins = 50):
    import matplotlib.pyplot as plt
    hist, bins = numpy.histogram(values, bins=num_bins)
    width = 0.7 * (bins[1] - bins[0])
    center = (bins[:-1] + bins[1:]) / 2
    plt.bar(center, hist, align='center', width=width)
    fig, ax = plt.subplots()
    ax.bar(center, hist, align='center', width=width)
    fig.savefig(out_filepath)