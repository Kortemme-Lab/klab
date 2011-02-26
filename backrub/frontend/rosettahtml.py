#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-

########################################
# This class produces HTML code
########################################

#

import sys, os
import cgi
import cgitb; cgitb.enable()
from string import join
import pickle
import gzip

from rwebhelper import *

class RosettaHTML:

    server = {}
    
    def __init__(self, server_url, server_title, script_filename, download_dir, 
                  username='', comment= '', warning='', contact_name='FLO'):
        self.server_url      = server_url
        self.server_title    = server_title
        self.script_filename = script_filename
        self.username        = username
        self.comment         = comment
        self.warning         = warning
        self.contact_name    = contact_name
        self.download_dir    = download_dir
        self.lowest_structs  = []
        self.html_refs       = ''
        self.protocolForms = (
             self.submitOnePointMutation,
             self.submitMultiplePointMutations,
             self.submitBRConformationalEnsemble,
             self.submitBREnsembleDesign,
             self.submitSeqTolHK,
             self.submitSeqTolSK,
            )
    
        #self.server = { 'Structure Prediction Backrub': 'http://%s/backrub' % self.server_url,
                        #'Interface Alanine Scanning' : 'http://%s/alascan/' % self.server_url,
                        #'more server soon' : 'http://kortemmelab.ucsf.edu/' }
                        # THIS gets to complicated
        tooltip_parameter = "offsetx=[-90] offsety=[20] singleclickstop=[on] cssbody=[tooltip] cssheader=[tth] delay=[250]"
        self.tooltips = { 
                        "tt_empty":         "header=[] body=[] %s" % tooltip_parameter,
                        "tt_general":       "header=[General Settings] body=[These settings are common for all applications.] %s" % tooltip_parameter,
                        "tt_specific":      "header=[Application Specific Settings] body=[These settings are dependent on the applications. If you are not sure use the recommended values. For a more detailed explanation of the parameters and their influence on simulation results see the reference below.] %s" % tooltip_parameter,
                        "tt_JobName":       "header=[Name for your job] body=[Enter a name that helps you identify your job later on the job queue page.] %s" % tooltip_parameter,
                        "tt_Structure":     "header=[Structure File] body=[Enter the path to a protein structure file in PDB format. For NMR structures only the first model in the file will be considered.] %s" % tooltip_parameter,
                        "tt_StructureURL":  "header=[URL to Structure File] body=[Enter the path to a protein structure file in PDB format. For NMR structures only the first model in the file will be considered.] %s" % tooltip_parameter,
                        "tt_PDBID":         "header=[PDB identifier] body=[Enter the 4-digit PDB identifier of the structure file. For NMR structures only the first model in the file will be considered.] %s" % tooltip_parameter,
                        "tt_RVersion":      "header=[Rosetta Version] body=[Choose the version of Rosetta, either Rosetta 2 (\'classic\') or the new Rosetta 3 (\'mini\'). Some applications only work with one version.] %s" % tooltip_parameter,
                        "tt_NStruct":       "header=[Number of Structures] body=[Number of generated structures or size of ensemble. We recommend to create 10 structures at a time.] %s" % tooltip_parameter,
                        "tt_ROutput":       "header=[Rosetta output] body=[If checked, the raw output of the Rosetta run is stored. Does not apply to all applications.] %s" % tooltip_parameter,
                        "tt_SelApp":        "header=[Select Application] body=[Click to choose one of the applications. Each application will give you a short explanation and a set of parameters that can be adjusted.] %s" % tooltip_parameter,
                        "tt_ChainId":       "header=[Chain ID] body=[The chain in which the residue is located.] %s" % tooltip_parameter,
                        "tt_ResId":         "header=[Residue Number] body=[The position (residue number according to the PDB file) that is going to be mutated.] %s" % tooltip_parameter,
                        "tt_NewAA":         "header=[New Amino Acid] body=[The Amino Acid to which the position is going to be mutated.] %s" % tooltip_parameter,
                        "tt_Radius":        "header=[Radius] body=[This radius determines the area around the mutation that is subject to backrub flexible backbone modeling. For detailed information see the referenced paper.] %s" % tooltip_parameter,
                        "tt_Temp":          "header=[Temperature] body=[at which backrub is carried out.] %s" % tooltip_parameter,
                        "tt_NSeq":          "header=[Number of Sequences] body=[The number of designed sequences for each ensemble structure.] %s" % tooltip_parameter,
                        "tt_SegLength":     "header=[Maximal segment length for backrub] body=[Limit the length of the segment to which the backrub move is applied to. (3-12)] %s" % tooltip_parameter,
                        "tt_error":         "header=[Rosetta Error</b></font><br>Rosetta (classic and mini) fail for some PDB files that have inconsistent residue numbering or miss residues. If an error occures for your structure please check the correctness of the PDB file.] %s" % tooltip_parameter,
                        "tt_seqtol_partner":"header=[Partner] body=[Define the two chains that form the protein-protein interface. For example: Partner 1: A; Partner 2: B] %s" % tooltip_parameter,
                        "tt_seqtol_SK_partner":"header=[Partner] body=[todo: Define the chain(s) that form the protein-protein interface. For example: Partner 1: A; Partner 2: B] %s" % tooltip_parameter,
                        "tt_seqtol_SK_weighting":"header=[Score reweighting] body=[todo: Define the intramolecular energies / self energy (e.g. k<sub>A</sub>) and the intermolecular / interaction energies (e.g. k<sub>AB</sub>).] %s" % tooltip_parameter,
                        "tt_seqtol_SK_Boltzmann":"header=[Boltzmann Factor] body=[todo: Define the Boltzmann factor kT. If the cited value is chosen then kT will be set as (0.228 + n * 0.021) where n is the number of valid premutated residues.] %s" % tooltip_parameter,
                        "tt_seqtol_list":   "header=[List] body=[List of residue-IDs of <b>Chain 2</b> that are subject to mutations. Enter residue-IDs seperated by a space.] %s" % tooltip_parameter,
                        "tt_seqtol_radius": "header=[Radius] body=[Defines the size of the interface. A residue is considered to be part of the interface if at least one of its atoms is within a sphere of radius r from any atom of the other chain.] %s" % tooltip_parameter,
                        "tt_seqtol_weights":"header=[Weights] body=[Describes how much the algorithm emphazises the energetic terms of this entity. The default of 1,1,2 emphasizes the energetic contributions of the interface. The interface is weighted with 2, while the energies of partner 1 and partner 2 are weighted with 1, respectively.] %s" % tooltip_parameter,
                        "tt_seqtol_design": "header=[Residues for design] body=[Rosetta is going to substitute these residues in order to find energetically stable sequences.] %s" % tooltip_parameter,
                        "tt_seqtol_premutated": "header=[Residues for design] body=[todo:] %s" % tooltip_parameter,
                        "tt_click":         "body=[Click on the link to read the description.] %s" % tooltip_parameter,
                        "ROSETTAWEB_SK_RecommendedNumStructures":   ROSETTAWEB_SK_RecommendedNumStructures,
                        }
        
        self.refs = { "Davis": 'Davis IW, Arendall III WB, Richardson DC, Richardson JS. <i>The Backrub Motion: How Protein Backbone Shrugs When a Sidechain Dances</i>,<br><a href="http://dx.doi.org/10.1016/j.str.2005.10.007" style="font-size: 10pt">Structure, Volume 14, Issue 2, 2 February 2006, Pages 265-274</a>',
                      "Smith": 'Smith CA, Kortemme T. <i>Backrub-Like Backbone Simulation Recapitulates Natural Protein Conformational Variability and Improves Mutant Side-Chain Prediction</i>,<br><a href="http://dx.doi.org/10.1016/j.jmb.2008.05.023" style="font-size: 10pt"> Journal of Molecular Biology, Volume 380, Issue 4, 18 July 2008, Pages 742-756 </a>',
                      "Humphris": 'Humphris EL, Kortemme T. <i>Prediction of Protein-Protein Interface Sequence Diversity using Flexible Backbone Computational Protein Design</i>,<br><a href="http://dx.doi.org/10.1016/j.str.2008.09.012" style="font-size: 10pt"> Structure, Volume 16, Issue 12, 12 December 2008, Pages 1777-1788</a>',
                      "Friedland": 'Friedland GD, Lakomek NA, Griesinger C, Meiler J, Kortemme T. <i>A Correspondence between Solution-State Dynamics of an Individual Protein and the Sequence and Conformational Diversity of its Family</i>,<br><a href="http://dx.doi.org/10.1371/journal.pcbi.1000393" style="font-size: 10pt"> PLoS Comput Biol. May;5(5):e1000393</a>',
                      "Lauck": 'Lauck F, Smith CA, Friedland GD, Humphris EL, Kortemme T. <i>RosettaBackrub - A web server for flexible backbone protein structure modeling and design.</i>,<br><a href="http://dx.doi.org/10.1093/nar/gkq369" style="font-size: 10pt">Nucleic Acids Res. 38:W569-W575</a>',
                      "Smith2": 'Smith CA, Kortemme T. <i>Structure-Based Prediction of the Peptide Sequence Space Recognized by Natural and Synthetic PDZ Domains.</i><br><a href="http://dx.doi.org/10.1016/j.jmb.2008.05.023" style="font-size: 10pt">Journal of Molecular Biology, Volume 402, Issue 2, 17 September 2010, Pages 460-474</a>',
                      "3": '<i></i>,<br><a href="" style="font-size: 10pt"> </a>',
                      "4": '<i></i>,<br><a href="" style="font-size: 10pt"> </a>',
                      "5": '<i></i>,<br><a href="" style="font-size: 10pt"> </a>',
                      "6": '<i></i>,<br><a href="" style="font-size: 10pt"> </a>',
                      "7": '<i></i>,<br><a href="" style="font-size: 10pt"> </a>',
        }
        

        
        
        

    def setUsername(self, username):
        self.username = username

    def main(self, CONTENT='This server is made of awesome sauce.', site='', query='' ):
        html = """
            <!-- *********************************************************
                 * RosettaBackrub                                        *
                 * Kortemme Lab, University of California, San Francisco *
                 * Tanja Kortemme, Florian Lauck, 2009-2010              *
                 ********************************************************* -->
            <html>
            <head>
                <title>%s - %s</title>
                <META name="description" content="RosettaBackrub a webserver for flexible backbone modeling">
                <META name="keywords" content="RosettaBackrub RosettaFlexibleBackbone Rosetta Kortemme protein structure modeling prediction backrub flexible backbone design point mutation">
                
                <link rel="STYLESHEET" type="text/css" href="../style.css">
                
                <script src="/javascripts/prototype.js" type="text/javascript"></script>
                <script src="/javascripts/scriptaculous.js" type="text/javascript"></script>
                <script src="/javascripts/niftycube.js" type="text/javascript"></script>
                <script src="/javascripts/boxover.js" type="text/javascript"></script>
                <script src="/jmol/Jmol.js" type="text/javascript"></script>
                """ % (self.server_title, site)
        
        # Embed the Python constants into the Javascript
        html += """<script type="text/javascript">//<![CDATA[
                        const SK_max_seqtol_chains = %d;
                        const SK_InitialBoltzmann = %f;
                        const SK_BoltzmannIncrease = %f;
                        const SK_MaxMutations = %d;
                        const SK_MaxPremutations = %d;
                        const RecommendedNumStructures = %d;
                        const RecommendedNumStructuresSeqTolSK = %d;
                     //]]></script>""" % (ROSETTAWEB_max_seqtol_SK_chains, ROSETTAWEB_SK_InitialBoltzmann, ROSETTAWEB_SK_BoltzmannIncrease, ROSETTAWEB_SK_MaxMutations, ROSETTAWEB_SK_MaxPremutations, ROSETTAWEB_SK_RecommendedNumStructures, ROSETTAWEB_SK_RecommendedNumStructuresSeqTolSK)
                
                    
        html += """        <script src="/backrub/jscripts.js" type="text/javascript"></script>
            </head>

            <body bgcolor="#ffffff" onload="startup( \'%s\' );">
            <center>
            <NOSCRIPT>
              <font style="color:red; font-weight:bold;">This page uses Javascript. Your browser either
              doesn't support Javascript or you have it turned off.
              To see this page as it is meant to appear please use
              a Javascript enabled browser.</font>
            </NOSCRIPT>
            <table border=0 width="700" cellpadding=0 cellspacing=0>

<!-- Header --> <tr> %s </tr>

<!-- Warning --> <tr> %s </tr>

<!-- Login Status --> <tr> %s </tr>

<!-- Menu --> <tr> %s </tr>
        <tr><td>&nbsp;&nbsp;&nbsp;</td></tr>
<!-- Content --> <tr> %s </tr>
        <tr><td>&nbsp;&nbsp;&nbsp;</td></tr>
<!-- Legal Info --> <tr> %s </tr>
            <tr><td>&nbsp;&nbsp;&nbsp;</td></tr>
<!-- Footer --> <tr> %s </tr>

           </table>
           </center>
           </body>
           </html>\n""" % ( query,
                            self._showHeader(),
                            self._showWarning(),
                            self._showLoginStatus(),
                            self._showMenu(),
                            CONTENT,
                            self._showLegalInfo(),
                            self._showFooter() )

        return html

