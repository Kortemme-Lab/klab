import sys
from string import join
import re
sys.path.insert(-1, "../backrub/common")
import colortext

lsttype = type([])

taglist = [
'TY',#  - Type of reference (must be the first tag)
'A2',#  - Secondary Author (each author on its own line preceded by the tag)
'A3',#  - Tertiary Author (each author on its own line preceded by the tag)
'A4',#  - Subsidiary Author (each author on its own line preceded by the tag)
'AB',#  - Abstract
'AD',#  - Author Address
'AN',#  - Accession Number
'AU',#  - Author (each author on its own line preceded by the tag)
'C1',#  - Custom 1
'C2',#  - Custom 2
'C3',#  - Custom 3
'C4',#  - Custom 4
'C5',#  - Custom 5
'C6',#  - Custom 6
'C7',#  - Custom 7
'C8',#  - Custom 8
'CA',#  - Caption
'CN',#  - Call Number
'CY',#  - Place Published
'DA',#  - Date
'DB',#  - Name of Database
'DO',#  - DOI
'DP',#  - Database Provider
'EP',#  - End Page
'ET',#  - Edition
'IS',#  - Number 
'JO',#  - Journal name
'J2',#  - Alternate Title (this field is used for the abbreviated title of a book or journal name)
'KW',#  - Keywords (keywords should be entered each on its own line preceded by the tag)
'L1',#  - File Attachments (this is a link to a local file on the users system not a URL link)
'L4',#  - Figure (this is also meant to be a link to a local file on the users's system and not a URL link)
'LA',#  - Language
'LB',#  - Label
'M1',#  - Number
'M3',#  - Type of Work
'N1',#  - Notes
'N2',#  - Abstract
'NV',#  - Number of Volumes
'OP',#  - Original Publication
'PB',#  - Publisher
'PY',#  - Year
'RI',#  - Reviewed Item
'RN',#  - Research Notes
'RP',#  - Reprint Edition
'SE',#  - Section
'SN',#  - ISBN/ISSN
'SP',#  - Start Page
'ST',#  - Short Title
'T2',#  - Secondary Title
'T3',#  - Tertiary Title
'TA',#  - Translated Author
'TI',#  - Title
'TT',#  - Translated Title
'UR',#  - URL
'VL',#  - Volume
'Y2',#  - Access Date
'ER',#  - End of Reference (must be the last tag)
#
'VO', # - Volume?
'URL', # Tag Shane added
'L3', # Link?
]

header  = '''
      <td style="width:100%">
        <table style="width: 100%;" border="0" cellpadding="0" cellspacing="0"> 
          <tbody> 
            <tr valign="top"> 
              <td style="width: 486px;">
                <img src="img/publications.jpg" alt="" style="border: 0px solid ; width: 271px; height: 35px;">
                <br>
                <div style="text-align:right"><a class="style14 publist" href="pubs.ris">bibliography (RIS)</a></div>
'''

sectionheader = '''
                <table style="text-align: left; width: 100%%; height: 19px;" border="0" cellpadding="0" cellspacing="2">
                  <tbody>
                    <tr>
                      <td style="cellpadding:0px; height: 28px; background-color: rgb(51, 102, 255); width: 100%%;">
                        <span class="style16_b">&nbsp;%s</span>
                      </td> 
                </table>
'''

footer  = '''
              </td>
            </tr> 
          </tbody> 
        </table> 
      </td>
'''

def parsePub(pub):
	d = {}
	pub = pub.strip()
	TYs = (pub.split("\n")[0])
	if TYs.startswith("TY  -"):
		for field in pub.split("\n"):
			typedata = field.split("-", 1)
			key = typedata[0].strip()
			val = typedata[1].strip()
			if key in ["A1", "A2", "A3", "A4"]:
				key = "AU"
			elif key == "T1":
				key = "TI"
			elif key == "Y1":
				key = "PY"
			elif key == "DOI":
				key = "M3"
			elif key in ["JF", "JA"]:
				key = "JO"
			if not key in taglist:
				raise Exception("Unrecognized bibliography tag '%s'." % key)
			if d.get(key):
				d[key].append(val)
			else:
				d[key] = [val]
		for k, v in d.iteritems():
			if len(v) == 1:
				d[k] = v[0]
	return d

