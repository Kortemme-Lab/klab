#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-

########################################
# This class produces HTML code for 
# showing the 
# This is accessed by clicking on 'View individual files' from the finished job page
########################################

import sys, os
import cgi
import cgitb; cgitb.enable()
from string import join
import pickle
from rosettahtml import RosettaHTML
from rosettahelper import *
from RosettaProtocols import RosettaBinaries

class RosettaDataDir(RosettaHTML):

  
    def __init__(self, server_url, server_title, script_filename, contact_name, download_dir):
        super(RosettaDataDir, self).__init__(server_url, server_title, script_filename, contact_name, download_dir)
      
        self.jobid           = 'NA'
        self.content         = ''
        self.header          = ''
        self.html_refs       = ''
        self.legal_info      = ''  
      
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
  
    def _get_pdb_files(self, cryptID, subdir = "."):
        directory = os.path.join(self.download_dir, cryptID, subdir)
        list_files = os.listdir(directory)
        list_files.sort()
        return grep('.pdb',list_files)
    
    
    def PointMutation(self, cryptID, jobid, binary, pdb_filename):
    
        usingMini = RosettaBinaries[binary]['mini']  
        self.jobid = jobid
        individual_scores = ''
        
        if usingMini:
          self.header = '<h1 align="center">Job %s - Point Mutation (Rosetta 3)</h1>' % jobid
          individual_scores = '<li>Detailed scores for each residue: <a href="../downloads/%s/scores_residues.txt">scores_residues.txt</a></li>' % cryptID
        else:
          self.header = '<h1 align="center">Job %s - Point Mutation (Rosetta++)</h1>' % jobid
        
        self.html_refs = '<P>%(SmithKortemme:2008)s</P>' % self.refs
        
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
  
    def MultiplePointMutations(self, cryptID, jobid, binary, pdb_filename):
        # let's reuse the point mutation function since the output files are the same
        self.PointMutation( cryptID, jobid, binary, pdb_filename )
        # and overwrite the parts that don't apply
        usingMini = RosettaBinaries[binary]['mini']
        if usingMini:
          self.header = '<h1 align="center">Job %s - Multiple Point Mutations (Rosetta 3)</h1>' % jobid
        else:
          self.header = '<h1 align="center">Job %s - Multiple Point Mutations (Rosetta++)</h1>' % jobid
    
    def Ensemble(self, cryptID, jobid, binary, pdb_filename):
        # let's reuse the point mutation function since the output files are the same
        self.PointMutation( cryptID, jobid, binary, pdb_filename )
        # and overwrite the parts that don't apply
        usingMini = RosettaBinaries[binary]['mini']
        if usingMini:
          self.header = '<h1 align="center">Job %s - Backrub Ensemble (Rosetta 3)</h1>' % jobid
        else:
          self.header = '<h1 align="center">Job %s - Backrub Ensemble (Rosetta++)</h1>' % jobid
    
    def EnsembleDesign(self, cryptID, jobid, binary, pdb_filename):
        
        usingMini = RosettaBinaries[binary]['mini']
        self.jobid = jobid
        if usingMini:
          self.header = '<h1 align="center">Job %s - Backrub Ensemble Design (Rosetta 3)</h1>' % jobid
        else:
          self.header = '<h1 align="center">Job %s - Backrub Ensemble Design (Rosetta++)</h1>' % jobid
        
        self.html_refs = '<P>%(FriedlandEtAl:2009)s</P>' % self.refs
        
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
    
    def SequenceToleranceHK(self, cryptID, jobid, binary, pdb_filename):
    
        self.jobid = jobid
        self.header = '<h1 align="center">Job %s - Interface Sequence Tolerance Prediction (Rosetta++)</h1>' % jobid
        self.html_refs = '<P>%(HumphrisKortemme:2008)s</P>' % self.refs
        
        # individual boxplots
        list_files = os.listdir( self.download_dir+'/'+cryptID )
        list_files.sort()
    
        self.content = '''
          <p>
          Input files:
            <ul>
              <li>Input PDB file: <a href="../downloads/%s/%s">%s</a></li>''' % (cryptID, pdb_filename, pdb_filename)
              
        for br_resfile in grep('backrub_[0-9]+\.resfile',list_files):
            self.content += '''
              <li>Backrub premutations residue file: <a href="../downloads/%s/%s">%s</a></li>
                ''' % (cryptID, br_resfile, br_resfile)
                
        self.content += '''
            </ul>
          </p>
          Output files:
            <ul>
              <li><a href="../downloads/%(cryptID)s/tolerance_sequences.fasta">tolerance_sequences.fasta</a> - up to 10 best scoring sequences for each backrub structure</li>
              <li><a href="../downloads/%(cryptID)s/tolerance_pwm.txt">tolerance_pwm.txt</a> - Matrix with amino acid frequencies</li>
              <li><a href="../downloads/%(cryptID)s/tolerance_boxplot.png">tolerance_boxplot.png</a>, 
                  <a href="../downloads/%(cryptID)s/tolerance_boxplot.pdf">tolerance_boxplot.pdf</a> - Boxplots with the amino acid frequencies</li>
              <li> Boxplot for each position: <BR>
          ''' % vars()        
        for png_fn in grep('tolerance_boxplot_[A-Z][0-9]*\.png',list_files):
          self.content += '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href="../downloads/%s/%s">%s</a><br>' % ( cryptID, png_fn, png_fn )
        
        self.content += '''
              </li>
            </ul>
            Individual PDB files:<br>
                &nbsp;&nbsp;&nbsp; Structure file from the backrub run along with the structures of up to 10 best scoring designed sequences.
            <ul>'''
          
        for fn_pdb in self._get_pdb_files(cryptID):
          if fn_pdb != pdb_filename:
            self.content += '<li><a href="../downloads/%s/%s">%s</a>' % (cryptID, fn_pdb, fn_pdb)
    
        self.content += "</ul></p>"      

    def SequenceToleranceSK(self, cryptID, jobid, binary, pdb_filename):
    
        self.jobid = jobid
        if binary == "seqtolJMB":
          self.header = '<h1 align="center">Job %s - Interface Sequence Tolerance Prediction (Rosetta 3)</h1>' % jobid
          self.html_refs = '<P>%(SmithKortemme:2010)s</P>' % self.refs
        else:
          self.header = '<h1 align="center">Job %s - Interface Sequence Tolerance Prediction</h1>' % jobid
          self.html_refs = '<P>%(HumphrisKortemme:2008)s</P>' % self.refs
          self.content = '<p>The logic to create data directory is missing.</p>'
          return
      
        # individual boxplots
        list_files = os.listdir( self.download_dir+'/'+cryptID )
        list_files.sort()
    
        self.content = []
        self.content.append('''
          <p>
          Input files:
            <ul>
              <li>Input PDB file: <a href="../downloads/%s/%s">%s</a></li>''' % (cryptID, pdb_filename, pdb_filename))
              
        for br_resfile in grep('backrub_[0-9]+\.resfile',list_files):
            self.content.append('''<li>Backrub premutations residue file: <a href="../downloads/%(cryptID)s/%(br_resfile)s">%(br_resfile)s</a></li>''' % vars())
        
        for st_resfile in grep('seqtol_[0-9]+\.resfile',list_files):
            self.content.append('''<li>Sequence tolerance residue file: <a href="../downloads/%(cryptID)s/%(st_resfile)s">%(st_resfile)s</a></li>''' % vars())
            
        self.content.append('''
            </ul>
          </p>
          Output files:
            <ul>
                <li><a href="../downloads/%(cryptID)s/backrub/backrub_scores.dat">backrub_scores.dat</a> - Backrub scores</li> 
                <li><a href="../downloads/%(cryptID)s/tolerance_sequences.fasta">tolerance_sequences.fasta</a> - up to 10 best scoring sequences for each backrub structure</li>
                <li><a href="../downloads/%(cryptID)s/tolerance_seqrank.png">tolerance_seqrank.png</a>, 
                               <a href="../downloads/%(cryptID)s/tolerance_seqrank.pdf">tolerance_seqrank.pdf</a> - ranked table of amino acid types for each position</li>
                <li><a href="../downloads/%(cryptID)s/tolerance_motif.png">tolerance_motif.png</a> - Logo of the best scoring sequences</li>
              <li><a href="../downloads/%(cryptID)s/tolerance_pwm.txt">tolerance_pwm.txt</a> - Matrix with amino acid frequencies</li>
              <li><a href="../downloads/%(cryptID)s/tolerance_boxplot.png">tolerance_boxplot.png</a>, 
                  <a href="../downloads/%(cryptID)s/tolerance_boxplot.pdf">tolerance_boxplot.pdf</a> - Boxplots with the amino acid frequencies</li>
              <li> Boxplot for each position: <BR>''' % vars())
 
    
        for png_fn in grep('tolerance_boxplot_[A-Z][0-9]*\.png',list_files):
            self.content.append('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href="../downloads/%s/%s">%s</a><br>' % ( cryptID, png_fn, png_fn ))
        
        self.content.append('''
              </li>
            </ul>
            Individual PDB files: <br>
                &nbsp;&nbsp;&nbsp;"low" PDB files are the result of the backrub run, <br>
                &nbsp;&nbsp;&nbsp;"low_ms" PDB files contain the lowest scoring designed sequence based on this backrub run.
                <ul>''')
          
        for fn_pdb in self._get_pdb_files(cryptID, subdir="sequence_tolerance"):
          if fn_pdb != pdb_filename:
            self.content.append('<li><a href="../downloads/%(cryptID)s/%(fn_pdb)s">%(fn_pdb)s</a>' % vars())
    
        self.content.append("</ul></p>")
        self.content = join(self.content, "")    

    def _showLegalInfo(self):
        html = """<td style="border:1px solid black; padding:10px" bgcolor="#FFFFE0">
                    <p style="text-align:left; font-size: 10pt">
                      For questions, please read our <A href="../wiki/">documentation</A>, see the reference below, or contact <img src="../images/support_email.png" style="vertical-align:text-bottom;" height="15">.
                    </p>
                    <p>
                      If you are using these data please cite:                  
                    </p>
                    %s
                  </td>""" % self.html_refs
        return html      
  
      