##############################################
# The following functions are called by main #
##############################################

    def _showHeader(self):
        html = '''<td align=center style="border-bottom:1px solid gray;"> 
                    <A href="../"><img src="../images/header.png" border="0" usemap="#links"></A> 
                  </td>
                  '''
        return html

    def _showLoginStatus(self):
        """shows a little field with the username if logged in """
        html = '<td align="right">[&nbsp;Other Services: <A class="nav" style="color:green;" href="/alascan">Alanine Scanning</A>&nbsp;] '
        if self.username != '':
            html += '<br><small>[ <font color=green>%s</font> | <a href="%s?query=logout"><small>Logout</small></a> ]</small></td>' % ( self.username, self.script_filename )
        else:
            html += '<br><small>[&nbsp;<font color=red>not logged in</font>&nbsp;]</small></td>' 
        return html

    def _showWarning(self):
        html = ''
        if self.warning != '':
            html += '''<td align="center">
                            <table width="500"><tr><td align="center" style="padding-left:20px; padding-right:20px; padding-top:10px; padding-bottom:10px; border-color:red; border-style:dashed; border-width:2px;">
                                <font color="black" >%s</font></td></tr>
                            </table>
                     </td></tr><tr>''' % self.warning #style="text-decoration:blink;"
            #html += '<tr> <td align="center"> </td></tr>'

        if self.comment != '':
            html += '''<td align="center" style="padding:10px;">
                                <table width="500"><tr><td align="center" style="padding-left:20px; padding-right:20px; padding-top:10px; padding-bottom:10px; padding-left:10px; border-color:orange; border-style:dashed; border-width:2px;">
                                    <font color="red">%s</font></td></tr>
                                </table>
                      </td>''' % self.comment
        return html

    def _showMenu(self):
        html = """
                <tr><td align=center>
                    [&nbsp;<A class="nav" href="%s?query=index" >Home</A>&nbsp;] &nbsp;&nbsp;&nbsp;
                    [&nbsp;<A class="nav" href="../wiki/" target="_blank">Documentation</A>&nbsp;] &nbsp;&nbsp;&nbsp;
                    [&nbsp;<A class="nav" href="%s?query=register">Register</A>&nbsp;]
                </td></tr>
                <tr><td align=center>""" % (self.script_filename,self.script_filename)
        
        if self.username != '':
            html += """
                    [&nbsp;<A class="nav" href="%s?query=submit">Submit</A>&nbsp;] &nbsp;&nbsp;&nbsp;
                    [&nbsp;<A class="nav" href="%s?query=queue">Queue</A>&nbsp;] &nbsp;&nbsp;&nbsp;""" % (self.script_filename,self.script_filename)
            if self.username != "guest":
                html += """[&nbsp;<A class="nav" href="%s?query=update">My Account</A>&nbsp;]""" % (self.script_filename)

        
        # else:
        #     html += """
        #               [&nbsp;<A class="nav" href="%s?query=login">Login</A>&nbsp;] &nbsp;&nbsp;&nbsp;
        #               [&nbsp;<A class="nav" href="%s?query=register">Register</A>&nbsp;]""" % (self.script_filename,self.script_filename)
        html += "\n</td></tr>"

        return html

    def _showLegalInfo(self):
        html = """<td style="border:1px solid black; padding:10px" bgcolor="#FFFFE0">
                    <p style="text-align:left; font-size: 10pt">
                      For questions, please read our <A href="../wiki/">documentation</A>, see the reference below, or contact <img src="../images/support_email.png" height="15">
                    </p>
                    %s
                  </td>""" % self.html_refs
        return html

    def _showFooter(self):
        SSL = ''
        if self.server_url == 'kortemmelab.ucsf.edu':
          SSL = '''
          <script language="javascript" src="https://seal.entrust.net/seal.js?domain=kortemmelab.ucsf.edu&img=16"></script>
          <a href="http://www.entrust.net">SSL</a>
          <script language="javascript" type="text/javascript">goEntrust();</script>
          '''
      
      
        html = """<td align=center style="border-top:1px solid gray; ">
                 <table width="720" style="border-width:0pt">
                    <tr>
                    <td align="left">
                    "RosettaBackrub" is available for NON-COMMERCIAL USE ONLY at this time. 
                    [&nbsp;<A class="nav" href="/backrub/wiki/TermsOfService" >Terms of Service</A>&nbsp;]<br>
                    <font style="font-size: 9pt">Copyright &copy; 2009 Tanja Kortemme, Florian Lauck and the Regents of the University of California San Francisco</font>
                    </td>
                    <td align="center">
                    %s
                    </td>
                    </tr>
                 </table></td>""" % (SSL)
        return html
# <td align="center"><img src="../images/ucsf_only_tiny.png" width="65%%" height="65%%" alt="UCSF" border=0></td>

##############################################
# The following functions are accessed from  #
# outside and produce the HTML content by    #
# main                                       #
##############################################

###############################################################################################
# index()                                                                                     #
###############################################################################################

    def index(self, message='', username='', login_disabled=False):
        return self.login(message=message, username=username, login_disabled=login_disabled)

