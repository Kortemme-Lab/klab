#!/usr/bin/python
# encoding: utf-8
"""
single_structure.py
A PSE builder for single structures.

Created by Shane O'Connor 2014.
The PyMOL commands are adapted from scripts developed and written by Roland A. Pache, Ph.D., Copyright (C) 2012, 2013.
"""

from klab.fs.fsio import write_file
from klab import colortext
from psebuilder import BatchBuilder, PDBContainer, PyMOLSessionBuilder, create_pymol_selection_from_PDB_residue_ids

# Notes:
#
# The select or cmd.select commands create the selection objects e.g. '(ExpStructure_mutations_s)' in the right pane. These
# are just selection sets so clicking on the name in the pane only results in a selection.
#
# The create or cmd.create commands create an object e.g. ExpStructure_mutations in the right pane. Clicking on this name
# toggles whether this selection is shown or not. To set up a default view, follow the create command with a show command
# e.g. show sticks, Scaffold_mutations.
#
# However, if you want the selection to be hidden when the PSE is loaded, you need to use the disable command, *not the hide command*
# e.g. disable spheres_Scaffold_HETATMs.
#
# There is another subtlety behavior difference between loading a PSE file versus pasting commands into the terminal of a PyMOL window.
# If you write e.g.
#     select Scaffold_mutations, [some selection string]
#     create Scaffold_mutations, [some selection string]
# into the terminal, two objects are created in the right pane. However, if you save the PSE and reload it, only one of these
# objects works as expected. Therefore, if you need both, use two separately named objects. Below, I instead write the equivalent of:
#     select Scaffold_mutations_s, [some selection string]
#     create Scaffold_mutations, [some selection string]
# to create two distinct objects. The '_s' is just my arbitrary convention to denote that the object came from a select command.

def create_single_structure_pse(structure_name, structure_content, residue_ids_of_interest, pymol_executable = 'pymol', settings = {}):
    ''' Generates the PyMOL session for the scaffold, model, and design structures.
        Returns this session and the script which generated it.'''
    b = BatchBuilder(pymol_executable = pymol_executable)
    PSE_files = b.run(SingleStructureBuilder, [{structure_name : PDBContainer(structure_name, structure_content, residue_ids_of_interest)}], settings = settings)
    return PSE_files[0], b.PSE_scripts[0]


class SingleStructureBuilder(PyMOLSessionBuilder):

    def __init__(self, pdb_containers, settings = {}, rootdir = '/tmp'):
        super(SingleStructureBuilder, self).__init__(pdb_containers, settings, rootdir)
        assert(len(pdb_containers) == 1)
        self.structure = pdb_containers[pdb_containers.keys()[0]]

    def _create_input_files(self):
        write_file(self._filepath('%s.pdb' % self.structure.pymol_name), self.structure.pdb_contents)

    def _add_preamble(self):
        self.script.append("cd %(outdir)s" % self.__dict__)

    def _add_load_section(self):
        self.script.append("### Load the structures")
        self.script.append("load %s.pdb, %s" % (self.structure.pymol_name, self.structure.pymol_name))

    def _add_view_settings_section(self):
        self.script.append('''
# Set general view options and hide waters
viewport 1200,800

hide eve

remove resn hoh
bg_color %(global.background-color)s
''' % self.color_scheme)

    def _add_generic_chain_settings_section(self):
        self.script.append('''
# Set generic chain and HETATM view options
show cartoon
util.cbc

# Hide selenomethionines and selenocysteines
hide sticks, resn CSE+SEC+MSE
util.cnc

set cartoon_side_chain_helper
set cartoon_rect_length, 0.9
set cartoon_oval_length, 0.9
set stick_radius, 0.2
''')

    def _add_specific_chain_settings_section(self):
        self.script.append('''
# Structure display
show car, %s''' % self.structure.pymol_name)
        self.script.append('''
color %s, %s
''' % (self.color_scheme['RosettaModel.bb'], self.structure.pymol_name))


    def _add_residue_highlighting_section(self):
        if self.structure.residues_of_interest:
            pymol_name = self.structure.pymol_name
            structure_selection = '%s and (%s)' % (self.structure.pymol_name, create_pymol_selection_from_PDB_residue_ids(self.structure.residues_of_interest))

            self.script.append('''
    ### Structure objects ###

    # Structure residues

    has_mutations = cmd.count_atoms('%(structure_selection)s') > 0
    if has_mutations: cmd.select('%(pymol_name)s_mutations_s', '%(structure_selection)s');
    if has_mutations: cmd.create('%(pymol_name)s_mutations', '%(structure_selection)s');
    if has_mutations: cmd.show('sticks', '%(pymol_name)s_mutations')
    ''' % vars())

            self.script.append('''
    if has_mutations: cmd.color('%s', '%s_mutations')''' % (self.color_scheme['RosettaModel.mutations'], pymol_name))

            self.script.append('''
    # Rosetta model HETATMs - create and display
    has_hetatms = cmd.count_atoms('%(pymol_name)s and het and !(resn CSE+SEC+MSE)') > 0
    if has_hetatms: cmd.create('%(pymol_name)s_HETATMs', '%(pymol_name)s and het and !(resn CSE+SEC+MSE)');
    if has_hetatms: cmd.show('sticks', '%(pymol_name)s_HETATMs')
    if has_hetatms: cmd.create('spheres_%(pymol_name)s_HETATMs', '%(pymol_name)s and het and !(resn CSE+SEC+MSE)');
    if has_hetatms: cmd.show('spheres', 'spheres_%(pymol_name)s_HETATMs')
    if has_hetatms: cmd.disable('spheres_%(pymol_name)s_HETATMs')
    ''' % vars())

    def _add_raytracing_section(self):
        self.script.append('''
# Atom coloring
select none
util.cnc

# Set lighting
set two_sided_lighting, on
''')
    def _add_postamble(self):
        self.script.append('''
# Show only polar hydrogens
hide (hydro)

# Set zoom
zoom

save session.pse
quit
''')

    def _create_script(self):
        self.script = []
        self._add_preamble()
        self._add_load_section()
        self._add_view_settings_section()
        self._add_generic_chain_settings_section()
        self._add_specific_chain_settings_section()
        self._add_residue_highlighting_section()
        self._add_raytracing_section()
        self._add_postamble()
        self.script = '\n'.join(self.script)
        