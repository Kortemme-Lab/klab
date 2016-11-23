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
                              plot_title = '',
                              x_axis_label = '', y_axis_label = '',
                              min_y_value = None, max_y_value = None, min_x_value = None, max_x_value = None,
                              cap_x_min = None, cap_x_max = None, cap_y_min = None, cap_y_max = None,
                              ignore_capped_values_in_correlation = True,
                              color_by_category = False,
                              shape_by_category = False, shape_category_series_index = None,
                              shape_category_title = 'Case',
                              label_series_index = None, label_outliers = True, label_criterium = None, label_criterium_values = None,
                              use_geom_text_repel = True,
                              default_point_color = "black",
                              default_point_shape = 16,
                              color_wheel_starting_angle = 180,
                              color_wheel_saturation = 0.50,
                              category_color_map = None,
                              category_shape_map = None,
                              omit_axis_labels = True
):

    '''This function was adapted from the covariation benchmark.'''

    # todo: Abstract this graph from the current usage (DDG measurements).
    # todo: make the capped value for unquantified but classified measurements (e.g. DDG > 7 kcal/mol) parameterizable

    # todo: add an option to use geom_text_repel to avoid/reduce overlapping text
    # todo: allow users to provide colors for the facets / categories

    # Changeset
    # todo: Change it to take in a pandas dataframe instead of the data_table_headers + data_table parameters.
    # todo: remove all references to SNX27 and NHERF1 below and loop over the set of categories instead
    # todo: add an option to identify outliers by quantiles (over the set of errors |x - y|) rather than by fixed value

    import pprint
    from klab.fs.fsio import read_file
    import sys

    #print(df[facet_index])
    color_map = {}
    categories = list(df.ix[:, category_series_index].unique())
    category_series_name = df.columns.values[category_series_index]
    category_series_rname = 'c' + category_series_name # prefix with a string in case the first character is non-alphabetic
    legal_shapes = range(15, 18 + 1) + range(21, 25 + 1) + range(0, 14 + 1)
    num_categories = len(categories)
    if num_categories > len(legal_shapes):
        colortext.warning('Too many categories ({0}) to plot using meaningful shapes.'.format(num_categories))
        shape_by_category = False
        df['CategorizationShape'] = df.apply(lambda r: 16, axis = 1)
    else:
        category_shapes = dict(zip(categories, legal_shapes[:num_categories]))
        pprint.pprint(category_shapes)
        df['CategorizationShape'] = df.apply(lambda r: category_shapes[r[category_series_name]], axis = 1)
    categorization_shape_index = len(df.columns.values) - 1

    #'#fe794c',
    category_colors = get_spaced_plot_colors(num_categories, start = color_wheel_starting_angle, saturation = color_wheel_saturation)
    for x in xrange(num_categories):
        color_map[categories[x]] = '#' + category_colors[x]
    pprint.pprint(color_map)
    if category_color_map:
        # Allow the caller to override the default color settings
        df['CategorizationColor'] = df.apply(lambda r: category_color_map[r[category_series_name]], axis = 1) # todo: emove this line? we do not seem to use it since we force the order using the sorted_categories etc. lines below
        color_map = category_color_map
        color_by_category = True
    elif color_by_category:
        df['CategorizationColor'] = df.apply(lambda r: color_map[r[category_series_name]], axis = 1) # todo: emove this line? we do not seem to use it since we force the order using the sorted_categories etc. lines below
    else:
        df['CategorizationColor'] = df.apply(lambda r: '#000000', axis = 1) # todo: emove this line? we do not seem to use it since we force the order using the sorted_categories etc. lines below
    categorization_color_index = len(df.columns.values) - 1

    if category_shape_map:
        category_shapes = category_shape_map

    print(df)
    print(color_map)
    assert(use_geom_text_repel) # todo: make parameterizable
    sorted_categories = '","'.join([k for k, v in sorted(color_map.iteritems())])
    sorted_colors = '","'.join([v for k, v in sorted(color_map.iteritems())])
    sorted_shapes = ','.join([str(v) for k, v in sorted(category_shapes.iteritems())])

    try: os.mkdir(output_directory)
    except: pass
    assert(os.path.exists(output_directory))

    r_script = ''
    if False:#todo
        if shape_by_category:
            r_script += '''
    # Plot
    p <- qplot(main="", xerrors, yerrors, data=xy_data, xlab=xlabel, ylab=ylabel, alpha = I(txtalpha), shape=factor(categories), col=factor(Classification)) +'''
        else:
            r_script += '''
    # Plot
    p <- qplot(main="", xerrors, yerrors, data=xy_data, xlab=xlabel, ylab=ylabel, alpha = I(txtalpha), shape=factor(Classification), col=factor(Classification)) +'''

        if shape_by_category:
            legal_shapes_str = ', '.join(map(str, legal_shapes))
            r_script += '''
scale_shape_manual('%(shape_category_title)s', values = c(%(legal_shapes_str)s),
                    labels = c( "Similar" = countsim,  "%(x_series_name)s" = countX,        "%(y_series_name)s" = countY))'''

    # Create the R script
    r_script += '''
library(ggplot2)
library(gridExtra)
library(scales)
library(qualV)'''
    if use_geom_text_repel:
        r_script +='''
library(ggrepel) # install with 'install.packages("ggrepel")' inside the R interactive shell.
'''
    r_script += '''

# PNG generation
png('%(file_prefix)s.png', width=2560, height=2048, bg="white", res=600)
txtalpha <- 0.8
'''

    xy_table_filename = '{0}.txt'.format(file_prefix)
    xy_table_filepath = os.path.join(output_directory, xy_table_filename)
    data_table = df.to_csv(header = True, index = False)
    write_file(xy_table_filepath, data_table)

    r_script += '''
# Set the margins
par(mar=c(5, 5, 1, 1))

xy_data <- read.csv('%(xy_table_filename)s', header=T)# , stringsAsFactors = TRUE)

names(xy_data)[%(x_series_index)d + 1] <- "xvalues"
names(xy_data)[%(y_series_index)d + 1] <- "yvalues"
    '''

    # Create fit lines per category
    r_script += '''\n
# Create environments to function as hashtables
correlation_e <- new.env()
lmv_intercept_e <- new.env()
lmv_yvalues_e <- new.env()
r_values_e <- new.env()
'''

    if label_outliers:
        r_script +='''names(xy_data)[%(label_series_index)d + 1] <- "outlier_labels"'''

    r_script += '''
xlabel <- "%(x_axis_label)s"
ylabel <- "%(y_axis_label)s"
plot_title <- "%(plot_title)s"
xy_data
    '''

    # Create a subset of xy_data which pass cut-off criteria
    # This can be useful if e.g. values have been capped so that they can be plotted but the values are unquantified (e.g. "> 200")
    # and should not be considered in the correlation calculation
    r_script += '''
valid_xy_data <- xy_data # make a copy of the dataframe: note, copying is lazily evaluated until modification'''
    if cap_x_min != None:
        r_script += '''
valid_xy_data <- valid_xy_data[which(valid_xy_data$xvalues > {0:.3f}), ]'''.format(cap_x_min)
    if cap_x_max != None:
        r_script += '''
valid_xy_data <- valid_xy_data[which(valid_xy_data$xvalues < {0:.3f}), ]'''.format(cap_x_max)
    if cap_y_min != None:
        r_script += '''
valid_xy_data <- valid_xy_data[which(valid_xy_data$yvalues > {0:.3f}), ]'''.format(cap_y_min)
    if cap_y_max != None:
        r_script += '''
valid_xy_data <- valid_xy_data[which(valid_xy_data$yvalues < {0:.3f}), ]'''.format(cap_y_max)

    if ignore_capped_values_in_correlation:
        # Overwrite the old value of R which used all datapoints
        r_script += '''\ndata_for_correlation = valid_xy_data'''
    else:
        r_script += '''\ndata_for_correlation = xy_data'''

    r_script += '''
# coefs contains two values: (Intercept) and yvalues
coefs <- coef(lm(yvalues~xvalues, data = data_for_correlation))
lmv_intercept_e$global_ <- as.numeric(coefs[1])
lmv_yvalues_e$global_ <- as.numeric(coefs[2])

fitcoefs = coef(lm(xvalues~0 + yvalues, data = data_for_correlation))
fitlmv_yvalues <- as.numeric(fitcoefs[1])
lm(data_for_correlation$yvalues~data_for_correlation$xvalues)

correlation_e$global_ <- cor(data_for_correlation$yvalues, data_for_correlation$xvalues)
#lmv_intercept_e$global_ <- as.numeric(fitcoefs[1])
#lmv_yvalues_e$global_ <- as.numeric(fitcoefs[2])

correlation_e$global_
lmv_intercept_e$global_
lmv_yvalues_e$global_

r_values_e$global_ <- cor(data_for_correlation$yvalues, data_for_correlation$xvalues)

data_for_correlation
r_values_e$global_

'''

    categories = list(df.ix[:, category_series_index].unique())
    for ctgry in categories:
        nctgry = 'c' + ctgry
        print ctgry

        r_script += '''
valid_xy_data_{0} <- valid_xy_data[which(valid_xy_data${1} == '{2}'),]
valid_xy_data_{0}
coefs_{0} <- coef(lm(yvalues~xvalues, data = valid_xy_data_{0}))
coefs_{0}
lmv_intercept_{0} <- as.numeric(coefs_{0}[1])
lmv_yvalues_{0} <- as.numeric(coefs_{0}[2])
correlation_e${0} <- cor(valid_xy_data_{0}$yvalues, valid_xy_data_{0}$xvalues)
lmv_intercept_e${0} <- lmv_intercept_{0}
lmv_yvalues_e${0} <- lmv_yvalues_{0}

lmv_intercept_{0}
lmv_yvalues_{0}
        '''.format(nctgry, category_series_name, ctgry)

        r_script += '''
valid_xy_data_{0}
lmv_yvalues_e${0}
lmv_intercept_e${0}

r_values_e${0} <- cor(valid_xy_data_{0}$yvalues, valid_xy_data_{0}$xvalues)
r_values_e${0}
    '''.format(nctgry)
