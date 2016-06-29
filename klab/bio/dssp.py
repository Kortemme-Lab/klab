#!/usr/bin/env python
# encoding: utf-8
"""
dssp.py
Wrapper functions for the DSSP program designed by Wolfgang Kabsch and Chris Sander.

Created by Shane O'Connor 2014.

DSSP is described here:

A series of PDB related databases for everyday needs.
Robbie P. Joosten, Tim A.H. te Beek, Elmar Krieger, Maarten L. Hekkelman, Rob W.W. Hooft, Reinhard Schneider, Chris Sander, and Gert Vriend.
Nucleic Acids Research 2011 January; 39(Database issue): D411-D419.
doi: 10.1093/nar/gkq1105
PMCID: PMC3013697
(PDF).

Dictionary of protein secondary structure: pattern recognition of hydrogen-bonded and geometrical features.
Kabsch W, Sander C,
Biopolymers. 1983 22 2577-2637.
PMID: 6667333; UI: 84128824.

The compute_burial function below computes a normalized value between 0 and 1. We took this approach from Tien et al., 2013 (http://dx.doi.org/10.1371/journal.pone.0080635).
The values (in A^2) used for the computation of burial are from Miller et al., 1987 (http://dx.doi.org/10.1016/0022-2836(87)90038-6).
 """

import os
import shlex
import traceback
import string
import pprint

from klab.fs.fsio import read_file, write_temp_file
from klab.process import Popen as _Popen
from klab import colortext
from klab.bio.pdb import PDB
from klab.bio.rcsb import retrieve_pdb
from klab.bio.basics import dssp_secondary_structure_types, residue_types_1, residue_type_1to3_map, residue_type_3to1_map
from klab.general.structures import NestedBunch


secondary_structure_types = dssp_secondary_structure_types.keys()
residue_types = [t for t in residue_types_1] + [ss_bridge_cysteine_code for ss_bridge_cysteine_code in string.ascii_lowercase]
residue_type_1to3 = {}
for k, v in residue_type_1to3_map.iteritems():
    residue_type_1to3[k] = v
for c in string.ascii_lowercase:
    residue_type_1to3[c] = 'CYS'

residue_max_acc = dict(
    # This dict is taken from the Wilke Lab's DSSP wrapper.
    # The code for the wrapper can be found at: http://wilke.openwetware.org/Software.html ("Program for computing relative solvent accessibilities for a protein that uses the DSSP program of Kabsch and Sander")
    # The values in the dict are presented in Tien et al., 2013 (http://dx.doi.org/10.1371/journal.pone.0080635)
    # and seem to be taken from the proposed values for ASA normalization (in A^2) from Miller et al., 1987 (http://dx.doi.org/10.1016/0022-2836(87)90038-6).
    Miller={
        'A': 113.0, 'R': 241.0, 'N': 158.0, 'D': 151.0,
        'C': 140.0, 'Q': 189.0, 'E': 183.0, 'G': 85.0,
        'H': 194.0, 'I': 182.0, 'L': 180.0, 'K': 211.0,
        'M': 204.0, 'F': 218.0, 'P': 143.0, 'S': 122.0,
        'T': 146.0, 'W': 259.0, 'Y': 229.0, 'V': 160.0
    },
    Wilke={
        'A': 129.0, 'R': 274.0, 'N': 195.0, 'D': 193.0,
        'C': 167.0, 'Q': 225.0, 'E': 223.0, 'G': 104.0,
        'H': 224.0, 'I': 197.0, 'L': 201.0, 'K': 236.0,
        'M': 224.0, 'F': 240.0, 'P': 159.0, 'S': 155.0,
        'T': 172.0, 'W': 285.0, 'Y': 263.0, 'V': 174.0
    },
)


class MissingAtomException(Exception): pass


