#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-

########################################
# This class produces HTML code for 
# showing the 
########################################

import sys, os
import cgi
import cgitb; cgitb.enable()
from string import join
import pickle
from rosettahtml import RosettaHTML
from rosettahelper import *

class RosettaDataDir(RosettaHTML):

  def __init__(self, server_url, server_title, script_filename, download_dir, contact_name='FLO'):
      self.server_url      = server_url
      self.server_title    = server_title
      self.script_filename = script_filename
      self.contact_name    = contact_name
      self.download_dir    = download_dir
      self.jobid           = 'NA'
      self.content         = ''
      self.header          = ''
      self.html_refs       = ''
      self.legal_info      = ''
      self.refs = { "Davis": 'Davis IW, Arendall III WB, Richardson DC, Richardson JS. <i>The Backrub Motion: How Protein Backbone Shrugs When a Sidechain Dances</i>,<br><a href="http://dx.doi.org/10.1016/j.str.2005.10.007" style="font-size: 10pt">Structure, Volume 14, Issue 2, 2 February 2006, Pages 265-274</a>',
                    "Smith": 'Smith CA, Kortemme T. <i>Backrub-Like Backbone Simulation Recapitulates Natural Protein Conformational Variability and Improves Mutant Side-Chain Prediction</i>,<br><a href="http://dx.doi.org/10.1016/j.jmb.2008.05.023" style="font-size: 10pt"> Journal of Molecular Biology, Volume 380, Issue 4, 18 July 2008, Pages 742-756 </a>',
                    "Humphris": 'Humphris EL, Kortemme T. <i>Prediction of Protein-Protein Interface Sequence Diversity using Flexible Backbone Computational Protein Design</i>,<br><a href="http://dx.doi.org/10.1016/j.str.2008.09.012" style="font-size: 10pt"> Structure, Volume 16, Issue 12, 12 December 2008, Pages 1777-1788</a>',
                    "Friedland": 'Friedland GD, Lakomek NA, Griesinger C, Meiler J, Kortemme T. <i>A Correspondence between Solution-State Dynamics of an Individual Protein and the Sequence and Conformational Diversity of its Family</i>,<br><a href="http://dx.doi.org/10.1371/journal.pcbi.1000393" style="font-size: 10pt"> PLoS Comput Biol. May;5(5):e1000393</a>',
                    "Smith_SP": 'Smith CA, Kortemme T. <i>Some Title</i>,<br><a href="http://someDOI" style="font-size: 10pt"> somewhere </a>',
                  }
   
      
  def main(self, text=''):
    
    if text != '':
      self.content = "<center>%s</center>" % text
    # if there is no reference, don't show the citation box
    if self.html_refs != '':
      self.legal_info = self._showLegalInfo()
    html = """
          <!-- *********************************************************
               * RosettaBackrub                                        *
               * Kortemme Lab, University of California, San Francisco *
               * Tanja Kortemme, Florian Lauck, 2009-2010              *
               ********************************************************* -->
          <html>
          <head>
              <title>%s - Data for Job %s</title>
              <link rel="STYLESHEET" type="text/css" href="../style.css">
              <style type="text/css">ul { list-style-type: none; }</style>
          </head>
          <body bgcolor="#ffffff">
          <center>
          <table border=0 width="700" cellpadding=0 cellspacing=0>

<!-- Header --> <tr> %s </tr>
<!-- Content --> <tr><td> %s %s </td></tr>
      <tr><td>&nbsp;&nbsp;&nbsp;</td></tr>
<!-- Legal Info --> <tr> %s </tr>
          <tr><td>&nbsp;&nbsp;&nbsp;</td></tr>
<!-- Footer --> <tr> %s </tr>

         </table>
         </center>
         </body>
         </html>\n""" % ( self.server_title, self.jobid,
                          self._showHeader(),
                          self.header, self.content,
                          self.legal_info,
                          self._showFooter() )

    return html
  
  def _get_pdb_files(self, cryptID):
    directory = self.download_dir+'/'+cryptID
    list_files = os.listdir(directory)
    list_files.sort()
    return grep('.pdb',list_files)
    
    
  def point_mutation(self, cryptID, jobid, mini, pdb_filename):
    
    self.jobid = jobid
    individual_scores = ''
    
    if mini:
      self.header = '<h1 align="center">Job %s - Point Mutation (mini)</h1>' % jobid
      individual_scores = '<li>Detailes scores for each residue: <a href="../downloads/%s/scores_residues.txt">scores_residues.txt</a></li>' % cryptID
    else:
      self.header = '<h1 align="center">Job %s - Point Mutation (classic)</h1>' % jobid
    
    self.html_refs = '<P>%(Smith)s</P>' % self.refs
    
    self.content = '''
    <p>
    Input files:
      <ul>
        <li>Input PDB file: <a href="../downloads/%s/%s">%s</a></li>
        <li>Rosetta Residue file: <a href="../downloads/%s/input.resfile">input.resfile</a></li>
      </ul>
    </p>
    <p>
    Output files:
      <ul>
        <!-- li><a href="../downloads/%s/score.sc">score.sc</a></li -->
        <li>Total score for each structure: <a href="../downloads/%s/scores_overall.txt">scores_overall.txt</a></li>
        <li>Detailed scores for each structure: <a href="../downloads/%s/scores_detailed.txt">scores_detailed.txt</a></li>
        %s
      </ul>
    Individual PDB files:
      <ul>
    ''' % ( cryptID, pdb_filename, pdb_filename, cryptID, cryptID, cryptID, cryptID, individual_scores )
    
    for fn_pdb in self._get_pdb_files(cryptID):
      if fn_pdb != pdb_filename:
        self.content += '<li><a href="../downloads/%s/%s">%s</a>' % (cryptID, fn_pdb, fn_pdb)
    
    self.content += "</ul></p>"
  
  def multiple_mutation(self, cryptID, jobid, mini, pdb_filename):
    # let's reuse the point mutation function since the output files are the same
    self.point_mutation( cryptID, jobid, mini, pdb_filename )
    # and overwrite the parts that don't apply
    if mini:
      self.header = '<h1 align="center">Job %s - Multiple Point Mutations (mini)</h1>' % jobid
    else:
      self.header = '<h1 align="center">Job %s - Multiple Point Mutations (classic)</h1>' % jobid
    
  def no_mutation(self, cryptID, jobid, mini, pdb_filename):
    # let's reuse the point mutation function since the output files are the same
    self.point_mutation( cryptID, jobid, mini, pdb_filename )
    # and overwrite the parts that don't apply
    if mini:
      self.header = '<h1 align="center">Job %s - Backrub Ensemble (mini)</h1>' % jobid
    else:
      self.header = '<h1 align="center">Job %s - Backrub Ensemble (classic)</h1>' % jobid
    
  def ensemble_design(self, cryptID, jobid, mini, pdb_filename):
    
    self.jobid = jobid
    if mini:
      self.header = '<h1 align="center">Job %s - Backrub Ensemble Design (mini)</h1>' % jobid
    else:
      self.header = '<h1 align="center">Job %s - Backrub Ensemble Design (classic)</h1>' % jobid
    
    self.html_refs = '<P>%(Friedland)s</P>' % self.refs
    
    self.content = '''
    <p>
    Input files:
      <ul>
        <li>Input PDB file: <a href="../downloads/%s/%s">%s</a></li>
      </ul>
    </p>
    Output files:
      <ul>
        <li>Core residues: <a href="../downloads/%s/core.txt">core.txt</a></li>
        <li>Amino Acid Frequency of core residues: <a href="../downloads/%s/seq_pop_core.txt">seq_pop_core.txt</a></li>
        <li>Designed sequences of core residues: <a href="../downloads/%s/designs_core.fasta">designs_core.fasta</a></li>
        <li>Sequence profile of core residues: <a href="../downloads/%s/logo_core.png">logo_core.png</a></li>
        <li>Amino acid frequencies of all residues: <a href="../downloads/%s/seq_pop.txt">seq_pop.txt</a></li>
        <li>Designed sequences of all residues: <a href="../downloads/%s/designs.fasta">designs.fasta</a></li>
        <li>Sequence profile of all residues: <a href="../downloads/%s/logo.png">logo.png</a></li>
        <li>C&alpha; atom distance matrix: <a href="../downloads/%s/ca_dist_difference_matrix.dat">ca_dist_difference_matrix.dat</a></li>
        <li>C&alpha; atom distance matrix: <a href="../downloads/%s/ca_dist_difference_1D_plot.png">ca_dist_difference_1D_plot.png</a></li>
        <li>C&alpha; atom distance matrix: <a href="../downloads/%s/ca_dist_difference_2D_plot.png">ca_dist_difference_2D_plot.png</a></li>
      </ul>
    PDB files:
      <ul>
        <li>C&alpha; distances mapped onto the input structure (b-factor values): <a href="../downloads/%s/ca_dist_difference_bfactors.pdb">ca_dist_difference_bfactors.pdb</a></li>
        <li>Structures of the designed ensemble: <a href="../downloads/%s/ensemble.pdb">ensemble.pdb</a></li>
      <ul>
    ''' % ( cryptID, pdb_filename, pdb_filename, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID )
    
    
    
  def sequence_tolerance(self, cryptID, jobid, mini, pdb_filename):
    
    self.jobid = jobid
    if mini:
      self.header = '<h1 align="center">Job %s - Backrub Ensemble Design (mini)</h1>' % jobid
      self.html_refs = '<P>%(Smith_SP)s</P>' % self.refs
    else:
      self.header = '<h1 align="center">Job %s - Backrub Ensemble Design (classic)</h1>' % jobid
      self.html_refs = '<P>%(Humphris)s</P>' % self.refs
    
    self.content = '''
      <p>
      Input files:
        <ul>
          <li>Input PDB file: <a href="../downloads/%s/%s">%s</a></li>
          <li>Rosetta Residue file: <a href="../downloads/%s/backrub_%s.resfile">backrub_%s.resfile</a></li>
        </ul>
      </p>
      Output files:
        <ul>
          <li><a href="../downloads/%s/plasticity_sequences.fasta">plasticity_sequences.fasta</a> - 10 best scoring sequences for each backrub structure</li>
          <!-- li><a href="../downloads/%s/plasticity_motif.png">plasticity_motif.png</a> - Motif of the best scoring sequences</li -->
          <li><a href="../downloads/%s/plasticity_pwm.txt">plasticity_pwm.txt</a> - Matrix with amino acid frequencies</li>
          <li><a href="../downloads/%s/plasticity_boxplot.png">plasticity_boxplot.png</a>, 
              <a href="../downloads/%s/plasticity_boxplot.pdf">plasticity_boxplot.pdf</a> - Boxplots with the amino acid frequencies</li>
      ''' % ( cryptID, pdb_filename, pdb_filename, cryptID, jobid, jobid, cryptID, cryptID, cryptID, cryptID, cryptID )

      # <li><a href="../downloads/%s/backrub_scores.dat">backrub_scores.dat</a> - Detailed scores for the backrub structures</li> # this had to go since the molprobity analysis was taken out.
    
    # individual boxplots
    list_files = os.listdir( self.download_dir+'/'+cryptID )
    list_files.sort()

    self.content += '<li> Boxplot for each position: <BR>'

    for png_fn in grep('plasticity_boxplot_[A-Z][0-9]*\.png',list_files):
      self.content += '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href="../downloads/%s/%s">%s</a><br>' % ( cryptID, png_fn, png_fn )
    
    self.content += '</li></ul>'
    
    if mini: 
      self.content += '''Individual PDB files: <br>
                          &nbsp;&nbsp;&nbsp;"low" PDB files are the result of the backrub run, <br>
                          &nbsp;&nbsp;&nbsp;"low_ms" PDB files contain the lowest scoring designed sequence based on this backrub run.
                        <ul>'''
    else:
      self.content += '''Individual PDB files:<br>
                          &nbsp;&nbsp;&nbsp; Structure file from the backrub run along with the structures of the best scoring designed sequences.
                        <ul>'''
      
    for fn_pdb in self._get_pdb_files(cryptID):
      if fn_pdb != pdb_filename:
        self.content += '<li><a href="../downloads/%s/%s">%s</a>' % (cryptID, fn_pdb, fn_pdb)

    self.content += "</ul></p>"      


    # def upload_mutation(self, cryptID, jobid, mini):
    # 
    #   self.content = 'Upload Mutation'
    #   self.html_refs = '<P>%(Smith)s</P>' % self.refs


  def _showLegalInfo(self):
      html = """<td style="border:1px solid black; padding:10px" bgcolor="#FFFFE0">
                  <p style="text-align:left; font-size: 10pt">
                    For questions, please read our <A href="../wiki/">documentation</A>, see the reference below, or contact <img src="../images/support_email.png" height="15">
                  </p>
                  <p>
                    If you are using this data please cite:                  
                  </p>
                  %s
                </td>""" % self.html_refs
      return html      
      
      
