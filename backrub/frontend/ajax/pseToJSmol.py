#!/usr/bin/python
#This file was initially developed and written by Roland A. Pache, Ph.D., Copyright (C) 2012. for creating PyMOL session files.
#Shane O'Connor, Copyright (C) 2012. then modified and adapted the file to create comparable JSmol scripts.

import os
import sys
import PDB_files
from subprocess import Popen, PIPE

sys.path.insert(0, '../../common')
from rosettahelper import readFile

def getPDBGZContents(fname):
	f = Popen(['gunzip', '-c', fname], stdout=PIPE)
	return "".join([line for line in f.stdout])

class JSmolScriptGenerationException(Exception): pass

class JSmolScriptGenerator(object):
	
	# constants
	color_A = 'x0080FF' # marine
	color_B = 'xC000C0' # purple

	def __init__(self, design_record, design_small_molecule, design_small_molecule_motif_residues, design_motif_residues, printout = False):
		'''design_record should be the contents of the corresponding Design record in the database.
		   design_small_molecule_motif_residues should be the contents of the SmallMoleculeMotifResidue records in the database corresponding with the TargetSmallMoleculeMotifID field of the design.
		''' 

		design_shell = 8
		
		# Read in the small molecule template
		template_filename = '/kortemmelab/shared/projects/Gen9/biosensor_design/data/%(SmallMoleculeID)s/%(PDBFileID)s/%(PDBFileID)s_liganded_renumbered.pdb' % design_small_molecule
		template_filename = template_filename.replace("kb_ART", "ART") 
		template_pdbdata = readFile(template_filename)
		
		# Read in the matching scaffold PDB
		scaffolds_dir = '/kortemmelab/shared/projects/Gen9/biosensor_design/data/heterodimers_all_biological_units'
		scaffold_id = '%(WildtypeScaffoldPDBFileID)s.%(WildtypeScaffoldBiologicalUnit)s' % design_record
		scaffold_filename = os.path.join(scaffolds_dir, scaffold_id)
		if not(os.path.exists(scaffold_filename)):
			scaffold_filename = os.path.join(scaffolds_dir, '%s.gz' % scaffold_id)
			if not(os.path.exists(scaffold_filename)):
				raise JSmolScriptGenerationException("Could not find scaffold '%s' in directory '%s'." % (scaffold_id, scaffolds_dir))
		scaffold_pdbdata =getPDBGZContents(scaffold_filename)
			
		# Read in the design PDB
		pdb_filepath = design_record['FilePath']
		if not os.path.exists(pdb_filepath):
			raise JSmolScriptGenerationException("File '%s' does not exist." % pdb_filepath)
		design_pdbdata = getPDBGZContents(pdb_filepath)
		
		# Create the list of template motif residues
		template_motif_residues = '+'.join(map(str, [r['ResidueID'] for r in design_small_molecule_motif_residues]))

		# Create the list of template motif residues
		#design_motif_residues = '+'.join(map(str, [r['ResidueID'] for r in design_motif_residues]))

		# Calculate C-alpha distances between chain termini (for attaching the split-reporter system)
		pdb_object=PDB_files.parsePDB(pdb_filepath)
		protein_chains = []
		model = pdb_object.models[0]
		for chain in model.chains:
			if len(chain.canonical_residues)>1: 
				protein_chains.append(chain)
		chain1 = protein_chains[0]
		chain2 = protein_chains[1]
		#print chain1.id
		#print chain2.id
		N_terminal_res_chain1=chain1.residues[0]
		C_terminal_res_chain1=chain1.residues[-1] 
		N_terminal_res_chain2=chain2.residues[0]
		C_terminal_res_chain2=chain2.residues[-1]
		C1C2='n/a'
		C1N2='n/a'
		N1N2='n/a'
		N1C2='n/a'
		try:
			C1C2 = round(PDB_files.cAlphaResidueDistance(C_terminal_res_chain1,C_terminal_res_chain2))
			C1N2 = round(PDB_files.cAlphaResidueDistance(C_terminal_res_chain1,N_terminal_res_chain2))
			N1N2 = round(PDB_files.cAlphaResidueDistance(N_terminal_res_chain1,N_terminal_res_chain2))
			N1C2 = round(PDB_files.cAlphaResidueDistance(N_terminal_res_chain1,C_terminal_res_chain2))
		except:
			raise JSmolScriptGenerationException("Issue encountered while trying to compute C-alpha residue distances")
		
		JSmol = []
		JSmol.append('load data "mydata"\n' + template_pdbdata + '\nend "mydata";'); # Template 1.1
		JSmol.append('load data "append mydata"\n' + design_pdbdata + '\nend "append mydata";'); # Design 2.1
		JSmol.append('load data "append mydata"\n' + scaffold_pdbdata + '\nend "append mydata";'); # Scaffold 3.1
		
		JSmol.append('frame all; display 2.1;')
		
		#JSmol.append('hide all')
		
		#JSmol.append("frame all; display 2.1; hide 1.1; hide 3.1;")
		
		#JSmol.append('hide all') # hide eve
		#JSmol.append('color background [xFFFFFF]')
		
		JSmol.append('set bondMode or; select sidechain; wireframe 0.3; select all; trace on;') # set cartoon_side_chain_helper
		
		JSmol.append('select sheet; cartoon 0.75;') # set cartoon_rect_length, 0.75
		JSmol.append('select helix; cartoon 0.75;') # set cartoon_oval_length, 0.75
		JSmol.append('select 2.1; cartoon only;') # show car, Design
		JSmol.append('select 1.1; color [x339933];') # color forest, Template
		JSmol.append('select 2.1; color [x808080];') # color gray, Design
		#JSmol.append('show all') # hide eve
		
		#skipping 'viewport 1200,800'
		
		# Set general view options - Check with Roland here
		JSmol.append("select :A/2; color [%s];" % JSmolScriptGenerator.color_A)
		JSmol.append("select :B/2; color [%s];" % JSmolScriptGenerator.color_B)
		
		# Select design_ligand, Design and resn LG1
		JSmol.append("select LG1:X/2; wireframe only; wireframe reset; spacefill reset;") # color [xff0000]") # select design_ligand, Design and resn LG1; show sticks, design_ligand
		#skip JSmol.append("select LG1:X/2; wireframe only; wireframe reset; spacefill reset;") # color [xffff00]") # select design_ligand, Design and resn LG1; show sticks, design_ligand
		
		#JSmol.append('console')
		#jsmol-13.1.14b.zip
		JSmol.append('print("C-alpha distances of terminal residues:");')
		JSmol.append('print("C-terminal of Chain 1 & C-terminal of Chain 2, %s");' % str(C1C2)) 
		JSmol.append('print("C-terminal of Chain 1 & N-terminal of Chain 2, %s");' % str(C1N2))
		JSmol.append('print("N-terminal of Chain 1 & N-terminal of Chain 2, %s");' % str(N1N2))
		JSmol.append('print("N-terminal of Chain 1 & C-terminal of Chain 2, %s");' % str(N1C2))
						
		# select template_ligand, Template and resn LG1; pair_fit template_ligand, design_ligand
		JSmol.append("compare {1.1} {2.1} SUBSET LG1 ROTATE TRANSLATE 0;")
		
		#todo here display 2.1 And LG1, 1.1 And LG1; compare {1.1} {2.1} SUBSET LG1 ROTATE TRANSLATE 0;
		
		# superimpose original scaffold onto the design
		JSmol.append("compare {3.1} {2.1} ROTATE TRANSLATE 0;") # super Scaffold, Design

		# hide ribbon, Scaffold; show car, Scaffold; util.cbc Scaffold; disable Scaffold;
		JSmol.append("select 3.1; cartoon only; color chain;")# hide 3.1;")
		
		self.script = JSmol
		#return
		bright_orange = 'xFFB333'
		hide_list = []
		hide_list.append('3.1')
		#hide_list.append('')#1.1 and not backbone')
		select_list = []
		display_list = ['2.1 and backbone']#'2.1']
		display_list.append('*X:2')#'2.1']
		template_motif_residues = [r['ResidueID'] for r in design_small_molecule_motif_residues]
		for r in template_motif_residues:
			select_list.append('%s:A/1' % r)
			hide_list.append('%s:A.C/1' % r)
			hide_list.append('%s:A.N/1' % r)
			hide_list.append('%s:A.O/1' % r)
			hide_list.append('%s:A.H/1' % r)
			display_list.append('%s:A/1' % r)
		JSmol.append("select %s; wireframe only; wireframe .1; color [%s];" % (', '.join(select_list), bright_orange)) #  spacefill 0.4;
		#hide_list.append('1.1')
		
		select_list = []
		tv_yellow = 'xFFFF33'
		design_motif_residues = [(r['Chain'], r['ResidueID']) for r in design_motif_residues]
		for r in design_motif_residues:
			select_list.append('%s:%s.C/2' % (r[1], r[0]))
			select_list.append('%s:%s.C?/2' % (r[1], r[0]))
			select_list.append('%s:%s.C??/2' % (r[1], r[0]))
			#hide_list.append('%s:A.C/2' % r)
			#hide_list.append('%s:A.N/2' % r)
			#hide_list.append('%s:A.O/2' % r)
			hide_list.append('%s:%s.H/2' % (r[1], r[0]))
			hide_list.append('%s:%s.H?/2' % (r[1], r[0]))
			hide_list.append('%s:%s.H??/2' % (r[1], r[0]))
			display_list.append('%s:%s.C/2' % (r[1], r[0]))
			display_list.append('%s:%s.C?/2' % (r[1], r[0]))
			display_list.append('%s:%s.C??/2' % (r[1], r[0]))
		JSmol.append("select %s; wireframe only; wireframe .1; color atoms cpk;" % (', '.join(select_list))) #  spacefill 0.4;
		
		for r in design_motif_residues:
			JSmol.append("color {%s:%s.C??} [%s];" % (r[1], r[0], tv_yellow)) 
		
		JSmol.append("hide %s;" % (', '.join(hide_list)))
		JSmol.append("display %s;" % (', '.join(display_list)))
		
		JSmol.append("center 2.1;")
		JSmol.append("zoom 100;")
		#JSmol.append('console;')
		JSmol.append('print("%s");' % template_filename)
		JSmol.append('print("%s");' % scaffold_filename)
		JSmol.append('print("%s");' % pdb_filepath)
		
		for jscmd in JSmol:
			if not jscmd.endswith(";") and printout:
				print('error', jscmd)
				sys.exit(1)
			elif printout:
				print(jscmd)
			assert(jscmd.endswith(";"))
			
		
		self.script = JSmol
		return
	
		JSmol.append('display 2.1; ')
		self.script = JSmol
		return
		
		if printout:
			print()
		
		#JSmol.append('display 1.1, 2.1')
		self.script = JSmol
		return
		
		

		self.script = JSmol
		
		if printout:
			print(template_motif_residues)
			print('load '+template_filename+', Template')
			print('load '+pdb_filepath+', Design')
			print('load '+scaffold_filename+', Scaffold')
			print('''
''')



