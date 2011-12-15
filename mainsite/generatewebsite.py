from string import join
import publications
import news

#<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">

header = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" 
"http://www.w3.org/TR/html4/strict.dtd">
<html>
  <head>
    <meta http-equiv="content-type" content="text/html;charset=UTF-8">
    <title>Kortemme Lab, UCSF | %(pagename)s</title>
    <link href="style.css" type="text/css" rel="stylesheet">
  </head>
  <body style="margin-bottom:0; margin-left:0; margin-right:0; margin-top:0; background-image: url(img/background.jpg);" %(bodyclass)s> 
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
                  <span class="lpanel"><a href="http://www.ucsf.edu/ccb/">Graduate Program in Chemistry and Chemical Biology (CCB)</a></span> 
              <tr valign="top"> 
                <td style="width:0px">  
                <td style="width:228px">
                  <span class="lpanel"><a href="http://www.ucsf.edu/dbps/pspg.html">Graduate Program in Pharmaceutical Sciences and Pharmacogenomics (PSPG)</a></span>
              <tr valign="top">
                <td style="width:0px">  
                <td style="width:228px">
                  <span class="lpanel"><a href="http://ncmi.bcm.tmc.edu/nanomedicine">NIH Center for Protein Folding Machinery</a></span>
                </td>
              <tr valign="top">
                <td style="width:0px">  
                <td style="width:228px">
                  <span class="lpanel"><a href="http://qb3.org/cpl">NIH Center on &quot;Engineering Cellular Control: Synthetic Signaling and Motility Systems&quot;</a></span>
                </td>
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
                    San Francisco, CA 94143-2540 <br>
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

def indexHTML(page):
	F = open(page + ".html", 'r')
	str = F.read()
	F.close()
	return [(page, str)]

news_items = [
	('September, 2010', 	'''Colin's paper on specificity prediction is highlighted by Faculty of 1000'''),
	('September, 2010',		'''Ryan receives the Mel Jones Excellence in Graduate Student Research Award'''),
	('June, 2010',			'''Dan receives the Julius R. Krevans Distinguished Dissertation Award'''),
	('June, 2010',			'''Dan graduates'''),
	('May, 2010', 			'''Matt graduates'''),
	('October, 2009', 		'''Elisabeth graduates'''),
	('August, 2009', 		'''The NSF &quot;Emerging Frontiers&quot; program awards our lab an ARRA research grant to improve and disseminate molecular modeling and prediction methods for the characterization and redesign of interactions between proteins, building on Florian's webserver work'''),
	('April, 2009', 		'''Noah is awarded a NSF graduate research fellowship'''),
	('January, 2009', 		'''The UC Office of the President awards our lab in collaboration with Charlie Strauss at LANL a UC Lab Research Grant on "New algorithms for computational design of protein biosensors". Our lab's contribution builds on Dan and Vageli's work on kinematic loop closure methods'''),
	('January, 2009', 		'''Dan is awarded a PhRMA Foundation predoctoral fellowship in informatics'''),
	('December, 2008', 		'''Greg F. graduates'''),
	('July, 2008', 			'''Ryan is awarded a UCSF HHMI/NIBIB fellowship'''),
	('July, 2008', 			'''Noah is awarded a UCSF HHMI/NIBIB fellowship'''),
	('June, 2008', 			'''Rich is awarded a Kozloff graduate fellowship'''),
	('March, 2008', 		'''Tanja receives an NSF CAREER award'''),
	('July, 2007', 			'''Rich is awarded an iPQB fellowship in complex biological systems'''),
	('April, 2007', 		'''Colin is awarded graduate student fellowships from Genentech, NSF, and DOD'''),
	('October, 2006', 		'''Dan and Elisabeth are recipients of the UCSF/UC Berkeley Nanosciences and Biology Student Award'''),
	('August, 2006', 		'''Elisabeth is awarded a Genentech/Sandler graduate student fellowship'''),
	('July, 2006', 			'''Matt's work on quantifying how alternative mechanisms of protein evolution shape organism fitness is funded by a grant from the Sandler Program in Basic Sciences'''),
	('June, 2006', 			'''Dan is awarded an ARCS graduate student fellowship'''),
	('September, 2005', 	'''Cristina's and Greg K.'s work on engineering protein interaction modules is funded by an NIH grant on &quot;Engineering Cellular Control: Synthetic Signaling and Motility Systems&quot;, headed by Wendell Lim and in collaboration with labs at UCSF and UC Berkeley. Our group will be leading the &quot;molecular tool kit&quot; platform of the center'''),
]

def newsHTML(page):
	'''One-use function to parse the news page to create the array above.''' 
	#F = open(page + "/var/www/html/news.html", 'r')
	F = open("news.html", 'r')
	str = F.readlines()
	F.close()
	
	newsstart = '''<tr><td width="125px" valign="top"><span class="meeting_text">'''
	newsmid = '''</span></td><td><span class="meeting_text">'''
	for line in str:
		idx = line.find(newsstart)
		if idx != -1:
			line = line[idx + len(newsstart):]
			idy = line.find(newsmid)
			tm = line[:idy].strip()
			event = line[idy + len(newsmid):].strip().replace("</span></td></tr>", "")
			print(tm, event)
	
	return [()]
	return [(page, str)]

def makePage(page, d, debug = True):
	testprefix = "test-"
	for pagehtml in d["generator"](page):
		if pagehtml:
			html = []
			html.append(header % d)
			html.append(leftpane % vars())
			html.append(pagehtml[1])
			html.append(footer % d)
			if debug:
				F = open("/var/www/html/%s%s.html" % (testprefix, pagehtml[0]), "w")
			else:
				F = open("/var/www/html/%s.html" % pagehtml[0], "w")
			F.write(join(html, "\n"))
			F.close()

def main():
	strictlyValidated = '''<a href="http://validator.w3.org/check?uri=referer"><img src="http://www.w3.org/Icons/valid-html401" alt="Valid HTML 4.01 Strict" height="31" width="88"></a>'''
	websitepages = {
		'index'        : {'pagename' : 'Home',          'bodyclass' : '',  'validation' : strictlyValidated, 'generator' : indexHTML},
		'publications' : {'pagename' : 'Publications',  'bodyclass' : '',  'validation' : '', 'generator' : publications.getHTML},
		#  'people.html'       : {'pagename' : 'People',        'bodyclass' : 'class="body_people"'},
		#  'research.html'     : {'pagename' : 'Research',      'bodyclass' : ''},
		'news'		: {'pagename' : 'News',         'bodyclass': '', 'validation' : '', 'generator' : news.getHTML},
		#  'contact.html'      : {'pagename' : 'Contact',       'bodyclass' : ''},
		#  'meetings.html'     : {'pagename' : 'Meetings',      'bodyclass' : ''},
	}
	
	for p, d in websitepages.iteritems():
		makePage(p, d)

main()