#rvalue_{0} <-
#rvalue_{0}

    # Set graph limits
    r_script += '''
# Set graph limits and the position for the correlation value

#minx <- min(0.0, min(xy_data$xvalues) - 0.1)
#miny <- min(0.0, min(xy_data$yvalues) - 0.1)
#maxx <- max(1.0, max(xy_data$xvalues) + 0.1)
#maxy <- max(1.0, max(xy_data$yvalues) + 0.1)

minx <- min(xy_data$xvalues) - 0.1
miny <- min(xy_data$yvalues) - 0.1
maxx <- max(xy_data$xvalues) + 0.1
maxy <- max(xy_data$yvalues) + 0.1
    '''
    if min_x_value != None:
        r_script += '''
minx <- min(minx, %(min_x_value)f)'''
    if max_x_value != None:
        r_script += '''
maxx <- max(maxx, %(max_x_value)f) + 0.2'''
    if min_y_value != None:
        r_script += '''
miny <- min(miny  - 0.2, %(min_y_value)f  - 0.2)'''
    if max_y_value != None:
        r_script += '''
maxy <- max(maxy + 0.5, %(max_y_value)f  + 0.5)'''


    if label_criterium == 'diff_absolute':
        assert(len(label_criterium_values) == 2)
        (outlier_neg, outlier_pos) = sorted(label_criterium_values)
        colortext.warning(str(outlier_neg) + ' : ' + str(outlier_pos))
    elif label_criterium == 'diff_quantile':
        assert(len(label_criterium_values) == 2)
        (lower_range, high_range) = sorted(label_criterium_values)
        assert((0 <= lower_range <= 100) and (0 <= high_range <= 100))
        # todo: quantile outliers
        r_script += '''
quantile(xy_data)

lowerq = quantile(xy_data)[2]
upperq = quantile(xy_data)[4]
lowerq
upperq
                        #iqr = upperq - lowerq  # Or use IQR(data)
        '''

    # todo: label outliers
    # todo: add all R correlations
    #

    r_script += '''
correlation_label_x <- minx + ((maxx - minx) * 0.03)
correlation_label_y <- maxy - ((maxy - miny) * 0.05)

lrt <- expression('R'^tst)

'''

