#!/usr/bin/python
# encoding: utf-8
"""
scaffold_design_crystal.py
A PSE builder for scaffold/design/ligand structures.

Created by Shane O'Connor 2014.
The PyMOL commands are adapted from scripts developed and written by Roland A. Pache, Ph.D., Copyright (C) 2012, 2013.
"""

from tools.fs.fsio import write_file
from tools import colortext
from psebuilder import PyMOLSessionBuilder

class ScaffoldDesignLigandBuilder(PyMOLSessionBuilder):

    def __init__(self, pdb_containers, rootdir = '/tmp'):
        super(ScaffoldDesignLigandBuilder, self).__init__(pdb_containers, rootdir)
        self.Scaffold = pdb_containers['Scaffold']
        self.Design = pdb_containers['Design']
        self.Crystal = pdb_containers.get('Crystal')

    def _create_input_files(self):
        colortext.message('self.outdir: ' + self.outdir)
        write_file(self._filepath('scaffold.pdb'), self.Scaffold.pdb_contents)
        write_file(self._filepath('design.pdb'), self.Design.pdb_contents)
        if self.Crystal:
            write_file(self._filepath('crystal.pdb'), self.Crystal.pdb_contents)


    def _create_script(self):
        script = '''
# load structures
cd %(outdir)s''' % self.__dict__
        if self.Crystal:
            script += '''
load crystal.pdb, Crystal'''
        script += '''
load design.pdb, Design
load scaffold.pdb, Scaffold

# set general view options
viewport 1200,800
hide eve

# set seq_view
bg_color white

# set cartoon_fancy_helices
set cartoon_side_chain_helper
set cartoon_rect_length, 0.9
set cartoon_oval_length, 0.9
set stick_radius, 0.2

# set cartoon_flat_sheets, off
show car, Design'''
        if self.Crystal:
            script += '''
color forest, Crystal
show car, Crystal'''
        script += '''
color gray, Design
#cmd.color("'+color_H+'", selector.process("Design and chain '+heavy_chain.id+'"))
#cmd.color("'+color_L+'", selector.process("Design and chain '+light_chain.id+'"))

#superpose template and design based on the ligand
select design_ligand, Design and resn LG1
show sticks, design_ligand'''
        if self.Crystal:
            script += '''
select template_ligand, Crystal and resn LG1
color gray, template_ligand
show sticks, template_ligand
pair_fit template_ligand, design_ligand'''
        if self.Crystal:
            script += '''
disable Crystal'''

        script += '''

# orient view
set_view (0.750491261,   -0.332692802,   -0.570965469,  -0.572279274,    0.104703479,   -0.813287377,   0.330366731,    0.937145591,   -0.111799516,    0.000000000,    0.000000000, -129.595489502,    36.783428192,   36.119152069,   77.293815613,   112.102447510,  147.088562012,  -20.000000000 )

# superimpose original scaffold onto the design
super Scaffold, Design

# preset.ligands(selection="Scaffold")
hide lines, Scaffold
hide ribbon, Scaffold
show car, Scaffold
util.cbc Scaffold
disable Scaffold

# highlight motif residues'''

#        if self.Crystal:
#            script += '''
#create template_motif_residues, Crystal and not resn LG1 and resi ''' + self.Crystal.residues_of_interest
        if self.Scaffold.residues_of_interest and self.Design.residues_of_interest:
            script += '''
create template_motif_residues, Scaffold and not resn LG1 and resi ''' + "+".join(self.Scaffold.residues_of_interest) + '''
select design_motif_residues, Design and not resn LG1 and resi ''' + "+".join(self.Design.residues_of_interest) + '''
set stick_radius, 0.1, template_motif_residues
show sticks, template_motif_residues and not symbol h and not name C+N+O
show sticks, design_motif_residues and not symbol h
color brightorange, template_motif_residues
color tv_yellow, design_motif_residues'''

# create ligand environment
        if self.Crystal:
            script += '''
create template_env, Crystal and byres template_ligand around %(visualization_shell)s''' % self.__dict__

        script += '''
create design_env, Design and byres design_ligand around %(visualization_shell)s
create scaffold_env, Scaffold and byres design_ligand around %(visualization_shell)s''' % self.__dict__
        if self.Crystal:
            script += '''
set stick_radius, 0.1, template_env
show sticks, template_env and not symbol h and not name C+N+O'''
        script += '''
show sticks, design_env and not symbol h
show sticks, scaffold_env and not symbol h'''
        if self.Crystal:
            script += '''
set cartoon_transparency, 1, template_env'''
        script += '''
set cartoon_transparency, 1, design_env
set cartoon_transparency, 1, scaffold_env

# hide ligand environment'''

        if self.Crystal:
            script += '''
disable template_env'''
        script += '''
disable design_env
disable scaffold_env

# create binding pocket'''

        if self.Crystal:
            script += '''
create template_env_surface, template_env
hide sticks, template_env_surface
show surface, template_env_surface
#color gray70, template_env_surface
set cartoon_transparency, 1, template_env_surface'''

        script += '''
create design_env_surface, design_env
hide sticks, design_env_surface
show surface, design_env_surface
set transparency, 0.25
#color gray70, design_env_surface
set cartoon_transparency, 1, design_env_surface

# hide binding pocket'''

        if self.Crystal:
            script += '''
disable template_env_surface'''
        script += '''
disable design_env_surface

# ray tracing and output
select none
select env, design_ligand around 6
set transparency, 0.5
util.cnc
show surface, Design and env
set two_sided_lighting, on
zoom design_ligand, 10
heavy_chain_residues=[]
light_chain_residues=[]
one_letter ={"VAL":"V", "ILE":"I", "LEU":"L", "GLU":"E", "GLN":"Q", "ASP":"D", "ASN":"N", "HIS":"H", "TRP":"W", "PHE":"F", "TYR":"Y", "ARG":"R", "LYS":"K", "SER":"S", "THR":"T", "MET":"M", "ALA":"A", "GLY":"G", "PRO":"P", "CYS":"C"}
#cmd.iterate(selector.process("Design and chain '+heavy_chain.id+' and name ca"),"heavy_chain_residues.append(resn)")
#cmd.iterate(selector.process("Design and chain '+light_chain.id+' and name ca"),"light_chain_residues.append(resn)")
#heavy_chain_seq=""
#light_chain_seq=""
#for residue in heavy_chain_residues: heavy_chain_seq+=one_letter[residue]
#for residue in light_chain_residues: light_chain_seq+=one_letter[residue]
#print
#print "Heavy chain ('+heavy_chain.id+','+color_H+')",heavy_chain_seq
#print
#print "Light chain ('+light_chain.id+','+color_L+')",light_chain_seq

print
save session.pse
quit
'''  % self.__dict__

        self.script = script

