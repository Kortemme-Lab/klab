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

    def setUsername(self, username):
        self.username = username

    def main(self, CONTENT='This server is made of awesome.', site='' ):
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
                <script src="/javascripts/scriptaculous.js?load=effects" type="text/javascript"></script>
                <script src="/javascripts/niftycube.js" type="text/javascript"></script>
                <script src="/jmol/Jmol.js" type="text/javascript"></script>
                <script src="/backrub/jscripts.js" type="text/javascript"></script>
            </head>

            <body bgcolor="#ffffff" onload=startup()>
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
                                <font color="black" style="text-decoration:blink;">%s</font></td></tr>
                            </table>
                     </td></tr><tr>''' % self.warning
            #html += '<tr> <td align="center"> </td></tr>'

        if self.comment != '':
            html += '''<td align="center" style="padding:10px;">
                                <table width="500"><tr><td style="padding-left:20px; padding-right:20px; padding-top:10px; padding-bottom:10px; padding-left:10px; border-color:orange; border-style:dashed; border-width:2px;">
                                    <font color="red">%s</font></td></tr>
                                </table>
                      </td>''' % self.comment
        return html

    def _showMenu(self):
        html = """
                <tr><td align=center>
                    [&nbsp;<A href="%s?query=index" >Home</A>&nbsp;] &nbsp;&nbsp;&nbsp;
                    [&nbsp;<A href="%s?query=doc">Documentation</A>&nbsp;]
                </td></tr>
                <tr><td align=center>""" % (self.script_filename,self.script_filename)
        
        if self.username != '':
            html += """
                    [&nbsp;<A href="%s?query=submit">Submit</A>&nbsp;] &nbsp;&nbsp;&nbsp;
                    [&nbsp;<A href="%s?query=queue">Queue</A>&nbsp;] &nbsp;&nbsp;&nbsp;
                    [&nbsp;<A href="%s?query=update">My Account</A>&nbsp;] &nbsp;&nbsp;&nbsp;""" % (self.script_filename,self.script_filename,self.script_filename)
        else:
            html += """
                    [&nbsp;<A href="%s?query=login">Login</A>&nbsp;] &nbsp;&nbsp;&nbsp;
                    [&nbsp;<A href="%s?query=register">Register</A>&nbsp;]""" % (self.script_filename,self.script_filename)
        html += "\n</td></tr>"

        return html

    def _showLegalInfo(self):
        html = """<td style="border:1px solid black; padding:10px" bgcolor="#FFFFE0">
                    <p style="text-align:left; font-size: 10pt" >
                      For questions, please contact <A href="mailto:%s" style="font-size: 10pt">%s</A>
                    </p>
                  </td>""" % ( self.contact_email, self.contact_name )
        return html

    def _showFooter(self):
        html = """<td align=center style="border-top:1px solid gray; ">
                 <table width="720" style="border-width:0pt">
                    <tr>
                    <td align="center"><img src="../images/ucsf_only_tiny.png" width="65%%" height="65%%" alt="UCSF" border=0></td>
                    <td align="left">
                    "Structure prediction using backrub" is available for NON-COMMERCIAL USE ONLY at this time<br>
                    <font color=#666688><b>[</b></font>
                    <A href="%s?query=terms_of_service" class="nav">Terms of Service</A>
                    <font color=#666688><b>]</b></font><br>
                    <font style="font-size: 9pt">Copyright &copy; 2009 University of California San Francisco, <A href="mailto:kortemme@cgl.ucsf.edu" style="font-size: 9pt">Tanja Kortemme</a>, <A href="mailto:lauck@cgl.ucsf.edu" style="font-size: 9pt">Florian Lauck</A></font>
                    </td>
                    </tr>
                 </table></td>""" % ( self.script_filename )
        return html


##############################################
# The following functions are accessed from  #
# outside and produce the HTML content by    #
# main                                       #
##############################################

###############################################################################################
# index()                                                                                     #
###############################################################################################

    def index(self):
        html = """<td align="center">
               <H1 class="title">Welcome to the Kortemme Lab Server</A> </H1> 
               <P>
               This is the structure prediction web server of the Kortemme Lab. This server utilizes the backrub method implemented in 
               <a href="%s?query=doc#Rosetta">Rosetta</a>
               for protein design and applies it to a structure uploaded by the user. For an explanation of how the server works see the
               <a href="%s?query=doc#instructions">instructions</a>. 
               </P>
               
               <P>
               You can choose a link from the menu above to proceed. Please <A href="%s?query=login">log in</A> or 
               <A href="%s?query=register">create an account</A> first. 
               </P>
               <br>         
               <br>
              """ % ( self.script_filename, self.script_filename, self.script_filename, self.script_filename ) 
        return html

###############################################################################################
# submit()                                                                                    #
###############################################################################################

    def submit(self, jobname='' ):
    	# this function uses javascript functions from jscript.js
		# if you change the application tabler here, please make sure to change jscript.js accordingly
		# calling the function with parameters will load those into the form. #not implemented yet

        html = '''<td align="center">
    <H1 class="title">Submit a new job</H1>
    <br>
    Please enter the required information and upload a structure. For help move your mouse to the parameter.
    <br><br>
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
              [ <A href="/alascan/" target="_blank">Interface Alanine Scanning</A> ]<br><center><small>opens in a new window</small></center>
            </li>
            <li id="ab2">
              <A href="javascript:void(0)" onclick="showMenu('menu_1'); ">Point Mutation</A>            
              <p id="menu_1" style="display:none; text-align:right; margin:0px;">
                  <table style="border:0px; padding:0px; margin:0px;">
                  <tr><td width="25" style="text-align:right;">-</td><td><a href="javascript:void(0)" onclick="changeApplication('task_1_one_mutation'); ">One mutation</a></td></tr>
                  <tr><td width="25" style="text-align:right;">-</td><td><a href="javascript:void(0)" onclick="changeApplication('task_1_multiple_mutation'); ">Multiple mutations</a></td></tr>
                  <tr><td width="25" style="text-align:right;">-</td><td>Upload List</td></tr>
                  </table>
              </p>
            </li>
            <li id="ab3">
              <A href="javascript:void(0)" onclick="showMenu('menu_2'); ">Backrub Ensemble Design</A>
              <p id="menu_2" style="display:none; text-align:right; margin:0px;">
                  <table style="border:0px; padding:0px; margin:0px;">
                  <tr><td width="25" style="text-align:right;">-</td><td><a href="javascript:void(0)" onclick="changeApplication('task_2_no_mutation'); " >Model Flexibility</a></td></tr>
                  <tr><td width="25" style="text-align:right;">-</td><td><a href="javascript:void(0)" onclick="changeApplication('task_2_ensemble'); ">Backrub ensemble</a></td></tr>
                  </table>
              </p>
            </li>
            <!--li id="ab4">
              <A href="javascript:void(0)" onclick="showMenu('menu_3'); ">Flexible Backbone Design</A>
              <p id="menu_3" style="display:none; text-align:right;">
                  Oops
              </p>
            </li-->
          </ul>
          </td>
