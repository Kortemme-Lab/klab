#!/usr/bin/env python2

# The MIT License (MIT)
#
# Copyright (c) 2015 Shane O'Connor
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
This module contains one main class.

The BenchmarkRun class creates a dataframe containing the raw data used for DDG analysis. This dataframe is then used to
performs analysis for the particular run or between another runs.

This class should not be specific to a particular computational method so it can be reusable for generic monomeric stability
DDG analysis.
'''

import os
import sys
import shutil
import numpy
import pprint
import shlex
import tempfile
import copy
import StringIO
import gzip
import time
import datetime
import getpass
import multiprocessing as mp
try: import json
except: import simplejson as json

import pandas

from klab import colortext
from klab.Reporter import Reporter
import klab.latex.latex_report as lr
from klab.fs.fsio import read_file, write_file, write_temp_file
from klab.loggers.simple import ReportingObject
from klab.gfx.color_definitions import rgb_colors as plot_colors
from klab.stats.misc import fraction_correct, fraction_correct_pandas, add_fraction_correct_values_to_dataframe, get_xy_dataset_statistics_pandas, format_stats, float_format_2sigfig, float_format_3sigfig, subtract_row_pairs_for_display
from klab.benchmarking.analysis.plot import plot_pandas
from klab.plot.rtools import RInterface
from klab.plot import general_matplotlib

class BenchmarkRun(ReportingObject):
    '''A object to contain benchmark run data which can be used to analyze that run or else to cross-analyze the run with another run.'''

    # Class variables
    amino_acid_details = {}
    CAA, PAA, HAA = set(), set(), set()


    # Human-readable descriptions for the volume breakdown
    by_volume_descriptions = dict(
        SL = 'small-to-large mutations',
        LS = 'large-to-small mutations',
        XX = 'no change in volume',
    )

    csv_headers = [
        'DatasetID', 'PDBFileID', 'Mutations', 'NumberOfMutations', 'Experimental', 'Predicted', 'AbsoluteError', 'StabilityClassification',
        'ResidueCharges', 'VolumeChange',
        'WildTypeDSSPType', 'WildTypeDSSPSimpleSSType', 'WildTypeDSSPExposure',
        'WildTypeSCOPClass', 'WildTypeSCOPFold', 'WildTypeSCOPClassification',
        'WildTypeExposure', 'WildTypeAA', 'MutantAA', 'HasGPMutation',
        'PDBResolution', 'PDBResolutionBin', 'NumberOfResidues', 'NumberOfDerivativeErrors',
    ]

    def __init__(self, benchmark_run_name, dataset_cases, analysis_data, contains_experimental_data = True, benchmark_run_directory = None, use_single_reported_value = False,
                 ddg_analysis_type = None,
                 calculate_scalar_adjustments = True,
                 description = None, dataset_description = None, credit = None, generate_plots = True, report_analysis = True, include_derived_mutations = False, recreate_graphs = False, silent = False, burial_cutoff = 0.25,
                 additional_join_parameters = {},
                 stability_classication_x_cutoff = 1.0, stability_classication_y_cutoff = 1.0, use_existing_benchmark_data = False, store_data_on_disk = True, misc_dataframe_attributes = {},
                 terminal_width = 200, restrict_to = set(), remove_cases = set()):

        self.contains_experimental_data = contains_experimental_data
        self.analysis_sets = [''] # some subclasses store values for multiple analysis sets
        self.calculate_scalar_adjustments = calculate_scalar_adjustments
        self.csv_headers = copy.deepcopy(self.__class__.csv_headers)
        self.additional_join_parameters = additional_join_parameters
        if 'ddg_analysis_type' in additional_join_parameters:
            if ddg_analysis_type != None:
                assert( ddg_analysis_type == additional_join_parameters['ddg_analysis_type']['long_name'] )
            self.ddg_analysis_type = additional_join_parameters['ddg_analysis_type']['long_name']
        else:
            assert( ddg_analysis_type != None )
            self.ddg_analysis_type = ddg_analysis_type

        if not self.contains_experimental_data:
            self.csv_headers.remove('Experimental')
            self.csv_headers.remove('AbsoluteError')
            self.csv_headers.remove('StabilityClassification')

        self.terminal_width = terminal_width # Used for printing the dataframe to a terminal. Set this to be less than the width of your terminal in columns.
        self.amino_acid_details, self.CAA, self.PAA, self.HAA = BenchmarkRun.get_amino_acid_details()
        self.benchmark_run_name = benchmark_run_name
        self.benchmark_run_directory = benchmark_run_directory
        self.dataset_cases = copy.deepcopy(dataset_cases)
        self.analysis_data = copy.deepcopy(analysis_data)
        self.analysis_directory = None
        self.subplot_directory = None
        self.restrict_to = restrict_to
        self.remove_cases = remove_cases
        self.use_single_reported_value = use_single_reported_value
        self.description = description
        self.dataset_description = dataset_description
        self.credit = credit
        self.generate_plots = generate_plots
        self.report_analysis = report_analysis
        self.silent = silent
        self.include_derived_mutations = include_derived_mutations
        self.burial_cutoff = burial_cutoff
        self.recreate_graphs = recreate_graphs
        self.stability_classication_x_cutoff = stability_classication_x_cutoff
        self.stability_classication_y_cutoff = stability_classication_y_cutoff
        self.scalar_adjustments = {}
        self.store_data_on_disk = store_data_on_disk
        self.misc_dataframe_attributes = misc_dataframe_attributes
        assert(credit not in self.misc_dataframe_attributes)
        self.misc_dataframe_attributes['Credit'] = credit

        self.metric_latex_objects = []
        self.stored_metrics_df = pandas.DataFrame()

        if self.store_data_on_disk:
            # This may be False in some cases e.g. when interfacing with a database
            self.analysis_csv_input_filepath = os.path.join(self.benchmark_run_directory, 'analysis_input.csv')
            self.analysis_json_input_filepath = os.path.join(self.benchmark_run_directory, 'analysis_input.json')
            self.analysis_raw_data_input_filepath = os.path.join(self.benchmark_run_directory, 'benchmark_data.json')
            self.analysis_pandas_input_filepath = os.path.join(self.benchmark_run_directory, 'analysis_input.pandas')
            assert(os.path.exists(self.analysis_csv_input_filepath))
            assert(os.path.exists(self.analysis_json_input_filepath))
            assert(os.path.exists(self.analysis_raw_data_input_filepath))
        else:
            self.analysis_csv_input_filepath, self.analysis_json_input_filepath, self.analysis_raw_data_input_filepath, self.analysis_pandas_input_filepath = None, None, None, None
        self.use_existing_benchmark_data = use_existing_benchmark_data
        self.ddg_analysis_type_description = None
        self.filter_data()

    def add_stored_metric_to_df(self, case_description, case_length, case_stats):
        # Reformat statistics to put a column for each stat type
        stats = {}
        for case_stat in case_stats:
            stats[ case_stat[0] ] = [case_stat[1]]
            stats[ case_stat[0] + '-p-val' ] = [case_stat[2]]

        df = pandas.DataFrame.from_dict(stats)
        num_rows = len(df.index)
        df.loc[:,'case_description'] = pandas.Series([case_description for x in xrange(num_rows)], index=df.index)
        df.loc[:,'benchmark_run_name'] = pandas.Series([self.benchmark_run_name for x in xrange(num_rows)], index=df.index)
        df.loc[:,'n'] = pandas.Series([case_length for x in xrange(num_rows)], index=df.index)
        self.stored_metrics_df = pandas.concat([self.stored_metrics_df, df])


    def filter_data(self):
        '''A very rough filtering step to remove certain data.
           todo: It is probably best to do this do the actual dataframe rather than at this point.
           todo: We currently only handle one filtering criterium.
        '''

        if not self.dataset_cases or not self.analysis_data:
            # colortext.error('No dataset cases or analysis (DDG) data were passed. Cannot filter the data. If you are using an existing dataframe, this may explain why no data was passed.')
            return
        if self.restrict_to or self.remove_cases:

            # Remove any cases with missing data
            available_cases = set(self.analysis_data.keys())
            missing_dataset_cases = [k for k in self.dataset_cases.keys() if k not in available_cases]
            for k in missing_dataset_cases:
                del self.dataset_cases[k]

            cases_to_remove = set()
            if self.restrict_to:
                # Remove cases which do not meet the restriction criteria
                if 'Exposed' in self.restrict_to:
                    for k, v in self.dataset_cases.iteritems():
                        for m in v['PDBMutations']:
                            if (m.get('ComplexExposure') or m.get('MonomericExposure')) <= self.burial_cutoff:
                                cases_to_remove.add(k)
                                break
            if self.remove_cases:
                # Remove cases which meet the removal criteria
                if 'Exposed' in self.remove_cases:
                    for k, v in self.dataset_cases.iteritems():
                        for m in v['PDBMutations']:
                            if (m.get('ComplexExposure') or m.get('MonomericExposure')) > self.burial_cutoff:
                                cases_to_remove.add(k)
                                break

            if cases_to_remove:
                colortext.warning('Filtering out {0} records.'.format(len(cases_to_remove)))

            for k in cases_to_remove:
                del self.dataset_cases[k]
                del self.analysis_data[k]


    def __repr__(self):
        '''Simple printer - we print the dataframe.'''
        with pandas.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', self.terminal_width):
            return '{0}'.format(self.dataframe)


    @staticmethod
    def get_analysis_set_fieldname(prefix, analysis_set):
        if analysis_set:
            return '{0}_{1}'.format(prefix, analysis_set)
        else:
            return prefix


    @staticmethod
    def get_amino_acid_details():
        if not BenchmarkRun.amino_acid_details:
            # Amino acid properties
            polarity_map = {'polar' : 'P', 'charged' : 'C', 'hydrophobic' : 'H'}
            aromaticity_map = {'aliphatic' : 'L', 'aromatic' : 'R', 'neither' : '-'}
            amino_acid_detail_headers = 'Code,Long code,Name,Polarity,Aromaticity,Hydrophobicity pH7,Sidechain acidity,pKa,Average mass,van der Waals volume,Size,Is tiny?'
            amino_acid_details_ = [
                'A,ALA,Alanine,non-polar,aliphatic,hydrophobic,neutral,NULL,71.0788,67,small,1',
                'C,CYS,Cysteine,polar,neither,hydrophilic,neutral,8.7,103.1388,86,small,1',
                'D,ASP,Aspartic acid,charged,neither,hydrophilic,acidic,3.9,115.0886,91,small,0',
                'E,GLU,Glutamic acid,charged,neither,hydrophilic,acidic,4.5,129.1155,109,large,0',
                'F,PHE,Phenylalanine,non-polar,aromatic,hydrophobic,neutral,NULL,147.1766,135,large,0',
                'G,GLY,Glycine,polar,neither,hydrophilic,neutral,NULL,57.0519,48,small,1',
                'H,HIS,Histidine,charged,neither,hydrophilic,basic,6.04,137.1411,118,large,0',
                'I,ILE,Isoleucine,non-polar,aliphatic,hydrophobic,neutral,NULL,113.1594,124,large,0',
                'K,LYS,Lysine,charged,neither,hydrophilic,basic,10.54,128.1741,135,large,0',
                'L,LEU,Leucine,non-polar,aliphatic,hydrophobic,neutral,NULL,113.1594,124,large,0',
                'M,MET,Methionine,non-polar,aliphatic,hydrophobic,neutral,NULL,131.1986,124,large,0',
                'N,ASN,Asparagine,polar,neither,hydrophilic,neutral,NULL,114.1039,96,small,0',
                'P,PRO,Proline,non-polar,neither,hydrophobic,neutral,NULL,97.1167,90,small,0',
                'Q,GLN,Glutamine,polar,neither,hydrophilic,neutral,NULL,128.1307,114,large,0',
                'R,ARG,Arginine,charged,neither,hydrophilic,basic,12.48,156.1875,148,large,0',
                'S,SER,Serine,polar,neither,hydrophilic,neutral,NULL,87.0782,73,small,1',
                'T,THR,Threonine,polar,neither,hydrophilic,neutral,NULL,101.1051,93,small,0',
                'V,VAL,Valine,non-polar,aliphatic,hydrophobic,neutral,NULL,99.1326,105,small,0',
                'W,TRP,Tryptophan,non-polar,aromatic,hydrophobic,neutral,NULL,186.2132,163,large,0',
                'Y,TYR,Tyrosine,polar,aromatic,hydrophobic,neutral,10.46,163.176,141,large,0' # Note: we treat tyrosine as hydrophobic in the polar/charged vs hydrophobic/Non-polar plot
            ]

            amino_acid_detail_headers = [t.strip() for t in amino_acid_detail_headers.split(',') if t.strip()]
            for aad in amino_acid_details_:
                tokens = aad.split(',')
                assert(len(tokens) == len(amino_acid_detail_headers))
                d = {}
                for x in range(len(amino_acid_detail_headers)):
                    d[amino_acid_detail_headers[x]] = tokens[x]
                aa_code = d['Code']
                BenchmarkRun.amino_acid_details[aa_code] = d
                del d['Code']
                d['Polarity'] = polarity_map.get(d['Polarity'], 'H')
                d['Aromaticity'] = aromaticity_map[d['Aromaticity']]
                d['Average mass'] = float(d['Average mass'])
                d['Is tiny?'] = d['Is tiny?'] == 1
                d['van der Waals volume'] = float(d['van der Waals volume'])
                try: d['pKa'] = float(d['pKa'])
                except: d['pKa'] = None

                if aa_code == 'Y':
                    BenchmarkRun.HAA.add(aa_code) # Note: Treating tyrosine as hydrophobic
                elif d['Polarity'] == 'C':
                    BenchmarkRun.CAA.add(aa_code)
                elif d['Polarity'] == 'P':
                    BenchmarkRun.PAA.add(aa_code)
                elif d['Polarity'] == 'H':
                    BenchmarkRun.HAA.add(aa_code)
        assert(len(BenchmarkRun.CAA.intersection(BenchmarkRun.PAA)) == 0 and len(BenchmarkRun.PAA.intersection(BenchmarkRun.HAA)) == 0 and len(BenchmarkRun.HAA.intersection(BenchmarkRun.CAA)) == 0)
        return BenchmarkRun.amino_acid_details, BenchmarkRun.CAA, BenchmarkRun.PAA, BenchmarkRun.HAA


    def report(self, str, fn = None):
        if (not self.silent) and (self.report_analysis):
            if fn:
                fn(str)
            else:
                print(str)


    def create_analysis_directory(self, analysis_directory = None):
        if self.analysis_directory:
            return
        if analysis_directory:
            if not(os.path.isdir(analysis_directory)):
                try:
                    os.makedirs(analysis_directory)
                    assert(os.path.isdir(analysis_directory))
                    self.analysis_directory = analysis_directory
                except Exception, e:
                    raise colortext.Exception('An exception occurred creating the subplot directory %s.' % analysis_directory)
        else:
            self.analysis_directory = tempfile.mkdtemp( prefix = '%s-%s-%s_' % (time.strftime("%y%m%d"), getpass.getuser(), self.benchmark_run_name) )

    def create_subplot_directory(self, analysis_directory = None):
        if self.subplot_directory:
            return

        self.create_analysis_directory(analysis_directory = analysis_directory)
        self.subplot_directory = os.path.join(self.analysis_directory, self.benchmark_run_name + '_subplots')
        if not os.path.isdir(self.subplot_directory):
            os.makedirs(self.subplot_directory)


    def read_dataframe_from_content(self, hdfstore_blob):
        fname = write_temp_file('/tmp', hdfstore_blob, ftype = 'wb')
        try:
            self.read_dataframe(fname)
            os.remove(fname)
        except:
            os.remove(fname)
            raise


    def read_dataframe(self, analysis_pandas_input_filepath, read_scalar_adjustments = True, fail_on_missing_scalar_adjustments = False):
        remove_file = False
        if len(os.path.splitext(analysis_pandas_input_filepath)) > 1 and os.path.splitext(analysis_pandas_input_filepath)[1] == '.gz':
            content = read_file(analysis_pandas_input_filepath)
            analysis_pandas_input_filepath = write_temp_file('/tmp', content, ftype = 'wb')
            remove_file = True

        # We do not use "self.dataframe = store['dataframe']" as we used append in write_dataframe
        self.dataframe = pandas.read_hdf(analysis_pandas_input_filepath, 'dataframe')

        store = pandas.HDFStore(analysis_pandas_input_filepath)
        self.scalar_adjustments = store['scalar_adjustments'].to_dict()
        self.ddg_analysis_type = store['ddg_analysis_type'].to_dict()['ddg_analysis_type']
        if read_scalar_adjustments:
            try:
                self.calculate_scalar_adjustments = store['calculate_scalar_adjustments'].to_dict()['calculate_scalar_adjustments']
            except:
                if not fail_on_missing_scalar_adjustments:
                    colortext.warning('The calculate_scalar_adjustments scalar was expected to be found in the pandas dataframe but is missing.')
                    self.calculate_scalar_adjustments = None
                else:
                    raise
        else:
            self.calculate_scalar_adjustments = None

        self.ddg_analysis_type_description = store['ddg_analysis_type_description'].to_dict()['ddg_analysis_type_description']

        # Handle our old dataframe format
        try:
            self.misc_dataframe_attributes = store['misc_dataframe_attributes'].to_dict()
        except: pass

        # Handle our new dataframe format
        try:
            misc_dataframe_attribute_names = store['misc_dataframe_attribute_names'].to_dict().keys()
            for k in misc_dataframe_attribute_names:
                assert(k not in self.misc_dataframe_attributes)
                self.misc_dataframe_attributes[k] = store[k].to_dict()[k]
        except: pass

        if 'Credit' in self.misc_dataframe_attributes:
            self.credit = self.misc_dataframe_attributes['Credit']

        store.close()
        if remove_file:
            os.remove(analysis_pandas_input_filepath)


    def set_dataframe(self, dataframe, verbose = True):
        self.dataframe = dataframe
        # Report the SCOPe classification counts
        SCOP_classifications = set(dataframe['WildTypeSCOPClassification'].values.tolist())
        SCOP_folds = set(dataframe['WildTypeSCOPFold'].values.tolist())
        SCOP_classes = set(dataframe['WildTypeSCOPClass'].values.tolist())
        self.log('The mutated residues span {0} unique SCOP(e) classifications in {1} unique SCOP(e) folds and {2} unique SCOP(e) classes.'.format(len(SCOP_classifications), len(SCOP_folds), len(SCOP_classes)), colortext.message)

        # Plot the optimum y-cutoff over a range of x-cutoffs for the fraction correct metric (when experimental data is available).
        # Include the user's cutoff in the range.
        if self.contains_experimental_data and self.calculate_scalar_adjustments:
            if len(self.analysis_sets) == 0 and len(self.scalar_adjustments):
                self.analysis_sets = self.scalar_adjustments.keys()
            self.log('Determining scalar adjustments with which to scale the predicted values to improve the fraction correct measurement.', colortext.warning)
            for analysis_set in self.analysis_sets:#scalar_adjustments.keys():
                self.scalar_adjustments[analysis_set], plot_filename = self.plot_optimum_prediction_fraction_correct_cutoffs_over_range(analysis_set, min(self.stability_classication_x_cutoff, 0.5), max(self.stability_classication_x_cutoff, 3.0), suppress_plot = True, verbose = verbose)


            # Add new columns derived from the adjusted values
            for analysis_set in self.analysis_sets:
                dataframe[BenchmarkRun.get_analysis_set_fieldname('Predicted_adj', analysis_set)] = dataframe['Predicted'] / self.scalar_adjustments[analysis_set]
                dataframe[BenchmarkRun.get_analysis_set_fieldname('AbsoluteError_adj', analysis_set)] = (dataframe[BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set)] - dataframe[BenchmarkRun.get_analysis_set_fieldname('Predicted_adj', analysis_set)]).abs()
                add_fraction_correct_values_to_dataframe(dataframe, BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set), BenchmarkRun.get_analysis_set_fieldname('Predicted_adj', analysis_set), BenchmarkRun.get_analysis_set_fieldname('StabilityClassification_adj', analysis_set),  x_cutoff = self.stability_classication_x_cutoff, y_cutoff = self.stability_classication_y_cutoff, ignore_null_values = True)

        # Write the dataframe out to CSV
        if self.store_data_on_disk:
            self.write_dataframe_to_csv(self.analysis_csv_input_filepath)

        # Write the dataframe out to JSON
        # Note: I rolled my own as dataframe.to_dict(orient = 'records') gives us the correct format but discards the DatasetID (index) field
        json_records = {}
        indices = dataframe.index.values.tolist()
        for i in indices:
            json_records[i] = {}
        for k, v in dataframe.to_dict().iteritems():
            for i, v in v.iteritems():
                assert(k not in json_records[i])
                json_records[i][k] = v
        if self.analysis_json_input_filepath and self.store_data_on_disk:
            write_file(self.analysis_json_input_filepath, json.dumps(json_records, indent = 4, sort_keys=True))

        # Write the values computed in this function out to disk
        analysis_pandas_input_filepath = self.analysis_pandas_input_filepath
        if self.store_data_on_disk:
            if os.path.exists(analysis_pandas_input_filepath):
                os.remove(analysis_pandas_input_filepath)
        else:
            analysis_pandas_input_filepath = write_temp_file('/tmp', '', ftype = 'wb')
        try:
            analysis_pandas_input_filepath = self.write_dataframe(analysis_pandas_input_filepath)
            dataframe_blob = read_file(analysis_pandas_input_filepath, binary = True)
            if not self.store_data_on_disk:
                os.remove(analysis_pandas_input_filepath)
        except Exception, e:
            if not self.store_data_on_disk:
                os.remove(analysis_pandas_input_filepath)
            raise
        return dataframe_blob

    def write_dataframe(self, analysis_pandas_input_filepath):
        store = pandas.HDFStore(analysis_pandas_input_filepath)

        # Using "store['dataframe'] = self.dataframe" throws a warning since some String columns contain null values i.e. mixed content
        # To get around this, we use the append function (see https://github.com/pydata/pandas/issues/4415)
        store.append('dataframe', self.dataframe)
        store['scalar_adjustments'] = pandas.Series(self.scalar_adjustments)
        store['ddg_analysis_type'] = pandas.Series(dict(ddg_analysis_type = self.ddg_analysis_type))
        store['calculate_scalar_adjustments'] = pandas.Series(dict(calculate_scalar_adjustments = self.calculate_scalar_adjustments))
        store['ddg_analysis_type_description'] = pandas.Series(dict(ddg_analysis_type_description = self.ddg_analysis_type_description))
        store['misc_dataframe_attribute_names'] = pandas.Series(dict.fromkeys(self.misc_dataframe_attributes, True))
        for k, v in self.misc_dataframe_attributes.iteritems():
            # misc_dataframe_attributes may have mixed content so we add the contents individually
            assert((k not in store.keys()) and ('/' + k not in store.keys()))
            store[k] = pandas.Series({k : v})
        store.close()

        with gzip.open(analysis_pandas_input_filepath + '.gz', 'wb') as f:
            f.write(read_file(analysis_pandas_input_filepath, binary = True))
        os.remove(analysis_pandas_input_filepath)
        return analysis_pandas_input_filepath + '.gz'


    def create_dataframe(self, pdb_data = {}, verbose = True):
        '''This function creates a dataframe (a matrix with one row per dataset record and one column for fields of interest)
           from the benchmark run and the dataset data.
           For rows with multiple mutations, there may be multiple values for some fields e.g. wildtype residue exposure.
           We take the approach of marking these records as None (to be read as: N/A).
           Another approach is to take averages of continuous and binary values.
           This function also determines scalar_adjustments used to scale the predictions to try to improve the fraction
           correct score and the MAE.
        '''

        if self.use_existing_benchmark_data and self.store_data_on_disk and os.path.exists(self.analysis_pandas_input_filepath):
            self.read_dataframe(self.analysis_pandas_input_filepath)
            return

        analysis_data = self.analysis_data
        dataset_cases = self.dataset_cases

        # Create XY data
        if self.store_data_on_disk:
            self.log('Creating the analysis input file %s and human-readable CSV and JSON versions %s and %s.' % (self.analysis_pandas_input_filepath, self.analysis_csv_input_filepath, self.analysis_json_input_filepath))
        if len(analysis_data) > len(dataset_cases):
            raise colortext.Exception('ERROR: There seems to be an error - there are more predictions than cases in the dataset. Exiting.')
        elif len(analysis_data) < len(dataset_cases):
            self.log('\nWARNING: %d cases missing for analysis; there are %d predictions in the output directory but %d cases in the dataset. The analysis below does not cover the complete dataset.\n' % (len(dataset_cases) - len(analysis_data), len(analysis_data), len(dataset_cases)), colortext.error)

        #  ddg_analysis_type can be set to 'DDG', 'DDG_Top[x]' (e.g. 'DDG_Top3'), eyc.
        # 'DDG' uses the value reported by the application. For the Rosetta application ddg_monomer by Kellogg et al., this is the value output at the end of a run (which is not the recommended value - the publication uses take_lowest := 3).
        # 'DDG_Top3' (generated by default) uses the metric from Kellogg et al. based on the three lowest scoring mutant structures and the three lowest scoring wildtype structures
        if self.use_single_reported_value or self.ddg_analysis_type == 'DDG':
            assert( self.ddg_analysis_type == 'DDG' )
            self.ddg_analysis_type_description = '\nThe predicted DDG value per case is the single DDG value reported by the application.'
        elif self.ddg_analysis_type[4:].startswith('Top') and int(self.ddg_analysis_type[7:]) == 3:
            take_lowest = int(self.ddg_analysis_type[7:])
            self.ddg_analysis_type_description = '\nThe predicted DDG value per case is computed using the {0} lowest-scoring mutant structures and the {0} lowest-scoring wildtype structures as in the paper by Kellogg et al.'.format(take_lowest)
        elif self.ddg_analysis_type[4:].startswith('Top'):
            take_lowest = int(self.ddg_analysis_type[7:])
            self.ddg_analysis_type_description = '\nThe predicted DDG value per case is computed using the {0} lowest-scoring mutant structures and the {0} lowest-scoring wildtype structures.'.format(take_lowest)
        elif self.ddg_analysis_type[4:].startswith('Random'):
            ddg_analysis_type = self.ddg_analysis_type[4:]
            if len( ddg_analysis_type ) > len('Random'):
                self.ddg_analysis_type_description = '\nThe predicted DDG value per case is computed by pairing {0} random mutant structures with {0} random wildtype structures.'.format( int(ddg_analysis_type[len('Random'):]) )
            else:
                self.ddg_analysis_type_description = '\nThe predicted DDG value per case is computed by pairing random mutant structures with random wildtype structures.'
        elif self.ddg_analysis_type[4:] == 'AvgAllPairs':
            self.ddg_analysis_type_description = '\nThe predicted DDG value per case is computed by constructing all pairs of all mutant structures with all wildtype structures.'
        elif self.ddg_analysis_type[4:] == 'MatchPairs':
            self.ddg_analysis_type_description = '\nThe predicted DDG value per case is computed by matching each wildtype structure with its corresponding (round number) mutant structure.'
        elif self.ddg_analysis_type[4:].startswith( 'CplxBoltzWT' ):
            assert( len(self.ddg_analysis_type[4:]) > len( 'CplxBoltzWT' ) )
            self.ddg_analysis_type_description = '\nThe predicted DDG value per case is computed by boltzmann weighting matching DDG scores on the wildtype complex score (temperature %.2f).' % float(self.ddg_analysis_type[4+len('CplxBoltzWT'):])
        elif self.ddg_analysis_type[4:].startswith( 'CplxBoltzMut' ):
            assert( len(self.ddg_analysis_type[4:]) > len( 'CplxBoltzMut' ) )
            self.ddg_analysis_type_description = '\nThe predicted DDG value per case is computed by boltzmann weighting matching DDG scores on the mutant complex score (temperature %.2f).' % float(self.ddg_analysis_type[4+len('CplxBoltzMut'):])
        elif self.ddg_analysis_type[4:].startswith( 'CplxBoltzBoth' ):
            assert( len(self.ddg_analysis_type[4:]) > len( 'CplxBoltzBoth' ) )
            self.ddg_analysis_type_description = '\nThe predicted DDG value per case is computed by boltzmann weighting matching DDG scores on both the mutant complex score and the wildtype complex score, added together (temperature %.2f).' % float(self.ddg_analysis_type[4+len('CplxBoltzBoth'):])
        else:
            raise Exception("Couldn't parse ddg_analysis_type: " + str(ddg_analysis_type))
        self.log(self.ddg_analysis_type_description)

        # Initialize the data structures
        #csv_file = []

        # Set the PDB input path
        if not pdb_data:
            try:
                pdb_data_ = json.loads(read_file('../../input/json/pdbs.json'))
                for k, v in pdb_data_.iteritems():
                    pdb_data[k.upper()] = v
            except Exception, e:
                self.log('input/json/pdbs.json could not be found - PDB-specific analysis cannot be performed.', colortext.error)
        else:
            # Normalize to upper case to avoid matching problems later
            new_pdb_data = {}
            for k, v in pdb_data.iteritems():
                assert(k.upper() not in new_pdb_data)
                new_pdb_data[k.upper()] = v
            pdb_data = new_pdb_data

        # Determine columns specific to the prediction data to be added
        additional_prediction_data_columns = set()
        for adv in analysis_data.values():
            additional_prediction_data_columns = additional_prediction_data_columns.union(set(adv.keys()))
        assert(len(additional_prediction_data_columns.intersection(set(self.csv_headers))) == 0)
        assert(self.ddg_analysis_type in additional_prediction_data_columns)
        additional_prediction_data_columns.remove(self.ddg_analysis_type)
        additional_prediction_data_columns = sorted(additional_prediction_data_columns)

        # Initialize the dataframe
        self.reset_csv_headers() # this is necessary for the DBBenchmarkRun class which is missing the Experimental, AbsoluteError, and StabilityClassification columns since it adds new columns per analysis set.
        res = pandas.DataFrame(columns=(self.csv_headers + additional_prediction_data_columns))
        dataframe_columns = self.csv_headers + additional_prediction_data_columns
        additional_prediction_data_columns = tuple(additional_prediction_data_columns)

        # Create the dataframe
        dataframe_table = {}
        indices = []
        for record_id, predicted_data in sorted(analysis_data.iteritems()):
            dataframe_record = self.get_dataframe_row(dataset_cases, predicted_data, pdb_data, record_id, additional_prediction_data_columns)
            if dataframe_record:
                indices.append(dataframe_record['DatasetID'])
                for h in dataframe_columns:
                    dataframe_table[h] = dataframe_table.get(h, [])
                    dataframe_table[h].append(dataframe_record[h])
                assert(sorted(dataframe_columns) == sorted(dataframe_record.keys()))
        dataframe = pandas.DataFrame(dataframe_table, index = indices)
        return self.set_dataframe(dataframe, verbose = verbose)

    def write_dataframe_to_csv(self, output_path):
        # Write the dataframe out to CSV
        self.dataframe.to_csv(output_path, sep = ',', header = True)

    def reset_csv_headers(self):
        pass


    def is_this_record_a_derived_mutation(self, record):
        '''Different callers to this class store this information differently so we make it class-dependent and subclass.'''
        if record['DerivedMutation']:
            return True


    def get_record_mutations(self, record):
        '''Different callers should use the same name here but they currently do not.'''
        return record['Mutations']


    def get_experimental_ddg_values(self, record, dataframe_record):
        dataframe_record['Experimental'] = record['DDG']


    def compute_stability_classification(self, predicted_data, record, dataframe_record):
        '''Calculate the stability classification for this case.'''
        stability_classification, stability_classication_x_cutoff, stability_classication_y_cutoff = None, self.stability_classication_x_cutoff, self.stability_classication_y_cutoff
        if record['DDG'] != None:
            stability_classification = fraction_correct([record['DDG']], [predicted_data[self.ddg_analysis_type]], x_cutoff = stability_classication_x_cutoff, y_cutoff = stability_classication_y_cutoff)
            stability_classification = int(stability_classification)
            assert(stability_classification == 0 or stability_classification == 1)
        dataframe_record['StabilityClassification'] = stability_classification


    def compute_absolute_error(self, predicted_data, record, dataframe_record):
        '''Calculate the absolute error for this case.'''
        absolute_error = abs(record['DDG'] - predicted_data[self.ddg_analysis_type])
        dataframe_record['AbsoluteError'] = absolute_error


    def get_record_pdb_file_id(self, record):
        return record['PDBFileID']


    def count_residues(self, record, pdb_record):
        '''Count the number of residues in the chains for the case.'''
        mutations = self.get_record_mutations(record)
        pdb_chains = set([m['Chain'] for m in mutations])
        assert(len(pdb_chains) == 1) # we expect monomeric cases
        pdb_chain = pdb_chains.pop()
        return len(pdb_record.get('Chains', {}).get(pdb_chain, {}).get('Sequence', ''))


    def get_dataframe_row(self, dataset_cases, predicted_data, pdb_data, record_id, additional_prediction_data_columns):
        '''Create a dataframe row for a prediction.'''

        # Ignore derived mutations if appropriate
        record = dataset_cases[record_id]
        if self.is_this_record_a_derived_mutation(record) and not self.include_derived_mutations:
            return None

        amino_acid_details, CAA, PAA, HAA = self.amino_acid_details, self.CAA, self.PAA, self.HAA
        burial_cutoff = self.burial_cutoff

        # Initialize variables. For ambiguous cases where the set of distinct values has multiple values, we default to None
        residue_charge, residue_charges = None, set()
        exposure, exposures = None, set()
        volume_change, volume_changes = None, set()
        record_wtaa, wtaas = None, set()
        record_mutaa, mutaas = None, set()
        DSSPSimpleSSType, DSSPSimpleSSTypes = None, set()
        DSSPType, DSSPTypes = None, set()
        DSSPExposure, DSSPExposures = None, set()
        scops = set()
        mutation_string = []
        num_derivative_errors = predicted_data.get('Errors', {}).get('Derivative error count', 0)
        run_time = predicted_data.get('RunTime', None)
        max_memory = predicted_data.get('MaxMemory', None)

        mutations = self.get_record_mutations(record)
        for m in mutations:

            wtaa = m['WildTypeAA']
            mutaa = m['MutantAA']
            mutation_string.append('{0} {1}{2}{3}'.format(m['Chain'], m['WildTypeAA'], m['ResidueID'], m['MutantAA']))

            # Residue types and chain
            wtaas.add(wtaa)
            mutaas.add(mutaa)
            if m.get('SCOP class'):
                scops.add(m['SCOP class'])
            DSSPSimpleSSTypes.add(m['DSSPSimpleSSType'])
            DSSPTypes.add(m['DSSPType'])
            DSSPExposures.add(m['DSSPExposure'])

            # Burial
            if m['DSSPExposure'] != None:
                if m['DSSPExposure'] > burial_cutoff:
                    exposures.add('E')
                else:
                    exposures.add('B')
            else:
                exposures.add(None)

            # Volume
            if amino_acid_details[wtaa]['van der Waals volume'] < amino_acid_details[mutaa]['van der Waals volume']:
                volume_changes.add('SL')
            elif amino_acid_details[wtaa]['van der Waals volume'] > amino_acid_details[mutaa]['van der Waals volume']:
                volume_changes.add('LS')
            elif amino_acid_details[wtaa]['van der Waals volume'] == amino_acid_details[mutaa]['van der Waals volume']:
                volume_changes.add('XX')

            # Charge
            if ((wtaa in CAA or wtaa in PAA) and (mutaa in HAA)) or ((mutaa in CAA or mutaa in PAA) and (wtaa in HAA)):
                residue_charges.add('Change')
            elif (wtaa in CAA or wtaa in PAA) and (mutaa in CAA or mutaa in PAA):
                residue_charges.add('Polar/Charged')
            elif (wtaa in HAA) and (mutaa in HAA):
                residue_charges.add('Hydrophobic/Non-polar')
            else:
                 raise colortext.Exception('Should not reach here.')

        # Create a string representing the mutations (useful for labeling rather than analysis)
        mutation_string = '; '.join(mutation_string)

        # Taking unique values, determine the residue charges of the wildtype and mutant residues, the wildtype residue exposure, and the relative change in van der Waals volume
        if len(residue_charges) == 1: residue_charge = residue_charges.pop()
        if len(exposures) == 1: exposure = exposures.pop()
        if len(volume_changes) == 1: volume_change = volume_changes.pop()

        # Taking unique values, determine the wildtype and mutant residue types
        all_residues = wtaas.union(mutaas)
        if len(wtaas) == 1: record_wtaa = wtaas.pop()
        if len(mutaas) == 1: record_mutaa = mutaas.pop()

        # Taking unique values, determine the secondary structure and residue exposures from the DSSP data in the dataset
        if len(DSSPSimpleSSTypes) == 1: DSSPSimpleSSType = DSSPSimpleSSTypes.pop()
        if len(DSSPTypes) == 1: DSSPType = DSSPTypes.pop()
        if len(DSSPExposures) == 1: DSSPExposure = DSSPExposures.pop()

        # Determine the SCOP classification from the SCOPe data in the dataset
        full_scop_classification, scop_class, scop_fold = None, None, None
        if len(scops) > 1:
            self.log('Warning: There is more than one SCOPe class for record {0}.'.format(record_id), colortext.warning)
        elif len(scops) == 1:
            full_scop_classification = scops.pop()
            scop_tokens = full_scop_classification.split('.')
            scop_class = scop_tokens[0]
            if len(scop_tokens) > 1:
                scop_fold = '.'.join(scop_tokens[0:2])

        # Partition the data by PDB resolution with bins: N/A, <1.5, 1.5-<2.0, 2.0-<2.5, >=2.5
        pdb_record = pdb_data.get(self.get_record_pdb_file_id(record).upper())
        pdb_resolution_bin = None
        pdb_resolution = pdb_record.get('Resolution')
        if pdb_resolution != None:
            if pdb_resolution < 1.5:
                pdb_resolution_bin = '<1.5'
            elif pdb_resolution < 2.0:
                pdb_resolution_bin = '1.5-2.0'
            elif pdb_resolution < 2.5:
                pdb_resolution_bin = '2.0-2.5'
            else:
                pdb_resolution_bin = '>=2.5'
        pdb_resolution_bin = pdb_resolution_bin or 'N/A'

        # Mark mutations involving glycine or proline
        has_gp_mutation = 'G' in all_residues or 'P' in all_residues

        # Create the data matrix
        dataframe_record = dict(
            DatasetID = record_id,
            PDBFileID = self.get_record_pdb_file_id(record),
            Mutations = mutation_string,
            NumberOfMutations = len(mutations),
            Predicted = predicted_data[self.ddg_analysis_type],
            ResidueCharges = residue_charge,
            VolumeChange = volume_change,
            HasGPMutation = int(has_gp_mutation),
            WildTypeDSSPType = DSSPType,
            WildTypeDSSPSimpleSSType = DSSPSimpleSSType,
            WildTypeDSSPExposure = DSSPExposure,
            WildTypeSCOPClass = scop_class,
            WildTypeSCOPFold = scop_fold,
            WildTypeSCOPClassification = full_scop_classification,
            WildTypeExposure = exposure,
            WildTypeAA = record_wtaa,
            MutantAA = record_mutaa,
            PDBResolution = pdb_record.get('Resolution'),
            PDBResolutionBin = pdb_resolution_bin,
            NumberOfResidues = self.count_residues(record, pdb_record) or None,
            NumberOfDerivativeErrors = num_derivative_errors,
            RunTime = run_time,
            MaxMemory = max_memory,
            )
        for c in additional_prediction_data_columns:
            dataframe_record[c] = predicted_data.get(c)

        if self.contains_experimental_data:
            # These fields are particular to dataframes containing experimental values e.g. for benchmarking runs or for
            # datasets where we have associated experimental values
            self.get_experimental_ddg_values(record, dataframe_record)
            self.compute_stability_classification(predicted_data, record, dataframe_record)
            self.compute_absolute_error(predicted_data, record, dataframe_record)

        return dataframe_record


    def analyze_all(self, analysis_directory = None):
        '''This function runs the analysis and creates the plots and summary file.'''
        for analysis_set in self.analysis_sets:
            self.analyze(analysis_set, analysis_directory = analysis_directory)


    def analyze(self, analysis_set = '', analysis_directory = None):
        '''This function runs the analysis and creates the plots and summary file.'''
        self.calculate_metrics(analysis_set, analysis_directory = analysis_directory)
        if self.generate_plots:
            self.plot(analysis_set, analysis_directory = analysis_directory)


    def full_analysis(self, analysis_set, output_directory, verbose = True, compile_pdf = True, quick_plots = False):
        '''Combines calculate_metrics, write_dataframe_to_csv, and plot'''
        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)
        self.analysis_directory = output_directory
        self.calculate_metrics(analysis_set = analysis_set, analysis_directory = output_directory, verbose = verbose)
        self.write_dataframe_to_csv( os.path.join(output_directory, 'data.csv') )

        # Return latex_report
        return self.plot(analysis_set = analysis_set, analysis_directory = output_directory, matplotlib_plots = True, verbose = verbose, compile_pdf = compile_pdf, quick_plots = quick_plots)


    def get_definitive_name(self, unique_ajps, join_character = '-', prepend_label = True):
        """
        Generates a definitive name for this benchmark run object, based on
        unique additional join parameters (as passed)
        """
        name = ''
        for ajp in unique_ajps:
            if len(name) > 0:
                name += join_character
            if prepend_label:
                name += str(ajp) + '_'
            name += str(self.additional_join_parameters[ajp]['short_name'])
        if name == '':
            name = 'ddg-benchmark'
        return name


    @staticmethod
    def get_unique_ajps( benchmark_runs ):
        """
        Determines which join parameters are unique
        """
        br_ajps = {}
        for br in benchmark_runs:
            for ajp in br.additional_join_parameters:
                if ajp not in br_ajps:
                    br_ajps[ajp] = set()
                br_ajps[ajp].add( br.additional_join_parameters[ajp]['short_name'] )
        unique_ajps = []
        for ajp in br_ajps:
            if len( br_ajps[ajp] ) > 1:
                unique_ajps.append( ajp )
        return unique_ajps


    @staticmethod
    def analyze_multiple(
            benchmark_runs,
            analysis_sets = [],
            # Singleton arguments
            analysis_directory = None,
            remove_existing_analysis_directory = True,
            quick_plots = False,
            use_multiprocessing = True,
            verbose = True,
            compile_pdf = True,
            limit_to_complete_presence = True,
            all_by_all_comparisons = False,
    ):
        '''This function runs the analysis for multiple input settings'''
        if remove_existing_analysis_directory and os.path.isdir(analysis_directory):
            shutil.rmtree(analysis_directory)

        unique_ajps = BenchmarkRun.get_unique_ajps( benchmark_runs )

        if limit_to_complete_presence:
            common_ids = set( benchmark_runs[0].dataframe.dropna(subset=['Predicted'])[['DatasetID']].as_matrix().flatten() )
            for br in benchmark_runs[1:]:
                common_ids = common_ids.intersection( set(br.dataframe.dropna(subset=['Predicted'])[['DatasetID']].as_matrix().flatten()) )
            print 'Common dataset size will be:', len(common_ids)
            if len(common_ids) == 0:
                for br in benchmark_runs:
                    common_ids = sorted( list( br.dataframe.dropna(subset=['Predicted'])[['DatasetID']].as_matrix().flatten() ) )
                    print br.get_definitive_name(unique_ajps, join_character = '-'), common_ids[:10]
                raise Exception('No data to make report on!')
            # limited_benchmark_runs = []
            for br in benchmark_runs:
                br.set_dataframe( br.dataframe.loc[br.dataframe['DatasetID'].isin(common_ids)], verbose = use_multiprocessing )
                # limited_benchmark_runs.append( br )
            # benchmark_runs = limited_benchmark_runs

        unique_ajps = BenchmarkRun.get_unique_ajps( benchmark_runs )

        ###  Process each benchmark run object individually
        if use_multiprocessing:
            pool = mp.Pool()
        singleton_chapters = []
        calculated_brs = []
        def save_latex_report(t):
            br, unique_name, latex_report = t
            latex_report.set_title_page( title = unique_name )
            singleton_chapters.append( latex_report )
            calculated_brs.append( br )
        for br in benchmark_runs:
            for analysis_set in analysis_sets:
                unique_name = br.get_definitive_name(unique_ajps, join_character = '\n')
                filepath_unique_name = br.get_definitive_name(unique_ajps, join_character = '-')
                subdir = os.path.join(analysis_directory, os.path.join('analysis_sets', os.path.join(analysis_set, filepath_unique_name) ) )
                if use_multiprocessing:
                    pool.apply_async( _full_analysis_mp_alias, ( br, analysis_set, subdir, unique_name, False, quick_plots ), callback = save_latex_report )
                else:
                    print 'Individual report saving in:', subdir
                    save_latex_report( _full_analysis_mp_alias( br, analysis_set, subdir, unique_name, True, quick_plots ) )
        if use_multiprocessing:
            pool.close()
            pool.join()
        benchmark_runs = calculated_brs

        ### Pointwise all-by-all comparison
        comparison_chapters = []
        if all_by_all_comparisons:
            if use_multiprocessing:
                pool = mp.Pool()
            def save_latex_report(t):
                latex_report = t
                comparison_chapters.append( latex_report )
            comparisons_subdir = os.path.join(analysis_directory, 'comparison_analysis_sets')
            for analysis_set in analysis_sets:
                analysis_set_subdir = os.path.join(comparisons_subdir, analysis_set)
                for i, br_i in enumerate(benchmark_runs):
                    for j, br_j in enumerate(benchmark_runs):
                        if i > j:
                            if use_multiprocessing:
                                br_i_copy = copy.deepcopy( br_i )
                                br_j_copy = copy.deepcopy( br_j )
                                pool.apply_async( _compare_mp_alias, (br_i_copy, br_j_copy, analysis_set, analysis_set_subdir, unique_ajps, False), callback = save_latex_report )
                            else:
                                save_latex_report( _compare_mp_alias(br_i, br_j, analysis_set, analysis_set_subdir, unique_ajps, True) )
            if use_multiprocessing:
                pool.close()
                pool.join()

        intro_report = lr.LatexReport()
        intro_report.set_title_page('All data comparison')
        # All data series comparison
        # Get joined stats comparison dataframe
        stats_df = BenchmarkRun.get_stats_comparison_dataframe(
            benchmark_runs, unique_ajps,
            output_csv = os.path.join(analysis_directory, 'analysis_metrics.csv'),
        )
        intro_report.add_section_page( title = 'Case comparison tables' )
        intro_report.content.extend( BenchmarkRun.make_case_description_tables( stats_df ) )

        intro_report.add_section_page('All data plots')
        subplot_directory = os.path.join(analysis_directory, 'subplots')
        if not os.path.isdir( subplot_directory ):
            os.makedirs(subplot_directory)
        runtime_df = benchmark_runs[0]._get_dataframe_columns( ['RunTime'] )
        runtime_df.columns = [ benchmark_runs[0].get_definitive_name(unique_ajps, join_character = '\n', prepend_label = False) ]
        for br in benchmark_runs[1:]:
            inner_runtime_df = br._get_dataframe_columns( ['RunTime'] )
            inner_runtime_df.columns = [ br.get_definitive_name(unique_ajps, join_character = '\n', prepend_label = False) ]
            runtime_df = runtime_df.merge(
                inner_runtime_df,
                left_index = True,
                right_index = True,
            )

        intro_report.add_plot(
            general_matplotlib.plot_box(
                runtime_df,
                output_directory = subplot_directory,
                plot_title = 'Prediction Run Times',
                output_name = 'runtimes',
                fig_height = 6.7,
                fig_width = 10,
                ylabel = 'Run time (minutes)',
                xlabel = 'Prediction Set',
                verbose = verbose,
                xtick_fontsize = 4,
                log_y = True,
                label_n = False,
                rotation_angle = 45,
            ),
            plot_title = 'Run times'
        )

        # Report concatenation
        main_latex_report = lr.LatexReport()
        main_latex_report.set_title_page('$\Delta\Delta G$ Report')
        main_latex_report.add_chapter(intro_report)
        for chapter in comparison_chapters:
            main_latex_report.add_chapter(chapter)
        for chapter in singleton_chapters:
            main_latex_report.add_chapter(chapter)
        main_latex_report.generate_pdf_report(
            os.path.join( analysis_directory, 'report.pdf' ),
            verbose = verbose,
            compile_pdf = compile_pdf,
        )
        print os.path.join( analysis_directory, 'report.pdf' )


    def compare(self, other, analysis_set, output_directory, unique_ajps, verbose = True, compile_pdf = True):
        """
        Generate comparison latex report in specified output directory
        Returns LatexReport object
        """
        self_unique_name = self.get_definitive_name(unique_ajps)
        other_unique_name = other.get_definitive_name(unique_ajps)

        output_directory = os.path.join(output_directory, os.path.join(self_unique_name, other_unique_name) )
        assert( not os.path.isdir( output_directory ) )

        subplot_directory = os.path.join(output_directory, 'plots')
        if not os.path.isdir(subplot_directory):
            os.makedirs(subplot_directory)

        report = lr.LatexReport( table_of_contents = False )

        # Construct dataframe comparing our predictions to other's predictions
        both_predictions = pandas.concat(
            [
                self.add_identifying_columns_to_df(self.dataframe[['Predicted']], unique_ajps),
                other.add_identifying_columns_to_df(other.dataframe[['Predicted']], unique_ajps),
            ],
            join = 'outer',
        ).sort_index()
        both_predictions_subtracted = subtract_row_pairs_for_display(
            both_predictions,
            output_csv = os.path.join(output_directory, 'predictions_v_predictions.csv'),
            merge_df = self.dataframe,
            verbose = verbose,
        )

        # Construct dataframe comparing our diff with experimental values to other's
        self_diff = self.get_pred_minus_exp_dataframe(analysis_set, unique_ajps)
        other_diff = other.get_pred_minus_exp_dataframe(analysis_set, unique_ajps)
        diffs_df = pandas.concat(
            [self_diff, other_diff],
            join = 'outer',
        )

        diffs_df = subtract_row_pairs_for_display(
            diffs_df,
            output_csv = os.path.join(output_directory, 'diffs_v_diffs.csv'),
            merge_df = self.dataframe,
            verbose = verbose,
        )

        report.set_title_page(
            '%s vs %s' % (
                self.get_definitive_name(unique_ajps, join_character = '\n'),
                other.get_definitive_name(unique_ajps, join_character = '\n')
            )
        )
        predictions_v_predictions_df = self.dataframe[['Predicted']].merge(
            other.dataframe[['Predicted']],
            left_index = True,
            right_index = True,
        )
        predictions_v_predictions_df.columns = [self_unique_name, other_unique_name]
        report.add_plot( general_matplotlib.make_corr_plot(predictions_v_predictions_df, predictions_v_predictions_df.columns.values[0], predictions_v_predictions_df.columns.values[1], output_directory = self.subplot_directory, plot_title = 'Prediction comparison', axis_label_size = 8.0, output_name = 'vs_scatter', fig_height = 7, fig_width = 8, verbose = verbose, plot_11_line = True ), plot_title = 'Experimental vs. Predicted scatterplot (with density binning)' )

        diff_v_diff_dataframe = self.get_pred_minus_exp_dataframe(analysis_set).merge(
            other.get_pred_minus_exp_dataframe(analysis_set),
            left_index = True,
            right_index = True,
        )
        report.add_section_page( title = 'Plots' )
        diff_v_diff_dataframe.columns = [self_unique_name, other_unique_name]
        report.add_plot( general_matplotlib.make_corr_plot(diff_v_diff_dataframe, diff_v_diff_dataframe.columns.values[0], diff_v_diff_dataframe.columns.values[1], output_directory = self.subplot_directory, plot_title = 'Error v. Error', axis_label_size = 7.0, output_name = 'diff_vs_scatter', fig_height = 7, fig_width = 8, verbose = verbose, plot_11_line = True ), plot_title = 'Outliers --- Error (Predicted - Experimental) v. error. \\ x-axis=%s \\ y-axis=%s' % (diff_v_diff_dataframe.columns.values[0], diff_v_diff_dataframe.columns.values[1]) )

        report.add_section_page( title = 'Tables' )

        report.content.append( lr.LatexPandasTable(
            diffs_df, float_format = float_format_2sigfig,
            caption_text = 'Outliers --- Comparison of error (Predicted - Experimental) for first prediction set (%s) vs second set of predictions (%s). Values sorted by descending absolute delta.' % (self_unique_name, other_unique_name),
        ) )

        report.content.append( lr.LatexPandasTable(
            both_predictions_subtracted, float_format = float_format_2sigfig,
            caption_text = 'Direct comparison of predicted values. Values sorted by descending absolute delta.',
        ) )

        # Get joined stats comparison dataframe
        for case_table in BenchmarkRun.make_case_description_tables(BenchmarkRun.get_stats_comparison_dataframe(
                [self, other], unique_ajps,
                output_csv = os.path.join(output_directory, 'comparison_metrics.csv'),
        )):
            report.content.append( case_table )

        report.generate_pdf_report(
            os.path.join(output_directory, 'comparison.pdf'),
            verbose = verbose,
            compile_pdf = compile_pdf,
        )
        if verbose:
            print 'Comparison report saved to:', os.path.join(output_directory, 'comparison.pdf')
        return report


    @staticmethod
    def make_case_description_tables(stats_df, sort_by = "Pearson's R"):
        stats_columns = ['n', 'Fraction correct', "Pearson's R", 'MAE']
        stats_columns_names = ['n', 'FC', "R", 'MAE']
        select_columns = list( stats_columns )
        select_columns.append( 'case_description' )
        stats_df = stats_df[ select_columns ]
        # Put tables for complete datasets first
        first_cases_to_process = set( ['complete dataset', 'complete dataset (scaled)'] )
        other_cases = set( stats_df['case_description'].unique() )
        first_cases_to_process.intersection_update( other_cases )
        other_cases.difference_update( first_cases_to_process )
        other_cases = sorted( list( other_cases ) )
        cases = sorted( list( first_cases_to_process ) )
        cases.extend( other_cases)
        # Make subcase tables
        report_content = []
        for case in cases:
            if case == 'complete dataset (scaled)':
                inner_sort_by = 'MAE'
                sort_ascending = True
            else:
                inner_sort_by = sort_by
                sort_ascending = False
            inner_df = stats_df[ stats_df['case_description'] == case ]
            inner_df = inner_df.sort_values(by = inner_sort_by, ascending = sort_ascending)
            inner_df = inner_df[ stats_columns ]
            inner_df.columns = stats_columns_names
            report_content.append( lr.LatexPandasTable(
                inner_df,
                float_format = float_format_3sigfig,
                caption_text = case + ". Abbreviations: FC = fraction correct, R = Pearson's R" ,
            ) )
        return report_content


    @staticmethod
    def make_specific_case_table(stats_df, case, sort_by = "Pearson's R"):
        stats_columns = ['n', 'Fraction correct', "Pearson's R", 'MAE']
        stats_columns_names = ['n', 'FC', "R", 'MAE']
        select_columns = list( stats_columns )
        select_columns.append('case_description')
        stats_df = stats_df[ select_columns ]

        inner_df = stats_df[ stats_df['case_description'] == case ]
        inner_df = inner_df.sort_values(by = sort_by, ascending = False)
        inner_df = inner_df[ stats_columns ]
        inner_df.columns = stats_columns_names
        return lr.LatexPandasTable(
            inner_df,
            float_format = float_format_3sigfig,
            caption_text = case + ". Abbreviations: FC = fraction correct, R = Pearson's R" ,
        )


    @staticmethod
    def get_stats_comparison_dataframe(benchmark_runs, unique_ajps, output_csv = None):
        annotated_stats_dfs = [
            br.add_identifying_columns_to_df(
                br.stored_metrics_df,
                unique_ajps,
                reset_index = True,
            )
            for br in benchmark_runs
        ]
        stats_df = pandas.concat(annotated_stats_dfs)
        stats_df = stats_df.sort_index()
        if output_csv:
            stats_df.to_csv( output_csv )
        return stats_df

    def get_pred_minus_exp_dataframe(self, analysis_set, unique_ajps = None):
        exp_name = BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set)
        return_df = self.dataframe['Predicted'].subtract( self.dataframe[exp_name] ).to_frame()
        return_df.columns = ['delta' + '-' + exp_name]
        return_df.index.name = 'ID'
        if unique_ajps:
            return self.add_identifying_columns_to_df(return_df, unique_ajps)
        else:
            return return_df


    def add_identifying_columns_to_df(self, df, unique_ajps, reset_index = False):
        if not reset_index:
            df.index.name = 'ID'
        for ajp in unique_ajps:
            df[ajp] = self.additional_join_parameters[ajp]['short_name']
            df.set_index(ajp, append = True, inplace = True)
        if reset_index:
            df = df.reset_index( level = 0 ).drop('level_0', axis = 1)
        return df


    def calculate_metrics(self, analysis_set = '', analysis_directory = None, drop_missing = True, case_n_cutoff = 5, verbose = True):
        '''Calculates the main metrics for the benchmark run and writes them to file and LaTeX object.'''

        dataframe = self.dataframe
        if drop_missing:
            dataframe = dataframe.dropna(subset=['Predicted'])

        if self.calculate_scalar_adjustments:
            scalar_adjustment = self.scalar_adjustments[analysis_set]
        experimental_field = BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set)

        self.metric_latex_objects.append( lr.LatexPageSection('Data tables', None, True) )
        intro_text = lr.LatexText( text = self.ddg_analysis_type_description )
        header_row = ['Statistic name', '{Value}', 'p-value']
        stats_column_format = ['l', 'S[table-format=3.2]', 'l']

        if self.include_derived_mutations:
            running_analysis_str = '\nDerived mutations in analysis are included):'
        else:
            running_analysis_str = '\nDerived mutations in analysis are omitted):'
        intro_text.add_text(running_analysis_str)
        if verbose:
            self.report(running_analysis_str, fn = colortext.message)

        classification_cutoffs_str = 'The stability classification cutoffs are: Experimental=%0.2f kcal/mol, Predicted=%0.2f energy units.' % (self.stability_classication_x_cutoff, self.stability_classication_y_cutoff)
        intro_text.add_text( classification_cutoffs_str )
        if verbose:
            self.report(classification_cutoffs_str, fn = colortext.warning)

        self.metric_latex_objects.append( intro_text )

        amino_acid_details, CAA, PAA, HAA = self.amino_acid_details, self.CAA, self.PAA, self.HAA

        # This dict is used for the print-statement below
        volume_groups = {}
        for aa_code, aa_details in amino_acid_details.iteritems():
            v = int(aa_details['van der Waals volume']) # Note: I only convert to int here to match the old script behavior and because all volumes are integer values so it does not do any harm
            volume_groups[v] = volume_groups.get(v, [])
            volume_groups[v].append(aa_code)

        section_latex_objs = []
        section_latex_objs.append( lr.LatexSubSection(
            'Breakdown by volume',
            'A case is considered a small-to-large (resp. large-to-small) mutation if all of the wildtype residues have a smaller (resp. larger) van der Waals volume than the corresponding mutant residue. The order is defined as %s so some cases are considered to have no change in volume e.g. MET -> LEU.' % (' < '.join([''.join(sorted(v)) for k, v in sorted(volume_groups.iteritems())]))
        ) )
        for subcase in ('XX', 'SL', 'LS'):
            subcase_dataframe = dataframe[dataframe['VolumeChange'] == subcase]
            table_header = 'Statistics - %s (%d cases)' % (BenchmarkRun.by_volume_descriptions[subcase], len(subcase_dataframe))
            if len(subcase_dataframe) >= 8:
                list_stats = format_stats(get_xy_dataset_statistics_pandas(subcase_dataframe, experimental_field, 'Predicted', fcorrect_x_cutoff = self.stability_classication_x_cutoff, fcorrect_y_cutoff = self.stability_classication_y_cutoff, ignore_null_values = True, run_standardized_analysis = False), return_string = False)
                section_latex_objs.append( lr.LatexTable(
                    header_row,
                    list_stats,
                    column_format = stats_column_format,
                    header_text = table_header
                ))
                self.add_stored_metric_to_df(BenchmarkRun.by_volume_descriptions[subcase], len(subcase_dataframe), list_stats)
            else:
                section_latex_objs.append( lr.LatexText(
                    'Not enough data for analysis of mutations ''%s'' (at least 8 cases are required).' % BenchmarkRun.by_volume_descriptions[subcase]
                ))
        if verbose:
            self.report('\n'.join([x.generate_plaintext() for x in section_latex_objs]), fn = colortext.sprint)
        self.metric_latex_objects.extend( section_latex_objs )


        section_latex_objs = []
        section_latex_objs.append( lr.LatexSubSection(
            'Mutations to alanine',
            'And mutations not to alanine'
        ))
        subcase_dataframe = dataframe[dataframe['MutantAA'] == 'A']
        if len(subcase_dataframe) > 0:
            table_header = 'Statistics - all mutations to alanine (including multiple mutations, if they are all to alanine) (%d cases)' % len(subcase_dataframe)
            list_stats = format_stats(get_xy_dataset_statistics_pandas(subcase_dataframe, experimental_field, 'Predicted', fcorrect_x_cutoff = self.stability_classication_x_cutoff, fcorrect_y_cutoff = self.stability_classication_y_cutoff, ignore_null_values = True, run_standardized_analysis = False), return_string = False)
            section_latex_objs.append( lr.LatexTable(
                header_row,
                list_stats,
                column_format = stats_column_format,
                header_text = table_header
            ))
            self.add_stored_metric_to_df('all mutations to alanine', len(subcase_dataframe), list_stats)

        subcase_dataframe = dataframe[(dataframe['MutantAA'] == 'A') & (dataframe['NumberOfMutations'] == 1)]
        if len(subcase_dataframe) > 0:
            table_header = 'Statistics - single mutations to alanine (%d cases)' % len(subcase_dataframe)
            list_stats = format_stats(get_xy_dataset_statistics_pandas(subcase_dataframe, experimental_field, 'Predicted', fcorrect_x_cutoff = self.stability_classication_x_cutoff, fcorrect_y_cutoff = self.stability_classication_y_cutoff, ignore_null_values = True, run_standardized_analysis = False), return_string = False)
            section_latex_objs.append( lr.LatexTable(
                header_row,
                list_stats,
                column_format = stats_column_format,
                header_text = table_header
            ))
            self.add_stored_metric_to_df('single mutations to alanine', len(subcase_dataframe), list_stats)

        subcase_dataframe = dataframe[(dataframe['MutantAA'] == 'A') & (dataframe['NumberOfMutations'] != 1)]
        if len(subcase_dataframe) > 0:
            table_header = 'Statistics - multiple mutations to alanine (%d cases)' % len(subcase_dataframe)
            list_stats = format_stats(get_xy_dataset_statistics_pandas(subcase_dataframe, experimental_field, 'Predicted', fcorrect_x_cutoff = self.stability_classication_x_cutoff, fcorrect_y_cutoff = self.stability_classication_y_cutoff, ignore_null_values = True, run_standardized_analysis = False), return_string = False)
            section_latex_objs.append( lr.LatexTable(
                header_row,
                list_stats,
                column_format = stats_column_format,
                header_text = table_header
            ))
            self.add_stored_metric_to_df('multiple mutations to alanine', len(subcase_dataframe), list_stats)

        subcase_dataframe = dataframe[dataframe['MutantAA'] != 'A']
        if len(subcase_dataframe) > 0:
            table_header = 'Statistics - mutations to anything other than alanine (including multiple mutations that include a non-alanine mutation) (%d cases)' % len(subcase_dataframe)
            list_stats = format_stats(get_xy_dataset_statistics_pandas(subcase_dataframe, experimental_field, 'Predicted', fcorrect_x_cutoff = self.stability_classication_x_cutoff, fcorrect_y_cutoff = self.stability_classication_y_cutoff, ignore_null_values = True, run_standardized_analysis = False), return_string = False)
            section_latex_objs.append( lr.LatexTable(
                header_row,
                list_stats,
                column_format = stats_column_format,
                header_text = table_header
            ))
            self.add_stored_metric_to_df('mutations not to alanine', len(subcase_dataframe), list_stats)
        if verbose and len(section_latex_objs) > 0:
            self.report('\n'.join([x.generate_plaintext() for x in section_latex_objs]), fn = colortext.sprint)
        self.metric_latex_objects.extend( section_latex_objs )


        section_latex_objs = []
        subcase_dataframe = dataframe[dataframe['HasGPMutation'] == 1]
        if len(subcase_dataframe) > 0:
            table_header = 'Statistics - cases with G or P (%d cases)' % len(subcase_dataframe)
            list_stats = format_stats(get_xy_dataset_statistics_pandas(subcase_dataframe, experimental_field, 'Predicted', fcorrect_x_cutoff = self.stability_classication_x_cutoff, fcorrect_y_cutoff = self.stability_classication_y_cutoff, ignore_null_values = True, run_standardized_analysis = False), return_string = False)
            section_latex_objs.append( lr.LatexTable(
                header_row,
                list_stats,
                column_format = stats_column_format,
                header_text = table_header
            ))
            self.add_stored_metric_to_df('cases with G or P', len(subcase_dataframe), list_stats)

        subcase_dataframe = dataframe[dataframe['HasGPMutation'] == 0]
        if len(subcase_dataframe) > 0:
            table_header = 'Statistics - cases without G or P (%d cases)' % len(subcase_dataframe)
            list_stats = format_stats(get_xy_dataset_statistics_pandas(subcase_dataframe, experimental_field, 'Predicted', fcorrect_x_cutoff = self.stability_classication_x_cutoff, fcorrect_y_cutoff = self.stability_classication_y_cutoff, ignore_null_values = True, run_standardized_analysis = False), return_string = False)
            section_latex_objs.append( lr.LatexTable(
                header_row,
                list_stats,
                column_format = stats_column_format,
                header_text = table_header
            ))
            self.add_stored_metric_to_df('cases without G or P', len(subcase_dataframe), list_stats)

        if len(section_latex_objs) > 0:
            section_latex_objs.insert( 0, lr.LatexSubSection(
                'Separating out mutations involving glycine or proline.',
                'This cases may involve changes to secondary structure so we separate them out here.'
            ))

        if verbose and len(section_latex_objs) > 0:
            self.report('\n'.join([x.generate_plaintext() for x in section_latex_objs]), fn = colortext.sprint)
        self.metric_latex_objects.extend( section_latex_objs )

        #### Single mutations
        section_latex_objs = []
        section_latex_objs.append( lr.LatexSubSection(
            'Number of mutations',
        ))
        subcase_dataframe = dataframe[dataframe['NumberOfMutations'] == 1]
        if len(subcase_dataframe) >= case_n_cutoff:
            table_header = 'Statistics - single mutations (%d cases)' % len(subcase_dataframe)
            list_stats = format_stats(get_xy_dataset_statistics_pandas(subcase_dataframe, experimental_field, 'Predicted', fcorrect_x_cutoff = self.stability_classication_x_cutoff, fcorrect_y_cutoff = self.stability_classication_x_cutoff, ignore_null_values = True, run_standardized_analysis = False), return_string = False)
            section_latex_objs.append( lr.LatexTable(
                header_row,
                list_stats,
                column_format = stats_column_format,
                header_text = table_header
            ))
            self.add_stored_metric_to_df('single mutations', len(subcase_dataframe), list_stats)
        subcase_dataframe = dataframe[dataframe['NumberOfMutations'] > 1]
        if len(subcase_dataframe) >= case_n_cutoff:
            table_header = 'Statistics - multiple mutations (%d cases)' % len(subcase_dataframe)
            list_stats = format_stats(get_xy_dataset_statistics_pandas(subcase_dataframe, experimental_field, 'Predicted', fcorrect_x_cutoff = self.stability_classication_x_cutoff, fcorrect_y_cutoff = self.stability_classication_x_cutoff, ignore_null_values = True, run_standardized_analysis = False), return_string = False)
            section_latex_objs.append( lr.LatexTable(
                header_row,
                list_stats,
                column_format = stats_column_format,
                header_text = table_header
            ))
            self.add_stored_metric_to_df('multiple mutations', len(subcase_dataframe), list_stats)
        # subcase_dataframe = dataframe[(dataframe.NumberOfMutations >= 2) & (dataframe.NumberOfMutations <= 5)]
        # if len(subcase_dataframe) >= case_n_cutoff:
        #     table_header = 'Statistics - 2-4 mutations (%d cases)' % len(subcase_dataframe)
        #     list_stats = format_stats(get_xy_dataset_statistics_pandas(subcase_dataframe, experimental_field, 'Predicted', fcorrect_x_cutoff = self.stability_classication_x_cutoff, fcorrect_y_cutoff = self.stability_classication_x_cutoff, ignore_null_values = True, run_standardized_analysis = False), return_string = False)
        #     section_latex_objs.append( LatexTable(
        #         header_row,
        #         list_stats,
        #         column_format = stats_column_format,
        #         header_text = table_header
        #     ))
        #     self.add_stored_metric_to_df('2-4 mutations', len(subcase_dataframe), list_stats)
        # mutation_cutoffs = [5, 10, 20, 50, 100, 200]
        # for i, mutation_cutoff in enumerate(mutation_cutoffs):
        #     if len(mutation_cutoffs) - 1 == i:
        #         break
        #     next_cutoff = mutation_cutoffs[i+1]
        #     subcase_dataframe = dataframe[(dataframe.NumberOfMutations >= mutation_cutoff) & (dataframe.NumberOfMutations <= next_cutoff)]
        #     if len(subcase_dataframe) >= case_n_cutoff:
        #         table_header = 'Statistics - %d $<=$ number of mutations $<=$ %d (%d cases)' % (mutation_cutoff, next_cutoff, len(subcase_dataframe))
        #         list_stats = format_stats(get_xy_dataset_statistics_pandas(subcase_dataframe, experimental_field, 'Predicted', fcorrect_x_cutoff = self.stability_classication_x_cutoff, fcorrect_y_cutoff = self.stability_classication_x_cutoff, ignore_null_values = True, run_standardized_analysis = False), return_string = False)
        #         section_latex_objs.append( LatexTable(
        #             header_row,
        #             list_stats,
        #             column_format = stats_column_format,
        #             header_text = table_header
        #         ))
        #         self.add_stored_metric_to_df('%d <= mutations<= %d' % (mutation_cutoff, next_cutoff), len(subcase_dataframe), list_stats)
        if verbose:
            self.report('\n'.join([x.generate_plaintext() for x in section_latex_objs]), fn = colortext.sprint)
        self.metric_latex_objects.extend( section_latex_objs )
        ####

        #### Complete dataset (scaled)
        if self.calculate_scalar_adjustments:
            section_latex_objs = []
            section_latex_objs.append( lr.LatexSubSection(
                'Entire dataset using a scaling factor of 1/%.03f to improve the fraction correct metric.' % scalar_adjustment,
                'Warning: Results in this section use an averaged scaling factor to improve the value for the fraction correct metric. This scalar will vary over benchmark runs so these results should not be interpreted as performance results; they should be considered as what could be obtained if the predicted values were scaled by a "magic" value.'
            ))
            table_header = 'Statistics - complete dataset (scaled) (%d cases)' % len(dataframe)
            # For these statistics, we assume that we have reduced any scaling issues and use the same cutoff for the Y-axis as the user specified for the X-axis
            list_stats = format_stats(get_xy_dataset_statistics_pandas(dataframe, experimental_field, BenchmarkRun.get_analysis_set_fieldname('Predicted_adj', analysis_set), fcorrect_x_cutoff = self.stability_classication_x_cutoff, fcorrect_y_cutoff = self.stability_classication_x_cutoff, ignore_null_values = True, run_standardized_analysis = False), return_string = False)
            section_latex_objs.append( lr.LatexTable(
                header_row,
                list_stats,
                column_format = stats_column_format,
                header_text = table_header
            ))
            self.add_stored_metric_to_df('complete dataset (scaled)', len(dataframe), list_stats)
            if verbose:
                self.report('\n'.join([x.generate_plaintext() for x in section_latex_objs]), fn = colortext.sprint)
            self.metric_latex_objects.extend( section_latex_objs )
        ####

        section_latex_objs = []
        section_latex_objs.append( lr.LatexSubSection(
            'Entire dataset',
            'Overall statistics'
        ))
        table_header = 'Statistics - complete dataset (%d cases)' % len(dataframe)
        # For these statistics, we assume that we have reduced any scaling issues and use the same cutoff for the Y-axis as the user specified for the X-axis
        list_stats = format_stats(get_xy_dataset_statistics_pandas(dataframe, experimental_field, 'Predicted', fcorrect_x_cutoff = self.stability_classication_x_cutoff, fcorrect_y_cutoff = self.stability_classication_x_cutoff, ignore_null_values = True, run_standardized_analysis = False), return_string = False)
        section_latex_objs.append( lr.LatexTable(
            header_row,
            list_stats,
            column_format = stats_column_format,
            header_text = table_header
        ))
        self.add_stored_metric_to_df('complete dataset', len(dataframe), list_stats)
        if verbose:
            self.report('\n'.join([x.generate_plaintext() for x in section_latex_objs]), fn = colortext.sprint)
        self.metric_latex_objects.extend( section_latex_objs )

        # There is probably a better way of writing the pandas code here
        record_with_most_errors = (dataframe[['PDBFileID', 'NumberOfDerivativeErrors', 'Mutations']].sort_values(by = 'NumberOfDerivativeErrors')).tail(1)
        record_index = record_with_most_errors.index.tolist()[0]
        pdb_id, num_errors, mutation_str = dataframe.loc[record_index, 'PDBFileID'], dataframe.loc[record_index, 'NumberOfDerivativeErrors'], dataframe.loc[record_index, 'Mutations']
        if num_errors > 0:
            error_detection_text = '\n\nDerivative errors were found in the run. Record #{0} - {1}, {2} - has the most amount ({3}) of derivative errors.'.format(record_index, pdb_id, mutation_str, num_errors)
            self.metric_latex_objects.append( lr.LatexText(error_detection_text, color = 'red') )
            if verbose:
                self.report(error_detection_text, fn = colortext.warning)

        # Write the analysis to file
        self.create_analysis_directory(analysis_directory)
        self.metrics_filepath = os.path.join(self.analysis_directory, '{0}_metrics.txt'.format(self.benchmark_run_name))
        write_file(self.metrics_filepath, '\n'.join([x.generate_plaintext() for x in self.metric_latex_objects]))

    def plot(self, analysis_set = '', analysis_directory = None, matplotlib_plots = True, verbose = True, compile_pdf = True, quick_plots = False):
        if matplotlib_plots:
            from klab.plot import general_matplotlib

        old_generate_plots = self.generate_plots # todo: hacky - replace with option to return graphs in memory
        self.generate_plots = True

        self.create_subplot_directory(analysis_directory) # Create a directory for plots

        # Save metric data (if it exists)
        if len(self.stored_metrics_df.index) > 0:
            self.stored_metrics_df.to_csv( os.path.join(analysis_directory, 'metrics.csv') )

        analysis_set_prefix = ''
        if analysis_set:
            analysis_set_prefix = '_{0}'.format(analysis_set)

        analysis_file_prefix = os.path.abspath( os.path.join( self.subplot_directory, self.benchmark_run_name + analysis_set_prefix + '_' ) )

        dataframe = self.dataframe
        latex_report = lr.LatexReport()
        latex_report.content.extend( self.metric_latex_objects ) # Add on table sections generated in calculate_metrics

        # Create a subtitle for the first page
        subtitle = self.benchmark_run_name
        if self.description:
            subtitle += ' ' + self.description
        if self.dataset_description and self.dataset_description != self.description:
            subtitle += ' ' + self.dataset_description
        if analysis_set and analysis_set != self.dataset_description:
            subtitle += ' ({0})'.format(analysis_set)

        # Plot which y-cutoff yields the best value for the fraction correct metric
        scalar_adjustment, scalar_adjustment_calculation_plot = self.plot_optimum_prediction_fraction_correct_cutoffs_over_range(analysis_set, min(self.stability_classication_x_cutoff, 0.5), max(self.stability_classication_x_cutoff, 3.0), suppress_plot = False, analysis_file_prefix = analysis_file_prefix, verbose = verbose)
        if self.calculate_scalar_adjustments:
            assert(self.scalar_adjustments[analysis_set] == scalar_adjustment)

        # Plot which the optimum y-cutoff given the specified or default x-cutoff
        optimal_predictive_cutoff_plot = self.plot_optimum_prediction_fraction_correct_cutoffs(analysis_set, analysis_file_prefix, self.stability_classication_x_cutoff, verbose = verbose)

        # Identify the column with the experimental values for the analysis_set
        experimental_series = BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set)

        latex_report.set_title_page( title = '$\Delta\Delta G$ Report --- %s' % self.benchmark_run_name, subtitle = subtitle )
        if self.credit:
            latex_report.add_to_abstract('Prediction set scoring credit: ' + self.credit)
        latex_report.add_section_page( title = 'Main plots' )

        if matplotlib_plots:
            latex_report.add_plot( general_matplotlib.plot_scatter(self.dataframe, experimental_series, 'Predicted', output_directory = self.subplot_directory, density_plot = True, plot_title = 'Experimental vs. Prediction', output_name = 'experimental_prediction_scatter', fig_height = 7, fig_width = 9, verbose = verbose ), plot_title = 'Experimental vs. Predicted scatterplot (with density binning)' )
            latex_report.add_plot( general_matplotlib.make_corr_plot(self.dataframe, experimental_series, 'Predicted', output_directory = self.subplot_directory, plot_title = 'Experimental vs. Prediction', fig_height = 7, fig_width = 9, verbose = verbose ), plot_title = 'Experimental vs. Predicted scatterplot, with histograms and linear fit statistics. The p-value here (if present) indicates the likelihood that a random set of this many points would produce a correlation at least as strong as the observed correlation.' )


        if not quick_plots:
            if matplotlib_plots:
                single_mutations_dataframe = dataframe[dataframe['NumberOfMutations'] == 1]
                if len(single_mutations_dataframe) > 0:
                    latex_report.add_plot( general_matplotlib.make_corr_plot(single_mutations_dataframe, experimental_series, 'Predicted', output_name = 'single_mutations_histogram_fit_scatter', output_directory = self.subplot_directory, plot_title = 'Experimental vs. Prediction', fig_height = 6, fig_width = 7, verbose = verbose), plot_title = 'Single mutations data subset' )

                multiple_mutations_dataframe = dataframe[dataframe['NumberOfMutations'] > 1]
                if len(multiple_mutations_dataframe) > 0:
                    latex_report.add_plot( general_matplotlib.make_corr_plot(multiple_mutations_dataframe, experimental_series, 'Predicted', output_name = 'multiple_mutations_histogram_fit_scatter', output_directory = self.subplot_directory, plot_title = 'Experimental vs. Prediction', fig_height = 6, fig_width = 7, verbose = verbose), plot_title = 'Multiple mutations data subset' )

                subcase_dataframe = dataframe[dataframe['MutantAA'] == 'A']
                output_name = 'all_alanine_mutations_fit_scatter'
                plot_title = 'Experimental vs. Prediction'
                fig_title = 'All mutations to alanine data subset'
                if len(subcase_dataframe) > 0:
                    latex_report.add_plot( general_matplotlib.make_corr_plot(subcase_dataframe, experimental_series, 'Predicted', output_name = output_name, output_directory = self.subplot_directory, plot_title = plot_title, fig_height = 6, fig_width = 7, verbose = verbose), plot_title = fig_title )

                subcase_dataframe = dataframe[(dataframe['MutantAA'] == 'A') & (dataframe['NumberOfMutations'] == 1)]
                output_name = 'single_alanine_mutations_fit_scatter'
                plot_title = 'Experimental vs. Prediction'
                fig_title = 'All single mutations to alanine data subset'
                if len(subcase_dataframe) > 0:
                    latex_report.add_plot( general_matplotlib.make_corr_plot(subcase_dataframe, experimental_series, 'Predicted', output_name = output_name, output_directory = self.subplot_directory, plot_title = plot_title, fig_height = 6, fig_width = 7, verbose = verbose), plot_title = fig_title )

                subcase_dataframe = dataframe[(dataframe['MutantAA'] == 'A') & (dataframe['NumberOfMutations'] != 1)]
                output_name = 'multiple_alanine_mutations_fit_scatter'
                plot_title = 'Experimental vs. Prediction'
                fig_title = 'All multiple mutations to alanine data subset'
                if len(subcase_dataframe) > 0:
                    latex_report.add_plot( general_matplotlib.make_corr_plot(subcase_dataframe, experimental_series, 'Predicted', output_name = output_name, output_directory = self.subplot_directory, plot_title = plot_title, fig_height = 6, fig_width = 7, verbose = verbose), plot_title = fig_title )

                subcase_dataframe = dataframe[dataframe['MutantAA'] != 'A']
                output_name = 'all_non_alanine_mutations_fit_scatter'
                plot_title = 'Experimental vs. Prediction'
                fig_title = 'All mutations to anything but alanine data subset'
                if len(subcase_dataframe) > 0:
                    latex_report.add_plot( general_matplotlib.make_corr_plot(subcase_dataframe, experimental_series, 'Predicted', output_name = output_name, output_directory = self.subplot_directory, plot_title = plot_title, fig_height = 6, fig_width = 7, verbose = verbose), plot_title = fig_title )

                latex_report.add_plot(
                    general_matplotlib.plot_box(
                        self._get_dataframe_columns( ['RunTime'] ),
                        output_directory = self.subplot_directory,
                        plot_title = 'Prediction Run Time',
                        output_name = 'runtime',
                        fig_height = 6,
                        fig_width = 7,
                        ylabel = 'Run time (minutes)',
                        xlabel = 'Prediction Set',
                        verbose = verbose,
                    ),
                    plot_title = 'Run time'
                )

            # Plot a histogram of the absolute errors
            absolute_error_series = BenchmarkRun.get_analysis_set_fieldname('AbsoluteError', analysis_set)
            latex_report.add_plot(self.plot_absolute_error_histogram('{0}absolute_errors'.format(analysis_file_prefix), absolute_error_series, analysis_set = analysis_set, verbose = verbose), plot_title = 'Absolute error histogram')
            latex_report.add_section_page( title = 'Adjustments', subtext = 'Optimization of the cutoffs\nfor the fraction correct metric' )
            latex_report.add_plot(scalar_adjustment_calculation_plot, plot_title = 'Scalar adjustment calculation plot')
            latex_report.add_plot(optimal_predictive_cutoff_plot, plot_title = 'Optimal predictive cutoff plot')

            # Create a scatterplot and histogram for the adjusted results
            if self.calculate_scalar_adjustments:
                adjusted_predicted_value_series = BenchmarkRun.get_analysis_set_fieldname('Predicted_adj', analysis_set)
                adjusted_absolute_error_series = BenchmarkRun.get_analysis_set_fieldname('AbsoluteError_adj', analysis_set)
                main_adj_scatterplot = '{0}main_adjusted_with_scalar_scatterplot.png'.format(analysis_file_prefix)
                if not(os.path.exists(main_adj_scatterplot) and not(self.recreate_graphs)):
                    if verbose:
                        self.log('Saving scatterplot to %s.' % main_adj_scatterplot)
                    plot_pandas(dataframe, experimental_series, adjusted_predicted_value_series, main_adj_scatterplot, RInterface.correlation_coefficient_gplot, title = 'Experimental vs. Prediction: adjusted scale')
                latex_report.add_plot(main_adj_scatterplot, plot_title = 'Main adj. scatterplot')
                latex_report.add_plot(self.plot_absolute_error_histogram('{0}absolute_errors_adjusted_with_scalar'.format(analysis_file_prefix, verbose = verbose), adjusted_absolute_error_series, analysis_set = analysis_set, verbose = verbose), plot_title = 'Absolute errors adjusted with scalar')

            # Scatterplots colored by residue context / change on mutation
            latex_report.add_section_page( title = 'Residue context' )
            latex_report.add_plot(self.scatterplot_generic('Experimental vs. Prediction - Residue charges', self.scatterplot_charges, '{0}scatterplot_charges.png'.format(analysis_file_prefix), analysis_set = analysis_set, verbose = verbose), plot_title = 'Experimental vs. Prediction - Residue charges')
            latex_report.add_plot(self.scatterplot_generic('Experimental vs. Prediction - Exposure (cutoff = %0.2f)' % self.burial_cutoff, self.scatterplot_exposure, '{0}scatterplot_exposure.png'.format(analysis_file_prefix), analysis_set = analysis_set, verbose = verbose), plot_title = 'Experimental vs. Prediction - Exposure (cutoff = %0.2f)' % self.burial_cutoff)
            latex_report.add_plot(self.scatterplot_generic('Experimental vs. Prediction - Change in volume', self.scatterplot_volume, '{0}scatterplot_volume.png'.format(analysis_file_prefix), analysis_set = analysis_set, verbose = verbose), plot_title = 'Experimental vs. Prediction - Change in volume')
            latex_report.add_plot(self.scatterplot_generic('Experimental vs. Prediction - Wildtype residue s.s.', self.scatterplot_ss, '{0}scatterplot_ss.png'.format(analysis_file_prefix), analysis_set = analysis_set, verbose = verbose), plot_title = 'Experimental vs. Prediction - Wildtype residue s.s.')

            # Scatterplots colored by SCOPe classification
            SCOP_classifications = set(dataframe['WildTypeSCOPClassification'].values.tolist())
            SCOP_folds = set(dataframe['WildTypeSCOPFold'].values.tolist())
            SCOP_classes = set(dataframe['WildTypeSCOPClass'].values.tolist())
            scop_section_page_generated = False
            if len(SCOP_classes) <= 25:
                if len(SCOP_classes) == 1 and ((None in SCOP_classes) or (numpy.isnan(sorted(SCOP_classes)[0]) or not(sorted(SCOP_classes)[0]))):
                    if verbose:
                        print('There are no defined SCOP classes. Skipping the SCOP class plot.')
                else:
                    if not scop_section_page_generated:
                        latex_report.add_section_page( title = 'SCOPe classes' )
                        scop_section_page_generated = True
                    latex_report.add_plot(self.scatterplot_generic('Experimental vs. Prediction - WT residue SCOP class', self.scatterplot_scop_class, '{0}scatterplot_scop_class.png'.format(analysis_file_prefix, verbose = verbose), analysis_set = analysis_set), plot_title = 'Experimental vs. Prediction - WT residue SCOP class')
            if len(SCOP_folds) <= 25:
                if len(SCOP_folds) == 1 and ((None in SCOP_folds) or (numpy.isnan(sorted(SCOP_folds)[0]) or not(sorted(SCOP_folds)[0]))):
                    if verbose:
                        print('There are no defined SCOP folds. Skipping the SCOP fold plot.')
                else:
                    if not scop_section_page_generated:
                        latex_report.add_section_page( title = 'SCOPe classes' )
                        scop_section_page_generated = True
                    latex_report.add_plot(self.scatterplot_generic('Experimental vs. Prediction - WT residue SCOP fold', self.scatterplot_scop_fold, '{0}scatterplot_scop_fold.png'.format(analysis_file_prefix), analysis_set = analysis_set, verbose = verbose), plot_title = 'Experimental vs. Prediction - WT residue SCOP fold')
            if len(SCOP_classifications) <= 25:
                if len(SCOP_classifications) == 1 and ((None in SCOP_classifications) or (numpy.isnan(sorted(SCOP_classifications)[0]) or not(sorted(SCOP_classifications)[0]))):
                    if verbose:
                        print('There are no defined SCOP classifications. Skipping the SCOP classification plot.')
                else:
                    if not scop_section_page_generated:
                        latex_report.add_section_page( title = 'SCOPe classes' )
                        scop_section_page_generated = True
                    latex_report.add_plot(self.scatterplot_generic('Experimental vs. Prediction - WT residue SCOP classification', self.scatterplot_scop_classification, '{0}scatterplot_scop_classification.png'.format(analysis_file_prefix), analysis_set = analysis_set, verbose = verbose), plot_title = 'Experimental vs. Prediction - WT residue SCOP classification')

            # Scatterplots colored by residue types
            latex_report.add_section_page( title = 'Residue types' )
            latex_report.add_plot(self.scatterplot_generic('Experimental vs. Prediction - Wildtype', self.scatterplot_wildtype_aa, '{0}scatterplot_wildtype_aa.png'.format(analysis_file_prefix), analysis_set = analysis_set, verbose = verbose), plot_title = 'Experimental vs. Prediction - Wildtype')
            latex_report.add_plot(self.scatterplot_generic('Experimental vs. Prediction - Mutant', self.scatterplot_mutant_aa, '{0}scatterplot_mutant_aa.png'.format(analysis_file_prefix), analysis_set = analysis_set, verbose = verbose), plot_title = 'Experimental vs. Prediction - Mutant')
            latex_report.add_plot(self.scatterplot_generic('Experimental vs. Prediction - Glycine/Proline', self.scatterplot_GP, '{0}scatterplot_gp.png'.format(analysis_file_prefix), analysis_set = analysis_set, verbose = verbose), plot_title = 'Experimental vs. Prediction - Glycine/Proline')

            # Scatterplots colored PDB resolution and chain length
            latex_report.add_section_page( title = 'Chain properties' )
            latex_report.add_plot(self.scatterplot_generic('Experimental vs. Prediction - PDB resolution', self.scatterplot_pdb_res_binned, '{0}scatterplot_pdb_res_binned.png'.format(analysis_file_prefix), analysis_set = analysis_set, verbose = verbose), plot_title = 'Experimental vs. Prediction - PDB resolution')
            latex_report.add_plot(self.scatterplot_generic('Experimental vs. Prediction - Chain length', self.scatterplot_chain_length, '{0}scatterplot_chain_length.png'.format(analysis_file_prefix), analysis_set = analysis_set, verbose = verbose), plot_title = 'Experimental vs. Prediction - Chain length')

            # Errors / debugging
            latex_report.add_section_page( title =  'Errors / debugging' )
            latex_report.add_plot(self.plot_derivative_error_barchart(analysis_file_prefix, verbose = verbose), plot_title = 'Derivative error barchart')

        ####### End extended plots section #########

        # Copy the analysis input files into the analysis directory - these files are duplicated but it makes it easier to share data
        if self.analysis_csv_input_filepath:
            shutil.copyfile(self.analysis_csv_input_filepath, self.analysis_directory)
        if self.analysis_json_input_filepath:
            shutil.copyfile(self.analysis_json_input_filepath, self.analysis_directory)
        if self.analysis_raw_data_input_filepath:
            shutil.copyfile(self.analysis_raw_data_input_filepath, self.analysis_directory)

        # Combine the plots into a PDF file
        latex_report.generate_pdf_report(
            os.path.join( self.analysis_directory, '{0}_benchmark_plots.pdf'.format(self.benchmark_run_name) ),
            verbose = verbose,
            compile_pdf = compile_pdf,
        )
        if verbose:
            self.log('Report written to: ' + os.path.join( self.analysis_directory, '{0}_benchmark_plots.pdf'.format(self.benchmark_run_name) ) )

        self.generate_plots = old_generate_plots

        return latex_report


    def determine_optimum_fraction_correct_cutoffs(self, analysis_set, dataframe, stability_classication_x_cutoff):
        '''Determines the value of stability_classication_y_cutoff which approximately maximizes the fraction correct
           measurement w.r.t. a fixed stability_classication_x_cutoff. This function uses discrete sampling and so it
           may miss the actual maximum. We use two rounds of sampling: i) a coarse-grained sampling (0.1 energy unit
           intervals); and ii) finer sampling (0.01 unit intervals).
           In both rounds, we choose the one corresponding to a lower value for the cutoff in cases of multiple maxima.'''

        # Determine the value for the fraction correct y-value (predicted) cutoff which will approximately yield the
        # maximum fraction-correct value

        fraction_correct_range = []
        experimental_field = BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set)

        # Round 1 : Coarse sampling. Test 0.5 -> 8.0 in 0.1 increments
        for z in range(5, 80):
            w = float(z) / 10.0
            fraction_correct_range.append((w, fraction_correct_pandas(dataframe, experimental_field, 'Predicted', x_cutoff = stability_classication_x_cutoff, y_cutoff = w, ignore_null_values = True)))

        max_value_cutoff, max_value = fraction_correct_range[0][0], fraction_correct_range[0][1]
        for p in fraction_correct_range:
            if p[1] > max_value:
                max_value_cutoff, max_value = p[0], p[1]

        # Round 2 : Finer sampling. Test max_value_cutoff - 0.1 -> max_value_cutoff + 0.1 in 0.01 increments
        for z in range(int((max_value_cutoff - 0.1) * 100), int((max_value_cutoff + 0.1) * 100)):
            w = float(z) / 100.0
            fraction_correct_range.append((w, fraction_correct_pandas(dataframe, experimental_field, 'Predicted', x_cutoff = stability_classication_x_cutoff, y_cutoff = w, ignore_null_values = True)))
        fraction_correct_range = sorted(set(fraction_correct_range)) # sort so that we find the lowest cutoff value in case of duplicate fraction correct values
        max_value_cutoff, max_value = fraction_correct_range[0][0], fraction_correct_range[0][1]
        for p in fraction_correct_range:
            if p[1] > max_value:
                max_value_cutoff, max_value = p[0], p[1]

        return max_value_cutoff, max_value, fraction_correct_range

    def plot_optimum_prediction_fraction_correct_cutoffs(self, analysis_set, analysis_file_prefix, stability_classication_x_cutoff, verbose = True):

        # Determine the optimal values
        max_value_cutoff, max_value, fraction_correct_range = self.determine_optimum_fraction_correct_cutoffs(analysis_set, self.dataframe, stability_classication_x_cutoff)

        # Filenames
        output_filename_prefix = '{0}optimum_fraction_correct_at_{1}_kcal_mol'.format(analysis_file_prefix, '%.2f' % stability_classication_x_cutoff)
        plot_filename = output_filename_prefix + '.png'
        csv_filename = output_filename_prefix + '.txt'
        R_filename = output_filename_prefix + '.R'

        if os.path.exists(plot_filename) and not(self.recreate_graphs):
            return plot_filename

        # Create CSV input
        lines = ['NeutralityCutoff,FractionCorrect,C']
        for p in fraction_correct_range:
            if p[1] == max_value:
                lines.append(','.join(map(str, (p[0], p[1], 'best'))))
            else:
                lines.append(','.join(map(str, (p[0], p[1], 'other'))))
        if verbose:
            print(csv_filename)
        write_file(csv_filename, '\n'.join(lines))

        # Create plot
        if self.generate_plots:
            title = 'Optimum cutoff for fraction correct metric at %0.2f kcal/mol' % stability_classication_x_cutoff
            r_script = '''library(ggplot2)
