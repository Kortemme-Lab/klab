#!/usr/bin/env python2

# The MIT License (MIT)
#
# Copyright (c) 2016 Samuel Thompson
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
'''

Analysis module for the site saturation mutagenesis data.
This module was initially by Samuel Thompson but added to the repository and edited by Shane O'Connor.
'''

import sys
import os

from scipy import stats
import numpy as np

from klab import colortext
from klab.fs.fsio import get_file_lines


# Used to rename fields to match the conventions used in misc.py
field_name_mapper = (
    ('R_value', 'pearsonr'),
    ('slope', 'pearsonr_slope'),
    ('R_value_through_origin', 'pearsonr_origin'),
    ('slope_through_origin', 'pearsonr_slope_origin'),
    ('STDev_cutoff', 'std_dev_cutoff'),
    ('warnings', 'warnings'),
    ('MAE', 'MAE'),
    ('scaled_MAE', 'scaled_MAE'),
    ('accuracy', 'accuracy'),
    ('specificity', 'specificity'),
    ('sensitivity', 'sensitivity'),
    ('significance_specificity', 'significance_specificity'),
    ('significance_sensitivity', 'significance_sensitivity'),
    ('significant_beneficient_sensitivity', 'significant_beneficient_sensitivity'),
    ('significant_beneficient_specificity', 'significant_beneficient_specificity'),
)


####################
# Utility functions
####################


def least_squares_fixed_origin(x, y):
    x_linalg = x[:, np.newaxis]
    linalg_slope, linalg_residual = np.linalg.lstsq(x_linalg, y)[:2]
    slope = linalg_slope[0]
    r_squared = 1 - linalg_residual[0] / sum((y - y.mean()) ** 2)
    if r_squared >= 0.0:
        r_value = np.sqrt(r_squared)
    elif r_squared < 0.0:  # This can happen when the correlation is uncorrelated.
        r_value = -np.sqrt(-r_squared)

    return slope, r_value


def get_std_dev(values):
    temp_pos = []
    temp_neg = []

    for value in values:

        if value == 0.0:
            continue

        if value > 0.0:
            temp_pos.append(value)
            temp_pos.append(-value)  # make it a symmetrical distribution
        elif value < 0.0:
            temp_neg.append(value)
            temp_neg.append(-value)  # make it a symmetrical distribution

        # Calculate standard deviations for sigma-based significance cutoffs
        pos_stdeviation = np.std(temp_pos)
        neg_stdeviation = -np.std(temp_neg)

    return pos_stdeviation, neg_stdeviation