#    todo: legend if color_by_category or shape_by_category:
#        CategorizationColor
#        CategorizationShape

    print(sorted_categories)
    print(sorted_colors)
    print(sorted_shapes)
    r_script += '''
static_categories <- c("%(sorted_categories)s")'''

    if shape_by_category:
        r_script += '''
static_shapes <- c(%(sorted_shapes)s)
names(static_shapes) <- static_categories
shape_scale <-  scale_shape_manual(name = "%(shape_category_title)s", values = static_shapes, labels = static_categories)'''


    if color_by_category:
        r_script += '''
static_colors <- c("%(sorted_colors)s")
names(static_colors) <- static_categories
color_scale <- scale_colour_manual(name = "%(shape_category_title)s", values = static_colors, labels = static_categories)

    #aes(x, y, colour = CategorizationColor_grp))
    #    + color_scale'''

    # todo qplot(main=""

    r_script += '''
    lmv_intercept_e$global_
    lmv_yvalues_e$global_

    lmv_intercept_e$c3QDO
    lmv_yvalues_e$c3QDO
    '''

    # Draw points
    if shape_by_category and color_by_category:
        r_script += '''

# Plot
p <- ggplot(xy_data, aes(xvalues, yvalues, shape=%(category_series_name)s, col=%(category_series_name)s)) +
    geom_point(alpha = txtalpha) +'''
    elif color_by_category:
        r_script += '''
# Plot
p <- ggplot(xy_data, aes(xvalues, yvalues, col=%(category_series_name)s)) +
     geom_point(shape = (default_point_shape)d, alpha = txtalpha) +'''

    elif shape_by_category:
        r_script += '''
# Plot
p <- ggplot(xy_data, aes(xvalues, yvalues, shape=%(category_series_name)s)) +
     geom_point(color = "%(default_point_color)s", alpha = txtalpha) +'''

    else:
        r_script += '''
# Plot
p <- ggplot(xy_data, aes(xvalues, yvalues)) +
     geom_point(shape = %(default_point_shape)d, color = "%(default_point_color)s", alpha = txtalpha) +
'''

    if shape_by_category:
        r_script += '''\n    shape_scale +'''
    if color_by_category:
        r_script += '''\n    color_scale +'''

    r_script += '''
    labs(title = "%(plot_title)s", x = xlabel, y = ylabel) +
    theme(plot.title = element_text(color = "#555555", size=rel(1.3))) +
    theme(axis.title = element_text(color = "#555555", size=rel(1.3))) +
    theme(axis.text.x  = element_text(size=rel(1.3))) +
    theme(axis.text.y  = element_text(size=rel(1.3))) +
    theme(legend.title = element_text(color = "#555555", size=rel(0.45)), legend.text = element_text(color = "#555555", size=rel(0.4))) +'''

    # todo: remove or parameterize. A solid line added for the CADRES 2016 plots to indicate unquantified values e.g. Kd > 200 micro M
    r_script += '''
    geom_vline(size = 0.5, color="black", xintercept = 4.0, alpha = 0.6) +'''

    # Correlation fit lines (global + one per facet
    r_script += '''
    # Diagonal (x=y)
    # todo: add as parameter
    #geom_abline(slope=1, intercept=0, linetype=3, size=0.25, alpha=0.4) +

    # Correlation fit lines (global + one per facet)
    geom_abline(size = 0.125, color="black", intercept = lmv_intercept_e$global_, slope = lmv_yvalues_e$global_, alpha=0.4) +'''

    for ctgry in categories:
        nctgry = 'c' + ctgry
        print ctgry

        r_script += '''
    geom_abline(size = 0.125, color="{1}", intercept = lmv_intercept_e${0}, slope = lmv_yvalues_e${0}, alpha=0.4) +
            '''.format(nctgry, color_map[ctgry])

    if label_outliers:
        r_script += '''

    # Label outliers
    geom_text_repel(size=1.5, segment.size = 0.15, color="#000000", alpha=0.6, data=subset(xy_data, abs(yvalues - xvalues) > %(outlier_neg)f & xvalues <= maxx / 2 & yvalues >=maxy/2), aes(xvalues, yvalues-maxy/100, label=outlier_labels)) +
    geom_text_repel(size=1.5, segment.size = 0.15, color="#000000", alpha=0.6, data=subset(xy_data, abs(yvalues - xvalues) > %(outlier_neg)f & xvalues <= maxx / 2 & yvalues < maxy/2), aes(xvalues, yvalues+2*maxy/100, label=outlier_labels)) +
    geom_text_repel(size=1.5, segment.size = 0.15, color="#000000", alpha=0.6, data=subset(xy_data, abs(yvalues - xvalues) > %(outlier_neg)f & xvalues > maxx / 2 & yvalues >=maxy/2), aes(xvalues, yvalues-maxy/100, label=outlier_labels)) +
    geom_text_repel(size=1.5, segment.size = 0.15, color="#000000", alpha=0.6, data=subset(xy_data, abs(yvalues - xvalues) > %(outlier_neg)f & xvalues > maxx / 2 & yvalues < maxy/2), aes(xvalues, yvalues+2*maxy/100, label=outlier_labels)) +'''

    r_script += '''
    annotate("text", hjust=0, size = 4, colour="#222222", x = correlation_label_x, y = correlation_label_y, label = sprintf("R = %%0.2f", round(r_values_e$global_, digits = 4))) + # add correlation text; hjust=0 sets left-alignment. Using annotate instead of geom_text avoids blocky text caused by geom_text being run multiple times over the series
'''

    #outlier_neg, outlier_pos


    #geom_text(hjust=0, size=2, colour="black", aes(x = correlation_label_x, y = correlation_label_y, label = sprintf("R == %%0.2f", round(r_values_e$global_, digits = 4))), parse = TRUE) +

    counter = 1
    for ctgry in categories:
        nctgry = 'c' + ctgry
        r_script += '''
    annotate("text", hjust=0, size = 4, color="{1}", x = correlation_label_x, y = correlation_label_y - ((maxy - miny) * 0.07 * {2}), label = sprintf("R = %%0.2f", round(r_values_e${0}, digits = 4))) + # add correlation text; hjust=0 sets left-alignment. Using annotate instead of geom_text avoids blocky text caused by geom_text being run multiple times over the series
'''.format(nctgry, color_map[ctgry], counter)
        counter += 1

    #geom_text(hjust = 0, size=1.5, color="#000000", alpha=0.6, data=subset(xy_data, abs(yvalues - xvalues) > 2 & xvalues <= 0), aes(xvalues, yvalues+0.35, label=outlier_labels), check_overlap = TRUE) + # label outliers
    #geom_text(hjust = 1, size=1.5, color="#000000", alpha=0.6, data=subset(xy_data, abs(yvalues - xvalues) > 2 & xvalues > 0), aes(xvalues, yvalues+0.35, label=outlier_labels), check_overlap = TRUE) + # label outliers


    a= '''
        todo: make parameterizable coord_cartesian(xlim = c(minx, maxx), ylim = c(miny, maxy)) + # set the graph limits

        geom_text(hjust=0, size=2, colour="black", aes(x = correlation_label_x, y = correlation_label_y, label = sprintf("R == %%0.2f", round(rvalue, digits = 4))), parse = TRUE) +

        ypos_SNX27 <- correlation_label_y - 1
        ypos_NHERF1 <- ypos_SNX27 - 1

        geom_text(hjust=0, size=2, colour="darkorange", aes(x = correlation_label_x, y = ypos_NHERF1, label = sprintf("R[NHERF] == %%0.2f", round(rvalue_NHERF1, digits = 4))), parse = TRUE) +
        geom_text(hjust=0, size=2, colour="blue", aes(x = correlation_label_x, y = ypos_SNX27, label = sprintf("R[SNX27] == %%0.2f", round(rvalue_SNX27, digits = 4))), parse = TRUE) +


        theme(legend.position = "none")
#       geom_text(hjust=0, size=2, colour="black", aes(correlation_label_x, correlation_label_y, fontface="plain", family = "sans", label=paste(sprintf("R = %%0.2f%%s", round(rvalue, digits = 4), lrt), expression('R'[3])  ))) # add correlation text; hjust=0 sets left-alignment

#geom_text(hjust=0, size=3, colour="black", aes(correlation_label_x, correlation_label_y, fontface="plain", family = "sans", label=sprintf("R = %%0.2f", round(rvalue, digits = 4)))) # add correlation text; hjust=0 sets left-alignment
#       geom_text(hjust=0, size=3, colour="black", aes(correlation_label_x, correlation_label_y, fontface="plain", family = "sans", label=sprintf("R = %%0.2f", round(rvalue, digits = 4)))) # add correlation text; hjust=0 sets left-alignment
'''

    r_script += '''
    #theme(legend.position = "right")
    theme(legend.position = "none")  # todo: make parameterizable

# Plot graph
p
dev.off()
        '''


    #geom_point(aes(color = C)) +
    #color = "%(series_color)s"

    # Create the R script
    plot_type = 'png'
    #png_plot_commands = single_plot_commands % locals()
    r_script = r_script % locals()
    r_script_filename = '{0}.R'.format(file_prefix)
    r_script_filepath = os.path.join(output_directory, r_script_filename)
    write_file(r_script_filepath, r_script)

    # Run the R script
    run_r_script(r_script_filename, cwd = output_directory)

    #assert (shape_by_category == 1)
    #assert (shape_category_series_index == -1)
    #assert (shape_category_title == 1)
    #assert (label_series_index  == -1)
    #assert (label_outliers == 1)
    #assert (use_geom_text_repel == 1)




    x = '''
#3QDO = SNX27
#1G9O = NHERF1

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


miny <- -6
maxy <- 12.5

'''