library(gridExtra)
library(scales)
library(qualV)

png('%(plot_filename)s', height=4096, width=4096, bg="white", res=600)
plot_data <- read.csv('%(csv_filename)s', header=T)

plot_scale <- scale_color_manual(
values = c( "best" = '#00dd00', "other" = '#666666'),
labels = c( "best" = "Best", "other" = "Other"),
guide = "none") # do not show the legend

best_y = max(plot_data$FractionCorrect)
p <- ggplot(data = plot_data, aes(x = NeutralityCutoff, y = FractionCorrect)) +
 plot_scale +
 xlab("Neutrality cutoff (energy units)") +
 ylab("Fraction correct") +
 ggtitle("%(title)s") +
 geom_point(aes(color = C)) +
 geom_line() +
 geom_smooth() +
 geom_text(hjust=0, size=4, color="black", aes(6.5, best_y, fontface="plain", family = "sans", label=sprintf("Max = %(max_value)0.2f\\nCutoff = %(max_value_cutoff)0.2f")))
p
dev.off()'''
            if verbose:
                self.log('Saving plot of approximate optimal fraction correct cutoffs to %s.' % plot_filename)
            RInterface._runRScript(r_script % locals())
            return plot_filename


    def plot_optimum_prediction_fraction_correct_cutoffs_over_range(self, analysis_set, min_stability_classication_x_cutoff, max_stability_classication_x_cutoff, suppress_plot = False, analysis_file_prefix = None, verbose = True):
        '''Plots the optimum cutoff for the predictions to maximize the fraction correct metric over a range of experimental cutoffs.
           Returns the average scalar corresponding to the best value of fraction correct over a range of cutoff values for the experimental cutoffs.'''

        # Filenames
        analysis_set_prefix = ''
        #if analysis_set:
        #    analysis_set_prefix = '_{0}'.format(analysis_set)
        plot_filename = None
        if not suppress_plot:
            output_filename_prefix = '{0}{1}optimum_fraction_correct_at_varying_kcal_mol'.format(analysis_file_prefix, analysis_set_prefix)
            plot_filename = output_filename_prefix + '.png'
            csv_filename = output_filename_prefix + '.txt'

        # Create CSV input
        lines = ['ExperimentalCutoff,BestPredictionCutoff']
        x_cutoff = min_stability_classication_x_cutoff
        x_values = []
        y_values = []
        avg_scale = 0
        plot_graph = self.generate_plots and not(suppress_plot)
        while x_cutoff < max_stability_classication_x_cutoff + 0.1:
            max_value_cutoff, max_value, fraction_correct_range = self.determine_optimum_fraction_correct_cutoffs(analysis_set, self.dataframe, x_cutoff)
            if plot_graph:
                lines.append(','.join(map(str, (x_cutoff, max_value_cutoff))))
            x_values.append(x_cutoff)
            y_values.append(max_value_cutoff)
            avg_scale += max_value_cutoff / x_cutoff
            x_cutoff += 0.1

        if plot_graph:
            write_file(csv_filename, '\n'.join(lines))

        # Determine the average scalar needed to fit the plot
        avg_scale = avg_scale / len(x_values)
        x_values = numpy.array(x_values)
        y_values = numpy.array(y_values)
        scalars = y_values / x_values
        average_scalar = numpy.mean(scalars)
        plot_label_1 = 'Scalar == %0.2f' % average_scalar
        plot_label_2 = 'sigma == %0.2f' % numpy.std(scalars)

        # Create plot
        if plot_graph:
            if not(os.path.exists(plot_filename) and not(self.recreate_graphs)):
                if verbose:
                    self.log('Saving scatterplot to %s.' % plot_filename)
                    self.log('Saving plot of approximate optimal fraction correct cutoffs over varying experimental cutoffs to %s.' % plot_filename)

                title = 'Optimum cutoff for fraction correct metric at varying experimental cutoffs'
                if analysis_set:
                    title += ' for {0}'.format(analysis_set)
                r_script = '''library(ggplot2)
