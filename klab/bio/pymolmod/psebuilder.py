#!/usr/bin/python
# encoding: utf-8
"""
psebuilder.py
Generic functions used to create PyMOL session builder objects.

Created by Shane O'Connor 2014.
"""

import os
import shutil
import string

from klab.fs.fsio import read_file, create_temp_755_path, write_file
from klab import colortext
from klab import process as tprocess
from colors import ColorScheme

def create_pymol_selection_from_PDB_residue_ids(residue_list):
    '''Elements of residue_list should be strings extracted from PDB lines from position 21-26 inclusive (zero-indexing)
       i.e. the chain letter concatenated by the 5-character (including insertion code) residue ID.'''
    residues_by_chain = {}
    for residue_id in residue_list:
        chain_id = residue_id[0]
        pruned_residue_id = residue_id[1:]
        residues_by_chain[chain_id] = residues_by_chain.get(chain_id, [])
        residues_by_chain[chain_id].append(pruned_residue_id)

    str = []
    for chain_id, residue_list in sorted(residues_by_chain.iteritems()):
        str.append('(chain %s and resi %s)' % (chain_id, '+'.join(map(string.strip, sorted(residue_list)))))
    return ' or '.join(str)

class PDBContainer(object):

    def __init__(self, pymol_name, pdb_contents, residues_of_interest = []):
        self.pymol_name = pymol_name
        self.pdb_contents = pdb_contents
        self.residues_of_interest = residues_of_interest

    @staticmethod
    def from_file(pymol_name, pdb_filename, residues_of_interest = []):
        return PDBContainer(pymol_name, read_file(pdb_filename), residues_of_interest)

    @staticmethod
    def from_triples(tpls):
        pdb_containers = {}
        for t in tpls:
            pdb_containers[t[0]] = PDBContainer(t[0], t[1], t[2])
        return pdb_containers

    @staticmethod
    def from_filename_triple(tpls):
        pdb_containers = {}
        for t in tpls:
            pdb_containers[t[0]] = PDBContainer.from_file(t[0], t[1], t[2])
        return pdb_containers

    @staticmethod
    def from_content_triple(tpls):
        pdb_containers = {}
        for t in tpls:
            pdb_containers[t[0]] = PDBContainer(t[0], t[1], t[2])
        return pdb_containers


class BatchBuilder(object):

    def __init__(self, pymol_executable = 'pymol'):
        self.visualization_shell = 6
        self.visualization_pymol = pymol_executable # the command used to run pymol - change as necessary for Mac OS X
        self.PSE_files = []
        self.PSE_scripts = []

    def run(self, builder_class, list_of_pdb_containers, settings = {}):
        PSE_files = []
        PSE_scripts = []
        for pdb_containers in list_of_pdb_containers:
            b = builder_class(pdb_containers, settings)
            b.visualization_shell = self.visualization_shell
            b.visualization_pymol = self.visualization_pymol
            b.run()
            PSE_files.append(b.PSE)
            PSE_scripts.append(b.script)

        self.PSE_files = PSE_files
        self.PSE_scripts = PSE_scripts

        return PSE_files


class PyMOLSessionBuilder(object):

    def __init__(self, pdb_containers, settings = {}, rootdir = '/tmp'):
        self.visualization_shell = 6
        self.visualization_pymol = 'pymol'
        self.pdb_containers = pdb_containers
        self.match_posfiles_interface_distance = 15
        self.rootdir = rootdir
        self.PSE = None
        self.outdir = None
        self.script = None
        self.stdout = None
        self.stderr = None
        self.return_code = None
        self.settings = {'colors' : {'global' : {'background-color' : 'black'}}}
        self.settings.update(settings)
        self.color_scheme = ColorScheme(settings.get('colors', {}))
        del self.settings['colors'] # to avoid confusion, remove the duplicated dict as the ColorScheme object may get updated

    def __del__(self):
        if self.outdir:
            if os.path.exists(self.outdir):
                shutil.rmtree(self.outdir)

    def _filepath(self, filename):
        return os.path.join(self.outdir, filename)

    def _create_temp_directory(self):
        self.outdir = create_temp_755_path(self.rootdir)

    def _create_input_files(self):
        raise Exception('Subclasses must implement this function.')

    def _create_script(self):
        raise Exception('Subclasses must implement this function.')

    def run(self):

        # Create input files
        self._create_temp_directory()
        self._create_input_files()
        self._create_script()
        write_file(self._filepath('script.pml'), self.script)

        # Run PyMOL
        #colortext.message(self.visualization_pymol +' -c ' + self._filepath('script.pml'))
        po = tprocess.Popen(self.outdir, [self.visualization_pymol, '-c', self._filepath('script.pml')])
        #colortext.message(po.stdout)
        #colortext.warning(po.errorcode)
        #colortext.error(po.stderr)
        self.stdout = po.stdout
        self.stderr = po.stderr
        self.return_code = po.errorcode

        if self.return_code != 0:
            raise Exception('Error: %s' % str(self.stderr))

        pse_path = self._filepath('session.pse')
        if os.path.exists(pse_path):
            self.PSE = read_file(pse_path, binary = True)


