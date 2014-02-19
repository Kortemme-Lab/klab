#Module for handling PDB files

import sys
import os
import signal
import math
from subprocess import Popen, PIPE

#CONSTANTS
one_letter_codes={}
one_letter_codes['ALA']='A'
one_letter_codes['CYS']='C'
one_letter_codes['ASP']='D'
one_letter_codes['GLU']='E'
one_letter_codes['PHE']='F'
one_letter_codes['GLY']='G'
one_letter_codes['HIS']='H'
one_letter_codes['ILE']='I'
one_letter_codes['LYS']='K'
one_letter_codes['LEU']='L'
one_letter_codes['MET']='M'
one_letter_codes['ASN']='N'
one_letter_codes['PRO']='P'
one_letter_codes['GLN']='Q'
one_letter_codes['ARG']='R'
one_letter_codes['SER']='S'
one_letter_codes['THR']='T'
one_letter_codes['VAL']='V'
one_letter_codes['TRP']='W'
one_letter_codes['TYR']='Y'


#CLASSES
class PDB:
    def __init__(self,id='',filename='',title='',resolution=None,models=[]):
        self.id=id
        self.filename=filename
        self.title=title
        self.resolution=resolution
        self.models=models

    def out(self):
        print self.id
        for model in self.models:
            model.out()

    def write(self):
        outstring=''
        if len(self.models)>1:
            for model in self.models:
                outstring+=model.write()
        else:
            outstring+=self.models[0].write_plain()
        #-
        outstring+='END\n'
        return outstring


class Model:
    def __init__(self,serial='',chains=[]):
        self.serial=serial
        self.chains=chains

    def out(self):
        print self.serial
        for chain in self.chains:
            chain.out()

    def write(self):
        outstring='MODEL '+'    '+self.serial+'\n'
        for chain in self.chains:
            outstring+=chain.write()
        #-
        outstring+='ENDMDL\n'
        return outstring

    def write_plain(self):
        outstring=''
        for chain in self.chains:
            outstring+=chain.write()
        #-
        return outstring


class Chain:
    def __init__(self,id='',residues=[],protein_id='',expression_system='',molecule=''):
        self.id=id
        self.residues=residues
        self.canonical_residues=[]
        for residue in residues:
            if residue.is_canonical:
                self.canonical_residues.append(residue)
        #--
        self.protein_id=protein_id
        self.expression_system=expression_system
        self.molecule=molecule

    def out(self):
        print self.id
        for residue in self.residues:
            residue.out()

    def write(self):
        outstring=''
        for residue in self.residues:
            outstring+=residue.write()
        #-
        outstring+='TER\n'
        return outstring
    

class Residue:
    def __init__(self,res_seq='',res_name='',is_canonical=True,atoms=[]):
        self.res_seq=res_seq
        self.res_name=res_name
        self.is_canonical=is_canonical
        self.atoms=atoms

    def out(self):
        print self.res_seq,self.res_name
        for atom in self.atoms:
            atom.out()

    def write(self):
        outstring=''
        for atom in self.atoms:
            outstring+=atom.write()
        #-
        return outstring


class Atom:
    def __init__(self,type='ATOM  ',serial='',name='',alt_loc='',res_name='',chain_id='',res_seq='',x='',y='',z='',occupancy='',temp_factor='',spacer='',element='',charge=''):
        self.type=type
        self.serial=serial
        self.name=name
        self.alt_loc=alt_loc
        self.res_name=res_name
        self.chain_id=chain_id
        self.res_seq=res_seq
        self.x=x
        self.y=y
        self.z=z
        self.occupancy=occupancy
        self.temp_factor=temp_factor
        self.spacer=spacer
        self.element=element
        self.charge=charge

    def out(self):
        print self.type,self.serial,self.name,self.alt_loc,self.res_name,self.chain_id,self.res_seq,self.x,self.y,self.z,self.occupancy,self.temp_factor,self.element,self.charge

    def write(self):
        return self.type+self.serial+' '+self.name+self.alt_loc+self.res_name+' '+self.chain_id+self.res_seq+'   '+self.x+self.y+self.z+self.occupancy+self.temp_factor+self.spacer+self.element+self.charge+'\n'


class Gunziplines:
    def __init__(self,fname):
        self.f = Popen(['gunzip', '-c', fname], stdout=PIPE)
    def readlines(self):
        for line in self.f.stdout:
            yield line
    def killGunzip(self):
        if self.f.poll() == None:
            os.kill(self.f.pid,signal.SIGHUP)