###############################################################################################
# submit() and the submission forms
###############################################################################################

    def submit(self, jobname='', error='', task=None, UploadedPDB='', StoredPDB='', listOfChains = [] ):
          # this function uses javascript functions from jscript.js
            # if you change the application tabler here, please make sure to change jscript.js accordingly
            # calling the function with parameters will load those into the form. #not implemented yet

        if error != '':
            error = '''<div align="center" style="width:300pt; background:lightgrey; margin:15pt; padding:15px; border-color:black; border-style:solid; border-width:2px;">
                          Your job could not be submitted:<br><font style="color:red;"><b>%s</b></font><br>
                          <a href="https://kortemmelab.ucsf.edu/backrub/wiki/Error#Errors_during_submission" target="_blank">More Information</a>. <a HREF="javascript:history.go(-1)">Return</a> to the form. 
                       </div>''' % error           
            
        self.tooltips.update({'username':self.username, 'jobname':jobname, 'script':self.script_filename, 'error':error})
        
        # <li id="ab1">
        #   [ <A href="/alascan/" class="nav" target="_blank">Interface Alanine Scanning</A> ]<br><center><small>opens in a new window</small></center>
        # </li>
        
        self.html_refs = '''<P>%(Lauck)s</P>
                         ''' % self.refs
                
        postscripts = ""
        html = '''<td align="center">
    <H1 class="title">Submit a new job</H1>
    %(error)s
<!-- Start Submit Form -->
    <FORM NAME="submitform" method="POST" onsubmit="return ValidateForm();" enctype="multipart/form-data">

      <table border=0 cellpadding=0 cellspacing=0>
        <colgroup>
          <col width="230">
          <col width="500">
        </colgroup>
        <tr>
<!-- left column = menu -->
          <td id="columnLeft" align="right" style="vertical-align:top; margin:0px;">
          <ul id="about">
            <li id="ab2">
              <A href="javascript:void(0)" class="nav" onclick="showMenu('1'); "><img src="../images/qm_s.png" border="0" title="%(tt_click)s"> Point Mutation</A><br>
              <font style="font-size:8pt">[ <a href="http://dx.doi.org/10.1016/j.jmb.2008.05.023" style="font-size: 8pt">Smith and Kortemme, 2008</a> ]</font>            
              <p id="menu_1" style="text-align:left; margin:0px;">
                  <table style="border:0px; padding:0px; margin:0px;">
                  <tr><td width="30" style="text-align:right;">&#8680;</td><td><a href="javascript:void(0)" onclick="changeApplication('1','1'); ">One mutation</a></td></tr>
                  <tr><td width="30" style="text-align:right;">&#8680;</td><td><a href="javascript:void(0)" onclick="changeApplication('1','2'); ">Multiple mutations</a></td></tr>
                  <!-- tr><td width="10" style="text-align:right;">&#8680;</td><td><a href="javascript:void(0)" onclick="changeApplication('1','3'); ">Upload List</td></tr -->
                  </table>
              </p>
            </li>
            <li id="ab3">
              <A href="javascript:void(0)" class="nav" onclick="showMenu('2'); "><img src="../images/qm_s.png" border="0" title="%(tt_click)s"> Backrub Ensembles</A>
              <p id="menu_2" style="text-align:right; margin:0px;">
                  <table style="border:0px; padding:0px; margin:0px;">
                  <tr><td width="30" style="text-align:right;">&#8680;</td>
                      <td><a href="javascript:void(0)" onclick="changeApplication('2','1'); ">
                          <font style="font-size:10pt">Backrub Conformational Ensemble</font></a><br>
                          <font style="font-size:8pt">[ <a href="http://dx.doi.org/10.1016/j.jmb.2008.05.023" style="font-size: 8pt">Smith and Kortemme, 2008</a> ]</font>
                      </td></tr>
                  <tr><td width="30" style="text-align:right;">&#8680;</td>
                      <td><a href="javascript:void(0)" onclick="changeApplication('2','2'); ">
                          <font style="font-size:10pt">Backrub Ensemble Design</font></a><br>
                          <font style="font-size:8pt">[ <a href="http://dx.doi.org/10.1371/journal.pcbi.1000393" style="font-size: 8pt">Friedland et. al., 2008</a> ]</font>
                      </td></tr>
                  </table>
              </p>
            </li>
            <li id="ab4">
              <A href="javascript:void(0)" class="nav" onclick="showMenu('3');"><img src="../images/qm_s.png" border="0" title="%(tt_click)s"> Interface / Fold Sequence Tolerance</A>
              
              <p id="menu_3" style="text-align:right; margin:0px;">
                  <table style="border:0px; padding:0px; margin:0px;">
                  <tr><td width="30" style="text-align:right;">&#8680;</td>
                      <td><a href="javascript:void(0)" onclick="changeApplication('3','1'); ">
                          <font style="font-size:10pt">todo: Title 1</font></a><br>
                          <font style="font-size:8pt">[ <a href="http://dx.doi.org/10.1016/j.str.2008.09.012" style="font-size: 8pt">Humphris and Kortemme, 2008</a> ]</font>
                      </td></tr>
                  <tr><td width="30" style="text-align:right;">&#8680;</td>
                      <td><a href="javascript:void(0)" onclick="subtask = 0; changeApplication('3','2'); ">
                          <font style="font-size:10pt">todo: Title 2</font></a><br>
                          <font style="font-size:8pt">[ <a href="http://dx.doi.org/10.1016/j.jmb.2010.07.032" style="font-size: 8pt">Smith and Kortemme, 2010</a> ]</font>
                      </td></tr>
                  </table>
              </p>
            </li>
          </ul>
          </td>
<!-- end left column -->
<!-- right column -->
          <td id="columnRight" align="center" style="vertical-align:top; padding:0px; margin:0px; height:240px; text-align:center;">
          <div id="box">
          <!-- pictures for the different applications -->
            <p id="pic1" style="display:none; text-align:center;">
              <img src="../images/logo1.png" width="85%%" alt="logo1" border=0>
            </p>

            <p id="pic2" style="display:none; text-align:center;">
              <img src="../images/logo2.png" width="85%%" alt="logo2" border=0>
            </p>
            
            <p id="pic3" style="display:none; text-align:center;">
              <img src="../images/logo3.png" width="85%%" alt="logo3" border=0>
            </p>

          <!-- end pictures -->
          <!-- description -->
            <p id="text0" style="text-align:justify;">
              Choose one of the applications on the left. Each application will give you a short explanation and a set of parameters that can be adjusted.<br><br>
              A <a href="../wiki/Tutorial">tutorial</a> on how to submit a job can be found in the <a href="../wiki">documentation</a>. For a brief explanation of each parameter move your mouse to the question mark symbol. The button "Check form" can be used to highlight fields with invalid entries in red; this is also shown when "Submit" is clicked.
            </p>
          
            <div id="text1" style="display:none; opacity:0.0; text-align:justify;"> 
                This function utilizes the backrub protocol implemented in Rosetta and applies it to the neighborhood of a mutated amino acid residue to model conformational changes in this region.
                There are two options.
                <dl style="text-align:left;">
                    <dt><b>One Mutation</b></dt><dd>
                        A single amino acid residue will be substituted and the neighboring residues within a radius of 6&#197; of the mutated residues 
                        will be allowed to change their side-chain conformations (\"repacked\"). 
                        The method, choice of parameters and benchmarking are described in [<a href="#ref1">1</a>].</dd>
                    <dt><b>Multiple Mutations</b></dt><dd>Up to 30 residues can be mutated and their neighborhoods repacked.
                                                          The modeling protocol is as described above for single mutations (but has not been benchmarked yet).</dd>
                    <!-- dt>Upload List</dt><dd>Upload a list with single residue mutations.</dd -->
                </dl>
            </div>

            <div id="text2" style="display:none; opacity:0.0; text-align:justify;"> 
                This function utilizes backrub and design protocols implemented in Rosetta. 
                There are two options.
                <dl style="text-align:left;">
                    <dt><b>Backrub Conformational Ensemble</b></dt>
                        <dd>Backrub is applied to the entire input structure to generate a flexible backbone ensemble of modeled protein conformations. 
                        Near-native ensembles made using this method have been shown to be consistent with measures of protein dynamics by 
                        Residual Dipolar Coupling measurements on Ubiquitin [<a href="#ref2">2</a>].</dd>
                    <dt><b>Backrub Ensemble Design</b></dt>
                      <dd>This method first creates an ensemble of structures to model protein flexibility. 
                          In a second step, the generated protein structures are used to predict an ensemble of low-energy sequences consistent with the input structures, 
                          using computational design implemented in Rosetta. The output is a sequence profile of this family of structures. 
                          For ubiquitin, the predicted conformational and sequence ensembles resemble those of the natural occurring protein family [<a href="#ref2">2</a>].</dd>
                </dl>
            </div>
            
            <div id="text3" style="display:none; opacity:0.0; text-align:justify;"> 
                This function utilizes backrub and design protocols implemented in Rosetta.<br><br>
                First, the backrub algorithm is applied to the uploaded protein-protein complex to generate a flexible backbone conformational ensemble of the entire complex. 
                Then, for each of the resulting structure, residue positions given by the user (up to 10) are subjected to protein design, using a genetic algorithm implemented in Rosetta. 
                All generated sequences are ranked by their Rosetta force field score. 
                Sequences with favorable scores both for the total protein complex and the interaction interface are used to build a sequence profile, as described and benchmarked in [<a href="#ref3">3</a>].
            </div>
          <!-- end description -->
          
          <!-- parameter form -->
            <TABLE id="parameter_common" align="center" style="display:none; opacity:0.0;">
              <TR>
                <TD align=right>User Name </TD>
                <TD align=left style="padding-left:5pt; padding-top:5pt;" ><INPUT TYPE="text" maxlength=30 SIZE=31 NAME="UserName" VALUE="%(username)s" disabled>
                </TD>
              </TR>
              <TR></td></TR>
              <TR class="PostPDBSubmission" style="display:none;">
                <TD align=right>Job Name <img src="../images/qm_s.png" title="%(tt_JobName)s"></TD>
                <TD align=left style="padding-left:5pt; padding-top:5pt;"><INPUT TYPE="text" maxlength=40 SIZE=31 NAME="JobName" VALUE="%(jobname)s"></TD>
              </TR>
              <TR class="PDBSelector" style="display:none;">
                <TD align=right>Upload Structure <img src="../images/qm_s.png" title="%(tt_Structure)s"></TD>
                <TD align=left style="padding-left:5pt; padding-top:5pt;" >
                <INPUT id="PDBComplex" TYPE="file" NAME="PDBComplex" size="20" onChange="if (document.submitform.task.value=='parameter3_2'){document.submitform.query.value = 'parsePDB'; document.submitform.submit();}">
                </TD>
              </TR>
              <TR class="PDBSelector" style="display:none;"><TD align="center" colspan="2" style="padding-bottom:0pt; padding-top:0pt;">or</TD></TR>
              <TR class="PDBSelector" style="display:none;">
                <TD align=right>4-digit PDB identifier <img src="../images/qm_s.png" title="%(tt_PDBID)s"></TD>
                <TD align=left style="padding-left:5pt; padding-top:5pt;" > <INPUT TYPE="text" NAME="PDBID" size="4" maxlength="4" onkeydown="if (event.keyCode == 13){document.submitform.query.value = 'parsePDB'; document.submitform.submit();}">
              </TD>
              </TR>''' % self.tooltips
        
        html += '''
              <TR id="UploadedPDB">
                  <TD></TD>
                  <TD align=right style="color:#00bb00;">PDB uploaded: %s</TD>
                  ''' % UploadedPDB
                  
        html += '''
              </TR>
              <TR class="PostPDBSubmission" style="display:none;"><TD colspan=2><br></TD></TR>
              <TR class="PostPDBSubmission" style="display:none;">
                <TD align="center" colspan=2 style="border-bottom:1pt dashed black">General Settings</TD>
              </TR>
              <TR class="PostPDBSubmission" style="display:none;">
                <TD align=right>Rosetta Version <img src="../images/qm_s.png" title="%(tt_RVersion)s"></TD>
                <TD id="rosetta1" style="padding-left:5pt; padding-top:5pt;">
                    <div id="rv0"><input type="radio" name="Mini" value="classic" checked> Rosetta v.2 (classic, as published)<div>
                    <div id="rv1"><input type="radio" name="Mini" value="mini"> Rosetta v.3 (mini, new)</div>
                </TD>
              </TR>
              <TR class="PostPDBSubmission" style="display:none;">
                <TD colspan="2" id="rosetta_remark" style="display:none;" align="right">The Rosetta version in this application is as published [2].</TD>
              </TR>
              <TR class="PostPDBSubmission" style="display:none;">
                <TD align=right>Number of structures <img src="../images/qm_s.png" title="%(tt_NStruct)s"></TD>
                <TD style="padding-left:5pt; padding-top:5pt;"> <input type="text" name="nos" maxlength=3 SIZE=5 VALUE="%(ROSETTAWEB_SK_RecommendedNumStructures)s">
                <span id="recNumStructures">(2-50, recommended 10)</span>
                <span id="recNumStructuresSeqTolSK" style="display:none; opacity:0.0;">(10-100, recommended 20)</span></TD>
              </TR>
              <TR><TD align=left><br></TD></TR>
              <TR class="PostPDBSubmission" style="display:none;">
                <TD align="center" colspan=2 style="border-bottom:1pt dashed black">Application Specific Settings <img src="../images/qm_s.png" border="0" title="%(tt_specific)s"></TD>
              </TR>
            </TABLE>
            
            <!-- Backrub - Costum Mutation -->
            <!-- todo: seems to be deprecated - was this a hack for Greg's protocol? -->
            <p id="parameter1_3" style="display:none; opacity:0.0; text-align:justify;"><b>Custom mutation.</b><br><br>
                This allows for a more flexible definition of mutations. Detailed information about the format of the file can be found in the <A style="color:#365a79; "href="../wiki/Mutations">documentation</A>. <br>
                <font style="text-align:left;">Upload file <INPUT TYPE="file" NAME="Mutations" size="13"></font>
            </p>
        ''' % self.tooltips

        for protocolForm in self.protocolForms:
            htmlcode, ps = protocolForm(listOfChains)
            html += htmlcode
            postscripts += ps

        html += '''     
            <p id="parameter_submit" style="display:none; opacity:0.0; text-align:center;">
              <input type="button" value="Load sample data" onClick="set_demo_values();">
              &nbsp;&nbsp;&nbsp;&nbsp;<input type="button" value="Check form" onClick="ValidateForm();">
              &nbsp;&nbsp;&nbsp;&nbsp;<input type="button" value="Reset Form" onClick="reset_form();">
              &nbsp;&nbsp;&nbsp;&nbsp;<INPUT TYPE="Submit" VALUE="Submit">
            </p>
            <!-- end parameter form -->
            
            <!-- references -->
            <p id="ref1" style="display:none; opacity:0.0; text-align:justify; border:1px solid #000000; padding:5px; font-size: 10pt; background-color:#FFFFFF; ">
                If you are using the data, please cite:<br><br>
                Colin A. Smith, Tanja Kortemme, <i>Backrub-Like Backbone Simulation Recapitulates Natural Protein Conformational Variability and Improves Mutant Side-Chain Prediction</i>,<br>
                <a href="http://dx.doi.org/10.1016/j.jmb.2008.05.023" style="font-size: 10pt"> Journal of Molecular Biology Volume 380, 742-756</a>
                </p>
            </p>

            <p id="ref2" style="display:none; opacity:0.0; text-align:justify;border:1px solid #000000; padding:5px; font-size: 10pt; background-color:#FFFFFF; ">
                If you are using the data, please cite:<br><br>
                Friedland GD, Lakomek NA, Griesinger C, Meiler J, Kortemme T., <i>A correspondence between solution-state dynamics of an individual protein and the sequence and conformational diversity of its family.</i>,<br>
                <a href="http://dx.doi.org/10.1371/journal.pcbi.1000393" style="font-size: 10pt"> PLoS Comput Biol. 2009 May</a>
            </p>   
            
            <p id="ref3" style="display:none; opacity:0.0; text-align:justify;border:1px solid #000000; padding:5px; font-size: 10pt; background-color:#FFFFFF; ">
                If you are using the data, please cite:<br><br>
                Humphris EL, Kortemme T. <i>Prediction of protein-protein interface sequence diversity using flexible backbone computational protein design.</i>,<br>
                <a href="http://dx.doi.org/10.1016/j.str.2008.09.012" style="font-size: 10pt"> Structure. (2008). Dec 12;16(12):1777-88</a> 
            </p> 

            <p id="ref4" style="display:none; opacity:0.0; text-align:justify;border:1px solid #000000; padding:5px; font-size: 10pt; background-color:#FFFFFF; ">
                If you are using the data, please cite:<br><br>
                Colin A. Smith, Tanja Kortemme, <i>Structure-Based Prediction of the Peptide Sequence Space Recognized by Natural and Synthetic PDZ Domains.</i><br>
                <a href="http://dx.doi.org/10.1016/j.jmb.2008.05.023" style="font-size: 10pt"> Journal of Molecular Biology Volume 402, 460-474</a> 
            </p> 

          </div> <!-- id=box -->  
          </td>
<!-- end right column -->            
        </tr>
      </table>
            ''' % self.tooltips
      
        if task == None:
            task = "init"
      
        # We store the uploaded PDB as a form value so it can be retrieved on submission
        # Note that this could allow a malicious user to replace the filename. As we read
        # and check the file for PDB content, this shouldn't be an issue but serverside, we
        # should ignore any path in the filename.
        # todo:  In fact, if a filename contains path information or is not a PDB (we have 
        #        ensured that the actual uploaded file was a PDB), then we should flag this 
        #        behaviour and email the admin.
        # todo:  Name the PDB better e.g. directory with user session id / original name
        html += '''
            <INPUT TYPE="hidden" NAME="task"  VALUE="%s">
            <INPUT TYPE="hidden" NAME="StoredPDB"  VALUE="%s">
            <INPUT TYPE="hidden" NAME="query" VALUE="submitted">
            <INPUT TYPE="hidden" NAME="mode"  VALUE="check">
          </FORM>
<!-- End Submit Form -->
        </td>
            ''' % (task, StoredPDB) 

        html += postscripts
        return html

        # <tr>
        #     <td  align="right"><img src="../images/qm_s.png" title="%(ttseqtol_weights)s">Weight for Partner</td>
        #     <td>
        #       <table >
        #         <tr >
        #           <td align="center">1:</td><td align="center"><input type="text" name="seqtol_weight_chain1" maxlength=1 SIZE=2 VALUE="1"></td>
        #           <td align="center">2:</td><td align="center"><input type="text" name="seqtol_weight_chain2" maxlength=1 SIZE=2 VALUE="1"></td>
        #           <td align="center">interface:</td><td align="center"><input type="text" name="seqtol_weight_interface" maxlength=1 SIZE=2 VALUE="2"></td>
        #         </tr>
        #       </table>
        #     </td>
        #   </tr>

    def submitOnePointMutation(self, listOfChains):
        return '''
         <!-- Backrub - Point Mutation -->
            <p id="parameter1_1" style="display:none; opacity:0.0; text-align:justify;">
                <table align=center>
                <tr>
                    <td align="right">Chain ID <img src="../images/qm_s.png" title="%(tt_ChainId)s"></td><td><input type="text" name="PM_chain"  maxlength=1 SIZE=5 VALUE=""></td>
                </tr>
                <tr>
                    <td align="right">Residue Number <img src="../images/qm_s.png" title="%(tt_ResId)s"></td><td><input type="text" name="PM_resid"  maxlength=4 SIZE=5 VALUE=""></td>
                </tr>
                <tr>
                    <td align="right">New Amino Acid <img src="../images/qm_s.png" title="%(tt_NewAA)s"></td><td><input type="text" name="PM_newres" maxlength=1 SIZE=5 VALUE=""></td>
                </tr>
                <tr>
                    <td><INPUT TYPE="hidden" NAME="PM_radius" VALUE="6.0"></td>
                </tr>
                </table>
                <br>
            </p>
            ''' % self.tooltips, ""

    def submitMultiplePointMutations(self, listOfChains):
        return '''
            <!-- Backrub - Multiple Point Mutation -->
            <p id="parameter1_2" style="display:none; opacity:0.0; text-align:justify;">
                <table bgcolor="#EEEEEE" align="center">
                <tr bgcolor="#828282" style="color:white;">
                    <td align="center">#</td>
                    <td align="center" title="%(tt_ChainId)s">Chain ID</td>
                    <td align="center" title="%(tt_ResId)s">Res ID</td>
                    <td align="center" title="%(tt_NewAA)s">AA</td>
                    <td align="center" title="%(tt_Radius)s">Radius [&#197;]</td>
                </tr>
                <!-- up to 31 point mutations are possible -->
                <tr id="row_PM0" style=""><td align="center">1</td><td align="center"><input name="PM_chain0" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid0" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres0" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius0" maxlength="4" size="7" type="text"></td></tr>
                <tr id="row_PM1" style="display:none"><td align="center">2</td><td align="center"><input name="PM_chain1" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid1" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres1" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius1" maxlength="4" size="7" type="text"></td></tr>   
                <tr id="row_PM2" style="display:none"><td align="center">3</td><td align="center"><input name="PM_chain2" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid2" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres2" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius2" maxlength="4" size="7" type="text"></td></tr>
                <tr id="row_PM3" style="display:none"><td align="center">4</td><td align="center"><input name="PM_chain3" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid3" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres3" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius3" maxlength="4" size="7" type="text"></td></tr>   
                <tr id="row_PM4" style="display:none"><td align="center">5</td><td align="center"><input name="PM_chain4" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid4" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres4" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius4" maxlength="4" size="7" type="text"></td></tr>
                <tr id="row_PM5" style="display:none"><td align="center">6</td><td align="center"><input name="PM_chain5" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid5" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres5" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius5" maxlength="4" size="7" type="text"></td></tr>   
                <tr id="row_PM6" style="display:none"><td align="center">7</td><td align="center"><input name="PM_chain6" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid6" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres6" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius6" maxlength="4" size="7" type="text"></td></tr>
                <tr id="row_PM7" style="display:none"><td align="center">8</td><td align="center"><input name="PM_chain7" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid7" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres7" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius7" maxlength="4" size="7" type="text"></td></tr>  
                <tr id="row_PM8" style="display:none"><td align="center">9</td><td align="center"><input name="PM_chain8" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid8" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres8" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius8" maxlength="4" size="7" type="text"></td></tr>
                <tr id="row_PM9" style="display:none"><td align="center">10</td><td align="center"><input name="PM_chain9" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid9" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres9" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius9" maxlength="4" size="7" type="text"></td></tr>   
                <tr id="row_PM10" style="display:none"><td align="center">11</td><td align="center"><input name="PM_chain10" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid10" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres10" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius10" maxlength="4" size="7" type="text"></td></tr>
                <tr id="row_PM11" style="display:none"><td align="center">12</td><td align="center"><input name="PM_chain11" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid11" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres11" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius11" maxlength="4" size="7" type="text"></td></tr> 
                <tr id="row_PM12" style="display:none"><td align="center">13</td><td align="center"><input name="PM_chain12" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid12" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres12" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius12" maxlength="4" size="7" type="text"></td></tr>
                <tr id="row_PM13" style="display:none"><td align="center">14</td><td align="center"><input name="PM_chain13" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid13" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres13" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius13" maxlength="4" size="7" type="text"></td></tr> 
                <tr id="row_PM14" style="display:none"><td align="center">15</td><td align="center"><input name="PM_chain14" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid14" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres14" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius14" maxlength="4" size="7" type="text"></td></tr>
                <tr id="row_PM15" style="display:none"><td align="center">16</td><td align="center"><input name="PM_chain15" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid15" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres15" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius15" maxlength="4" size="7" type="text"></td></tr> 
                <tr id="row_PM16" style="display:none"><td align="center">17</td><td align="center"><input name="PM_chain16" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid16" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres16" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius16" maxlength="4" size="7" type="text"></td></tr>
                <tr id="row_PM17" style="display:none"><td align="center">18</td><td align="center"><input name="PM_chain17" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid17" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres17" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius17" maxlength="4" size="7" type="text"></td></tr> 
                <tr id="row_PM18" style="display:none"><td align="center">19</td><td align="center"><input name="PM_chain18" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid18" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres18" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius18" maxlength="4" size="7" type="text"></td></tr>
                <tr id="row_PM19" style="display:none"><td align="center">20</td><td align="center"><input name="PM_chain19" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid19" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres19" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius19" maxlength="4" size="7" type="text"></td></tr> 
                <tr id="row_PM20" style="display:none"><td align="center">21</td><td align="center"><input name="PM_chain20" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid20" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres20" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius20" maxlength="4" size="7" type="text"></td></tr>
                <tr id="row_PM21" style="display:none"><td align="center">22</td><td align="center"><input name="PM_chain21" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid21" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres21" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius21" maxlength="4" size="7" type="text"></td></tr> 
                <tr id="row_PM22" style="display:none"><td align="center">23</td><td align="center"><input name="PM_chain22" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid22" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres22" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius22" maxlength="4" size="7" type="text"></td></tr>
                <tr id="row_PM23" style="display:none"><td align="center">24</td><td align="center"><input name="PM_chain23" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid23" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres23" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius23" maxlength="4" size="7" type="text"></td></tr> 
                <tr id="row_PM24" style="display:none"><td align="center">25</td><td align="center"><input name="PM_chain24" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid24" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres24" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius24" maxlength="4" size="7" type="text"></td></tr>
                <tr id="row_PM25" style="display:none"><td align="center">26</td><td align="center"><input name="PM_chain25" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid25" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres25" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius25" maxlength="4" size="7" type="text"></td></tr> 
                <tr id="row_PM26" style="display:none"><td align="center">27</td><td align="center"><input name="PM_chain26" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid26" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres26" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius26" maxlength="4" size="7" type="text"></td></tr>
                <tr id="row_PM27" style="display:none"><td align="center">28</td><td align="center"><input name="PM_chain27" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid27" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres27" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius27" maxlength="4" size="7" type="text"></td></tr> 
                <tr id="row_PM28" style="display:none"><td align="center">29</td><td align="center"><input name="PM_chain28" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid28" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres28" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius28" maxlength="4" size="7" type="text"></td></tr>
                <tr id="row_PM29" style="display:none"><td align="center">30</td><td align="center"><input name="PM_chain29" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid29" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres29" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius29" maxlength="4" size="7" type="text"></td></tr> 
                <tr id="row_PM30" style="display:none"><td align="center">31</td><td align="center"><input name="PM_chain30" maxlength="1" size="5" type="text"></td><td align="center"><input name="PM_resid30" maxlength="4" size="5" type="text"></td><td align="center"><input name="PM_newres30" maxlength="1" size="2" type="text"></td><td align="center"><input name="PM_radius30" maxlength="4" size="7" type="text"></td></tr>
                <tr><td align="center" colspan="4"><a href="javascript:void(0)" onclick="addOneMore();">Click here to add a residue</a></td></tr>
                </table>
            </p>
            ''' % self.tooltips, ""

    def submitBRConformationalEnsemble(self, listOfChains):
        return '''
            <!-- Ensemble - simple -->
            <p id="parameter2_1" style="display:none; opacity:0.0; text-align:center;">no options</p>            
            ''' % self.tooltips, ""

    def submitBREnsembleDesign(self, listOfChains):
        return '''
            <!-- Ensemble - design -->
            <p id="parameter2_2" style="display:none; opacity:0.0; text-align:center;">
                <table align="center">
                <tr>
                    <td align="right">Temperature [kT] <img src="../images/qm_s.png" title="%(tt_Temp)s"></td><td><input type="text" name="ENS_temperature" maxlength=3 SIZE=5 VALUE="1.2">(max 4.8, recommended 1.2)</td>
                </tr>
                <tr>
                    <td align="right">Max. segment length <img src="../images/qm_s.png" title="%(tt_SegLength)s"></td><td><input type="text" name="ENS_segment_length" maxlength=2 SIZE=5 VALUE="12">(max 12, recommended 12)</td>
                </tr>
                <tr>
                    <td align="right">No. of sequences <img src="../images/qm_s.png" title="%(tt_NSeq)s"></td><td><input type="text" name="ENS_num_designs_per_struct" maxlength=4 SIZE=5 VALUE="20">(max 20, recommended 20)</td>
                </tr>
                </table>
            </p>
            ''' % self.tooltips, ""
            
    def submitSeqTolHK(self, listOfChains):
        return '''
            <!-- Library Design -->
            <p id="parameter3_1" style="display:none; opacity:0.0; text-align:center;">
            <table align="center">
              <tr>
                  <td  align="right">Partner 1 <img src="../images/qm_s.png" title="%(tt_seqtol_partner)s"></td>
                  <td>Chain <input type="text" name="seqtol_chain1" maxlength=1 SIZE=2 VALUE=""></td>
              </tr>
              <tr>
                  <td  align="right">Partner 2 <img src="../images/qm_s.png" title="%(tt_seqtol_partner)s"></td>
                  <td>Chain <input type="text" name="seqtol_chain2" maxlength=1 SIZE=2 VALUE="">
                  </td>
              </tr>
              
                <tr>
                  <td align="right">Residues for design<img src="../images/qm_s.png" title="%(tt_seqtol_design)s"></td>
                  <td>
                    <table bgcolor="#EEEEEE">
                      <tr bgcolor="#828282" style="color:white;">
                        <td>#</td><td>Chain ID</td><td>Residue Number</td>
                      </tr>
                      <tr align="center" id="seqtol_row_0" >                    <td>1</td><td><input type="text" name="seqtol_mut_c_0" maxlength=1 SIZE=2></td><td><input type="text" name="seqtol_mut_r_0" maxlength=4 SIZE=4></td></tr>
                      <tr align="center" id="seqtol_row_1" style="display:none"><td>2</td><td><input type="text" name="seqtol_mut_c_1" maxlength=1 SIZE=2></td><td><input type="text" name="seqtol_mut_r_1" maxlength=4 SIZE=4></td></tr>
                      <tr align="center" id="seqtol_row_2" style="display:none"><td>3</td><td><input type="text" name="seqtol_mut_c_2" maxlength=1 SIZE=2></td><td><input type="text" name="seqtol_mut_r_2" maxlength=4 SIZE=4></td></tr>
                      <tr align="center" id="seqtol_row_3" style="display:none"><td>4</td><td><input type="text" name="seqtol_mut_c_3" maxlength=1 SIZE=2></td><td><input type="text" name="seqtol_mut_r_3" maxlength=4 SIZE=4></td></tr>
                      <tr align="center" id="seqtol_row_4" style="display:none"><td>5</td><td><input type="text" name="seqtol_mut_c_4" maxlength=1 SIZE=2></td><td><input type="text" name="seqtol_mut_r_4" maxlength=4 SIZE=4></td></tr>
                      <tr align="center" id="seqtol_row_5" style="display:none"><td>6</td><td><input type="text" name="seqtol_mut_c_5" maxlength=1 SIZE=2></td><td><input type="text" name="seqtol_mut_r_5" maxlength=4 SIZE=4></td></tr>
                      <tr align="center" id="seqtol_row_6" style="display:none"><td>7</td><td><input type="text" name="seqtol_mut_c_6" maxlength=1 SIZE=2></td><td><input type="text" name="seqtol_mut_r_6" maxlength=4 SIZE=4></td></tr>
                      <tr align="center" id="seqtol_row_7" style="display:none"><td>8</td><td><input type="text" name="seqtol_mut_c_7" maxlength=1 SIZE=2></td><td><input type="text" name="seqtol_mut_r_7" maxlength=4 SIZE=4></td></tr>
                      <tr align="center" id="seqtol_row_8" style="display:none"><td>9</td><td><input type="text" name="seqtol_mut_c_8" maxlength=1 SIZE=2></td><td><input type="text" name="seqtol_mut_r_8" maxlength=4 SIZE=4></td></tr>
                      <tr align="center" id="seqtol_row_9" style="display:none"><td>10</td><td><input type="text" name="seqtol_mut_c_9" maxlength=1 SIZE=2></td><td><input type="text" name="seqtol_mut_r_9" maxlength=4 SIZE=4></td></tr>
                      <tr align="center"><td colspan="3"><a href="javascript:void(0)" onclick="addOneMoreSeqtol();">Click here to add a residue</a></td></tr>
                      </table>
                  </td>
                </tr>
            </table>
            </p>
            ''' % self.tooltips, ""

    def submitSeqTolSK(self, listOfChains):

        # Test: python rosettaseqtol.py 1601 2I0L_A_C_V2006.pdb 2 10.0 0.228 2 0.4 1.0 0.4 A 318 B
            #Upload structure: 2I0L_A_C_V2006.pdb
            #Number of structures: 2 
            #Radius: 10.0
            #kT: 0.228
            #Weights list: 2 0.4 1.0 0.4
            #Designed residues: A 318 B
        
        postscript = ""
        
        # This string holds options for comboboxes to select chains
        # When there is only one, we fill in the default choice
        numChainsAvailable = len(listOfChains)
        chainOptions = ""
        if numChainsAvailable == 1:
            for c in listOfChains:
                chainOptions = '''<option value="%s" selected>%s</option> 
                                  <option value="invalid">Select a chain</option>
                                ''' % (c, c) 
        else:
            chainOptions = '''<option value="invalid" selected>Select a chain</option>''' 
            for c in listOfChains:
                chainOptions += '''<option value="%s">%s</option>''' % (c, c)


        html = '''<p id="parameter3_2" style="display:none; opacity:0.0; text-align:center;">'''
        
         # Header

        html += '''<table id="parameter3_2_header"  style="display:none; opacity:0.0; text-align:center;">
                    <tr>
                    <td>
                    <select id="numPartners" name="numPartners" onfocus="this.valueatfocus=this.value" 
                        onChange="if ((this.value != this.valueatfocus) && (this.value != 'x')) {subtask = 2; changeApplication('3','2', this.selectedIndex);} " 
                        onblur  ="if ((this.value != this.valueatfocus) && (this.value != 'x')) {subtask = 2; changeApplication('3','2', this.selectedIndex);} "                        
                    >
                        <option value="x">Select the number of partners</option>
                        <option value="1">1 Partner (Fold stability)</option>                    
                    '''
         
        if numChainsAvailable > 1:
            html += '''
                            <option value="2">2 Partners (Interface)</option> '''
            numChainsAllowed = min(ROSETTAWEB_max_seqtol_SK_chains, numChainsAvailable)
            for j in range(3, numChainsAllowed + 1):
                html += ''' <option value="%s">%s Partners</option> ''' % (j, j)
        
        html += '''</select></td></tr><tr><td height="10"></td></tr></table>'''
        
        # Body
        html += '''<table align="center" id="parameter3_2_body">'''
        
        # Chains
        tt = self.tooltips["tt_seqtol_SK_partner"]

        # Chains are either: i) selectable with the name of the chain as value or "invalid" if no selection is made;
        # or ii) not selectable with the value set to "ignore"
    
        for i in range(numChainsAvailable):
            html += '''
              <tr id="seqtol_SK_chainrow_%d">
                  <td align="left">Partner %d <img src="../images/qm_s.png" title="%s"></td>
                  <td>Chain <select name="seqtol_SK_chain%d" onChange="chainsChanged();" onfocus="this.valueatfocus=this.value" onblur="if (this.value != this.valueatfocus) chainsChanged()">%s</select></td>
                  </tr>
                  ''' % (i, i+1, tt, i, chainOptions)
        for i in range(numChainsAvailable, ROSETTAWEB_max_seqtol_SK_chains):
            html += '''
                <tr id="seqtol_SK_chainrow_%d">
                  <td align="left">Partner %d <img src="../images/qm_s.png" title="%s"></td>
                  <td>Chain <select name="seqtol_SK_chain%d"><option value="ignore" selected>Select a chain</option></select></td>
                  </tr>
                  ''' % (i, i+1, tt, i)
        
        html += '''
              <tr>
                  <td></td>
                  <td><div id="seqtol_SK_addchain"><a href="javascript:void(0)" onclick="addOneMoreChainSK();">Click here to add a chain</a></div></td>
              </tr> '''

        # Premutated residues
        html += '''
              <tr><td height="10"></td></tr>
                <tr>
                  <td align="left" valign="top">Premutated residues<img src="../images/qm_s.png" title="%(tt_seqtol_premutated)s"></td>
                  <td>
                    <table bgcolor="#EEEEEE">
                      <tr bgcolor="#828282" style="color:white;">
                        <td>#</td><td>Chain ID</td><td>Residue Number</td><td>Target amino acid</td>
                      </tr>
              ''' % self.tooltips
        for i in range(0, ROSETTAWEB_SK_MaxPremutations):
            #style="display:none"
            html += '''<tr align="center" id="seqtol_SK_pre_row_%d"> 
                            <td>%d</td>
                            <td><select name="seqtol_SK_pre_mut_c_%d" style="text-align:center;" onChange="updateBoltzmann();">%s</select></td>
                        ''' % (i, i+1, i, chainOptions)
            
            html += '''     <td><input type="text" name="seqtol_SK_pre_mut_r_%d" maxlength=4 SIZE=4 onChange="updateBoltzmann();"></td>
                            <td><select name="premutatedAA%d" style="text-align:center;" onChange="updateBoltzmann();">
                            <option value="" selected>Select an amino acid</option>''' % (i, i)
            for j in sorted(ROSETTAWEB_SK_AA.keys()):
                html += ''' <option value="%s">%s</option> ''' % (j, j)
            html += ''' </select></tr>'''
            
        html += '''
                      <tr align="center"><td colspan="3"><div id="seqtol_SK_pre_addrow"><a href="javascript:void(0)" onclick="addOneMoreSeqtolSKPremutated();">Click here to add a residue</a></div></td></tr>
                      </table>
                  </td>
                </tr>
              <tr><td height="10"></td></tr>'''
        
        # Residues for design       
        html += '''
              <tr><td height="10"></td></tr>
                <tr>
                  <td align="left" valign="top">Residues for design<img src="../images/qm_s.png" title="%(tt_seqtol_design)s"></td>
                  <td>
                    <table bgcolor="#EEEEEE">
                      <tr bgcolor="#828282" style="color:white;">
                        <td>#</td><td>Chain ID</td><td>Residue Number</td>
                      </tr>
              ''' % self.tooltips
        html += '''<tr align="center" id="seqtol_SK_row_0"><td>1</td>
                    <td><select name="seqtol_SK_mut_c_0" style="text-align:center;">%s</select>
                    </td>
                    <td><input type="text" name="seqtol_SK_mut_r_0" maxlength=4 SIZE=4></td></tr>''' % chainOptions
        for i in range(1, ROSETTAWEB_SK_MaxMutations):
            html += '''<tr align="center" id="seqtol_SK_row_%d" style="display:none">
                        <td>%d</td>
                        <td><select name="seqtol_SK_mut_c_%d" style="text-align:center;">%s</select></td>
                        ''' % (i, i+1, i, chainOptions)
                
            html += ''' <td><input type="text" name="seqtol_SK_mut_r_%d" maxlength=4 SIZE=4></td>
                        </tr>''' % i
        html += '''
                      <tr align="center"><td colspan="3"><div id="seqtol_SK_addrow"><a href="javascript:void(0)" onclick="addOneMoreSeqtolSK();">Click here to add a residue</a></div></td></tr>
                      </table>
                  </td>
                </tr>
              <tr><td height="10"></td></tr>'''
        
        # Score reweighting        
        html += '''               
              <tr><td height="10"></td></tr>
              <tr>
                  <td align="left">Score Reweighting<img src="../images/qm_s.png" title="%(tt_seqtol_SK_weighting)s"></td>
              ''' % self.tooltips
        
        html += '''
                  <td colspan="1">
                    <table id="mutationsTable" bgcolor="#EEEEEE">
                      <tr bgcolor="#828282" style="color:white;">
                          <td bgcolor="#EEEEEE"></td>
                          <td align="center" bgcolor="#EEEEEE"></td>
                          <td align="center" colspan="%d" id="seqtol_SK_IEHeader">Interaction Energies</td> 
                      </tr>
                      <tr align="center" bgcolor="#828282" style="color:white;" >
                        <td bgcolor="#EEEEEE"></td>
                        <td>Self Energy</td>
                ''' % (ROSETTAWEB_max_seqtol_SK_chains - 1)
        
        for i in range(1, ROSETTAWEB_max_seqtol_SK_chains):
            html += '''<td class="seqtol_SK_kP%d" style="display:none">Partner %d</td>''' % (i - 1, i)
        
        html += '''</tr>'''
        
        for i in range(0, ROSETTAWEB_max_seqtol_SK_chains):
            html += '''   <tr align="center" id="seqtol_SK_weight_%d" style="display:none">                    
                          <td align="left">Partner %d</td>
                          <td><input type="text" name="seqtol_SK_kP%dP%d" maxlength=5 SIZE=4 VALUE="0.4"></td>
                           ''' % (i, i + 1, i, i)
                        
            for j in range(0, i):
                html += '''<td class="seqtol_SK_kP%d"><input type="text" name="seqtol_SK_kP%dP%d" maxlength=5 SIZE=4 VALUE="1.0"></td>''' % (j, j, i)                           
            
            for j in range(i, ROSETTAWEB_max_seqtol_SK_chains - 1):
                html += '''<td class="seqtol_SK_kP%d"></td>''' % j   
            
            html += "</tr>"
        html += "</tr></table></td></tr>"
        
        # Boltzmann factor
        html += '''
                <tr><td height="10"></td></tr>
                <tr>
                  <td align="left">Boltzmann Factor (kT)<img src="../images/qm_s.png" title="%(tt_seqtol_SK_Boltzmann)s"></td>
                  <td>
                  ''' % self.tooltips
        html += '''<input type="text" name="seqtol_SK_Boltzmann" disabled="true" maxlength=5 SIZE=5 VALUE="">                                 
                  </td>
                </tr>
                <tr>
                <td></td><td><input type="checkbox" name="customBoltzmann" checked="checked" value="Milk" onClick="set_Boltzmann();">Use published value</td>
                </tr>''' 
 
        html += '''                    
            </table>
            </p>'''

        return html, postscript
            
    def submitted(self, jobname, cryptID, remark, warnings):
      
      if remark == 'new':
        box = '''<table width="550"><tr><td class="linkbox" align="center" style="background-color:#F0454B;">
                    <font color="black" style="font-weight: bold; text-decoration:blink;">If you are a guest user bookmark this link to retrieve your results later!</font><br>
                    Raw data files:<br><a class="blacklink" href="https://%s%s?query=datadir&job=%s" target="_blank">https://%s%s?query=datadir&job=%s</a>
                    </td></tr></table>''' % ( self.server_url, self.script_filename, cryptID, self.server_url, self.script_filename, cryptID )
