import sys
from string import join
import re
sys.path.insert(-1, "../backrub/common")
import colortext

lsttype = type([])
strtype = type("")

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
'BT',#  - Title Primary.
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
                <div style="text-align:right"><a class="style14 publist" href="publications.ris">bibliography (RIS)&nbsp;</a></div>
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
	
	# Create public RIS file
	risfile = contents.split("\n")
	for i in range(len(risfile)):
		if risfile[i].startswith("ER"):
			risfile = risfile[i+1:]
			break
	risfile = join([line for line in risfile if line[0:2] != "C8"], "\n")
	if saveRis:
		F = open("publications.ris", "w")
		F.write(risfile)
		F.write("\n")
		F.close()
	
	publist = []
	
	count = 0
		
	contents.split("\n")
	
	authornames = {}
	sectionTitles = []
	pubsBySection = {}
	pubs = contents.split("ER  -")[1:] # Ignore the comments before the first entry
	for pub in pubs:
		pub = pub.strip()
		errors = []
		if pub:
			d = parsePub(pub)
			
			if not d:
				break
			
			# Get the section title from the custom field and populate the ordered lists
			if not d.get("C8") or type(d["C8"]) == lsttype:
				errors.append("There is a missing or duplicate value for C8 which we reserve for section titles.")
				break
			sectiontitle = d.get("C8")
			if sectiontitle not in sectionTitles:
				sectionTitles.append(sectiontitle)
				pubsBySection[sectiontitle] = []
				
			title = d.get("TI")
			for author in d.get("AU",[]):
				authornames[author] = True
			authors = join(d.get("AU",[]), ", ")
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
			for k, v in d.iteritems():
				if type(v) == strtype and v.startswith("doi:"):
					doi = v[4:].strip()
			#doi = d.get("M3")
			#if doi and doi.startswith("doi: "):
			#	doi = doi.split(":")[1].strip()
			if not(doi or d.get("URL")):
				errors.append("No DOI or URL available.")
			pubsBySection[sectiontitle].append({"authors" : authors, "title" : title, "journal" : journal, "entry" : entry, "doi" : doi, "URL" : d.get("URL")})
			if errors:
				colortext.warning("%s (%s)" % (title, sectiontitle))
				for e in errors:
					colortext.error("\t%s" % e)
				#%s. %s. %s. %s. %s" % (authors, title, journal, entry, doi))
	colortext.message('''
Authors - change names which have duplicate forms to the same long format (full name and surname).
Some potential duplicates are highlighted below but the highlighting neither comprehensive or failsafe.
Yellow potentially indicates a duplicate name, cyan potentially indicates a missing period or first name.''')
	lastSurname = None
	lastInitial = None
	for author in sorted(authornames.keys()):
		names = [n for n in re.split(r'[, ]', author) if n]
		surname = names[0]
		initial = None
		if len(names) > 1:
			initial = names[1][0]
		
		# Catch missing periods in abbreviated names
		maybeMissingPeriodOrFirstName = False
		numberOfFullNames = 0
		for n in names:
			firstPeriod = n.find(".")
			if firstPeriod != -1 and firstPeriod != len(n) - 1:
				maybeMissingPeriodOrFirstName = True
			if len(n) == 1:
				maybeMissingPeriodOrFirstName = True
			elif n[1] != ".":
				numberOfFullNames += 1
		if numberOfFullNames < 2:
			maybeMissingPeriodOrFirstName = True
			
		if lastSurname and surname == lastSurname:
			if not(initial):
				colortext.warning(author)
			elif initial == lastInitial:
				colortext.warning(author)
			else:
				if maybeMissingPeriodOrFirstName:
					colortext.printf(author, color = "cyan")
				else:
					print(author)
		elif maybeMissingPeriodOrFirstName:
			colortext.printf(author, color = "cyan")
		else:
			print(author)
		lastSurname = surname
		lastInitial = initial
		
	for sectiontitle in sectionTitles:
		publist.append((sectiontitle, pubsBySection[sectiontitle]))
		
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

#Missing in PubMed:
# Morozov, AV, Kortemme, T, & Baker, D. Evaluation of models of electrostatic interactions in proteins. J. Phys. Chem. B 107, 2075-2090, 2003.
# Ollikainen N, Sentovich E, Coelho C, Kuehlmann A, Kortemme, T. (2009). SAT-based protein design. Proceedings of the 2009 IEEE/ACM International Conference on Computer-Aided Design (ICCAD 2009): 128-35.
