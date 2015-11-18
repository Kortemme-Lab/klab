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

The BenchmarkRun class extends the generic DDG BenchmarkRun class to add columns particular to binding
affinity predictions.
'''


from klab.bio.basics import dssp_elision
from klab.benchmarking.analysis.ddg_monomeric_stability_analysis import DBBenchmarkRun as GenericDBBenchmarkRun



class DBBenchmarkRun(GenericDBBenchmarkRun):

    def get_dataframe_row(self, dataset_cases, predicted_data, pdb_data, record_id, additional_prediction_data_columns):
        '''Create a dataframe row for a prediction.'''
        record = dataset_cases[record_id]
        for m in record['PDBMutations']:
            assert('DSSPSimpleSSType' not in m)
            m['DSSPSimpleSSType'] = dssp_elision.get(m['ComplexDSSP']) or dssp_elision.get(m['MonomericDSSP'])
            m['DSSPType'] = m.get('ComplexDSSP') or m.get('MonomericDSSP')
            m['DSSPExposure'] = m.get('ComplexExposure') or m.get('MonomericExposure')

        dataframe_record = super(DBBenchmarkRun, self).get_dataframe_row(dataset_cases, predicted_data, pdb_data, record_id, additional_prediction_data_columns)
        # add columns
        return dataframe_record