def determine_correct_sign(prediction_data, experimental_data, expect_negative_correlation = False, STDev_cutoff = 1.0):
    """

    :param prediction_data:
    :param experimental_data:
    :param expect_negative_correlation: Indicates wheter or not the predictions have the same or opposite sign as the experimental data.
    :param STDev_cutoff: Number of standard deviations as a threshold for significance cut-off. Used for both predictions and experiments.

    :return:
    """
    if len(experimental_data['list']) != len(prediction_data['list']):
        print str("Error: number of experimental values (%d) and prediction values () do not match. Cannot continue.") % (len(experimental_data['list']), len(prediction_data['list']))
        exit()

    classifications = {}

    classifications['prediction-below_threshold_and_experimental-above_threshold'] = [0, 0]
    classifications['prediction-below_threshold_and_experimental-positive'] = [1, 0]
    classifications['prediction-below_threshold_and_experimental-zero'] = [2, 0]
    classifications['prediction-below_threshold_and_experimental-negative'] = [3, 0]
    classifications['prediction-below_threshold_and_experimental-below_threshold'] = [4, 0]

    classifications['prediction-negative_and_experimental-above_threshold'] = [0, 1]
    classifications['prediction-negative_and_experimental-positive'] = [1, 1]
    classifications['prediction-negative_and_experimental-zero'] = [2, 1]
    classifications['prediction-negative_and_experimental-negative'] = [3, 1]
    classifications['prediction-negative_and_experimental-below_threshold'] = [4, 1]

    classifications['prediction-zero_and_experimental-above_threshold'] = [0, 2]
    classifications['prediction-zero_and_experimental-positive'] = [1, 2]
    classifications['prediction-zero_and_experimental-zero'] = [2, 2]
    classifications['prediction-zero_and_experimental-negative'] = [3, 2]
    classifications['prediction-zero_and_experimental-below_threshold'] = [4, 2]

    classifications['prediction-positive_and_experimental-above_threshold'] = [0, 3]
    classifications['prediction-positive_and_experimental-positive'] = [1, 3]
    classifications['prediction-positive_and_experimental-zero'] = [2, 3]
    classifications['prediction-positive_and_experimental-negative'] = [3, 3]
    classifications['prediction-positive_and_experimental-below_threshold'] = [4, 3]

    classifications['prediction-above_threshold_and_experimental-above_threshold'] = [0, 4]
    classifications['prediction-above_threshold_and_experimental-positive'] = [1, 4]
    classifications['prediction-above_threshold_and_experimental-zero'] = [2, 4]
    classifications['prediction-above_threshold_and_experimental-negative'] = [3, 4]
    classifications['prediction-above_threshold_and_experimental-below_threshold'] = [4, 4]

    classification_matrix = np.zeros((5, 5))

    for num in range(len(experimental_data['list'])):

        if prediction_data['list'][num] > prediction_data['positive significance threshold'] * STDev_cutoff:
            prediction_category = "prediction-above_threshold"
        elif prediction_data['list'][num] > 0.0 and not (
            prediction_data['list'][num] > prediction_data['positive significance threshold'] * STDev_cutoff):
            prediction_category = "prediction-positive"
        elif prediction_data['list'][num] < prediction_data['negative significance threshold'] * STDev_cutoff:
            prediction_category = "prediction-below_threshold"
        elif prediction_data['list'][num] < 0.0 and not (
            prediction_data['list'][num] < prediction_data['negative significance threshold'] * STDev_cutoff):
            prediction_category = "prediction-negative"
        else:
            prediction_category = "prediction-zero"

        if experimental_data['list'][num] > experimental_data['positive significance threshold'] * STDev_cutoff:
            experimental_category = "experimental-above_threshold"
        elif experimental_data['list'][num] > 0.0 and not (
            experimental_data['list'][num] > experimental_data['positive significance threshold'] * STDev_cutoff):
            experimental_category = "experimental-positive"
        elif experimental_data['list'][num] < experimental_data['negative significance threshold'] * STDev_cutoff:
            experimental_category = "experimental-below_threshold"
        elif experimental_data['list'][num] < 0.0 and not (
            experimental_data['list'][num] < experimental_data['negative significance threshold'] * STDev_cutoff):
            experimental_category = "experimental-negative"
        else:
            experimental_category = "experimental-zero"

        classification_category = prediction_category + "_and_" + experimental_category

        column, row = classifications[classification_category]
        classification_matrix[column][row] = 1 + classification_matrix[column][row]


    # Calculate classifications
    mat = classification_matrix

    total = np.sum(classification_matrix)

    if not expect_negative_correlation:
        true_positive = mat[4][0] + mat[4][1] + mat[3][0] + mat[3][1]
        true_negative = mat[0][4] + mat[0][3] + mat[1][3] + mat[1][4]
        predicted_significant_correct_sign = mat[0][4] + mat[1][4] + mat[4][0] + mat[3][0]  # Specificity
        experimental_significant_correct_sign = mat[0][4] + mat[0][3] + mat[4][0] + mat[4][1]  # Sensitivity
        predicted_significant_are_experimentally_significant = mat[0][4] + mat[4][0]  # Specific accuracy and

        # Added during CADRES 2016
        significant_beneficient_sensitivity_n = int(mat[4][0] + mat[4][1] + mat[4][2] + mat[4][3] + mat[4][4])
        significant_beneficient_sensitivity = float(mat[4][0]) / float(significant_beneficient_sensitivity_n)
        significant_beneficient_specificity_n = int(mat[0][0] + mat[1][0] + mat[2][0] + mat[3][0] + mat[4][0])
        significant_beneficient_specificity = float(mat[4][0]) / float(significant_beneficient_specificity_n)

    elif expect_negative_correlation:
        true_positive = mat[0][0] + mat[0][1] + mat[1][0] + mat[1][1]
        true_negative = mat[3][3] + mat[3][4] + mat[4][3] + mat[4][4]
        predicted_significant_correct_sign = mat[4][4] + mat[3][4] + mat[0][0] + mat[1][0]  # Specificity
        experimental_significant_correct_sign = mat[4][4] + mat[4][3] + mat[0][0] + mat[0][1]  # Sensitivity
        predicted_significant_are_experimentally_significant = mat[4][4] + mat[0][0]  # Specific accuracy

        # Added during CADRES 2016
        significant_beneficient_sensitivity_n = int(mat[0][0] + mat[0][1] + mat[0][2] + mat[0][3] + mat[0][4])
        significant_beneficient_sensitivity = float(mat[0][0]) / float(significant_beneficient_sensitivity_n)
        significant_beneficient_specificity_n = int(mat[0][0] + mat[1][0] + mat[2][0] + mat[3][0] + mat[4][0])
        significant_beneficient_specificity = float(mat[0][0]) / float(significant_beneficient_specificity_n)

    correct_sign = true_positive + true_negative  # Accuracy
    accuracy = float(correct_sign) / total

    total_significant_predictions = mat[0][4] + mat[1][4] + mat[2][4] + mat[3][4] + mat[4][4] + mat[4][0] + mat[3][0] + mat[2][0] + mat[1][0] + mat[0][0]
    specificity = float(predicted_significant_correct_sign) / total_significant_predictions

    total_significant_experimental_hits = mat[4][4] + mat[4][3] + mat[4][2] + mat[4][1] + mat[4][0] + mat[0][0] + mat[0][1] + mat[0][2] + mat[0][3] + mat[0][4]
    sensitivity = float(experimental_significant_correct_sign) / total_significant_experimental_hits

    significance_specificity = float(predicted_significant_are_experimentally_significant) / total_significant_predictions
    significance_sensitivity = float(predicted_significant_are_experimentally_significant) / total_significant_experimental_hits

    return accuracy, specificity, sensitivity, significance_specificity, significance_sensitivity, significant_beneficient_sensitivity, significant_beneficient_specificity, significant_beneficient_sensitivity_n, significant_beneficient_specificity_n


