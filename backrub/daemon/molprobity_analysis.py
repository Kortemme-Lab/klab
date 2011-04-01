#!/usr/bin/python2.4
# encoding: utf-8
"""
rosettaexec.py

Created by Florian Lauck on 2009-10-02.
Copyright (c) 2009 __UCSF__. All rights reserved.

"""
import os
import sys
import re
import time
import numpy
import types
import string ##debug
import shutil
import subprocess
from rosettaexec import RosettaExec
#from matplotlib.figure import Figure
from pylab import *


class MolProbityAnalysis(RosettaExec):
  """this executed the MolProbity Analysis
        ID = arbitrary ID
        workingdir = directory where the file can be written
        pdbdir  = directory with the pdb structures that are under investigation
  """

      
  def __init__( self, ID = 0, 
                      bin_dir = "/var/www/html/rosettaweb/backrub/bin/",
                      workingdir = "../temp/",
                      initial_structure = ''):
      
    self.ID                = ID  
    self.bin_dir           = bin_dir
    self.executable        = self.bin_dir + "/molprobity3/cmdline/oneline-analysis"
    self.workingdir        = workingdir                    # directory for molprobity output and analysis file
    self.pdbdir            = self.workingdir_file_path('pdb_links/') # directory with pdb files
    self.initial_structure = self.workingdir_file_path( initial_structure )
    self.filename_stdout   = "molprobity_raw_output.txt"
    self.filename_stderr   = "molprobity_err_%s.dat" % str(self.ID)
    self.filename_results  = "molprobity_data.txt"

    self.data    = {} # individual values from molprobity, [0] is xray
    self.results = {} # mean and standard deviation of the respective values 
    self.volumes = []


  def get_volume(self, filename):

    exec_cute_able = self.bin_dir + "/calc-volume"
    
    args = [exec_cute_able, '-i', filename, '-method', '1' ]

    self.subp = subprocess.Popen([str(arg) for arg in args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.workingdir )

    # while not self.subp.is_done():
    #   time.sleep(1)

    output = self.subp.communicate()[0].split('\n') # 0 is stdout, 1 is stderr

    sum_volume = 0.0
    
    for line in output:
      if len(line) > 1 and line.split()[0] == 'ATOM':
        sum_volume += float(line[75:80])
    
    # print sum_volume
    return sum_volume


  def preprocessing(self, suffix=''):
    """create links and calc volume for input structure"""
    
    # create links to the low energy structure files:
    os.mkdir( self.pdbdir )
    # this is supposed to make sure that the xray structure is the first structure that is processed
    os.symlink( self.workingdir_file_path(self.initial_structure), os.path.join(self.pdbdir, '0AA0.pdb' ) )
    
    files = os.listdir( self.workingdir )
    files.sort()
    # print files
    for fn in files:
      if re.match ('.*low%s.*(pdb|PDB)' % suffix,fn):
        #print 'create link for %s' % fn
        os.symlink( self.workingdir_file_path(fn), os.path.join(self.pdbdir, fn) )
        
    self.volumes.append(self.get_volume(self.initial_structure))

    
  def run(self):
    """this couldn't be more obvious"""
    self.run_args( [self.pdbdir] )
    
  
  def postprocessing(self):
    """ read in stuff do the statistics """
    
    # this is what we're reading in:
    #pdbFileName:chains:residues:nucacids:resolution:rvalue:rfree:clashscore:clashscoreB<40:minresol:maxresol:n_samples:pct_rank:pct_rank40:cbeta>0.25:numCbeta:maxCbeta:medianCbeta:meanCbeta:rota<1%:numRota:ramaOutlier:ramaAllowed:ramaFavored:numRama:pct_badbonds:pct_badangles:MolProbityScore
    
      
    handle_in = open( self.workingdir + '/' + self.filename_stdout , 'r')
    no_structures = 0
    
    handle_in.readline() # discard header
    keys = handle_in.readline()[1:-1].split(':') # read names of the scores while avoiding the # at the beginning
    self.data = {}.fromkeys(keys)
    for key in self.data.keys(): # populate dict
      self.data[key] = []
    # read in the actual numbers
    
    filename_dict = {}
    for line in handle_in:
      filename_dict[line.split(':')[0]] = line.split(':')
    handle_in.close()  
    
    # print filename_dict.keys()
    filenames_list = sorted(filename_dict.keys())
    # print filenames_list
    
    for fn in filenames_list:
      i = 0
      for value in filename_dict[fn]: # for each parameter 
        try:
          self.data[keys[i]].append(float(value)) # add the value to the data list
        except ValueError:
          self.data[keys[i]].append(value)
        i+=1
    
    print self.data
    
    # clashscore
    # needs to be normalized: see Greg's email from 10/21/09
    # I think dividing by 100 is too much, 10 sounds more reasonable
    #self.data['clashscore'] = [ x/100 for x in self.data['clashscore']] # normalize
    self.results['clashscore'] = [ numpy.mean(self.data['clashscore']), numpy.std(self.data['clashscore']) ]
    
    # volume
    # self.volumes[0] = volume of xray structure
    self.data['nvol'] = [0.0] # xray has 0% volume change, new volume
    # subtract the volume of the xray from the volume of the new structure and calculate the percent change
    factor = 100 / self.volumes[0] # factor * (Vnew - Vxray) = change of volume in percent

    
    for pdb_fn in self.data['pdbFileName']:
      volume = self.get_volume(self.pdbdir + '/' + pdb_fn)
      self.volumes.append( volume )
      self.data['nvol'].append( factor * (self.volumes[0] - volume) ) # new - xray => +: worse packaging; -: better packaging  ## should we normalize here?
    
    # self.volumes.extend( [ (factor * (self.get_volume(self.pdbdir + '/' + fn) - self.volumes[0]))/100 for fn in self.data['pdbFileName'] ] ) # outer /100 is for normalization
    self.results['volume'] = [ numpy.mean(self.data['nvol'][1:]), numpy.std(self.data['nvol'][1:]) ] # exclude the xray structure
    # rotamer
    self.results['rotamer'] = [ numpy.mean(self.data['rota<1%']), numpy.std(self.data['rota<1%']) ]
    # cbeta
    self.results['cbeta'] = [ numpy.mean(self.data['cbeta>0.25']), numpy.std(self.data['cbeta>0.25']) ]
    # pct_badangles
    self.data['pct_badangles'] = [ x/100 for x in self.data['pct_badangles']] # normalize
    self.results['pct_badangles'] = [ numpy.mean(self.data['pct_badangles']), numpy.std(self.data['pct_badangles']) ]
    # rama not favored = numRama-ramaFavored
    self.list_rama_not_favored = [(a - b)/100 for a, b in zip(self.data['numRama'], self.data['ramaFavored'])]
    self.results['rama'] = [ numpy.mean( self.list_rama_not_favored ), numpy.std( self.list_rama_not_favored ) ]

    # finally remove pdb dir with links:
    if os.path.exists( self.pdbdir ):
      os.popen( "rm -rf %s" % self.pdbdir, "w")
      os.close()


  def print_results(self):
    print 'value mean sd'
    print 'clashscore %s %s'       % (self.results['clashscore'][0], self.results['clashscore'][1])
    print 'volume %s %s'           % (self.results['volume'][0], self.results['volume'][1])
    print 'rotamer %s %s'          % (self.results['rotamer'][0], self.results['rotamer'][1])
    print 'cbeta %s %s'            % (self.results['cbeta'][0], self.results['cbeta'][1])
    print 'pct_badangles %s %s'    % (self.results['pct_badangles'][0], self.results['pct_badangles'][1])
    print 'rama not favored %s %s' % (self.results['rama'][0], self.results['rama'][1])
    print '**************'
    print "structure clashscore volume rotamer cbeta pct_badangles rama"
    for i in range(0,len(self.data['clashscore'])):
      print '%04.i' % i, self.data['clashscore'][i], self.volumes[i+1], self.data['rota<1%'][i], self.data['cbeta>0.25'][i], self.data['pct_badangles'][i], self.list_rama_not_favored[i]


  def write_results(self):
    handle_out = open( self.workingdir + '/' + self.filename_results , 'w')
    handle_out.write( 'value mean sd\n')
    handle_out.write( 'clashscore %s %s\n'       % (self.results['clashscore'][0], self.results['clashscore'][1]) )    
    handle_out.write( 'volume %s %s\n'           % (self.results['volume'][0], self.results['volume'][1]) )
    handle_out.write( 'rotamer %s %s\n'          % (self.results['rotamer'][0], self.results['rotamer'][1]) )
    handle_out.write( 'cbeta %s %s\n'            % (self.results['cbeta'][0], self.results['cbeta'][1]) )    
    handle_out.write( 'pct_badangles %s %s\n'    % (self.results['pct_badangles'][0], self.results['pct_badangles'][1]) )    
    handle_out.write( 'rama not favored %s %s\n' % (self.results['rama'][0], self.results['rama'][1]) )
    handle_out.write('\n**************\n')
    handle_out.write("structure clashscore volume rotamer cbeta pct_badangles rama\n")
    for i in range(0,len(self.data['clashscore'])):
      handle_out.write('%04.i %s %s %s %s %s %s\n' % ( i, self.data['clashscore'][i], self.volumes[i+1], self.data['rota<1%'][i], self.data['cbeta>0.25'][i], self.data['pct_badangles'][i], self.list_rama_not_favored[i]) )
    handle_out.close()
  
  
  def plot_results(self,image_file=None):
    
    # for key in self.data.keys():
    #   print self.data[key]
    # print
    # for key in self.results.keys():
    #   print self.results[key]
    # print
    #   
    # print '--------'
    # print self.data
    # print '--------'
    
    s_data = [ self.data['nvol'],
               self.data['clashscore'],
               self.data['cbeta>0.25'],
               self.data['pct_badangles'],
               self.list_rama_not_favored ]
    
    
    label = [ 'Volume increase in %',
              'Clashes >4A per 100,000 atoms',
              'cbeta > 0.25A',
              'bondangles > 4sd',
              'rama not favored' ]
    
    fig = figure(figsize=(10,6))
    fig.canvas.set_window_title('Quality measures according to Molprobity')

    i = 151
    for values in s_data:
      axis = fig.add_subplot(i)
      subplots_adjust(left=0.1, right=0.99,bottom=0.1, top=0.9, wspace=0.9, hspace=0.2)

      bp = boxplot(values,widths=0.6)
      setp(bp['boxes'], color='black')
      
      axis.set_axisbelow(False)
      axis.yaxis.set_ticks_position('left')
      
      axis.set_ylabel(label[s_data.index(values)])
      if i-150 == int(numpy.ceil(float(len(s_data))/2.0)):
        axis.set_title('Quality measures according to Molprobity')
            
      plot( [numpy.average( bp['medians'][0].get_xdata())], [numpy.average(values)], color='r', marker='o', markeredgecolor='k' )
      plot( [numpy.average( bp['medians'][0].get_xdata())], [values[0]], color='g', marker='D' )

      boxplot(values,widths=0.6)
            
      i+=1
    
    # subplot(256)
    # boxplot(s_data,widths=0.6)
    
    if image_file == None:
      show()
    else:
      savefig(self.workingdir + '/' + image_file, dpi=300, orientation='landscape')
    
      

if __name__ == "__main__":

  if len(sys.argv) < 3:
    print 'usage: %s <path to pdbfiles> <name of initial pdb>' % sys.argv[0]
    sys.exit(1)

  obj = MolProbityAnalysis(ID=0,
                           bin_dir="/var/www/html/rosettaweb/backrub/bin/",
                           workingdir=sys.argv[1],
                           initial_structure=sys.argv[2])
  
  obj.preprocessing(suffix='_ms_0000')
  obj.run()
  while not obj.is_done():
    time.sleep(3)
  obj.postprocessing()
  # obj.write_results()
  obj.print_results()
  obj.plot_results('molprobity_plot')
  print "red dot: mean, blue diamond: value of xray structure"
  
  print 'DONE' 
  