library(gridExtra)
library(scales)
library(qualV)

png('%(plot_filename)s', height=4096, width=4096, bg="white", res=600)
plot_data <- read.csv('%(csv_filename)s', header=T)

max_y = max(plot_data$BestPredictionCutoff)
p <- ggplot(data = plot_data, aes(x = ExperimentalCutoff, y = BestPredictionCutoff)) +
 xlab("Experimental cutoff (kcal/mol)") +
 ylab("Optimal prediction cutoff (energy units)") +
 ggtitle("%(title)s") +
 geom_point() +
 geom_line() +
 geom_smooth() +
 geom_text(hjust=0, size=4, color="black", aes(0.5, max_y, fontface="plain", family = "sans", label="%(plot_label_1)s"), parse = T) +
 geom_text(hjust=0, size=4, color="black", aes(0.5, max_y - 0.5, fontface="plain", family = "sans", label="%(plot_label_2)s"), parse = T)
p
dev.off()'''
                RInterface._runRScript(r_script % locals())

        return average_scalar, plot_filename

    def _get_dataframe_columns(self, column_names):
        new_dataframe = self.dataframe.copy()
        new_dataframe = new_dataframe[column_names]
        new_dataframe.columns = [name + '_' + self.benchmark_run_name for name in new_dataframe.columns]
        return new_dataframe

    def plot_derivative_error_barchart(self, analysis_file_prefix, verbose = True):

        # Filenames
        output_filename_prefix = '{0}errors_by_pdb_id'.format(analysis_file_prefix)
        plot_filename = output_filename_prefix + '.png'
        csv_filename = output_filename_prefix + '.txt'
        R_filename = output_filename_prefix + '.R'

        new_dataframe = self.dataframe.copy()
        new_dataframe = new_dataframe[['PDBFileID', 'NumberOfDerivativeErrors']]
        new_dataframe.columns = ['PDB', 'AverageDerivativeErrorCount']
        new_dataframe = new_dataframe.groupby(['PDB'])['AverageDerivativeErrorCount'].mean()
        new_dataframe.to_csv(csv_filename, sep = ',', header = True)

        if os.path.exists(plot_filename) and not(self.recreate_graphs):
            return plot_filename

        # Create plot
        firebrick = plot_colors['firebrick']
        brown = plot_colors['brown']
        if verbose:
            self.log('Saving barchart to %s.' % plot_filename)
        title = 'Average count of Inaccurate G! errors by PDB ID'
        r_script = '''library(ggplot2)
