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

import sys
import os
import tempfile
import time
import getpass
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rc('text', usetex=True)
plt.rc('font', family='sans-serif')
from matplotlib.ticker import NullFormatter

import scipy
from klab.latex.util import make_latex_safe
from klab.stats.misc import mae

def plot_scatter(
    dataframe, x_series, y_series,
    output_name = 'scatter',
    output_directory = None,
    output_format = None,
    verbose = True,
    dropna = True,
    density_plot = False,
    plot_title = None,
    fig_dpi = 300,
    fig_width = None,
    fig_height = None,
    fig_grid = True,
    axis_label_size = 12.0,
):
    if not output_directory:
        output_directory = tempfile.mkdtemp( prefix = '%s-%s-plots_' % (time.strftime("%y%m%d"), getpass.getuser()) )
    fig, ax = plt.subplots()
    ax.grid(fig_grid)
    if dropna:
        dataframe = dataframe[[x_series, y_series]].replace([np.inf, -np.inf], np.nan).dropna()

    if not output_format:
        # If there are many points, save figure as a PNG (since PDFs perform poorly with many points)
        if max( len(dataframe.as_matrix([x_series])), len(dataframe.as_matrix([y_series])) ) >= 1500:
            output_format = 'png'
        else:
            output_format = 'pdf'

    output_path = os.path.join(output_directory, output_name + '.' + output_format)

    if density_plot:
        xdat = dataframe.as_matrix([x_series]).flatten()
        ydat = dataframe.as_matrix([y_series]).flatten()

        #histogram definition
        xyrange = [ [np.min(xdat), np.max(xdat)], [np.min(ydat), np.max(ydat)] ] # data range
        bins = [100, 100] # number of bins
        thresh = 3  #density threshold

        # histogram the data
        hh, locx, locy = scipy.histogram2d(xdat, ydat, range=xyrange, bins=bins)
        posx = np.digitize(xdat, locx)
        posy = np.digitize(ydat, locy)

        #select points within the histogram
        ind = (posx > 0) & (posx <= bins[0]) & (posy > 0) & (posy <= bins[1])
        hhsub = hh[posx[ind] - 1, posy[ind] - 1] # values of the histogram where the points are
        xdat_low = xdat[ind][hhsub < thresh] # low density points
        ydat_low = ydat[ind][hhsub < thresh]
        xdat_high = xdat[ind][hhsub >= thresh] # low density points
        ydat_high = ydat[ind][hhsub >= thresh]
        hh[hh < thresh] = np.nan # fill the areas with low density by NaNs

        plt.scatter(xdat_low, ydat_low, s = 10, alpha = 0.6, linewidth = 0.1)
        plt.scatter(xdat_high, ydat_high, s = 0.6, alpha = 0.15, linewidth = 0.1, color='white')
        plt.imshow(np.flipud(hh.T),cmap='jet',extent=np.array(xyrange).flatten(), interpolation='none')
        plt.colorbar(label = 'Counts per (high point density) histogram region')
    else:
        plt.scatter(dataframe[[x_series]], dataframe[[y_series]], s = 10, alpha = 0.6)

    plt.ylabel( make_latex_safe(y_series), fontsize = axis_label_size )
    plt.xlabel( make_latex_safe(x_series), fontsize = axis_label_size )
    if plot_title:
        plt.title( make_latex_safe(plot_title) )

    if verbose:
        print 'Saving scatterplot figure to:', output_path
    if fig_height and fig_width:
        plt.gcf().set_size_inches(fig_width, fig_height)
    plt.savefig(
        output_path, dpi = fig_dpi, format = output_format
    )
    plt.close()
    return output_path

