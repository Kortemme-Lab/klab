#!/usr/bin/python
# encoding: utf-8
"""
scaffold_design_crystal.py
A PSE builder for scaffold/design/crystal structures.

Created by Shane O'Connor 2014.
The PyMOL commands are adapted from scripts developed and written by Roland A. Pache, Ph.D., Copyright (C) 2012, 2013.
"""

from tools.fs.fsio import write_file
from tools import colortext
from psebuilder import PyMOLSessionBuilder, create_pymol_selection_from_PDB_residue_ids

class ScaffoldDesignCrystalBuilder(PyMOLSessionBuilder):

    def __init__(self, pdb_containers, rootdir = '/tmp'):
        super(ScaffoldDesignCrystalBuilder, self).__init__(pdb_containers, rootdir)
        self.Scaffold = pdb_containers['Scaffold']
        self.Design = pdb_containers['Design']
        self.Crystal = pdb_containers.get('Crystal')

    def _create_input_files(self):
        #colortext.message('self.outdir: ' + self.outdir)
        write_file(self._filepath('scaffold.pdb'), self.Scaffold.pdb_contents)
        write_file(self._filepath('design.pdb'), self.Design.pdb_contents)
        if self.Crystal:
            write_file(self._filepath('crystal.pdb'), self.Crystal.pdb_contents)

    def _add_preamble(self):
        self.script.append("cd %(outdir)s" % self.__dict__)

    def _add_load_section(self):
        self.script.append("# load structures")
        if self.Crystal:
            self.script.append("load crystal.pdb, Crystal")
        self.script.append("load design.pdb, Design")
        self.script.append("load scaffold.pdb, Scaffold")

    def _add_view_settings_section(self):
        self.script.append('''
# set general view options
viewport 1200,800
hide eve
remove resn hoh

# set seq_view
bg_color white''')

    def _add_generic_chain_settings_section(self):
        self.script.append('''
show cartoon
util.cbc
show sticks, het
util.cnc

# set cartoon_fancy_helices
set cartoon_side_chain_helper
set cartoon_rect_length, 0.9
set cartoon_oval_length, 0.9
set stick_radius, 0.2
''')

    def _add_specific_chain_settings_section(self):
        self.script.append('''
# set cartoon_flat_sheets, off
show car, Design
color gray, Design
''')
        if self.Crystal:
            self.script.append('''
color forest, Crystal
show car, Crystal
''')

    def _add_superimposition_section(self):
        self.script.append("super Scaffold, Design")
        if self.Crystal:
            self.script.append("super Crystal, Design")

    def _add_orient_view_section(self):
        self.script.append('''
# orient view
set_view (0.750491261,   -0.332692802,   -0.570965469,  -0.572279274,    0.104703479,   -0.813287377,   0.330366731,    0.937145591,   -0.111799516,    0.000000000,    0.000000000, -129.595489502,    36.783428192,   36.119152069,   77.293815613,   112.102447510,  147.088562012,  -20.000000000 )
''')

    def _add_scaffold_view_section(self):
          self.script.append('''
# preset.ligands(selection="Scaffold")
hide lines, Scaffold
hide ribbon, Scaffold
show car, Scaffold
util.cbc Scaffold
disable Scaffold''')

    def _add_residue_highlighting_section(self):
        scaffold_selection = 'Scaffold and (%s)' % (create_pymol_selection_from_PDB_residue_ids(self.Scaffold.residues_of_interest))
        self.script.append('''select scaffold_residues, %s''' % scaffold_selection)
        self.script.append('''show sticks, scaffold_residues''')

        #self.script.append('set label_color, black')
        #self.script.append('label n. CA and Scaffold and chain A and i. 122, "A122" ')

        design_selection = 'Design and (%s)' % (create_pymol_selection_from_PDB_residue_ids(self.Design.residues_of_interest))
        self.script.append('''select design_residues, %s''' % design_selection)
        self.script.append('''show sticks, design_residues''')

        if self.Crystal:
            crystal_selection = 'Crystal and %s' % (create_pymol_selection_from_PDB_residue_ids(self.Crystal.residues_of_interest))
            self.script.append('''select crystal_residues, %s''' % crystal_selection)
            self.script.append('''show sticks, crystal_residues''')

        self.script.append('color brightorange, scaffold_residues')
        self.script.append('color tv_yellow, design_residues')

    def _add_raytracing_section(self):
        self.script.append('''
# ray tracing and output
select none
util.cnc
set two_sided_lighting, on
heavy_chain_residues=[]
light_chain_residues=[]
one_letter ={"VAL":"V", "ILE":"I", "LEU":"L", "GLU":"E", "GLN":"Q", "ASP":"D", "ASN":"N", "HIS":"H", "TRP":"W", "PHE":"F", "TYR":"Y", "ARG":"R", "LYS":"K", "SER":"S", "THR":"T", "MET":"M", "ALA":"A", "GLY":"G", "PRO":"P", "CYS":"C"}
''')
    def _add_postamble(self):
        self.script.append('''
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
        self._add_superimposition_section()
        self._add_orient_view_section()
        self._add_scaffold_view_section()
        self._add_residue_highlighting_section()
        self._add_raytracing_section()
        self._add_postamble()
        self.script = '\n'.join(self.script)
