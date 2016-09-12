#!/usr/bin/python
# encoding: utf-8
"""
The correctness "abacus" plot displays measurements M (e.g. the difference in binding affinity given in kcal/mol)
over a set of cases (e.g. peptide binders) and possibly many categories (e.g. binding partners). For each case on the X-axis,
the measurement is shown on the Y-axis as a point.

Points are further distinguished by a second set of measurements N where |M| = |N|. Each m in M is categorized into one of
three classes: beneficial, neutral, or deleterious according to some cut-off for M. If the corresponding n in N has the same
categorization according to the cut-off for N then this point is plotted as a grey circle indicating a correct prediction.
Otherwise, the point is plotted as:
  - a red triangle if n is classified as deleterious;
  - a blue diamond if n is classified as neutral;
  - a green triangle if n is classified as beneficial.

This plot allows incorrectly classified values n in N to be distinguished by color and shape and also indicates the type
of wrong classification. A shaded region is drawn on the plot to identify the neutral zone which helps to identify cases
which are near-misses due to edge artifacts.

This function was used to generate assessment plots for CADRES 2016.
See .examples/plot/graphs for expected output.

todo: Abstract this graph from the current usage (DDG measurements).

Created by Shane O'Connor 2016
"""

import os

import numpy

from klab import colortext
from klab.fs.fsio import write_file
from klab.plot.rtools import run_r_script


def _determine_fraction_correct_class(x, y, x_cutoff = 1.0, y_cutoff = 1.0):
    if (x == None or y == None or numpy.isnan(x) or numpy.isnan(y)):  # If we are missing values then we either discount the case or consider it as incorrect depending on ignore_null_values
        return None
    elif (x >= x_cutoff) and (y >= y_cutoff):  # both positive
        return ('Correct', 16, 'black') # black circles
    elif (x <= -x_cutoff) and (y <= -y_cutoff):  # both negative
        return ('Correct', 16, 'black') # black circles
    elif (-x_cutoff < x < x_cutoff) and (-y_cutoff < y < y_cutoff):  # both neutral
        return ('Correct', 16, 'black') # black circles

    # Only incorrect categorizations are left
    elif (y >= y_cutoff):
        return ('Positive', 17, 'red') # red triangles
    elif (y <= -y_cutoff):
        return ('Negative', 25, 'green') # green inverted triangles
    else:
        return ('Neutral', 18, 'blue') # grey diamonds


