header = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" 
"http://www.w3.org/TR/html4/strict.dtd">
<html>
  <head>
    <meta http-equiv="content-type" content="text/html;charset=UTF-8">
    <title>Kortemme Lab, UCSF | %(pagename)s</title>
    <link href="style.css" type="text/css" rel="stylesheet">
  </head>
  <body style="margin-bottom:0; margin-left:0; margin-right:0; margin-top:0; background-image: url(img/background.jpg);"> 
    <table border="0" cellpadding="0" cellspacing="0" width="100%%"> 
      <tbody> 
        <tr valign="top"> 
          <td style="height:92px; width:766px"><img src="img/logo_comp2.jpg" alt=""
     style="border: 0px solid ; width: 766px; height: 92px;"></td> 
          <td class="topimg" style="height:92px; width:100%%">&nbsp;</td> 
        </tr> 
      </tbody> 
    </table>'''
# body is open

leftpane = '''
    <table border="0" cellpadding="0" cellspacing="0" width="100%%"> 
      <tbody> 
        <tr valign="top"> 
          <td style="width:228px">
            <table class="menubg" border="0" cellpadding="0" cellspacing="0" width="228"> 
              <tbody> 
                <tr valign="top"> 
                  <td>
                    <table border="0" cellpadding="0" cellspacing="0" width="228"> 
                      <tr valign="top"> 
                        <td style="width:30px">
                        <td>
                        <a href="%(testprefix)sindex.html" class="menulink">Home</a><br>
                      </tr>
                    </table>                    
                    <table border="0" cellpadding="0" cellspacing="0" width="228"> 
                      <tr>
                        <td style="width:27px">
                        <td> 
                          <img src="img/menu_bar.jpg" alt="" class="menu_bar" height="6" width="175"> 
                      </tr>  
                    </table>
                    <table border="0" cellpadding="0" cellspacing="0" width="228"> 
                      <tr valign="top"> 
                        <td style="width:30px">
                        <td><a href="%(testprefix)speople.html" class="menulink">People</a><br>
                      </tr>
                    </table>
                    <table border="0" cellpadding="0" cellspacing="0" width="228"> 
                      <tr>
                        <td style="width:27px">
                        <td> 
                          <img src="img/menu_bar.jpg" alt="" class="menu_bar" height="6" width="175"> 
                      </tr>  
                    </table>     
                    <table border="0" cellpadding="0" cellspacing="0" width="228"> 
                      <tr valign="top"> 
                        <td style="width:30px">
                        <td><a href="%(testprefix)spublications.html" class="menulink">Publications</a><br>
                      </tr>
                    </table>
                    <table border="0" cellpadding="0" cellspacing="0" width="228"> 
                      <tr>
                        <td style="width:27px">
                        <td> 
                          <img src="img/menu_bar.jpg" alt="" class="menu_bar" height="6" width="175"> 
                        </tr>  
                    </table>
                    <table border="0" cellpadding="0" cellspacing="0" width="228"> 
                      <tr valign="top"> 
                        <td style="width:30px">
                        <td><a href="%(testprefix)sresearch.html" class="menulink">Research</a><br>
                        </tr>
                    </table>
                    <table border="0" cellpadding="0" cellspacing="0" width="228"> 
                      <tr>
                        <td style="width:27px">
                        <td> 
                          <img src="img/menu_bar.jpg" alt="" class="menu_bar" height="6" width="175"> 
                      </tr>  
                    </table>
                    <table border="0" cellpadding="0" cellspacing="0" width="228"> 
                      <tr valign="top"> 
                        <td style="width:30px">
                        <td><a href="%(testprefix)smeetings.html" class="menulink">Meetings</a><br>
                      </tr>
                    </table>
                    <table border="0" cellpadding="0" cellspacing="0" width="228"> 
                      <tr>
                        <td style="width:27px">
                        <td> 
                          <img src="img/menu_bar.jpg" alt="" class="menu_bar" height="6" width="175"> 
                      </tr>  
                    </table>
                    <table border="0" cellpadding="0" cellspacing="0" width="228"> 
                      <tr valign="top"> 
                        <td style="width:30px">
                        <td><a href="%(testprefix)snews.html" class="menulink">News</a><br>
                      </tr>
                    </table>
                    <table border="0" cellpadding="0" cellspacing="0" width="228"> 
                      <tr>
                        <td style="width:27px">
                        <td> 
                          <img src="img/menu_bar.jpg" alt="" class="menu_bar" height="6" width="175"> 
                      </tr>  
                    </table>
                    <table border="0" cellpadding="0" cellspacing="0" width="228"> 
                      <tr valign="top"> 
                        <td style="width:30px">
                        <td><a href="%(testprefix)scontact.html" class="menulink">Contact / Join the Lab</a><br>
                      </tr>
                    </table>
                   </td> 
                </tr> 
              </tbody> 
            </table> 
            <img src="img/menubottom.jpg" alt="" class="menu_bar" height="30" width="229">
            <table border="0" cellpadding="0" cellspacing="10" style="line-height:8px;"> 
              <tr valign="top"> 
                <td style="width:0px" valign="middle">  
                <td style="width:228px; height:5px" valign="middle">
                  <span class="lpanel_header">We are part of: </span> 
              <tr valign="top"> 
                <td style="width:0px">
                <td style="width:228px">
                  <span class="lpanel"><a href="http://bts.ucsf.edu/">Department of Bioengineering and Therapeutic Sciences</a></span> 
              <tr valign="top">
                <td style="width:0px">  
                <td style="width:228px">
                  <span class="lpanel"><a href="http://www.qb3.org">California Institute for Quantitative Biosciences (QB3)</a></span>
                </td> 
              <tr valign="top"> 
                <td style="width:0px">  
                <td style="width:228px">
                  <span class="lpanel"><a href="http://ipqb.ucsf.edu/">Integrative Program in Quantitative Biology</a></span> 
              <tr valign="top"> 
                <td style="width:0px">  
                <td style="width:228px">
                  <span class="lpanel"><a href="http://biophysics.ucsf.edu/">Graduate Group in Biophysics</a></span> 
              <tr valign="top"> 
                <td style="width:0px">  
                <td style="width:228px">
                  <span class="lpanel"><a href="http://bioinformatics.ucsf.edu">Graduate Program in Bioinformatics</a></span>
              <tr valign="top"> 
                <td style="width:0px">  
                <td style="width:228px">
                  <span class="lpanel"><a href="http://ccb.ucsf.edu/">Graduate Program in Chemistry and Chemical Biology (CCB)</a></span> 
              <tr valign="top">
                <td style="width:0px">  
                <td style="width:228px">
                  <span class="lpanel"><a href="http://www.synberc.org">Synthetic Biology Engineering and Research Center (SynBERC)</a></span>
                </td>
              </tr> 
            </table> 
            <table border="0" cellpadding="0" cellspacing="10" style="line-height:8px;"> 
              <tr valign="top"> 
                <td style="width:0px" valign="middle">  
                <td style="width:228px; height:5px" valign="middle">
                  <span class="lpanel_header">We are located at: </span> 
              <tr valign="top"> 
                <td style="width:0px">  
                <td style="width:228px">
                  <span class="lpanel">
                    1700 4th Street, Byers Hall 308E<br>
                    UCSF MC 2530<br>
                    San Francisco, CA 94143-2530 <br>
                    (CA 94158 for courier delivery)<br>
                    301 (computational lab)<br>
                    309 (experimental lab)<br>
                    308E (Tanja Kortemme's office)<br>
                  </span>
                </td> 
              </tr> 
            </table> 
            <br><br>
          </td> 
          <!-- Begin page content -->'''

# tr is open
# tbody is open
# table is open
# body is open
# html is open

# The footer closes all of the open tags. Therefore all pages should be wrapped inside a <td> tag. 
footer = '''
        </tr> 
      </tbody> 
    </table>
    <div><br><br></div>
    <table border="0" cellpadding="0" cellspacing="0" width="100%%"> 
      <tbody> 
        <tr valign="top"> 
          <td class="bottombg" style="width:100%%; height:42px">&nbsp;%(validation)s</td> 
        </tr> 
      </tbody> 
    </table> 
    <!-- copyright text -->
    </body>
</html>
'''

strict401 = '''<a href="http://validator.w3.org/check?uri=referer"><img src="http://www.w3.org/Icons/valid-html401" alt="Valid HTML 4.01 Strict" height="31" width="88"></a>'''
	