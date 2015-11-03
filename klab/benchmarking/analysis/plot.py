import os
import traceback

import matplotlib.pyplot as plt
import numpy

from klab.fs.fsio import write_temp_file

def create_csv(analysis_table):
    contents = '\n'.join(['DatasetID,Experimental,Predicted'] + ['%s,%s,%s' % (str(l['DatasetID']), str(l['Experimental']), str(l['Predicted'])) for l in analysis_table])
    return write_temp_file('.', contents)


def plot(analysis_table, output_filename, RFunction, title = ''):
    filetype = os.path.splitext(output_filename)[1].lower()
    if not(filetype == '.png' or filetype == '.pdf' or filetype == '.eps'):
        filetype = 'png'
        output_filename += '.png'
    else:
        filetype = filetype[1:]
    if len(analysis_table) <= 1:
        raise Exception("The analysis table must have at least two points.")
    else:
        input_filename = create_csv(analysis_table)
        try:
            R_output = RFunction(input_filename, output_filename, filetype, title = title)
        except Exception, e:
            print(traceback.format_exc())
            os.remove(input_filename)
            raise Exception(e)
        os.remove(input_filename)
    return output_filename


def plot_pandas(dataframe, x_series, y_series, output_filename, RFunction, title = ''):
    new_dataframe = dataframe[[x_series, y_series]]
    new_dataframe.columns = ['Experimental', 'Predicted']
    new_dataframe = new_dataframe.dropna(subset = ['Experimental', 'Predicted']) # todo: using 'Experimental' and 'Predicted' is hacky - make the inner function more general

    csv_filename = os.path.splitext(output_filename)[0] + '.txt'
    filetype = os.path.splitext(output_filename)[1].lower()
    if not(filetype == '.png' or filetype == '.pdf' or filetype == '.eps'):
        filetype = 'png'
        output_filename += '.png'
    else:
        filetype = filetype[1:]
    if len(new_dataframe) <= 1:
        raise Exception("The analysis table must have at least two points.")
    else:
        new_dataframe.to_csv(csv_filename, sep = ',', header = True)
        try:
            R_output = RFunction(csv_filename, output_filename, filetype, title = title)
        except Exception, e:
            print(traceback.format_exc())
            raise Exception(e)
    return output_filename


def histogram(values, out_filepath, num_bins = 50):
    hist, bins = numpy.histogram(values, bins=num_bins)
    width = 0.7 * (bins[1] - bins[0])
    center = (bins[:-1] + bins[1:]) / 2
    plt.bar(center, hist, align='center', width=width)
    fig, ax = plt.subplots()
    ax.bar(center, hist, align='center', width=width)
    fig.savefig(out_filepath)
