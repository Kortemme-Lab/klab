#!/usr/bin/python2.4
# encoding: utf-8
"""
untitled.py

Created by Florian Lauck on 2010.
Copyright (c) 2009 __UCSF__. All rights reserved.
"""

# This implements Elisabeth's version of Sequence Plasticity.
# The binary to create the backrub ensemble is: rosetta_classic_elisabeth_backrub.gcc and was found here: chef.compbio.ucsf.edu:/netapp/home/colin/rosetta/rosetta.gcc
# This file has the command line parameters: /kortemmelab/shared/publication_data/ehumphris/Structure_2008/TO_ORGANIZE/ensemble_template


import os
import sys
import re
import pdb
import time
import types
import string ##debug
import shutil
import tempfile
import subprocess
import chainsequence
import rosettahelper

from rosettaexec import RosettaExec
from rosettaplusplus import RosettaPlusPlus
from rosettaseqtol_onerun_classic import RosettaSeqTolONE
from weblogolib import *
#from molprobity_analysis import MolProbityAnalysis

server_root = '/var/rosettabackend/'

class RosettaSeqTol(RosettaExec):
  """Rosetta Sequence Tolerance Code class. 
     This class executes a backrub rub on it's own and uses the resulting ensemble for interface design"""
  
  ## 'parameter' should contain the following list of parameter:
  # pdb_id, pdb_content, ensemble_size, backrub_executable, partner_1, partner_design, design
  ## optional (depending on mode)
    
  # additional attributes
  default       = ""   # resfile default for amino acids
  residues      = {}   # contains the residues and their modes according to rosetta: { (chain, resID):["PIKAA","PHKL"] }
  backrub       = []   # residues to which backrub should be applied: [ (chain,resid), ... ]
  pivot_res     = []   # list of pivot residues, consecutively numbered from 1 [1,...]
  map_res_id    = {}   # contains the mapping from (chain,resid) to pivot_res 
  failed_runs   = []
  filename_stdout = "stdout_postprocessing.txt"
  filename_stderr = "stderr_postprocessing.txt"
  executable    = ''
  
  def import_pdb(self, filename, contents):
    """Import a pdb file from the database and write it to the temporary directory"""
    
    self.pdb = pdb.PDB(contents.split('\n'))
    self.pdb.remove_hetatm()   # rosetta doesn't like heteroatoms so let's remove them
    #self.pdb.fix_chain_id()   # adds a chain ID if the column is empty
          
    # internal mini resids don't correspond to the pdb file resids
    # the pivot residues need to be numbered consecuively from 1 up
    self.map_res_id = self.pdb.get_residue_mapping()
    self.pdb.write(self.workingdir_file_path(filename))
    self.name_pdb = filename
    
    # get chains
    seqs = chainsequence.ChainSequences()
    # create dict with key = chain ID, value = list of residue IDs
    self.dict_chain2resnums = seqs.parse_atoms(self.pdb)
            
    return self.name_pdb

    
  def _write_line(self, chain, seq_res, pdb_res, mode ):
    ''' chain, sequential residue number, pdb residue number, mode'''
    line = " %s " % chain
    line += "%4.i " % seq_res
    line += "%4.i " % pdb_res
    line += mode + '\n'
    
    return line

      
  def write_resfile( self ):
    """create a resfile for the two chains
        residues in interface: NATAA (conformation can be changed)
        residues mutation: PIKAA ADEFGHIKLMNPQRSTVWY (design sequence)"""
    
    # get all residues:
    residue_ids = self.pdb.aa_resids()
    # turn list of ints in chainid, resid strings
    self.design =  [ '%s%s' % (self.parameter['partner_1'], str(residue).rjust(4)) for residue in self.parameter['design_1'] ]
    self.design += [ '%s%s' % (self.parameter['partner_2'], str(residue).rjust(4)) for residue in self.parameter['design_2'] ]
    print self.design
    self.name_resfile = "seqtol.resfile" #% self.ID
    output_handle = None
    if os.path.exists( self.workingdir_file_path(self.name_resfile) ):
      return
    
    output_handle = open( self.workingdir_file_path(self.name_resfile), 'w')
    output_handle.write("""This file specifies which residues will be varied

 Column   2:  Chain
 Column   4-7:  sequential residue number
 Column   9-12:  pdb residue number
 Column  14-18: id  (described below)
 Column  20-40: amino acids to be used

 NATAA  => use native amino acid
 ALLAA  => all amino acids
 NATRO  => native amino acid and rotamer
 PIKAA  => select inividual amino acids
 POLAR  => polar amino acids
 APOLA  => apolar amino acids
 
 The following demo lines are in the proper format
 
 A    1    3 NATAA
 A    2    4 ALLAA
 A    3    6 NATRO
 A    4    7 NATAA
 B    5    1 PIKAA  DFLM
 B    6    2 PIKAA  HIL
 B    7    3 POLAR
 -------------------------------------------------
 start 
""")

    # get neighbors of all designed residues
    neighbor_list = []
    for residue in self.design:
      neighbor_list.extend( self.pdb.neighbors3(self.parameter['radius'], residue) )
    
    neighbor_list = rosettahelper.unique(neighbor_list)
    neighbor_list.sort()

    self.map_chainres2seq = {}
    
    # get list of chain IDs
    chains = self.dict_chain2resnums.keys()
    chains.sort()
    seq_resnum = 0
    for chain in chains:
      for resnum in self.dict_chain2resnums[chain]:
        seq_resnum += 1 # important
        resnum = int(resnum)
        residue = "%s%4.i" % (chain, resnum)
        if residue in self.design:
          output_handle.write( self._write_line(chain, seq_resnum, resnum, "ALLAA") )
        elif residue in neighbor_list:
          output_handle.write( self._write_line(chain, seq_resnum, resnum, "NATAA") )
        else:
          output_handle.write( self._write_line(chain, seq_resnum, resnum, "NATRO") )
          
        self.map_chainres2seq[chain+str(resnum)] = str(seq_resnum) # save this for later
    output_handle.write( "\n" )
    output_handle.close()
    return

      
  def preprocessing(self):    
    """this is the place to implement the preprocessing protocol for your application
        e.g.: -create temp dir
              -clean up pdb file
              -...
    """
    # self.make_workingdir( "seqtol_" )       # create working dir with prefix "seqtol_"
    self.workingdir = os.path.abspath('./')
    self.import_pdb( self.parameter['pdb_filename'], self.parameter['pdb_content'])
    self.write_resfile()
    

  def run(self):
    
    
    if not os.path.exists( self.workingdir + '/backrub' ): # skip the whole backrub run
      # RUN BACKRUB FIRST TO CREATE AN ENSEMBLE
      # this creates an backrub object, with a temporary directory "backrub" insiede the seqtol tempdir
      self.RosettaBackrub = RosettaPlusPlus( ID = 0, 
                                             executable = self.parameter['backrub_executable'], 
                                             datadir = self.dbdir, 
                                             tempdir = self.tempdir, 
                                             auto_cleanup = False)
      # do preprocessing
      os.mkdir( self.workingdir + '/backrub' )
      self.RosettaBackrub.workingdir = './backrub'
      self.RosettaBackrub.set_pdb( self.parameter['pdb_filename'], self.parameter['pdb_content'] )
    
      # no mutation, apply backrub to all residues
      default         = "NATAA"
      residue_ids     = self.pdb.aa_resids()
      resid2type      = self.pdb.aa_resid2type()
      backbone        = []   # residues to which backrub should be applied: [ (chain,resid), ... ]
      chain_parameter = []
    
      # chains for classic
      for chain in self.pdb.chain_ids():
        chain_parameter.append("-chain")
        chain_parameter.append(str(chain))
      
      for res in residue_ids:
        x = [ res[0], res[1:].strip() ]
        if len(x) == 1:
          backbone.append( ( "_", int(x[0].lstrip())) )
        elif resid2type[res] != "C": # no backrub for cystein residues to avoid S=S breaking
          backbone.append( ( x[0], int(x[1].lstrip())) )
      
      fn_resfile = self.RosettaBackrub.write_resfile( default, {}, backbone )
      
      print "\tRunning backrub."
      self.RosettaBackrub.run_args( [ "-paths", os.path.abspath("backrub") + "/paths.txt",
                                      "-pose1","-backrub_mc",
                                      "-fa_input",
                                      "-norepack_disulf", "-find_disulf",
                                      "-s", self.name_pdb, "-read_all_chains" ] + chain_parameter + ["-series","BR",
                                      "-protein", self.parameter['pdb_id'],
                                      "-resfile", fn_resfile,
                                      "-bond_angle_params","bond_angle_amber",
                                      "-use_pdb_numbering",
                                      "-ex1","-ex2",
                                      "-skip_missing_residues",
                                      "-extrachi_cutoff","0",
                                      "-max_res", "12", 
                                      "-only_bb", ".5", 
                                      "-only_rot", ".5",
                                      "-nstruct",  self.parameter['ensemble_size'],
                                      "-ntrials", "10000"] ) # should be: 10000
    
      while not self.RosettaBackrub.is_done():
        time.sleep(5)
      if self.RosettaBackrub == 'terminated':
        handle_err = open('failed_backrub.txt','w')
        handle_err.write('Backrub run was terminated\n')
        handle_err.close()
        sys.exit(0)
      print self.RosettaBackrub.command
      self.RosettaBackrub.file_stdout.close()
      self.RosettaBackrub.file_stderr.close()
    ######## end skip
    sys.exit(0)   
    # check whether files were created
    low_filenames = []
    error = ''
    shutil.copy( os.path.abspath("backrub") + "/paths.txt", self.workingdir + "/paths.txt" )
    shutil.copy( os.path.abspath("backrub") + "/input.resfile", self.workingdir + "/backrub.resfile" )
    for x in range(1, int(self.parameter['ensemble_size'])+1):
      low_file  = self.workingdir_file_path( 'backrub/BR%slow_%04.i.pdb' % (self.parameter['pdb_id'], x ))
      last_file = self.workingdir_file_path( 'backrub/BR%slast_%04.i.pdb'  % (self.parameter['pdb_id'], x ))
      if not os.path.exists( low_file ): 
        error += ' %s missing\n' % low_file
      else:
        shutil.copy( low_file, self.workingdir + '/' + low_file.split('/')[-1] )
        low_filenames.append( 'BR%slow_%04.i.pdb' % (self.parameter['pdb_id'], x ) )
      if not os.path.exists( last_file ):
        error += ' %s missing\n' % ( last_file )
    
    if error != '':
      print error
      handle_err = open('failed_backrub.txt','a+')
      handle_err.write(error)
      handle_err.close()
      sys.exit(0)
    
    # RUN DESIGN
    print "\tRunning Design:",
    seqtol_parameter = {'resfile': self.workingdir_file_path(self.name_resfile)}
    self.list_outfiles = []
    
    for filename in low_filenames:
      i = low_filenames.index(filename) + 1
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
      while not one_run.is_done():
        time.sleep(5)
      if one_run.exit == "terminated":
        self.failed_runs.append(i)
      else:
        one_run.postprocessing()
        self.list_outfiles.append(one_run.filename_stdout)
      
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
    if self.failed_runs != []: # check if any failed
      failed_handle = open(self.workingdir_file_path("failed_jobs.txt"),'w')
      for i in self.failed_runs:
        failed_handle.write("%s\t%s\n" % (i,low_filenames[i]))
      failed_handle.close()
      
  # def _grep(self,string,filename):
  #   cmd = "grep \'^ %s\' %s" % ( string, filename )
  #   output = os.system( cmd )
  #   print cmd
  #   return [line.split() for line in output.split('\n')]
  
  def _grep(self,string,handle):
      expr = re.compile(string)
      results = filter(expr.search,[str(line) for line in handle])
      return results
      # for i in range(len(result)):
      #   result[i] = result[i].split()
      # return result
  
  def _filter(self,list_seq):
    """this sorts sequences after fitness score"""
    import decimal
    decimal.getcontext().prec = 1
    list_seq.sort(lambda x,y: cmp(decimal.Decimal(x[1]), decimal.Decimal(y[1])), reverse=False)
    return list_seq
      
      
  def postprocessing(self):
    """ this recreates Elisabeth Analysis scripts in /kortemmelab/shared/publication_data/ehumphris/Structure_2008/CODE/SCRIPTS """
    handle_err = open( self.workingdir_file_path( 'error.log' ), 'a+' )
    # AMINO ACID FREQUENCIES
    print "\tAmino Acid frequencies"
    list_res = []
    
    for x in self.parameter['design_1']:
      list_res.append(self.parameter['partner_1']+str(x))
    for x in self.parameter['design_2']:
      list_res.append(self.parameter['partner_2']+str(x))
    
    # this does the same as get_data.pl
    for design_res in list_res:
      one_pos = []
      for filename in self.list_outfiles:
        handle = open(filename,'r')
        # print "grep:", 
        # print '^ %s' % self.map_chainres2seq[design_res], "result: "
        grep_result = rosettahelper.grep('^ %s' % self.map_chainres2seq[design_res], handle)
        # print 'list:',  grep_result
        # print 'string', grep_result[0]
        # print 'split:', grep_result[0].split()
        # print grep_result
        if grep_result != []:
          one_pos.append( grep_result[0].split() )
        else:
          handle_err.write('Single sequence tolerance prediction run failed: see %s for details\n' % filename)
        handle.close()

      # sort and transpose the data of one_pos table: invert_textfiles.pl
      # the values are in the following order:
      order = ['id','A','D','E','F','G','H','I','K','L','M','N','P','Q','R','S','T','V','W','Y']
      # they should be in this order:
      res_order = ['W','F','Y','M','L','I','V','A','G','S','T','R','K','H','N','Q','D','E','P']
      # transpose:
      dict_res2values = {}
      for res in order:
        i = order.index(res)
        values4oneres = []
        for line in one_pos:
          values4oneres.append(line[i])
        dict_res2values[res] = values4oneres
      
      # sort and write the table to a file
      frequency_file = "freq_%s.txt" % design_res
      handle2 = open(frequency_file, 'w')
      for res in res_order:
        for freq in dict_res2values[res]:
          handle2.write('%s ' % freq)
        handle2.write('\n')
      handle2.write('\n')
      handle2.close()

    # run the R script for all positions and create the boxplots 
    
    parameter = "c("
    for design_res in list_res:
      parameter += "\'%s\'," % design_res
    parameter = parameter[:-1] + ")" # gets rid of the last ','
      
    cmd = '''/bin/echo \"plot_specificity_list(%s)\" \\
            | /bin/cat %sdaemon/specificity_classic.R - > specificity.R ; \\
            /usr/bin/R CMD BATCH specificity.R''' % ( parameter,server_root )
    print cmd
    # open files for stderr and stdout
    self.file_stdout = open(self.workingdir_file_path( self.filename_stdout ), 'a+')
    self.file_stderr = open(self.workingdir_file_path( self.filename_stderr ), 'a+')
    self.file_stdout.write("*********************** R output ***********************\n")

    subp = subprocess.Popen(cmd, 
                            stdout=self.file_stdout,
                            stderr=self.file_stderr,
                            cwd=self.workingdir,
                            shell=True,
                            executable='/bin/bash' )

    while subp.poll() == None:
      time.sleep(2)
  
    self.file_stdout.close()
    self.file_stderr.close()
    
    # CREATE SEQUENCE MOTIF    ## this all would be better off in the postprocessing of the onerun class
    print "\tSequence Motif"
    # 1st, get the data
    sequences_list_total = []
    si = 0
    for filename in self.list_outfiles:
      si += 1
      sequences_list = []
      output_handle = open(filename,'r')
      # read until the first "Generation"
      for line in output_handle:
        if line[0:10] == "Generation":
          # sequences_list.append( line.split()[5] )
          break                                    # and break
      # now the stuff we actually need to read in:
      for line in output_handle:
        if line[0:10] == "Generation":             # new Generation line: Contains the best scoring sequence, which is not necessarily in the cutoff range
          # sequences_list.append( line.split()[5] )
          pass
        elif len(line) > 1:                        # normal line is not empty and the sequence is at the beginning
          sequences_list.append( (line.split()[0], line.split()[1]) ) # ( sequence, fitness )
        else:
          break # break for the first empty line. This means we're done.
      output_handle.close()
      # now sort after score:
      self._filter(sequences_list)
      # get all pdb files associated with this run:
      list_files = os.listdir(self.workingdir)
      list_files.sort()
      list_this_run = rosettahelper.grep('BR%slow_%04.i_[A-Z]*\.pdb' % (self.parameter['pdb_id'], si), list_files)
      best_scoring_pdbs = []
      for designed_sequence in sequences_list[0:10]: # keep the 10 best scoring structures
        best_scoring_pdb = 'BR%slow_%04.i_%s.pdb' % (self.parameter['pdb_id'], si, designed_sequence[0])
        best_scoring_pdbs.append( best_scoring_pdb )
        try:
          list_this_run.remove( best_scoring_pdb ) # this list keeps track of the files that should be removed in the next step
        except ValueError:
          pass
      
      for pdb in list_this_run:
        if pdb not in best_scoring_pdbs:
          os.remove( self.workingdir_file_path( pdb ) )
          #print "delete " + self.workingdir + "/" + pdb

      sequences_list_total.extend(sequences_list[0:10]) # add 10 best scoring to the total list
    
    # write the actual fasta file with the 100 best scoring sequences
    fasta_file = "tolerance_sequences.fasta"
    handle_fasta = open(fasta_file,'w')
    i = 0
    for sequence in sequences_list_total[0:100]:
      i += 1
      handle_fasta.write('>%s\n%s\n' % (i,sequence[0]))
    handle_fasta.close()
    
    # 3rd, create the motif
    count = 0
    if not os.path.exists( self.workingdir_file_path("tolerance_sequences.fasta") ) and count < 10 :
      time.sleep(1) # make sure the fasta file gets written
      count += 1
    # create weblogo from the created fasta file
    seqs = read_seq_data(open(self.workingdir_file_path("tolerance_sequences.fasta")))
    logo_data = LogoData.from_seqs(seqs)
    logo_data.alphabet = std_alphabets['protein'] # this seems to affect the coloring, but not the actual motif
    logo_options = LogoOptions()
    logo_options.title = "Sequence profile"
    logo_options.number_interval = 1
    logo_options.color_scheme = std_color_schemes["chemistry"]
    logo_options.annotate = [self.parameter['partner_1'] + str(resid) for resid in self.parameter['design_1']] + [self.parameter['partner_2'] + str(resid) for resid in self.parameter['design_2']] #res_nums this is for Gregs hacked version that I don't have
    logo_format = LogoFormat(logo_data, logo_options)
    png_print_formatter(logo_data, logo_format, open(self.workingdir_file_path( "tolerance_motif.png" ), 'w'))

    # clean up and remove backrub directory
    #shutil.rmtree( self.workingdir_file_path("backrub") )
    
