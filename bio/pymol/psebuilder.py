#!/usr/bin/python
# encoding: utf-8
"""
psebuilder.py
Functions used to create PyMOL sessions (PSE files).

Adapted from scripts developed and written by Roland A. Pache, Ph.D., Copyright (C) 2012, 2013.
Created by Shane O'Connor 2014.
"""

import os
import time
import sys
sys.dont_write_bytecode = True
import re

from tools.unmerged.rpache import functions_lib
from tools.unmerged.rpache import PDB_files
from tools.fs.io import read_file

###############################################
## Visualization parameters
###############################################

class PDBContainer(object):

    def __init__(self, pymol_name, pdb_contents):
        self.pymol_name = pymol_name
        self.pdb_contents = pdb_contents

    @staticmethod
    def from_file(pymol_name, pdb_filename):
        return PDBContainer(pymol_name, read_file(pdb_filename))

    @staticmethod
    def from_tuples(tpls):
        pdb_containers = []
        for t in tpls:
            pdb_containers.append(PDBContainer(t[0], t[1]))
        return pdb_containers

    @staticmethod
    def from_filename_tuples(tpls):
        pdb_containers = []
        for t in tpls:
            pdb_containers.append(PDBContainer.from_file(t[0], t[1]))
        return pdb_containers

class BatchBuilder(object):

    def __init__(self):
        self.visualization_shell = 6
        self.visualization_pymol = 'pymol' # the command used to run pymol - change as necessary for Mac OS X

    def run(self, builder_class, list_of_pdb_containers):
        for pdb_containers in list_of_pdb_containers:
            b = builder_class(pdb_containers)
            b.visualization_shell = self.visualization_shell
            b.visualization_pymol = self.visualization_pymol
            b.run()


class GenericBuilder(object):

    def __init__(self, pdb_containers):
        self.visualization_shell = 6
        self.visualization_pymol = 'pymol'
        self.pdb_containers = pdb_containers

    def run(self):
        pass



#constants
pymol_scriptname='visualize_antibody_design.pml'
color_H='marine'
color_L='purple'


start_time=time.time()

#parse input parameters
if len(sys.argv)<3 or len(sys.argv)>4:
    print
    print 'Usage: ./visualize_antibody_design.py PDB PARAMETER_FILE outfile_name(optional)'
    print
    sys.exit()
#-
parameter_file=sys.argv[2]
parameters=functions_lib.parseParameterFile(parameter_file)
main_dir=parameters['global_main_dir']
interface_cutoff=float(parameters['match_posfiles_interface_distance'])
scaffolds_dir=main_dir+parameters['match_scaffolds_indir']
match_template_indir=main_dir+parameters['match_template_indir']
template=match_template_indir+parameters['match_template_pdb_file']
match_constraints_file=match_template_indir+parameters['match_constraints_file']
design_shell=parameters['visualization_shell']
pymol=parameters['visualization_pymol']


#check outfile name
outfile_name=None
if len(sys.argv)==4:
    outfile_name=sys.argv[3]
#-


#load input structure
pdb_filename=sys.argv[1]
if not os.path.isfile(pdb_filename):
    print
    print 'ERROR: PDB does not exist'
    print
    sys.exit()
#-
data=pdb_filename.split('/')
is_relaxed_design=False
is_match=False
scaffold_id=data[-4]
if data[-2].startswith('DE_'):
    is_relaxed_design=True
    scaffold_id=data[-5]
#-
if data[-3].startswith('motif'):
    is_match=True
    scaffold_id=data[-2]
#-
#scaffold_id='3FAP.pdb1'#TODO:remove
print
print 'Scaffold ID:',scaffold_id


#determine matching scaffold
scaffolds_dir_contents=os.listdir(scaffolds_dir)
for item in scaffolds_dir_contents:
    if item.endswith('.gz') and scaffold_id in item:
        scaffold=scaffolds_dir+item
        break
#--
print 'Scaffold:',scaffold


