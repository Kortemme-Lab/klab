#!/usr/bin/python
# encoding: utf-8
"""
scaffold_model_design.py
A PSE builder for scaffold/model/design structures.

Created by Shane O'Connor 2014.
The PyMOL commands are adapted from scripts developed and written by Roland A. Pache, Ph.D., Copyright (C) 2012, 2013.
"""

from klab.fs.fsio import write_file
from klab import colortext
from psebuilder import PyMOLSessionBuilder, create_pymol_selection_from_PDB_residue_ids

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

class ScaffoldModelDesignBuilder(PyMOLSessionBuilder):

    def __init__(self, pdb_containers, settings = {}, rootdir = '/tmp'):
        super(ScaffoldModelDesignBuilder, self).__init__(pdb_containers, settings, rootdir)
        self.Scaffold = pdb_containers.get('Scaffold')
        self.Model = pdb_containers['Model']
        self.ExpStructure = pdb_containers.get('ExpStructure')

    def _create_input_files(self):
        #colortext.message('self.outdir: ' + self.outdir)
        if self.Scaffold:
            write_file(self._filepath('scaffold.pdb'), self.Scaffold.pdb_contents)
        write_file(self._filepath('model.pdb'), self.Model.pdb_contents)
        if self.ExpStructure:
            write_file(self._filepath('design.pdb'), self.ExpStructure.pdb_contents)

    def _add_preamble(self):
        self.script.append("cd %(outdir)s" % self.__dict__)

    def _add_load_section(self):
        self.script.append("### Load the structures")
        if self.ExpStructure:
            self.script.append("load design.pdb, ExpStructure")
        self.script.append("load model.pdb, RosettaModel")
        self.script.append("load scaffold.pdb, Scaffold")

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

# Scaffold display
color %(Scaffold.bb)s, Scaffold

# RosettaModel display
show car, RosettaModel
color %(RosettaModel.bb)s, RosettaModel
''' % self.color_scheme)

        if self.ExpStructure:
            self.script.append('''
# ExpStructure display
show car, ExpStructure
color %(ExpStructure.bb)s, ExpStructure
''' % self.color_scheme)

    def _add_superimposition_section(self):
        self.script.append('''
# Superimpose the structures
super Scaffold, RosettaModel''')
        if self.ExpStructure:
            self.script.append("super ExpStructure, RosettaModel")

    def _add_orient_view_section(self):
        pass

    def _add_scaffold_view_section(self):
        self.script.append('''
# Scaffold view options
hide lines, Scaffold
hide ribbon, Scaffold
show car, Scaffold
util.cbc Scaffold''')
        if self.ExpStructure:
            # Hide the scaffold if there is an experimental structure
            self.script.append('''
disable Scaffold''')

    def _add_residue_highlighting_section(self):
        if self.Scaffold:
            scaffold_selection = 'Scaffold and (%s)' % (create_pymol_selection_from_PDB_residue_ids(self.Scaffold.residues_of_interest))
            self.script.append('''
### Scaffold objects ###

# Scaffold mutations

has_mutations = cmd.count_atoms('%(scaffold_selection)s') > 0
if has_mutations: cmd.select('Scaffold_mutations_s', '%(scaffold_selection)s');
if has_mutations: cmd.create('Scaffold_mutations', '%(scaffold_selection)s');
if has_mutations: cmd.show('sticks', 'Scaffold_mutations')
''' % vars())

            self.script.append('''
if has_mutations: cmd.color('%(Scaffold.mutations)s', 'Scaffold_mutations')

