#!/usr/bin/python2.4
# encoding: utf-8
"""
untitled.py

Created by Florian Lauck on 2009-10-02.
Copyright (c) 2009 __UCSF__. All rights reserved.
"""

import os
import sys
sys.path.insert(0, "../common/")
import pdb
import time
import types
import string ##debug
import shutil
import tempfile
import subprocess
import rosettahelper
import traceback
import re

from rosettaexec import RosettaExec
from rosettabackrub import RosettaBackrub
from rosettaseqtol_onerun import RosettaSeqTolONE
from weblogolib import *
#from molprobity_analysis import MolProbityAnalysis
from RosettaProtocols import RosettaBinaries

server_root = '/var/www/html/rosettaweb/backrub/'

def parseResidueList(partners, pattern, argv):
    mapping = {}
    idx = 0
    while (idx < len(argv)):
        str = argv[idx]
        if str not in string.ascii_uppercase:
            # The parameter is a residue
            m = re.match(r"%s" % pattern, str, re.IGNORECASE)
            if m:
                numparams = m.lastindex       
                if numparams == 1:
                    if not mapping.get(chain):
                        mapping[chain] = []
                    mapping[chain].append(m.group("Residue"))
                elif numparams == 2:
                    if not mapping.get(chain):
                        mapping[chain] = {}
                    mapping[chain][m.group("Residue")] = m.group("AminoAcid")
                else:
                    # Should never happen
                    raise CommandLineException
            else:
                sys.stderr.write("Error parsing the list of residues (%s)." % str)
                raise CommandLineException
        else:
            # The parameter is a chain name
            if not partners:
                idx += 1
                break
            try:
                # We expect each partner to appear exactly once within the parsing
                chain = str
                partners.remove(str)
            except:
                raise CommandLineException
        idx += 1
    # If there are additional parameters, spit the last one back 
    if idx < len(argv):
        idx -= 1
        
    return mapping, idx

def getResIDs(params, justification = 0):
    design = []
    for partner in params['Partners']:
        if params['Designed'].get(partner):
            pm = params['Designed'][partner]
            for residue in pm:
                design.append('%s%s' % (partner, str(residue).rjust(justification)))
    return design

def make_seqtol_resfile( pdb, params, radius, residue_ids = None):
    """create a resfile for the chains
       Returns True, contents_of_resfile if a non-empty sequence tolerance residue file is made 
       Returns False, error_message if the sequence tolerance residue file is empty 
       residues in interface: NATAA (conformation can be changed)
       residues mutation: PIKAA ADEFGHIKLMNPQRSTVWY (design sequence)"""
        
    # get all residues:
    if not residue_ids:
        residue_ids = pdb.aa_resids() #todo: cache these values locally on first access and clear on pdb editing
    # turn list of ints in chainid, resid strings
    # e.g. design := ['A  23', 'B 123', 'A1234']
        
    # Compile a formatted list of designed residues
    design = getResIDs(params, justification = 4)
        
    # get the neighbors for each residue:
    resentry = {}            
    neighbor_lists = pdb.fastneighbors2( float(radius), design, atom = " CA ")

    # Add any residues neighboring designed residues to the flexible set
    for designres, neighbors in neighbor_lists.items():
        for neighbor in neighbors:
            resentry["%s %s" % (neighbor[1:].strip(), neighbor[0])] = " NATAA\n"  
        
    #for res in design:
    #    for neighbor in neighbor_lists.get(res) or []:
    #        resentry["%s %s" % (neighbor[1:].strip(), neighbor[0])] = " NATAA\n"  
    # Add the designed residues to the designed set, overriding any existing flexible entries
    for res in design:
        resentry["%s %s" % (res[1:].strip(), res[0])] = " PIKAA ADEFGHIKLMNPQRSTVWY\n"        
    
    if not resentry:
        return False, "The chosen designed residues resulting in an empty resfile and so could not be used."    
    
    contents = 'NATRO\nstart\n'
    for k,v in iter(sorted(resentry.iteritems())):
        contents += k + v
        
    return True, contents
    
    
    