def make_corr_plot(
    df, x_series, y_series,
    output_name = 'histogram_fit_scatter',
    output_directory = None,
    output_format = None,
    verbose = True,
    dropna = True,
    plot_title = None,
    fig_dpi = 300,
    fig_height = None,
    fig_width = None,
    fig_grid = True,
    scatter_alpha = 0.8,
    axis_label_size = 12.0,
    plot_11_line = False,
):
    if not output_directory:
        output_directory = tempfile.mkdtemp( prefix = '%s-%s-plots_' % (time.strftime("%y%m%d"), getpass.getuser()) )

    df = df[[x_series, y_series]].dropna()
    x = np.array(df.ix[:,0])
    y = np.array(df.ix[:,1])

    if not output_format:
        # If there are many points, save figure as a PNG (since PDFs perform poorly with many points)
        if max( len(x), len(y) ) >= 1500:
            output_format = 'png'
        else:
            output_format = 'pdf'

    fig_path = os.path.join(output_directory, output_name + '.' + output_format)

    nullfmt = NullFormatter()         # no labels

    # definitions for the axes
    left, width = 0.1, 0.65
    bottom, height = 0.1, 0.65
    bottom_h = left_h = left+width+0.02

    rect_scatter = [left, bottom, width, height]
    if plot_title:
        # Leave extra space for the plot title
        rect_histx = [left, bottom_h, width, 0.17]
        rect_text = [left_h, bottom_h, 0.2, 0.17]
    else:
        rect_histx = [left, bottom_h, width, 0.2]
        rect_text = [left_h, bottom_h, 0.2, 0.2]
    rect_histy = [left_h, bottom, 0.2, height]

    if fig_width and fig_height:
        plt.figure( 1, figsize=(fig_width, fig_height) )
    else:
        plt.figure( 1, figsize=(8, 8) )

    axScatter = plt.axes(rect_scatter)
    axHistx = plt.axes(rect_histx)
    axHisty = plt.axes(rect_histy)
    axText = plt.axes(rect_text)

    axText.set_axis_off()

    # no labels
    axHistx.xaxis.set_major_formatter(nullfmt)
    axHisty.yaxis.set_major_formatter(nullfmt)

    # the scatter plot:
    axScatter.scatter(x, y, alpha = scatter_alpha)
    axScatter.set_xlabel( make_latex_safe(df.columns[0]), fontsize = axis_label_size )
    axScatter.set_ylabel( make_latex_safe(df.columns[1]), fontsize = axis_label_size )
    axScatter.grid(fig_grid)


    # determine best fit line
    par = np.polyfit(x, y, 1, full=True)

    slope = par[0][0]
    intercept = par[0][1]
    xl = [min(x), max(x)]
    yl = [slope*xx + intercept for xx in xl]

    # coefficient of determination, plot text
    variance = np.var(y)
    residuals = np.var([(slope*xx + intercept - yy)  for xx,yy in zip(x,y)])
    Rsqr = 1-residuals/variance
    r, p_val = scipy.stats.stats.pearsonr(x, y)
    mae_value = mae(x, y)

    if max( len(x), len(y) ) >= 500:
        # From scipy documentation:
        # The p-value roughly indicates the probability of an uncorrelated system producing datasets that have a Pearson correlation
        # at least as extreme as the one computed from these datasets. The p-values are not entirely reliable but are probably
        # reasonable for datasets larger than 500 or so.
        axText.text(0, 1, '$R^2=%0.2f$\n$m=%.2f$\n$R=%.2f$\n$mae=%.2f$\n$p=%.2e$'% (Rsqr,slope, r, mae_value, p_val),
                    fontsize=16, ha='left', va='top'
        )
    else:
        # Too small for p-value to be reliable
        axText.text(0, 1, '$R^2=%0.2f$\n$m=%.2f$\n$R=%.2f$\n$mae=%.2f$'% (Rsqr,slope, r, mae_value),
                    fontsize=16, ha='left', va='top'
        )

    yerrUpper = [(xx*slope+intercept)+(slope*xx**2 + intercept*xx + par[2]) for xx in x]
    yerrLower = [(xx*slope+intercept)-(slope*xx**2 + intercept*xx + par[2]) for xx in x]

    axScatter.plot(xl, yl, '-r')
    # axScatter.plot(x, yerrLower, '--r')
    # axScatter.plot(x, yerrUpper, '--r')

    if plot_11_line:
        axScatter.plot(xl, xl, '-g')

    # now determine nice limits by hand:
    xbinwidth = np.max(np.fabs(x)) / 30.0
    ybinwidth = np.max(np.fabs(y)) / 30.0

    axScatter.set_xlim( (np.min(x), np.max(x)) )
    axScatter.set_ylim( (np.min(y), np.max(y)) )

    xbins = np.arange(np.min(x), np.max(x) + xbinwidth, xbinwidth)
    axHistx.hist(x, bins=xbins)
    ybins = np.arange(np.min(y), np.max(y) + ybinwidth, ybinwidth)
    axHisty.hist(y, bins=ybins, orientation='horizontal')
    axHisty.set_xticklabels([int(x) for x in axHisty.get_xticks()], rotation=50)

    axHistx.set_xlim( axScatter.get_xlim() )
    axHisty.set_ylim( axScatter.get_ylim() )

    axHistx.set_ylabel('Counts')
    axHisty.set_xlabel('Counts')

    if verbose:
        print 'Saving scatterplot to:', fig_path
    if plot_title:
        if fig_width and fig_height:
            plt.gcf().suptitle( make_latex_safe(plot_title), fontsize = fig_width*fig_height/4.1 )
        else:
            plt.gcf().suptitle( make_latex_safe(plot_title) )
    plt.savefig(fig_path, dpi = fig_dpi, format = output_format)
    plt.close()
    return fig_path