def calculate_mae(prediction_data, experimental_data):
    warning = ""

    mae = np.mean(np.abs(np.array(prediction_data['array']) - np.array(experimental_data['array'])))
    scaled_prediction = prediction_data['array'] * np.abs(prediction_data['slope_through_origin'])
    scaled_mae = np.mean(np.abs(np.array(scaled_prediction) - np.array(experimental_data['array'])))

    if prediction_data['slope_through_origin'] < 0.0:
        print "Warning: Data is anti-correlated for regression through the origin.\nMean absolute error is not an effective metric for anti-correlated data."
        warning = "MAE is not applicable for anti-correlated data."
    return mae, scaled_mae, warning


####################
# Main functionality
####################


def parse_csv(csv_lines, expect_negative_correlation = False, STDev_cutoff = 1.0, headers_start_with = 'ID', comments_start_with = None, separator = ','):
    """
    Analyzes lines in CSV format.

    Expects the first line to be a header line starting with headers_start_with e.g. "ID,experimental value, prediction 1 value, prediction 2 value,"
    Record IDs are expected in the first column.
    Experimental values are expected in the second column.
    Predicted values are expected in the subsequent columns.

    :param csv_lines: Lines read from a CSV file containing experimental and predicted data for some dataset.
    :param expect_negative_correlation: Indicates wheter or not the predictions have the same or opposite sign as the experimental data.
    :param STDev_cutoff: Number of standard deviations as a threshold for significance cut-off. Used for both predictions and experiments.
    :param headers_start_with: A string used to distinguish the header line.
    :param comments_start_with: A string used to distinguish lines containing comments to be ignored.
    :param separator: Column separator. For CSV files, ',' should be used. For TSV files, '\t' should be used.
    """
    data = {}
    data['experimental'] = {}
    data['experimental']['list'] = []
    data['experimental']['dict'] = {}
    data['predictions'] = {}

    if comments_start_with != None:
        lines = [l for l in csv_lines if l.strip() and not(l.strip().startswith(comments_start_with))]
    else:
        lines = [l for l in csv_lines if l.strip()]

    print(lines[0], '&')

    headers = lines[0]
    assert(headers.startswith(headers_start_with))
    headers = headers.split(separator)
    num_fields = len(headers)
    prediction_names = headers[2:]

    skipped_cases = []
    for line in lines[1:]:

        fields = [t.strip() for t in line.split(separator)]
        assert(len(fields) == num_fields)

        mut_name = fields[0]
        expt_value = fields[1]

        # The script as is requires values for all records. We skip any which are missing some data.
        predicted_values = [t.strip() for t in fields[2:] if t.strip()]
        if(len(predicted_values) != len(fields) - 2):
            skipped_cases.append(fields[0])
            continue

        data['experimental']['dict'][mut_name] = float(expt_value)
        data['experimental']['list'].append(float(expt_value))
        predictions = fields[2:]
        counter = 0
        for value in predictions:
            counter += 1
            prediction_id = counter
            prediction_name = prediction_names[counter - 1]

            data['predictions'][prediction_id] = data['predictions'].get(prediction_id, dict(name = prediction_name, id = prediction_id))
            prediction_cases = data['predictions'][prediction_id]

            prediction_cases['list'] = prediction_cases.get('list', [])
            prediction_cases['dict'] = prediction_cases.get('dict', {})

            prediction_cases['dict']['mut_name'] = float(value)
            prediction_cases['list'].append(float(value))

    data['skipped_cases'] = skipped_cases
    for prediction_id, prediction_cases in data['predictions'].iteritems():
        prediction_cases['array'] = np.array(prediction_cases['list'])
        pos_STDev, neg_STDev = get_std_dev(prediction_cases['array'])
        prediction_cases['positive significance threshold'] = pos_STDev
        prediction_cases['negative significance threshold'] = neg_STDev

    data['experimental']['array'] = np.array(data['experimental']['list'])
    pos_STDev, neg_STDev = get_std_dev(data['experimental']['array'])
    data['experimental']['positive significance threshold'] = pos_STDev
    data['experimental']['negative significance threshold'] = neg_STDev

    for prediction_id, prediction_cases in sorted(data['predictions'].iteritems()):
        slope_through_origin, r_value_through_origin = least_squares_fixed_origin(prediction_cases['array'], data['experimental']['array'])
        slope, intercept, r_value, p_value, std_err = stats.linregress(prediction_cases['array'], data['experimental']['array'])

        prediction_cases.update(dict(
            prediction_id = prediction_id,
            slope_through_origin = slope_through_origin,
            R_value_through_origin = r_value_through_origin,
            slope = slope,
            R_value = r_value,
        ))

        warnings = []
        mae, scaled_mae, warning = calculate_mae(prediction_cases, data['experimental'])
        accuracy, specificity, sensitivity, significance_specificity, significance_sensitivity, significant_beneficient_sensitivity, significant_beneficient_specificity, significant_beneficient_sensitivity_n, significant_beneficient_specificity_n = determine_correct_sign(prediction_cases, data['experimental'], expect_negative_correlation, STDev_cutoff)
        if warning:
            warnings = [warning]

        prediction_cases.update(dict(
            STDev_cutoff = STDev_cutoff,
            warnings = warnings,
            MAE = mae,
            scaled_MAE = scaled_mae,
            accuracy = accuracy,
            specificity = specificity,
            sensitivity = sensitivity,
            significance_specificity = significance_specificity,
            significance_sensitivity = significance_sensitivity,
            significant_beneficient_sensitivity = (significant_beneficient_sensitivity, significant_beneficient_sensitivity_n),
            significant_beneficient_specificity = (significant_beneficient_specificity, significant_beneficient_specificity_n),
        ))
    return data