def parsePublist(saveRis = True):
	F = open("publist.txt", "r")
	contents = F.read()
	F.close()
	
	publist = []
	risfile = []
	#contents=contents.split("[[")
	
	#sections = re.split(r'\[\[(.*?)]](.*?)', contents)
	sections = re.split('(\[\[.*?]].*)', contents)
	if not sections[0]:
		sections = sections[1:]
	assert(len(sections) % 2 == 0)
	sections = [(sections[i], sections[i + 1]) for i in range(0, len(sections), 2)]
	
	count = 0
	print("")
	for section in sections:
		sectiontitle = section[0].replace("[[","")
		sectiontitle = sectiontitle.replace("]]","")
		
		risfile.append(section[1].strip())
		pubs = section[1].split("ER  -")
		pubsBySection = []
		for pub in pubs:
			pub = pub.strip()
			errors = []
			if pub:
				d = parsePub(pub)
				authors = join(d.get("AU",[]), ", ")
				title = d.get("TI")
				journal = d.get("JO")
				volume = d.get("VL")
				issue = d.get("IS")
				startpage = d.get("SP")
				endpage = d.get("EP")
				if type(journal) == lsttype:
					journal = journal[0]
				if volume:
					entry = volume
					if issue:
						entry += "(%s)" % issue
					else:
						errors.append("No issue found.")
					if startpage and endpage:
						entry += ":%s-%s" % (startpage, endpage)
					else:
						errors.append("No start or endpage found.")
					#entry = "%s(%s):%s-%s" % (d.get("VL"), d.get("IS"), d.get("SP"), d.get("EP"))
				else:
					if startpage and endpage and startpage.isdigit() and endpage.isdigit():
						entry += "%s-%s" % (startpage, endpage)
					else:
						errors.append("No start or endpage found.")
				doi = d.get("M3")
				if doi and doi.startswith("doi: "):
					doi = doi.split(":")[1].strip()
				pubsBySection.append({"authors" : authors, "title" : title, "journal" : journal, "entry" : entry, "doi" : doi, "URL" : d.get("URL")})
				if errors:
					colortext.warning(title)
					for e in errors:
						colortext.error("\t%s" % e)
				#%s. %s. %s. %s. %s" % (authors, title, journal, entry, doi))
		publist.append((sectiontitle, pubsBySection))
		count += 1
		if count == 3:#todo
			break
	
	if saveRis:
		F = open("publications.ris", "w")
		F.write(join(risfile, "\n"))
		F.write("\n")
		F.close()
	else:
		print(join(risfile, "\n"))
	return publist

def getHTML(page):
	html = [header]
	count = 0
	for section in parsePublist():
		sectiontitle = section[0]
		html.append(sectionheader % sectiontitle)
		
		sectionpubs = section[1]
		html.append('''                <ol class="style14" style="counter-reset:item %d;" start="%d">''' % (count, count +1))
		for p in sectionpubs:
			if p.get("doi"):
				html.append('''                  <li class="publist">%(authors)s. %(title)s. %(journal)s. %(entry)s. doi: <a class="publist" href="http://dx.doi.org/%(doi)s">%(doi)s</a><br>''' % p)
			elif p.get("URL"):
				html.append('''                  <li class="publist">%(authors)s. <a class="publist" href="%(URL)s">%(title)s</a>. %(journal)s. %(entry)s.<br>''' % p)
			else:
				html.append('''                  <li class="publist">%(authors)s. %(title)s. %(journal)s. %(entry)s.<br>''' % p)
			count += 1				
		html.append('''                </ol>''')
	html.append(footer)
	return join(html)

#SAT-based protein design is missing in PubMed
