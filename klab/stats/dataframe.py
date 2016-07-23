#!/usr/bin/env python2
# encoding: utf-8

# This file is taken from the klab repository. Please see that repository for any updates.
#   https://github.com/Kortemme-Lab/klab/

# The MIT License (MIT)
#
# Copyright (c) 2016 Shane O'Connor
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
"""
dataframe.py
A wrapper class for pandas dataframes using the miscellaneous statistical functions from misc.py to run generic analyses.

Created by Shane O'Connor 2016
"""

import copy
import pprint

import pandas

from klab import colortext
from klab.stats.misc import get_xy_dataset_statistics_pandas, format_stats


class DatasetDataFrame(object):
    '''A class to store benchmark data where once series contains the reference or experimental values and the remaining
       columns contain predicted results from benchmark runs.'''


    # Default name for the set of data for analysis
    reference_dataset_name = 'Benchmark dataset'


    def iprint(msg):  # Note: no args, kwargs
        print(str(msg))


    def __init__(self, dataframe,
                 reference_column_index = 0, restricted_predicted_column_indices = [], restricted_predicted_column_names = [],
                 reference_dataset_name = None, index_layers = [],
                 log_level = 10, log_fn = iprint):
        '''Expects a dataframe where:
            the indices correspond to some set of IDs e.g. dataset case IDs;
            there is one reference column/series against which all other series will be pairwise compared.

        For example, the reference column may contain experimental data and the remaining columns may contain predicted data
        from multiple benchmarking runs.

        The class handles multi-indexed data e.g. data grouped by 'Team' and then 'Method'. In that case, the index_layers
        list can be specified to name these layers. In the example above, we would use index_layers = ['Team', 'Method'].

        :param reference_column: The index of the column which contains the reference data series. Indices are zero-indexed.
        :param restricted_predicted_column_indices: Indices of columns which should be considered for analysis.
        :param restricted_predicted_column_indices: Names of columns which should be considered for analysis.
        :param log_level: All log messages with levels set below log_level will be printed.
        :param log_fn: The logging function. This expects exactly one argument which is then passed to the print statement.

        By default, all non-reference columns are analyzed. If either restricted_predicted_column_indices or restricted_predicted_column_names
        is set then the set of columns is restricted to the *union* of those two lists.

        '''

        # Setup
        reference_dataset_name = reference_dataset_name or DatasetDataFrame.reference_dataset_name
        all_series_names = dataframe.columns.values
        num_series = len(all_series_names)
        assert(num_series == len(set(all_series_names)))

        if restricted_predicted_column_names != []:
            assert(isinstance(restricted_predicted_column_names, list))
            for n in restricted_predicted_column_names:
                # Allow either string indexing (typical) or tuple indexing (for multi-indexed columns)
                if isinstance(n, tuple):
                    # Multi-indexing case
                    try:
                        t = dataframe[n]
                    except:
                        raise Exception('Could not find multi-indexed column {0}.'.format(n))
                else:
                    assert(isinstance(n, basestring))
                    assert(n in dataframe.columns.values)

        if restricted_predicted_column_indices != []:
            assert (isinstance(restricted_predicted_column_indices, list))
            for n in restricted_predicted_column_indices:
                assert(isinstance(n, int))
                assert(0 <= n < num_series)

        # Dataframe variables
        # If a multi-indexed dataframe is passed then the column names will be tuples rather than simple types and self.multi_indexed will be set
        self.log_level = log_level
        self.log_fn = log_fn
        self.df = dataframe

        # Handle single- and multi-indexed dataframes
        self.multi_indexed = False
        self.index_layers = index_layers
        if len(dataframe.columns) > 0 and len(dataframe.columns.values[0]) > 1:
            self.multi_indexed = True
            if self.index_layers:
                assert(len(self.index_layers) == len(dataframe.columns.values[0]))
                self.index_layers = tuple(map(str, self.index_layers))
            else:
                self.index_layers = tuple(['Group {0}'.format(n + 1) for n in range(len(dataframe.columns.values[0]))])
        else:
            if self.index_layers:
                assert(len(self.index_layers) == 1)
            else:
                self.index_layers = ['Group']
            self.index_layers = tuple(self.index_layers)

        self.series_index = {}
        self.series_names = dict(zip(range(num_series), list(dataframe.columns.values)))
        self.reference_dataset_name = reference_dataset_name
        for k, v in self.series_names.iteritems():
            self.series_index[v] = k
        assert(len(self.series_index) == len(self.series_names))

        # Set up series
        # self.reference_series is the name of the reference series' column
        # self.data_series is the list of names of the prediction series' columns
        if not (0 <= reference_column_index < num_series):
            raise Exception('Reference column index {0} is out of bounds (bounds are 0,..,{1}).'.format(reference_column_index, num_series - 1))
        elif reference_column_index in restricted_predicted_column_indices:
            raise Exception('The reference column index {0} was specified as a prediction series in the restricted_predicted_column_indices list ({1}).'.format(reference_column_index, ', '.join(map(str, restricted_predicted_column_indices))))
        elif self.series_names[reference_column_index] in restricted_predicted_column_names:
            raise Exception('The reference column {0} was specified as a prediction series in the restricted_predicted_column_names list ({1}).'.format(self.series_names[reference_column_index], ', '.join(restricted_predicted_column_names)))
        self.reference_series = self.series_names[reference_column_index]
        self.data_series = self.get_series_names(column_indices = restricted_predicted_column_indices, column_names = restricted_predicted_column_names)
        self.analysis = {}

        # Keep a reference to the full dataframe
        self.df_full = dataframe

        # During analysis, we consider the subset of cases where all series have data so we use dropna to filter out the
        # cases with missing data. To prevent filtering out too many cases, we first restrict the dataset to the series
        # of interest
        self.df = dataframe.copy()
        dropped_series = [n for n in all_series_names if n not in [self.reference_series] + self.data_series]
        self.df.drop(dropped_series, axis = 1, inplace = True)

        # Add a series with the absolute errors
        for dseries in self.data_series:
            # It may be cleaner to create new dataframes for the absolute error values but we are already creating a new dataframe for the pruned data
            # todo: do we ever use these columns? not for reporting although it could be useful when dumping to text to create them at that point
            if self.multi_indexed:
                new_series = list(dseries)
                new_series[-1] = new_series[-1] + '_abs_error'
                new_series = tuple(new_series)
                assert(new_series not in dataframe.columns.values)
                self.df[new_series] = abs(self.df[self.reference_series] - self.df[dseries])
            else:
                assert(dseries + '_abs_error' not in dataframe.columns.values)
                self.df[dseries + '_abs_error'] = abs(self.df[self.reference_series] - self.df[dseries])

        # Now that we have pruned by column, we drop records with missing data
        self.df_pruned = self.df.dropna()
        num_pruned_cases = len(self.df) - len(self.df_pruned)
        if num_pruned_cases:
            self.log('{0} cases do not have data for all series. Datasets pruned to the set of common records will be asterisked in the tabular results.'.format(num_pruned_cases), 3)


    @staticmethod
    def from_csv(id_field_column = 0, reference_field_column = 1, reference_dataset_name = None,
                 id_col_name = None, reference_col_name = None, comparison_col_name_prefix = 'Predicted',
                 columns_to_omit = [], columns_to_ignore = [],
                 headers_included = True, separator = ',', ignore_lines_starting_with = None,
                 log_level = 10, log_fn = iprint,
                 ):
        """

        :param id_field_column: The column index (zero-indexed) whose corresponding column contains the ID (record/case ID) field. Values in this field must be integer values.
        :param reference_field_column: The column index (zero-indexed) whose corresponding column contains the reference data (X-axis) e.g. experimental measurements or reference data. Values in this field are assumed to be integers or floating-point values. Otherwise, they will be imported as NaN.
        :param reference_dataset_name: The name of the dataset being analyzed.
        :param id_col_name: The name of the ID column. This will override any name in the header. If the header does not exist, this defaults to "ID".
        :param reference_col_name: The name of the ID column. This will override any name in the header. If the header does not exist, this defaults to "Experimental".
        :param comparison_col_name_prefix: Any remaining unnamed columns will be named (comparison_col_name_prefix + '_' + i) with integer i increasing.
        :param columns_to_omit: These columns will be omitted from the dataframe.
        :param columns_to_ignore: These columns will be included in the dataframe but not considered in analysis.
        :param headers_included: Whether the CSV file has a header line. If this line exists, it must be the first parsable (non-blank and which does not start with the value of ignore_lines_starting_with) line in the file.
        :param separator: Column separator. For CSV imports, ',' should be used. For TSV imports, '\t' should be used.
        :param ignore_lines_starting_with. Any lines starting with this string will be ignored during parsing. This allows you to include comments in the CSV file.
        :param log_level: See DatasetDataFrame constructor.
        :param log_fn: See DatasetDataFrame constructor.

        Note: Unlike the DatasetDataFrame constructor, this function does not currently handle multi-indexed tables.
        """
        raise Exception('todo: Implement this.')

        # ignore all columns_to_ignore

        # if headers_included, set id_col_name, reference_col_name, etc.
        # if not id_col_name: id_col_name = 'RecordID'
        # if not reference_col_name: reference_col_name = 'Experimental'
        # if not comparison_col_name_prefix: comparison_col_name_prefix = 'Predicted'

        # assert num columns >= 2
        # Set up these variables
        dataframe = None
        # dataset IDs should be used for the index
        # reference_column_index should be the first column
        # remaining columns should contain prediction data

        return DatasetDataFrame(
            dataframe,
            reference_dataset_name = reference_dataset_name,
            log_level = log_level,
            log_fn = log_fn)


    def log(self, msg, lvl = 0):
        '''Log messages according to the logging level (0 is highest priority).'''
        if self.log_level >= lvl:
            self.log_fn(msg)


    def get_series_names(self, column_indices = [], column_names = []):
        '''Returns the series' names corresponding to column_indices and column_names.
           "names" here are:
              - strings for single-indexed dataframes; or
              - tuples for multi-indexed dataframes.

           If both parameters are empty then all column names are returned.
        '''
        n = []
        if not column_indices and not column_names:
            for k, v in sorted(self.series_names.iteritems()):
                # Iterate by index to preserve document order
                if v != self.reference_series:
                    n.append(k)
        else:
            s = set([self.series_names[x] for x in column_indices])
            t = set([self.series_index[x] for x in column_names])
            n = sorted(s.union(t))
        assert(n)
        return [self.series_names[x] for x in n]


    def _analyze(self):
        '''Run-once function to generate analysis over all series, considering both full and partial data.
           Initializes the self.analysis dict which maps:
               (non-reference) column/series -> 'full' and/or 'partial' -> stats dict returned by get_xy_dataset_statistics
        '''

        if not self.analysis:
            for dseries in self.data_series:

                # Count number of non-NaN rows
                dseries_count = self.df[dseries].count()
                assert(len(self.df_pruned) <= dseries_count <= len(self.df) or dseries_count)
                self.analysis[dseries] = dict(
                    partial = None,
                    full = None,
                )

                # Compute the statistics for the common records
                stats = get_xy_dataset_statistics_pandas(self.df_pruned, self.reference_series, dseries,
                                                         fcorrect_x_cutoff = 1.0, fcorrect_y_cutoff = 1.0,
                                                         bootstrap_data = False,
                                                         x_fuzzy_range = 0.1,
                                                         y_scalar = 1.0, ignore_null_values = True)

                if (len(self.df_pruned) == len(self.df)):
                    # There are no pruned records so these are actually the full stats
                    self.analysis[dseries]['full'] = dict(data = stats, description = format_stats(stats, floating_point_format = '%0.3f', sci_notation_format = '%.2E', return_string = True))
                else:
                    # Store the results for the partial dataset
                    self.analysis[dseries]['partial'] = dict(data = stats, description = format_stats(stats, floating_point_format = '%0.3f', sci_notation_format = '%.2E', return_string = True))
                    if dseries_count > len(self.df_pruned):
                        # This dataset has records which are not in the pruned dataset
                        stats = get_xy_dataset_statistics_pandas(self.df, self.reference_series, dseries,
                                                                 fcorrect_x_cutoff = 1.0, fcorrect_y_cutoff = 1.0,
                                                                 bootstrap_data = False,
                                                                 x_fuzzy_range = 0.1,
                                                                 y_scalar = 1.0, ignore_null_values = True)
                        self.analysis[dseries]['full'] = dict(data = stats, description = format_stats(stats, floating_point_format = '%0.3f', sci_notation_format = '%.2E', return_string = True))

        return self.analysis


    def to_csv(self, filepath):
        return self.df.to_csv(filepath)


    def get_stats(self):
        self._analyze()
        return self.analysis


    def summarize(self, series_ = None, subset_ = None, summary_title_formatter = None, color = True):
        self._analyze()
        summary = []
        for series, subset in sorted(self.analysis.iteritems()):
            if series_ == None or series_ == series:
                ttl, sub_summary = series, []
                for subset_type, v in sorted(subset.iteritems()):
                    if subset_ == None or subset_ == series:
                        if v:
                            if color:
                                sub_summary.append(colortext.make('Subset: ' + subset_type, 'yellow'))
                            else:
                                sub_summary.append('Subset: ' + subset_type)
                            sub_summary.append(self._summarize_case(v['data']))
                if sub_summary:
                    if summary_title_formatter:
                        summary += [summary_title_formatter(series)] + sub_summary
                    else:
                        summary += [series] + sub_summary

        if summary:
            return '\n'.join(summary)
        else:
            return None


    def _summarize_case(self, data):

        assert(data)
        s = []
        data = copy.deepcopy(data)
        # Some of the data is currently returned as tuples
        data['significant_beneficient_sensitivity_n'] = data['significant_beneficient_sensitivity'][1]
        data['significant_beneficient_sensitivity'] = data['significant_beneficient_sensitivity'][0]
        data['significant_beneficient_specificity_n'] = data['significant_beneficient_specificity'][1]
        data['significant_beneficient_specificity'] = data['significant_beneficient_specificity'][0]
        data['pearsonr'], data['pearsonr_pvalue'] = data['pearsonr']
        data['spearmanr'], data['spearmanr_pvalue'] = data['spearmanr']
        return '''
Cardinality
\tn         : {n:d}
\tNull cases: {num_null_cases:d}

Correlation
\tR-value: {pearsonr:<10.03f} Slope: {pearsonr_slope:<10.03f} pvalue={pearsonr_pvalue:.2E}\t (Pearson's R)
\tR-value: {pearsonr_origin:<10.03f} Slope: {pearsonr_slope_origin:<10.03f} -               \t (Pearson's R through origin)
\trho    : {spearmanr:<10.03f} -                 pvalue={pearsonr_pvalue:.2E}\t (Spearman's rho)

Error:
\tMAE                  : {MAE:<10.03f} Scaled MAE: {scaled_MAE:.03f}
\tFraction correct (FC): {fraction_correct:<10.03f} Fuzzy FC  : {fraction_correct_fuzzy_linear:.03f}

Error (normalized, signficance = {std_dev_cutoff:.2f} standard deviations):
\tPercent correct sign (accuracy): {accuracy:.01%}
\tPercent significant predictions with correct sign (specificity): {specificity:.01%}
\tPercent significant experimental hits with correct prediction sign (sensitivity): {sensitivity:.01%}
\tPercent significant predictions are significant experimental hits (significance specificity): {significance_specificity:.01%}
\tPercent significant experimental hits are predicted significant hits (significance sensitivity): {significance_sensitivity:.01%}
\tPercent significant beneficial experimental hits are predicted significant beneficial hits (significant beneficient sensitivity): {significant_beneficient_sensitivity:.01%}
\tPercent significant beneficial predictions are significant beneficial experimental hits (significant beneficient specificity): {significant_beneficient_specificity:.01%}
\n'''.format(**data)


    def tabulate(self, restricted_predicted_column_indices = [], restricted_predicted_column_names = [], dataset_name = None):
        '''Returns summary analysis from the dataframe as a DataTable object.
           DataTables are wrapped pandas dataframes which can be combined if the have the same width. This is useful for combining multiple analyses.
           DataTables can be printed to terminal as a tabular string using their representation function (i.e. print(data_table)).
           This function (tabulate) looks at specific analysis; this class (DatasetDataFrame) can be subclassed for custom tabulation.'''

        self._analyze()

        data_series = self.get_series_names(column_indices = restricted_predicted_column_indices, column_names = restricted_predicted_column_names)

        # Determine the multi-index headers
        group_names = []
        for l in self.index_layers:
            group_names.append(l)

        # Set up the table headers
        headers = ['Dataset'] + group_names + ['n', 'R', 'rho', 'MAE', 'Fraction correct  ', 'FC sign', 'SB sensitivity', 'SB specificity']
        table_rows = []
        for dseries in data_series:
            if isinstance(dseries, tuple):
                dseries_l = list(dseries)
            else:
                assert(isinstance(dseries, basestring))
                dseries_l = [dseries]

            results = []
            assert (len(self.index_layers) == len(dseries))
            if self.analysis.get(dseries, {}).get('partial') and self.analysis.get(dseries, {}).get('full'):# data_series in self.analysis[dseries]['full']:
                results.append((dseries_l[:-1] + [dseries_l[-1] + '*'], self.analysis[dseries]['partial']))
                results.append((dseries_l[:-1] + [dseries_l[-1]], self.analysis[dseries]['full']))
            elif (self.analysis.get(dseries, {}).get('partial')):
                results.append((dseries_l[:-1] + [dseries_l[-1] + '*'], self.analysis[dseries]['partial']))
            elif (self.analysis.get(dseries, {}).get('full')):
                results = [(dseries, self.analysis[dseries]['full'])]

            for result in results:
                n = result[1]['data']['n']
                R = result[1]['data']['pearsonr'][0]
                rho = result[1]['data']['spearmanr'][0]
                mae = result[1]['data']['MAE']
                fraction_correct = result[1]['data']['fraction_correct']
                accuracy = result[1]['data']['accuracy']
                SBSensitivity = '{0:.3f} / {1}'.format(result[1]['data']['significant_beneficient_sensitivity'][0], result[1]['data']['significant_beneficient_sensitivity'][1])
                SBSpecificity = '{0:.3f} / {1}'.format(result[1]['data']['significant_beneficient_specificity'][0], result[1]['data']['significant_beneficient_specificity'][1])

                method = result[0]
                if isinstance(method, tuple):
                    method = list(method)

                table_rows.append([dataset_name or self.reference_dataset_name] + method +
                                  [n, R, rho, mae, fraction_correct, accuracy, SBSensitivity, SBSpecificity])

        # Convert the lists into a (wrapped) pandas dataframe to make use of the pandas formatting code to save reinventing the wheel...
        return DataTable(pandas.DataFrame(table_rows, columns = headers), self.index_layers)


