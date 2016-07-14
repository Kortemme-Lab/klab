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
This module was initially by Samuel Thompson but added to the repository by Shane O'Connor.
'''

import sys
import os

from scipy import stats
import numpy as np

from klab import colortext
from klab.fs.fsio import get_file_lines


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

    elif expect_negative_correlation:
        true_positive = mat[0][0] + mat[0][1] + mat[1][0] + mat[1][1]
        true_negative = mat[3][3] + mat[3][4] + mat[4][3] + mat[4][4]
        predicted_significant_correct_sign = mat[4][4] + mat[3][4] + mat[0][0] + mat[1][0]  # Specificity
        experimental_significant_correct_sign = mat[4][4] + mat[4][3] + mat[0][0] + mat[0][1]  # Sensitivity
        predicted_significant_are_experimentally_significant = mat[4][4] + mat[0][0]  # Specific accuracy

    correct_sign = true_positive + true_negative  # Accuracy
    accuracy = float(correct_sign) / total

    total_significant_predictions = mat[0][4] + mat[1][4] + mat[2][4] + mat[3][4] + mat[4][4] + mat[4][0] + mat[3][0] + \
                                    mat[2][0] + mat[1][0] + mat[0][0]
    specificity = float(predicted_significant_correct_sign) / total_significant_predictions

    total_significant_experimental_hits = mat[4][4] + mat[4][3] + mat[4][2] + mat[4][1] + mat[4][0] + mat[0][0] + \
                                          mat[0][1] + mat[0][2] + mat[0][3] + mat[0][4]
    sensitivity = float(experimental_significant_correct_sign) / total_significant_experimental_hits

    significance_specificity = float(predicted_significant_are_experimentally_significant) / total_significant_predictions
    significance_sensitivity = float(predicted_significant_are_experimentally_significant) / total_significant_experimental_hits

    return accuracy, specificity, sensitivity, significance_specificity, significance_sensitivity


def calculate_mae(prediction_data, experimental_data):
    warning = ""

    mae = np.mean(np.abs(np.array(prediction_data['array']) - np.array(experimental_data['array'])))
    scaled_prediction = prediction_data['array'] * np.abs(prediction_data['slope through origin'])
    scaled_mae = np.mean(np.abs(np.array(scaled_prediction) - np.array(experimental_data['array'])))

    if prediction_data['slope through origin'] < 0.0:
        print "Warning: Data is anti-correlated for regression through the origin.\nMean absolute error is not an effective metric for anti-correlated data."
        warning = "MAE is not applicable for anti-correlated data."
    return mae, scaled_mae, warning


def parse_csv(csv_filepath, expect_negative_correlation = False, STDev_cutoff = 1.0, headers_start_with = 'ID'):
    """
    Expects a CSV file with a header line starting with headers_start_with e.g. "ID,experimental value, prediction 1 value, prediction 2 value,"
    Record IDs are expected in the first column.
    Experimental values are expected in the second column.
    Predicted values are expected in the subsequent columns.

    :param csv_filepath: The path to a CSV file containing experimental and predicted data for some dataset.
    :param expect_negative_correlation: Indicates wheter or not the predictions have the same or opposite sign as the experimental data.
    :param STDev_cutoff: Number of standard deviations as a threshold for significance cut-off. Used for both predictions and experiments.
    :param headers_start_with: A string used to distinguish the header line.

    """
    data = {}
    data['experimental'] = {}
    data['experimental']['list'] = []
    data['experimental']['dict'] = {}
    data['predictions'] = {}

    assert(os.path.exists(csv_filepath))
    lines = get_file_lines(csv_filepath)

    skipped_cases = []
    for line in lines:
        if line[:2] == "ID":
            continue  # Skip the header if it is present

        fields = line.split(',')

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
            prediction_name = str(counter)

            try:
                test = data['predictions'][prediction_name]
            except KeyError:
                data['predictions'][prediction_name] = {}

            try:
                test = data['predictions'][prediction_name]['list']
            except KeyError:
                data['predictions'][prediction_name]['list'] = []
                data['predictions'][prediction_name]['dict'] = {}

            data['predictions'][prediction_name]['dict']['mut_name'] = float(value)
            data['predictions'][prediction_name]['list'].append(float(value))

    for prediction_name in data['predictions'].keys():
        data['predictions'][prediction_name]['array'] = np.array(data['predictions'][prediction_name]['list'])
        pos_STDev, neg_STDev = get_std_dev(data['predictions'][prediction_name]['array'])
        data['predictions'][prediction_name]['positive significance threshold'] = pos_STDev
        data['predictions'][prediction_name]['negative significance threshold'] = neg_STDev

    data['experimental']['array'] = np.array(data['experimental']['list'])
    pos_STDev, neg_STDev = get_std_dev(data['experimental']['array'])
    data['experimental']['positive significance threshold'] = pos_STDev
    data['experimental']['negative significance threshold'] = neg_STDev

    for prediction_name in data['predictions'].keys():
        slope_through_origin, r_value_through_origin = least_squares_fixed_origin(
                data['predictions'][prediction_name]['array'], data['experimental']['array'])
        slope, intercept, r_value, p_value, std_err = stats.linregress(data['predictions'][prediction_name]['array'],
                                                                       data['experimental']['array'])
        data['predictions'][prediction_name]['warnings'] = []
        data['predictions'][prediction_name]['slope through origin'] = slope_through_origin
        data['predictions'][prediction_name]['R-value through origin'] = r_value_through_origin
        data['predictions'][prediction_name]['slope'] = slope
        data['predictions'][prediction_name]['R value'] = r_value
        mae, scaled_mae, warning = calculate_mae(data['predictions'][prediction_name], data['experimental'])
        data['predictions'][prediction_name]['MAE'] = mae
        data['predictions'][prediction_name]['scaled MAE'] = scaled_mae
        data['predictions'][prediction_name]['warnings'].append(warning)
        accuracy, specificity, sensitivity, significance_specificity, significance_sensitivity = determine_correct_sign(
                data['predictions'][prediction_name], data['experimental'], expect_negative_correlation, STDev_cutoff)
        data['predictions'][prediction_name]['accuracy'] = accuracy
        data['predictions'][prediction_name]['specificity'] = specificity
        data['predictions'][prediction_name]['sensitivity'] = sensitivity
        data['predictions'][prediction_name]['significance specificity'] = significance_specificity
        data['predictions'][prediction_name]['significance sensitivity'] = significance_sensitivity

        if skipped_cases:
            colortext.warning('\nSkipped {0} cases due to partial data: {1}.\n'.format(len(skipped_cases), ', '.join(skipped_cases)))
        print str("Prediction number: %s") % prediction_name
        print str("\tR-value: %03f\t\tSlope: %03f") % (r_value, slope)
        print str("\tR-value with origin as intercept: %03f\t\tSlope: %03f") % (r_value_through_origin, slope_through_origin)
        print str("\tMAE: %03f\t\t Scaled MAE: %03f") % (mae, scaled_mae)

        print str("\n\tClassifications:\n\t\t-- Cut-off for significance at %f STDevs -- ") % STDev_cutoff
        print str("\tPercent correct sign (accuracy): %03f") % accuracy
        print str("\tPercent significant predictions with correct sign (specificity): %03f") % specificity
        print str("\tPercent significant experimental hits with correct prediction sign (sensitivity): %03f") % sensitivity
        print str("\tPercent significant predictions are significant experimental hits (significance specificity): %03f") % significance_specificity
        print str("\tPercent significant experimental hits are predicted significant hits (significance sensitivity): %03f") % significance_sensitivity
        print str("\n\n")


if __name__ == '__main__':
    datafilename = sys.argv[1]
    print str("\n\n--Analysis of predictions in %s--") % datafilename
    parse_csv(datafilename, expect_negative_correlation, STDev_cutoff = 1.0, headers_start_with = 'ID')