library(gridExtra)
library(scales)
library(qualV)

png('%(plot_filename)s', height=4096, width=4096, bg="white", res=600)
plot_data <- read.csv('%(csv_filename)s', header=T)

b <- ggplot(plot_data, aes(x=PDB, y=AverageDerivativeErrorCount)) +
     geom_bar(stat='identity', colour = "%(brown)s", fill = "%(firebrick)s") +
     ggtitle("%(title)s") +
     xlab("PDB ID") +
     ylab("Derivative errors (average)") +
     coord_flip()
b

#m <- ggplot(plot_data, aes(x=AbsoluteError)) +
#    geom_histogram(colour = "%(brown)s", fill = "%(firebrick)s", binwidth = 0.5) +
#    ggtitle("%(title)s") +
#    xlab("Absolute error (kcal/mol - energy units)") +
#    ylab("Number of cases")
#m
dev.off()'''
        RInterface._runRScript(r_script % locals())
        return plot_filename


    def plot_absolute_error_histogram(self, output_filename_prefix, data_series, analysis_set = '', verbose = True):

        # Filenames
        plot_filename = output_filename_prefix + '.png'
        csv_filename = output_filename_prefix + '.txt'
        R_filename = output_filename_prefix + '.R'

        if os.path.exists(plot_filename) and not(self.recreate_graphs):
            return plot_filename

        # Create CSV input
        new_dataframe = self.dataframe[[data_series]]
        new_dataframe.to_csv(csv_filename, sep = ',', header = True)

        if not self.generate_plots:
            return

        # Create plot
        if verbose:
            self.log('Saving scatterplot to %s.' % plot_filename)
        title = 'Distribution of absolute errors (prediction - observed)'
        if analysis_set:
            title += ' for {0}'.format(analysis_set)
        r_script = '''library(ggplot2)
