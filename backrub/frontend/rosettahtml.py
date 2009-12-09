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

class RosettaHTML:

    server = {}

    def __init__(self, server_url, server_title, script_filename, download_dir, username='', comment='', warning='', contact_email='lauck@cgl.ucsf.edu' , contact_name='FLO'):
        self.server_url      = server_url
        self.server_title    = server_title
        self.script_filename = script_filename
        self.username        = username
        self.comment         = comment
        self.warning         = warning
        self.contact_email   = contact_email
        self.contact_name    = contact_name
        self.download_dir    = download_dir


        #self.server = { 'Structure Prediction Backrub': 'http://%s/backrub' % self.server_url,
                        #'Interface Alanine Scanning' : 'http://%s/alascan/' % self.server_url,
                        #'more server soon' : 'http://kortemmelab.ucsf.edu/' }
                        # THIS gets to complicated
        tooltip_parameter = "offsetx=[-90] offsety=[20] singleclickstop=[on] cssbody=[tooltip] cssheader=[tth] delay=[250]"
        self.tooltips = { 
                        "tt_empty":         "header=[] body=[] %s" % tooltip_parameter,
                        "tt_general":       "header=[General Settings] body=[These settings are common for all applications.] %s" % tooltip_parameter,
                        "tt_specific":      "header=[Application Specific Settings] body=[These settings are dependent on the applications. If you are not sure use the standard values.] %s" % tooltip_parameter,
                        "tt_JobName":       "header=[Name for your job] body=[Enter a name that helps you identifying your job later.] %s" % tooltip_parameter,
                        "tt_Structure":     "header=[Structure File] body=[Enter the path to a protein structure file in PDB format. For NMR structures only the first model in teh file is considered.] %s" % tooltip_parameter,
                        "tt_StructureURL":  "header=[URL to Structure File] body=[Enter the path to a protein structure file in PDB format. For NMR structures only the first model in teh file is considered.] %s" % tooltip_parameter,
                        "tt_RVersion":      "header=[Rosetta Version] body=[Choose the version of Rosetta, either Rosetta 2 (\'classic\') or the new Rosetta 3 (\'mini\'). Some applications only work with one version.] %s" % tooltip_parameter,
                        "tt_NStruct":       "header=[Number of Structures] body=[Number of generated structures or size of ensemble.] %s" % tooltip_parameter,
                        "tt_ROutput":       "header=[Rosetta output] body=[If checked, the raw output of the Rosetta run is stored. Does not apply to all applications.] %s" % tooltip_parameter,
                        "tt_SelApp":        "header=[Select Application] body=[Click to choose one of the applications. Each application will give you a short explanation and a set of parameters that can be adjusted.] %s" % tooltip_parameter,
                        "tt_ChainId":       "header=[Chain ID] body=[The chain in which the residue is located.] %s" % tooltip_parameter,
                        "tt_ResId":         "header=[Residue ID] body=[The position (residue ID according to the PDB file) that is going to be mutated.] %s" % tooltip_parameter,
                        "tt_NewAA":         "header=[New Amino Acid] body=[The Amino Acid to which the position is going to be mutated.] %s" % tooltip_parameter,
                        "tt_Radius":        "header=[Radius] body=[This radius determines the area around the mutation that is subject to backrub. For detailed information see the referenced paper.] %s" % tooltip_parameter,
                        "tt_Temp":          "header=[Temperature] body=[at which backrub is carried out.] %s" % tooltip_parameter,
                        "tt_NSeq":          "header=[Number of Sequences] body=[The number of designed sequences for each ensemble structure.] %s" % tooltip_parameter,
                        "tt_SegLength":     "header=[Maximal segment length for backrub] body=[Limit the length of the segment to which the bachrub move is applied to.] %s" % tooltip_parameter,
                        "tt_error":         "header=[Rosetta Error</b></font><br>Rosetta (classic and mini) fail for some PDB files that have inconsistent residue numbering or miss residues. If an error occures for your structure please check the correctness of the PDB file.] %s" % tooltip_parameter,
                        "tt_seqtol_partner":"header=[Partner] body=[The two chains in the PDB file that form an interface.] %s" % tooltip_parameter,
                        "tt_seqtol_list":   "header=[List] body=[List of residue-IDs of <b>Chain 2</b> that are subject to mutations. Enter residue-IDs seperated by a space.] %s" % tooltip_parameter,
                        "tt_seqtol_radius": "header=[Radius] body=[Defines the size of the interface. A residue is considered to be part of the interface if at least one of its atoms is within a sphere of radius r from any atom of the other chain.] %s" % tooltip_parameter,
                        "tt_seqtol_weights":"header=[Weights] body=[Describes how much the algorithm emphazises the energetic terms of this entity. The default of 1,1,2 emphasizes the energetic contributions of the interface. The interface is weighted with 2, while the energies of partner 1 and partner 2 are weighted with 1, respectively.] %s" % tooltip_parameter,
                        "tt_seqtol_design": "header=[Residues for design] body=[Rosetta is going to substitute these residues in order to find energetically stable sequences.] %s" % tooltip_parameter,
                        }
        
        

    def setUsername(self, username):
        self.username = username

    def main(self, CONTENT='This server is made of awesome.', site='', query='' ):
        html = """
            <!-- *********************************************************
                 * Rosetta Web Server - Python - BACKRUB                 *
                 * Kortemme Lab, University of California, San Francisco *
                 * Tanja Kortemme, Florian Lauck, 2009                   *
                 ********************************************************* -->
            <html>
            <head>
                <title>%s - %s</title>
                <META name="description" content="Structure Prediction using Backrub.">
                <META name="keywords" content="rosetta baker kortemme protein structure prediction backrub protein design point mutation">
                
                <link rel="STYLESHEET" type="text/css" href="../style.css">
                
                <script src="/javascripts/prototype.js" type="text/javascript"></script>
                <script src="/javascripts/scriptaculous.js" type="text/javascript"></script>
                <script src="/javascripts/niftycube.js" type="text/javascript"></script>
                <script src="/javascripts/boxover.js" type="text/javascript"></script>
                <script src="/jmol/Jmol.js" type="text/javascript"></script>
                <script src="/backrub/jscripts.js" type="text/javascript"></script>
            </head>

            <body bgcolor="#ffffff" onload="startup( \'%s\' );">
            <center>
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
           </html>\n""" % ( self.server_title, site,
                            query,
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
        html = ''
        if self.username != '':
            html += '<td align=right><small>[ <font color=green>%s</font> | <a href="%s?query=logout"><small>Logout</small></a> ]</small></td>' % ( self.username, self.script_filename )
        else:
            html += '<td align=right><small>[&nbsp;<font color=red>not logged in</font>&nbsp;]</small></td>'
        return html

    def _showWarning(self):
        html = ''
        if self.warning != '':
            html += '''<td align="center">
                            <table width="500"><tr><td style="padding-left:20px; padding-right:20px; padding-top:10px; padding-bottom:10px; border-color:red; border-style:dashed; border-width:2px;">
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
                    [&nbsp;<A class="nav" href="../wiki/">Documentation</A>&nbsp;] &nbsp;&nbsp;&nbsp;
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
                    <p style="text-align:left; font-size: 10pt" >
                      For questions, please read our <A href="../wiki/">documentation</A> or contact <A href="mailto:%s" style="font-size: 10pt">%s</A>
                    </p>
                  </td>""" % ( self.contact_email, self.contact_name )
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
# submit()                                                                                    #
###############################################################################################

    def submit(self, jobname='' ):
    	# this function uses javascript functions from jscript.js
		# if you change the application tabler here, please make sure to change jscript.js accordingly
		# calling the function with parameters will load those into the form. #not implemented yet
        self.tooltips.update({'username':self.username, 'jobname':jobname, 'script':self.script_filename})
      
        html = '''<td align="center">
    <H1 class="title">Submit a new job</H1>
    <br>
<!-- Start Submit Form -->
    <FORM NAME="submitform" method="POST" onsubmit="return ValidateForm();" enctype="multipart/form-data">

      <table border=0 cellpadding=0 cellspacing=0>
        <colgroup>
          <col width="210">
          <col width="500">
        </colgroup>
        <tr>
<!-- left column = menu -->
          <td id="columnLeft" align="right" style="vertical-align:top; margin:0px;">
          <ul id="about">
            <li id="ab1">
              [ <A href="/alascan/" class="nav" target="_blank">Interface Alanine Scanning</A> ]<br><center><small>opens in a new window</small></center>
            </li>
            <li id="ab2">
              <A href="javascript:void(0)" class="nav" onclick="showMenu('1'); ">Point Mutation</A>            
              <p id="menu_1" style="display:none; opacity:0.0; text-align:left; margin:0px;">
                <font style="font-size:8pt">[ Smith and Kortemme, 2008 ]</font>
                  <table style="border:0px; padding:0px; margin:0px;">
                  <tr><td width="10" style="text-align:right;">&#8680;</td><td><a href="javascript:void(0)" onclick="changeApplication('1','1'); ">One mutation</a></td></tr>
                  <tr><td width="10" style="text-align:right;">&#8680;</td><td><a href="javascript:void(0)" onclick="changeApplication('1','2'); ">Multiple mutations</a></td></tr>
                  <!-- tr><td width="10" style="text-align:right;">&#8680;</td><td><a href="javascript:void(0)" onclick="changeApplication('1','3'); ">Upload List</td></tr -->
                  </table>
              </p>
            </li>
            <li id="ab3">
              <A href="javascript:void(0)" class="nav" onclick="showMenu('2'); ">Backrub Ensembles</A>
              <p id="menu_2" style="display:none; opacity:0.0; text-align:right; margin:0px;">
                  <table style="border:0px; padding:0px; margin:0px;">
                  <tr><td width="10" style="text-align:right;">&#8680;</td><td><a href="javascript:void(0)" onclick="changeApplication('2','1'); "><font style="font-size:10pt">Generate Backrub Ensemble</font></a><br><font style="font-size:8pt">[ Smith and Kortemme, 2008 ]</font></td></tr>
                  <tr><td width="10" style="text-align:right;">&#8680;</td><td><a href="javascript:void(0)" onclick="changeApplication('2','2'); "><font style="font-size:10pt">Backrub Ensemble Design</font></a><br><font style="font-size:8pt">[ Friedland et. al., 2008 ]</font></td></tr>
                  </table>
              </p>
            </li>
            <li id="ab4">
              <A href="javascript:void(0)" class="nav" onclick="showMenu('3');">Sequence Plasticity Prediciton</A>
              <p id="menu_3" style="display:none; opacity:0.0; text-align:right;">
                  <table style="border:0px; padding:0px; margin:0px;">
                  <tr><td width="10" style="text-align:right;">&#8680;</td><td><a href="javascript:void(0)" onclick="changeApplication('3','1');">Enter Data</a></td></tr>
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
              <img src="../images/logo1.png" width="85%%" alt="Rosetta" border=0>
            </p>

            <p id="pic2" style="display:none; text-align:center;">
              logo2
              <!-- img src="../images/logo2.png" width="85%%" alt="Rosetta" border=0 -->
            </p>
            
            <p id="pic3" style="display:none; text-align:center;">
              logo3
              <!-- img src="../images/logo2.png" width="85%%" alt="Rosetta" border=0 -->
            </p>

          <!-- end pictures -->
          <!-- description -->
            <p id="text0" style="text-align:justify;">
              Choose one of the applications on the left. Each application will give you a short explanation and a set of parameters that can be adjusted.<br><br>
              For a brief explanation hover your mouse over the parameter.
            </p>
          
            <div id="text1" style="display:none; opacity:0.0; text-align:justify;"> 
                This function utilizes the backrub protocol implemented in Rosetta and applies it to the neighborhood 
                of a mutated residue to account for the conformational changes in this region. 
                There are two options.
                <dl style="text-align:left;">
                    <dt><b>One Mutation</b></dt><dd>A single residue will be substituted and the neigboring residue in a radius of 6&#197; will be repacked. This value was empirically determined (see reference).</dd>
                    <dt><b>Multiple Mutations</b></dt><dd>Up to 30 residues can be mutated and their neighborhoods repacked. This method has not been benchmarked yet.</dd>
                    <!-- dt>Upload List</dt><dd>Upload a list with single residue mutations.</dd -->
                </dl>
            </div>

            <div id="text2" style="display:none; opacity:0.0; text-align:justify;"> 
                This function utilizes backrub and design protocols implemented in ROSETTA. 
                There are two options.
                <dl style="text-align:left;">
                    <dt><b>Generate Backrub Ensemble</b></dt><dd>Backrub is applied to the input structure in order to model backbone flexibility.</dd>
                    <dt><b>Backrub Ensemble Design</b></dt>
                      <dd>This method first creates an ensemble of structures that resembles the flexibility in solution. 
                          These ensembles are similar to the ensembles detected by the NMR method.<br> 
                          In a second step the generated protein structures are used to design an ensemble that has similar properties as the natural occuring protein family.
                          The output is a sequence profile of this family of structures.</dd>
                </dl>
            </div>
            
            <div id="text3" style="display:none; opacity:0.0; text-align:justify;"> 
                This function utilizes backrub and design protocols implemented in Rosetta.<br><br>
                First, the backrub algorithm is applied to the uploaded complex in order to generate an ensemble.
                Then, for each of the resulting structure the given residues are mutated by an genetic algorithm. 
                All generated sequences are ranked by their score and used to build a sequence profile.
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
              <TR>
                <TD align=right title="%(tt_JobName)s">Job Name </TD>
                <TD align=left style="padding-left:5pt; padding-top:5pt;"><INPUT TYPE="text" maxlength=40 SIZE=31 NAME="JobName" VALUE="%(jobname)s"></TD>
              </TR>
              <TR>
                <TD align=right title="%(tt_Structure)s">Upload Structure </TD>
                <TD align=left style="padding-left:5pt; padding-top:5pt;" > <INPUT TYPE="file" NAME="PDBComplex" size="20"></TD>
              </TR>
              <TR><TD align="center" colspan="2" style="padding-bottom:0pt; padding-top:0pt;">or</TD></TR>
              <TR>
                <TD align=right title="%(tt_StructureURL)s"> Enter URL to structure file </TD>
                <TD align=left style="padding-left:5pt; padding-top:5pt;" > <INPUT TYPE="text" NAME="PDBComplexURL" size="31">
              </TD>
              </TR>
              <TR><TD colspan=2><br></TD></TR>
              <TR>
                <TD align="center" colspan=2 style="border-bottom:1pt dashed black" title="%(tt_general)s">General Settings</TD>
              </TR>
              <TR>
                <TD align=right title="%(tt_RVersion)s">Rosetta Version </TD>
                <TD id="rosetta1" style="padding-left:5pt; padding-top:5pt;">
                    <input type="radio" name="Mini" value="classic" checked> Rosetta v.2 (classic)<br>
                    <input type="radio" name="Mini" value="mini"> Rosetta v.3 (mini)
                </TD>
              </TR>
              <TR>
                <TD align=right title="%(tt_NStruct)s">Number of structures </TD>
                <TD style="padding-left:5pt; padding-top:5pt;"> <input type="text" name="nos" maxlength=3 SIZE=5 VALUE=""> (max 100) </TD>
              </TR>
              <!-- TR>
                <TD align=right title="%(tt_ROutput)s">ROSETTA output </TD>
                <TD id="rosetta2" style="padding-left:5pt; padding-top:5pt;"> <input type="checkbox" name="keep_output" VALUE="1" disabled checked> keep files</TD>
              </TR -->
              <TR><TD align=left><br></TD></TR>
              <TR>
                <TD align="center" colspan=2 style="border-bottom:1pt dashed black" title="%(tt_specific)s">Application Specific Settings</TD>
              </TR>
            </TABLE>
            
            <!-- Backrub - Point Mutation -->
            <p id="parameter1_1" style="display:none; opacity:0.0; text-align:justify;">
                <table align=center>
                <tr>
                    <td align="right" title="%(tt_ChainId)s">Chain ID </td><td><input type="text" name="PM_chain"  maxlength=1 SIZE=5 VALUE=""></td>
                </tr>
                <tr>
                    <td align="right" title="%(tt_ResId)s">Residue ID </td><td><input type="text" name="PM_resid"  maxlength=4 SIZE=5 VALUE=""></td>
                </tr>
                <tr>
                    <td align="right" title="%(tt_NewAA)s">New Amino Acid </td><td><input type="text" name="PM_newres" maxlength=1 SIZE=5 VALUE=""></td>
                </tr>
                <tr>
                    <td><INPUT TYPE="hidden" NAME="PM_radius" VALUE="6.0"></td>
                </tr>
                </table>
                <br>
            </p>
            
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
                <tr><td align="center" colspan="4"><a href="javascript:void(0)" onclick="addOneMore();">Click here to add a mutation</a></td></tr>
                </table>
                
            </p>
            
            <!-- Backrub - Costum Mutation -->
            <p id="parameter1_3" style="display:none; opacity:0.0; text-align:justify;"><b>Custom mutation.</b><br><br>
                This allows for a more flexible definition of mutations. Detailed information about the format of the file can be found in the <A style="color:#365a79; "href="%(script)s?query=doc#mutations">documentation</A>. <br>
                <font style="text-align:left;">Upload file <INPUT TYPE="file" NAME="Mutations" size="13"></font>
            </p>
            
            <!-- Ensemble - simple -->
            <p id="parameter2_1" style="display:none; opacity:0.0; text-align:center;">no options</p>
            
            <!-- Ensemble - design -->
            <p id="parameter2_2" style="display:none; opacity:0.0; text-align:center;">
                <table align="center">
                <tr>
                    <td title="%(tt_Temp)s">Temperature [kT]</td><td><input type="text" name="ENS_temperature" maxlength=3 SIZE=5 VALUE="0.3"></td>
                </tr>
                <tr>
                    <td title="%(tt_NSeq)s">No. of sequences</td><td><input type="text" name="ENS_num_designs_per_struct" maxlength=4 SIZE=5 VALUE="20"></td>
                </tr>
                <tr>
                    <td title="%(tt_SegLength)s">Max. segment length</td><td><input type="text" name="ENS_segment_length" maxlength=1 SIZE=5 VALUE="12"></td>
                </tr>
                </table>
            </p>
            
            <!-- Library Design -->
            <p id="parameter3_1" style="display:none; opacity:0.0; text-align:center;">
            <table align="center">
              <tr>
                  <td align="right" title="%(tt_seqtol_partner)s">Partner 1:</td>
                  <td>Chain <input type="text" name="seqtol_chain1" maxlength=1 SIZE=2 VALUE=""></td>
              </tr>
              <tr>
                  <td align="right" title="%(tt_seqtol_partner)s">Partner 2:</td>
                  <td>Chain <input type="text" name="seqtol_chain2" maxlength=1 SIZE=2 VALUE="">
                  </td>
              </tr>
              <!-- tr>
                  <td align="right" title="%(tt_seqtol_list)s">Residues of Partner 2</td>
                  <td><input type="text" name="seqtol_list" maxlength=120 SIZE=10 VALUE="">
                  </td>
              </tr -->
              <tr>
                  <td align="right" title="%(tt_Radius)s">Area for repacking.</td>
                  <td>Radius<input type="text" name="seqtol_radius" maxlength=5 SIZE=4 VALUE="4.0"> &#197;</td>
              </tr>
              <tr>
                  <td align="right" title="%(tt_seqtol_weights)s">Weight for Partner</td>
                  <td>
                    <table >
                      <tr >
                        <td align="center">1:</td><td align="center"><input type="text" name="seqtol_weight_chain1" maxlength=1 SIZE=2 VALUE="1"></td>
                        <td align="center">2:</td><td align="center"><input type="text" name="seqtol_weight_chain2" maxlength=1 SIZE=2 VALUE="1"></td>
                        <td align="center">interface:</td><td align="center"><input type="text" name="seqtol_weight_interface" maxlength=1 SIZE=2 VALUE="2"></td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <tr>
                  <td align="right" title="%(tt_seqtol_design)s">Residues for design</td>
                  <td>
                    <table bgcolor="#EEEEEE">
                      <tr bgcolor="#828282" style="color:white;">
                        <td>#</td<td>Chain ID</td><td>Residue ID</td>
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
                      <tr align="center"><td colspan="3"><a href="javascript:void(0)" onclick="addOneMoreSeqtol();">Click here to add a mutation</a></td></tr>
                      </table>
                  </td>
                </tr>
            </table>
            </p>
            
            <p id="parameter_submit" style="display:none; opacity:0.0; text-align:center;">
              <input type="button" value="Load sample data" onClick="set_demo_values();">
              &nbsp;&nbsp;&nbsp;&nbsp;<input type="button" value="Reset Form" onClick="this.form.reset()">
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

          </div> <!-- id=box -->  
          </td>
<!-- end right column -->            
        </tr>
      </table>
            <INPUT TYPE="hidden" NAME="task"  VALUE="init">
            <INPUT TYPE="hidden" NAME="query" VALUE="submitted">
            <INPUT TYPE="hidden" NAME="mode"  VALUE="check">
          </FORM>
<!-- End Submit Form -->
        </td>''' % self.tooltips

        return html


    def submited(self, jobname='', cryptID=''):
        html = """<td align="center"><H1 class="title">New Job successfully submitted</H1> 
                  <table width="550"><tr><td class="linkbox" align="center">
                    <font color="black" style="font-weight: bold; text-decoration:blink;">If you are a guest user bookmark this link!</font><br>
                    <a class="blacklink" href="https://%s/backrub/downloads/%s" target="_blank">https://%s/backrub/downloads/%s</a>
                    </td></tr></table><br>
                  <P>Once your request has been processed the results are accessible via the above URL. You can also access your data via the <A href="%s?query=queue">job queue</A> at any time.<br>
                  If you <b>are not</b> registered and use the guest access please bookmark this link, your data will be stored for 10 days.<br>
                  If you are registered and logged in we will send you an email with this information once the job is finished, in this case you will be able to access your data for 60 days.<br>
                  </P>
                  From here you can proceed to the <a href="%s?query=jobinfo&jobnumber=%s">job info page</a>, 
                  <a HREF="javascript:history.go(-1)"><b>resubmit this job</b></a>, or 
                  <a href="%s?query=submit">submit a new job</a>.<br><br>
                  </td>\n"""  % ( self.server_url, cryptID, self.server_url, cryptID, self.script_filename, self.script_filename, cryptID, self.script_filename )
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
        Please enter all required (*) information.  
        This account will also be valid for <A href="http://albana.ucsf.edu/alascan/">Alanine Scanning</A>. 
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
            <tr><td align=right class="register">Institution: </td>
                <td><input type=text size=20 maxlength=50 name="institution" value="%s"></td>
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
                  <table border=0 cellpadding=2 cellspacing=1 width=700 >
                   <colgroup>
                     <col width="25">
                     <col width="60">
                     <col width="90">
                     <col width="90">
                     <col width="200">
                     <col width="140">
                     <col width="25">
                     <col width="70">
                   </colgroup>
                  <tr align=center bgcolor="#828282" style="color:white;"> 
                   <td > ID </td> 
                   <td > Status </td> 
                   <td > User Name </td>
                   <td > Date (PST) </td>
                   <td > Job Name </td>
                   <td > Rosetta Application </td>
                   <td > Structures </td>
                   <td > Error </td></tr>\n"""
                   
        for line in job_list:
            task = ''
            if line[9] == '0' or line[9] == 'no_mutation':
                task = "Backrub Ensemble"
            elif line[9] == '1' or line[9] == 'point_mutation':
                task = "Point Mutation"
            elif line[9] == '3' or line[9] == 'multiple_mutation':
                task = "Multiple Point Mutations"
            elif line[9] == '2' or line[9] == 'upload_mutation':
                task = "Custom Mutation"
            elif line[9] == '4' or line[9] == 'ensemble':
                task = "Backrub Ensemble Design"
            elif line[9] == 'sequence_tolerance':
                task = "Sequence Plasticity"
          
            html += """<tr align=center bgcolor="#EEEEEE" onmouseover="this.style.background='#447DAE'; this.style.color='#FFFFFF'" onmouseout="this.style.background='#EEEEEE'; this.style.color='#000000'" onclick="window.location.href='%s?query=jobinfo&jobnumber=%s'">""" % ( self.script_filename, line[1] )
            # write ID
            html += '<td>%s </td>' % (str(line[0]))
            # write status 
            status = int(line[2])  
            if status == 0:
                html += '<td><font color="orange">in queue</font></td>'
            elif status == 1:
                html += '<td><font color="green">active</font></td>'
            elif status == 2:
                html += '<td><font color="darkblue">done</font></td>'
            elif status == 5:
                html += '<td><font color="darkblue" style="background-color: #AFE2C2;">sample</font></td>'
            else:
                html += '<td><font color="FF0000">error</font></td>'
                
            # write username
            html += '<td>%s</td>' % str(line[3])
            # write date
            html += '<td style="font-size:small;">%s</td>' % str(line[4])
            # write jobname or "notes"
            if len(str(line[5])) < 26:
                html += '<td>%s</td>' % str(line[5])
            else:
                html += '<td>%s</td>' % (str(line[5])[0:23] + "...")
            # Rosetta version
            if line[6] == '1' or line[6] == 'mini':
                html += '<td style="font-size:small;"><i>mini</i><br>%s</td>' % task
            elif line[6] == '0' or line[6] == 'classic':
                html += '<td style="font-size:small;"><i>classic</i><br>%s</td>' % task
            # write size of ensemble
            html += '<td>%s</td>' % str(line[7])
            # write error
            html += '<td>%s</td>' % str(line[8])
        
            html += '</tr>\n'
        
        html += '</table> <br> </td>'
        
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
        else:
            status_html = '<font color="FF0000">error:</font> %s' % error
        
        html += """
                <tr><td align=right bgcolor="#EEEEFF">Job Name:       </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Status:         </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#FFFFFF"></td><td bgcolor="#FFFFFF"></td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Submitted from: </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Date Submitted: </td><td bgcolor="#EEEEFF">%s</td></tr>
                """ % ( jobname, status_html, hostname, date_submit )
                
        if status == 'active':
            html += '<tr><td align=right bgcolor="#EEEEFF">Started:        </td><td bgcolor="#EEEEFF">%s</td></tr>\n' % ( date_start )
        
        if status == 'done':
            html +="""
                <tr><td align=right bgcolor="#EEEEFF">Started:        </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Ended:          </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Computing time: </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Expires:        </td><td bgcolor="#EEEEFF">%s (%s)</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Binary:         </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#FFFFFF"></td><td bgcolor="#FFFFFF"></td></tr>
                """ % ( date_start, date_end, time_computation, date_expiration, time_expiration, rosetta )
        
        if delete or restart:
            html += '<tr><td align=right bgcolor="#FFFFFF"></td><td bgcolor="#FFFFFF"></td></tr>'
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

        return html
    
    def _show_molprobity(self,cryptID):
      
      html = '''<tr><td align="left" bgcolor="#FFFCD8">Analysis of the generated ensemble with Molprobity.
                                                       The red circle denotes the mean, the blue diamond the value from the input structure.
                              <ul><li><a href="../downloads/%s/molprobity_data.txt">Data shown in Plot</a></li>
                                  <li><a href="../downloads/%s/molprobity_raw_output.txt">raw output</a></li></ul></td>
                <td bgcolor="#FFFCD8"><a href="../downloads/%s/molprobity_plot.png">
                                      <img src="../downloads/%s/molprobity_plot.png" alt="image missing." width="400"></a>
                                      </td></tr>''' % ( cryptID,cryptID,cryptID,cryptID)
      return html
    
    
    def _showNoMutation(self, status, input_filename, size_of_ensemble, cryptID):

        html = """
                <tr><td align=right bgcolor="#EEEEFF">Task:           </td><td bgcolor="#EEEEFF">No Mutation</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Input file:     </td><td bgcolor="#EEEEFF">%s</td></tr> 
                <tr><td align=right bgcolor="#EEEEFF">No. Generated structures: </td><td bgcolor="#EEEEFF">%s</td></tr>
                """ % ( input_filename, size_of_ensemble )
        if status == 'done':
          html += '<tr><td align=right bgcolor="#FFFFFF"></td><td bgcolor="#FFFFFF"></td></tr>'
          html += self._show_scores_file(cryptID)        
        
          comment = 'Ensemble of structures.<br>Red denotes the query structure.'
          html += self._showApplet4MultipleFiles( comment, self._getPDBfiles(input_filename, cryptID, 'low'))
          html += self._show_molprobity( cryptID )
          
        return html


    
    def _showPointMutation(self, status, cryptID, input_filename, size_of_ensemble, chain, resid, newaa):
        
        html = """
                <tr><td align=right bgcolor="#EEEEFF">Task:           </td><td bgcolor="#EEEEFF">Point Mutation</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Input file:     </td><td bgcolor="#EEEEFF"><a href="../downloads/%s/%s">%s</a></td></tr> 
                <tr><td align=right bgcolor="#EEEEFF">No. Generated structures: </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Parameters:    </td><td bgcolor="#EEEEFF">Chain: %s<br>Residue: %s<br>Mutation: %s</td></tr>
                """ % ( cryptID, input_filename, input_filename, size_of_ensemble, chain, resid, newaa )
                
        if status == 'done':
          html += '<tr><td align=right bgcolor="#FFFFFF"></td><td bgcolor="#FFFFFF"></td></tr>'
          html += self._show_scores_file(cryptID)
          comment = 'Ensemble of structures.<br>Red denotes the query structure. The point mutated residue is shown as sticks representation'
        
          html += self._showApplet4MultipleFiles( comment, self._getPDBfiles(input_filename, cryptID, 'low'), mutation_res=resid, mutation_chain=chain )
          html += self._show_molprobity( cryptID )
          
        return html
    
    def _showMultiplePointMutations(self, status, cryptID, input_filename, size_of_ensemble, chain, resid, newres, radius):
    
        list_chains = chain.split('-')
        list_resids = [ int(x.strip('\'')) for x in resid.split('-') ]
        list_newres = [ x.strip('\'') for x in newres.split('-') ]
        list_radius = [ float(x.strip('\'')) for x in radius.split('-') ]
        
        multiple_mutations_html = ''
        for x in range(len(list_chains)):
            multiple_mutations_html += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % ( x+1, list_chains[x].strip('\''), list_resids[x], list_newres[x], list_radius[x] )
        
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
        if status == 'done':
          html += '<tr><td align=right bgcolor="#FFFFFF"></td><td bgcolor="#FFFFFF"></td></tr>'
          html += self._show_scores_file(cryptID)
          comment = 'Ensemble of structures.<br>Red denotes the query structure. The point mutated residues are shown as sticks representation'
        
          html += self._showApplet4MultipleFiles( comment, self._getPDBfiles(input_filename, cryptID, 'low'), mutation_res=list_resids, mutation_chain=chain )
          html += self._show_molprobity( cryptID )
          
        return html
    
    def _showComplexMutation(self, status, cryptID, input_filename, size_of_ensemble, mutation_file):
    
        html = """
                <tr><td align=right bgcolor="#EEEEFF">Task:           </td><td bgcolor="#EEEEFF">Complex Mutation</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Input file:     </td><td bgcolor="#EEEEFF">%s</td></tr> 
                <tr><td align=right bgcolor="#EEEEFF">No. Generated structures: </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Parameters:    </td><td bgcolor="#EEEEFF"><pre>%s</pre></td></tr>
                """ % ( input_filename, size_of_ensemble, mutation_file )
                
        if status == 'done':
          html += '<tr><td align=right bgcolor="#FFFFFF"></td><td bgcolor="#FFFFFF"></td></tr>'
          html += self._show_scores_file(cryptID)
          comment = 'Ensemble of structures.<br>Red denotes the query structure.'
        
          html += self._showApplet4MultipleFiles( comment, self._getPDBfiles(input_filename, cryptID, 'low'))
          html += self._show_molprobity( cryptID )       
        
        return html
    
    
    def _showEnsemble(self, status, cryptID, input_filename, size_of_ensemble, temperature, seq_per_struct, len_of_seg):
        
        html = """
                <tr><td align=right bgcolor="#EEEEFF">Task:           </td><td bgcolor="#EEEEFF">Ensemble</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Input file:     </td><td bgcolor="#EEEEFF">%s</td></tr> 
                <tr><td align=right bgcolor="#EEEEFF">No. Generated structures: </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Parameters:    </td><td bgcolor="#EEEEFF">Temperature: %s<br>Sequences per Structure: %s<br>Length of Segment: %s</td></tr>
                """ % ( input_filename, size_of_ensemble, temperature, seq_per_struct, len_of_seg )
        
        if status == 'done':
          html += '<tr><td align=right bgcolor="#FFFFFF"></td><td bgcolor="#FFFFFF"></td></tr>'

          html += """
                <tr><td align="right" bgcolor="#FFFCD8">Average C&alpha; distances</td>                 
                    <td bgcolor="#FFFCD8"><a href="../downloads/%s/ca_dist_difference_1D_plot.png">
                                          <img src="../downloads/%s/ca_dist_difference_1D_plot.png" alt="image missing." width="400"></a></td></tr>
              
                <tr><td align="right" bgcolor="#FFFCD8">Pairwise C&alpha; distances [ <a href="../downloads/%s/ca_dist_difference_matrix.dat">matrix file</a> ]</td>                
                    <td bgcolor="#FFFCD8"><a href="../downloads/%s/ca_dist_difference_2D_plot.png">
                                          <img src="../downloads/%s/ca_dist_difference_2D_plot.png" alt="image missing." width="400"></a></td></tr>
              
                <tr><td align="right" bgcolor="#FFFCD8">Frequency of amino acids for core residues<br><br>
                                                        Sequences [ <a href="../downloads/%s/designs_core.fasta">fasta formated file</a> ]<br>
                                                        Sequence population matrix [ <a href="../downloads/%s/seq_pop_core.txt">matrix file</a> ]</td> 
                    <td bgcolor="#FFFCD8"><a href="../downloads/%s/logo_core.png"><img src="../downloads/%s/logo_core.png" alt="image missing." width="400"></a><br>
                                          <small>Crooks GE, Hon G, Chandonia JM, Brenner SE, 
                                          <a href="Crooks-2004-GR-WebLogo.pdf"><small>WebLogo: A sequence <br>logo generator</small></a>, 
                                          <em>Genome Research</em>, 14:1188-1190, (2004)</small> [<a href="http://weblogo.berkeley.edu/"><small>website</small></a>]</td></tr>
              
                <tr><td align="right" bgcolor="#FFFCD8">Frequency of amino acids for all residues<br><br>
                                                        Sequences [ <a href="../downloads/%s/designs.fasta">fasta formated file</a> ]<br>
                                                        Sequence population matrix [ <a href="../downloads/%s/seq_pop.txt">matrix file</a> ]</td>
                    <td bgcolor="#FFFCD8"><a href="../downloads/%s/logo.png"><img src="../downloads/%s/logo.png" alt="image missing." width="400"></a><br>
                                          <small>Crooks GE, Hon G, Chandonia JM, Brenner SE, <a href="Crooks-2004-GR-WebLogo.pdf">
                                          <small>WebLogo: A sequence <br>logo generator</small></a>, <em>Genome Research</em>, 14:1188-1190, (2004)</small> 
                                          [<a href="http://weblogo.berkeley.edu/"><small>website</small></a>]
                    </td></tr>
              
                <tr><td align="right" bgcolor="#FFFCD8">RMSD for individual residues</td>               
                    <td bgcolor="#FFFCD8"><a href="../downloads/%s/rmsd_plot.png"><img src="../downloads/%s/rmsd_plot.png" alt="image missing." width="400"></a></td></tr>
              
                """ % ( cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID )
        
          html += '<tr><td align=right bgcolor="#FFFFFF"></td><td bgcolor="#FFFFFF"></td></tr>'
        
          comment1 = """Mean C&alpha; difference distance values of the ensemble mapped onto X-ray structure.<br>
           [ <a href="../downloads/%s/ca_dist_difference_bfactors.pdb">PDB file</a> ]""" % cryptID
        
          html += self._showApplet4EnsembleFile( comment1, '../downloads/%s/ca_dist_difference_bfactors.pdb' % cryptID, style='cartoon' )

          comment2 = """Structures of the C&alpha; backbone traces of the backrub ensemble.<br>
          [ <a href="../downloads/%s/ensemble.pdb">PDB file</a> ]""" % cryptID
        
          html += self._showApplet4EnsembleFile( comment2, '../downloads/%s/ensemble.pdb' % cryptID, style='backbone' )

        return html
    
    def _showSequenceTolerance(self, status, cryptID, input_filename, size_of_ensemble, seqtol_chain1, seqtol_chain2, seqtol_list_1, seqtol_list_2, seqtol_radius, w1, w2, w3 ):
        
        html = """
              <tr><td align=right bgcolor="#EEEEFF">Task:           </td><td bgcolor="#EEEEFF">Ensemble</td></tr>
              <tr><td align=right bgcolor="#EEEEFF">Input file:     </td><td bgcolor="#EEEEFF">%s</td></tr> 
              <tr><td align=right bgcolor="#EEEEFF">No. Generated structures: </td><td bgcolor="#EEEEFF">%s</td></tr>
              <tr><td align=right bgcolor="#EEEEFF">Parameters:    </td>
                  <td bgcolor="#EEEEFF">
                      Partner 1: Chain %s<br>
                      Partner 2: Chain %s<br>
                      Designed residues of Partner 1: %s<br>
                      Designed residues of Partner 2: %s<br>
                      Radius of interface: %s [&#197;]<br>
                      Weights (Partner1:Partner2:Interface): (%s:%s:%s)
                  </td></tr>
              """ % ( input_filename, size_of_ensemble, seqtol_chain1, seqtol_chain2, join(seqtol_list_1,' '), join(seqtol_list_2,' '), seqtol_radius, w1, w2, w3 )
        
        input_id = input_filename[:-4] # filename without suffix
        if status == 'done':
            html += '<tr><td align=right bgcolor="#FFFFFF"></td><td bgcolor="#FFFFFF"></td></tr>'
            
            list_pdb_files = ['../downloads/%s/%s_0.pdb' % (cryptID, input_id) ]
            list_pdb_files.extend( [ '../downloads/%s/%s_0_%04.i_low_ms_0000.pdb' % (cryptID, input_id, i) for i in range(1,size_of_ensemble+1) ] )
            
            comment1 = """Backbone representation the best scoring structures.<br>Query structure is shown in red. The designed residues are shown in balls-and-stick representation."""
            
            mutated_chains = [seqtol_chain1 for res in seqtol_list_1] + [seqtol_chain2 for res in seqtol_list_2]
            
            html += self._showApplet4MultipleFiles(comment1, list_pdb_files, mutation_res=[seqtol_list_1,seqtol_list_2], mutation_chain=mutated_chains)
                        
            html += '''<tr><td align="left" bgcolor="#FFFCD8">Motif of the mutated residues.<br>Download corresponding <a href="../downloads/%s/specificity_sequences.fasta">FASTA file</a>.</td>
                           <td bgcolor="#FFFCD8"><a href="../downloads/%s/specificity_motif.png">
                                                 <img src="../downloads/%s/specificity_motif.png" alt="image missing." width="400"></a></td></tr> 
                       <tr><td align="left" bgcolor="#FFFCD8">Individual boxplots of the frequencey of amino acids at the mutated site.<br>
                              Download <a href="../downloads/%s/specificity_pwm.txt">weight matrix</a> or file with all plots as 
                              <a href="../downloads/%s/specificity_boxplot.png">PNG</a>, <a href="../downloads/%s/specificity_boxplot.pdf">PDF</a>.<br>
                              To rerun the analysis we provide the <a href="../downloads/specificity.R">R-script</a> that was used to analyze this data. 
                              A <a href="../wiki/SequencePlasticityPrediction" target="_blank">tutorial</a> on how to use the R-script can be found on 
                              the <a href="../wiki/" target="_blank">wiki</a>.
                              </td>
                           <td bgcolor="#FFFCD8">
                    ''' % ( cryptID, cryptID, cryptID, cryptID, cryptID, cryptID )
            
            for resid in seqtol_list_1:
              html += '''<a href="../downloads/%s/specificity_boxplot_%s%s.png"><img src="../downloads/%s/specificity_boxplot_%s%s.png" alt="image missing." width="400"></a><br>
                    ''' % ( cryptID, seqtol_chain1, resid, cryptID, seqtol_chain1, resid )
            for resid in seqtol_list_2:
              html += '''<a href="../downloads/%s/specificity_boxplot_%s%s.png"><img src="../downloads/%s/specificity_boxplot_%s%s.png" alt="image missing." width="400"></a><br>
                    ''' % ( cryptID, seqtol_chain2, resid, cryptID, seqtol_chain2, resid )
            
            html += self._show_molprobity( cryptID )
            
            html +="</td></tr>"
        return html      
    
    
    def _showDownloadLinks(self, status, extended, cryptID, jobnumber):
    
        html = ''

        if status == "done":
            html += '<tr><td align=right bgcolor="#B7FFE0"><b>Results</b>:</td><td bgcolor="#B7FFE0">'
            
            if os.path.exists( '%s%s/' % (self.download_dir, cryptID) ):
                html += '''<A href="../downloads/%s/"><b>View</b></A> individual files.<br>
                         <A href="../downloads/%s/data_%s.zip"><b>Download</b></A> all results (zip).''' % ( cryptID, cryptID, jobnumber )
                # if extended:
                #     html += ', <A href="../downloads/%s/input.resfile">view Resfile</A>, <A href="../downloads/%s/stdout_%s.dat">view raw output</A>' % ( cryptID, cryptID, jobnumber )
            else:
                html += 'no data'
        html += '</td>\n</tr><tr><td align=right bgcolor="#FFFFFF"></td><td bgcolor="#FFFFFF"></td></tr>'
        
        return html
    
    def _getPDBfiles(self, input_filename, cryptID, key):       
        
        dir_results = '%s%s/' % (self.download_dir, cryptID)
        
        if os.path.exists( dir_results ):
        
            list_files = os.listdir( dir_results )
            list_pdb_files = ['../downloads/%s/' % cryptID + input_filename]
            
            for filename in list_files:
                if filename.find(key) != -1:
                    list_pdb_files.append('../downloads/%s/' % cryptID + filename)
            list_pdb_files.sort()
            
            return list_pdb_files
            
        else:
            return None
    
    def jobinfo(self, parameter):
        """this function decides what _showFunction to pick"""
        
        # SELECT ID, Status, Email, Date, StartDate, EndDate, Notes, Errors, Mini, PDBComplexFile, EnsembleSize, Host, KeepOutput, task, UserID, 
        # PM_chain, PM_resid, PM_newres, PM_radius, ENS_temperature, ENS_num_design_per_struct, ENS_segment_length
        
        # DATE_ADD(EndDate, INTERVAL 8 DAY), TIMEDIFF(DATE_ADD(EndDate, INTERVAL 7 DAY), NOW()), TIMEDIFF(EndDate, StartDate)
        
        status  = ''
        task    = ''
        html    = ''
        rosetta = ''
        
        if   int(parameter['Status']) == 0:
            status = 'in queue'
        elif int(parameter['Status']) == 1:
            status = 'active'
        elif int(parameter['Status']) == 2:
            status = 'done'
        elif int(parameter['Status']) == 5:
            status = 'sample results'
                        
        if parameter['Mini'] == 'mini' or parameter['Mini'] == '1':
            parameter['Mini'] = 'Rosetta v.3 (mini)'
        elif parameter['Mini'] == 'classic' or parameter['Mini'] == '0':
            parameter['Mini'] = 'Rosetta v.2 (classic)'
        else:
            parameter['Mini'] = '???'            
        
        html += """<td align="center"><H1 class="title">Job %s</H1> """ % ( parameter['ID'] )
        if int(parameter['Status']) == 4:
            html += """ <P><font color=red><b>Rosetta Error:</b></font><br>
                            We are sorry but your simulation failed. Please check the uploaded structure file for non consecutive numbering or missing residues. 
                            If the PDB file is correct and Rosetta still fails, please <a href="mailto:lauck@cgl.ucsf.edu">contact us</a>.</P> <br>"""
        
        html += '<table border=0 cellpadding=2 cellspacing=1>\n'
        
        html += self._defaultParameters( parameter['ID'], parameter['Notes'], status, parameter['Host'], parameter['Date'], parameter['StartDate'], 
                                    parameter['EndDate'], parameter['time_computation'], parameter['date_expiration'], parameter['time_expiration'], parameter['Mini'], parameter['Errors'], delete=False, restart=False )
        
        if parameter['Errors'] == '' or parameter['Errors'] == None:
            
            html += self._showDownloadLinks(status, parameter['KeepOutput'], parameter['cryptID'], parameter['ID'])
            
            if parameter['task'] == '0' or parameter['task'] == 'no_mutation':
                task = "Backrub Ensemble"
                html += self._showNoMutation( status, parameter['PDBComplexFile'], parameter['EnsembleSize'], parameter['cryptID'] )            
                
            elif parameter['task'] == '1' or parameter['task'] == 'point_mutation':
                task = "Point Mutation"
                html += self._showPointMutation( status, parameter['cryptID'],  parameter['PDBComplexFile'], parameter['EnsembleSize'], 
                                                 parameter['PM_chain'], parameter['PM_resid'], parameter['PM_newres'])
                
            elif parameter['task'] == '3' or parameter['task'] == 'multiple_mutation':
                task = "Multiple Point Mutations"
                html += self._showMultiplePointMutations( status, parameter['cryptID'], parameter['PDBComplexFile'], parameter['EnsembleSize'], parameter['PM_chain'], 
                                                          parameter['PM_resid'], parameter['PM_newres'], parameter['PM_radius'])
                
            elif parameter['task'] == '2' or parameter['task'] == 'upload_mutation':
                task = "Custom Mutation"
                html += self._showComplexMutation( status, parameter['cryptID'], parameter['PDBComplexFile'], parameter['EnsembleSize'], parameter['Mutations'])
                
            elif parameter['task'] == '4' or parameter['task'] == 'ensemble':
                task = "Backrub Ensemble Design"
                html += self._showEnsemble( status, parameter['cryptID'], parameter['PDBComplexFile'], parameter['EnsembleSize'], parameter['ENS_temperature'], 
                                            parameter['ENS_num_designs_per_struct'], parameter['ENS_segment_length'] )
                                            
            elif parameter['task'] == 'sequence_tolerance':
                task = "Sequence Plasticity Prediciton"
                seqtol_parameter = pickle.loads(parameter['seqtol_parameter'])
                html += self._showSequenceTolerance( status, parameter['cryptID'], parameter['PDBComplexFile'], parameter['EnsembleSize'], 
                                                     seqtol_parameter['seqtol_chain1'], seqtol_parameter['seqtol_chain2'], 
                                                     seqtol_parameter['seqtol_list_1'], seqtol_parameter['seqtol_list_2'],
                                                     seqtol_parameter['seqtol_radius'], 
                                                     seqtol_parameter['seqtol_weight_chain1'], seqtol_parameter['seqtol_weight_chain2'], seqtol_parameter['seqtol_weight_interface'] )
                
        html += '</table><br></td>\n'
        
        return html


    def _showApplet4MultipleFiles(self, comment, list_pdb_files, mutation_res=None, mutation_chain=None):
        """This shows the Jmol applet for an ensemble of structures with their point mutation(s)"""
        
        # jmol command to load files
        if list_pdb_files != None:
            jmol_cmd = 'load %s; color red; ' % list_pdb_files[0]
            for pdb in list_pdb_files[1:]:
                jmol_cmd += 'load APPEND %s; ' % pdb
            
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
                     <tr><td align="justify" bgcolor="#FFFCD8">%s</td>
                         <td bgcolor="#FFFCD8">
                            <script type="text/javascript">
                              jmolInitialize("../../jmol"); 
                              jmolApplet(400, "set appendNew false; %s cpk off; wireframe off; backbone 0.2; %s"); 
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
                      jmolApplet(400, "load %s cpk off; wireframe off; %s");
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

        html = """<td align="center">
                  <H1 class="title">Welcome to RosettaBackrub</A> </H1> 
                    <P>
                      This is the structure prediction web server of the Kortemme Lab. This server utilizes the backrub method for flexible protein backbone modeling implemented in 
                      <a href="/backrub/wiki/Rosetta">Rosetta</a>. 
                      This server allows the user to upload a protein structure and choose an algorithm that is applied to this structure. 
                      For a tutorial on how to submit a job see the <a href="/backrub/wiki/">documentation</a>. 
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
        html += open("doc.html", 'r').read()
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

    test_html = RosettaHTML('albana.ucsf.edu', 'Structure Prediction Backrub', 'rosettahtml.py', 'DFTBA', comment='this is just a test', contact_email='kortemme@cgl.ucsf.edu' , contact_name='Tanja Kortemme')

    #html_content = test_html.index() 
    html_content = test_html.submit()
    #html_content = test_html.register( error='You broke everything', update=True )
    #html_content = test_html.login()  
    #html_content += '</tr><tr>'  
    #html_content += test_html.logout('DFTBA')
    #html_content = test_html.sendPassword()
    
    s.write( test_html.main(html_content) )

    s.close()