# Scaffold HETATMs - create
has_hetatms = cmd.count_atoms('Scaffold and het and !(resn CSE+SEC+MSE)') > 0
if has_hetatms: cmd.create('Scaffold_HETATMs', 'Scaffold and het and !(resn CSE+SEC+MSE)');
if has_hetatms: cmd.show('sticks', 'Scaffold_HETATMs')
if has_hetatms: cmd.disable('Scaffold_HETATMs')
if has_hetatms: cmd.create('spheres_Scaffold_HETATMs', 'Scaffold and het and !(resn CSE+SEC+MSE)');
if has_hetatms: cmd.show('spheres', 'spheres_Scaffold_HETATMs')
if has_hetatms: cmd.disable('spheres_Scaffold_HETATMs')
''' % self.color_scheme)

        #self.script.append('set label_color, black')
        #self.script.append('label n. CA and Scaffold and chain A and i. 122, "A122" ')

        model_selection = 'RosettaModel and (%s)' % (create_pymol_selection_from_PDB_residue_ids(self.Model.residues_of_interest))

        self.script.append('''
### Rosetta model objects ###

# Rosetta model mutations

has_mutations = cmd.count_atoms('%(model_selection)s') > 0
if has_mutations: cmd.select('RosettaModel_mutations_s', '%(model_selection)s');
if has_mutations: cmd.create('RosettaModel_mutations', '%(model_selection)s');
if has_mutations: cmd.show('sticks', 'RosettaModel_mutations')
''' % vars())

        self.script.append('''
if has_mutations: cmd.color('%(RosettaModel.mutations)s', 'RosettaModel_mutations')

# Rosetta model HETATMs - create and display
has_hetatms = cmd.count_atoms('RosettaModel and het and !(resn CSE+SEC+MSE)') > 0
if has_hetatms: cmd.create('RosettaModel_HETATMs', 'RosettaModel and het and !(resn CSE+SEC+MSE)');
if has_hetatms: cmd.show('sticks', 'RosettaModel_HETATMs')
if has_hetatms: cmd.create('spheres_RosettaModel_HETATMs', 'RosettaModel and het and !(resn CSE+SEC+MSE)');
if has_hetatms: cmd.show('spheres', 'spheres_RosettaModel_HETATMs')
if has_hetatms: cmd.disable('spheres_RosettaModel_HETATMs')
''' % self.color_scheme)

        if self.ExpStructure:
            exp_structure_selection = 'ExpStructure and (%s)' % (create_pymol_selection_from_PDB_residue_ids(self.ExpStructure.residues_of_interest))
            self.script.append('''
### ExpStructure objects ###

# ExpStructure mutations
has_mutations = cmd.count_atoms('%(exp_structure_selection)s') > 0
if has_mutations: cmd.select('ExpStructure_mutations_s', '%(exp_structure_selection)s');
if has_mutations: cmd.create('ExpStructure_mutations', '%(exp_structure_selection)s');
if has_mutations: cmd.show('sticks', 'ExpStructure_mutations')
''' % vars())

            self.script.append('''if has_mutations: cmd.color('%(ExpStructure.mutations)s', 'ExpStructure_mutations')

# ExpStructure HETATMs - create and display
has_hetatms = cmd.count_atoms('ExpStructure and het and !(resn CSE+SEC+MSE)') > 0
if has_hetatms: cmd.create('ExpStructure_HETATMs', 'ExpStructure and het and !(resn CSE+SEC+MSE)');
if has_hetatms: cmd.show('sticks', 'ExpStructure_HETATMs')
if has_hetatms: cmd.create('spheres_ExpStructure_HETATMs', 'ExpStructure and het and !(resn CSE+SEC+MSE)');
if has_hetatms: cmd.show('spheres', 'spheres_ExpStructure_HETATMs')
if has_hetatms: cmd.disable('spheres_ExpStructure_HETATMs')
#ExpStructure and het and !(resn CSE+SEC+MSE)')
''' % self.color_scheme)

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

# Re-order the objects in the right pane
order *,yes
order Scaffold_mutations_s, location=bottom
order RosettaModel_mutations_s, location=bottom
order ExpStructure_mutations_s, location=bottom
order spheres_Scaffold_HETATMs, location=bottom
order spheres_RosettaModel_HETATMs, location=bottom
order spheres_ExpStructure_HETATMs, location=bottom

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
        self._add_superimposition_section()
        self._add_orient_view_section()
        self._add_scaffold_view_section()
        self._add_residue_highlighting_section()
        self._add_raytracing_section()
        self._add_postamble()
        self.script = '\n'.join(self.script)
        