#outliers consistent


class DataTable(object):

    def __init__(self, dataframe, index_layers):
        self.df = dataframe
        self.index_layers = index_layers
        self.headers = self.df.columns.values

    def __add__(self, other):
        if len(self.headers) != len(other.headers):
            raise Exception('The two tables have different widths.')
        if len(self.index_layers) != len(other.index_layers):
            raise Exception('The two tables have different levels of grouping.')
        if sorted(self.headers) != sorted(other.headers):
            # todo: Think about what to do if the headers disagree (ignore and combine anyway or add additional columns?). Should we at least require the index layers to be identical?
            raise Exception('The two tables have different headers and may contain different data.')

        return DataTable(pandas.concat([self.df, other.df]), self.index_layers)


    def __repr__(self):
        '''
        Note: This is very sensitive to the width of the table. Move the formatters into the constructor instead.
        Reinventing the wheel to get around problem justifying text columns - the justify argument to to_string only
        justifies the headers because that is a really sensible thing to do...'''
        text_formatters = []
        for i in range(len(self.index_layers)):
            h = self.headers[1 + i]
            max_str_len = max(len(h), self.df[h].map(str).map(len).max())
            if max_str_len >= 7:
                max_str_len += 3 # extra space
            text_formatters.append('{{:<{}}}'.format(max_str_len).format)

        return self.df.to_string(
                index = False,
                justify = 'left',
                col_space = 9,
                formatters = [None] + text_formatters +
                    ['{:,d}'.format] +     # n
                    (['{:.3f}'.format] * 5) +
                    (['{}'.format] * 2)
        )