#                     Job Info page:<br><a class="blacklink" href="%s?query=jobinfo&jobnumber=%s" target="_blank">https://%s?query=jobinfo&jobnumber=%s</a><br> % ( self.script_filename, cryptID, self.script_filename, cryptID )
                    
      elif remark == 'old':
        box = '''<table width="550"><tr><td class="linkbox" align="center" style="background-color:#53D04F;">
                    <font color="black" style="font-weight: bold; text-decoration:blink;">A job with the same parameters has already been processed. 
                                                                                          Please use one of the following links to go to the results:</font><br>
                     <br><a class="blacklink" href="%s?query=jobinfo&jobnumber=%s" target="_blank">Job Info page</a> or Raw data files:<br>
                         <a class="blacklink" href="%s?query=datadir&job=%s" target="_blank">https://%s%s?query=datadir&job=%s</a>
                    </td></tr></table>''' % ( self.script_filename, cryptID, self.script_filename, cryptID, self.server_url, self.script_filename, cryptID )
      else:
        # I don't think this can happen but best to be safe
        box = '<font color="red">An error occured, please <a HREF="javascript:history.go(-1)">go back</a> and try again</font>'
      
      if warnings != '':
          warningsbox = '''
              <table width="550" style="background-color:#ff4500;">
                  <tr>
                      <td class="linkbox" align="center">
                        <font color="black" style="font-weight: bold; text-decoration:blink;">The job submission raised the following warnings/messages:</font>
                      </td>
                      <td align="left"><ul>%s</ul></td>
                      <td class="linkbox" align="center">
                      <font color="black" style="font-weight: bold;">However, the job will continue to run.</font>
                      </td>
                  </tr>
              </table>''' % ( warnings )
      else:
          warningsbox = ''
      
      html = """<td align="center"><H1 class="title">New Job successfully submitted</H1>
                  %s<br>
                  %s<br>
                  <P>Once your request has been processed the results are accessible via the above URL. You can also access your data via the <A href="%s?query=queue">job queue</A> at any time.<br>
                  If you <b>are not</b> registered and use the guest access please bookmark this link. Your data will be stored for 10 days.<br>
                  If you are registered and logged in we will send you an email with this information once the job is finished. 
                  In this case you will be able to access your data for 60 days.<br>
                  </P>
                  From here you can proceed to the <a href="%s?query=jobinfo&jobnumber=%s">job info page</a>, 
                  <a HREF="javascript:history.go(-1)">submit a new job</a>.
                  <br><br>
                  </td>\n"""  % ( box, warningsbox, self.script_filename, self.script_filename, cryptID )
                     #% (UserName, JobName, pdbfile.filename) )
      return html