#extract template motif residues from .cst file
print
print 'Template:',template
template_motif_residues=''
infile=open(match_constraints_file)
for line in infile:
    line=line.strip('\n')
    if line.startswith('#') and 'descriptor' not in line:
        print line
        template_motif_residues+=line.split()[-1]+'+'
#--
infile.close()
template_motif_residues=template_motif_residues.rstrip('+')
print 'Template motif residues:',template_motif_residues


#extract design motif residues from filename
design_motif_residues=template_motif_residues
if '_' in pdb_filename.split('/')[-1]:
    design_motif_residues_list=re.findall('\d+',pdb_filename.split('/')[-1].replace('UM_','').split('_')[1].split('.')[0])
    design_motif_residues=str(design_motif_residues_list).replace("'",'').replace(', ','+').strip('[]')
#-
print
print 'Design motif residues:', design_motif_residues


#determine antibody heavy and light chains
print
print 'detecting antibody light and heavy chains...'
pdb=PDB_files.parsePDB(pdb_filename)
model=pdb.models[0]
chains=model.chains
max_num_contacts=0
antibody_chains=(None,None)
#process chains
for i in range(len(chains)):
    chain1=chains[i]
    for j in range(i+1,len(chains)):
        chain2=chains[j]
        num_contacts=0
        for residue1 in chain1.residues:
            for residue2 in chain2.residues:
                distance=PDB_files.cAlphaResidueDistance(residue1,residue2)
                if distance<interface_cutoff:
                    num_contacts+=1
        #---
        if num_contacts>max_num_contacts:
            max_num_contacts=num_contacts
            antibody_chains=(chain1,chain2)
#---
heavy_chain=antibody_chains[0]
light_chain=antibody_chains[1]
if len(light_chain.residues)>len(heavy_chain.residues):
    heavy_chain=antibody_chains[1]
    light_chain=antibody_chains[0]
#-
print 'heavy chain:',heavy_chain.id
print 'light chain:',light_chain.id