class SequenceToleranceException(Exception): pass

# todo: Move into common file
class PostProcessingException(Exception): pass
class CommandLineException(Exception): pass

class RosettaSeqTol(RosettaExec):
    """Rosetta Sequence Tolerance Code class. 
       This class executes a backrub rub on its own and uses the resulting ensemble for interface design"""
  
    # 'parameter' should contain the following list of parameters:
    #    backrub_executable, seqtol_executable, pdb_filename, pdb_id, pdb_content, ensemble_size, radius, Boltzmann
    #    numchains, partners, weights, premutated, designed
  
    # additional attributes
    default       = ""   # resfile default for amino acids
    residues      = {}   # contains the residues and their modes according to rosetta: { (chain, resID):["PIKAA","PHKL"] }
    backrub       = []   # residues to which backrub should be applied: [ (chain,resid), ... ]
    pivot_res     = []   # list of pivot residues, consecutively numbered from 1 [1,...]
    map_res_id    = {}   # contains the mapping from (chain,resid) to pivot_res 
    backrub_resfile = None
    executable    = ''
  
    def import_pdb(self, filename, contents):
        """Import a pdb file from the database and write it to the temporary directory"""
        
        self.pdb = pdb.PDB(contents.split('\n'))
        self.pdb.pruneChains(self.parameter['Partners'])  # remove everything but the chosen chains or keep all chains if the list is empty
        
        # pdb_content is passed directly to backrub so remove the pruned chain lines before the backrub
        # todo: Note that the removed heteroatoms are read by backrub 
        self.parameter['pdb_content'] = string.join(self.pdb.lines, '\n')        
        
        self.pdb.remove_hetatm()  # rosetta doesn't like heteroatoms so let's remove them
        #self.pdb.fix_chain_id()   # adds a chain ID if the column is empty
              
        # internal mini resids don't correspond to the pdb file resids
        # the pivot residues need to be numbered consecuively from 1 up
        self.map_res_id = self.pdb.get_residue_mapping()
        self.pdb.write(self.workingdir_file_path(filename))
        self.name_pdb = filename
        return self.name_pdb
    
    def write_backrub_resfile( self ):
        """create a resfile of premutations for the backrub"""
        
        
        # Write out the premutated residues
        s = ""
        params = self.parameter
        for partner in params['Partners']:
            if params['Premutated'].get(partner):
                pm = params['Premutated'][partner]
                for residue in pm:
                    #todo: check that residue exists -  # get all residues:  residue_ids     = self.pdb.aa_resids()
                    s += ("%s %s PIKAA %s\n" % (residue.strip(), partner, pm[residue]))
        
        # Only create a file if there are any premutations
        if s != "":
            self.backrub_resfile = "backrub_%s.resfile" % self.ID
            output_handle = open( self.workingdir_file_path(self.backrub_resfile), 'w')
            output_handle.write('NATAA\nstart\n')
            output_handle.write(s)  
            output_handle.write( "\n" )
            output_handle.close()
        
    def write_seqtol_resfile( self ):
        """create a resfile for the chains
            residues in interface: NATAA (conformation can be changed)
            residues mutation: PIKAA ADEFGHIKLMNPQRSTVWY (design sequence)"""
        
        resfileHasContents, contents = make_seqtol_resfile( self.pdb, self.parameter, self.parameter['radius'], self.pdb.aa_resids())
        
        if resfileHasContents:
            self.name_resfile = "seqtol_%s.resfile" % self.ID
            output_handle = open( self.workingdir_file_path(self.name_resfile), 'w')
            output_handle.write(contents)
            output_handle.write( "\n" )
            output_handle.close()
        else:
            sys.stderr.write("An error occurred during the sequence tolerance execution. The chosen designed residues resulting in an empty resfile and so could not be used.")
            raise SequenceToleranceException
          
      
    def preprocessing(self):    
        """this is the place to implement the preprocessing protocol for your application
            e.g.: -create temp dir
                  -clean up pdb file
                  -...
        """
        # self.make_workingdir( "seqtol_" )       # create working dir with prefix "seqtol_"
        self.workingdir = os.path.abspath('./')
        self.import_pdb( self.parameter['pdb_filename'], self.parameter['pdb_content'])
        self.write_backrub_resfile()
        self.write_seqtol_resfile()
    

    def run(self):
    
        # RUN BACKRUB FIRST TO CREATE AN ENSEMBLE
        # parameter for backrub
        backrub_parameter = {'pdb_id' : self.parameter['pdb_id'],
                             'pdb_content' : self.parameter['pdb_content'],
                             'ensemble_size' : int(self.parameter['ensemble_size']),
                             'mode' : 'no_mutation'}
        # this creates an backrub object, with a temporary directory "backrub_*" insiede the seqtol tempdir
        self.RosettaBackrub = RosettaBackrub( ID = 0,
                                              executable = self.parameter['backrub_executable'],
                                              dbdir      = self.dbdir,
                                              tempdir    = self.tempdir,
                                              parameter  = backrub_parameter )
        # run preprocessing
        self.RosettaBackrub.preprocessing(self.backrub_resfile)    
        
        print "\tRunning backrub."
        # start the backrub job and check every 5 seconds whether it's finished yet
        self.RosettaBackrub.run()
        while not self.RosettaBackrub.is_done():
            time.sleep(5)
        # check if all files were created
        if not self.RosettaBackrub.postprocessing():
            print "Failed"
            sys.stdout.flush()
            sys.exit(0)
        
        # get list of the low file filenames
        low_filenames = self.RosettaBackrub.get_low_filenames()
        
        print "\tRunning Design:",
        
        seqtol_parameter = {'resfile': self.workingdir_file_path(self.name_resfile)}
    
        for filename in low_filenames:
            i = low_filenames.index(filename) +1
            print ' %s' % i,
            
            seqtol_parameter['weights'] = self.parameter['weights']
            seqtol_parameter['name_pdb'] = filename
            
            one_run = RosettaSeqTolONE( ID = i,
                                        executable = self.parameter['seqtol_executable'],
                                        dbdir      = self.dbdir,
                                        tempdir    = self.tempdir,
                                        parameter  = seqtol_parameter )
            one_run.preprocessing()
            one_run.run()
            while True:   
                if one_run.is_done():
                    errorcode = one_run.errorcode
                    if errorcode != 0:
                        if errorcode == None:
                            sys.stderr.write("An error occurred setting the return code from the sequence tolerance execution.")
                        sys.stderr.write("An error occurred during the sequence tolerance execution. The errorcode is %s." % str(errorcode))
                        raise SequenceToleranceException
                    break;
                time.sleep(5)
            
            one_run.postprocessing()
    
            # molprobity analysis of designed files
            # bindir = string.join(self.parameter['backrub_executable'].split('/')[:-1],'/')
            # self.molprobity = MolProbityAnalysis(ID=0,
            #                                      bin_dir=bindir,  #"/opt/rosettabackend/bin/",
            #                                      workingdir=self.workingdir,
            #                                      initial_structure=self.parameter['pdb_filename'] )
            # self.molprobity.preprocessing(suffix='_ms_0000')
            # self.molprobity.run()
            # while not self.molprobity.is_done():
            #   time.sleep(2)
            # self.molprobity.postprocessing()
            # self.molprobity.write_results()
            # self.molprobity.plot_results('molprobity_plot')
          
            print ''
    
    def postprocessing(self):
        """ Run the post processing on the script """
    
        # run Colin's analysis script: filtering and profiles/motifs
        
        
        thresh_or_temp = self.parameter['Boltzmann']
        
        weights = self.parameter['weights']
        fitness_coef = 'c(%s' % weights[0]
        for i in range(1, len(weights)):
            fitness_coef += ', %s' % weights[i]
        fitness_coef += ')'
        
        type_st = '\\"boltzmann\\"'
        prefix  = '\\"tolerance\\"'
        percentile = '.5'
        
        self.workingdir = os.path.abspath('./') #todo: delete
        cmd = '''/bin/echo "process_seqtol(\'%s\', %s, %s, %s, %s, %s);\" \\
                  | /bin/cat %sdaemon/specificity.R - \\
                  | /usr/bin/R --vanilla''' % ( self.workingdir, fitness_coef, thresh_or_temp, type_st, percentile, prefix, server_root)
        
                 
        # open files for stderr and stdout 
        self.file_stdout = open(self.workingdir_file_path( self.filename_stdout ), 'a+')
        self.file_stderr = open(self.workingdir_file_path( self.filename_stderr ), 'a+')
        self.file_stdout.write("*********************** R output ***********************\n")
        print(cmd)
        subp = subprocess.Popen(cmd, 
                                stdout=self.file_stdout,
                                stderr=self.file_stderr,
                                cwd=self.workingdir,
                                shell=True,
                                executable='/bin/bash' )
                
        while True:
            returncode = subp.poll()
            if returncode != None:
                if returncode != 0:
                    sys.stderr.write("An error occurred during the postprocessing script. The errorcode is %d." % returncode)
                    raise PostProcessingException
                break;
            time.sleep(2)
        
        subp.returncode
        
        self.file_stdout.close()
        self.file_stderr.close()
        count = 0
        if not os.path.exists( self.workingdir_file_path("tolerance_sequences.fasta") ) and count < 10 :
            time.sleep(1) # make sure the fasta file gets written
            count += 1
        
        #todo: should fail gracefully here if the fasta file still isn't written
          
        # create weblogo from the created fasta file
        seqs = read_seq_data(open(self.workingdir_file_path("tolerance_sequences.fasta")))
        logo_data = LogoData.from_seqs(seqs)
        logo_data.alphabet = std_alphabets['protein'] # this seems to affect the coloring, but not the actual motif
        logo_options = LogoOptions()
        logo_options.title = "Sequence profile"
        logo_options.number_interval = 1
        logo_options.color_scheme = std_color_schemes["chemistry"]
        
        ann = getResIDs(self.parameter)
        logo_options.annotate = ann
        
        logo_format = LogoFormat(logo_data, logo_options)
        png_print_formatter(logo_data, logo_format, open(self.workingdir_file_path( "tolerance_motif.png" ), 'w'))
        
        # let's just quickly delete the *last.pdb and generation files:
        list_files = os.listdir(self.workingdir)
        list_files.sort()
        for pdb_fn in rosettahelper.grep('%s_[0-9]_[0-9]{4}_last\.pdb' % (self.parameter['pdb_id']), list_files):
            os.remove( self.workingdir_file_path(pdb_fn) )
        for pdb_fn in rosettahelper.grep('%s_[0-9]_[0-9]{4}_low\.ga\.generations\.gz' % (self.parameter['pdb_id']), list_files):
            os.remove( self.workingdir_file_path(pdb_fn) )
        
        # stdout = open(self.workingdir_file_path( self.filename_stdout ),'r')
        # for x in stdout.readlines():
        #   print x,
        # stdout.close()
        # # self.copy_working_dir('')