###############################################################################################
#                                                                                             #
###############################################################################################

    def register(self, username='', firstname='', lastname='', institution='', email='', address='', city='', zip='', state='', country='', error='', update=False ):
        
        error_html = ''
        if error != '':
            error_html = '<P style="text-align:center; color:red;">%s</P>' % ( error )
        
        disabled = ''
        mode = 'check'
        if update:
            disabled = 'disabled'
            mode = 'update'

        html = """<td align=center>
        <H1 class="title" align=center>Registration</H1>
    
        <P style="text-align:center;">
        Please enter all required information.  
        </P>
        %s
        <br>
        <form name="myForm" method="post" onsubmit="return ValidateFormRegister();">
          <table border=0 cellpadding=2 cellspacing=0>
            <tr><td colspan=2><b>Required Fields</b></td></tr>
            <tr><td align=right class="register">Username: </td>
                <td><input type=text size=20 maxlength=50 name="username" value="%s" %s></td>
            </tr>
            <tr><td align=right class="register">First Name: </td>
                <td><input type=text size=20 maxlength=50 name="firstname" value="%s"></td>
            </tr>
            <tr><td align=right class="register">Last Name: </td>
                <td><input type=text size=20 maxlength=50 name="lastname" value="%s"></td>
            </tr>
            <tr><td align=right class="register">Email: </td>
                <td><input type=text size=20 maxlength=50 name="email" value="%s" %s></td>
            </tr>
            <tr><td align=right class="register">Password: </td>
                <td><input type=password size=20 maxlength=50 name="password" value=""></td>
            </tr>
            <tr><td align=right class="register">Confirm Password: </td>
                <td><input type=password size=20 maxlength=50 name="confirmpassword" value=""></td>
            </tr>                                                                
            <tr><td colspan=2>&nbsp;</td></tr>                                                  
            <tr><td colspan=2><b>Optional Fields</b></td></tr>
            <tr><td align=right class="register">Institution: </td>
                <td><input type=text size=20 maxlength=50 name="institution" value="%s"></td>
            </tr>
            <tr><td align=right class="register">Address: </td>
                <td><input type=text size=20 maxlength=50 name="address" value="%s"></td>
            </tr>
            <tr><td align=right class="register">City: </td>
                <td><input type=text size=20 maxlength=50 name="city" value="%s"></td>
            </tr>
            <tr><td align=right class="register">Zip: </td>
                <td><input type=text size=20 maxlength=50 name="zip" value="%s"></td>
            </tr>
            <tr><td align=right class="register">State: </td>
                <td><input type=text size=20 maxlength=50 name="state" value="%s"></td>
            </tr>
            <tr><td align=right class="register">Country</td>
                <td><select name="country">
                %s
            </select></td>
        </tr>
            <tr><td>&nbsp;</td></tr>
            <tr><td></td>
            <td align=left><input type=hidden name=query  value=register>                     
                           <input type=hidden name=mode   value=%s>
            <A href="%s?query=terms_of_service#privacy">View privacy notice</A>                           
                        &nbsp; &nbsp; &nbsp; 
        <input type=submit name=submit value=Register>
                  </td>
              </form>                    
          </tr>                            
        </table></td>
        """ % (error_html, username, disabled, firstname, lastname, institution, email, disabled, address, city, zip, state, self._printCountries(country), mode, self.script_filename)
    
        return html
    

    def registered(self):
      html = """ <td align="center">Registration successful. You should recieve a confirmation Email shortly.<br> <br> \n 
                   Proceed to <A href="%s?query=login">Login</A> \n""" % ( self.script_filename )
      return html

    def updated(self):
      html = '<td align="center">Your information has been updated successfully.<br> <br> \n'
      return html

    def _printCountries(self,selected):
      
      country_file = open("countries.txt",'r')
      countries = country_file.readlines()
      country_file.close()
      html = ""
      
      if selected == "":
        html = """         <option value="" selected>Select Country</option>\n"""
      
      for country in countries:
        country_name = country.rstrip()
        if selected == country_name:
          html += """      <option value="%s"%s>%s</option>\n""" % (country_name, " selected ", country_name)
        else:
          html += """      <option value="%s">%s</option>\n""" % (country_name, country_name)
    
      return html

    
###############################################################################################
#                                                                                             #
###############################################################################################


    def printQueue(self,job_list):
      
        html = """<td align=center><H1 class="title"> Job queue </H1> <br>
                  <div id="queue_bg">
                  <table border=0 cellpadding=2 cellspacing=0 width=700 >
                   <colgroup>
                     <col width="35">
                     <col width="80">
                     <col width="90">
                     <col width="90">
                     <col width="200">
                     <col width="160">
                     <col width="25">
                   </colgroup>
                  <tr align=center bgcolor="#828282" style="color:white;"> 
                   <td > ID </td> 
                   <td > Status </td> 
                   <td > User Name </td>
                   <td > Date (PST) </td>
                   <td > Job Name </td>
                   <td > Rosetta Application </td>
                   <td > Structures </td>\n"""
                   
        for line in job_list:
            task = ''
            task_color = '#EEEEEE'
            if line[9] == '0' or line[9] == 'no_mutation':
                task = "Backrub Ensemble"
                task_color = '#B7FFE0'
            elif line[9] == '1' or line[9] == 'point_mutation':
                task = "Point Mutation"
                task_color = '#DCE9F4'
            elif line[9] == '3' or line[9] == 'multiple_mutation':
                task = "Multiple Point Mutations"
                task_color = '#DCE9F4'
            elif line[9] == '2' or line[9] == 'upload_mutation':
                task = "Custom Mutation"
                task_color = '#DCE9F4'
            elif line[9] == '4' or line[9] == 'ensemble':
                task = "Backrub Ensemble Design"
                task_color = '#B7FFE0'
            elif line[9] == 'sequence_tolerance':
                task = "Sequence Tolerance"
                task_color = '#FFE2E2'
            elif line[9] == 'sequence_tolerance_SK':
                task = "Sequence Tolerance"
                task_color = '#FFE2E2'
          
            html += """<tr align=center bgcolor="#EEEEEE" onmouseover="this.style.background='#447DAE'; this.style.color='#FFFFFF';" 
                                                          onmouseout="this.style.background='#EEEEEE'; this.style.color='#000000';" >
                                                          """
            link_to_job = 'onclick="window.location.href=\'%s?query=jobinfo&jobnumber=%s\'"' % ( self.script_filename, line[1] )
            # write ID
            html += '<td id="lw" %s>%s </td>' % (link_to_job, str(line[0]))
            # write status 
            status = int(line[2])
            if status == 0:
                html += '<td id="lw" %s><font color="orange">in queue</font></td>' % link_to_job
            elif status == 1:
                html += '<td id="lw" %s><font color="green">active</font></td>' % link_to_job
            elif status == 2:
                html += '<td id="lw" %s>done</td>' % link_to_job # <font color="darkblue" %s></font>
            elif status == 5:
                html += '<td id="lw" style="background-color: #AFE2C2;" %s><font color="darkblue">sample</font></td>' % link_to_job
            else:
              # write error
              if  str(line[8]) != '' and line[8] != None:
                # onclick="window.open('https://kortemmelab.ucsf.edu/backrub/wiki/Error#Errors_during_the_simulation','backrub_wiki')"
                #                        onmouseover="this.style.background='#447DAE'; this.style.color='#000000'"
                #                        onmouseout="this.style.background='#EEEEEE';"
                html += '''<td id="lw">
                              <font color="FF0000">error</font>
                              (<a href="https://kortemmelab.ucsf.edu/backrub/wiki/Error#Errors_during_the_simulation" target="_blank"
                                 onmouseover="this.style.color='#FFFFFF'" onmouseout="this.style.color='#365a79'">%s</a>)</td>''' % str(line[8])
              else:
                html += '<td id="lw"><font color="FF0000">error</font></td>'
                
            # write username
            html += '<td id="lw" %s>%s</td>' % (link_to_job, str(line[3]))
            # write date
            html += '<td id="lw" style="font-size:small;" %s>%s</td>' % (link_to_job, str(line[4]))
            # write jobname or "notes"
            if len(str(line[5])) < 26:
                html += '<td id="lw" %s>%s</td>' % (link_to_job, str(line[5]))
            else:
                html += '<td id="lw" %s>%s</td>' % (link_to_job, str(line[5])[0:23] + "...")
            # Rosetta version
            if line[6] == '1' or line[6] == 'mini':
                html += '<td id="lw" style="font-size:small;" bgcolor="%s" %s ><i>mini</i><br>%s</td>' % (task_color, link_to_job, task)
            elif line[6] == '0' or line[6] == 'classic':
                html += '<td id="lw" style="font-size:small;" bgcolor="%s" %s ><i>classic</i><br>%s</td>' % (task_color, link_to_job, task)
            # write size of ensemble
            html += '<td id="lw" %s >%s</td>' % (link_to_job, str(line[7]))
        
            html += '</tr>\n'
        
        html += '</table> </div><br> </td>'
        
        return html

###############################################################################################
#                                                                                             #
###############################################################################################

