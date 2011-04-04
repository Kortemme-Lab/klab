#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-

########################################
# This class produces HTML code
########################################

#

import sys, os
sys.path.insert(0, "../common/")
import cgi
import cgitb; cgitb.enable()
from string import join
from string import find
import pickle
import gzip

from rwebhelper import *
from RosettaProtocols import *

class RosettaHTML(object):

    server = {}
    
    def __init__(self, server_url, server_title, script_filename, contact_name, download_dir,
                  username='', comment= '', warning=''):
        
        # Calls the init function of object (important)
        super(RosettaHTML, self).__init__()
        
        self.server_url      = server_url
        self.server_title    = server_title
        self.script_filename = script_filename
        self.contact_name    = contact_name
        self.download_dir    = download_dir
        
        self.username        = username
        self.comment         = comment
        self.warning         = warning
        
        self.lowest_structs  = []
        self.html_refs       = ''
        self.refs = References()
                            
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
        self.WebLogoText = '''
            <small>Crooks GE, Hon G, Chandonia JM, Brenner SE,                                           
            <a href="Crooks-2004-GR-WebLogo.pdf"><small>WebLogo: A sequence <br>logo generator</small></a>,                                           
            <em>Genome Research</em>, 14:1188-1190, (2004)</small>
            [<a href="http://weblogo.berkeley.edu/"><small>website</small></a>]'''
    
        
    def main(self, CONTENT='This server is made of awesome sauce.', site='', query='' ):
        html = []
        html.append("""
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
                """ % (self.server_title, site))
        
        # Add the Javascript constants
        self._setupJavascript()
        html.append(join(self.JS,"\n"))
                    
        html.append("""        <script src="/backrub/jscripts.js" type="text/javascript"></script>
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
                            self._showFooter() ))

        return join(html, "")

##############################################
# API functions follow below, one per section.
##############################################

###############################################################################################
# index()                                                                                     #
###############################################################################################

    def index(self, message='', username='', login_disabled=False):
        return self.login(message=message, username=username, login_disabled=login_disabled)

###############################################################################################
# submit()
###############################################################################################

    def submit(self, jobname='', errors=None, activeProtocol = (-1, -1), UploadedPDB='', StoredPDB='', listOfChains = [], MiniVersion='' ):
          # this function uses javascript functions from jscript.js
            # if you change the application tabler here, please make sure to change jscript.js accordingly
            # calling the function with parameters will load those into the form. #not implemented yet
        if activeProtocol[0] != -1 and activeProtocol[1] != -1:
            JSCommand = 'HREF="javascript:void(0)" onclick="changeApplication(%d, %d, 0, 2)"' % (int(activeProtocol[0]), int(activeProtocol[1])) 
        else:
            JSCommand = 'HREF="javascript:history.go(-1)"'   
        
        if errors:
            errors = '''<div align="center" style="width:300pt; background:lightgrey; margin:15pt; padding:15px; border-color:black; border-style:solid; border-width:2px;">
                          Your job could not be submitted:<br><font style="color:red;"><b>%s</b></font><br>
                          <a href="https://kortemmelab.ucsf.edu/backrub/wiki/Error#Errors_during_submission" target="_blank">More Information</a>. <a %s>Return</a> to the form. 
                       </div>''' % (join(errors, '<br>'), JSCommand)           
        else:
            errors = ''
             
        self.tooltips.update({'username':self.username, 'jobname':jobname, 'script':self.script_filename, 'errors':errors})
        
        # <li id="ab1">
        #   [ <A href="/alascan/" class="nav" target="_blank">Interface Alanine Scanning</A> ]<br><center><small>opens in a new window</small></center>
        # </li>
        
        self._referenceAll()
        
        # This string holds options for comboboxes to select chains
        # When there is only one, we fill in the default choice
        numChainsAvailable = len(listOfChains)
        chainOptions = ""
        if numChainsAvailable == 1:
            c = listOfChains[0]
            chainOptions = '''<option value="%s" selected>%s</option> 
                              <option value="invalid">Select a chain</option>''' % (c, c) 
        else:
            chainOptions = []
            chainOptions.append('''<option value="invalid" selected>Select a chain</option>''') 
            for c in listOfChains:
                chainOptions.append('''<option value="%s">%s</option>''' % (c, c))
            chainOptions = join(chainOptions, "")
        
        # This string holds options for comboboxes to select chains
        # When there is only one, we fill in the default choice
        aminoAcidOptions = []
        aminoAcidOptions.append('''<option value="" selected>Select an amino acid</option>''')
        for j in sorted(ROSETTAWEB_SK_AA.keys()):
            aminoAcidOptions.append(''' <option value="%s">%s</option> ''' % (j, j))
        aminoAcidOptions = join(aminoAcidOptions, "")

        postscripts = []
        html = []
        html.append('''<td align="center">
    <H1 class="title">Submit a new job</H1>
    %(errors)s
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
              <A href="javascript:void(0)" class="nav" onclick="showMenu('0'); "><img src="../images/qm_s.png" border="0" title="%(tt_click)s"> Point Mutation</A><br>
              <font style="font-size:8pt">[ <a href="http://dx.doi.org/10.1016/j.jmb.2008.05.023" style="font-size: 8pt">Smith and Kortemme, 2008</a> ]</font>            
              <p id="menu_1" style="text-align:left; margin:0px;">
                  <table style="border:0px; padding:0px; margin:0px;">
                  <tr><td width="30" style="text-align:right;">&#8680;</td><td><a href="javascript:void(0)" onclick="changeApplication(0, 0); ">One mutation</a></td></tr>
                  <tr><td width="30" style="text-align:right;">&#8680;</td><td><a href="javascript:void(0)" onclick="changeApplication(0, 1); ">Multiple mutations</a></td></tr>
                  <!-- tr><td width="10" style="text-align:right;">&#8680;</td><td><a href="javascript:void(0)" onclick="changeApplication(0, 2); ">Upload List</td></tr -->
                  </table>
              </p>
            </li>
            <li id="ab3">
              <A href="javascript:void(0)" class="nav" onclick="showMenu('1'); "><img src="../images/qm_s.png" border="0" title="%(tt_click)s"> Backrub Ensembles</A>
              <p id="menu_2" style="text-align:right; margin:0px;">
                  <table style="border:0px; padding:0px; margin:0px;">
                  <tr><td width="30" style="text-align:right;">&#8680;</td>
                      <td><a href="javascript:void(0)" onclick="changeApplication(1, 0); ">
                          <font style="font-size:10pt">Backrub Conformational Ensemble</font></a><br>
                          <font style="font-size:8pt">[ <a href="http://dx.doi.org/10.1016/j.jmb.2008.05.023" style="font-size: 8pt">Smith and Kortemme, 2008</a> ]</font>
                      </td></tr>
                  <tr><td width="30" style="text-align:right;">&#8680;</td>
                      <td><a href="javascript:void(0)" onclick="changeApplication(1, 1); ">
                          <font style="font-size:10pt">Backrub Ensemble Design</font></a><br>
                          <font style="font-size:8pt">[ <a href="http://dx.doi.org/10.1371/journal.pcbi.1000393" style="font-size: 8pt">Friedland et. al., 2008</a> ]</font>
                      </td></tr>
                  </table>
              </p>
            </li>
            <li id="ab4">
              <A href="javascript:void(0)" class="nav" onclick="showMenu('2');"><img src="../images/qm_s.png" border="0" title="%(tt_click)s"> Sequence Tolerance</A>
              
              <p id="menu_3" style="text-align:right; margin:0px;">
                  <table style="border:0px; padding:0px; margin:0px;">
                  <tr><td width="30" style="text-align:right;">&#8680;</td>
                      <td><a href="javascript:void(0)" onclick="changeApplication(2, 0); ">
                          <font style="font-size:10pt">Interface Sequence Tolerance</font></a><br>
                          <font style="font-size:8pt">[ <a href="http://dx.doi.org/10.1016/j.str.2008.09.012" style="font-size: 8pt">Humphris and Kortemme, 2008</a> ]</font>
                      </td></tr>
                  <tr><td width="30" style="text-align:right;">&#8680;</td>
                      <td><a href="javascript:void(0)" onclick="changeApplication(2, 1); ">
                          <font style="font-size:10pt">Interface / Fold Sequence Tolerance</font></a><br>
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
            <p id="pic0" style="display:none; text-align:center;">
              <img src="../images/logo0.png" width="85%%" alt="logo0" border=0>
            </p>

            <p id="pic1" style="display:none; text-align:center;">
              <img src="../images/logo1.png" width="85%%" alt="logo1" border=0>
            </p>
            
            <p id="pic2" style="display:none; text-align:center;">
              <img src="../images/logo2.png" width="85%%" alt="logo2" border=0>
            </p>

          <!-- end pictures -->
          <!-- description -->
            <p id="textintro" style="text-align:justify;">
              Choose one of the applications on the left. Each application will give you a short explanation and a set of parameters that can be adjusted.<br><br>
              A <a href="../wiki/Tutorial">tutorial</a> on how to submit a job can be found in the <a href="../wiki">documentation</a>. For a brief explanation of each parameter move your mouse to the question mark symbol. The button "Check form" can be used to highlight fields with invalid entries in red; this is also shown when "Submit" is clicked.
            </p>''' % self.tooltips)
        
        protocolGroups = self.protocolGroups
        numProtocolGroups = len(protocolGroups)
        for i in range(numProtocolGroups):
            html.append('<div id="text%d" style="display:none; opacity:0.0; text-align:justify;">%s</div>' % (i, protocolGroups[i].getDescription()))
        
        html.append("<!-- end description -->")
        
        self.tooltips["UploadedPDB"] = UploadedPDB
        
        # PDB loading subform
        html.append('''        
            <TABLE id="PrePDBParameters" align="center" style="display:none; opacity:0.0;">
              <TR>
                <TD align=right>User Name </TD>
                <TD align=left style="padding-left:5pt; padding-top:5pt;" ><INPUT TYPE="text" maxlength=30 SIZE=31 NAME="UserName" VALUE="%(username)s" disabled>
                </TD>
              </TR>
              <TR><td></td></TR>
              <TR>
                <TD align=right style="width:300px">Rosetta Version <img src="../images/qm_s.png" title="%(tt_RVersion)s"></TD>
                <TD id="rosetta1" style="padding-left:5pt; padding-top:5pt;">''' % self.tooltips)
        
        i = 0
        # As it happens, alphabetical ordering of RosettaBinaries co-incides with revision ordering 
        
        refIDs = self.refs.getReferences()
        for desc, details in sorted(RosettaBinaries.iteritems()):
            # This is a hack to add show which of the two Sequence Tolerance papers the binary references
            bname = details["name"]
            if desc == "seqtolJMB":
                bname += '<a href="#refSmithKortemme:2010"><sup id="ref">%(SmithKortemme:2010)d</sup></a>' % refIDs
            elif desc == "seqtolP1":
                bname += '<a href="#refSmithKortemme:2010"><sup id="ref">%(SmithKortemme:2010)d</sup></a>' % refIDs
            
            # Escape the name so we can pass it to javascript
            bnamevalue = bname
            embeddedHTML = find(bname, "<")
            if embeddedHTML != -1:
                bnamevalue = bname[0:embeddedHTML]
            
            html.append('''
                    <div id="rv%s" style="display:none;" class="bin_revisions"><input type="radio" name="Mini" value="%s" onChange="document.submitform.MiniTextValue.value = '%s'"/> %s</div>
                    ''' % (desc, desc, bnamevalue, bname))
            i += 1
        
        html.append('''
             </TD>
              </TR>
              <TR>
                <TD align=right>Upload Structure <img src="../images/qm_s.png" title="%(tt_Structure)s"></TD>
                <TD align=left style="padding-left:5pt; padding-top:5pt;" >
                <INPUT id="PDBComplex" TYPE="file" NAME="PDBComplex" size="20" onChange="document.submitform.query.value = 'parsePDB'; document.submitform.submit();">
                </TD>
              </TR>
              <TR><TD align="center" colspan="2" style="padding-bottom:0pt; padding-top:0pt;">or</TD></TR>
              <TR>
                <TD align=right>4-digit PDB identifier <img src="../images/qm_s.png" title="%(tt_PDBID)s"></TD>
                <TD align=left style="padding-left:5pt; padding-top:5pt;" > <INPUT TYPE="text" NAME="PDBID" size="4" maxlength="4" onkeydown="if (event.keyCode == 13 && document.submitform.PDBID.value.length == 4){document.submitform.query.value = 'parsePDB'; document.submitform.submit();}">
                <span><input type="button" value="Load PDB" onClick="if (document.submitform.PDBID.value.length == 4) {document.submitform.query.value = 'parsePDB'; document.submitform.submit();}"></span>
                </TD>
              </TR>
              <TR><td></td></TR>
              <TR>
                <TD align="center" colspan=2 style="border-bottom:1pt dashed black"></TD>
              </TR> 
              </TABLE> ''' % self.tooltips)
                
        # Subform after PDB is loaded
        self.tooltips["MiniVersion"] = MiniVersion
        html.append('''
          <!-- parameter form -->
            <TABLE id="PostPDBParameters" align="center" style="display:none; opacity:0.0;">
              <TR>
                <TD align=right>User Name </TD>
                <TD align=left style="padding-left:5pt; padding-top:5pt;" ><INPUT TYPE="text" maxlength=30 SIZE=31 NAME="UserName" VALUE="%(username)s" disabled>
                </TD>
              </TR>
              <TR>
                <TD align=right>Rosetta Version </TD>
                <TD align=left style="padding-left:5pt; padding-top:5pt;" ><INPUT TYPE="text" maxlength=70 SIZE=31 NAME="MiniTextbox" VALUE="%(MiniVersion)s" disabled>
                </TD>
              </TR>
              <TR><td></td></TR>
              <TR>
                <TD align=right>Job Name <img src="../images/qm_s.png" title="%(tt_JobName)s"></TD>
                <TD align=left style="padding-left:5pt; padding-top:5pt;"><INPUT TYPE="text" maxlength=40 SIZE=31 NAME="JobName" VALUE="%(jobname)s"></TD>
              </TR>
              <TR id="UploadedPDB">
                  <TD></TD>
                  <TD align=right style="color:#00bb00;">PDB uploaded: %(UploadedPDB)s</TD>
              </TR>
              <TR><TD colspan=2><br></TD></TR>
              <TR>
                <TD align="center" colspan=2 style="border-bottom:1pt dashed black">General Settings</TD>
              </TR>
              <TR>
                <TD align=right>Number of structures <img src="../images/qm_s.png" title="%(tt_NStruct)s"></TD>
                <TD style="padding-left:5pt; padding-top:5pt;"> <input type="text" name="nos" maxlength=3 SIZE=5 VALUE="%(ROSETTAWEB_SK_RecommendedNumStructures)s">
                 ''' % self.tooltips)
        
        for i in range(numProtocolGroups):
            numProtocols = protocolGroups[i].getSize()
            for j in range(numProtocols):
                html.append('''<span id="recNumStructures%d_%d" style="display:none; opacity:0.0;">(%d-%d, recommended %d)</span>
                    ''' %(i, j, protocolGroups[i][j].nos[0], protocolGroups[i][j].nos[2], protocolGroups[i][j].nos[1]))

        html.append('''
               </TD>
               </TR>
              <TR><TD align=left><br></TD></TR>
              <TR>
                <TD align="center" colspan=2 style="border-bottom:1pt dashed black">Application Specific Settings <img src="../images/qm_s.png" border="0" title="%(tt_specific)s"></TD>
              </TR> 
            </TABLE>''' % self.tooltips)
        
        for protocol in self.protocols:
            protocolForm = protocol.getSubmitfunction()
            htmlcode, ps = protocolForm(chainOptions, aminoAcidOptions, numChainsAvailable)
            html.extend(htmlcode)
            postscripts.append(ps)        
        
        html.append('''     
            <p id="parameter_submit" style="display:none; opacity:0.0; text-align:center;">
              <input type="button" value="Load sample data" onClick="set_demo_values();">
              <span class="allStepsShown" style="display:none;">&nbsp;&nbsp;&nbsp;&nbsp;<input type="button" value="Check form" onClick="ValidateForm();"></span>
              <span class="allStepsShown" style="display:none;">&nbsp;&nbsp;&nbsp;&nbsp;<input type="button" value="Reset Form" onClick="reset_form();"></span>
              <span class="allStepsShown" style="display:none;">&nbsp;&nbsp;&nbsp;&nbsp;<INPUT TYPE="Submit" VALUE="Submit"></span>
            </p>
            <!-- end parameter form -->''')
        
        # references        
        protocolGroups = self.protocolGroups
        numProtocolGroups = len(protocolGroups)
        for i in range(numProtocolGroups):
            numProtocols = protocolGroups[i].getSize()
            for j in range(numProtocols):
                html.append('''
                    <p id="ref%d_%d" style="display:none; opacity:0.0; text-align:justify; border:1px solid #000000; padding:5px; font-size: 10pt; background-color:#FFFFFF; ">
                        If you are using the data, please cite:''' % (i, j))
                for r in protocolGroups[i][j].getReferences():
                    html.append('<br><br>%s' % self.refs[r])
                html.append('</p>')

        html.append('''
                  </div> <!-- id=box -->  
                  </td>
            <!-- end right column -->            
                </tr>
              </table>
                    ''')
          
        # We store the uploaded PDB as a form value so it can be retrieved on submission
        # Note that this could allow a malicious user to replace the filename. As we read
        # and check the file for PDB content, this shouldn't be an issue but serverside, we
        # should ignore any path in the filename.
        # todo:  In fact, if a filename contains path information or is not a PDB (we have 
        #        ensured that the actual uploaded file was a PDB), then we should flag this 
        #        behaviour and email the admin.
        # todo:  Name the PDB better e.g. directory with user session id / original name
        
        html.append(' <INPUT TYPE="hidden" NAME="protocolgroup" VALUE="%s"> ' % activeProtocol[0])
        html.append(' <INPUT TYPE="hidden" NAME="protocoltask" VALUE="%s"> ' % activeProtocol[1])
        html.append('''
            <INPUT TYPE="hidden" NAME="StoredPDB"  VALUE="%s">
            <INPUT TYPE="hidden" NAME="MiniTextValue" VALUE="none">
            <INPUT TYPE="hidden" NAME="query" VALUE="submitted">
            <INPUT TYPE="hidden" NAME="mode"  VALUE="check">
          </FORM>
<!-- End Submit Form -->
        </td>
            ''' % (StoredPDB)) 

        html.extend(postscripts)
        return join(html, "")

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


###############################################################################################
# submitted                                                                                             #
###############################################################################################
            
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
      
      if warnings:
          warnings = "<li>" + join(warnings, "</li><li>") + "</li>"
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
# register                                                                                             #
###############################################################################################

    def register(self, username='', firstname='', lastname='', institution='', email='', address='', city='', zip='', state='', country='', errors=None, update=False ):
        
        error_html = ''
        if errors != None:
            error_html = '<P style="text-align:center; color:red;">%s</P>' % ( join(errors, '<br>') )
        
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
# registered                                                                                             #
###############################################################################################

    def registered(self):
      html = """ <td align="center">Registration successful. You should recieve a confirmation Email shortly.<br> <br> \n 
                   Proceed to <A href="%s?query=login">Login</A> \n""" % ( self.script_filename )
      return html

###############################################################################################
# updated                                                                                             #
###############################################################################################

    def updated(self):
      html = '<td align="center">Your information has been updated successfully.<br> <br> \n'
      return html
    
###############################################################################################
# printQueue                                                                                             #
###############################################################################################

    def printQueue(self,job_list):
      
        html = []
        html.append("""<td align=center><H1 class="title"> Job queue </H1> <br>
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
                   <td > Structures </td>\n""")
        
        protocols = self.protocols
        for line in job_list:
            for p in protocols:
                if line[9] == p.dbname:
                    task = p.name
                    task_color = p.group.color
                    break
          
            html.append("""<tr align=center bgcolor="#EEEEEE" onmouseover="this.style.background='#447DAE'; this.style.color='#FFFFFF';" 
                                                          onmouseout="this.style.background='#EEEEEE'; this.style.color='#000000';" >
                                                          """)
            link_to_job = 'onclick="window.location.href=\'%s?query=jobinfo&jobnumber=%s\'"' % ( self.script_filename, line[1] )
            # write ID
            html.append('<td id="lw" %s>%s </td>' % (link_to_job, str(line[0])))
            # write status 
            status = int(line[2])
            if status == 0:
                html.append('<td id="lw" %s><font color="orange">in queue</font></td>' % link_to_job)
            elif status == 1:
                html.append('<td id="lw" %s><font color="green">active</font></td>' % link_to_job)
            elif status == 2:
                html.append('<td id="lw" %s>done</td>' % link_to_job) # <font color="darkblue" %s></font>
            elif status == 5:
                html.append('<td id="lw" style="background-color: #AFE2C2;" %s><font color="darkblue">sample</font></td>' % link_to_job)
            else:
              # write error
              if  str(line[8]) != '' and line[8] != None:
                # onclick="window.open('https://kortemmelab.ucsf.edu/backrub/wiki/Error#Errors_during_the_simulation','backrub_wiki')"
                #                        onmouseover="this.style.background='#447DAE'; this.style.color='#000000'"
                #                        onmouseout="this.style.background='#EEEEEE';"
                html.append('''<td id="lw">
                              <font color="FF0000">error</font>
                              (<a href="https://kortemmelab.ucsf.edu/backrub/wiki/Error#Errors_during_the_simulation" target="_blank"
                                 onmouseover="this.style.color='#FFFFFF'" onmouseout="this.style.color='#365a79'">%s</a>)</td>''' % str(line[8]))
              else:
                html.append('<td id="lw"><font color="FF0000">error</font></td>')
                
            # write username
            html.append('<td id="lw" %s>%s</td>' % (link_to_job, str(line[3])))
            # write date
            html.append('<td id="lw" style="font-size:small;" %s>%s</td>' % (link_to_job, str(line[4])))
            # write jobname or "notes"
            if len(str(line[5])) < 26:
                html.append('<td id="lw" %s>%s</td>' % (link_to_job, str(line[5])))
            else:
                html.append('<td id="lw" %s>%s</td>' % (link_to_job, str(line[5])[0:23] + "..."))
            
            # Rosetta version
            # todo: the mini/classic distinction is somewhat deprecated with the new seqtol protocol
            miniVersion = "classic"
            if RosettaBinaries[line[6]]["mini"]:
                miniVersion = "mini"
            html.append('<td id="lw" style="font-size:small;" bgcolor="%s" %s ><i>%s</i><br>%s</td>' % (task_color, link_to_job, miniVersion, task))

            # write size of ensemble
            html.append('<td id="lw" %s >%s</td>' % (link_to_job, str(line[7])))
        
            html.append('</tr>\n')
        
        html.append('</table> </div><br> </td>')
        
        return join(html, "")
   
###############################################################################################
# jobinfo function and related subfunctions                                                                                  #
# This function creates the HTML for the Job Info page accessed by clicking a job in the queue
###############################################################################################

    def jobinfo(self, parameter):
        """this function decides what _showFunction to pick"""
        
        self._referenceAll()
                
        statuslist = ['in queue', 'active', 'done', 'unknown', 'error', 'sample'] 
        status = statuslist[int(parameter['Status'])]
        miniVersion = RosettaBinaries[parameter['Mini']]['name']
        endOfName = miniVersion.find(", as published")
        if endOfName != -1:
            miniVersion = miniVersion[0:endOfName]
        
        html = ["""<td align="center"><H1 class="title">Job %s</H1>
                    <div id="jobinfo">
                    <table border=0 cellpadding=2 cellspacing=1>""" % ( parameter['ID'] )]
        
        html.extend(self._defaultParameters( parameter['ID'], parameter['Notes'], status, parameter['Host'], parameter['Date'], parameter['StartDate'], 
                                    parameter['EndDate'], parameter['time_computation'], parameter['date_expiration'], parameter['time_expiration'], miniVersion, parameter['Errors'], delete=False, restart=False ))
        
        
        html.append(self._showDownloadLinks(status, parameter['KeepOutput'], parameter['cryptID'], parameter['ID']))
        ProtocolParameters = pickle.loads(parameter['ProtocolParameters'])
        
        protocols = self.protocols
        for p in protocols:
            if parameter['task'] == p.dbname:
                showFn = p.getShowResultsFunction()
                html.extend(showFn(status, parameter['cryptID'], parameter['PDBComplexFile'], parameter['EnsembleSize'], ProtocolParameters))   
                break
                
        html.append('</table><br></div></td>\n')
        return join(html, "")

    def _defaultParameters(self, ID, jobname, status, hostname, date_submit, date_start, date_end, time_computation, date_expiration, time_expiration, mini, error, delete=False, restart=False ):
        # print the first part of the result table  
    
        qcolors = {
            "in queue" : "orange",
            "active" : "green",
            "done" : "darkblue",
            "sample" : "darkblue"
        }
        
        status_html = None
        for state, color in qcolors.iteritems():
            if status == state:
                status_html = '<font color="%s">%s</font>' % (color, state)
        if not status_html:        
            status_html = '''<font color="FF0000">Error:</font> <a href="https://kortemmelab.ucsf.edu/backrub/wiki/Error#Errors_during_the_simulation">%s</a> <br>
                              We are sorry but your simulation failed. Please refer to 
                              <a href="https://kortemmelab.ucsf.edu/backrub/wiki/Error#Errors_during_the_simulation">Errors during the simulation</a> 
                              in the documentation and contact us via <img src="../images/support_email.png" style="vertical-align:text-bottom;" height="15"> if necessary.
                          ''' % error
        
        html = ["""
                <tr><td align=right bgcolor="#EEEEFF">Job Name:       </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Status:         </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right></td><td></td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Submitted from: </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Date Submitted: </td><td bgcolor="#EEEEFF">%s</td></tr>
                """ % ( jobname, status_html, hostname, date_submit )]
                
        if status == 'active':
            html.append('<tr><td align=right bgcolor="#EEEEFF">Started:        </td><td bgcolor="#EEEEFF">%s</td></tr>\n' % ( date_start ))
        
        if status == 'done' or status == 'sample' or status == 'error':
            html.append("""
                <tr><td align=right bgcolor="#EEEEFF">Started:        </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Ended:          </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Computing time: </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Expires:        </td><td bgcolor="#EEEEFF">%s (%s)</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Binary:         </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right></td><td></td></tr>
                """ % ( date_start, date_end, time_computation, date_expiration, time_expiration, mini ))
        
        #function confirm_delete(jobID)
        #{
        # var r=confirm("Delete Job " + jobID + "?");
        # if (r==true) {
        #               //document.write("You pressed OK!");
        #               window.location.href = "rosettaweb.py?query=delete&jobID=" + jobID + "&button=Delete" ; }
        # //  else {
        #           //    window.location.href = "rosettaweb.py?query=queue" ; }
        # }


        if delete or restart:
            html.append('<tr><td align=right></td><td></td></tr>')
            if delete and status == 'in queue':
                html.append('<a href="#" onclick="confirm_delete(%s); return false;"><font color="red">DELETE</font></a>' % ID)
            if restart and status == 'done':
                html.append('<a href="#"><font color="red">RESUBMIT</font></a>')
        
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
  
    def _showApplet4MultipleFiles(self, comment, list_pdb_files, mutated = None, designed = None):
        """This shows the Jmol applet for an ensemble of structures with their point mutation(s)"""
       
        # todo: Maybe think about color-scheme selector w.r.t. color blindness         
        # todo: set these values in rwebhelper
        # jmol command to load files
        if list_pdb_files != None:
            jmol_cmd = ' "load %s; color red; cpk off; wireframe off; backbone 0.2;" +\n' % (list_pdb_files[0] ) #, list_pdb_files[0].split('/')[-1].split('.')[0])
            for pdb in list_pdb_files[1:11]:
                jmol_cmd += ' "load APPEND %s;" +\n' % (pdb)
            jmol_cmd += ' "cpk off; wireframe off; backbone 0.2;" +'
                        
            # jmol command to show mutation as balls'n'stick
            # todo: the coercion to string for the residue is a hangover from the old codebase. Remove when it always passes  
            jmol_cmd_mutation = ''
            if mutated:
                for chain, residues in mutated.iteritems():
                    for residue in residues:
                        jmol_cmd_mutation += 'select %s:%s; cartoon off; backbone on; wireframe 0.3; ' % ( str(residue), chain )        
            jmol_cmd_designed = ''
            if designed: 
                for chain, residues in designed.iteritems():
                    for residue in residues:
                        # Not the most efficient but numbers should be small
                        # Display residues which are designed but not mutated using green
                        # Display residues which are designed and mutated using yellow 
                        if mutated and mutated[chain] and (residue in mutated[chain]):
                            jmol_cmd_designed += 'select %s:%s; color backbone yellow; cartoon off; backbone on; wireframe 0.3; ' % ( str(residue), chain )
                        else:
                            jmol_cmd_designed += 'select %s:%s; color backbone green; cartoon off; backbone on; wireframe 0.3; ' % ( str(residue), chain )
                        
            # html code
            html = """
                    <form>
                     <tr><td align="justify" bgcolor="#FFFCD8">%s<br><br>Please wait, it may take a few moments to load the C&alpha; trace representation.</td>
                         <td bgcolor="#FFFCD8">
                            <script type="text/javascript">
                              jmolInitialize("../../jmol"); 
                              jmolApplet(400, "set appendNew false;" + %s "%s %s frame all;" ); 
                            </script><br>
                            <small>Jmol: an open-source Java viewer for chemical structures in 3D.</small><br><a href=http://www.jmol.org/><small>www.jmol.org</small></a>
                         </td>
                    </tr>
                    </form>
                    """ % ( comment, jmol_cmd, jmol_cmd_mutation, jmol_cmd_designed )
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
# login                                                                                             #
###############################################################################################

    def login(self, message='', username='', login_disabled=False):
        
        message_html = ''
        if message != '':
            message_html = '<tr><td colspan="3" align="right"><P style="text-align:center; color:red;">%s</P></td></tr>' % ( message )
        disabled = ''
        if login_disabled:
            disabled = 'disabled'
        
        self._referenceAll()

        refIDs = self.refs.getReferences()        
        html = []
        html.append("""<td align="center">
                  <H1 class="title">Welcome to RosettaBackrub</A> </H1> 
                    <P>
                    This is the flexible backbone protein structure modeling and design server of the Kortemme Lab. 
                    The server utilizes the \"<b>backrub</b>\" method, first described by Davis et al.<a href="#refDavisEtAl:2006"><sup id="ref">%(DavisEtAl:2006)d</sup></a>, 
                    for flexible protein backbone modeling implemented in <a href="/backrub/wiki/Rosetta">Rosetta</a><a href="#refSmithKortemme:2008"><sup id="ref">%(SmithKortemme:2008)d,</sup></a><a href="#refHumphrisKortemme:2008"><sup id="ref">%(HumphrisKortemme:2008)d,</sup></a><a href="#refFriedlandEtAl:2009"><sup id="ref">%(FriedlandEtAl:2009)d,</sup></a><a href="#refSmithKortemme:2010"><sup id="ref">%(SmithKortemme:2010)d</sup></a>.</P>
                    <P>The server <b>input</b> is a protein structure (a single protein or a protein-protein complex) uploaded by the user and a choice of parameters and modeling method: 
                    prediction of point mutant structures, creation of conformational ensembles given the input protein structure and flexible backbone design.
                    The server <b>output</b>, dependent on the application, consists of: structures of point mutants<a href="#refSmithKortemme:2008"><sup id="ref">%(SmithKortemme:2008)d</sup></a> and their Rosetta force field scores, 
                    near-native structural ensembles of protein backbone conformations<a href="#refSmithKortemme:2008"><sup id="ref">%(SmithKortemme:2008)d,</sup></a><a href="#refFriedlandEtAl:2009"><sup id="ref">%(FriedlandEtAl:2009)d</sup></a> 
                    and designed sequences using flexible backbone computational protein design<a href="#refHumphrisKortemme:2008"><sup id="ref">%(HumphrisKortemme:2008)d,</sup></a><a href="#refSmithKortemme:2010"><sup id="ref">%(SmithKortemme:2010)d</sup></a>.</P>
                    <P>For a <b>tutorial</b> on how to submit a job and interpret the results see the <a href="/backrub/wiki/" target="_blank">documentation</a>.
            Please also check for <a href="/backrub/wiki/" target="_blank">current announcements</a>. 
                    </P>""" % refIDs)
        
        html.append("""
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
                   <td>""" % ( self.script_filename, self.script_filename, message_html, username, disabled, disabled, self.script_filename ))

        return join(html, "\n")

###############################################################################################
# loggedIn                                                                                             #
###############################################################################################

    def loggedIn(self, username):
        self.username = username
        html = """ <div id="login_box"></div>
                   <td align="center">You have successfully logged in as %s. <br> <br> \n 
                   From here you can proceed to the <A href="%s?query=submit">submission page</A> to <A href="%s?query=submit">submit a new job</A> <br>
                   or navigate to the <A href="%s?query=queue">queue</A> to check for submitted, running or finished jobs. <br><br> </td>
                   """ % ( username, self.script_filename, self.script_filename, self.script_filename )
        return html


###############################################################################################
# logout                                                                                             #
###############################################################################################

    def logout(self, username):
        self.username = ''
        html = """<td align="center"> 
                <H1 class="title">Logout</H1>
                You (%s) have successfully logged out. Thank you for using this server. 
                <br><br> 
              </td>""" % ( username )
        return html


      
###############################################################################################
# sendPassword                                                                                            #
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
      
###############################################################################################
# passwordUpdated                                                                                            #
###############################################################################################

    def passwordUpdated(self, message):
        html = """<td align="center">
                  <H1 class="title">Password Updated</H1>
                    <P style="text-align:center;">%s</P>
                    </td>""" % message
                  
        return html

###############################################################################################
# help                                                                                             #
###############################################################################################

    def help(self):
        html = '<td>'
        html += open("doc.html", 'r').read() # '<a href="../wiki/">doc</a>' #
        html += '</td>'     
        return html
        
        
###############################################################################################
# terms_of_service                                                                                             #
###############################################################################################

    def terms_of_service(self):
        html = '<td align="center">'
        # terms of service html can be found in this file
        html += open("terms_of_service.html", 'r').read()
        html += '</td>'
        return html    
  
###############################################################################################
# Protocol-specific functions - submission form and results display                                                                                             #
###############################################################################################

    def submitformPointMutation(self, chainOptions, aminoAcidOptions, numChainsAvailable):
        html = ['''
         <!-- Backrub - Point Mutation -->
            <p id="parameter0_0" style="display:none; opacity:0.0; text-align:justify;">
            
                <table id="parameter0_0_step1" style="display:none;" bgcolor="#EEEEEE" align="center">
                    <tr bgcolor="#828282" style="color:white;">
                        <td align="center">#</td>
                        <td align="center" title="%(tt_ChainId)s">Chain ID</td>
                        <td align="center" title="%(tt_ResId)s">Residue ID</td>
                        <td align="center" title="%(tt_NewAA)s">New Amino Acid</td>
                    </tr>''' % self.tooltips ]
        
        html.append('''
                    <tr style="">
                        <td style="text-align:center;">1</td>
                        <td style="text-align:center;"><select name="PM_chain">%s</select></td>
                        <td style="text-align:center;"><input name="PM_resid" maxlength="4" size="5" type="text"/></td>
                        <td style="text-align:center;"><select name="PM_newres" style="text-align:center;">%s</select></td>
                        <td><INPUT TYPE="hidden" NAME="PM_radius" VALUE="6.0"></td>
                    </tr>
                </table>
                <span id="parameter0_0_step2" style="display:none;"/>
                <br>
            </p>
            ''' % (chainOptions, aminoAcidOptions))
     
        return html, ""
    
    def resultsPointMutation(self, status, cryptID, input_filename, size_of_ensemble, ProtocolParameters):
    
        chain = ProtocolParameters["Mutations"][0][0]
        resid = ProtocolParameters["Mutations"][0][1]
        newaa = ProtocolParameters["Mutations"][0][2]
        #todo: not shown radius= ProtocolParameters["Mutations"][0][3]
        
        html = ["""
                <tr><td align=right bgcolor="#EEEEFF">Task:           </td><td bgcolor="#EEEEFF">Point Mutation</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Input file:     </td><td bgcolor="#EEEEFF">%s</td></tr> 
                <tr><td align=right bgcolor="#EEEEFF">No. Generated structures: </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Parameters:    </td><td bgcolor="#EEEEFF">Chain: %s<br>Residue: %s<br>Mutation: %s</td></tr>
                """ % ( input_filename, size_of_ensemble, chain, resid, newaa )]
                
        if status == 'done' or status == 'sample':
          html.append('<tr><td align=right></td><td></td></tr>')
          html.append(self._show_scores_file(cryptID))
          comment = 'Backbone representation of up to 10 of the best scoring structures. The query structure is shown in red, the mutated residue is shown as sticks representation.'
        
          html.append(self._showApplet4MultipleFiles( comment, self._getPDBfiles(input_filename, cryptID, 'low'), mutated = {chain : [resid]}))
          html.append(self._show_molprobity( cryptID ))
          
        return html
    
    def submitformMultiplePointMutations(self, chainOptions, aminoAcidOptions, numChainsAvailable):
        html = ['''
            <!-- Backrub - Multiple Point Mutation -->
            <p id="parameter0_1" style="display:none; opacity:0.0; text-align:justify;">
                <table id="parameter0_1_step1" style="display:none;" bgcolor="#EEEEEE" align="center">
                    <tr bgcolor="#828282" style="color:white;">
                        <td align="center">#</td>
                        <td align="center" title="%(tt_ChainId)s">Chain ID</td>
                        <td align="center" title="%(tt_ResId)s">Residue ID</td>
                        <td align="center" title="%(tt_NewAA)s">Amino Acid</td>
                        <td align="center" title="%(tt_Radius)s">Radius [&#197;]</td>
                    </tr>''' % self.tooltips ]
        
        html.append('''
                    <!-- up to 30 point mutations are possible -->
                    <tr id="row_PM0" style="">
                        <td style="text-align:center;">1</td>
                        <td style="text-align:center;"><select name="PM_chain0">%s</select></td>
                        <td style="text-align:center;"><input name="PM_resid0" maxlength="4" size="5" type="text"/></td>
                        <td style="text-align:center;"><select name="PM_newres0" style="text-align:center;">%s</select></td>
                        <td style="text-align:center;"><input name="PM_radius0" maxlength="4" size="7" type="text" value="6.0"/></td>
                    </tr>
                ''' % (chainOptions, aminoAcidOptions))    
        
        for i in range(1, ROSETTAWEB_MaxMultiplePointMutations):
            html.append('''
                    <tr id="row_PM%d" style="display:none">
                        <td style="text-align:center;">%d</td>
                        <td style="text-align:center;"><select name="PM_chain%d">%s</select></td>
                        <td style="text-align:center;"><input name="PM_resid%d" maxlength="4" size="5" type="text"/></td>
                        <td style="text-align:center;"><select name="PM_newres%d" style="text-align:center;">%s</select></td>
                        <td style="text-align:center;"><input name="PM_radius%d" maxlength="4" size="7" type="text" value="6.0"/></td>
                    </tr>''' % (i, i + 1, i, chainOptions, i, i, aminoAcidOptions, i))
            
        
        html.append('''    
                    <tr><td align="center" colspan="4"><div id="addmrow_0_1" style="display:none"><a href="javascript:void(0)" onclick="addOneMore();">Click here to add a residue</a></div></td></tr>
                </table>
                <span id="parameter0_1_step2" style="display:none;"/>
            </p>''')
        return html, ""
    
    
    def resultsMultiplePointMutations(self, status, cryptID, input_filename, size_of_ensemble, ProtocolParameters):
    
        list_chains = []
        list_resids = []
        list_newres = []
        list_radius = []
        mutated = {}
        for entry in ProtocolParameters["Mutations"]:
            chain = ProtocolParameters["Mutations"][0]
            resid = ProtocolParameters["Mutations"][1] 
            list_chains.append(chain)
            list_resids.append(resid)
            list_newres.append(ProtocolParameters["Mutations"][2])
            list_radius.append(ProtocolParameters["Mutations"][3])
            mutated[chain] = mutated[chain] or []
            mutated[chain].append(resid)
            
        multiple_mutations_html = ''
        for x in range(len(list_chains)):
            multiple_mutations_html += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % ( x+1, list_chains[x], list_resids[x], list_newres[x], list_radius[x] )
        
        html = ["""
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
                    """ % ( input_filename, size_of_ensemble, multiple_mutations_html )]
        
        if status == 'done' or status == 'sample':
          html.append('<tr><td align=right></td><td></td></tr>')
          html.append(self._show_scores_file(cryptID))
          comment = 'Backbone representation of up to 10 of the best scoring structures. The query structure is shown in red, the mutated residues are shown as sticks representation.'
        
          html.append(self._showApplet4MultipleFiles( comment, self._getPDBfiles(input_filename, cryptID, 'low'), mutated = mutated ))
          html.append(self._show_molprobity( cryptID ))
          
        return html
    
    def submitformEnsemble(self, chainOptions, aminoAcidOptions, numChainsAvailable):
        return ['''
            <!-- Ensemble - simple -->
            <p id="parameter1_0" style="display:none; opacity:0.0; text-align:center;">
            <span id="parameter1_0_step1" style="display:none;">no options</span>
            <span id="parameter1_0_step2" style="display:none;"/>            
            </p>
            ''' % self.tooltips], ""
    
    def showEnsemble(self, status, cryptID, input_filename, size_of_ensemble, ProtocolParameters):
        html = ["""
                <tr><td align=right bgcolor="#EEEEFF">Task:           </td><td bgcolor="#EEEEFF">Backrub Conformational Ensemble</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Input file:     </td><td bgcolor="#EEEEFF">%s</td></tr> 
                <tr><td align=right bgcolor="#EEEEFF">No. Generated structures: </td><td bgcolor="#EEEEFF">%s</td></tr>
                """ % ( input_filename, size_of_ensemble )]
        
        if status == 'done' or status == 'sample':
            html.append('<tr><td align=right></td><td></td></tr>')
            html.append(self._show_scores_file(cryptID))        
        
            comment = 'Backbone representation of the 10 best scoring structures. The query structure is shown in red.'
            html.append(self._showApplet4MultipleFiles( comment, self._getPDBfiles(input_filename, cryptID, 'low')))
            html.append(self._show_molprobity( cryptID ))
          
        return html
    
    def submitformEnsembleDesign(self, chainOptions, aminoAcidOptions, numChainsAvailable):
        return ['''
            <!-- Ensemble - design -->
            <p id="parameter1_1" bgcolor="#EEEEEE"style="display:none; opacity:0.0; text-align:center;">
                <table id="parameter1_1_step1" bgcolor="#EEEEEE" style="display:none;" align="center">
                <tr>
                    <td align="right" style="color:white;" bgcolor="#828282">Temperature [kT] <img src="../images/qm_s.png" title="%(tt_Temp)s"></td>
                    <td><input type="text" name="ENS_temperature" maxlength=3 SIZE=5 VALUE="1.2"></td>
                    <td bgcolor="#DDDDDD">(max 4.8, recommended 1.2)</td>
                </tr>
                <tr>
                    <td align="right" style="color:white;" bgcolor="#828282">Max. segment length <img src="../images/qm_s.png" title="%(tt_SegLength)s"></td>
                    <td><input type="text" name="ENS_segment_length" maxlength=2 SIZE=5 VALUE="12"></td>
                    <td bgcolor="#DDDDDD">(max 12, recommended 12)</td>
                </tr>
                <tr>
                    <td align="right" style="color:white;" bgcolor="#828282">No. of sequences <img src="../images/qm_s.png" title="%(tt_NSeq)s"></td>
                    <td><input type="text" name="ENS_num_designs_per_struct" maxlength=4 SIZE=5 VALUE="20"></td>
                    <td bgcolor="#DDDDDD">(max 20, recommended 20)</td>
                </tr>
                </table>
                <span id="parameter1_1_step2" style="display:none"/>            
            </p>
            ''' % self.tooltips], ""
            
    def showEnsembleDesign(self, status, cryptID, input_filename, size_of_ensemble, ProtocolParameters):
        temperature = ProtocolParameters["Temperature"]
        seq_per_struct = ProtocolParameters["NumDesignsPerStruct"]
        len_of_seg = ProtocolParameters["SegmentLength"]
        
        html = ["""
                <tr><td align=right bgcolor="#EEEEFF">Task:           </td><td bgcolor="#EEEEFF">Backrub Ensemble Design</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Input file:     </td><td bgcolor="#EEEEFF">%s</td></tr> 
                <tr><td align=right bgcolor="#EEEEFF">No. Generated structures: </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Parameters:    </td><td bgcolor="#EEEEFF">Temperature: %s<br>Sequences per Structure: %s<br>Length of Segment: %s</td></tr>
                """ % ( input_filename, size_of_ensemble, temperature, seq_per_struct, len_of_seg )]
        
        if status == 'done' or status == 'sample':
            html.append('<tr><td align=right></td><td></td></tr>')
          
            comment2 = """Structures of the C&alpha; backbone traces of the backrub ensemble.<br>
              [ <a href="../downloads/%s/ensemble.pdb">PDB file</a> ]
              <br><br>Please wait, it may take a few moments to load the C&alpha; trace representation.""" % cryptID
        
            html.append(self._showApplet4EnsembleFile( comment2, '../downloads/%s/ensemble.pdb' % cryptID, style='backbone' ))        
          
            comment1 = """Mean C&alpha; difference distance values of the ensemble mapped onto X-ray structure. 
                        The gradient from red to white to blue corresponds to flexible, intermediate and rigid regions, respectively.<br>
               [ <a href="../downloads/%s/ca_dist_difference_bfactors.pdb">PDB file</a> ]
               <br><br>Please wait, it may take a few moments to load cartoon representation.""" % cryptID
        
            html.append(self._showApplet4EnsembleFile( comment1, '../downloads/%s/ca_dist_difference_bfactors.pdb' % cryptID, style='cartoon' ))
          
            WebLogoText = self.WebLogoText
            html.append("""
                <tr><td align="right" bgcolor="#FFFCD8">Mean C&alpha; difference distance values</td>                 
                    <td bgcolor="#FFFCD8"><a href="../downloads/%(cryptID)s/ca_dist_difference_1D_plot.png">
                                          <img src="../downloads/%(cryptID)s/ca_dist_difference_1D_plot.png" alt="image file not available" width="400"></a></td></tr>
              
                <tr><td align="right" bgcolor="#FFFCD8">Pairwise C&alpha; difference distance values [ <a href="../downloads/%(cryptID)s/ca_dist_difference_matrix.dat">matrix file</a> ]</td>                
                    <td bgcolor="#FFFCD8"><a href="../downloads/%(cryptID)s/ca_dist_difference_2D_plot.png">
                                          <img src="../downloads/%(cryptID)s/ca_dist_difference_2D_plot.png" alt="image file not available" width="400"></a></td></tr>
                
                <tr><td align="right" bgcolor="#FFFCD8">Mean RMSD of C&alpha; atoms for individual residues</td>
                    <td bgcolor="#FFFCD8"><a href="../downloads/%(cryptID)s/rmsd_plot.png"><img src="../downloads/%(cryptID)s/rmsd_plot.png" alt="image file not available" width="400"></a></td></tr>                          
                                          
                <tr><td align="center" colspan="2" bgcolor="#FFFCD8">Design results:</td></tr>
                <tr><td align="right" bgcolor="#FFFCD8">Frequency of amino acids for core residues<br><br>
                                                        Sequences [ <a href="../downloads/%(cryptID)s/designs_core.fasta">fasta formated file</a> ]<br>
                                                        Sequence population matrix [ <a href="../downloads/%(cryptID)s/seq_pop_core.txt">matrix file</a> ]</td> 
                    <td bgcolor="#FFFCD8"><a href="../downloads/%(cryptID)s/logo_core.png"><img src="../downloads/%(cryptID)s/logo_core.png" alt="image file not available" width="400"></a><br>
                    %(WebLogoText)s
                    </td>
                </tr>
                
                <tr><td align="right" bgcolor="#FFFCD8">Frequency of amino acids for all residues<br><br>
                                                        Sequences [ <a href="../downloads/%(cryptID)s/designs.fasta">fasta formated file</a> ]<br>
                                                        Sequence population matrix [ <a href="../downloads/%(cryptID)s/seq_pop.txt">matrix file</a> ]</td>
                    <td bgcolor="#FFFCD8"><a href="../downloads/%(cryptID)s/logo.png"><img src="../downloads/%(cryptID)s/logo.png" alt="image file not available" width="400"></a><br>
                    %(WebLogoText)s
                    </td></tr>
                    <tr><td align=right></td><td></td></tr>""" % vars())

        return html
    
    def submitformSequenceToleranceHK(self, chainOptions, aminoAcidOptions, numChainsAvailable):
        
        ttc = self.tooltips["tt_seqtol_partner"] 
        ttd = self.tooltips["tt_seqtol_design"]                   
        html = ['''
            <!-- Library Design -->
            <p id="parameter2_0" style="display:none; opacity:0.0; text-align:center;">
            <table id="parameter2_0_step1" style="display:none;" align="center">
              <tr>
                  <td style="vertical-align:top" align="right">Partners <img src="../images/qm_s.png" title="%(ttc)s"></td>
                  <td>
                      <table bgcolor="#EEEEEE">
                          <tr bgcolor="#828282" style="color:white;">
                            <td>#</td>
                            <td>Chain ID</td>
                          </tr>
                          <tr>
                            <td>1</td>
                            <td><select name="seqtol_chain1">%(chainOptions)s</select></td>
                          </tr>
                          <tr>
                            <td>2</td>
                            <td><select name="seqtol_chain2">%(chainOptions)s</select></td>
                          </tr>
                      </table>
                    </td>
                </tr>
                <tr>
                  <td style="vertical-align:top" align="right">Residues for design<img src="../images/qm_s.png" title="%(ttd)s"></td>
                  <td>
                    <table bgcolor="#EEEEEE">
                      <tr bgcolor="#828282" style="color:white;">
                        <td>#</td><td>Chain ID</td><td>Residue Number</td>
                      </tr> ''' % vars()]                
        
        html.append('''<tr align="center" id="seqtol_row_0" >
                            <td>1</td>
                            <td><select name="seqtol_mut_c_0">%s</select></td>
                            <td><input type="text" name="seqtol_mut_r_0" maxlength=4 SIZE=4></td>
                        </tr>''' % chainOptions)
        
        for i in range(1, ROSETTAWEB_HK_MaxMutations):
            html.append('''<tr align="center" id="seqtol_row_%d" style="display:none">
                                <td>%d</td>
                                <td><select name="seqtol_mut_c_%d">%s</select></td>
                                <td><input type="text" name="seqtol_mut_r_%d" maxlength=4 SIZE=4></td>
                            </tr>''' % (i, i + 1, i, chainOptions, i))
        
        html.append('''<tr align="center"><td colspan="3"><div id="addmrow_2_0" style="display:none"><a href="javascript:void(0)" onclick="addOneMoreSeqtol();">Click here to add a residue</a></div></td></tr>
                      </table>
                  </td>
                </tr>
            </table>
            <span id="parameter2_0_step2" style="display:none;"/>            
            </p>''')
            
        return html, ""
    
    def showSequenceToleranceHK(self, status, cryptID, input_filename, size_of_ensemble, ProtocolParameters):

        seqtol_chain1 = ProtocolParameters["Partners"][0]
        seqtol_chain2 = ProtocolParameters["Partners"][1]
        seqtol_list_1 = ProtocolParameters["Designed"][seqtol_chain1]
        seqtol_list_2 = ProtocolParameters["Designed"][seqtol_chain2]
        w1 = ProtocolParameters["Weights"][0]
        w2 = ProtocolParameters["Weights"][1]
        w3 = ProtocolParameters["Weights"][2]
        
        html = ["""
              <tr><td align=right bgcolor="#EEEEFF">Task:         </td><td bgcolor="#EEEEFF">Interface Sequence Tolerance Prediction  (Humphris, Kortemme 2008)</td></tr>
              <tr><td align=right bgcolor="#EEEEFF">Input file:   </td><td bgcolor="#EEEEFF">%s</td></tr>
              <tr><td align=right bgcolor="#EEEEFF">No. Generated structures: </td><td bgcolor="#EEEEFF">%s</td></tr>
              <tr><td align=right bgcolor="#EEEEFF">Parameters:   </td>
                  <td bgcolor="#EEEEFF">
                      Partner 1: Chain %s<br>
                      Partner 2: Chain %s<br>
                      Designed residues of Partner 1: %s<br>
                      Designed residues of Partner 2: %s<br>
                  </td>
              </tr>""" % ( input_filename, size_of_ensemble, seqtol_chain1, seqtol_chain2, join(seqtol_list_1,' '), join(seqtol_list_2,' ')) ]
                                                  
        input_id = input_filename[:-4] # filename without suffix
        if status == 'done' or status == 'sample':
            html.append('<tr><td align=right></td><td></td></tr>')
            
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
            
            html.append(self._showApplet4MultipleFiles(comment1, list_pdb_files[:10], mutated = ProtocolParameters["Designed"])) # only the first 10 structures are shown
                           
            html.append('''<tr><td align="left" bgcolor="#FFFCD8">Individual boxplots of the predicted frequencies at each mutated site.<br>
                              Download <a href="../downloads/%s/tolerance_pwm.txt">weight matrix</a> or file with all plots as 
                              <a href="../downloads/%s/tolerance_boxplot.png">PNG</a>, <a href="../downloads/%s/tolerance_boxplot.pdf">PDF</a>.<br>
                              </td>
                           <td bgcolor="#FFFCD8">
                    ''' % ( cryptID, cryptID, cryptID ))
                    
                    # To rerun the analysis we provide the <a href="../downloads/specificity.R">R-script</a> that was used to analyze this data. 
                    # A <a href="../wiki/SequenceTolerancePrediction" target="_blank">tutorial</a> on how to use the R-script can be found on 
                    # the <a href="../wiki/" target="_blank">wiki</a>.
            
            for resid in seqtol_list_1:
              html.append('''<a href="../downloads/%s/tolerance_boxplot_%s%s.png"><img src="../downloads/%s/tolerance_boxplot_%s%s.png" alt="image file not available" width="400"></a><br>
                    ''' % ( cryptID, seqtol_chain1, resid, cryptID, seqtol_chain1, resid ))
            for resid in seqtol_list_2:
              html.append('''<a href="../downloads/%s/tolerance_boxplot_%s%s.png"><img src="../downloads/%s/tolerance_boxplot_%s%s.png" alt="image file not available" width="400"></a><br>
                    ''' % ( cryptID, seqtol_chain2, resid, cryptID, seqtol_chain2, resid ))
            
            html.append(self._show_molprobity( cryptID ))
            
            html.append("</td></tr>")
        return html      
    
    def submitformSequenceToleranceSK(self, chainOptions, aminoAcidOptions, numChainsAvailable):

        # Test: python rosettaseqtol.py 1601 2I0L_A_C_V2006.pdb 2 10.0 0.228 2 0.4 1.0 0.4 A 318 B
            #Upload structure: 2I0L_A_C_V2006.pdb
            #Number of structures: 2 
            #Radius: 10.0
            #kT: 0.228
            #Weights list: 2 0.4 1.0 0.4
            #Designed residues: A 318 B
        
        postscript = ""
        html = ['''<p id="parameter2_1" style="display:none; opacity:0.0; text-align:center;">''']
        
         # Header

        html.append('''<table id="parameter2_1_step1"  style="display:none; opacity:0.0; text-align:center;">
                    <tr>
                    <td>
                    <select id="numPartners" name="numPartners" onfocus="this.valueatfocus=this.value" 
                        onChange="if ((this.value != this.valueatfocus) && (this.value != 'x')) {changeApplication(2, 1, 2, this.selectedIndex);} " 
                        onblur  ="if ((this.value != this.valueatfocus) && (this.value != 'x')) {changeApplication(2, 1, 2, this.selectedIndex);} "                        
                    >
                        <option value="x">Select the number of partners</option>
                        <option value="1">1 Partner (Fold stability)</option>                    
                    ''')
         
        if numChainsAvailable > 1:
            html.append('''
                            <option value="2">2 Partners (Interface)</option> ''')
            numChainsAllowed = min(ROSETTAWEB_max_seqtol_SK_chains, numChainsAvailable)
            for j in range(3, numChainsAllowed + 1):
                html.append(''' <option value="%s">%s Partners</option> ''' % (j, j))
        
        html.append('''</select></td></tr><tr><td height="10"></td></tr></table>''')
        
        # Body
        html.append('''<table align="center" id="parameter2_1_step2" style="display:none;">''')
        
        # Chains
        tt = self.tooltips["tt_seqtol_SK_partner"]

        # Chains are either: i) selectable with the name of the chain as value or "invalid" if no selection is made;
        # or ii) not selectable with the value set to "ignore"
    
        for i in range(numChainsAvailable):
            html.append('''
              <tr id="seqtol_SK_chainrow_%d">
                  <td align="left">Partner %d <img src="../images/qm_s.png" title="%s"></td>
                  <td>Chain <select name="seqtol_SK_chain%d" onChange="chainsChanged();" onfocus="this.valueatfocus=this.value" onblur="if (this.value != this.valueatfocus) chainsChanged()">%s</select></td>
                  </tr>
                  ''' % (i, i+1, tt, i, chainOptions))
        for i in range(numChainsAvailable, ROSETTAWEB_max_seqtol_SK_chains):
            html.append('''
                <tr id="seqtol_SK_chainrow_%d">
                  <td align="left">Partner %d <img src="../images/qm_s.png" title="%s"></td>
                  <td>Chain <select name="seqtol_SK_chain%d"><option value="ignore" selected>Select a chain</option></select></td>
                  </tr>
                  ''' % (i, i+1, tt, i))
        
        # Premutated residues
        html.append('''
              <tr><td height="10"></td></tr>
                <tr>
                  <td align="left" valign="top">Premutated residues<img src="../images/qm_s.png" title="%(tt_seqtol_premutated)s"></td>
                  <td>
                    <table bgcolor="#EEEEEE">
                      <tr bgcolor="#828282" style="color:white;">
                        <td>#</td><td>Chain ID</td><td>Residue Number</td><td>Target amino acid</td>
                      </tr>
              ''' % self.tooltips)
        for i in range(0, ROSETTAWEB_SK_MaxPremutations):
            #style="display:none"
            html.append('''<tr align="center" id="seqtol_SK_pre_row_%d"> 
                            <td>%d</td>
                            <td><select name="seqtol_SK_pre_mut_c_%d" style="text-align:center;" onChange="updateBoltzmann();">%s</select></td>            
                            <td><input type="text" name="seqtol_SK_pre_mut_r_%d" maxlength=4 SIZE=4 onChange="updateBoltzmann();"></td>
                            <td><select name="premutatedAA%d" style="text-align:center;" onChange="updateBoltzmann();">%s</select>
                           </tr>''' % (i, i+1, i, chainOptions, i, i, aminoAcidOptions))
            
        html.append('''
                      <tr align="center"><td colspan="3"><div id="seqtol_SK_pre_addrow"><a href="javascript:void(0)" onclick="addOneMoreSeqtolSKPremutated();">Click here to add a residue</a></div></td></tr>
                      </table>
                  </td>
                </tr>
              <tr><td height="10"></td></tr>''')
        
        # Residues for design       
        html.append('''
              <tr><td height="10"></td></tr>
                <tr>
                  <td align="left" valign="top">Residues for design<img src="../images/qm_s.png" title="%(tt_seqtol_design)s"></td>
                  <td>
                    <table bgcolor="#EEEEEE">
                      <tr bgcolor="#828282" style="color:white;">
                        <td>#</td><td>Chain ID</td><td>Residue Number</td>
                      </tr>
              ''' % self.tooltips)
        html.append('''<tr align="center" id="seqtol_SK_row_0"><td>1</td>
                    <td><select name="seqtol_SK_mut_c_0" style="text-align:center;">%s</select>
                    </td>
                    <td><input type="text" name="seqtol_SK_mut_r_0" maxlength=4 SIZE=4></td></tr>''' % chainOptions)
        for i in range(1, ROSETTAWEB_SK_MaxMutations):
            html.append('''<tr align="center" id="seqtol_SK_row_%d" style="display:none">
                        <td>%d</td>
                        <td><select name="seqtol_SK_mut_c_%d" style="text-align:center;">%s</select></td>
                        ''' % (i, i+1, i, chainOptions))
                
            html.append(''' <td><input type="text" name="seqtol_SK_mut_r_%d" maxlength=4 SIZE=4></td>
                        </tr>''' % i)
        html.append('''
                      <tr align="center"><td colspan="3"><div id="addmrow_2_1" style="display:none"><a href="javascript:void(0)" onclick="addOneMoreSeqtolSK();">Click here to add a residue</a></div></td></tr>
                      </table>
                  </td>
                </tr>
              <tr><td height="10"></td></tr>''')
        
        # Score reweighting        
        html.append('''               
              <tr><td height="10"></td></tr>
              <tr>
                  <td align="left">Score Reweighting<img src="../images/qm_s.png" title="%(tt_seqtol_SK_weighting)s"></td>
              ''' % self.tooltips)
        
        html.append('''
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
                ''' % (ROSETTAWEB_max_seqtol_SK_chains - 1))
        
        for i in range(1, ROSETTAWEB_max_seqtol_SK_chains):
            html.append('''<td class="seqtol_SK_kP%d" style="display:none">Partner %d</td>''' % (i - 1, i))
        
        html.append('''</tr>''')
        
        for i in range(0, ROSETTAWEB_max_seqtol_SK_chains):
            html.append('''   <tr align="center" id="seqtol_SK_weight_%d" style="display:none">                    
                          <td align="left">Partner %d</td>
                          <td><input type="text" name="seqtol_SK_kP%dP%d" maxlength=5 SIZE=4 VALUE="0.4"></td>
                           ''' % (i, i + 1, i, i))
                        
            for j in range(0, i):
                html.append('''<td class="seqtol_SK_kP%d"><input type="text" name="seqtol_SK_kP%dP%d" maxlength=5 SIZE=4 VALUE="1.0"></td>''' % (j, j, i))                           
            
            for j in range(i, ROSETTAWEB_max_seqtol_SK_chains - 1):
                html.append('''<td class="seqtol_SK_kP%d"></td>''' % j)   
            
            html.append("</tr>")
        
        
        # Boltzmann factor
        html.append('''</tr>
                </table>
                </td>
                </tr>
                <tr><td height="10"></td></tr>
                <tr>
                  <td align="left">Boltzmann Factor (kT)<img src="../images/qm_s.png" title="%(tt_seqtol_SK_Boltzmann)s"></td>
                  <td>
                  <input type="text" name="seqtol_SK_Boltzmann" disabled="true" maxlength=5 SIZE=5 VALUE="">                                 
                  </td>
                </tr>
                <tr>
                <td></td><td><input type="checkbox" name="customBoltzmann" checked="checked" value="Milk" onClick="set_Boltzmann();">Use published value</td>
                </tr>                   
            </table>
            </p>''' % self.tooltips)

        return html, postscript
    
    def showSequenceToleranceSK(self, status, cryptID, input_filename, size_of_ensemble, ProtocolParameters):

        html = ["""
              <tr><td align=right bgcolor="#EEEEFF">Task:         </td><td bgcolor="#EEEEFF">Interface Sequence Tolerance Prediction (Smith, Kortemme 2010)</td></tr>
              <tr><td align=right bgcolor="#EEEEFF">Input file:   </td><td bgcolor="#EEEEFF">%s</td></tr>
              <tr><td align=right bgcolor="#EEEEFF">No. Generated structures: </td><td bgcolor="#EEEEFF">%s</td></tr>
              <tr><td align=right valign=top bgcolor="#EEEEFF">Parameters:   </td>
                  <td bgcolor="#EEEEFF">
                      """ % ( input_filename, size_of_ensemble)]
                
        # Note:  We use get here rather than direct dictionary access as we choose not to 
        #        store empty keys in the parameter to save space
        numActive = 0
        for partner in ProtocolParameters["Partners"]:
            numActive += 1
            html.append('Partner %d: Chain %s<br>' % (numActive, partner))
            plist = ProtocolParameters["Premutated"][partner]
            if plist:
                html.append('<table><tr><td>&nbsp;&nbsp;</td><td><i>Premutated residues at positions:</i></td><td></td><td>')
                for k,v in sorted(plist.items()):
                    html.append('%s (%s) ' % (k, ROSETTAWEB_SK_AAinv[v]))
                html.append('</td></tr></table>')
            dlist = ProtocolParameters["Designed"][partner]
            if dlist:
                html.append('<table><tr><td>&nbsp;&nbsp;</td><td><i>Designed residues at positions:</i></td><td></td><td> %s</td></tr></table>' % (join(map(str, dlist.keys()),' ')))
        
        html.append('''<br>Boltzmann factor: %f 
                    <br><br>
                    Score Reweighting<br>
                    <table><tr>
                      <td> 
                        <table><thead>
                            <tr bgcolor="#828282" style="color:white;">
                            <td bgcolor="#EEEEFF"></td>
                            <td>Self Energy (k<sub>_</sub>)</td>''' % (ProtocolParameters["kT"]))

        for i in range(numActive - 1):
            html.append("<td>k<sub>P<sub>%s</sub></sub>_</td>" % (ProtocolParameters["Partners"][i]))
        
        html.append("</thead></tr><tbody bgcolor='#F4F4FF'>")
    
        weights = ProtocolParameters["Weights"]
        
        lweights = []
        offset = 0
        idx = 1 + numActive
        
        for i in range(numActive):
            numweights = numActive - i - 1
            if numweights:
                lweights.append(weights[idx : idx + numweights])
            idx += numweights
        
        for i in range(numActive):
            html.append("""
                    <tr align="left" border=1>                    
                          <td bgcolor="#828282" style="color:white; align="left">%s</td>
                          <td>%s</td>""" % (ProtocolParameters["Partners"][i], ProtocolParameters["Weights"][i+1]))
            for h in range(numActive - 1):
                if h < i:
                    html.append("<td>%s</td>" % lweights[h][i - h - 1])
                else:
                    html.append("<td bgcolor='#EEEEFF'></td>")
            html.append("</tr>")

        html.append("</tbody></table></td></tr></table>") 
        html.append("</td></tr>")
        
        #todo: if status == 'done' or status == 'sample':
        input_id = input_filename[:-4] # filename without suffix
        if status == 'done' or status == 'sample':
            html.append('<tr><td align=right></td><td></td></tr>')
            
            list_pdb_files = ['../downloads/%s/%s_0.pdb' % (cryptID, input_id) ]
            list_pdb_files.extend( [ '../downloads/%s/%s_0_%04.i_low.pdb' % (cryptID, input_id, i) for i in range(1,size_of_ensemble+1) ] )
            
            comment1 = """Backbone representation of the best scoring designs for 10 different initial backrub structures.<br>
                        The query structure is shown in red. 
                        The designed residues and premutated residues are shown in balls-and-stick representation.
                        Residues which are designed but not mutated have green backbone atoms.
                        Residues which are designed <i>and</i> mutated have yellow backbone atoms.
                        """
             
            designed_chains = []
            designed_res = []
            designed = {}
            for partner in ProtocolParameters["Partners"]:
                reslist = ProtocolParameters["Designed"][partner]
                if reslist:
                    designed[partner] = reslist.keys() 
                    designed_chains += [partner for res in reslist.keys()]
                    designed_res += reslist.keys()
        
            premutated = {}
            for partner in ProtocolParameters["Partners"]:
                reslist = ProtocolParameters["Premutated"][partner]
                if reslist:
                    premutated[partner] = reslist.keys()
             
            html.append(self._showApplet4MultipleFiles(comment1, list_pdb_files[:10], mutated = premutated, designed=designed)) # only the first 10 structures are shown
            
            #todo: text
            html.append('''<tr><td align="left" bgcolor="#FFFCD8">A ranked table of amino acid types for each position.<br>
                              Download the table as 
                              <a href="../downloads/%s/tolerance_seqrank.png">PNG</a>, <a href="../downloads/%s/tolerance_seqrank.pdf">PDF</a>.<br>
                              </td>
                           <td bgcolor="#FFFCD8">
                    ''' % ( cryptID, cryptID ))
                    
                    # To rerun the analysis we provide the <a href="../downloads/specificity.R">R-script</a> that was used to analyze this data. 
                    # A <a href="../wiki/SequenceTolerancePrediction" target="_blank">tutorial</a> on how to use the R-script can be found on 
                    # the <a href="../wiki/" target="_blank">wiki</a>.
            
            html.append('''<a href="../downloads/%s/tolerance_seqrank.png"><img src="../downloads/%s/tolerance_seqrank.png" alt="image file not available" width="400"></a><br>
                        </td>
                        </tr>
                        <tr><td align="left" bgcolor="#FFFCD8">Individual boxplots of the predicted frequencies at each mutated site.<br>
                              Download <a href="../downloads/%s/tolerance_pwm.txt">weight matrix</a> or file with all plots as 
                              <a href="../downloads/%s/tolerance_boxplot.png">PNG</a>, <a href="../downloads/%s/tolerance_boxplot.pdf">PDF</a>.<br>
                              </td>
                           <td bgcolor="#FFFCD8">''' % ( cryptID, cryptID, cryptID, cryptID, cryptID ))
                    
                    # To rerun the analysis we provide the <a href="../downloads/specificity.R">R-script</a> that was used to analyze this data. 
                    # A <a href="../wiki/SequenceTolerancePrediction" target="_blank">tutorial</a> on how to use the R-script can be found on 
                    # the <a href="../wiki/" target="_blank">wiki</a>.
            
            for (chain, resid) in zip(designed_chains, designed_res):
              html.append('''<a href="../downloads/%s/tolerance_boxplot_%s%s.png"><img src="../downloads/%s/tolerance_boxplot_%s%s.png" alt="image file not available" width="400"></a><br>
                    ''' % ( cryptID, chain, resid, cryptID, chain, resid ))
                            
            
            #todo: I arbitrarily chose the image size below.
            WebLogoText = self.WebLogoText
            html.append('''</td></tr>
                        <tr><td align="left" bgcolor="#FFFCD8">Predicted sequence tolerance of the mutated residues.<br>Download corresponding <a href="../downloads/%(cryptID)s/tolerance_sequences.fasta">FASTA file</a>.</td>
                             <td align="center" bgcolor="#FFFCD8"><a href="../downloads/%(cryptID)s/tolerance_motif.png">
                                                   <img height="250" src="../downloads/%(cryptID)s/tolerance_motif.png" alt="image file not available" ></a><br>
                             %(WebLogoText)s
                             </td></tr> ''' % vars())

        return html  


#########################################################
# Private functions mainly called by __init__ and main 
#########################################################

    def _referenceAll(self):
        refs = sorted(self.refs.iteritems())
        i = 0
        for reftag, reference in refs:
            i += 1
            self.html_refs += '<P>[<a name="ref%s">%d</a>] %s</P>' % (reftag, i, reference)

    def _setupJavascript(self):
        # Save out the protocol information
        # Arrays containing the lengths of the protocol groups (the number of tasks in each group)
        # and the binaries used by each protocol. 
        JS = []
        JS.append('<script type="text/javascript">//<![CDATA[')
        
        pts = "protocolTasks = ["
        pbs = "protocolBins = [" 
        pnos = "protocolNos = ["
        colors = "colors = ["           # The background colors for the protocol groups
        protocolGroups = self.protocolGroups
        for i in range(len(protocolGroups)):
            pglen = len(protocolGroups[i].getProtocols())
            pts += "%d," % pglen
            colors += "'%s'," % protocolGroups[i].color
            pbs += "["
            pnos += "["
            for j in range(pglen):
                pbs += str(protocolGroups[i][j].binaries) + ","
                pnos += str(protocolGroups[i][j].nos) + ","
            pbs = pbs[0:len(pbs) - 1]
            pnos = pnos[0:len(pnos) - 1]
            pnos += "],"
            pbs += "],"
        
        bversion = "bversion = new Array();\n"
        for binname, v in RosettaBinaries.items():
            bversion += 'bversion["%s"] = %s;\n' % (binname, str(v["mini"]).lower())
        
        pts = (pts + "]").replace(",]", "]")
        colors = (colors + "]").replace(",]", "]")
        pbs = (pbs + ")").replace(",)", "]")
        pbs = pbs.replace("(","[")
        pbs = pbs.replace(")","]")
        pnos = (pnos + ")").replace(",)", "]")
        pnos = pnos.replace("(","[")
        pnos = pnos.replace(")","]")
        
        JS.append(pts)
        JS.append(pbs)
        JS.append(pnos)
        JS.append(colors)
        JS.append(bversion)
        
        # Embed the Python constants into the Javascript
        JS.append("""   const HK_MaxMutations = %d;
                        const SK_max_seqtol_chains = %d;
                        const SK_InitialBoltzmann = %f;
                        const SK_BoltzmannIncrease = %f;
                        const SK_MaxMutations = %d;
                        const SK_MaxPremutations = %d;
                        const MaxMultiplePointMutations = %d;
                    """ % (ROSETTAWEB_HK_MaxMutations, ROSETTAWEB_max_seqtol_SK_chains, ROSETTAWEB_SK_InitialBoltzmann, 
                           ROSETTAWEB_SK_BoltzmannIncrease, ROSETTAWEB_SK_MaxMutations, ROSETTAWEB_SK_MaxPremutations, 
                           ROSETTAWEB_MaxMultiplePointMutations))
        JS.append('//]]></script>')
        self.JS = JS
                    
    def _showHeader(self):
        html = '''<td align=center style="border-bottom:1px solid gray;"> 
                    <A href="../"><img src="../images/header.png" border="0" usemap="#links"></A> 
                  </td>
                  '''
        return html

    def _showLoginStatus(self):
        """shows a little field with the username if logged in """
        html = []
        html.append('<td align="right">[&nbsp;Other Services: <A class="nav" style="color:green;" href="/alascan">Alanine Scanning</A>&nbsp;] ')
        if self.username != '':
            html.append('<br><small>[ <font color=green>%s</font> | <a href="%s?query=logout"><small>Logout</small></a> ]</small></td>' % ( self.username, self.script_filename ))
        else:
            html.append('<br><small>[&nbsp;<font color=red>not logged in</font>&nbsp;]</small></td>') 
        return join(html, "")

    def _showWarning(self):
        if self.warning != '':
            return '''<td align="center">
                            <table width="500"><tr><td align="center" style="padding-left:20px; padding-right:20px; padding-top:10px; padding-bottom:10px; border-color:red; border-style:dashed; border-width:2px;">
                                <font color="black" >%s</font></td></tr>
                            </table>
                     </td></tr><tr>''' % self.warning #style="text-decoration:blink;"

        if self.comment != '':
            return '''<td align="center" style="padding:10px;">
                                <table width="500"><tr><td align="center" style="padding-left:20px; padding-right:20px; padding-top:10px; padding-bottom:10px; padding-left:10px; border-color:orange; border-style:dashed; border-width:2px;">
                                    <font color="red">%s</font></td></tr>
                                </table>
                      </td>''' % self.comment
        return ''

    def _showMenu(self):
        s1 = ""
        s2 = ""
        if self.username != '':
            s1 = """
                    [&nbsp;<A class="nav" href="%s?query=submit">Submit</A>&nbsp;] &nbsp;&nbsp;&nbsp;
                    [&nbsp;<A class="nav" href="%s?query=queue">Queue</A>&nbsp;] &nbsp;&nbsp;&nbsp;""" % (self.script_filename,self.script_filename)
            if self.username != "guest":
                s2 = """[&nbsp;<A class="nav" href="%s?query=update">My Account</A>&nbsp;]""" % (self.script_filename)
        
        html = """
                <tr><td align=center>
                    [&nbsp;<A class="nav" href="%s?query=index" >Home</A>&nbsp;] &nbsp;&nbsp;&nbsp;
                    [&nbsp;<A class="nav" href="../wiki/" target="_blank">Documentation</A>&nbsp;] &nbsp;&nbsp;&nbsp;
                    [&nbsp;<A class="nav" href="%s?query=register">Register</A>&nbsp;]
                </td></tr>
                <tr><td align=center> %s %s \n</td></tr>""" % (self.script_filename,self.script_filename, s1, s2)
    
        return html

    def _showLegalInfo(self):
        html = """<td style="border:1px solid black; padding:10px" bgcolor="#FFFFE0">
                    <p style="text-align:left; font-size: 10pt">
                      For questions, please read our <A href="../wiki/">documentation</A>, see the reference below, or contact <img src="../images/support_email.png" style="vertical-align:text-bottom;" height="15">.
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
    

###############################################################################################
# End of HTML class                                                                                             #
###############################################################################################



if __name__ == "__main__":
    """here goes our testcode"""

    from cStringIO import StringIO

    s = sys.stdout

    s.write("Content-type: text/html\n\n\n")

    test_html = RosettaHTML('albana.ucsf.edu', 'Structure Prediction Backrub', 'rosettahtml.py', 'Tanja Kortemme', 'DFTBA', comment='this is just a test')

    #html_content = test_html.index() 
    html_content = test_html.submit()
    #html_content = test_html.register( error='You broke everything', update=True )
    #html_content = test_html.login()  
    #html_content += '</tr><tr>'  
    #html_content += test_html.logout('DFTBA')
    #html_content = test_html.sendPassword()
    
    s.write( test_html.main(html_content) )

    s.close()