library(gridExtra)
library(scales)
library(qualV)

png('%(plot_filename)s', height=4096, width=4096, bg="white", res=600)
plot_data <- read.csv('%(csv_filename)s', header=T)

m <- ggplot(plot_data, aes(x=%(data_series)s)) +
    geom_histogram(colour = "darkgreen", fill = "green", binwidth = 0.5) +
    ggtitle("%(title)s") +
    xlab("Absolute error (kcal/mol - energy units)") +
    ylab("Number of cases")
m
dev.off()'''
        RInterface._runRScript(r_script % locals())
        return plot_filename


    def scatterplot_generic(self, title, plotfn, plot_filename, analysis_set = '', verbose = True):
        if os.path.exists(plot_filename) and not(self.recreate_graphs):
            return plot_filename

        csv_filename = os.path.splitext(plot_filename)[0] + '.txt'
        plot_commands = plotfn(title, csv_filename, analysis_set = analysis_set)
        r_script = '''library(ggplot2)
library(gridExtra)
library(scales)
library(qualV)

png('%(plot_filename)s', height=4096, width=4096, bg="white", res=600)
plot_data <- read.csv('%(csv_filename)s', header=T)

%(plot_commands)s

dev.off()''' % locals()
        if self.generate_plots:
            if verbose:
                self.log('Saving scatterplot to %s.' % plot_filename)
            RInterface._runRScript(r_script)
            return plot_filename


    def scatterplot_color_by_series(self, colorseries, xseries = "Experimental", yseries = "Predicted", title = '', plot_scale = '', point_opacity = 0.4, extra_commands = '', analysis_set = '', verbose = True):

        experimental_field = BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set)

        # Compute MAE
        mae_str = ''
        if xseries == experimental_field:
            if yseries == 'Predicted':
                mae_str = self.dataframe[BenchmarkRun.get_analysis_set_fieldname('AbsoluteError', analysis_set)].mean()
            elif yseries == 'Predicted_adj':
                mae_str = self.dataframe[BenchmarkRun.get_analysis_set_fieldname('AbsoluteError_adj', analysis_set)].mean()
        if mae_str:
            mae_str = 'MAE = {0:.3f}'.format(mae_str)

        plot_scale_line = ''
        plot_scale_argument = ''
        if plot_scale:
            plot_scale_line = plot_scale.strip()
            plot_scale_argument = '\n    plot_scale +'

        return '''