class MonomerDSSP(object):
    '''
    A class wrapper for DSSP.

    Note: This class strips a PDB file to each chain and computes the DSSP for that chain alone. If you want to run DSSP
    on complexes, subclass this class and do not perform the stripping.

    Once initialized, the dssp element of the object should contain a mapping from protein chain IDs to dicts.
    The dict associated with a protein chain ID is a dict from PDB residue IDs to details about that residue.
    For example:
       dssp -> 'A' -> '  64 ' -> {
                                  '3LC': 'LEU',
                                  'acc': 171,
                                  'bp_1': 0,
                                  'bp_2': 0,
                                  'chain_id': 'I',
                                  'dssp_res_id': 10,
                                  'dssp_residue_aa': 'L',
                                  'exposure': 0.95,
                                  'is_buried': False,
                                  'pdb_res_id': '  64 ',
                                  'residue_aa': 'L',
                                  'sheet_label': ' ',
                                  'ss': None,
                                  'ss_details': '<      '}

    Description of the fields:
      - residue_aa and 3LC contain the residue 1-letter and 3-letter codes respectively;
      - acc is the number of water molecules in contact with this residue (according to DSSP);
      - exposure is a normalized measure of exposure where 0.0 denotes total burial and 1.0 denotes total exposure;
        - exposure is calculated by dividing the number of water molecules in contact with this residue (according to DSSP) by the residue_max_acc value from the appropriate value table;
      - is_buried is either None (could not be determined), True if exposure < cut_off, or False if exposure >= cut_off;
      - ss is the assigned secondary structure type, using the DSSP secondary structure types (see basics.py/dssp_secondary_structure_types). This value may be None if no secondary structure was assigned.

    Usage:
       d = DSSP.from_RCSB('1HAG')

       # access the dict directly
       print(d.dssp['I']['  64 ']['exposure'])
       print(d.dssp['I']['  64 ']['is_buried'])

       # use dot notation
       print(d.dsspb.I.get('  64 ').exposure)
       print(d.dsspb.I.get('  64 ').is_buried)

       # iterate through the residues
       for chain_id, mapping in d:
           for residue_id, residue_details in sorted(mapping.iteritems()):
               print(residue_id, residue_details['exposure'])

    '''

    @classmethod
    def from_pdb_contents(cls, pdb_contents, cut_off = 0.25, acc_array = 'Miller', tmp_dir = '/tmp', read_only = False):
        return cls(PDB(pdb_contents), cut_off = cut_off, acc_array = acc_array, tmp_dir = tmp_dir, read_only = read_only)

    @classmethod
    def from_pdb_filepath(cls, pdb_filepath, cut_off = 0.25, acc_array = 'Miller', tmp_dir = '/tmp', read_only = False):
        return cls(PDB(read_file(pdb_filepath)), cut_off = cut_off, acc_array = acc_array, tmp_dir = tmp_dir, read_only = read_only)

    @classmethod
    def from_RCSB(cls, pdb_id, cut_off = 0.25, acc_array = 'Miller', tmp_dir = '/tmp', read_only = False):
        return cls(PDB(retrieve_pdb(pdb_id)), cut_off = cut_off, acc_array = acc_array, tmp_dir = tmp_dir, read_only = read_only)

    def __init__(self, p, cut_off = 0.25, acc_array = 'Miller', tmp_dir = '/tmp', read_only = False):
        '''This function strips a PDB file to one chain and then runs DSSP on this new file.
           p should be a PDB object (see pdb.py).
        '''
        try:
            _Popen('.', shlex.split('mkdssp --version'))
        except:
            raise colortext.Exception('mkdssp does not seem to be installed in a location declared in the environment path.')

        self.cut_off = cut_off
        self.tmp_dir = tmp_dir
        self.residue_max_acc = residue_max_acc[acc_array]
        self.read_only = read_only
        if not self.read_only:
            self.pdb = p.clone()  # make a local copy in case this gets modified externally
        else:
            self.pdb = p
        self.chain_order = self.pdb.atom_chain_order
        self.dssp_output = {}
        self.dssp = {}
        for chain_id in [c for c in self.pdb.atom_sequences.keys() if self.pdb.chain_types[c] == 'Protein']:
            self.compute(chain_id)
        self.chain_order = [c for c in self.chain_order if c in self.dssp]
        self.dsspb = NestedBunch(self.dssp)

    def __iter__(self):
        self._iter_keys = [c for c in self.chain_order]
        self._iter_keys.reverse()  # we pop from the list
        return self

    def next(self):  # todo: This is __next__ in Python 3.x
        try:
            chain_id = self._iter_keys.pop()
            return chain_id, self.dssp[chain_id]
        except:
            raise StopIteration

    def __repr__(self):
        return pprint.pformat(self.dssp)

    def compute(self, chain_id):
        tmp_dir = self.tmp_dir
        pdb_object = self.pdb.clone()  # we are immediately modifying the PDB file by stripping chains so we need to make a copy
        pdb_object.strip_to_chains(chain_id)
        input_filepath = write_temp_file(tmp_dir, pdb_object.get_content(), ftype = 'w', prefix = 'dssp_')
        output_filepath = write_temp_file(tmp_dir, '', ftype = 'w', prefix = 'dssp_')
        try:
            p = _Popen('.', shlex.split('mkdssp -i {input_filepath} -o {output_filepath}'.format(**locals())))
            if p.errorcode:
                if p.stderr.find('empty protein, or no valid complete residues') != -1:
                    raise MissingAtomException(p.stdout)
                else:
                    raise Exception('An error occurred while calling DSSP:\n%s' % p.stderr)
            self.dssp_output[chain_id] = read_file(output_filepath)
            self.dssp[chain_id] = self.parse_output(chain_id)
        except MissingAtomException as e:
            os.remove(input_filepath)
            os.remove(output_filepath)
            raise
        except Exception as e:
            os.remove(input_filepath)
            os.remove(output_filepath)
            raise colortext.Exception('%s\n%s' % (str(e), traceback.format_exc()))
        os.remove(input_filepath)
        os.remove(output_filepath)

    def parse_output(self, chain_id):
        d = {}
        dssp_output = self.dssp_output[chain_id]
        assert(dssp_output.startswith('===='))
        header_line = '  #  RESIDUE AA STRUCTURE BP1 BP2  ACC     N-H-->O    O-->H-N    N-H-->O    O-->H-N    TCO  KAPPA ALPHA  PHI   PSI    X-CA   Y-CA   Z-CA'
        idx = dssp_output.find(header_line)
        assert(idx != -1)
        data_lines = [l for l in dssp_output[idx + len(header_line):].split('\n') if l.strip()]
        for dl in data_lines:
            l = self.parse_data_line(dl)
            if l:
                d[l['pdb_res_id']] = l
        return d


    #Sample line:
    #  #  RESIDUE AA STRUCTURE BP1 BP2  ACC     N-H-->O    O-->H-N    N-H-->O    O-->H-N    TCO  KAPPA ALPHA  PHI   PSI    X-CA   Y-CA   Z-CA
    #    1   55 I D              0   0  210      0, 0.0     2,-0.2     0, 0.0     0, 0.0   0.000 360.0 360.0 360.0 -37.4    5.2  -12.5    1.9
    #   13    5 E P  T 345S+     0   0   13      0, 0.0    -1,-0.1     0, 0.0   136,-0.1   0.852 103.9  38.3 -44.1 -45.0    1.8   14.6   14.5
    #   54   33 E L  E     -IJ  64  97B   1     10,-2.7     9,-1.4    -2,-0.4    10,-0.9  -0.789  25.5-160.5 -94.1 131.9   15.6   -3.3    9.4
    #Sample line with insertion code
    #    1    1HE T              0   0  152      0, 0.0     2,-0.3     0, 0.0     4,-0.0   0.000 360.0 360.0 360.0  53.3   22.6   20.0   16.5
    #0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345
    #          1         2         3         4         5         6         7         8         9         0         1         2         3
    def parse_data_line(self, data_line):
        d = dict(
            dssp_res_id = data_line[0:5],
            pdb_res_id = data_line[5:11], # this includes an insertion code e.g. run against 1HAG
            chain_id = data_line[11],
            dssp_residue_aa = data_line[13], # e.g. a-z can be used for SS-bridge cysteines
            ss = data_line[16].strip() or ' ',
            ss_details = data_line[18:25],
            bp_1 = data_line[25:29],
            bp_2 = data_line[29:33],
            sheet_label = data_line[33],
            acc = data_line[34:38],
        )
        if d['dssp_residue_aa'] != '!':  # e.g. 1A22, chain A, between PDB residue IDs 129 and 136
            self.check_line(d)  # note: this function call has side-effects
            self.compute_burial(d)
            return d
        else:
            return None

    def check_line(self, d):
        d['dssp_res_id'] = int(d['dssp_res_id'])
        int(d['pdb_res_id'][:-1])
        assert(d['pdb_res_id'][0] == ' ')  # I think this is the case
        assert(d['pdb_res_id'][-1] == ' ' or d['pdb_res_id'][-1].isalpha())
        d['pdb_res_id'] = d['pdb_res_id'][1:]
        assert(d['chain_id'].isalnum())
        d['residue_aa'] = residue_type_3to1_map[residue_type_1to3[d['dssp_residue_aa']]]  # convert the DSSP residue type into a canonical 1-letter code or 'X'
        assert(d['residue_aa'] in residue_types_1)
        assert(d['ss'] in secondary_structure_types)
        d['bp_1'] = int(d['bp_1'])
        d['bp_2'] = int(d['bp_2'])
        d['acc'] = int(d['acc'])
        d['3LC'] = residue_type_1to3.get(d['dssp_residue_aa'])

    def compute_burial(self, d):
        cut_off = self.cut_off
        if d['3LC'] == 'UNK':
            d['is_buried'] = None
            d['exposure'] = None
        else:
            acc = float(d['acc']) / float(self.residue_max_acc[d['residue_aa']])
            d['exposure'] = acc
            if acc < self.cut_off:
                d['is_buried'] = True
            else:
                d['is_buried'] = False