def correctness_abacus_plot(output_directory, file_prefix, df,
                                   x_series_index, y_series_index, facet_index, peptide_index, series_color, plot_title = '', x_axis_label = '', y_axis_label = '',
                                   fcorrect_x_cutoff = 1.0, fcorrect_y_cutoff = 1.0,
                                   min_experimental_ddg = None,
                                   max_experimental_ddg = None):
    try:
        os.mkdir(output_directory)
    except:
        pass
    assert (os.path.exists(output_directory))

    #first_peptide = df.ix[:, peptide_index].min()
    #last_peptide = df.ix[:, peptide_index].max()

    df['Categorization'] = df.apply(lambda r: _determine_fraction_correct_class(r[x_series_index], r[y_series_index])[0], axis = 1)
    categorization_index = len(df.columns.values) - 1
    df['CategorizationShape'] = df.apply(lambda r: _determine_fraction_correct_class(r[x_series_index], r[y_series_index])[1], axis = 1)
    categorization_shape_index = len(df.columns.values) - 1
    df['CategorizationColor'] = df.apply(lambda r: _determine_fraction_correct_class(r[x_series_index], r[y_series_index])[2], axis = 1)
    categorization_color_index = len(df.columns.values) - 1

    # Create the R script
    boxplot_r_script = '''
library(ggplot2)
library(gridExtra)
library(scales)
library(qualV)

# PNG generation
png('%(file_prefix)s.png', width=2560, height=2048, bg="white", res=600)
txtalpha <- 0.6
redtxtalpha <- 0.6

%(png_plot_commands)s
        '''

    xy_table_filename = '{0}.txt'.format(file_prefix)
    xy_table_filepath = os.path.join(output_directory, xy_table_filename)

    header_names = df.columns.values
    #x_series = header_names[x_series_index]
    #y_series = header_names[y_series_index]
    facet_series = header_names[facet_index]
    peptide_series = header_names[peptide_index]
    #categorization_series = header_names[categorization_index]
    #print(x_series,y_series, facet_series, peptide_series, categorization_series)

    data_table = df.to_csv(header = True, index = False)
    print(data_table)

    df = df.sort_values([facet_series, peptide_series])
    data_table = df.to_csv(header = True, index = False)
    print(data_table)

    write_file(xy_table_filepath, data_table)

    main_plot_script = '''
# Set the margins
par(mar=c(5, 5, 1, 1))

xy_data <- read.csv('%(xy_table_filename)s', header=T)

names(xy_data)[%(x_series_index)d + 1] <- "xvalues"
names(xy_data)[%(y_series_index)d + 1] <- "yvalues"
names(xy_data)[%(facet_index)d + 1] <- "facets"
names(xy_data)[%(peptide_index)d + 1] <- "peptides"
names(xy_data)[%(categorization_index)d + 1] <- "categorization"
names(xy_data)[%(categorization_shape_index)d + 1] <- "categorization_shape"
names(xy_data)[%(categorization_color_index)d + 1] <- "categorization_color"


xy_data[%(peptide_index)d + 1]

peptide_names <- sort(xy_data[[%(peptide_index)d + 1]])

peptide_names
class(peptide_names)

first_peptide = peptide_names[1]
last_peptide = peptide_names[length(peptide_names)]

xlabel <- "%(x_axis_label)s"
ylabel <- "%(y_axis_label)s"
plot_title <- "%(plot_title)s"

xy_data

# Set graph limits and the position for the correlation value

miny <- min(0.0, min(xy_data$xvalues) - 0.1) # "X-axis" values are plotted on to Y-axis
maxy <- max(1.0, max(xy_data$xvalues) + 0.1)
'''

    if min_experimental_ddg != None:
        main_plot_script += '''
miny <- min(miny  - 0.2, %(min_experimental_ddg)f  - 0.2)
'''
    if min_experimental_ddg != None:
        main_plot_script += '''
maxy <- max(maxy + 0.5, %(min_experimental_ddg)f  + 0.5)

first_peptide
last_peptide
'''

    main_plot_script += '''

#aes(color = categorization_color, shape = categorization_shape)

p <- ggplot(data=xy_data, aes(x=peptides, y = xvalues, color = categorization_color, shape = categorization_color, group = facets)) +
       theme(legend.position = "none") + # hide the legend
       annotate("rect", xmin = first_peptide, xmax = last_peptide, ymin = -1, ymax = +1, alpha = .2) +
       xlab(xlabel) +
       labs(title = "%(plot_title)s") +
       theme(plot.title = element_text(color = "#555555", size=rel(0.55))) +
       labs(x = xlabel, y = ylabel) +
       theme(axis.text.x = element_text(angle = 90, hjust = 1, size = 3)) +
       geom_point() +
       scale_colour_manual(values = c("black", "blue", "green", "red")) +
       scale_shape_manual(values = c(16, 18, 25, 17)) +
       facet_wrap(~facets)

# Plot graph
p
dev.off()
        '''

    # Create the R script
    plot_type = 'png'
    png_plot_commands = main_plot_script % locals()
    boxplot_r_script = boxplot_r_script % locals()
    r_script_filename = '{0}.R'.format(file_prefix)
    r_script_filepath = os.path.join(output_directory, r_script_filename)
    write_file(r_script_filepath, boxplot_r_script)

    # Run the R script
    run_r_script(r_script_filename, cwd = output_directory)