# end analysis
    handle_err.close()
    # stdout = open(self.workingdir_file_path( self.filename_stdout ),'r')
    # for x in stdout.readlines():
    #   print x,
    # stdout.close()
    # # self.copy_working_dir('')



if __name__ == "__main__":
  '''this runs a sequence tolerance simulation for a given set of parameters'''
  
  if len(sys.argv) < 8:
    print 'usage: %s <server job ID> <path to pdb> <ensemble size> <radius> <chain id 1> <design residues of chain 1> <chain id 2> <design residues of chain 2> ' % sys.argv[0]
    sys.exit(1)
  
  ## 'parameter' should contain the following list of parameter:
  # pdb_id, pdb_content, ensemble_size, backrub_executable, partner_1, partner_2, design
  # dict_para = { 'partner_1':'A', 'partner_2':'B', 'design1':[11,12,13,14,15], 'design2':[123,124,148] }
  
  print "Reading parameter."
  
  dict_para = {}

  bin_dir = '%sbin/' % server_root
  
  dict_para['backrub_executable'] = '%srosetta_classic_elisabeth_backrub.gcc' % bin_dir
  dict_para['seqtol_executable']  = '%srosetta_1Oct08.gcc' % bin_dir
  
  # parse parameter
  dict_para['pdb_filename'] = sys.argv[2].split('/')[-1]
  dict_para['pdb_id'] = dict_para['pdb_filename'].split('.')[0]
  handle_pdb = open(sys.argv[2])
  dict_para['pdb_content'] =  handle_pdb.read()
  handle_pdb.close()

  dict_para['ensemble_size']  = sys.argv[3]
  #dict_para['weights']        = ( sys.argv[4], sys.argv[5], sys.argv[6] )
  dict_para['radius'] = float(sys.argv[4])
  dict_para['partner_1']    = sys.argv[5]
  dict_para['design_1'] = []
  dict_para['design_2'] = []
  c = 1
  for residue in sys.argv[6:]:
    if residue not in string.ascii_uppercase:
      c += 1
      dict_para['design_1'].append(int(residue))
    else:
      dict_para['partner_2'] = residue
      break
  for residue in sys.argv[(6+c):]:
    dict_para['design_2'].append(int(residue))
    
  # print dict_para['partner_1'], dict_para['design_1']
  # print dict_para['partner_2'], dict_para['design_2']

  # create the object and get the simulation running
  for xxx in sys.argv:
    print xxx,
  print '\n'
  print "Creating RosettaSeqTol object."
  obj = RosettaSeqTol(ID = sys.argv[1],
                      executable = "ls", # not needed since this class doesn't actually execute the simulation
                      dbdir      = "%sdata/rosetta_database_elisabeth/" % server_root,
                      tempdir    = './',
                      parameter  = dict_para )
  print "Running Preprocessing."
  obj.preprocessing()
  print "Running Simulation."
  #obj.run()
  # this is for debugging:
  #handle_list = open("out.txt")
  #obj.list_outfiles = []
  #for fn in handle_list:
  #  obj.list_outfiles.append(fn.strip())
  #handle_list.close()
  print "Running Postprocessing and Analysis."
  #obj.postprocessing()
  print "Success!"
  
  
  
  
  