cmdLineUsage = """
The command line has the form:
  rosettaseqtol.py <job#> <pdbfilename> <#structures> <radius> <kT> <#chains> <list_of_chains> <list_of_weights> <chain1> <chain1premutations> .. <chainn> <chain1premutations> <chain1> <chain1residues> .. <chainn> <chainnresidues>

<list_of_weights> is a space-separated sequence, ordered by chain index i, of:
  1) the self-energies k_P_i, for all i;
  2) followed by all interaction energies k_P_iP_j where i < j, and so on for all i.
Thus, the length of list_of_weights is determined by: 1 + sum_{i \in [1,..,#chains]}(i).
  e.g. #chains = 1 => length = 1 + 1 = 2, #chains = 2 => length = 1+1+2=4. #chains = 3 => length = 1+1+2+3 = 7, ... 

An element of <chainipremutations> has the form <residue><short amino acid code> e.g. "318A" for ALA.
An element of <chainiresidues> has the form <residue> e.g. "318".

An example command line for two chains A, B with one mutation for A and standard weights is: 
  rosettaseqtol.py 1601 2I0L_A_C_V2006.pdb 2 10.0 0.251 2 A B 0.4 0.4 1.0 A 318 K B A 318 B
where the <list_of_weights> consists of k_P1 = 0.4, k_P2 = 0.4, and k_P1P2 = 1.0.
"""

