#!/usr/bin/python
# encoding: utf-8
"""
misc.py
A place for miscellaneous statistical functions to live until there is a suitable place for them.

Created by Shane O'Connor 2014
"""

from scipy.stats import pearsonr, spearmanr, normaltest, ks_2samp, kstest, norm
from tools.unmerged.rpache.functions_lib import gammaCC
import matplotlib.pyplot as plt
import numpy as np

def get_xy_dataset_correlations(x_values, y_values):
    assert(len(x_values) == len(y_values))
    return dict(
        pearsonr = pearsonr(x_values, y_values),
        spearmanr = spearmanr(x_values, y_values),
        gammaCC = gammaCC(x_values, y_values),
        normaltestx = normaltext(x_values),
        normaltesty = normaltext(y_values),
        kstestx = kstest(x_values),
        kstesty = kstest(y_values),
        ks_2samp = ks_2samp(x_values, y_values),
    )

def histogram(values, out_filepath, num_bins = 50):
    hist, bins = np.histogram(values, bins=num_bins)
    width = 0.7 * (bins[1] - bins[0])
    center = (bins[:-1] + bins[1:]) / 2
    plt.bar(center, hist, align='center', width=width)
    fig, ax = plt.subplots()
    ax.bar(center, hist, align='center', width=width)
    fig.savefig(out_filepath)