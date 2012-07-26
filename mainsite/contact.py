content = '''
      <td style="width:100%;">
        <table style="width: 100%;" border="0" cellpadding="0" cellspacing="0"> 
          <tbody> 
            <tr valign="top">
              <td style="width: 486px;">
                <img src="img/contact.jpg" alt="news" style="border: 0px solid ; width: 271px; height: 35px;">
                <br>
                <br> 
                <table style="text-align: left; width: 100%; height: 19px;" border="0" cellpadding="0" cellspacing="2">
                  <tr>
                    <td>
                      <span class="contact_text">
                        <span class="lpanel_header">Prospective graduate students </span> should contact <a href="http://graduate.ucsf.edu/content/prospective-students">UCSF's Graduate Division Office</a> to apply to one of UCSF's graduate programs. I am a member of the <a href="http://ipqb.ucsf.edu">Integrated Program in Quantitative Biology (Biophysics, Bioinformatics and Complex Systems)</a> and the <a href="http://ccb.ucsf.edu">Chemistry and Chemical Biology (CCB)</a> program. We cannot accept graduate students directly into our lab (only after acceptance into a UCSF graduate program and first year rotations)
                        <br>
                        <br>
                        <span class="lpanel_header">Post-doctoral candidates</span> should be highly motivated and experienced, with a passion for science and interest in quantitative biology, computational method development in Rosetta, molecular modeling and design, and molecular engineering. The Kortemme Lab provides a stimulating interdisciplinary environment; we have diverse backgrounds in computer science, physics, engineering, biology and biochemistry. Candidates should have a strong scientific background in one or more of these areas, and have a demonstrated record of high productivity in peer-reviewed literature.  
                        <br>
                        <br>
                        Applications and inquiries should be submitted to Tanja Kortemme (kortemme@cgl.ucsf.edu). Please include a cover letter describing your scientific interests and goals for the postdoc, a CV with publication list, an abstract of your thesis research, and ask three references to email their letters of recommendation directly to Tanja at the same time. 
                        <br><br>
                        The Kortemme Lab is located on the 3rd floor of Byers Hall at the UCSF Mission Bay campus <a href="http://www.ucsf.edu/maps/directions-to-ucsf-mission-bay/">(directions)</a>.
                        <br>
                        <br>
                        <br>
                      </span>
                    </td>
                    <td valign="top"><img src="img/qb3_2.jpg" class="floatright" alt="qb3" style="border: 10px ;">
                    </td>
                  </tr>
                </table>
              </td>
             </tr>
           </tbody>
         </table>
       </td>'''

def getHTML(page):
	return [(page, content)] 