class ComplexDSSP(MonomerDSSP):
    '''
    A class wrapper for DSSP.

    Note: This class does *not* strip the PDB file.

    Once initialized, the dssp element of the object should contain a mapping from protein chain IDs to dicts.
    The dict associated with a protein chain ID is a dict from PDB residue IDs to details about that residue.
    For example:
       dssp -> 'A' -> '  64 ' -> {
                                  '3LC': 'LEU',
                                  'acc': 171,
                                  'bp_1': 0,
                                  'bp_2': 0,
                                  'chain_id': 'I',
                                  'dssp_res_id': 10,
                                  'dssp_residue_aa': 'L',
                                  'exposure': 0.95,
                                  'is_buried': False,
                                  'pdb_res_id': '  64 ',
                                  'residue_aa': 'L',
                                  'sheet_label': ' ',
                                  'ss': None,
                                  'ss_details': '<      '}

    Description of the fields:
      - residue_aa and 3LC contain the residue 1-letter and 3-letter codes respectively;
      - acc is the number of water molecules in contact with this residue (according to DSSP);
      - exposure is a normalized measure of exposure where 0.0 denotes total burial and 1.0 denotes total exposure;
        - exposure is calculated by dividing the number of water molecules in contact with this residue (according to DSSP) by the residue_max_acc value from the appropriate value table;
      - is_buried is either None (could not be determined), True if exposure < cut_off, or False if exposure >= cut_off;
      - ss is the assigned secondary structure type, using the DSSP secondary structure types (see basics.py/dssp_secondary_structure_types). This value may be None if no secondary structure was assigned.

    Usage:
       d = DSSP.from_RCSB('1HAG')

       # access the dict directly
       print(d.dssp['I']['  64 ']['exposure'])
       print(d.dssp['I']['  64 ']['is_buried'])

       # use dot notation
       print(d.dsspb.I.get('  64 ').exposure)
       print(d.dsspb.I.get('  64 ').is_buried)

       # iterate through the residues
       for chain_id, mapping in d:
           for residue_id, residue_details in sorted(mapping.iteritems()):
               print(residue_id, residue_details['exposure'])

    '''

    @classmethod
    def from_pdb_contents(cls, pdb_contents, cut_off = 0.25, acc_array = 'Miller', tmp_dir = '/tmp', read_only = False):
        return cls(PDB(pdb_contents), cut_off = cut_off, acc_array = acc_array, tmp_dir = tmp_dir, read_only = read_only)

    @classmethod
    def from_pdb_filepath(cls, pdb_filepath, cut_off = 0.25, acc_array = 'Miller', tmp_dir = '/tmp', read_only = False):
        return cls(PDB(read_file(pdb_filepath)), cut_off = cut_off, acc_array = acc_array, tmp_dir = tmp_dir, read_only = read_only)

    @classmethod
    def from_RCSB(cls, pdb_id, cut_off = 0.25, acc_array = 'Miller', tmp_dir = '/tmp', read_only = False):
        return cls(PDB(retrieve_pdb(pdb_id)), cut_off = cut_off, acc_array = acc_array, tmp_dir = tmp_dir, read_only = read_only)

    def __init__(self, p, cut_off = 0.25, acc_array = 'Miller', tmp_dir = '/tmp', read_only = False):
        '''This function strips a PDB file to one chain and then runs DSSP on this new file.
           p should be a PDB object (see pdb.py).
        '''
        try:
            _Popen('.', shlex.split('mkdssp --version'))
        except:
            raise colortext.Exception('mkdssp does not seem to be installed in a location declared in the environment path.')

        self.cut_off = cut_off
        self.tmp_dir = tmp_dir
        self.residue_max_acc = residue_max_acc[acc_array]
        self.read_only = read_only
        if not self.read_only:
            self.pdb = p.clone()  # make a local copy in case this gets modified externally
        else:
            self.pdb = p
        self.chain_order = self.pdb.atom_chain_order
        self.dssp_output = None
        self.dssp = {}
        self.compute()
        self.chain_order = [c for c in self.chain_order if c in self.dssp]
        self.dsspb = NestedBunch(self.dssp)

    def compute(self):
        tmp_dir = self.tmp_dir
        if not self.read_only:
            pdb_object = self.pdb.clone()
        else:
            pdb_object = self.pdb  # in general, we should not be modifying the structure in this class
        input_filepath = write_temp_file(tmp_dir, pdb_object.get_content(), ftype = 'w', prefix = 'dssp_')
        output_filepath = write_temp_file(tmp_dir, '', ftype = 'w', prefix = 'dssp_')
        try:
            p = _Popen('.', shlex.split('mkdssp -i {input_filepath} -o {output_filepath}'.format(**locals())))
            if p.errorcode:
                if p.stderr.find('empty protein, or no valid complete residues') != -1:
                    raise MissingAtomException(p.stdout)
                else:
                    raise Exception('An error occurred while calling DSSP:\n%s' % p.stderr)

            self.dssp_output = read_file(output_filepath)
            self.dssp = self.parse_output()
        except MissingAtomException as e:
            os.remove(input_filepath)
            os.remove(output_filepath)
            raise
        except Exception as e:
            os.remove(input_filepath)
            os.remove(output_filepath)
            raise colortext.Exception('%s\n%s' % (str(e), traceback.format_exc()))
        os.remove(input_filepath)
        os.remove(output_filepath)

    def parse_output(self):
        d = {}
        dssp_output = self.dssp_output
        assert(dssp_output.startswith('===='))
        header_line = '  #  RESIDUE AA STRUCTURE BP1 BP2  ACC     N-H-->O    O-->H-N    N-H-->O    O-->H-N    TCO  KAPPA ALPHA  PHI   PSI    X-CA   Y-CA   Z-CA'
        idx = dssp_output.find(header_line)
        assert(idx != -1)
        data_lines = [l for l in dssp_output[idx + len(header_line):].split('\n') if l.strip()]
        for dl in data_lines:
            l = self.parse_data_line(dl)
            if l:
                d[l['chain_id']] = d.get(l['chain_id'], {})
                d[l['chain_id']][l['pdb_res_id']] = l
        return d
