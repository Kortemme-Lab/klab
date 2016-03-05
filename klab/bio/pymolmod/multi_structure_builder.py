#!/usr/bin/python
# encoding: utf-8
"""
multi_structure_builder.py
A PSE builder for a generic collection of multiple structures.
This builder uses the PyMOLStructure class from psebuilder.py.

Created by Shane O'Connor 2016.
"""

from klab.fs.fsio import write_file
from klab import colortext
from psebuilder import PyMOLSessionBuilder, create_pymol_selection_from_PDB_residue_ids
from colors import default_display_scheme

# Notes:
#
# The select or cmd.select commands create the selection objects e.g. '(structurename_roi_s)' in the right pane. These
# are just selection sets so clicking on the name in the pane only results in a selection.
#
# The create or cmd.create commands create an object e.g. structurename_roi in the right pane. Clicking on this name
# toggles whether this selection is shown or not. To set up a default view, follow the create command with a show command
# e.g. show sticks, structurename_roi.
#
# However, if you want the selection to be hidden when the PSE is loaded, you need to use the disable command, *not the hide command*
# e.g. disable spheres_structurename_HETATMs.
#
# There is another subtlety behavior difference between loading a PSE file versus pasting commands into the terminal of a PyMOL window.
# If you write e.g.
#     select structurename_roi, [some selection string]
#     create structurename_roi, [some selection string]
# into the terminal, two objects are created in the right pane. However, if you save the PSE and reload it, only one of these
# objects works as expected. Therefore, if you need both, use two separately named objects. Below, I instead write the equivalent of:
#     select structurename_roi_s, [some selection string]
#     create structurename_roi, [some selection string]
# to create two distinct objects. The '_s' is just my arbitrary convention to denote that the object came from a select command.


class MultiStructureBuilder(PyMOLSessionBuilder):


    def __init__(self, structures, settings = {}, rootdir = '/tmp'):
        super(MultiStructureBuilder, self).__init__(structures, settings, rootdir)
        self.structures = self.pdb_containers


    def _create_input_files(self):
        for s in self.structures:
            write_file(self._filepath('{0}.pdb'.format(s.structure_name)), str(s.pdb_object))


    def _add_preamble(self):
        self.script.append("cd %(outdir)s" % self.__dict__)


    def _add_load_section(self):
        self.script.append("### Load the structures")
        for s in self.structures:
            self.script.append('load {0}.pdb, {0}'.format(s.structure_name))


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

# color by chain
util.cbc

# Hide selenomethionines and selenocysteines
hide sticks, resn CSE+SEC+MSE

# Color atoms according to type
util.cnc

set cartoon_side_chain_helper
set cartoon_rect_length, 0.9
set cartoon_oval_length, 0.9
set stick_radius, 0.2
''')


    def _add_specific_chain_settings_section(self):
        # Thursday resume here - todo use s.backbone_display to get 'cartoon' etc.

        for s in self.structures:
            self.script.append('''
# {0} display
hide lines, {0}
hide ribbon, {0}
show {1}, {0}
color {2}, {0}
'''.format(s.structure_name, s.backbone_display or self.display_scheme['GenericProtein'].backbone_display, s.backbone_color or self.display_scheme['GenericProtein'].backbone_color))
            for c, clr in s.chain_colors.iteritems():
                self.script.append('set_color {0}_{1} = {2}'.format(s.structure_name, c, clr))
                self.script.append('color {0}_{1}, {0} and chain {1}'.format(s.structure_name, c))

            if not s.visible:
                self.script.append('disable {0}\n'.format(s.structure_name))


    def _add_superimposition_section(self):
        for i in xrange(1, len(self.structures)):
            self.script.append('''
# Superimpose the structures on backbone atoms
align {0} and name n+ca+c+o, {1} and name n+ca+c+o
#super {0}, {1}'''.format(self.structures[i].structure_name, self.structures[0].structure_name))


    def _add_orient_view_section(self):
        pass


    def _add_residue_highlighting_section(self):

        for s in self.structures:

            residue_selection = '{0} and {1}'.format(s.structure_name, create_pymol_selection_from_PDB_residue_ids(s.residues_of_interest))
            self.script.append('''
### {0} objects ###

# {0} residues of interest

has_rois = cmd.count_atoms('{1}') > 0
if has_rois: cmd.select('{0}_roi_s', '{1}');
if has_rois: cmd.create('{0}_roi', '{1}');
if has_rois: cmd.show('{2}', '{0}_roi')
if has_rois: cmd.color('{3}', '{0}_roi')
'''.format(s.structure_name, residue_selection, s.sidechain_display or self.display_scheme['GenericProtein'].sidechain_display, s.sidechain_color or self.display_scheme['GenericProtein'].sidechain_color))


    def _add_hetatm_highlighting_section(self):

        for s in self.structures:

            self.script.append('''
### {0} HETATMs ###

has_hetatms = cmd.count_atoms('{0} and het and !(resn CSE+SEC+MSE)') > 0
if has_hetatms: cmd.create('{0}_HETATMs', '{0} and het and !(resn CSE+SEC+MSE)');
if has_hetatms: cmd.show('{1}', '{0}_HETATMs')
if has_hetatms: cmd.disable('{0}_HETATMs')
if has_hetatms: cmd.create('spheres_{0}_HETATMs', '{0} and het and !(resn CSE+SEC+MSE)');
if has_hetatms: cmd.show('spheres', 'spheres_{0}_HETATMs')
if has_hetatms: cmd.disable('spheres_{0}_HETATMs')
if has_hetatms: cmd.color('{2}', '{0}_roi')
'''.format(s.structure_name, s.hetatm_display or self.display_scheme['GenericProtein'].hetatm_display, s.hetatm_color or self.display_scheme['GenericProtein'].hetatm_color))


    def _add_residue_label_section(self):
        # Note: This only creates one label per residue position.
        #       This will work fine for mutant/wildtype ensembles but not in general.
        #       Use PyMOLStructure.label_all_residues_of_interest to fix this when necessary.
        residue_labels = {}
        self.script.append('\nset label_color, black\n')
        for s in self.structures:
            for roi in s.residues_of_interest:
                residue_labels[roi] = s

        for roi, s in residue_labels.iteritems():
            self.script.append('\nlabel n. O and {0} and chain {1} and i. {2}, "{1}{2}"\n'.format(s.structure_name, roi[0], roi[1:].strip()))


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
#order *,yes
''')

        for s in self.structures:
            self.script.append('''order {0}_roi, location=bottom'''.format(s.structure_name))

        for s in self.structures:
            self.script.append('''order spheres_{0}_HETATMs, location=bottom'''.format(s.structure_name))

        self.script.append('order input, location=top')

        self.script.append('''
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
        self._add_residue_highlighting_section()
        self._add_hetatm_highlighting_section()
        self._add_residue_label_section()
        self._add_raytracing_section()
        self._add_postamble()
        self.script = '\n'.join(self.script)