opacity <- %(point_opacity)s

coefs <- coef(lm(%(yseries)s~%(xseries)s, data = plot_data))
coefs
fitcoefs = coef(lm(%(yseries)s~0 + %(xseries)s, data = plot_data))
fitlmv_Predicted <- as.numeric(fitcoefs[1])

lmv_intercept <- as.numeric(coefs[1])
lmv_Predicted <- as.numeric(coefs[2])

lm(plot_data$%(yseries)s~plot_data$%(xseries)s)
fitcoefs

xlabel <- expression(paste(plain("%(xseries)s ")*Delta*Delta*plain("G (kcal/mol)")))
ylabel <- expression(paste(plain("%(yseries)s ")*Delta*Delta*plain(G)))
rvalue <- cor(plot_data$%(yseries)s, plot_data$%(xseries)s)

minx <- min(plot_data$%(xseries)s)
maxx <- max(plot_data$%(xseries)s)
miny <- min(plot_data$%(yseries)s)
maxy <- max(plot_data$%(yseries)s)
xpos <- minx + ((maxx - minx) * 0.05)
ypos_cor <- maxy - ((maxy - miny) * 0.015)
ypos_mae <- maxy - ((maxy - miny) * 0.055)

%(plot_scale_line)s

p <- ggplot(data = plot_data, aes(x = %(xseries)s, y = %(yseries)s)) +%(plot_scale_argument)s %(extra_commands)s
    xlab("Experimental (kcal/mol)") +
    ylab("Predictions (energy units)") +
    ggtitle("%(title)s") +
    geom_point(aes(color = %(colorseries)s), alpha = I(opacity), shape = I(19)) +
    geom_abline(size = 0.25, intercept = lmv_intercept, slope = lmv_Predicted) +
    geom_abline(color="blue",size = 0.25, intercept = 0, slope = fitlmv_Predicted) +
    geom_text(hjust=0, size=4, aes(xpos, ypos_cor, fontface="plain", family = "sans", label=sprintf("R = %%0.3f", round(rvalue, digits = 4)))) +
    geom_text(hjust=0, size=4, aes(xpos, ypos_mae, fontface="plain", family = "sans", label="%(mae_str)s"))
