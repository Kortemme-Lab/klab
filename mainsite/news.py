from string import join

header  = '''
      <td width="100%">
        <table style="width: 100%;" border="0" cellpadding="0" cellspacing="0">
          <tbody>
            <tr valign="top">
              <td style="width: 486px;">
                <img src="img/news.jpg" alt="news" style="border: 0px solid ; width: 271px; height: 35px;">
                <br>
                <br> 
                <table style="text-align: left; width: 100%; height: 19px;" border="0" cellpadding="0" cellspacing="0">
                  <tbody>'''

item_html = '''
                    <tr><td width="125px" valign="top"><span class="meeting_text">%(tm)s</span></td><td><span class="meeting_text">%(event)s</span></td></tr> 
                    <tr><td height="10px><td height="10px"></tr>'''

footer = '''
                  </tbody>
                </table>
              </td>
            </tr>
          </tbody>
        </table>
      </td>'''

news_items = [
	('September 2011', 		'''Ryan’s work on engineering light-controlled cadherins is funded by a grant from the NSF'''),
	('August 2011', 		'''A new project on quantifying systems-level protein interaction specificity is funded by the NIH, in collaboration with Nevan Krogan’s group'''),
	('July 2012', 			'''Colin graduates'''),
	('July 2011', 			'''Noah’s abstract is selected for a talk at the “Structural Bioinformatics and Computational Biophysics” ISMB meeting in Vienna'''),
	('June 2011', 			'''Laurens is awarded an ARCS graduate student fellowship'''),
	('June 2011', 			'''Amelie is awarded an EMBO postdoctoral fellowship'''),
	('March 2011', 			'''Dan's work on engineering small molecule biosensors is funded by a grant from the NIH'''),
	('February 2011', 		'''Daniel is awarded a postdoctoral fellowship from the German Research Foundation'''),
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
	('September, 2005',		'''Wah Chiu's NIH nanomedicine grant "Center for Protein Folding Machinery" is funded. Dan's work on developing methods for flexible backbone protein design and engineering "protein adaptors" will be part of the computational core of the center, in collaboration with Judith Frydman and Vijay Pande (Stanford University), and Andrej Sali'''),
	('May, 2005',			'''Greg F. is awarded a NSF graduate research fellowship'''),
	('February, 2005',		'''Tanja is named an Alfred P. Sloan Fellow in Molecular Biology'''),
]

def getHTML(page):
	html = [header]
	for item in news_items:
		tm = item[0]
		event = item[1]
		html.append(item_html % vars())
	html.append(footer)
	return [(page, join(html))]