#FUNCTIONS
def parsePDB(pdb_file_name):
    #unzip if zipped
    zipped=False
    if pdb_file_name.endswith('.gz'):
        zipped=True
        infile=Gunziplines(pdb_file_name)
    else:
        infile=open(pdb_file_name)
    #-
    line_count=0
    residue_map={}
    residue_list=[]
    model_serial=0
    protein_id_map={}
    mol_id_to_chain_ids_map={}
    mol_id_to_molecule_map={}
    expression_system_map={}
    molecule_map={}
    mol_id=''
    chain_id=''
    title=''
    resolution=None
    #parse atoms and expression system data
    for line in infile.readlines():
        line=line.strip('; \n')
        line_count+=1
        type=line[0:6]
        if type.strip()=='TITLE':
            title+=line[6:].strip('\n ')
        elif type=='REMARK' and line[9]=='2' and line[11:21]=='RESOLUTION':
            resolution=line[23:30]
        elif type=='COMPND':
            if 'MOL_ID:' in line:
                mol_id=line.split()[-1].strip(';')
            elif 'CHAIN:' in line:
                chain_ids=line.split('CHAIN:')[1].replace(' ','').split(',')
                mol_id_to_chain_ids_map[mol_id]=chain_ids
            elif 'MOLECULE:' in line:
                molecule=line.split('MOLECULE:')[1].upper()
                mol_id_to_molecule_map[mol_id]=molecule
        #--
        elif type=='SOURCE':
            if 'MOL_ID:' in line:
                mol_id=line.split()[-1].strip(';')
                if mol_id in mol_id_to_chain_ids_map and mol_id in mol_id_to_molecule_map:
                    chain_ids=mol_id_to_chain_ids_map[mol_id]
                    molecule=mol_id_to_molecule_map[mol_id]
                    for chain_id in chain_ids:
                        molecule_map[chain_id]=molecule
            #---
            elif 'EXPRESSION_SYSTEM:' in line:
                expression_system=line.split('EXPRESSION_SYSTEM:')[-1].upper()
                if mol_id in mol_id_to_chain_ids_map:
                    chain_ids=mol_id_to_chain_ids_map[mol_id]
                    for chain_id in chain_ids:
                        expression_system_map[chain_id]=expression_system
                        
        #----
        elif type.strip()=='ATOM' or type=='HETATM':
            if len(line)<78:
                print 'ERROR in line:',line_count
                print line
                print
                sys.exit()
            #-
            #create new atom
            serial=line[6:11]
            name=line[12:16]
            alt_loc=line[16]
            res_name=line[17:20]
            chain_id=line[21]
            res_seq=line[22:27]#this includes the insertion code
            x=line[30:38]
            y=line[38:46]
            z=line[46:54]
            occupancy=line[54:60]
            temp_factor=line[60:66]
            spacer=line[66:76]
            element=line[76:78]
            charge=line[78:80]
            atom=Atom(type,serial,name,alt_loc,res_name,chain_id,res_seq,x,y,z,occupancy,temp_factor,spacer,element,charge)
            key=(model_serial,(chain_id,res_seq))
            if key not in residue_map:
                residue_map[key]=[]
                residue_list.append(key)
            #-
            residue_map[key].append(atom)
        elif type.strip()=='MODEL':
            model_serial=line[10:14]
        elif type.strip()=='DBREF':
            chain_id=line[12]
            db_id=line[26:32]
            protein_id=line[33:41]
            protein_id_map[chain_id]=protein_id
    #--
    if zipped: 
        infile.killGunzip()
    else:
        infile.close()
    #-
    #create residues
    chain_map={}
    chain_list=[]
    atoms=[]
    for item in residue_list:
        (model_serial,(chain_id,res_seq))=item
        atoms=residue_map[item]
        is_canonical=True
        if atoms[0].type=='HETATM':
            is_canonical=False
        #-
        res_name=atoms[0].res_name
        residue=Residue(res_seq,res_name,is_canonical,atoms)
        key=(model_serial,chain_id)
        if key not in chain_map:
            chain_map[key]=[]
            chain_list.append(key)
        #-
        chain_map[key].append(residue)
    #-
    #create chains
    model_map={}
    model_list=[]
    for item in chain_list:
        (model_serial,chain_id)=item
        residues=chain_map[item]
        protein_id=''
        if chain_id in protein_id_map:
            protein_id=protein_id_map[chain_id]
        #-
        expression_system=''
        if chain_id in expression_system_map:
            expression_system=expression_system_map[chain_id]
        #-
        molecule=''
        if chain_id in molecule_map:
            molecule=molecule_map[chain_id]
        #-
        chain=Chain(chain_id,residues,protein_id,expression_system,molecule)
        if model_serial not in model_map:
            model_map[model_serial]=[]
            model_list.append(model_serial)
        #-
        model_map[model_serial].append(chain)
    #-
    #create models
    models=[]
    for model_serial in model_list:
        chains=model_map[model_serial]
        model=Model(model_serial,chains)
        models.append(model)
    #-
    #create final PDB object
    pdb_id=pdb_file_name.split('/')[-1].split('.')[0]
    pdb=PDB(pdb_id,pdb_file_name,title,resolution,models)
    return pdb


def atomDistance(atom1,atom2):
    try:
        atom_distance=math.sqrt((float(atom1.x)-float(atom2.x))**2+(float(atom1.y)-float(atom2.y))**2+(float(atom1.z)-float(atom2.z))**2)
    except:
        atom_distance=None
    #-
    return atom_distance