p

''' % locals()


    def scatterplot_charges(self, title, csv_filename, analysis_set = ''):
        '''Scatterplot by residue charge.'''

        # Create CSV input
        new_dataframe = self.dataframe.copy()
        experimental_field = BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set)
        new_dataframe = new_dataframe[[experimental_field, 'Predicted', 'ResidueCharges']]
        new_dataframe['Opacity'] = 0.4
        new_dataframe = new_dataframe.dropna(subset = [experimental_field, 'Predicted'])
        new_dataframe.to_csv(csv_filename, sep = ',', header = True)

        plot_scale = '''
plot_scale <- scale_color_manual(
    values = c( "None" = '#777777', "Change" = '%(cornflower_blue)s', "Polar/Charged" = 'magenta', "Hydrophobic/Non-polar" = 'green'),
    labels = c( "None" = "N/A", "Change" = "Change", "Polar/Charged" = "Polar/Charged", "Hydrophobic/Non-polar" = "Hydrophobic/Non-polar"))''' % plot_colors
        return self.scatterplot_color_by_series(xseries = experimental_field, colorseries = "ResidueCharges", title = title, plot_scale = plot_scale, point_opacity = 0.6, analysis_set = analysis_set)


    def scatterplot_exposure(self, title, csv_filename, analysis_set = ''):
        '''Scatterplot by exposure class.'''

        # Create CSV input
        new_dataframe = self.dataframe.copy()
        experimental_field = BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set)
        new_dataframe = new_dataframe[[experimental_field, 'Predicted', 'WildTypeExposure']]
        new_dataframe['Opacity'] = 0.4
        new_dataframe = new_dataframe.dropna(subset = [experimental_field, 'Predicted'])
        new_dataframe.columns = [experimental_field, 'Predicted', 'Exposure', 'Opacity'] # rename the exposure column
        new_dataframe.to_csv(csv_filename, sep = ',', header = True)

        plot_scale = '''
plot_scale <- scale_color_manual(
    values = c( "None" = '#777777', "B" = '%(brown)s', "E" = '%(purple)s'),
    labels = c( "None" = "N/A", "B" = "Buried", "E" = "Exposed"))''' % plot_colors
        return self.scatterplot_color_by_series(xseries = experimental_field, colorseries = "Exposure", title = title, plot_scale = plot_scale, analysis_set = analysis_set)


    def scatterplot_volume(self, title, csv_filename, analysis_set = '', verbose = True):
        '''Scatterplot by change in volume upon mutation.'''

        # Create CSV input
        new_dataframe = self.dataframe.copy()
        experimental_field = BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set)
        new_dataframe = new_dataframe[[experimental_field, 'Predicted', 'VolumeChange']]
        new_dataframe['Opacity'] = 0.4
        new_dataframe = new_dataframe.dropna(subset = [experimental_field, 'Predicted'])
        new_dataframe.to_csv(csv_filename, sep = ',', header = True)

        plot_scale = '''
plot_scale <- scale_color_manual(
    values = c( "None" = '#777777', "SL" = '%(brown)s', "LS" = '%(purple)s', 'XX' = "%(cornflower_blue)s"),
    labels = c( "None" = "N/A", "SL" = "Increase", "LS" = "Decrease", "XX" = "No change"))''' % plot_colors
        return self.scatterplot_color_by_series(xseries = experimental_field, colorseries = "VolumeChange", title = title, plot_scale = plot_scale, analysis_set = analysis_set, verbose = verbose)


    def scatterplot_ss(self, title, csv_filename, analysis_set = '', verbose = True):
        '''Scatterplot by secondary structure.'''

        # Create CSV input
        new_dataframe = self.dataframe.copy()
        experimental_field = BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set)
        new_dataframe = new_dataframe[[experimental_field, 'Predicted', 'WildTypeDSSPSimpleSSType']]
        new_dataframe['Opacity'] = 0.4
        new_dataframe = new_dataframe.dropna(subset = [experimental_field, 'Predicted'])
        new_dataframe.columns = [experimental_field, 'Predicted', 'WTSecondaryStructure', 'Opacity'] # rename the s.s. column
        new_dataframe.to_csv(csv_filename, sep = ',', header = True)

        plot_scale = '''