# lets make this nice and modular


    def _defaultParameters(self, ID, jobname, status, hostname, date_submit, date_start, date_end, time_computation, date_expiration, time_expiration, rosetta, error, delete=False, restart=False ):
        # print the first part of the result table  
        
        html = ''
        
        status_html = ''
        if   status == 'in queue':
            status_html = '<font color="orange">in queue</font>'
        elif status == 'active':
            status_html = '<font color="green">active</font>'
        elif status == 'done':
            status_html = '<font color="darkblue">done</font>'
        elif status == 'sample':
            status_html = '<font color="darkblue">done</font>'
        else:
            status_html = '''<font color="FF0000">Error:</font> <a href="https://kortemmelab.ucsf.edu/backrub/wiki/Error#Errors_during_the_simulation">%s</a> <br>
                              We are sorry but your simulation failed. Please referr to 
                              <a href="https://kortemmelab.ucsf.edu/backrub/wiki/Error#Errors_during_the_simulation">Errors during the simulation</a> 
                              in the documentation and contact us via <img src="../images/support_email.png" height="15"> if necessary.
                          ''' % error
        
        html += """
                <tr><td align=right bgcolor="#EEEEFF">Job Name:       </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Status:         </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right></td><td></td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Submitted from: </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Date Submitted: </td><td bgcolor="#EEEEFF">%s</td></tr>
                """ % ( jobname, status_html, hostname, date_submit )
                
        if status == 'active':
            html += '<tr><td align=right bgcolor="#EEEEFF">Started:        </td><td bgcolor="#EEEEFF">%s</td></tr>\n' % ( date_start )
        
        if status == 'done' or status == 'sample' or status == 'error':
            html +="""
                <tr><td align=right bgcolor="#EEEEFF">Started:        </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Ended:          </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Computing time: </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Expires:        </td><td bgcolor="#EEEEFF">%s (%s)</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Binary:         </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right></td><td></td></tr>
                """ % ( date_start, date_end, time_computation, date_expiration, time_expiration, rosetta )
        
        if delete or restart:
            html += '<tr><td align=right></td><td></td></tr>'
            if delete and status == 'in queue':
                html += '<a href="#" onclick="confirm_delete(%s); return false;"><font color="red">DELETE</font></a>' % ID
            if restart and status == 'done':
                html += '<a href="#"><font color="red">RESUBMIT</font></a>'
        
        return html
        
    
    def _show_scores_file(self, cryptID):
        score_file     = '../downloads/%s/scores_overall.txt' % cryptID
        score_file_res = '../downloads/%s/scores_residues.txt' % cryptID
        html = ''
        if os.path.exists( score_file ):
          handle = open(score_file,'r')
          html = '''<tr><td align="left" bgcolor="#FFFCD8">Total scores for the generated structures. Download files:<br>
                                                            <ul><li><a href="../downloads/%s/scores_overall.txt">total scores only</a></li>
                                                                <li><a href="../downloads/%s/scores_detailed.txt">detailed scores</a></li>''' % (cryptID, cryptID)
          if os.path.exists( score_file_res ):
            html += '''                                         <li><a href="%s">detailed scores for residues (also in individual pdb files)</a></li>''' % (score_file_res)
          html += '''                                      </ul>
                        </td>
                      <td bgcolor="#FFFCD8"><a class="blacklink" href="%s"><pre>%s</pre><a></td></tr>
              ''' % ( score_file, join(handle.readlines()[:7], '') + '...\n' )
          handle.close()
          
          # the next 5 lines get the 10 best scoring structures from the overall energies file
          handle = open(score_file,'r')
          import operator
          L = [ line.split() for line in handle if line[0] != '#' and line[0] != 'i' ]
          self.lowest_structs = sorted(L,key=operator.itemgetter(1))[:9]
          handle.close()
        
        return html
    
    def _show_molprobity(self,cryptID):
      
      html = '''<tr><td align="left" bgcolor="#FFFCD8">Analysis of the generated ensemble with Molprobity.
                                                       The red circle denotes the mean, the blue diamond the value from the input structure.
                              <ul><li><a href="../downloads/%s/molprobity_data.txt">Data shown in Plot</a></li>
                                  <li><a href="../downloads/%s/molprobity_raw_output.txt">raw output</a></li></ul></td>
                <td bgcolor="#FFFCD8"><a href="../downloads/%s/molprobity_plot.png">
                                      <img src="../downloads/%s/molprobity_plot.png" alt="image file not available" width="400"></a>
                                      </td></tr>''' % ( cryptID,cryptID,cryptID,cryptID)
      html = '' #todo: this is turned off!
      return html
    
    
    def _showNoMutation(self, status, input_filename, size_of_ensemble, cryptID):

        html = """
                <tr><td align=right bgcolor="#EEEEFF">Task:           </td><td bgcolor="#EEEEFF">Backrub Conformational Ensemble</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Input file:     </td><td bgcolor="#EEEEFF">%s</td></tr> 
                <tr><td align=right bgcolor="#EEEEFF">No. Generated structures: </td><td bgcolor="#EEEEFF">%s</td></tr>
                """ % ( input_filename, size_of_ensemble )
        if status == 'done' or status == 'sample':
          html += '<tr><td align=right></td><td></td></tr>'
          html += self._show_scores_file(cryptID)        
        
          comment = 'Backbone representation of the 10 best scoring structures. The query structure is shown in red.'
          html += self._showApplet4MultipleFiles( comment, self._getPDBfiles(input_filename, cryptID, 'low'))
          html += self._show_molprobity( cryptID )
          
        return html


    
    def _showPointMutation(self, status, cryptID, input_filename, size_of_ensemble, chain, resid, newaa):
        
        html = """
                <tr><td align=right bgcolor="#EEEEFF">Task:           </td><td bgcolor="#EEEEFF">Point Mutation</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Input file:     </td><td bgcolor="#EEEEFF">%s</td></tr> 
                <tr><td align=right bgcolor="#EEEEFF">No. Generated structures: </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Parameters:    </td><td bgcolor="#EEEEFF">Chain: %s<br>Residue: %s<br>Mutation: %s</td></tr>
                """ % ( input_filename, size_of_ensemble, chain, resid, newaa )
                
        if status == 'done' or status == 'sample':
          html += '<tr><td align=right></td><td></td></tr>'
          html += self._show_scores_file(cryptID)
          comment = 'Backbone representation of up to 10 of the best scoring structures. The query structure is shown in red, the mutated residue is shown as sticks representation.'
        
          html += self._showApplet4MultipleFiles( comment, self._getPDBfiles(input_filename, cryptID, 'low'), mutation_res=resid, mutation_chain=chain )
          html += self._show_molprobity( cryptID )
          
        return html
    
    def _showMultiplePointMutations(self, status, cryptID, input_filename, size_of_ensemble, chain, resid, newres, radius):
    
        list_chains = [ str(x.strip('\'')) for x in chain.split('-') ]
        list_resids = [ int(x.strip('\'')) for x in resid.split('-') ]
        list_newres = [ x.strip('\'') for x in newres.split('-') ]
        list_radius = [ float(x.strip('\'')) for x in radius.split('-') ]
        
        multiple_mutations_html = ''
        for x in range(len(list_chains)):
            multiple_mutations_html += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % ( x+1, list_chains[x], list_resids[x], list_newres[x], list_radius[x] )
        
        html = """
                <tr><td align=right bgcolor="#EEEEFF">Task:           </td><td bgcolor="#EEEEFF">Multiple Point Mutations</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Input file:     </td><td bgcolor="#EEEEFF">%s</td></tr> 
                <tr><td align=right bgcolor="#EEEEFF">No. Generated structures: </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Parameters:    </td>
                          <td bgcolor="#EEEEFF"><table border="0" rules="rows" style="text-align:center;" align="center"><tr>
                                                <td style="padding-left:10px;padding-right:10px;">Mutation No.</td>
                                                <td style="padding-left:10px;padding-right:10px;">Chain</td>
                                                <td style="padding-left:10px;padding-right:10px;">Residue</td>
                                                <td style="padding-left:10px;padding-right:10px;">Mutation</td>
                                                <td style="padding-left:10px;padding-right:10px;">Radius</td></tr>
                                                %s
                                                </table>
                          </td></tr>
                    """ % ( input_filename, size_of_ensemble, multiple_mutations_html )
        if status == 'done' or status == 'sample':
          html += '<tr><td align=right></td><td></td></tr>'
          html += self._show_scores_file(cryptID)
          comment = 'Backbone representation of up to 10 of the best scoring structures. The query structure is shown in red, the mutated residues are shown as sticks representation.'
        
          html += self._showApplet4MultipleFiles( comment, self._getPDBfiles(input_filename, cryptID, 'low'), mutation_res=list_resids, mutation_chain=list_chains )
          html += self._show_molprobity( cryptID )
          
        return html
    
    def _showComplexMutation(self, status, cryptID, input_filename, size_of_ensemble, mutation_file):
    
        html = """
                <tr><td align=right bgcolor="#EEEEFF">Task:           </td><td bgcolor="#EEEEFF">Complex Mutation</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Input file:     </td><td bgcolor="#EEEEFF">%s</td></tr> 
                <tr><td align=right bgcolor="#EEEEFF">No. Generated structures: </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Parameters:    </td><td bgcolor="#EEEEFF"><pre>%s</pre></td></tr>
                """ % ( input_filename, size_of_ensemble, mutation_file )
                
        if status == 'done' or status == 'sample':
          html += '<tr><td align=right></td><td></td></tr>'
          html += self._show_scores_file(cryptID)
          comment = 'Backbone representation of up to 10 of the best scoring structures. The query structure is shown in red.'
        
          html += self._showApplet4MultipleFiles( comment, self._getPDBfiles(input_filename, cryptID, 'low'))
          html += self._show_molprobity( cryptID )       
        
        return html
    
    
    def _showEnsemble(self, status, cryptID, input_filename, size_of_ensemble, temperature, seq_per_struct, len_of_seg):
        
        html = """
                <tr><td align=right bgcolor="#EEEEFF">Task:           </td><td bgcolor="#EEEEFF">Backrub Ensemble Design</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Input file:     </td><td bgcolor="#EEEEFF">%s</td></tr> 
                <tr><td align=right bgcolor="#EEEEFF">No. Generated structures: </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Parameters:    </td><td bgcolor="#EEEEFF">Temperature: %s<br>Sequences per Structure: %s<br>Length of Segment: %s</td></tr>
                """ % ( input_filename, size_of_ensemble, temperature, seq_per_struct, len_of_seg )
        
        if status == 'done' or status == 'sample':
          html += '<tr><td align=right></td><td></td></tr>'
          
          comment2 = """Structures of the C&alpha; backbone traces of the backrub ensemble.<br>
          [ <a href="../downloads/%s/ensemble.pdb">PDB file</a> ]
          <br><br>Please wait, it may take a few moments to load the C&alpha; trace representation.""" % cryptID
        
          html += self._showApplet4EnsembleFile( comment2, '../downloads/%s/ensemble.pdb' % cryptID, style='backbone' )        
          
          comment1 = """Mean C&alpha; difference distance values of the ensemble mapped onto X-ray structure. 
                        The gradient from red to white to blue corresponds to flexible, intermediate and rigid regions, respectively.<br>
           [ <a href="../downloads/%s/ca_dist_difference_bfactors.pdb">PDB file</a> ]
           <br><br>Please wait, it may take a few moments to load cartoon representation.""" % cryptID
        
          html += self._showApplet4EnsembleFile( comment1, '../downloads/%s/ca_dist_difference_bfactors.pdb' % cryptID, style='cartoon' )
          
          html += """
                <tr><td align="right" bgcolor="#FFFCD8">Mean C&alpha; difference distance values</td>                 
                    <td bgcolor="#FFFCD8"><a href="../downloads/%s/ca_dist_difference_1D_plot.png">
                                          <img src="../downloads/%s/ca_dist_difference_1D_plot.png" alt="image file not available" width="400"></a></td></tr>
              
                <tr><td align="right" bgcolor="#FFFCD8">Pairwise C&alpha; difference distance values [ <a href="../downloads/%s/ca_dist_difference_matrix.dat">matrix file</a> ]</td>                
                    <td bgcolor="#FFFCD8"><a href="../downloads/%s/ca_dist_difference_2D_plot.png">
                                          <img src="../downloads/%s/ca_dist_difference_2D_plot.png" alt="image file not available" width="400"></a></td></tr>
                
                <tr><td align="right" bgcolor="#FFFCD8">Mean RMSD of C&alpha; atoms for individual residues</td>
                    <td bgcolor="#FFFCD8"><a href="../downloads/%s/rmsd_plot.png"><img src="../downloads/%s/rmsd_plot.png" alt="image file not available" width="400"></a></td></tr>                          
                                          
                <tr><td align="center" colspan="2" bgcolor="#FFFCD8">Design results:</td></tr>
                <tr><td align="right" bgcolor="#FFFCD8">Frequency of amino acids for core residues<br><br>
                                                        Sequences [ <a href="../downloads/%s/designs_core.fasta">fasta formated file</a> ]<br>
                                                        Sequence population matrix [ <a href="../downloads/%s/seq_pop_core.txt">matrix file</a> ]</td> 
                    <td bgcolor="#FFFCD8"><a href="../downloads/%s/logo_core.png"><img src="../downloads/%s/logo_core.png" alt="image file not available" width="400"></a><br>
                                          <small>Crooks GE, Hon G, Chandonia JM, Brenner SE, 
                                          <a href="Crooks-2004-GR-WebLogo.pdf"><small>WebLogo: A sequence <br>logo generator</small></a>, 
                                          <em>Genome Research</em>, 14:1188-1190, (2004)</small> [<a href="http://weblogo.berkeley.edu/"><small>website</small></a>]</td></tr>
                
                <tr><td align="right" bgcolor="#FFFCD8">Frequency of amino acids for all residues<br><br>
                                                        Sequences [ <a href="../downloads/%s/designs.fasta">fasta formated file</a> ]<br>
                                                        Sequence population matrix [ <a href="../downloads/%s/seq_pop.txt">matrix file</a> ]</td>
                    <td bgcolor="#FFFCD8"><a href="../downloads/%s/logo.png"><img src="../downloads/%s/logo.png" alt="image file not available" width="400"></a><br>
                                          <small>Crooks GE, Hon G, Chandonia JM, Brenner SE, <a href="Crooks-2004-GR-WebLogo.pdf">
                                          <small>WebLogo: A sequence <br>logo generator</small></a>, <em>Genome Research</em>, 14:1188-1190, (2004)</small> 
                                          [<a href="http://weblogo.berkeley.edu/"><small>website</small></a>]
                    </td></tr>

              
                """ % ( cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID )
        
          html += '<tr><td align=right></td><td></td></tr>'

        return html
    
    def _showSequenceTolerance(self, status, cryptID, input_filename, size_of_ensemble, mini, seqtol_chain1, seqtol_chain2, seqtol_list_1, seqtol_list_2, w1, w2, w3 ):
        
        html = """
              <tr><td align=right bgcolor="#EEEEFF">Task:         </td><td bgcolor="#EEEEFF">Interface Sequence Tolerance Prediction  (Humphris, Kortemme 2008)</td></tr>
              <tr><td align=right bgcolor="#EEEEFF">Input file:   </td><td bgcolor="#EEEEFF">%s</td></tr>
              <tr><td align=right bgcolor="#EEEEFF">No. Generated structures: </td><td bgcolor="#EEEEFF">%s</td></tr>
              <tr><td align=right bgcolor="#EEEEFF">Parameters:   </td>
                  <td bgcolor="#EEEEFF">
                      Partner 1: Chain %s<br>
                      Partner 2: Chain %s<br>
                      Designed residues of Partner 1: %s<br>
                      Designed residues of Partner 2: %s<br>
                      """ % ( input_filename, size_of_ensemble, seqtol_chain1, seqtol_chain2, join(seqtol_list_1,' '), join(seqtol_list_2,' ') )
                      
        # this needs to be ennables IF Colins paper is released
        # if mini == 'mini' or mini == '1':
        #   html += """
        #               Weights (Partner1:Partner2:Interface): (%s:%s:%s)
        #       """ %  (w1, w2, w3 )
              
        html += '</td></tr>'
              
        
        input_id = input_filename[:-4] # filename without suffix
        if status == 'done' or status == 'sample':
            html += '<tr><td align=right></td><td></td></tr>'
            
            if mini == 'mini' or mini == '1':
              list_pdb_files = ['../downloads/%s/%s_0.pdb' % (cryptID, input_id) ]
              list_pdb_files.extend( [ '../downloads/%s/%s_0_%04.i_low_ms_0000.pdb' % (cryptID, input_id, i) for i in range(1,size_of_ensemble+1) ] )
            else:
              list_pdb_files = ['../downloads/%s/%s.pdb' % (cryptID, input_id) ]
              list_files = os.listdir( self.download_dir+'/'+cryptID )
              list_files.sort()
              list_all_pdbs = grep('BR%slow_[0-9][0-9][0-9][0-9]_[A-Z]*\.pdb' % (input_id) ,list_files)
              # we don't know at this point what the best scoring structures are. for each backrub structure, let's take the first we can find.
              list_structure_shown = []
              seq_before = ''
              for pdb_fn in list_all_pdbs:
                if seq_before != pdb_fn.split('_')[1]:
                  list_structure_shown.append(pdb_fn)
                seq_before = pdb_fn.split('_')[1]
                
              list_pdb_files.extend( [ '../downloads/%s/%s' % ( cryptID, fn_pdb ) for fn_pdb in list_structure_shown ] )
              
            comment1 = """Backbone representation of the best scoring designs for 10 different initial backrub structures.<br>The query structure is shown in red. The designed residues are shown in balls-and-stick representation."""
            
            designed_chains = [seqtol_chain1 for res in seqtol_list_1] + [seqtol_chain2 for res in seqtol_list_2]
            designed_res    = seqtol_list_1 + seqtol_list_2
            
            html += self._showApplet4MultipleFiles(comment1, list_pdb_files[:10], mutation_res=designed_res , mutation_chain=designed_chains) # only the first 10 structures are shown
            
            if mini == 'mini' or mini == '1':        
              html += '''<tr><td align="left" bgcolor="#FFFCD8">Predicted sequence tolerance of the mutated residues.<br>Download corresponding <a href="../downloads/%s/tolerance_sequences.fasta">FASTA file</a>.</td>
                             <td bgcolor="#FFFCD8"><a href="../downloads/%s/tolerance_motif.png">
                                                   <img src="../downloads/%s/tolerance_motif.png" alt="image file not available" width="400"></a><br>
                                                   <small>Crooks GE, Hon G, Chandonia JM, Brenner SE, 
                                                   <a href="Crooks-2004-GR-WebLogo.pdf"><small>WebLogo: A sequence <br>logo generator</small></a>, 
                                                   <em>Genome Research</em>, 14:1188-1190, (2004)</small> [<a href="http://weblogo.berkeley.edu/"><small>website</small></a>]
                             </td></tr> ''' % (cryptID, cryptID, cryptID)
                           
            html += '''<tr><td align="left" bgcolor="#FFFCD8">Individual boxplots of the predicted frequencies at each mutated site.<br>
                              Download <a href="../downloads/%s/tolerance_pwm.txt">weight matrix</a> or file with all plots as 
                              <a href="../downloads/%s/tolerance_boxplot.png">PNG</a>, <a href="../downloads/%s/tolerance_boxplot.pdf">PDF</a>.<br>
                              </td>
                           <td bgcolor="#FFFCD8">
                    ''' % ( cryptID, cryptID, cryptID )
                    
                    # To rerun the analysis we provide the <a href="../downloads/specificity.R">R-script</a> that was used to analyze this data. 
                    # A <a href="../wiki/SequenceTolerancePrediction" target="_blank">tutorial</a> on how to use the R-script can be found on 
                    # the <a href="../wiki/" target="_blank">wiki</a>.
            
            for resid in seqtol_list_1:
              html += '''<a href="../downloads/%s/tolerance_boxplot_%s%s.png"><img src="../downloads/%s/tolerance_boxplot_%s%s.png" alt="image file not available" width="400"></a><br>
                    ''' % ( cryptID, seqtol_chain1, resid, cryptID, seqtol_chain1, resid )
            for resid in seqtol_list_2:
              html += '''<a href="../downloads/%s/tolerance_boxplot_%s%s.png"><img src="../downloads/%s/tolerance_boxplot_%s%s.png" alt="image file not available" width="400"></a><br>
                    ''' % ( cryptID, seqtol_chain2, resid, cryptID, seqtol_chain2, resid )
            
            html += self._show_molprobity( cryptID )
            
            html +="</td></tr>"
        return html      
    
    def _showSequenceToleranceSK(self, status, cryptID, input_filename, size_of_ensemble, seqtol_parameter):

        html = """
              <tr><td align=right bgcolor="#EEEEFF">Task:         </td><td bgcolor="#EEEEFF">Interface Sequence Tolerance Prediction (Smith, Kortemme 2010)</td></tr>
              <tr><td align=right bgcolor="#EEEEFF">Input file:   </td><td bgcolor="#EEEEFF">%s</td></tr>
              <tr><td align=right bgcolor="#EEEEFF">No. Generated structures: </td><td bgcolor="#EEEEFF">%s</td></tr>
              <tr><td align=right valign=top bgcolor="#EEEEFF">Parameters:   </td>
                  <td bgcolor="#EEEEFF">
                      """ % ( input_filename, size_of_ensemble)
                
        active = []    
        activeList = []
        maxActive = -1
        
        # Note:  We use get here rather than direct dictionary access as we choose not to 
        #        store empty keys in the parameter to save space 
        for i in range(0, ROSETTAWEB_max_seqtol_SK_chains):
            partner = seqtol_parameter.get("Partner%d" % i)
            if partner:
                active.append(True)
                activeList.append(i)
                if i > maxActive:
                    maxActive = i
                html += 'Partner %d: Chain %s<br>' % (i + 1, partner)
                plist = seqtol_parameter.get("Premutated%d" % i)
                if plist:
                    html += '<table><tr><td>&nbsp;&nbsp;</td><td><i>Premutated residues at positions:</i></td><td></td><td>'
                    for k,v in sorted(plist.items()):
                        html += '%s (%s) ' % (k, ROSETTAWEB_SK_AAinv[v])
                    html += '</td></tr></table>'
                dlist = seqtol_parameter.get("Designed%d" % i)
                if dlist:
                    html += '<table><tr><td>&nbsp;&nbsp;</td><td><i>Designed residues at positions:</i></td><td></td><td> %s</td></tr></table>' % (join(dlist.keys(),' '))
            else:
                active.append(False)
        
        html += '<br>Boltzmann factor: %s' % (seqtol_parameter["kT"])
        
        html += """
                    <br><br>
                    Score Reweighting<br>
                    <table><tr>
                      <td> 
                        <table><thead>
                            <tr bgcolor="#828282" style="color:white;">
                            <td bgcolor="#EEEEFF"></td>
                            <td>Self Energy (k<sub>_</sub>)</td>"""

        for i in range(0, ROSETTAWEB_max_seqtol_SK_chains):
            if active[i] and i != maxActive:
                html += "<td>k<sub>P<sub>%s</sub></sub>_</td>" % (seqtol_parameter.get("Partner%d" % i))
        
        html += "</thead></tr><tbody bgcolor='#F4F4FF'>"
    
        for i in range(0, ROSETTAWEB_max_seqtol_SK_chains):
            if active[i]:
                html += """
                        <tr align="left" border=1>                    
                              <td bgcolor="#828282" style="color:white; align="left">%s</td>
                              <td>%s</td>""" % (seqtol_parameter.get("Partner%d" % i), seqtol_parameter["kP%dP%d" % (i, i)])
                for j in activeList:
                    if j < i:
                        html += "<td>%s</td>" % seqtol_parameter["kP%dP%d" % (j, i)]
                    elif j != maxActive:
                        html += "<td bgcolor='#EEEEFF'></td>"
                html += "</tr>"

        html += "</tbody></table></td></tr></table>" 
        html += "</td></tr>"
        
        
        
        #todo: if status == 'done' or status == 'sample':
        input_id = input_filename[:-4] # filename without suffix
        if status == 'done' or status == 'sample':
            html += '<tr><td align=right></td><td></td></tr>'
            
            list_pdb_files = ['../downloads/%s/%s_0.pdb' % (cryptID, input_id) ]
            list_pdb_files.extend( [ '../downloads/%s/%s_0_%04.i_low.pdb' % (cryptID, input_id, i) for i in range(1,size_of_ensemble+1) ] )
            
            comment1 = """Backbone representation of the best scoring designs for 10 different initial backrub structures.<br>The query structure is shown in red. The designed residues are shown in balls-and-stick representation."""
             
            designed_chains = []
            designed_res = []
            for i in range(0, ROSETTAWEB_max_seqtol_SK_chains): 
                chain = seqtol_parameter.get("Partner%d" % i)
                if chain:
                    reslist = seqtol_parameter.get("Designed%d" % i)
                    if reslist:
                        designed_chains += [chain for res in reslist.keys()]
                        designed_res += reslist
             
            html += self._showApplet4MultipleFiles(comment1, list_pdb_files[:10], mutation_res=designed_res , mutation_chain=designed_chains) # only the first 10 structures are shown
            
            #todo: text
            html += '''<tr><td align="left" bgcolor="#FFFCD8">A ranked table of amino acid types for each position.<br>
                              Download the table as 
                              <a href="../downloads/%s/tolerance_seqrank.png">PNG</a>, <a href="../downloads/%s/tolerance_seqrank.pdf">PDF</a>.<br>
                              </td>
                           <td bgcolor="#FFFCD8">
                    ''' % ( cryptID, cryptID )
                    
                    # To rerun the analysis we provide the <a href="../downloads/specificity.R">R-script</a> that was used to analyze this data. 
                    # A <a href="../wiki/SequenceTolerancePrediction" target="_blank">tutorial</a> on how to use the R-script can be found on 
                    # the <a href="../wiki/" target="_blank">wiki</a>.
            
            html += '''<a href="../downloads/%s/tolerance_seqrank.png"><img src="../downloads/%s/tolerance_seqrank.png" alt="image file not available" width="400"></a><br>
                    ''' % ( cryptID, cryptID )
                            
            html +="</td></tr>"
                                       
            html += '''<tr><td align="left" bgcolor="#FFFCD8">Individual boxplots of the predicted frequencies at each mutated site.<br>
                              Download <a href="../downloads/%s/tolerance_pwm.txt">weight matrix</a> or file with all plots as 
                              <a href="../downloads/%s/tolerance_boxplot.png">PNG</a>, <a href="../downloads/%s/tolerance_boxplot.pdf">PDF</a>.<br>
                              </td>
                           <td bgcolor="#FFFCD8">
                    ''' % ( cryptID, cryptID, cryptID )
                    
                    # To rerun the analysis we provide the <a href="../downloads/specificity.R">R-script</a> that was used to analyze this data. 
                    # A <a href="../wiki/SequenceTolerancePrediction" target="_blank">tutorial</a> on how to use the R-script can be found on 
                    # the <a href="../wiki/" target="_blank">wiki</a>.
            
            for (chain, resid) in zip(designed_chains, designed_res):
              html += '''<a href="../downloads/%s/tolerance_boxplot_%s%s.png"><img src="../downloads/%s/tolerance_boxplot_%s%s.png" alt="image file not available" width="400"></a><br>
                    ''' % ( cryptID, chain, resid, cryptID, chain, resid )
                            
            html +="</td></tr>"
            
                        #todo: There's a lot of duplicated code between the protocols here and I specialized the image size below.
            html += '''<tr><td align="left" bgcolor="#FFFCD8">Predicted sequence tolerance of the mutated residues.<br>Download corresponding <a href="../downloads/%s/tolerance_sequences.fasta">FASTA file</a>.</td>
                             <td align="center" bgcolor="#FFFCD8"><a href="../downloads/%s/tolerance_motif.png">
                                                   <img height="250" src="../downloads/%s/tolerance_motif.png" alt="image file not available" ></a><br>
                                                   <small>Crooks GE, Hon G, Chandonia JM, Brenner SE, 
                                                   <a href="Crooks-2004-GR-WebLogo.pdf"><small>WebLogo: A sequence <br>logo generator</small></a>, 
                                                   <em>Genome Research</em>, 14:1188-1190, (2004)</small> [<a href="http://weblogo.berkeley.edu/"><small>website</small></a>]
                             </td></tr> ''' % (cryptID, cryptID, cryptID)

        return html  
    
    def _showDownloadLinks(self, status, extended, cryptID, jobnumber):
    
        html = ''

        if status == "done" or status == 'sample' or status == 'error':
            html += '<tr><td align=right bgcolor="#B7FFE0"><b>Results</b>:</td><td bgcolor="#B7FFE0">'
            
            if os.path.exists( '%s%s/' % (self.download_dir, cryptID) ): # I could also remove this since rosettadatadir.py is taking care of this
                if status == 'error':
                    html += 'Please follow <a href="../downloads/%s/">this link</a> to see which files were created.' % cryptID
                else:
                    html += '''<A href="%s?query=datadir&job=%s"><b>View</b></A> individual files.
                                <A href="../downloads/%s/data_%s.zip"><b>Download</b></A> all results (zip).''' % ( self.script_filename, cryptID, cryptID, jobnumber )
                # if extended:
                #     html += ', <A href="../downloads/%s/input.resfile">view Resfile</A>, <A href="../downloads/%s/stdout_%s.dat">view raw output</A>' % ( cryptID, cryptID, jobnumber )
            else:
                html += 'no data'
        html += '</td>\n</tr><tr><td align=right></td><td></td></tr>'
        
        return html
    
    def _getPDBfiles(self, input_filename, cryptID, key):
        
        dir_results = '%s%s/' % (self.download_dir, cryptID)
        
        if os.path.exists( dir_results ):
      
          list_files = os.listdir( dir_results )
          list_pdb_files = ['../downloads/%s/' % cryptID + input_filename]
          
          list_id_lowest_structs = [ x[0] for x in self.lowest_structs ]
          
          for filename in list_files:
            if filename.find(key) != -1:
              if self.lowest_structs != []: # if the list contains anything
                if filename[-8:-4] in list_id_lowest_structs or filename[-12:-9] : # if the filename is one of the 10 lowest structures, use it
                  list_pdb_files.append('../downloads/%s/%s' % (cryptID, filename))
              else:
                list_pdb_files.append('../downloads/%s/%s' % (cryptID, filename))
          list_pdb_files.sort()
          
          for pdb_file in list_pdb_files:
            pdb_file_path = pdb_file.replace('../downloads', self.download_dir) # build absolute path to the file
            if not os.path.exists(pdb_file_path + '.gz'):
              f_in = open(pdb_file_path, 'rb')
              f_out = gzip.open(pdb_file_path + '.gz', 'wb')
              f_out.writelines(f_in)
              f_out.close()
              f_in.close()
            pdb_file += '.gz'
          
          return list_pdb_files
        else:
            return None
    
    # This function creates the HTML for the Job Info page accessed by clicking a job in the queue
    def jobinfo(self, parameter):
        """this function decides what _showFunction to pick"""
        
        self.html_refs = '''<P>%(Lauck)s</P>
                         ''' % self.refs
        
        # SELECT ID, Status, Email, Date, StartDate, EndDate, Notes, Errors, Mini, PDBComplexFile, EnsembleSize, Host, KeepOutput, task, UserID, 
        # PM_chain, PM_resid, PM_newres, PM_radius, ENS_temperature, ENS_num_design_per_struct, ENS_segment_length
        
        # DATE_ADD(EndDate, INTERVAL 8 DAY), TIMEDIFF(DATE_ADD(EndDate, INTERVAL 7 DAY), NOW()), TIMEDIFF(EndDate, StartDate)
        
        status  = ''
        html    = ''
        rosetta = ''
        
        if   int(parameter['Status']) == 0:
            status = 'in queue'
        elif int(parameter['Status']) == 1:
            status = 'active'
        elif int(parameter['Status']) == 2:
            status = 'done'
        elif int(parameter['Status']) == 4:
            status = 'error'    
        elif int(parameter['Status']) == 5:
            status = 'sample'
                        
        if parameter['Mini'] == 'mini' or parameter['Mini'] == '1':
            parameter['Mini'] = 'Rosetta v.3 (mini)'
        elif parameter['Mini'] == 'classic' or parameter['Mini'] == '0':
            parameter['Mini'] = 'Rosetta v.2 (classic)'
        else:
            parameter['Mini'] = '???'            
        
        html += """<td align="center"><H1 class="title">Job %s</H1> """ % ( parameter['ID'] )
        
        html += '<div id="jobinfo">'
        html += '<table border=0 cellpadding=2 cellspacing=1>\n'
        
        html += self._defaultParameters( parameter['ID'], parameter['Notes'], status, parameter['Host'], parameter['Date'], parameter['StartDate'], 
                                    parameter['EndDate'], parameter['time_computation'], parameter['date_expiration'], parameter['time_expiration'], parameter['Mini'], parameter['Errors'], delete=False, restart=False )
        
        
        if True: #str(parameter['Errors']).strip() in ['', 'Postprocessing'] or parameter['Errors'] == None:
            #todo: Clean up the logic here - why is there two possibilities? maybe old legacy DB records in which case update the DB
            html += self._showDownloadLinks(status, parameter['KeepOutput'], parameter['cryptID'], parameter['ID'])
            
            if parameter['task'] == '0' or parameter['task'] == 'no_mutation':
                html += self._showNoMutation( status, parameter['PDBComplexFile'], parameter['EnsembleSize'], parameter['cryptID'] )            
                
            elif parameter['task'] == '1' or parameter['task'] == 'point_mutation':
                html += self._showPointMutation( status, parameter['cryptID'],  parameter['PDBComplexFile'], parameter['EnsembleSize'], 
                                                 parameter['PM_chain'], parameter['PM_resid'], parameter['PM_newres'])
                
            elif parameter['task'] == '3' or parameter['task'] == 'multiple_mutation':
                html += self._showMultiplePointMutations( status, parameter['cryptID'], parameter['PDBComplexFile'], parameter['EnsembleSize'], parameter['PM_chain'], 
                                                          parameter['PM_resid'], parameter['PM_newres'], parameter['PM_radius'])
                
            elif parameter['task'] == '2' or parameter['task'] == 'upload_mutation':
                html += self._showComplexMutation( status, parameter['cryptID'], parameter['PDBComplexFile'], parameter['EnsembleSize'], parameter['Mutations'])
                
            elif parameter['task'] == '4' or parameter['task'] == 'ensemble':
                html += self._showEnsemble( status, parameter['cryptID'], parameter['PDBComplexFile'], parameter['EnsembleSize'], parameter['ENS_temperature'], 
                                            parameter['ENS_num_designs_per_struct'], parameter['ENS_segment_length'] )
                                            
            elif parameter['task'] == 'sequence_tolerance':
                seqtol_parameter = pickle.loads(parameter['seqtol_parameter'])
                html += self._showSequenceTolerance( status, parameter['cryptID'], parameter['PDBComplexFile'], parameter['EnsembleSize'], parameter['Mini'],
                                                     seqtol_parameter['seqtol_chain1'], seqtol_parameter['seqtol_chain2'], 
                                                     seqtol_parameter['seqtol_list_1'], seqtol_parameter['seqtol_list_2'],
                                                     seqtol_parameter['seqtol_weight_chain1'], seqtol_parameter['seqtol_weight_chain2'], seqtol_parameter['seqtol_weight_interface'] )

            elif parameter['task'] == 'sequence_tolerance_SK':
                seqtol_parameter = pickle.loads(parameter['seqtol_parameter'])
                html += self._showSequenceToleranceSK( status, parameter['cryptID'], parameter['PDBComplexFile'], parameter['EnsembleSize'], seqtol_parameter)
                
        html += '</table><br></div></td>\n'
        
        return html


    def _showApplet4MultipleFiles(self, comment, list_pdb_files, mutation_res=None, mutation_chain=None):
        """This shows the Jmol applet for an ensemble of structures with their point mutation(s)"""
        
        # todo: set these values in rwebhelper
        # jmol command to load files
        if list_pdb_files != None:
            jmol_cmd = ' "load %s; color red; cpk off; wireframe off; backbone 0.2;" +\n' % (list_pdb_files[0] ) #, list_pdb_files[0].split('/')[-1].split('.')[0])
            for pdb in list_pdb_files[1:11]:
                jmol_cmd += ' "load APPEND %s;" +\n' % (pdb)
            jmol_cmd += ' "cpk off; wireframe off; backbone 0.2;" +'
                        
            # jmol command to show mutation as balls'n'stick
            jmol_cmd_mutation = ''
            if mutation_res != None and mutation_chain != None: 
                if type(mutation_res) == type(''):
                    jmol_cmd_mutation = 'select %s:%s; cartoon off; backbone on; wireframe 0.3; ' % ( mutation_res, mutation_chain )
                elif type(mutation_res) == type([]):
                    for i in range(len(mutation_res)):
                        jmol_cmd_mutation += 'select %s:%s; cartoon off; backbone on; wireframe 0.3; ' % (mutation_res[i], mutation_chain[i])
            
            # html code
            html = """
                    <form>
                     <tr><td align="justify" bgcolor="#FFFCD8">%s<br><br>Please wait, it may take a few moments to load the C&alpha; trace representation.</td>
                         <td bgcolor="#FFFCD8">
                            <script type="text/javascript">
                              jmolInitialize("../../jmol"); 
                              jmolApplet(400, "set appendNew false;" + %s "%s frame all;" ); 
                            </script><br>
                            <small>Jmol: an open-source Java viewer for chemical structures in 3D.</small><br><a href=http://www.jmol.org/><small>www.jmol.org</small></a>
                         </td>
                    </tr>
                    </form>
                    """ % ( comment, jmol_cmd, jmol_cmd_mutation )
        else:
            html = '<tr><td align="center" bgcolor="#FFFCD8" colspan=2>no structures found</td></tr>'
                
        return html


    def _showApplet4EnsembleFile(self, comment, filename, style=None ):
        """shows a Jmol applet for a file that contains several pdb structures"""
        
        jmol_style = 'cartoon'
        if style != None:
            if style == 'backbone':
                jmol_style = 'backbone 0.2; frame all; color green;'
            elif style == 'cartoon':
                jmol_style = 'cartoon; color cartoon temperature;'
            
        html = """
            <form>
             <tr><td align="justify" bgcolor="#FFFCD8">%s</td>
                 <td bgcolor="#FFFCD8">
                    <script type="text/javascript">
                      jmolInitialize("../../jmol"); 
                      jmolApplet(400, "load %s; cpk off; wireframe off; %s");
                    </script><br>
                    <small>Jmol: an open-source Java viewer for chemical structures in 3D.</small><br><a href=http://www.jmol.org/><small>www.jmol.org</small></a>
                  </td>
            </form>""" % ( comment, filename, jmol_style )
       
        return html