if __name__ == "__main__":
    '''this runs a sequence tolerance simulation for a given set of parameters'''

    errorDuringParsingCommandLine = True
    try:      
        # You needs 9 arguments for a run with one chain and no residues 
        if len(sys.argv) < 10:
            raise CommandLineException
      
        print "Reading parameters."
        print ("%s" % string.join(sys.argv[0:], " ") )
        
        dict_para = {}
    
        bin_dir = '%sbin/' % server_root
      
        #todo: Parameterize the revision number
        #dict_para['backrub_executable'] = '%sbackrub_r32532' % bin_dir
        #dict_para['seqtol_executable']  = '%ssequence_tolerance_r32532' % bin_dir

        dict_para['backrub_executable'] = '%s%s' % (bin_dir, RosettaBinaries["seqtolJMB"]["backrub"])
        dict_para['seqtol_executable']  = '%s%s' % (bin_dir, RosettaBinaries["seqtolJMB"]["sequence_tolerance"])
        
        # parse parameters
        dict_para['pdb_filename'] = sys.argv[2].split('/')[-1]
        dict_para['pdb_id'] = dict_para['pdb_filename'].split('.')[0]
        try:
            handle_pdb = open(sys.argv[2])
            dict_para['pdb_content'] =  handle_pdb.read()
            handle_pdb.close()
        except:
            errorDuringParsingCommandLine = False
            raise
    
        dict_para['ensemble_size']  = sys.argv[3]
        dict_para['radius']         = sys.argv[4]
        dict_para['Boltzmann']      = sys.argv[5]
        numchains                   = int(sys.argv[6])
        dict_para['numchains']      = numchains      
        vaidx = 7 + numchains
        dict_para['Partners']       = sys.argv[7:vaidx]    
        
        # Read in the weights
        numweights = 1
        for i in range(1, numchains + 1):
            numweights += i
        dict_para['weights'] =  sys.argv[vaidx:vaidx + numweights]
        vaidx += numweights
        
        # Read in the residues
        premutated, numparsed = parseResidueList(list(dict_para['Partners']), "^(?P<Residue>\d+)(?P<AminoAcid>[A-Za-z])$", sys.argv[vaidx:])            
        dict_para["Premutated"] = premutated
        vaidx += numparsed
        
        designed, numparsed   = parseResidueList(list(dict_para['Partners']), "^(?P<Residue>\d+)$", sys.argv[vaidx:])
        dict_para["Designed"] = designed    
        vaidx += numparsed
        
        errorDuringParsingCommandLine = False
      
        print "Creating RosettaSeqTol object."
      
        obj = RosettaSeqTol(ID = sys.argv[1],
                    executable = "ls", # not needed since this class doesn't actually execute the simulation
                    dbdir      = "%sdata/%s/" % (server_root, RosettaBinaries["seqtolJMB"]["database"]),
                    tempdir    = './',
                    parameter  = dict_para )
        
        print "Running Preprocessing."
        
        obj.preprocessing()
        print "Running Simulation."
        obj.run()
        print "Running Postprocessing and Analysis."
        obj.postprocessing()
        print "Success!"
    except:
        sys.stderr.write("\nError occurred:\n")
        #traceback.print_exc()
        if errorDuringParsingCommandLine:
            print("Arguments passed: ", string.join(sys.argv, ', '))
            print(cmdLineUsage)
        raise
        
    