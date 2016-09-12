#!/usr/bin/python
# encoding: utf-8
"""
The error-by-error scatterplot takes a pandas dataframe containing a reference series (e.g. experimental values) and two
other series (e.g. predicted values) of equal length to plot the errors (|experimental - predicted|) against each other.
A legend counts the number of cases where one series is better than the other or similar.

The plot has a number of configurable settings including the range of similarity and whether or not to label outliers
(and what to use as the outliers).

This function was used to generate assessment plots for CADRES 2016.
See .examples/plot/graphs for expected output.

Created by Shane O'Connor 2016
"""

import os

from klab import colortext
from klab.fs.fsio import write_file
from klab.plot.rtools import run_r_script


def _classify_smallest_error(x_error, y_error, similarity_range, x_series_name = 'X', y_series_name = 'Y'):
    xydiff = x_error - y_error
    if -similarity_range <= xydiff <= similarity_range:
        return 'Similar'
    elif xydiff > 0:
        return y_series_name
    elif xydiff < 0:
        return x_series_name
    assert(False)


def error_by_error_scatterplot(output_directory, file_prefix, df,
                             reference_series_index, x_series_index, y_series_index,
                             x_color, y_color,
                             x_series_name = None, y_series_name = None,
                             plot_title = '', x_axis_label = '', y_axis_label = '', similarity_range = 0.25,
                             add_similarity_range_annotation = True,
                             shape_by_category = False, shape_category_series_index = None, shape_category_title = 'Case',
                             label_series_index = None, label_outliers = True,
                             use_geom_text_repel = True,
                             ):

    """ Creates a scatterplot of error versus error intended to show which computational method (X or Y) has the least amount of error relative to a reference series.

        The difference vectors (reference_series - x_series, reference_series - y_series) are created and these differences (errors)
        are plotted against each other.

        :param output_directory: The output directory.
        :param file_prefix: A prefix for the generated files. A CSV file with the plot points, the R script, and the R output is saved along with the plot itself.
        :param df: A pandas dataframe. Note: The dataframe is zero-indexed.
        :param reference_series_index: The numerical index of the reference series e.g. experimental data.
        :param x_series_index: The numerical index of the X-axis series e.g. predictions from a computational method.
        :param y_series_index: The numerical index of the Y-axis series e.g. predictions from a second computational method.
        :param x_color: The color of the "method X is better" points.
        :param y_color: The color of the "method Y is better" points.
        :param x_series_name: A name for the X-series which is used in the the classification legend.
        :param y_series_name: A name for the Y-series which is used in the the classification legend.
        :param plot_title: Plot title.
        :param x_axis_label: X-axis label.
        :param y_axis_label: Y-axis label.
        :param similarity_range: A point (x, y) is considered as similar if |x - y| <= similarity_range.
        :param add_similarity_range_annotation: If true then the similarity range is included in the plot.
        :param shape_by_category: Boolean. If set then points are shaped by the column identified with shape_category_series_index. Otherwise, points are shaped by classification ("X is better", "Y is better", or "Similar")
        :param shape_category_series_index: The numerical index of the series used to choose point shapes.
        :param shape_category_title: The title of the shape legend.
        :param label_series_index: The numerical index of the series label_series_index
        :param label_outliers: Boolean. If set then label outliers using the column identified with label_series_index.
        :param use_geom_text_repel: Boolean. If set then the ggrepel package is used to avoid overlapping labels.

        This function was adapted from the Kortemme Lab covariation benchmark (https://github.com/Kortemme-Lab/covariation).
        todo: I need to check that ggplot2 is respecting the color choices. It may be doing its own thing.
    """
    try:
        os.mkdir(output_directory)
    except:
        pass
    assert (os.path.exists(output_directory))

    if not isinstance(shape_category_series_index, int):
        shape_by_category = False
    if not isinstance(label_series_index, int):
        label_outliers = False
    assert(x_series_name != None and y_series_name != None)

    df = df.copy()
    headers = df.columns.values

    num_categories = len(set(df.ix[:, shape_category_series_index].values))
    legal_shapes = range(15,25+1) + range(0,14+1)
    if num_categories > len(legal_shapes):
        colortext.warning('Too many categories ({0}) to plot using meaningful shapes.'.format(num_categories))
        shape_by_category = False
    else:
        legal_shapes = legal_shapes[:num_categories]

    df['X_error'] = abs(df[headers[reference_series_index]] - df[headers[x_series_index]])
    x_error_index = len(df.columns.values) - 1
    df['Y_error'] = abs(df[headers[reference_series_index]] - df[headers[y_series_index]])
    y_error_index = len(df.columns.values) - 1

    # Get the list of domains common to both runs
    df['Classification'] = df.apply(lambda r: _classify_smallest_error(r['X_error'], r['Y_error'], similarity_range, x_series_name, y_series_name), axis = 1)
    error_classification_index = len(df.columns.values) - 1

    # Create the R script
    boxplot_r_script = '''
library(ggplot2)
library(gridExtra)
library(scales)
library(qualV)
library(grid)'''
    if use_geom_text_repel:
        boxplot_r_script +='''
library(ggrepel) # install with 'install.packages("ggrepel")' inside the R interactive shell.
'''
    boxplot_r_script += '''

# PNG generation
png('%(file_prefix)s.png', width=2560, height=2048, bg="white", res=600)
txtalpha <- 0.8
redtxtalpha <- 0.8

%(png_plot_commands)s
        '''

    xy_table_filename = '{0}.txt'.format(file_prefix)
    xy_table_filepath = os.path.join(output_directory, xy_table_filename)

    data_table = df.to_csv(header = True, index = False)
    write_file(xy_table_filepath, data_table)

    main_plot_script = '''
# Set the margins
par(mar=c(5, 5, 1, 1))

xy_data <- read.csv('%(xy_table_filename)s', header=T)

names(xy_data)[%(x_error_index)d + 1] <- "xerrors"
names(xy_data)[%(y_error_index)d + 1] <- "yerrors"
'''

    if label_outliers:
        main_plot_script +='''names(xy_data)[%(label_series_index)d + 1] <- "outlier_labels"'''
    main_plot_script +='''
names(xy_data)[%(shape_category_series_index)d + 1] <- "categories"

xy_data[%(x_error_index)d + 1]
xy_data[%(y_error_index)d + 1]

# coefs contains two values: (Intercept) and yerrors
coefs <- coef(lm(xerrors~yerrors, data = xy_data))
fitcoefs = coef(lm(xerrors~0 + yerrors, data = xy_data))
fitlmv_yerrors <- as.numeric(fitcoefs[1])
lmv_intercept <- as.numeric(coefs[1])
lmv_yerrors <- as.numeric(coefs[2])
lm(xy_data$yerrors~xy_data$xerrors)

xlabel <- "%(x_axis_label)s"
ylabel <- "%(y_axis_label)s"
plot_title <- "%(plot_title)s"
rvalue <- cor(xy_data$yerrors, xy_data$xerrors)

# Alphabetically, "Similar" < "X" < "Y" so the logic below works
countsim <- paste("Similar =", dim(subset(xy_data, Classification=="Similar"))[1])
countX <- paste("%(x_series_name)s =", dim(subset(xy_data, Classification=="%(x_series_name)s"))[1])
countY <- paste("%(y_series_name)s =", dim(subset(xy_data, Classification=="%(y_series_name)s"))[1])

countX
countY
countsim

# Set graph limits and the position for the correlation value

minx <- min(0.0, min(xy_data$xerrors) - 0.1)
miny <- min(0.0, min(xy_data$yerrors) - 0.1)
maxx <- max(1.0, max(xy_data$xerrors) + 0.1)
maxy <- max(1.0, max(xy_data$yerrors) + 0.1)

# Create a square plot (x-range = y-range)
minx <- min(minx, miny)
miny <- minx
maxx <- max(maxx, maxy)
maxy <- maxx

xpos <- maxx / 25.0
ypos <- maxy - (maxy / 25.0)
ypos_2 <- maxy - (2 * maxy / 25.0)


plot_scale <- scale_color_manual(
    "Counts",
    values = c( "Similar" = '#444444', "%(x_series_name)s" = '%(x_color)s', "%(y_series_name)s" ='%(y_color)s'),
    labels = c( "Similar" = countsim,  "%(x_series_name)s" = countX,        "%(y_series_name)s" = countY) )'''

    if add_similarity_range_annotation:
        main_plot_script += '''
# Polygon denoting the similarity range. We turn off plot clipping below (gt$layout$clip) so we need to be more exact than using 4 points when defining the region
boxy_mc_boxface <- data.frame(
  X = c(minx - 0,                        maxx - %(similarity_range)f, maxx + 0, maxx + 0,                       0 + %(similarity_range)f, 0),
  Y = c(minx - 0 + %(similarity_range)f, maxx + 0,                    maxx + 0, maxx + 0 -%(similarity_range)f, 0, 0 )
)'''
    else:
        main_plot_script += '''
# Polygon denoting the similarity range. We turn off plot clipping below (gt$layout$clip) so we need to be more exact than using 4 points when defining the region
boxy_mc_boxface <- data.frame(
  X = c(minx - 1, maxx + 1, maxx + 1, minx - 1),
  Y = c(minx - 1 + %(similarity_range)f, maxx + 1 + %(similarity_range)f, maxx + 1 - %(similarity_range)f, minx - 1 - %(similarity_range)f)
)'''

    if shape_by_category:
        main_plot_script += '''
# Plot
p <- qplot(main="", xerrors, yerrors, data=xy_data, xlab=xlabel, ylab=ylabel, alpha = I(txtalpha), shape=factor(categories), col=factor(Classification)) +'''
    else:
        main_plot_script += '''
# Plot
p <- qplot(main="", xerrors, yerrors, data=xy_data, xlab=xlabel, ylab=ylabel, alpha = I(txtalpha), shape=factor(Classification), col=factor(Classification)) +'''

    main_plot_script += '''
geom_polygon(data=boxy_mc_boxface, aes(X, Y), fill = "#bbbbbb", alpha = 0.4, color = "darkseagreen", linetype="blank", inherit.aes = FALSE, show.legend = FALSE) +
plot_scale +
geom_point() +
guides(col = guide_legend()) +
labs(title = "%(plot_title)s") +
theme(plot.title = element_text(color = "#555555", size=rel(0.75))) +
theme(axis.title = element_text(color = "#555555", size=rel(0.6))) +
theme(legend.title = element_text(color = "#555555", size=rel(0.45)), legend.text = element_text(color = "#555555", size=rel(0.4))) +
coord_cartesian(xlim = c(minx, maxx), ylim = c(miny, maxy)) + # set the graph limits
annotate("text", hjust=0, size = 2, colour="#222222", x = xpos, y = ypos, label = sprintf("R = %%0.2f", round(rvalue, digits = 4))) + # add correlation text; hjust=0 sets left-alignment. Using annotate instead of geom_text avoids blocky text caused by geom_text being run multiple times over the series'''

    if label_outliers:
        if use_geom_text_repel:
            main_plot_script += '''

# Label outliers
geom_text_repel(size=1.5, segment.size = 0.15, color="#000000", alpha=0.6, data=subset(xy_data, abs(yerrors - xerrors) > maxx/3 & xerrors <= maxx / 2 & yerrors >=maxy/2), aes(xerrors, yerrors-maxy/100, label=outlier_labels)) +
geom_text_repel(size=1.5, segment.size = 0.15, color="#000000", alpha=0.6, data=subset(xy_data, abs(yerrors - xerrors) > maxx/3 & xerrors <= maxx / 2 & yerrors < maxy/2), aes(xerrors, yerrors+2*maxy/100, label=outlier_labels)) +
geom_text_repel(size=1.5, segment.size = 0.15, color="#000000", alpha=0.6, data=subset(xy_data, abs(yerrors - xerrors) > maxx/3 & xerrors > maxx / 2 & yerrors >=maxy/2), aes(xerrors, yerrors-maxy/100, label=outlier_labels)) +
geom_text_repel(size=1.5, segment.size = 0.15, color="#000000", alpha=0.6, data=subset(xy_data, abs(yerrors - xerrors) > maxx/3 & xerrors > maxx / 2 & yerrors < maxy/2), aes(xerrors, yerrors+2*maxy/100, label=outlier_labels)) +'''
        else:
            main_plot_script += '''

# Label outliers
geom_text(hjust = 0, size=1.5, color="#000000", alpha=0.6, data=subset(xy_data, abs(yerrors - xerrors) > maxx/3 & xerrors <= maxx / 2 & yerrors >=maxy/2), aes(xerrors, yerrors-maxy/100, label=outlier_labels)) +
geom_text(hjust = 0, size=1.5, color="#000000", alpha=0.6, data=subset(xy_data, abs(yerrors - xerrors) > maxx/3 & xerrors <= maxx / 2 & yerrors < maxy/2), aes(xerrors, yerrors+2*maxy/100, label=outlier_labels)) +
geom_text(hjust = 1, size=1.5, color="#000000", alpha=0.6, data=subset(xy_data, abs(yerrors - xerrors) > maxx/3 & xerrors > maxx / 2 & yerrors >=maxy/2), aes(xerrors, yerrors-maxy/100, label=outlier_labels)) +
geom_text(hjust = 1, size=1.5, color="#000000", alpha=0.6, data=subset(xy_data, abs(yerrors - xerrors) > maxx/3 & xerrors > maxx / 2 & yerrors < maxy/2), aes(xerrors, yerrors+2*maxy/100, label=outlier_labels)) +'''

        counts_title = 'Counts'
        if add_similarity_range_annotation:
            counts_title += '*'

        main_plot_script += '''


#geom_text(hjust = 0, size=1.5, color="#000000", alpha=0.6, data=subset(xy_data, abs(yvalues - xvalues) > 2 & xvalues <= 0), aes(xvalues, yvalues+0.35, label=Origin_of_peptide), check_overlap = TRUE) + # label outliers
#geom_text(hjust = 1, size=1.5, color="#000000", alpha=0.6, data=subset(xy_data, abs(yvalues - xvalues) > 2 & xvalues > 0), aes(xvalues, yvalues+0.35, label=Origin_of_peptide), check_overlap = TRUE) + # label outliers




scale_colour_manual('%(counts_title)s', values = c('#444444', '%(x_color)s', '%(y_color)s'),
                    labels = c( "Similar" = countsim,  "%(x_series_name)s" = countX,        "%(y_series_name)s" = countY)) +'''

    if shape_by_category:
        legal_shapes_str = ', '.join(map(str, legal_shapes))
        main_plot_script += '''
scale_shape_manual('%(shape_category_title)s', values = c(%(legal_shapes_str)s),
                    labels = c( "Similar" = countsim,  "%(x_series_name)s" = countX,        "%(y_series_name)s" = countY))'''

    else:
        main_plot_script += '''
scale_shape_manual('%(counts_title)s', values = c(18, 16, 15),
                    labels = c( "Similar" = countsim,  "%(x_series_name)s" = countX,        "%(y_series_name)s" = countY))'''

    if add_similarity_range_annotation:
        main_plot_script += '''+
    # Add a caption
    annotation_custom(grob = textGrob(gp = gpar(fontsize = 5), hjust = 0, sprintf("* Similar \\u225d \\u00b1 %%0.2f", round(%(similarity_range)f, digits = 2))), xmin = maxx + (2 * maxx / 10), ymin = -1, ymax = -1)'''

    main_plot_script += '''

# Plot graph
p
    '''
    if add_similarity_range_annotation:
        main_plot_script += '''
# Code to override clipping
gt <- ggplot_gtable(ggplot_build(p))
gt$layout$clip[gt$layout$name=="panel"] <- "off"
grid.draw(gt)'''

    main_plot_script +='''
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