###############################################################################################
#                                                                                             #
###############################################################################################

    def login(self, message='', username='', login_disabled=False):
        
        message_html = ''
        if message != '':
            message_html = '<tr><td colspan="3" align="right"><P style="text-align:center; color:red;">%s</P></td></tr>' % ( message )
        disabled = ''
        if login_disabled:
            disabled = 'disabled'
        
        self.html_refs = '''<P>%(Lauck)s</P>
                            <P>[<a name="ref1">1</a>] %(Davis)s</P>
                            <P>[<a name="ref2">2</a>] %(Smith)s</P>
                            <P>[<a name="ref3">3</a>] %(Friedland)s</P>
                            <P>[<a name="ref4">4</a>] %(Humphris)s</P>
                            <P>[<a name="ref5">5</a>] %(Smith2)s</P>
                            ''' % self.refs
        
        html = """<td align="center">
                  <H1 class="title">Welcome to RosettaBackrub</A> </H1> 
                    <P>
                    This is the flexible backbone protein structure modeling and design server of the Kortemme Lab. 
                    The server utilizes the \"<b>backrub</b>\" method, first described by Davis et al<a href="#ref1"><sup id="ref">1</sup></a>, 
                    for flexible protein backbone modeling implemented in <a href="/backrub/wiki/Rosetta">Rosetta</a><a href="#ref2"><sup id="ref">2,</sup></a><a href="#ref3"><sup id="ref">3,</sup></a><a href="#ref4"><sup id="ref">4,</sup></a><a href="#ref5"><sup id="ref">5</sup></a>.</P>
                    <P>The server <b>input</b> is a protein structure (a single protein or a protein-protein complex) uploaded by the user and a choice of parameters and modeling method: 
                    prediction of point mutant structures, creation of conformational ensembles given the input protein structure and flexible backbone design.
                    The server <b>output</b>, dependent on the application, consists of: structures of point mutants<a href="#ref2"><sup id="ref">2</sup></a> and their Rosetta force field scores, 
                    near-native structural ensembles of protein backbone conformations<a href="#ref2"><sup id="ref">2,</sup></a><a href="#ref3"><sup id="ref">3</sup></a> 
                    and designed sequences using flexible backbone computational protein design<a href="#ref4"><sup id="ref">4</sup></a>.</P>
                    <P>For a <b>tutorial</b> on how to submit a job and interpret the results see the <a href="/backrub/wiki/" target="_blank">documentation</a>.
            Please also check for <a href="/backrub/wiki/" target="_blank">current announcements</a>. 
                    </P>

                  <div id="login_box">
                    <form name="loginform" method="post" action="%s">
                    <P style="text-align:justify;">
                    You are not required to register for this service, but you can choose to do so. 
                    If you want to proceed without registering click on \"Guest access\", otherwise enter your login and password.
                    <A href="%s?query=register">Click here</A>, if you wish to register.</P>
                    <table border=0 cellpadding=5 cellspacing=0>
                    %s
                    <tr><td valign="middle" align="center" style="color:red;">
                          <input type="button" name="guest_access" value="Guest Access" onClick="document.loginform.myUserName.value='guest';  document.loginform.myPassword.value=''; document.loginform.submit(); return true;"><br><br>
                          No password required.
                    </td><td width="100"></td><td>
                      <table border=0 cellpadding=5 cellspacing=0>
                          <tr><td align="right">Username: </td><td><input type=text name=myUserName value="%s">    </td></tr>
                          <tr><td align="right">Password: </td><td><input type=password name=myPassword value="" %s></td></tr>
                          <tr><td></td>
                      <td align="center">
                      <input type=hidden name=query  value="login">
                      <input type=hidden name=login  value="login">
                      <input type=submit name=Submit value="Login" %s>
                      </td></tr>
                      </table>
                    </td></tr></table>
                    </form>                    
                    Forgot your password? <A href="%s?query=oops">Click here</A> .
                    <br>
                    </div>
                   <td>""" % ( self.script_filename, self.script_filename, message_html, username, disabled, disabled, self.script_filename )

        return html

    def loggedIn(self, username):
        self.username = username
        html = """ <td align="center">You have successfully logged in as %s. <br> <br> \n 
                   From here you can proceed to the <A href="%s?query=submit">submission page</A> to <A href="%s?query=submit">submit a new job</A> <br>
                   or navigate to the <A href="%s?query=queue">queue</A> to check for submitted, running or finished jobs. <br><br> </td>
                   """ % ( username, self.script_filename, self.script_filename, self.script_filename )
        return html



    def logout(self, username):
        self.username = ''
        html = """<td align="center"> 
                <H1 class="title">Logout</H1>
                You (%s) have successfully logged out. Thank you for using this server. 
                <br><br> 
              </td>""" % ( username )
        return html


      