'''
#create ligand environment
create template_env, Template and byres template_ligand around '+str(design_shell)+'
create design_env, Design and byres design_ligand around '+str(design_shell)+'
create scaffold_env, Scaffold and byres design_ligand around '+str(design_shell)+'
set stick_radius, 0.1, template_env
show sticks, template_env and not symbol h and not name C+N+O
show sticks, design_env and not symbol h
show sticks, scaffold_env and not symbol h
set cartoon_transparency, 1, template_env
set cartoon_transparency, 1, design_env
set cartoon_transparency, 1, scaffold_env


#hide ligand environment
disable template_env
disable design_env
disable scaffold_env


\n#create binding pocket
\ncreate template_env_surface, template_env
\ncreate design_env_surface, design_env
\nhide sticks, template_env_surface
\nhide sticks, design_env_surface
\nshow surface, template_env_surface
\nshow surface, design_env_surface
\nset transparency, 0.25
\n#color gray70, template_env_surface
\n#color gray70, design_env_surface
\nset cartoon_transparency, 1, template_env_surface
\nset cartoon_transparency, 1, design_env_surface
\n
\n#hide binding pocket
\ndisable template_env_surface
\ndisable design_env_surface
\n

ray tracing and output
select none
select env, design_ligand around 6
set transparency, 0.5
util.cnc
show surface, Design and env
set two_sided_lighting, on
zoom design_ligand, 10
'''