#######################
# Derived functionality
#######################


def parse_csv_file(csv_filepath, expect_negative_correlation = False, STDev_cutoff = 1.0, headers_start_with = 'ID', comments_start_with = None, separator = ','):
    """
    Analyzes a CSV file.
    Expects a CSV file with a header line starting with headers_start_with e.g. "ID,experimental value, prediction 1 value, prediction 2 value,"
    Record IDs are expected in the first column.
    Experimental values are expected in the second column.
    Predicted values are expected in the subsequent columns.

    :param csv_filepath: The path to a CSV file containing experimental and predicted data for some dataset.
    :param expect_negative_correlation: See parse_csv.
    :param STDev_cutoff: See parse_csv.
    :param headers_start_with: See parse_csv.
    :param comments_start_with: See parse_csv.
    :param separator: See parse_csv.
    """
    assert (os.path.exists(csv_filepath))
    return parse_csv(get_file_lines(csv_filepath),
                     expect_negative_correlation = expect_negative_correlation, STDev_cutoff = STDev_cutoff, headers_start_with = headers_start_with,
                     comments_start_with = comments_start_with, separator = separator)


def get_std_xy_dataset_statistics(x_values, y_values, expect_negative_correlation = False, STDev_cutoff = 1.0):
    '''Calls parse_csv and returns the analysis in a format similar to get_xy_dataset_statistics in klab.stats.misc.'''
    assert(len(x_values) == len(y_values))
    csv_lines = ['ID,X,Y'] + [','.join(map(str, [c + 1, x_values[c], y_values[c]])) for c in xrange(len(x_values))]
    data = parse_csv(csv_lines, expect_negative_correlation = expect_negative_correlation, STDev_cutoff = STDev_cutoff)

    assert(len(data['predictions']) == 1)
    assert(1 in data['predictions'])
    assert(data['predictions'][1]['name'] == 'Y')
    summary_data = data['predictions'][1]

    stats = {}
    for spair in field_name_mapper:
        stats[spair[1]] = summary_data[spair[0]]
    if stats['warnings']:
        stats['warnings'] = '\n'.join(stats['warnings'])
    else:
        stats['warnings'] = None
    return stats