###############################################################################################
#                                                                                             #
###############################################################################################
    
    def sendPassword(self, message):
    
        message_html = ''
        if message != '':
            message_html = '<P style="text-align:center; color:red;">%s</P>' % ( message )
    
        html = """<TD align="center">
                  <H1 class="title">Forgot your password?</H1>
                  %s
                  <p style="text-align:center;">Enter your email address below to have a new password emailed to you.</p>
                  <form name="myForm" method="post" onsubmit="return ValidateFormEmail();">
                  <table border=0 cellpadding=3 cellspacing=0>
                    <tr><td>
                      Email Address: <br><input type="text" maxlength=100 name="Email" value="" size=20>
                    </td></tr>
                  </table>
                  <br>
                  <input type=hidden name="query" value="oops">
                  <input type=submit value="Submit">
                  </form></td>""" % ( message_html )
        return html
      
    def passwordUpdated(self, message):
        html = """<td align="center">
                  <H1 class="title">Password Updated</H1>
                    <P style="text-align:center;">%s</P>
                    </td>""" % message
                  
        return html

###############################################################################################
#                                                                                             #
###############################################################################################

    def help(self):
        html = '<td>'
        html += open("doc.html", 'r').read() # '<a href="../wiki/">doc</a>' #
        html += '</td>'     
        return html
        
        
    def terms_of_service(self):
        html = '<td align="center">'
        # terms of service html can be found in this file
        html += open("terms_of_service.html", 'r').read()
        html += '</td>'
        return html    
  
###############################################################################################
#                                                                                             #
###############################################################################################





if __name__ == "__main__":
    """here goes our testcode"""

    from cStringIO import StringIO

    s = sys.stdout

    s.write("Content-type: text/html\n\n\n")

    test_html = RosettaHTML('albana.ucsf.edu', 'Structure Prediction Backrub', 'rosettahtml.py', 'DFTBA', comment='this is just a test', contact_name='Tanja Kortemme')

    #html_content = test_html.index() 
    html_content = test_html.submit()
    #html_content = test_html.register( error='You broke everything', update=True )
    #html_content = test_html.login()  
    #html_content += '</tr><tr>'  
    #html_content += test_html.logout('DFTBA')
    #html_content = test_html.sendPassword()
    
    s.write( test_html.main(html_content) )

    s.close()


