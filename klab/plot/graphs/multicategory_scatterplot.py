#!/usr/bin/python
# encoding: utf-8
"""
The multi-category scatterplot is a regular scatterplot where we also display the correlations and best-fit lines for subsets
(categories) of the data. Categories are distinguished by color and shape.

This function was used to generate assessment plots for CADRES 2016.
See .examples/plot/graphs for expected output.

Created by Shane O'Connor 2016
"""

import os
import fractions

import numpy

from klab import colortext
from klab.fs.fsio import write_file
from klab.plot.rtools import run_r_script
from klab.gfx.colors import get_spaced_plot_colors


def multicategory_scatterplot(output_directory, file_prefix, df,
                              x_series_index, y_series_index, category_series_index,
                              series_color, plot_title = '',
                              x_axis_label = '', y_axis_label = '',
                              min_predicted_ddg = None, max_predicted_ddg = None, min_experimental_ddg = None, max_experimental_ddg = None):
    '''This function was adapted from the covariation benchmark.'''

    # todo: Abstract this graph from the current usage (DDG measurements).
    # todo: make the capped value for unquantified but classified measurements (e.g. DDG > 7 kcal/mol) parameterizable
    # todo: add an option to identify outliers by standard deviations (over the set of errors |x - y|) rather than by fixed value
    # todo: add an option to use geom_text_repel to avoid/reduce overlapping text
    # todo: allow users to provide colors for the facets / categories

    # Changeset
    # todo: Change it to take in a pandas dataframe instead of the data_table_headers + data_table parameters.
    # todo: Add exception if number of cases > 2 so the general case can be implemented once we have test data.
    # todo: use one column as the category e.g. "PDB". assert that there is a maximum number of categories. Test with > 2 categories
    # todo: remove all references to SNX27 and NHERF1 below and loop over the set of categories instead

    #print(df[facet_index])
    color_map = {}
    categories = list(df.ix[:, category_series_index].unique())
    print(type(categories))
    num_categories = len(categories)
    category_colors = get_spaced_plot_colors(num_categories)
    for x in xrange(num_categories):
        color_map[categories[x]] = '#' + category_colors[x]

    df['CategorizationColor'] = df.apply(lambda r: color_map[r[category_series_index]], axis = 1)
    categorization_color_index = len(df.columns.values) - 1

    # Monday: continue here
    print(df)
    sys.exit(0)
    try: os.mkdir(output_directory)
    except: pass
    assert(os.path.exists(output_directory))


    df['Categorization'] = df.apply(lambda r: _determine_fraction_correct_class(r[x_series_index], r[y_series_index])[0], axis = 1)
    categorization_index = len(df.columns.values) - 1
    df['CategorizationShape'] = df.apply(lambda r: _determine_fraction_correct_class(r[x_series_index], r[y_series_index])[1], axis = 1)
    categorization_shape_index = len(df.columns.values) - 1




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
    write_file(xy_table_filepath, '\n'.join(','.join(map(str, line)) for line in [data_table_headers] + data_table))

    single_plot_commands = '''
# Set the margins
par(mar=c(5, 5, 1, 1))

xy_data <- read.csv('%(xy_table_filename)s', header=T)

names(xy_data)[%(x_series_index)d + 1] <- "xvalues"
names(xy_data)[%(y_series_index)d + 1] <- "yvalues"

# coefs contains two values: (Intercept) and yvalues
coefs <- coef(lm(xvalues~yvalues, data = xy_data))
fitcoefs = coef(lm(xvalues~0 + yvalues, data = xy_data))
fitlmv_yvalues <- as.numeric(fitcoefs[1])
lmv_intercept <- as.numeric(coefs[1])
lmv_yvalues <- as.numeric(coefs[2])
lm(xy_data$yvalues~xy_data$xvalues)

xlabel <- "%(x_axis_label)s"
ylabel <- "%(y_axis_label)s"
plot_title <- "%(plot_title)s"
rvalue <- cor(xy_data$yvalues, xy_data$xvalues)
rvalue
xy_data

#3QDO = SNX27
#1G9O = NHERF1

valid_xy_data <- xy_data[which(xy_data$xvalues < 6.99),]
rvalue <- cor(valid_xy_data$yvalues, valid_xy_data$xvalues)
rvalue
valid_xy_data

valid_xy_data_NHERF1 <- xy_data[which(xy_data$xvalues < 6.99 & xy_data$PDB == '1G9O'),]
rvalue_NHERF1 <- cor(valid_xy_data_NHERF1$yvalues, valid_xy_data_NHERF1$xvalues)
rvalue_NHERF1
valid_xy_data_NHERF1

coefs_NHERF1 <- coef(lm(xvalues~yvalues, data = valid_xy_data_NHERF1))
lmv_intercept_NHERF1 <- as.numeric(coefs_NHERF1[1])
lmv_yvalues_NHERF1 <- as.numeric(coefs_NHERF1[2])

valid_xy_data_SNX27 <- xy_data[which(xy_data$xvalues < 6.99 & xy_data$PDB == '3QDO'),]
rvalue_SNX27 <- cor(valid_xy_data_SNX27$yvalues, valid_xy_data_SNX27$xvalues)
rvalue_SNX27
valid_xy_data_SNX27

coefs_SNX27 <- coef(lm(xvalues~yvalues, data = valid_xy_data_SNX27))
lmv_intercept_SNX27 <- as.numeric(coefs_SNX27[1])
lmv_yvalues_SNX27 <- as.numeric(coefs_SNX27[2])

lmv_intercept
lmv_yvalues
lmv_intercept_NHERF1
lmv_yvalues_NHERF1
lmv_intercept_SNX27
lmv_yvalues_SNX27

# Set graph limits and the position for the correlation value

minx <- min(0.0, min(xy_data$xvalues) - 0.1)
miny <- min(0.0, min(xy_data$yvalues) - 0.1)
maxx <- max(1.0, max(xy_data$xvalues) + 0.1)
maxy <- max(1.0, max(xy_data$yvalues) + 0.1)
    '''

    if min_predicted_ddg != None:
        single_plot_commands += '''
miny <- min(miny  - 0.2, %(min_predicted_ddg)f  - 0.2)
    '''
    if max_predicted_ddg != None:
        single_plot_commands += '''
maxy <- max(maxy + 0.5, %(max_predicted_ddg)f  + 0.5)

miny <- -6
maxy <- 12.5

    '''
    if min_experimental_ddg != None:
        single_plot_commands += '''
    minx <- min(minx, %(min_experimental_ddg)f)
        '''
    if max_experimental_ddg != None:
        single_plot_commands += '''
    maxx <- max(maxx, %(max_experimental_ddg)f) + 0.2
        '''

    single_plot_commands += '''
xpos <- minx + 0.2
ypos <- maxy - 1
ypos_SNX27 <- ypos - 1
ypos_NHERF1 <- ypos_SNX27 - 1

lrt <- expression('R'^tst)

p <- qplot(main="", xvalues, yvalues, data=xy_data, xlab=xlabel, ylab=ylabel, shape = PDB, alpha = I(txtalpha)) +
        geom_point(aes(color = PDB), alpha = 0.6) +
        scale_colour_manual(name="", values = c("1G9O"="orange", "3QDO"="blue", "3"="red", "value3"="grey", "value2"="black")) +
        labs(title = "%(plot_title)s") +
        theme(plot.title = element_text(color = "#555555", size=rel(0.75))) +

        # Correlation fit lines (global + one per facet
        geom_abline(size = 0.125, color="black", intercept = lmv_intercept, slope = lmv_yvalues, alpha=0.2) +
        geom_abline(size = 0.125, color="orange", intercept = lmv_intercept_NHERF1, slope = lmv_yvalues_NHERF1, alpha=0.4) +
        geom_abline(size = 0.125, color="blue", intercept = lmv_intercept_SNX27, slope = lmv_yvalues_SNX27, alpha=0.4) +

        geom_abline(slope=1, intercept=0, linetype=3, size=0.25, alpha=0.4) + # add a diagonal (dotted)
        coord_cartesian(xlim = c(minx, maxx), ylim = c(miny, maxy)) + # set the graph limits

        geom_text(hjust = 0, size=1.5, color="#000000", alpha=0.6, data=subset(xy_data, abs(yvalues - xvalues) > 2 & xvalues <= 0), aes(xvalues, yvalues+0.35, label=Origin_of_peptide), check_overlap = TRUE) + # label outliers
        geom_text(hjust = 1, size=1.5, color="#000000", alpha=0.6, data=subset(xy_data, abs(yvalues - xvalues) > 2 & xvalues > 0), aes(xvalues, yvalues+0.35, label=Origin_of_peptide), check_overlap = TRUE) + # label outliers
        geom_text(hjust=0, size=2, colour="black", aes(x = xpos, y = ypos, label = sprintf("R == %%0.2f", round(rvalue, digits = 4))), parse = TRUE) +
        geom_text(hjust=0, size=2, colour="darkorange", aes(x = xpos, y = ypos_NHERF1, label = sprintf("R[NHERF] == %%0.2f", round(rvalue_NHERF1, digits = 4))), parse = TRUE) +
        geom_text(hjust=0, size=2, colour="blue", aes(x = xpos, y = ypos_SNX27, label = sprintf("R[SNX27] == %%0.2f", round(rvalue_SNX27, digits = 4))), parse = TRUE) +
        theme(legend.position = "none")
#       geom_text(hjust=0, size=2, colour="black", aes(xpos, ypos, fontface="plain", family = "sans", label=paste(sprintf("R = %%0.2f%%s", round(rvalue, digits = 4), lrt), expression('R'[3])  ))) # add correlation text; hjust=0 sets left-alignment

#geom_text(hjust=0, size=3, colour="black", aes(xpos, ypos, fontface="plain", family = "sans", label=sprintf("R = %%0.2f", round(rvalue, digits = 4)))) # add correlation text; hjust=0 sets left-alignment
#       geom_text(hjust=0, size=3, colour="black", aes(xpos, ypos, fontface="plain", family = "sans", label=sprintf("R = %%0.2f", round(rvalue, digits = 4)))) # add correlation text; hjust=0 sets left-alignment

# Plot graph
p
dev.off()
        '''


    #geom_point(aes(color = C)) +
    #color = "%(series_color)s"

    # Create the R script
    plot_type = 'png'
    png_plot_commands = single_plot_commands % locals()
    boxplot_r_script = boxplot_r_script % locals()
    r_script_filename = '{0}.R'.format(file_prefix)
    r_script_filepath = os.path.join(output_directory, r_script_filename)
    write_file(r_script_filepath, boxplot_r_script)

    # Run the R script
    run_r_script(r_script_filename, cwd = output_directory)

