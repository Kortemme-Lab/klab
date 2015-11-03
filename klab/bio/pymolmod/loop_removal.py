#!/usr/bin/python
# encoding: utf-8
"""
loop_removal.py
A PSE builder for displaying a structure, its removed loop residues, and its removed sidechains.

Created by Shane O'Connor 2015.
"""

import copy
from klab.fs.fsio import write_file
from klab import colortext
from psebuilder import PyMOLSessionBuilder, create_pymol_selection_from_PDB_residue_ids
from colors import ColorScheme


loops_color_scheme = ColorScheme({
    'Main' : {
        'bb' : 'grey30',
        'hetatm' : 'grey60',
        'mutations' : 'grey80'
    },
    'Loop' : {
        'bb' : 'green',
        'hetatm' : 'warmpink',
        'mutations' : 'magenta'
    },
    'LoopShell'  : {
        'bb' : 'brightorange',
        'hetatm' : 'deepolive',
        'mutations' : 'yellow'
    },
})


class LoopRemovalBuilder(PyMOLSessionBuilder):

    def __init__(self, pdb_containers, settings = {}, rootdir = '/tmp'):
        super(LoopRemovalBuilder, self).__init__(pdb_containers, settings, rootdir)
        main_label = settings.get('Main', 'Main')
        loop_label = settings.get('Loop', 'Loop')
        self.main_label = main_label
        self.loop_label = loop_label
        self.MainStructure = pdb_containers.get(main_label)
        self.Loop = pdb_containers[loop_label]
        self.color_scheme = loops_color_scheme

    def _create_input_files(self):
        write_file(self._filepath('main.pdb'), self.MainStructure.pdb_contents)
        write_file(self._filepath('loop.pdb'), self.Loop.pdb_contents)

    def _add_preamble(self):
        self.script.append("cd %(outdir)s" % self.__dict__)

    def _add_load_section(self):
        self.script.append("### Load the structures")
        self.script.append("load main.pdb, {0}".format(self.main_label))
        self.script.append("load loop.pdb, {0}".format(self.loop_label))

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

# Main structure display
color {0}, {1}

# Loop display
hide lines, {3}
hide ribbon, {3}
show car, {3}
show sticks, {3}
color {2}, {3}
'''.format(self.color_scheme['Main.bb'], self.main_label, self.color_scheme['LoopShell.bb'], self.loop_label))

    def _add_orient_view_section(self):
        pass

    def _add_main_structure_view_section(self):
        self.script.append('''
# Main structure view options
hide lines, {0}
hide ribbon, {0}
show car, {0}
show sticks, {0}
util.cbc Scaffold'''.format(self.main_label))

    def _add_residue_highlighting_section(self):

        loop_label = self.loop_label
        loop_selection = '{0} and ({1})'.format(self.loop_label, create_pymol_selection_from_PDB_residue_ids(self.Loop.residues_of_interest))
        loop_color = self.color_scheme['Loop.bb']

        self.script.append('''
### Loop objects ###

show car, %(loop_selection)s
show sticks, %(loop_selection)s
color %(loop_color)s, %(loop_selection)s
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

# Re-order the objects in the right pane
order *,yes
order {0}_residues_s, location=bottom

save session.pse
quit
'''.format(self.loop_label))

    def _create_script(self):
        self.script = []
        self._add_preamble()
        self._add_load_section()
        self._add_view_settings_section()
        self._add_generic_chain_settings_section()
        self._add_specific_chain_settings_section()
        self._add_orient_view_section()
        self._add_main_structure_view_section()
        self._add_residue_highlighting_section()
        self._add_raytracing_section()
        self._add_postamble()
        self.script = '\n'.join(self.script)