'''
> On Monday 27 September 2004 16:26, Miguel wrote:
> > > is there an easy way to turn on the ball and stick 
> representation in the
> > > applet via a script?
> > > like "ballstick on" ???
> >
> > You need to explicitly set the 'ball radius' and the 'stick radius'
> >
> > The following will set the ball radius
> >
> > spacefill .5 # .5 angstrom radius
> > spacefill 20% # 20% of vdw radius
> >
> > The following will set the stick radius:
> >
> > wireframe .1 # .1 angstrom radius for the bond cylinders
'''

if __name__ == "__main__":
	import cgi
	import cgitb
	import traceback
	import sys
	import os
	import base64
	form = cgi.FieldStorage()

	import rosettadb
	from rosettahelper import WebsiteSettings
	settings = WebsiteSettings(sys.argv, '/backrub/frontend/ajax/pseToJSmol.py')
	gen9db = rosettadb.ReusableDatabaseInterface(settings, host = "kortemmelab.ucsf.edu", db = "Gen9Design")
	
	design_record = gen9db.execute("SELECT * FROM Design WHERE ID = 55")[0]
	small_molecule = gen9db.execute("SELECT SmallMoleculeID, PDBFileID FROM SmallMoleculeMotif WHERE ID=%s", parameters=(design_record['TargetSmallMoleculeMotifID'],))[0]
	small_molecule_motif_residues = gen9db.execute("SELECT * FROM SmallMoleculeMotifResidue WHERE SmallMoleculeMotifID = %s", parameters=(design_record['TargetSmallMoleculeMotifID'],))
	motif_residues = gen9db.execute("SELECT Chain, OriginalAA, ResidueID, VariantAA, IsMutation FROM DesignResidue WHERE DesignID=%s AND IsMotifResidue=1", parameters=(design_record['ID'],))
	jmol = JSmolScriptGenerator(design_record, small_molecule, small_molecule_motif_residues, motif_residues, printout=True)
	