def residueDistance(residue_1,residue_2):
    atoms_1=residue_1.atoms
    atoms_2=residue_2.atoms
    #start debug
    ## print residue_1.res_seq
    ## print residue_1.res_name
    ## print residue_2.res_seq
    ## print residue_2.res_name
    #end debug
    #calculate atomic distances
    atomic_distances=[]
    for atom1 in atoms_1:
        for atom2 in atoms_2:
            distance=atomDistance(atom1,atom2)
            atomic_distances.append(distance)
    #--
    #compute residue-residue distance as the minimum of all atomic distances
    residue_distance=min(atomic_distances)
    #print residue_distance
    return residue_distance


def atomToResidueDistance(atom,residue):
    atoms_2=residue.atoms
    #start debug
    ## print residue.res_seq
    ## print residue.res_name
    #end debug
    #calculate atomic distances
    atomic_distances=[]
    for atom2 in atoms_2:
        distance=atomDistance(atom,atom2)
        atomic_distances.append(distance)
    #-
    #compute atom-residue distance as the minimum of all atomic distances
    atom_to_residue_distance=min(atomic_distances)
    #print atom_to_residue_distance
    return atom_to_residue_distance


def cAlphaDistance(resnum_1,resnum_2,pdb,modelnum=0,chain_ID1='A',chain_ID2='A'):
    model=pdb.models[modelnum]
    chain_1=None
    chain_2=None
    for chain in model.chains:
        if chain.id==chain_ID1:
            chain_1=chain
        elif chain.id==chain_ID2:
            chain_2=chain
    #--
    residue_1=chain_1.residues[resnum_1-1]
    residue_2=chain_2.residues[resnum_2-1]
    atoms_1=residue_1.atoms
    atoms_2=residue_2.atoms
    #start debug
    ## print pdb.id
    ## print model.serial
    ## print chain_1.id
    ## print chain_2.id
    ## print residue_1.res_seq
    ## print residue_1.res_name
    ## print residue_2.res_seq
    ## print residue_2.res_name
    #end debug
    #calculate C-alpha distance
    c_alpha_distance=''
    for atom1 in atoms_1:
        #print '#'+atom1.name+'#'
        if atom1.name.strip()=='CA':
            for atom2 in atoms_2:
                if atom2.name.strip()=='CA':
                    c_alpha_distance=atomDistance(atom1,atom2)
                    break
            #--
            break
    #--
    #print c_alpha_distance
    return c_alpha_distance


def cAlphaResidueDistance(residue_1,residue_2):
    atoms_1=residue_1.atoms
    atoms_2=residue_2.atoms
    #start debug
    ## print residue_1.res_seq
    ## print residue_1.res_name
    ## print residue_2.res_seq
    ## print residue_2.res_name
    #end debug
    #calculate C-alpha distance
    c_alpha_distance=''
    for atom1 in atoms_1:
        #print '#'+atom1.name+'#'
        if atom1.name.strip()=='CA':
            for atom2 in atoms_2:
                if atom2.name.strip()=='CA':
                    c_alpha_distance=atomDistance(atom1,atom2)
                    break
            #--
            break
    #--
    #print c_alpha_distance
    return c_alpha_distance


def cAlphaRMSD(residues_1,residues_2,printWarnings=True):
    num_residues=len(residues_1)
    c_alpha_rmsd=0
    #calculate C-alpha rmsd
    for i in range(num_residues):
        residue1=residues_1[i]
        residue2=residues_2[i]
        if residue1.res_seq!=residue2.res_seq and printWarnings:
            print residue1.res_seq,residue2.res_seq
            print 'WARNING: calculating RMSD for potentially different positions'
        #-
        atoms_1=residue1.atoms
        atoms_2=residue2.atoms
        for atom1 in atoms_1:
            if atom1.name.strip()=='CA':
                for atom2 in atoms_2:
                    if atom2.name.strip()=='CA':
                        squared_distance=(float(atom1.x)-float(atom2.x))**2+(float(atom1.y)-float(atom2.y))**2+(float(atom1.z)-float(atom2.z))**2
                        #print residue1.res_seq, math.sqrt(squared_distance)
                        c_alpha_rmsd+=squared_distance
                        break
                #--
                break
    #---
    c_alpha_rmsd=round(math.sqrt(c_alpha_rmsd/float(num_residues)),2)
    #start debug
    ## print residues_1[0].res_seq, residues_1[-1].res_seq
    ## print residues_2[0].res_seq, residues_2[-1].res_seq
    ## print c_alpha_rmsd
    #end debug
    return c_alpha_rmsd


def getRosettaNumbering(pdb_filename,model_serial=0,chain_ID='A'):
    rosetta_numbering_map={}
    #parse PDB file and store Rosetta numbering map
    pdb=parsePDB(pdb_filename)
    for model in pdb.models:
        if model.serial==model_serial:
            for chain in model.chains:
                if chain.id==chain_ID:
                    residues=chain.residues
                    for i in range(len(residues)):
                        residue=residues[i]
                        rosetta_numbering_map[int(residue.res_seq)]=i+1
    #-----
    return rosetta_numbering_map


def getModelSequence(model=None):
    sequence=''
    for chain in model.chains:
        residues=chain.residues
        for residue in residues:
            if residue.is_canonical:
                sequence+=one_letter_codes[residue.res_name]
    #---
    return sequence

 
    