plot_scale <- scale_color_manual(
    name="Secondary structure",
    values = c( "None" = '#777777', "H" = 'magenta', "S" = 'orange', "O" = '%(cornflower_blue)s'),
    labels = c( "None" = "N/A", "H" = "Helix", "S" = "Sheet", "O" = "Other"))''' % plot_colors
        return self.scatterplot_color_by_series(xseries = experimental_field, colorseries = "WTSecondaryStructure", title = title, plot_scale = plot_scale, point_opacity = 0.6, analysis_set = analysis_set, verbose = verbose)


    def scatterplot_scop_class(self, title, csv_filename, analysis_set = '', verbose = True):
        '''Scatterplot by SCOPe class.'''

        # Create CSV input
        new_dataframe = self.dataframe.copy()
        experimental_field = BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set)
        new_dataframe = new_dataframe[[experimental_field, 'Predicted', 'WildTypeSCOPClass']]
        new_dataframe['Opacity'] = 0.4
        new_dataframe = new_dataframe.dropna(subset = [experimental_field, 'Predicted'])
        new_dataframe.to_csv(csv_filename, sep = ',', header = True)

        return self.scatterplot_color_by_series(xseries = experimental_field, colorseries = "WildTypeSCOPClass", title = title, point_opacity = 0.6, analysis_set = analysis_set, verbose = verbose)


    def scatterplot_scop_fold(self, title, csv_filename, analysis_set = '', verbose = True):
        '''Scatterplot by SCOPe fold.'''

        # Create CSV input
        new_dataframe = self.dataframe.copy()
        experimental_field = BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set)
        new_dataframe = new_dataframe[[experimental_field, 'Predicted', 'WildTypeSCOPFold']]
        new_dataframe['Opacity'] = 0.4
        new_dataframe = new_dataframe.dropna(subset = [experimental_field, 'Predicted'])
        new_dataframe.to_csv(csv_filename, sep = ',', header = True)

        return self.scatterplot_color_by_series(xseries = experimental_field, colorseries = "WildTypeSCOPFold", title = title, point_opacity = 0.6, analysis_set = analysis_set)


    def scatterplot_scop_classification(self, title, csv_filename, analysis_set = ''):
        '''Scatterplot by SCOPe classification.'''

        # Create CSV input
        new_dataframe = self.dataframe.copy()
        experimental_field = BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set)
        new_dataframe = new_dataframe[[experimental_field, 'Predicted', 'WildTypeSCOPClassification']]
        new_dataframe['Opacity'] = 0.4
        new_dataframe = new_dataframe.dropna(subset = [experimental_field, 'Predicted'])
        new_dataframe.to_csv(csv_filename, sep = ',', header = True)

        return self.scatterplot_color_by_series(xseries = experimental_field, colorseries = "WildTypeSCOPClassification", title = title, point_opacity = 0.6, analysis_set = analysis_set, verbose = verbose)


    def scatterplot_wildtype_aa(self, title, csv_filename, analysis_set = '', verbose = True):
        '''Scatterplot by wildtype residue.'''

        # Create CSV input
        new_dataframe = self.dataframe.copy()
        experimental_field = BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set)
        new_dataframe = new_dataframe[[experimental_field, 'Predicted', 'WildTypeAA']]
        new_dataframe['Opacity'] = 0.4
        new_dataframe = new_dataframe.dropna(subset = [experimental_field, 'Predicted'])
        new_dataframe.to_csv(csv_filename, sep = ',', header = True)

        plot_scale = '''
plot_scale <- scale_color_manual(
    name="Residue",
    values = c( "None" = '#808080', "A" = '#FF0000', "C" = '#BFBF00', "D" = '#008000', "E" = "#80FFFF", "F" = "#8080FF", "G" = "#BF40BF", "H" = "#A0A424", "I" = "#411BEA", "K" = "#1EAC41", "L" = "#F0C80E", "M" = "#B430E5", "N" = "#ED7651", "P" = "#19CB97", "Q" = "#362698", "R" = "#7E7EB8", "S" = "#603000", "T" = "#A71818", "V" = "#DF8020", "W" = "#E75858", "Y" = "#082008"),
    labels = c( "None" = "N/A", "A" = "A", "C" = "C", "D" = "D", "E" = "E", "F" = "F", "G" = "G", "H" = "H", "I" = "I", "K" = "K", "L" = "L", "M" = "M", "N" = "N", "P" = "P", "Q" = "Q", "R" = "R", "S" = "S", "T" = "T", "V" = "V", "W" = "W", "Y" = "Y"))
    ''' % plot_colors
        return self.scatterplot_color_by_series(xseries = experimental_field, colorseries = "WildTypeAA", title = title, plot_scale = plot_scale, point_opacity = 0.6, analysis_set = analysis_set, verbose = verbose)


    def scatterplot_mutant_aa(self, title, csv_filename, analysis_set = '', verbose = True):
        '''Scatterplot by mutant residue.'''

        # Create CSV input
        new_dataframe = self.dataframe.copy()
        experimental_field = BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set)
        new_dataframe = new_dataframe[[experimental_field, 'Predicted', 'MutantAA']]
        new_dataframe['Opacity'] = 0.4
        new_dataframe = new_dataframe.dropna(subset = [experimental_field, 'Predicted'])
        new_dataframe.to_csv(csv_filename, sep = ',', header = True)

        plot_scale = '''
plot_scale <- scale_color_manual(
    name="Residue",
    values = c( "None" = '#808080', "A" = '#FF0000', "C" = '#BFBF00', "D" = '#008000', "E" = "#80FFFF", "F" = "#8080FF", "G" = "#BF40BF", "H" = "#A0A424", "I" = "#411BEA", "K" = "#1EAC41", "L" = "#F0C80E", "M" = "#B430E5", "N" = "#ED7651", "P" = "#19CB97", "Q" = "#362698", "R" = "#7E7EB8", "S" = "#603000", "T" = "#A71818", "V" = "#DF8020", "W" = "#E75858", "Y" = "#082008"),
    labels = c( "None" = "N/A", "A" = "A", "C" = "C", "D" = "D", "E" = "E", "F" = "F", "G" = "G", "H" = "H", "I" = "I", "K" = "K", "L" = "L", "M" = "M", "N" = "N", "P" = "P", "Q" = "Q", "R" = "R", "S" = "S", "T" = "T", "V" = "V", "W" = "W", "Y" = "Y"))
    ''' % plot_colors
        return self.scatterplot_color_by_series(xseries = experimental_field, colorseries = "MutantAA", title = title, plot_scale = plot_scale, point_opacity = 0.6, analysis_set = analysis_set, verbose = verbose)


    def scatterplot_GP(self, title, csv_filename, analysis_set = '', verbose = True):

        # Create CSV input
        new_dataframe = self.dataframe.copy()
        experimental_field = BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set)
        new_dataframe = new_dataframe[[experimental_field, 'Predicted', 'HasGPMutation']]
        new_dataframe['GP'] = numpy.where(new_dataframe['HasGPMutation'] == 1, 'GP', 'Other')
        new_dataframe['Opacity'] = numpy.where(new_dataframe['HasGPMutation'] == 1, 0.9, 0.5)
        new_dataframe = new_dataframe[[experimental_field, 'Predicted', 'GP', 'Opacity']]
        new_dataframe = new_dataframe.dropna(subset = [experimental_field, 'Predicted'])
        new_dataframe.to_csv(csv_filename, sep = ',', header = True)

        plot_scale = '''plot_scale <- scale_color_manual(
    name="Glycine/Proline",
    values = c( "None" = '#777777', "GP" = '%(neon_green)s', "Other" = '#440077'),
    labels = c( "None" = "N/A", "GP" = "GP", "Other" = "Other"))''' % plot_colors
        return self.scatterplot_color_by_series(xseries = experimental_field, colorseries = "GP", title = title, plot_scale = plot_scale, point_opacity = 0.75, analysis_set = analysis_set, verbose = verbose)


    def scatterplot_pdb_res_binned(self, title, csv_filename, analysis_set = '', verbose = True):
        '''Scatterplot by binned PDB resolution.'''

        # Create CSV input
        new_dataframe = self.dataframe.copy()
        experimental_field = BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set)
        new_dataframe = new_dataframe[[experimental_field, 'Predicted', 'PDBResolutionBin']]
        new_dataframe['Opacity'] = 0.4
        new_dataframe = new_dataframe.dropna(subset = [experimental_field, 'Predicted'])
        new_dataframe.to_csv(csv_filename, sep = ',', header = True)

        plot_scale = '''
plot_scale <- scale_color_manual(
    name = "Resolution",
    values = c( "N/A" = '#777777', "<1.5" = '#0052aE', "1.5-2.0" = '#554C54', '2.0-2.5' = "#FFA17F", '>=2.5' = "#ce4200")
    )''' % plot_colors
        return self.scatterplot_color_by_series(xseries = experimental_field, colorseries = "PDBResolutionBin", title = title, plot_scale = plot_scale, point_opacity = 0.75, analysis_set = analysis_set, verbose = verbose)


    def scatterplot_chain_length(self, title, csv_filename, analysis_set = '', verbose = True):
        '''Scatterplot by chain length.'''

        # Create CSV input
        new_dataframe = self.dataframe.copy()
        experimental_field = BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set)
        new_dataframe = new_dataframe[[experimental_field, 'Predicted', 'NumberOfResidues']]
        new_dataframe['Opacity'] = 0.4
        new_dataframe.columns = [experimental_field, 'Predicted', 'Residues', 'Opacity'] # rename the monomer length column
        new_dataframe = new_dataframe.dropna(subset = [experimental_field, 'Predicted'])
        new_dataframe.to_csv(csv_filename, sep = ',', header = True)

        plot_scale = '''
plot_scale <- scale_color_manual(
    name = "Resolution",
    values = c( "N/A" = '#777777', "<1.5" = '#0052aE', "1.5-2.0" = '#554C54', '2.0-2.5' = "#FFA17F", '>=2.5' = "#ce4200")
    )''' % plot_colors
        extra_commands ='\n    scale_colour_gradient(low="yellow", high="#880000") +'
        return self.scatterplot_color_by_series(xseries = experimental_field, colorseries = "Residues", title = title, plot_scale = '', point_opacity = 0.75, extra_commands = extra_commands, analysis_set = analysis_set, verbose = verbose)


def _full_analysis_mp_alias(br_obj, analysis_set, output_directory, unique_name, verbose, quick_plots):
    """
    Alias for instance method that allows the method to be called in a
    multiprocessing pool. Needed as multiprocessing does not otherwise work
    on object instance methods.
    """
    return (br_obj, unique_name, br_obj.full_analysis(analysis_set, output_directory, verbose = verbose, compile_pdf = verbose, quick_plots = quick_plots))


def _compare_mp_alias(br_i, br_j, analysis_set, analysis_set_subdir, unique_ajps, verbose):
    """
    Alias for instance method that allows the method to be called in a
    multiprocessing pool. Needed as multiprocessing does not otherwise work
    on object instance methods.
    """
    return br_i.compare(br_j, analysis_set, analysis_set_subdir, unique_ajps, verbose = verbose, compile_pdf = verbose)


class DBBenchmarkRun(BenchmarkRun):
    '''Our database storage has a different (more detailed) data structure than the JSON dump so we need to override some classes.'''

    csv_headers = [
        'DatasetID', 'PDBFileID', 'Mutations', 'NumberOfMutations', 'Experimental', 'Predicted', 'AbsoluteError', 'StabilityClassification',
        'ResidueCharges', 'VolumeChange',
        'WildTypeDSSPType', 'WildTypeDSSPSimpleSSType', 'WildTypeDSSPExposure',
        'WildTypeSCOPClass', 'WildTypeSCOPFold', 'WildTypeSCOPClassification',
        'WildTypeExposure', 'WildTypeAA', 'MutantAA', 'HasGPMutation',
        'PDBResolution', 'PDBResolutionBin', 'NumberOfResidues', 'NumberOfDerivativeErrors',
    ]


    def __init__(self, *args, **kwargs):
        super(DBBenchmarkRun, self).__init__(*args, **kwargs)
        self.analysis_sets = []


    def get_analysis_sets(self, record):
        if not self.analysis_sets:
            if record['DDG'] != None:
                self.analysis_sets = sorted(record['DDG'].keys())
        return self.analysis_sets


    def is_this_record_a_derived_mutation(self, record):
        '''Returns True if a record is marked as a derived record i.e. the DDG value is calculated from one source ("reverse"
           mutation) or two sources (a "mutation triangle") without a separate experiment having taken place. This property
           is marked in the Kortemme lab database when we have determined that this is indeed the case. Otherwise, return
           False.
           For purely computational dataframes, we should always return False.'''
        if self.contains_experimental_data:
            for analysis_set in self.get_analysis_sets(record):
                ddg_details = record['DDG'][analysis_set]
                if ddg_details and ddg_details['IsDerivedValue']:
                    return True
            return False
        else:
            # Computational dataframe case
            return False


    def get_record_mutations(self, record):
        return record['PDBMutations']


    def reset_csv_headers(self):
        analysis_sets = None
        for record in self.dataset_cases.values():
            analysis_sets = self.get_analysis_sets(record)
            break
        if analysis_sets:
            self.csv_headers.remove('Experimental')
            self.csv_headers.remove('AbsoluteError')
            self.csv_headers.remove('StabilityClassification')
            for analysis_set in analysis_sets:
                self.csv_headers.append(BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set))
                self.csv_headers.append(BenchmarkRun.get_analysis_set_fieldname('AbsoluteError', analysis_set))
                self.csv_headers.append(BenchmarkRun.get_analysis_set_fieldname('StabilityClassification', analysis_set))


    def get_experimental_ddg_values(self, record, dataframe_record):
        '''Adds the mean experimental value associated with each analysis set to the dataframe row.'''
        new_idxs = []
        for analysis_set in self.get_analysis_sets(record):
            ddg_details = record['DDG'][analysis_set]
            exp_ddg_fieldname = BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set)
            new_idxs.append(exp_ddg_fieldname)
            dataframe_record[exp_ddg_fieldname] = None
            if ddg_details:
                dataframe_record[exp_ddg_fieldname] = ddg_details['MeanDDG']

        # Update the CSV headers
        try:
            idx = self.csv_headers.index('Experimental')
            self.csv_headers = self.csv_headers[:idx] + new_idxs + self.csv_headers[idx + 1:]
        except ValueError, e: pass


    def compute_stability_classification(self, predicted_data, record, dataframe_record):
        '''Calculate the stability classification for the analysis cases. Must be called after get_experimental_ddg_values.'''

        new_idxs = []
        stability_classication_x_cutoff, stability_classication_y_cutoff = self.stability_classication_x_cutoff, self.stability_classication_y_cutoff
        for analysis_set in self.get_analysis_sets(record):
            ddg_details = record['DDG'][analysis_set]
            exp_ddg_fieldname = BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set)
            stability_classification_fieldname = BenchmarkRun.get_analysis_set_fieldname('StabilityClassification', analysis_set)
            new_idxs.append(stability_classification_fieldname)
            dataframe_record[stability_classification_fieldname] = None

            if ddg_details:
                stability_classification = None
                if dataframe_record[exp_ddg_fieldname] != None:
                    stability_classification = fraction_correct([dataframe_record[exp_ddg_fieldname]], [predicted_data[self.ddg_analysis_type]], x_cutoff = stability_classication_x_cutoff, y_cutoff = stability_classication_y_cutoff)
                    stability_classification = int(stability_classification)
                    assert(stability_classification == 0 or stability_classification == 1)
                dataframe_record[stability_classification_fieldname] = stability_classification

        # Update the CSV headers
        try:
            idx = self.csv_headers.index('StabilityClassification')
            self.csv_headers = self.csv_headers[:idx] + new_idxs + self.csv_headers[idx + 1:]
        except ValueError, e: pass


    def compute_absolute_error(self, predicted_data, record, dataframe_record):
        '''Calculate the absolute error for the analysis cases. Must be called after get_experimental_ddg_values.'''

        new_idxs = []
        for analysis_set in self.get_analysis_sets(record):
            ddg_details = record['DDG'][analysis_set]
            exp_ddg_fieldname = BenchmarkRun.get_analysis_set_fieldname('Experimental', analysis_set)
            absolute_error_fieldname = BenchmarkRun.get_analysis_set_fieldname('AbsoluteError', analysis_set)
            new_idxs.append(absolute_error_fieldname)
            dataframe_record[absolute_error_fieldname] = None

            if ddg_details and predicted_data[self.ddg_analysis_type] != None:
                absolute_error = abs(dataframe_record[exp_ddg_fieldname] - predicted_data[self.ddg_analysis_type])
                dataframe_record[absolute_error_fieldname] = absolute_error

        # Update the CSV headers
        try:
            idx = self.csv_headers.index('AbsoluteError')
            self.csv_headers = self.csv_headers[:idx] + new_idxs + self.csv_headers[idx + 1:]
        except ValueError, e: pass


    def get_record_pdb_file_id(self, record):
        return record['Structure']['PDBFileID']


    def count_residues(self, record, pdb_record):
        NumberOfResidues = 0
        try:
            pdb_chains = set(record['Structure']['Partners']['L'] + record['Structure']['Partners']['R'])
            assert(len(pdb_chains) > 1) # we expect non-monomeric cases
            for pdb_chain in pdb_chains:
                NumberOfResidues += len(pdb_record.get('Chains', {}).get(pdb_chain, {}).get('Sequence', ''))
        except: pass
        return NumberOfResidues
