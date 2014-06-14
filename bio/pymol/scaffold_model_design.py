#!/usr/bin/python
# encoding: utf-8
"""
scaffold_model_design.py
A PSE builder for scaffold/model/design structures.

Created by Shane O'Connor 2014.
The PyMOL commands are adapted from scripts developed and written by Roland A. Pache, Ph.D., Copyright (C) 2012, 2013.
"""

from tools.fs.fsio import write_file
from tools import colortext
from psebuilder import PyMOLSessionBuilder, create_pymol_selection_from_PDB_residue_ids

class ScaffoldModelDesignBuilder(PyMOLSessionBuilder):

    def __init__(self, pdb_containers, settings = {}, rootdir = '/tmp'):
        super(ScaffoldModelDesignBuilder, self).__init__(pdb_containers, settings, rootdir)
        self.Scaffold = pdb_containers['Scaffold']
        self.Model = pdb_containers['Model']
        self.ExpStructure = pdb_containers.get('ExpStructure')

    def _create_input_files(self):
        #colortext.message('self.outdir: ' + self.outdir)
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
bg_color %(background-color)s
''' % self.settings)

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
# RosettaModel display
show car, RosettaModel
color gray, RosettaModel
''')
        if self.ExpStructure:
            self.script.append('''
# ExpStructure display
color forest, ExpStructure
show car, ExpStructure
''')

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
util.cbc Scaffold
disable Scaffold''')

    def _add_residue_highlighting_section(self):
        scaffold_selection = 'Scaffold and (%s)' % (create_pymol_selection_from_PDB_residue_ids(self.Scaffold.residues_of_interest))
        self.script.append('''
### Scaffold objects ###

# Scaffold mutations
select Scaffold_mutations, %(scaffold_selection)s
create Scaffold_mutations, %(scaffold_selection)s
show sticks, Scaffold_mutations
color brightorange, Scaffold_mutations

# Scaffold HETATMs - create
if cmd.count_atoms('Scaffold and het and !(resn CSE+SEC+MSE)') > 0: cmd.create('Scaffold_HETATMs', 'Scaffold and het and !(resn CSE+SEC+MSE)');
''' % vars())

        #self.script.append('set label_color, black')
        #self.script.append('label n. CA and Scaffold and chain A and i. 122, "A122" ')

        model_selection = 'RosettaModel and (%s)' % (create_pymol_selection_from_PDB_residue_ids(self.Model.residues_of_interest))

        self.script.append('''
### Rosetta model objects ###

# Rosetta model mutations
select RosettaModel_mutations, %(model_selection)s
create RosettaModel_mutations, %(model_selection)s
show sticks, RosettaModel_mutations
color tv_yellow, RosettaModel_mutations

# Rosetta model HETATMs - create and display
if cmd.count_atoms('RosettaModel and het and !(resn CSE+SEC+MSE)') > 0: cmd.create('RosettaModel_HETATMs', 'RosettaModel and het and !(resn CSE+SEC+MSE)'); show sticks, RosettaModel_HETATMs
''' % vars())

        if self.ExpStructure:
            exp_structure_selection = 'ExpStructure and (%s)' % (create_pymol_selection_from_PDB_residue_ids(self.ExpStructure.residues_of_interest))
            self.script.append('''
### ExpStructure objects ###

# ExpStructure mutations
select ExpStructure_mutations, %(exp_structure_selection)s
create ExpStructure_mutations, %(exp_structure_selection)s
show sticks, ExpStructure_mutations
color violet, ExpStructure_mutations

# ExpStructure HETATMs - create and display
if cmd.count_atoms('ExpStructure and het and !(resn CSE+SEC+MSE)') > 0: cmd.create('ExpStructure_HETATMs', 'ExpStructure and het and !(resn CSE+SEC+MSE)'); show sticks, ExpStructure_HETATMs
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
# Set zoom
zoom

# Re-order the objects in the right pane
order *,yes
order Scaffold_mutations, location=bottom
order RosettaModel_mutations, location=bottom
order ExpStructure_mutations, location=bottom

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