<!-- end left column -->
<!-- right column -->
          <td id="columnRight" align="center" style="vertical-align:top; padding:0px; margin:0px; height:240px; text-align:center;">
          <div id="box">
          <!-- pictures for the different applications -->
            <p id="pic_1" style="display:none; text-align:center;">
              <img src="../images/logo1.png" width="85%%" height="85%%" alt="Rosetta" border=0>
            </p>

            <p id="pic_2" style="display:none; text-align:center;">
              <!-- img src="../images/logo2.png" width="85%%" alt="Rosetta" border=0 -->
            </p>

            <p id="task_init" style="text-align:justify;"> 
              Click left to choose one of the applications. Each application will give you a short explanation and a set of parameters that can be adjusted.
            </p>
          <!-- end pictures -->
          <!-- description -->
            <div id="text_1" style="display:none; text-align:justify;"> 
                This function utilizes the backrub protocol implemented in ROSETTA.<br>
                There are three options:
                <ul style=" text-align:left;">
                    <li>One Mutation: A single residue will be substituted. (see reference below)</li>
                    <li>Multiple Mutations: Up to 30 residues can be mutated. (not thoroughly tested)</li>
                    <li>Upload List: Upload a list with single residue mutations</li>
                </ul>
            </div>

            <div id="text_2" style="display:none; text-align:justify;"> 
                This function utilizes the backrub protocol implemented in ROSETTA.<br>
                There are two options:
                <ul style="text-align:left;">
                    <li>Model Flexibility: The backrub protocol is applied to the whole structure without changing any residues.</li>
                    <li>Backrub Ensemble: This method creates an ensemble of structures that model the flexibility in solution. (see reference below)</li>
                </ul>
            </div>
          <!-- end description -->
          <!-- parameter form -->
            <TABLE id="common_form" align="center" style="display:none;">
              <TR>
                <TD align=right onmouseover="popUp('tt_UserName');" onmouseout="popUp('tt_UserName');">User Name </TD>
                <TD align=left style="padding-left:5pt; padding-top:5pt;" ><INPUT TYPE="text" maxlength=30 SIZE=31 NAME="UserName" VALUE="%s" disabled>
                </TD>
              </TR>
              <TR></td></TR>
              <TR>
                <TD align=right onmouseover="popUp('tt_JobName');" onmouseout="popUp('tt_JobName');">Job Name </TD>
                <TD align=left style="padding-left:5pt; padding-top:5pt;"><INPUT TYPE="text" maxlength=40 SIZE=31 NAME="JobName" VALUE="%s"> *</TD>
              </TR>
              <TR><TD align=left><br></TD></TR>
              <TR>
                <TD align=right onmouseover="popUp('tt_Structure');" onmouseout="popUp('tt_Structure');"> Structure </TD>
                <TD align=left style="padding-left:5pt; padding-top:5pt;" > <INPUT TYPE="file" NAME="PDBComplex" size="20"> *</TD>
              </TR>
              <TR><TD colspan=2><br></TD></TR>
              <TR>
                <TD align="center" colspan=2 style="border-bottom:1pt dashed black">General Settings</TD>
              </TR>
              <TR>
                <TD align=right onmouseover="popUp('tt_RVersion');" onmouseout="popUp('tt_RVersion');">Rosetta Version </TD>
                <TD id="rosetta1" style="padding-left:5pt; padding-top:5pt;">
                    <input type="radio" checked name="Mini" value="classic"> Rosetta 2.3 (classic)<br>
                    <input type="radio" name="Mini" value="mini"> Rosetta 3.0 (mini)
                </TD>
              </TR>
              <TR>
                <TD align=right onmouseover="popUp('tt_NStruct');" onmouseout="popUp('tt_NStruct');">Number of structures </TD>
                <TD style="padding-left:5pt; padding-top:5pt;"> <input type="text" name="nos" maxlength=3 SIZE=5 VALUE=""> (max 100) </TD>
              </TR>
              <TR>
                <TD align=right onmouseover="popUp('tt_ROutput');" onmouseout="popUp('tt_ROutput');">ROSETTA output </TD>
                <TD id="rosetta2" style="padding-left:5pt; padding-top:5pt;"> <input type="checkbox" name="keep_output" VALUE="1"> keep files</TD>
              </TR>
              <TR><TD align=left><br></TD></TR>
              <TR>
                <TD align="center" colspan=2 style="border-bottom:1pt dashed black">Application Specific Settings</TD>
              </TR>
            </TABLE>

            <p id="task_1_one_mutation" style="display:none; text-align:justify;">
            Backrub is applied to residues that have at least one atom within a radius of 6.0 &#197; near the mutation. [ <a href="http://www.sciencedirect.com/science/article/B6WK7-4SHVT2K-7/2/7bb4ba6dcb946d7e39662232433bbb09">Smith and Kortemme, 2008</a> ]<br>
                <table align=center>
                <tr>
                    <td align="right" onmouseover="popUp('tt_ChainId');" onmouseout="popUp('tt_ChainId');">Chain ID </td><td><input type="text" name="PM_chain"  maxlength=1 SIZE=5 VALUE=""></td>
                </tr>
                <tr>
                    <td align="right" onmouseover="popUp('tt_ResId');" onmouseout="popUp('tt_ResId');">Residue ID </td><td><input type="text" name="PM_resid"  maxlength=4 SIZE=5 VALUE=""></td>
                </tr>
                <tr>
                    <td align="right" onmouseover="popUp('tt_NewAA');" onmouseout="popUp('tt_NewAA');">New Amino Acid </td><td><input type="text" name="PM_newres" maxlength=1 SIZE=5 VALUE=""></td>
                </tr>
                <tr>
                    <td><INPUT TYPE="hidden" NAME="PM_radius" VALUE="6.0"></td>
                </tr>
                </table>
                <br>
            </p>

            <p id="task_1_multiple_mutation" style="display:none; text-align:justify;">
            Choose up to 30 residues for mutations. Backrub is applied to neighboring residues in a given radius. <br>
                <table bgcolor="#EEEEEE" align="center">
                <tr bgcolor="#828282" style="color:white;">
                    <td align="center">#</td>
                    <td align="center" onmouseover="popUp('tt_ChainId');" onmouseout="popUp('tt_ChainId');">Chain ID</td>
                    <td align="center" onmouseover="popUp('tt_ResId');"   onmouseout="popUp('tt_ResId');">Res ID</td>
                    <td align="center" onmouseover="popUp('tt_NewAA');"   onmouseout="popUp('tt_NewAA');">AA</td>
                    <td align="center" onmouseover="popUp('tt_Radius');"  onmouseout="popUp('tt_Radius');">Radius [&#197;]</td>
                </tr>
                <tr><SCRIPT>writeRow(0)</SCRIPT></tr>
                <!-- up to 31 point mutations are possible -->
                <tr id="row_PM1"  style="display:none"><SCRIPT>writeRow(1)</SCRIPT></tr>   <tr id="row_PM2"  style="display:none"><SCRIPT>writeRow(2)</SCRIPT></tr>
                <tr id="row_PM3"  style="display:none"><SCRIPT>writeRow(3)</SCRIPT></tr>   <tr id="row_PM4"  style="display:none"><SCRIPT>writeRow(4)</SCRIPT></tr>
                <tr id="row_PM5"  style="display:none"><SCRIPT>writeRow(5)</SCRIPT></tr>   <tr id="row_PM6"  style="display:none"><SCRIPT>writeRow(6)</SCRIPT></tr>
                <tr id="row_PM7"  style="display:none"><SCRIPT>writeRow(7)</SCRIPT></tr>   <tr id="row_PM8"  style="display:none"><SCRIPT>writeRow(8)</SCRIPT></tr>
                <tr id="row_PM9"  style="display:none"><SCRIPT>writeRow(9)</SCRIPT></tr>   <tr id="row_PM10" style="display:none"><SCRIPT>writeRow(10)</SCRIPT></tr>
                <tr id="row_PM11" style="display:none"><SCRIPT>writeRow(11)</SCRIPT></tr>  <tr id="row_PM12" style="display:none"><SCRIPT>writeRow(12)</SCRIPT></tr>
                <tr id="row_PM13" style="display:none"><SCRIPT>writeRow(13)</SCRIPT></tr>  <tr id="row_PM14" style="display:none"><SCRIPT>writeRow(14)</SCRIPT></tr>
                <tr id="row_PM15" style="display:none"><SCRIPT>writeRow(15)</SCRIPT></tr>  <tr id="row_PM16" style="display:none"><SCRIPT>writeRow(16)</SCRIPT></tr>
                <tr id="row_PM17" style="display:none"><SCRIPT>writeRow(17)</SCRIPT></tr>  <tr id="row_PM18" style="display:none"><SCRIPT>writeRow(18)</SCRIPT></tr>
                <tr id="row_PM19" style="display:none"><SCRIPT>writeRow(19)</SCRIPT></tr>  <tr id="row_PM20" style="display:none"><SCRIPT>writeRow(20)</SCRIPT></tr>
                <tr id="row_PM21" style="display:none"><SCRIPT>writeRow(21)</SCRIPT></tr>  <tr id="row_PM22" style="display:none"><SCRIPT>writeRow(22)</SCRIPT></tr>
                <tr id="row_PM23" style="display:none"><SCRIPT>writeRow(23)</SCRIPT></tr>  <tr id="row_PM24" style="display:none"><SCRIPT>writeRow(24)</SCRIPT></tr>
                <tr id="row_PM25" style="display:none"><SCRIPT>writeRow(25)</SCRIPT></tr>  <tr id="row_PM26" style="display:none"><SCRIPT>writeRow(26)</SCRIPT></tr>
                <tr id="row_PM27" style="display:none"><SCRIPT>writeRow(27)</SCRIPT></tr>  <tr id="row_PM28" style="display:none"><SCRIPT>writeRow(28)</SCRIPT></tr>
                <tr id="row_PM29" style="display:none"><SCRIPT>writeRow(29)</SCRIPT></tr>  <tr id="row_PM30" style="display:none"><SCRIPT>writeRow(30)</SCRIPT></tr>
                </table>
                <a href="javascript:void(0)" onclick="addOneMore();">Click here to add a mutation</a>
            </p>

            <p id="task_upload_mutation" style="display:none; text-align:justify;"><b>Custom mutation.</b><br><br>
                This allows for a more flexible definition of mutations. Detailed information about the format of the file can be found in the <A style="color:#365a79; "href="%s?query=doc#mutations">documentation</A>. <br>
                <font style="text-align:left;">Upload file <INPUT TYPE="file" NAME="Mutations" size="13"></font>
            </p>

            <p id="task_2_no_mutation" style="display:none; text-align:center;"><b>Apply backrub to all residues.</b><br><br>no options
            </p>

            <p id="task_2_ensemble" style="display:none; text-align:center;">
                <b>Create a backrub ensemble.</b><br> [ <a href="http://www.pubmedcentral.nih.gov/articlerender.fcgi?artid=2682763">Friedland et al. 2009</a> ]<br><br>
                <table align="center">
                <tr>
                    <td onmouseover="popUp('tt_Temp');" onmouseout="popUp('tt_Temp');">Temperature [kT]</td><td><input type="text" name="ENS_temperature" maxlength=3 SIZE=5 VALUE="0.3"></td>
                </tr>
                <tr>
                    <td onmouseover="popUp('tt_NSeq');" onmouseout="popUp('tt_NSeq');">No. of sequences</td><td><input type="text" name="ENS_num_designs_per_struct" maxlength=4 SIZE=5 VALUE="20"></td>
                </tr>
                <tr>
                    <td onmouseover="popUp('tt_SegLength');" onmouseout="popUp('tt_SegLength');">Max. segment length</td><td><input type="text" name="ENS_segment_length" maxlength=1 SIZE=5 VALUE="12"></td>
                </tr>
                </table>
            </p>

            <p id="submit_button" style="display:none; text-align:center;">
            * required fields &nbsp;&nbsp;&nbsp;&nbsp;<INPUT TYPE="Submit" VALUE="Submit">
            </p>
            <!-- end parameter form -->
            
            <!-- references -->
            <p id="ref_1" style="display:none; text-align:justify; border:1px solid #000000; padding:5px; font-size: 10pt; background-color:#FFFFFF; ">
                If you are using the data, please cite:<br><br>
                Colin A. Smith, Tanja Kortemme, <i>Backrub-Like Backbone Simulation Recapitulates Natural Protein Conformational Variability and Improves Mutant Side-Chain Prediction</i>,<br>
                <a href="http://dx.doi.org/10.1016/j.jmb.2008.05.023" style="font-size: 10pt"> Journal of Molecular Biology Volume 380, 742-756</a>
                </p>
            </p>

            <p id="ref_2" style="display:none; text-align:justify;border:1px solid #000000; padding:5px; font-size: 10pt; background-color:#FFFFFF; ">
                If you are using the data, please cite:<br><br>
                Friedland GD, Lakomek NA, Griesinger C, Meiler J, Kortemme T., <i>A correspondence between solution-state dynamics of an individual protein and the sequence and conformational diversity of its family.</i>,<br>
                <a href="http://dx.doi.org/10.1371/journal.pcbi.1000393" style="font-size: 10pt"> PLoS Comput Biol. 2009 May</a>
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
        </td>''' % (self.username, jobname, self.script_filename )

        html += self._helpButtons()

        return html

    def submited(self, jobname='', cryptID=''):
        html = """<td align="center"><H1 class="title">New Job successfully submitted</H1> 
                 <A href="%s?query=jobinfo&jobnumber=%s">Go to job info</a>. 
                 <A href="%s?query=submit">Submit another job</A> or <A href="%s?query=queue">check the queue</A>.<br><br></td>\n"""  % ( self.script_filename, cryptID, self.script_filename, self.script_filename )
                     #% (UserName, JobName, pdbfile.filename) )
        return html



    def _helpButtons(self):
        html = '<!-- these divs are used for the help tooltips -->\n'
        html += '<div id="tt_UserName" class="tooltip"><b>Your username</b></div>\n'
        html += '<div id="tt_JobName" class="tooltip"><b>Name for your job</b><br>Enter a name that helps you identifying your job later.</div>\n'
        html += """<div id="tt_Structure" class="tooltip"><b>Structure File</b><br>Enter the path to a protein structure file in PDB format. <br></div>\n"""
        #          <br> <font color=red><b>Important note:</b></font><br> This server renumbers the residues of the individual chains in a consecutive manner if the numbering in the PDB file does not start at 1 <b>AND</b> Rosetta++ is used.
        #         This is also consistently applied to the mutations. </div>\n"""
        #html += '<div id="tt_GSettings" class="tooltip"><b>General Settings.</b><br>Not-application specific settings.</div>\n'
        html += '<div id="tt_RVersion" class="tooltip"><b>Rosetta Version</b><br>Choose the version of Rosetta, either the \'classic\' Rosetta++ or the new MiniRosetta. Does not apply to all applications.</div>\n'
        html += '<div id="tt_NStruct" class="tooltip"><b>Number of Structures</b><br>Number of generated structures or size of ensemble.</div>\n'
        html += '<div id="tt_ROutput" class="tooltip"><b>Rosetta output</b><br>If checked, the raw output of the Rosetta run is stored. Does not apply to all applications.</div>\n'
        html += '<div id="tt_SelApp" class="tooltip"><b>Select Application</b><br>Click to choose one of the applications. Each application will give you a short explanation and a set of parameters that can be adjusted.</div>\n'
        html += '<div id="tt_ChainId" class="tooltip"><b>Chain ID</b><br>The chain in which the residue is located.</div>\n'
        html += '<div id="tt_ResId" class="tooltip"><b>Residue ID</b><br>The position (residue ID according to the PDB file) that is going to be mutated.</div>\n'
        html += '<div id="tt_NewAA" class="tooltip"><b>New Amino Acid</b><br>The Amino Acid to which the position is going to be mutated.</div>\n'
        html += '<div id="tt_Radius" class="tooltip"><b>Radius</b><br>This radius determines the area around the mutation that is subject to backrub. For detailed information see the referenced paper. </div>\n'
        html += '<div id="tt_Temp" class="tooltip"><b>Temperature</b><br>at which backrub is carried out.</div>\n'
        html += '<div id="tt_NSeq" class="tooltip"><b>Number of Sequences</b><br>The number of designed sequences for each ensemble structure.</div>\n'
        html += '<div id="tt_SegLength" class="tooltip"><b>Maximal segment length for backrub</b><br>Limit the length of the segment to which the bachrub move is applied to.</div>\n'
        #html += '<div id="tt_ListOfMutations" class="tooltip"><b>List of Mutations</b><br>This allows for </div>\n'
        #html += '<div id="tt_" class="tooltip"><b></b><br></div>\n'
        html += """<div id="tt_error" class="tooltip"><font color=red><b>Rosetta Error:</b></font><br>
                Rosetta (classic and mini) fail for some PDB files that have inconsistent residue numbering or miss residues.
                If an error occures for your structure please check the correctness of the PDB file.
                If the PDB file is correct and Rosetta still fails, please <a href="mailto:lauck@cgl.ucsf.edu">contact us</a>.</div>\n"""
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
                     <col width="30">
                     <col width="70">
                     <col width="100">
                     <col width="100">
                     <col width="200">
                     <col width="100">
                     <col width="25">
                     <col width="75">
                   </colgroup>
                  <tr align=center bgcolor="#828282" style="color:white;"> 
                   <td > ID </td> 
                   <td > Status </td> 
                   <td > User Name </td>
                   <td > Date (PST) </td>
                   <td > Job Name </td>
                   <td > Rosetta </td>
                   <td > Structures </td>
                   <td > Error </td></tr>\n"""
                   
        for line in job_list:
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
                html += '<td>mini</td>'
            elif line[6] == '0' or line[6] == 'classic':
                html += '<td>classic</td>'
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
        score_file = '../downloads/%s/scores.dat' % cryptID
        html = ''
        if os.path.exists( score_file ):
          handle = open(score_file,'r')
          html = '''<tr><td align="right" bgcolor="#FFFCD8">Individual scores for structures in the ensemble</td>              
                      <td bgcolor="#FFFCD8"><pre style="font-size:10pt">%s</pre></td></tr>
              ''' % ( join(handle.readlines(), '') )
          handle.close()

        return html

    def _showNoMutation(self, input_filename, size_of_ensemble, cryptID):

        html = """
                <tr><td align=right bgcolor="#EEEEFF">Task:           </td><td bgcolor="#EEEEFF">No Mutation</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Input file:     </td><td bgcolor="#EEEEFF">%s</td></tr> 
                <tr><td align=right bgcolor="#EEEEFF">No. Generated structures: </td><td bgcolor="#EEEEFF">%s</td></tr>
                """ % ( input_filename, size_of_ensemble )
        html += self._show_scores_file(cryptID)
        return html


    
    def _showPointMutation(self, cryptID, input_filename, size_of_ensemble, chain, resid, newaa):
        
        html = """
                <tr><td align=right bgcolor="#EEEEFF">Task:           </td><td bgcolor="#EEEEFF">Point Mutation</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Input file:     </td><td bgcolor="#EEEEFF">%s</td></tr> 
                <tr><td align=right bgcolor="#EEEEFF">No. Generated structures: </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Parameters:    </td><td bgcolor="#EEEEFF">Chain: %s<br>Residue: %s<br>Mutation: %s</td></tr>
                """ % ( input_filename, size_of_ensemble, chain, resid, newaa )
        
        html += '<tr><td align=right bgcolor="#FFFFFF"></td><td bgcolor="#FFFFFF"></td></tr>'
        html += self._show_scores_file(cryptID)
        comment = 'Ensemble of structures with lowest energies.<br>Red denotes the query structure. The point mutated residue is shown as sticks representation'
        
        html += self._showApplet4MultipleFiles( comment, self._getPDBfiles(input_filename, cryptID, 'low'), mutation=resid )
        
        return html
    
    def _showMultiplePointMutations(self, cryptID, input_filename, size_of_ensemble, chain, resid, newres, radius):
    
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
        
        html += '<tr><td align=right bgcolor="#FFFFFF"></td><td bgcolor="#FFFFFF"></td></tr>'
        html += self._show_scores_file(cryptID)
        comment = 'Ensemble of structures with lowest energies.<br>Red denotes the query structure. The point mutated residues are shown as sticks representation'
        
        html += self._showApplet4MultipleFiles( comment, self._getPDBfiles(input_filename, cryptID, 'low'), mutation=list_resids )
        
        return html
    
    def _showComplexMutation(self, cryptID, input_filename, size_of_ensemble, mutation_file):
    
        html = """
                <tr><td align=right bgcolor="#EEEEFF">Task:           </td><td bgcolor="#EEEEFF">Complex Mutation</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Input file:     </td><td bgcolor="#EEEEFF">%s</td></tr> 
                <tr><td align=right bgcolor="#EEEEFF">No. Generated structures: </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Parameters:    </td><td bgcolor="#EEEEFF"><pre>%s</pre></td></tr>
                """ % ( input_filename, size_of_ensemble, mutation_file )
        
        html += '<tr><td align=right bgcolor="#FFFFFF"></td><td bgcolor="#FFFFFF"></td></tr>'
        html += self._show_scores_file(cryptID)
        comment = 'Ensemble of structures with lowest energies.<br>Red denotes the query structure.'
        
        html += self._showApplet4MultipleFiles( comment, self._getPDBfiles(input_filename, cryptID, 'low'))        
        
        return html
    
    def _showEnsemble(self, cryptID, input_filename, size_of_ensemble, temperature, seq_per_struct, len_of_seg):
        
        html = """
                <tr><td align=right bgcolor="#EEEEFF">Task:           </td><td bgcolor="#EEEEFF">Ensemble</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Input file:     </td><td bgcolor="#EEEEFF">%s</td></tr> 
                <tr><td align=right bgcolor="#EEEEFF">No. Generated structures: </td><td bgcolor="#EEEEFF">%s</td></tr>
                <tr><td align=right bgcolor="#EEEEFF">Parameters:    </td><td bgcolor="#EEEEFF">Temperature: %s<br>Sequences per Structure: %s<br>Length of Segment: %s</td></tr>
                """ % ( input_filename, size_of_ensemble, temperature, seq_per_struct, len_of_seg )
        
        html += '<tr><td align=right bgcolor="#FFFFFF"></td><td bgcolor="#FFFFFF"></td></tr>'

        html += """
              <tr><td align="right" bgcolor="#FFFCD8">Average C&alpha; distances</td>                 
                  <td bgcolor="#FFFCD8"><a href="../downloads/%s/ca_dist_difference_1D_plot.png">
                                        <img src="../downloads/%s/ca_dist_difference_1D_plot.png" alt="Sorry, picture missing." width="400"></a></td></tr>
              
              <tr><td align="right" bgcolor="#FFFCD8">Pairwise C&alpha; distances [ <a href="../downloads/%s/ca_dist_difference_matrix.dat">matrix file</a> ]</td>                
                  <td bgcolor="#FFFCD8"><a href="../downloads/%s/ca_dist_difference_2D_plot.png">
                                        <img src="../downloads/%s/ca_dist_difference_2D_plot.png" alt="Sorry, picture missing." width="400"></a></td></tr>
              
              <tr><td align="right" bgcolor="#FFFCD8">Frequency of amino acids for core residues<br><br>
                                                      Sequences [ <a href="../downloads/%s/designs_core.fasta">fasta formated file</a> ]<br>
                                                      Sequence population matrix [ <a href="../downloads/%s/seq_pop_core.txt">matrix file</a> ]</td> 
                  <td bgcolor="#FFFCD8"><a href="../downloads/%s/logo_core.png"><img src="../downloads/%s/logo_core.png" alt="Sorry, picture missing." width="400"></a><br>
                                        <small>Crooks GE, Hon G, Chandonia JM, Brenner SE, 
                                        <a href="Crooks-2004-GR-WebLogo.pdf"><small>WebLogo: A sequence <br>logo generator</small></a>, 
                                        <em>Genome Research</em>, 14:1188-1190, (2004)</small> [<a href="http://weblogo.berkeley.edu/"><small>website</small></a>]</td></tr>
              
              <tr><td align="right" bgcolor="#FFFCD8">Frequency of amino acids for all residues<br><br>
                                                      Sequences [ <a href="../downloads/%s/designs.fasta">fasta formated file</a> ]<br>
                                                      Sequence population matrix [ <a href="../downloads/%s/seq_pop.txt">matrix file</a> ]</td>
                  <td bgcolor="#FFFCD8"><a href="../downloads/%s/logo.png"><img src="../downloads/%s/logo.png" alt="Sorry, picture missing." width="400"></a><br>
                                        <small>Crooks GE, Hon G, Chandonia JM, Brenner SE, <a href="Crooks-2004-GR-WebLogo.pdf">
                                        <small>WebLogo: A sequence <br>logo generator</small></a>, <em>Genome Research</em>, 14:1188-1190, (2004)</small> 
                                        [<a href="http://weblogo.berkeley.edu/"><small>website</small></a>]
                  </td></tr>
              
              <tr><td align="right" bgcolor="#FFFCD8">RMSD for individual residues</td>               
                  <td bgcolor="#FFFCD8"><a href="../downloads/%s/rmsd_plot.png"><img src="../downloads/%s/rmsd_plot.png" alt="Sorry, picture missing." width="400"></a></td></tr>
              
              """ % ( cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID, cryptID )
        
        html += '<tr><td align=right bgcolor="#FFFFFF"></td><td bgcolor="#FFFFFF"></td></tr>'
        
        comment1 = """Mean C&alpha; difference distance values of the ensemble mapped onto X-ray structure.<br>
         [ <a href="../downloads/%s/ca_dist_difference_bfactors.pdb">PDB file</a> ]""" % cryptID
        
        html += self._showApplet4EnsembleFile( comment1, '../downloads/%s/ca_dist_difference_bfactors.pdb' % cryptID, style='cartoon' )

        comment2 = """Structures of the C&alpha; backbone traces of the backrub ensemble.<br>
          [ <a href="../downloads/%s/ensemble.pdb">PDB file</a> ]""" % cryptID
        
        html += self._showApplet4EnsembleFile( comment2, '../downloads/%s/ensemble.pdb' % cryptID, style='backbone' )


        return html
    
    def _showDownloadLinks(self, status, extended, cryptID, jobnumber):
    
        html = ''

        if status == "done":
            html += '<tr><td align=right bgcolor="#B7FFE0">Download results:</td><td bgcolor="#B7FFE0">'
            
            if os.path.exists( '%s%s/' % (self.download_dir, cryptID) ):
                html += '<A href="../downloads/%s/">view all files</A>, <A href="../downloads/%s/data_%s.zip">download all files</A>' % ( cryptID, cryptID, jobnumber )
                if extended:
                    html += ', <A href="../downloads/%s/input.resfile">view Resfile</A>, <A href="../downloads/%s/stdout_%s.dat">view raw output</A>' % ( cryptID, cryptID, jobnumber )
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
        
        if parameter['Mini'] == 'mini' or parameter['Mini'] == '1':
            parameter['Mini'] = 'Rosetta 3.0 (mini)'
        elif parameter['Mini'] == 'classic' or parameter['Mini'] == '0':
            parameter['Mini'] = 'Rosetta 2.3 (classic)'
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
        
        if parameter['Errors'] == '' or parameter['Errors'] == 'None':
            
            html += self._showDownloadLinks(status, parameter['KeepOutput'], parameter['cryptID'], parameter['ID'])
            
            if parameter['task'] == '0' or parameter['task'] == 'no_mutation':
                task = "Model Flexibility"
                html += self._showNoMutation( parameter['PDBComplexFile'], parameter['EnsembleSize'], parameter['cryptID'] )            
                
            elif parameter['task'] == '1' or parameter['task'] == 'point_mutation':
                task = "Point Mutation"
                html += self._showPointMutation( parameter['cryptID'],  parameter['PDBComplexFile'], parameter['EnsembleSize'], 
                                                 parameter['PM_chain'], parameter['PM_resid'], parameter['PM_newres'])
                
            elif parameter['task'] == '3' or parameter['task'] == 'multiple_mutation':
                task = "Multiple Point Mutations"
                html += self._showMultiplePointMutations( parameter['cryptID'], parameter['PDBComplexFile'], parameter['EnsembleSize'], parameter['PM_chain'], 
                                                          parameter['PM_resid'], parameter['PM_newres'], parameter['PM_radius'])
                
            elif parameter['task'] == '2' or parameter['task'] == 'upload_mutation':
                task = "Custom Mutation"
                html += self._showComplexMutation( parameter['cryptID'], parameter['PDBComplexFile'], parameter['EnsembleSize'], parameter['Mutations'])
                
            elif parameter['task'] == '4' or parameter['task'] == 'ensemble':
                task = "Backrub ensemble"
                html += self._showEnsemble( parameter['cryptID'], parameter['PDBComplexFile'], parameter['EnsembleSize'], parameter['ENS_temperature'], 
                                            parameter['ENS_num_designs_per_struct'], parameter['ENS_segment_length'] )

        html += '</table><br></td>\n'
        
        return html


    def _showApplet4MultipleFiles(self, comment, list_pdb_files, mutation=None):
        """This shows the Jmol applet for an ensemble of structures with their point mutation(s)"""
        
        # jmol command to load files
        if list_pdb_files != None:
            jmol_cmd = 'load %s; color red; ' % list_pdb_files[0]
            for pdb in list_pdb_files[1:]:
                jmol_cmd += 'load APPEND %s; ' % pdb
            
            # jmol command to show mutation as balls'n'stick
            jmol_cmd_mutation = ''
            if mutation != None: 
                if type(mutation) == type(''):
                    jmol_cmd_mutation = 'select %s; cartoon off; backbone on; wireframe 0.3; ' % mutation
                elif type(mutation) == type([]):
                    for x in mutation:
                        jmol_cmd_mutation += 'select %s; cartoon off; backbone on; wireframe 0.3; ' % x
            
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
            message_html = '<P style="text-align:center; color:red;">%s</P>' % ( message )
        disabled = ''
        if login_disabled:
            disabled = 'disabled'

        html = """<td align="center">
                  <H1 class="title">Login</H1>
                    <P style="text-align:center;">If you do not have an account, please <A href="%s?query=register">register</A> .</P>
                    %s
                    <form method=post action="%s">
                    <table border=0 cellpadding=5 cellspacing=0>
                        <tr><td align=right>Username: </td><td><input type=text name=myUserName value="%s">    </td></tr>
                        <tr><td align=right>Password: </td><td><input type=password name=myPassword value="" %s></td></tr>
                        <tr><td></td>
                    <td align=left>
                    <input type=hidden name=query  value="login">
                    <input type=hidden name=login  value="login">
                    <input type=submit name=submit value="Login" %s>
                    </td></tr>
                    </table>
                    </form>                    
                    Forgot your password? <A href="%s?query=oops">Click here</A> .
                    <br>
                   <td>""" % ( self.script_filename, message_html, self.script_filename, username, disabled, disabled, self.script_filename )

        return html

    def loggedIn(self, username):
        self.username = username
        html = """ <td align="center">You have successfully logged in as %s. <br> <br> \n 
                   Proceed to <A href="%s?query=submit">Simulation Form</A>  or \n
                   <A href="%s?query=queue">Queue</A> . <br><br> </td>\n""" % ( username, self.script_filename, self.script_filename )
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