def analyze_dataframe(df, id_field_column, reference_field_column, prediction_field_columns = [],
                          expect_negative_correlation = False, STDev_cutoff = 1.0):
    """Takes a dataframe, converts it to a CSV, and runs parse_csv.
       Typically, we would work the other way around, converting a CSV to dataframe. However, this was quicker to implement with the existing code.

       :param df: A pandas dataframe.
       :param id_field_column: The column index (zero-indexed) whose corresponding column contains the ID (record/case ID) field. Values in this field must be integer values.
       :param reference_field_column: The column index (zero-indexed) whose corresponding column contains the reference data (X-axis) e.g. experimental measurements or reference data. Values in this field are assumed to be integers or floating-point values. Otherwise, they will be imported as NaN.
       :param prediction_field_columns: The column indices (zero-indexed) whose corresponding columns contains the prediction data (Y-axis). If this parameter is unspecified, all columns excepting the ID and reference columns are treated as predictions.
       :param expect_negative_correlation: See parse_csv.
       :param STDev_cutoff: See parse_csv.
       :return:
    """
    raise Exception('Implement this using parse_csv.')


####################
# Reporters
####################


def print_summary(data):

    if data['skipped_cases']:
        colortext.warning('\nSkipped {0} cases due to partial data: {1}.\n'.format(len(data['skipped_cases']),
                                                                                   ', '.join(data['skipped_cases'])))
    for prediction_id, prediction_cases in sorted(data['predictions'].iteritems()):

        print('''
Prediction: #{id}
Prediction name: {name}
\tR-value: {R_value:.03f}\t\tSlope: {slope:.03f}
\tR-value with origin as intercept: {R_value_through_origin:.03f}\t\tSlope: {slope_through_origin:.03f}
\tMAE: {MAE:.03f}\t\t Scaled MAE: {scaled_MAE:.03f}

\n\tClassifications:\n\t\t-- Cut-off for significance at {STDev_cutoff:f} STDevs --
\tPercent correct sign (accuracy): {accuracy:.03f}
\tPercent significant predictions with correct sign (specificity): {specificity:.03f}
\tPercent significant experimental hits with correct prediction sign (sensitivity): {sensitivity:.03f}
\tPercent significant predictions are significant experimental hits (significance specificity): {significance_specificity:.03f}
\tPercent significant experimental hits are predicted significant hits (significance sensitivity): {significance_sensitivity:.03f}
\n\n'''.format(**prediction_cases))


######################
# Command-line handler
######################


if __name__ == '__main__':
    datafilename = sys.argv[1]
    print str("\n\n--Analysis of predictions in %s--") % datafilename
    parse_csv_file(datafilename, expect_negative_correlation, STDev_cutoff = 1.0, headers_start_with = 'ID')