def plot_box(
    dataframe,
    output_name = 'bar',
    output_directory = None,
    output_format = None,
    verbose = True,
    dropna = True,
    plot_title = None,
    fig_dpi = 300,
    fig_width = None,
    fig_height = None,
    fig_grid = True,
    ylabel = None,
    xlabel = 'Data',
    plot_average = True,
    xtick_fontsize = 10,
    rotation_angle = 0,
    log_y = False,
    label_n = True,
):
    if not output_directory:
        output_directory = tempfile.mkdtemp( prefix = '%s-%s-plots_' % (time.strftime("%y%m%d"), getpass.getuser()) )

    fig, ax = plt.subplots()
    if dropna:
        dataframe = dataframe.replace([np.inf, -np.inf], np.nan).dropna()

    if not output_format:
        output_format = 'pdf'

    dataframe_columns = sorted(list(dataframe.columns.values))

    output_path = os.path.join(output_directory, output_name + '.' + output_format)

    meanpointprops = dict(marker='*', markeredgecolor='black',
                          markerfacecolor='firebrick')

    # Convert to list of columns because matplotlib chokes if array columns aren't of equal length
    data = [list(column) for column in dataframe.values.transpose()]
    bp = ax.boxplot(dataframe.values, notch=True, meanline=False,
                    showmeans = plot_average)
    plt.setp(bp['fliers'], color='forestgreen', marker='+', markersize=12)

    ax.set_xticklabels([make_latex_safe(x) for x in dataframe_columns], fontsize = xtick_fontsize, rotation = rotation_angle)

    y_min_limit = min(dataframe.min())
    y_max_limit = max(dataframe.max())
    bottom_pad = 0.05 * (y_max_limit - y_min_limit)
    y_min_limit = y_min_limit - bottom_pad

    if label_n:
        for i, column_name in enumerate(dataframe_columns):
            ax.text(i+1, y_min_limit + bottom_pad,
                    'n=%d' % len( dataframe[[column_name]] ),
                    fontsize = 8,
                    ha='center', va='bottom')

    if log_y:
        ax.set_yscale("log", nonposy='clip')

    if ylabel:
        plt.ylabel( make_latex_safe(ylabel) )
    if xlabel:
        plt.xlabel( make_latex_safe(xlabel) )
    if plot_title:
        plt.title( make_latex_safe(plot_title) )

    if verbose:
        print 'Saving bar plot figure to:', output_path
    if fig_height and fig_width:
        plt.gcf().set_size_inches(fig_width, fig_height)

    plt.savefig(
        output_path, dpi = fig_dpi, format = output_format
    )
    plt.close()
    return output_path