#write pymol script
pymol_commands='\
\n#load structures\
\ncd '+os.getcwd()+'\
\nload '+template+', Template\
\nload '+pdb_filename+', Design\
\nload '+scaffold+', Scaffold\
\n\
\n#set general view options\
\nviewport 1200,800\
\nhide eve\
\n#set seq_view\
\nbg_color white\
\n#set cartoon_fancy_helices\
\nset cartoon_side_chain_helper\
\nset cartoon_rect_length, 0.9\
\nset cartoon_oval_length, 0.9\
\nset stick_radius, 0.2\
\n#set cartoon_flat_sheets, off\
\nshow car, Design\
\ncolor forest, Template\
\nshow car, Template\
\ncolor gray, Design\
\ncmd.color("'+color_H+'", selector.process("Design and chain '+heavy_chain.id+'"))\
\ncmd.color("'+color_L+'", selector.process("Design and chain '+light_chain.id+'"))\
\n\
\n#superpose template and design based on the ligand\
\nselect design_ligand, Design and resn LG1\
\nshow sticks, design_ligand\
\nselect template_ligand, Template and resn LG1\
\ncolor gray, template_ligand\
\nshow sticks, template_ligand\
\npair_fit template_ligand, design_ligand\
\ndisable Template\
\n\
\n#orient view\
\nset_view (\
     0.750491261,   -0.332692802,   -0.570965469,\
    -0.572279274,    0.104703479,   -0.813287377,\
     0.330366731,    0.937145591,   -0.111799516,\
     0.000000000,    0.000000000, -129.595489502,\
    36.783428192,   36.119152069,   77.293815613,\
   112.102447510,  147.088562012,  -20.000000000 )\
\n\
\n#superimpose original scaffold onto the design\
\nsuper Scaffold, Design\
\n#preset.ligands(selection="Scaffold")\
\nhide lines, Scaffold\
\nhide ribbon, Scaffold\
\nshow car, Scaffold\
\nutil.cbc Scaffold\
\ndisable Scaffold\
\n\
\n#highlight motif residues\
\ncreate template_motif_residues, Template and not resn LG1 and resi '+template_motif_residues+'\
\nselect design_motif_residues, Design and not resn LG1 and resi '+design_motif_residues+'\
\nset stick_radius, 0.1, template_motif_residues\
\nshow sticks, template_motif_residues and not symbol h and not name C+N+O\
\nshow sticks, design_motif_residues and not symbol h\
\ncolor brightorange, template_motif_residues\
\ncolor tv_yellow, design_motif_residues\
\n\
\n#create ligand environment\
\ncreate template_env, Template and byres template_ligand around '+str(design_shell)+'\
\ncreate design_env, Design and byres design_ligand around '+str(design_shell)+'\
\ncreate scaffold_env, Scaffold and byres design_ligand around '+str(design_shell)+'\
\nset stick_radius, 0.1, template_env\
\nshow sticks, template_env and not symbol h and not name C+N+O\
\nshow sticks, design_env and not symbol h\
\nshow sticks, scaffold_env and not symbol h\
\nset cartoon_transparency, 1, template_env\
\nset cartoon_transparency, 1, design_env\
\nset cartoon_transparency, 1, scaffold_env\
\n\
\n#hide ligand environment\
\ndisable template_env\
\ndisable design_env\
\ndisable scaffold_env\
\n\
\n#create binding pocket\
\ncreate template_env_surface, template_env\
\ncreate design_env_surface, design_env\
\nhide sticks, template_env_surface\
\nhide sticks, design_env_surface\
\nshow surface, template_env_surface\
\nshow surface, design_env_surface\
\nset transparency, 0.25\
\n#color gray70, template_env_surface\
\n#color gray70, design_env_surface\
\nset cartoon_transparency, 1, template_env_surface\
\nset cartoon_transparency, 1, design_env_surface\
\n\
\n#hide binding pocket\
\ndisable template_env_surface\
\ndisable design_env_surface\
\n\
\n#ray tracing and output\
\nselect none\
\nselect env, design_ligand around 6\
\nset transparency, 0.5\
\nutil.cnc\
\nshow surface, Design and env\
\nset two_sided_lighting, on\
\nzoom design_ligand, 10\
\nheavy_chain_residues=[]\
\nlight_chain_residues=[]\
\none_letter ={"VAL":"V", "ILE":"I", "LEU":"L", "GLU":"E", "GLN":"Q", \
"ASP":"D", "ASN":"N", "HIS":"H", "TRP":"W", "PHE":"F", "TYR":"Y",    \
"ARG":"R", "LYS":"K", "SER":"S", "THR":"T", "MET":"M", "ALA":"A",    \
"GLY":"G", "PRO":"P", "CYS":"C"}\
\ncmd.iterate(selector.process("Design and chain '+heavy_chain.id+' and name ca"),"heavy_chain_residues.append(resn)")\
\ncmd.iterate(selector.process("Design and chain '+light_chain.id+' and name ca"),"light_chain_residues.append(resn)")\
\nheavy_chain_seq=""\
\nlight_chain_seq=""\
\nfor residue in heavy_chain_residues: heavy_chain_seq+=one_letter[residue]\
\nfor residue in light_chain_residues: light_chain_seq+=one_letter[residue]\
\nprint\
\nprint "Heavy chain ('+heavy_chain.id+','+color_H+')",heavy_chain_seq\
\nprint\
\nprint "Light chain ('+light_chain.id+','+color_L+')",light_chain_seq\
\n\
\nprint\
\nprint "'+pdb_filename+'"'
if outfile_name!=None:
    pymol_commands+='\
    \nsave '+outfile_name+'\
    \nquit'
#-
pymol_script=open(pymol_scriptname,'w')
pymol_script.write(pymol_commands)
pymol_script.close()
print
print 'wrote',pymol_scriptname


#run pymol
print
print 'running',pymol_scriptname
if outfile_name!=None:
    functions_lib.run(pymol+' -c '+pymol_scriptname)
    print 'writing session file...'
else:
    functions_lib.run(pymol+' '+pymol_scriptname)
#-

end_time=time.time()
print
print "\ntime consumed: "+str(end_time-start_time)
