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
        self.Design = pdb_containers.get('Design')

    def _create_input_files(self):
        #colortext.message('self.outdir: ' + self.outdir)
        write_file(self._filepath('scaffold.pdb'), self.Scaffold.pdb_contents)
        write_file(self._filepath('model.pdb'), self.Model.pdb_contents)
        if self.Design:
            write_file(self._filepath('design.pdb'), self.Design.pdb_contents)

    def _add_preamble(self):
        self.script.append("cd %(outdir)s" % self.__dict__)

    def _add_load_section(self):
        self.script.append("### Load the structures")
        if self.Design:
            self.script.append("load design.pdb, Design")
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
        if self.Design:
            self.script.append('''
# Design display
color forest, Design
show car, Design
''')

    def _add_superimposition_section(self):
        self.script.append('''
# Superimpose the structures
super Scaffold, RosettaModel''')
        if self.Design:
            self.script.append("super Design, RosettaModel")

    def _add_orient_view_section(self):
        self.script.append('''
# Orient view
set_view (0.750491261,   -0.332692802,   -0.570965469,  -0.572279274,    0.104703479,   -0.813287377,   0.330366731,    0.937145591,   -0.111799516,    0.000000000,    0.000000000, -129.595489502,    36.783428192,   36.119152069,   77.293815613,   112.102447510,  147.088562012,  -20.000000000 )
''')

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

        if self.Design:
            design_selection = 'Design and (%s)' % (create_pymol_selection_from_PDB_residue_ids(self.Design.residues_of_interest))
            self.script.append('''
### Design objects ###

# Design mutations
select Design_mutations, %(design_selection)s
create Design_mutations, %(design_selection)s
show sticks, Design_mutations
color violet, Design_mutations

# Design HETATMs - create and display
if cmd.count_atoms('Design and het and !(resn CSE+SEC+MSE)') > 0: cmd.create('Design_HETATMs', 'Design and het and !(resn CSE+SEC+MSE)'); show sticks, Design_HETATMs
''' % vars())

    def _add_raytracing_section(self):
        self.script.append('''
# Ray tracing and output
select none
util.cnc
set two_sided_lighting, on

# Unused - left over from Roland's project
heavy_chain_residues=[]
light_chain_residues=[]
one_letter ={"VAL":"V", "ILE":"I", "LEU":"L", "GLU":"E", "GLN":"Q", "ASP":"D", "ASN":"N", "HIS":"H", "TRP":"W", "PHE":"F", "TYR":"Y", "ARG":"R", "LYS":"K", "SER":"S", "THR":"T", "MET":"M", "ALA":"A", "GLY":"G", "PRO":"P", "CYS":"C"}
''')
    def _add_postamble(self):
        self.script.append('''
# Set zoom
zoom

# Re-order the objects in the right pane
order *,yes
order Scaffold_mutations, location=bottom
order RosettaModel_mutations, location=bottom
order Design_mutations, location=bottom

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
