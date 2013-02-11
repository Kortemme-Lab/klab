#!/usr/bin/python3
# -*- coding: latin-1 -*-

import sys
from string import join
import re
sys.path.insert(-1, "../backrub/common")
import colortext
from os.path import commonprefix

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
'ID', # Seems to be doi
'L3', # Link?
'J1', # ?
]

publication_abbreviations = {
	#"Advances in Protein Chemistry"						: "Adv Protein Chem",
	"ACS Chemical Biology"								: "ACS Chem Biol",
	"Analytical Chemistry"								: "Analyt Chem",
	"Aquatic Toxicology"								: "Aquatic Toxicol",
	"Biochemical and Biophysical Research Communications": "Biochem Biophys Res Comms",
	"Biochemistry"										: "Biochemistry",
	"Bioconjugate Chemistry"							: "Bioconjugate Chem",
	"Bioinformatics"									: "Bioinformatics",
	"Bioorganic & Medicinal Chemistry"					: "Bioorg Med Chem",
	"Biophysical Journal"								: "Biophys Journal",
	"BMC Evolutionary Biology"							: "BMC Evol Biol",
	"BMC Systems Biology"								: "BMC Sys Biol",
	"Cell"												: "Cell",
	"Chemistry & Biology"								: "Chem Biol",
	"Chemical Research in Toxicology"					: "Chem Res Toxicol",
	"Comprehensive Biophysics"							: "Comprehensive Biophysics",
	"Current Opinion in Chemical Biology"				: "Curr Opin Chem Biol",
	"Current Opinion in Structural Biology"				: "Curr Opin Struct Biol",
	"Current Opinion in Biotechnology"					: "Curr Opin Biotechnol",
	"EMBO Reports"										: "EMBO Rep",
	"Environmental and Molecular Mutagenesis"			: "Environ Mol Mutagen",
	"FEBS Journal"										: "FEBS Journal",
	"FEBS Letters"										: "FEBS Letters",
	"Genome Biology"									: "Genome Biology",
	"Genome Research"									: "Genome Research",
	"Integrative and Comparative Biology"				: "Integr and Comparative Biol",
	"Journal of Biological Chemistry"					: "J Biol Chem",
	"Journal of Biomedical & Laboratory Sciences"		: "J Biomed Lab Sci",
	"Journal of Chemical Information and Modeling"		: "J Chem Inf Model",
	"Journal of Computational Biology"					: "J Comp Biol",
	"Journal of the American Chemical Society"			: "J Am Chem Soc",
	#"Methods in Enzymology"								: "Meth Enzym",
	"Journal of Molecular Biology"						: "J Mol Biol",
	"Metabolomics"										: "Metabolomics",
	"Molecular & Cellular Proteomics"					: "Mol Cell Proteomics",
	"Molecular Cell"									: "Mol Cell",
	"Molecular Systems Biology"							: "Mol Syst Biol",
	"Nature"											: "Nature",
	"Nature Biotechnology"								: "Nat Biotech",
	"Nature Chemical Biology" 							: "Nat Chem Biol",
	"Nature Methods" 									: "Nat Methods",
	"Nature Structural & Molecular Biology" 			: "Nat Struct Mol Biol",
	"Nucleic Acids Research"							: "Nucleic Acids Res",
	"NeuroToxicology"									: "NeuroToxicol",
	"Physical Review E"									: "Phys Rev E",
	"Physical Chemistry Chemical Physics"				: "Phys Chem Chem Phys",
	"PLoS Biology" 										: "PLoS Biol",
	"PLoS Computational Biology" 						: "PLoS Comput Biol",
	"PLoS ONE"											: "PLoS ONE",
	"Proceedings of the 9th International Congress of Therapeutic Drug Monitoring & Clinical Toxicology" : "Ther Drug Mon",
	"Proceedings of the National Academy of Sciences"	: "Proc Natl Acad Sci U S A",
	"Protein Science"									: "Protein Sci",
	"Proteins: Structure, Function, and Bioinformatics"	: "Proteins",
	"Proteomics"										: "Proteomics",
	"Sci. STKE"											: "Sci STKE",
	"Science"											: "Science",
	"Spectroscopy: An International Journal"			: "Spectr Int J",
	"Structure"											: "Structure",
	"The Journal of Physical Chemistry B" 				: "J Phys Chem B",
	"The Journal of Cell Biology"						: "J Cell Biol",
	"The Journal of Immunology"							: "J Immunol",
	"Proceedings of the 2009 IEEE/ACM International Conference on Computer-Aided Design (ICCAD 2009)"	: "Proceedings of the 2009 IEEE/ACM International Conference on Computer-Aided Design (ICCAD 2009)",
}
	
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
			
			if key == "JO" and d.get("JO"): # precedence
				d["JO"].insert(-1, val)
				continue
			elif key in ["A1"]:
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

def pubpageID(pub_name):
	if type(pub_name) == type([]):
		pub_name = pub_name[0]
	s = shortFormatAuthor(pub_name)
	s = s.replace(" ", "")
	s = s.replace(".", "")
	s = s.replace(",", "")
	s = s.replace("Ó", "O")
	s = s.replace("ú", "u")
	s = s.lower()
	return s
	
def shortFormatAuthor(author):
	names = re.split(r'[,]', author)
	surname = names[0]
	firstnames = [n for n in re.split(r'[ ]', names[1]) if n]
	initials = join([n[0] for n in firstnames], "")
	return "%s, %s" % (surname, initials)
	
def shortFormatAuthors(authors):
	short = []
	for author in authors:
		short.append(shortFormatAuthor(author))
		#names = re.split(r'[,]', author)
		#surname = names[0]
		#firstnames = [n for n in re.split(r'[ ]', names[1]) if n]
		#initials = join([n[0] for n in firstnames], "")
		#short.append("%s, %s" % (surname, initials))
	return short

def getShortPageRange(startpage, endpage):
	if startpage and endpage:
		endpage_prefix = commonprefix([startpage, endpage])
		if len(endpage_prefix) == len(endpage):
			endpage = endpage[-1] # If the prefix is the end page, just use the last digit
		else:
			endpage = endpage[len(endpage_prefix):]
		return "%s-%s" % (startpage, endpage)
	elif startpage or endpage:
		return startpage or endpage
	else:
		return None

class PublicationEntry(dict):
	
	def __init__(self, publicationtype, authors, title, journal, entry, year, doi, URL, ReferralURL, subtitle):
		self.dict = {
			"Type"			: publicationtype,
			"authors"		: authors,
			"authors_str"	: join(shortFormatAuthors(authors), ", "),
			"title"			: title,
			"journal"		: journal,
			"entry"			: entry or "",
			"year"			: year,
			"doi"			: doi,
			"URL"			: URL,
			"ReferralURL"	: ReferralURL or "",
			"Subtitle"		: "",
		}

	def __getitem__(self, k):
		return self.dict[k]
	
	def getHTML(self, showyear = True):
		d = self.dict
		if showyear:
			d["year_str"] = ", %s" % d["year"]
		else:
			d["year_str"] = ""
		if d["ReferralURL"]:
			d["ReferralURL"] = " <a class='publist' href='%(ReferralURL)s'>[free download]</a>" % d
		
		if d["Type"] == "CHAP":
			d["titlesuffix"] = " in"
		else:
			d["titlesuffix"] = "."
		
		if d.get("doi"):
			return '''%(authors_str)s. %(title)s%(titlesuffix)s %(journal)s %(entry)s%(year_str)s. doi: <a class="publist" href="http://dx.doi.org/%(doi)s">%(doi)s</a>%(ReferralURL)s''' % d
		elif d.get("URL"):
			return '''%(authors_str)s. <a class="publist" href="%(URL)s">%(title)s</a>%(titlesuffix)s %(journal)s %(entry)s%(year_str)s.%(ReferralURL)s''' % d
		else:
			return '''%(authors_str)s. %(title)s%(titlesuffix)s %(journal)s %(entry)s%(year_str)s.%(ReferralURL)s''' % d
	
	def __repr__(self):
		d = self.dict
		if d.get("doi"):
			return '''%(authors_str)s. %(title)s. %(journal)s %(entry)s%(year)s. doi: %(doi)s''' % d
		else:
			return '''%(authors_str)s. %(title)s. %(journal)s %(entry)s%(year)s.''' % d
		
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
	risfile = join([line for line in risfile if line[0:2] != "C8" and line[0:2] != "C7"], "\n")
	if saveRis:
		F = open("publications.ris", "w")
		F.write(risfile)
		F.write("\n")
		F.close()
	
	publist = []
	author_publications = {}
	DOIs = {}
	
	count = 0
		
	contents.split("\n")
	
	knownIssues = ["doi: 10.1038/msb.2009.9"]
	
	publications = {}
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
			authors = d.get("AU",[])
			
			journal = None
			recordtype = d.get("TY") 
			if  recordtype == "JOUR" or recordtype == "CONF":
				journal = d.get("JO")
			elif recordtype == "CHAP":
				journal = d.get("BT")
			else:
				errors.append("Could not determine publication type.")
			
			year = d.get("PY") or d.get("Y1")
			if type(year) == lsttype:
				year = year[0]
			if year and year[:4].isdigit():
				year = year[:4]
			else:
				errors.append("Could not parse year '%s'." % (year))
				year = None
			
			volume = d.get("VL")
			issue = d.get("IS")
			if type(journal) == lsttype:
				journal = journal[0]
			
			publications[journal] = True
		
			entry = None
			startpage = d.get("SP")
			endpage = d.get("EP")
			if volume:
				entry = volume
				if d.get("T2"):
					entry += " (%(T2)s)" % d
				if issue:
					entry += "(%s)" % issue
				elif d.get("TY") != "CHAP":
					errors.append("No issue found.")
				pagerange = getShortPageRange(startpage, endpage)
				if pagerange:
					entry += ":%s" % pagerange
				else:
					errors.append("No start or endpage found.")
				#entry = "%s(%s):%s-%s" % (d.get("VL"), d.get("IS"), d.get("SP"), d.get("EP"))
			else:
				if startpage and endpage and startpage.isdigit() and endpage.isdigit():
					entry = ""
					if d.get("T2"):
						entry = " (%(T2)s)" % d
					entry += ":%s" % getShortPageRange(startpage, endpage)
				else:
					errors.append("No start or endpage found.")
			
			if not(journal):
				errors.append("No journal name found.")
			
			doi = None	
			for k, v in d.iteritems():
				if type(v) == strtype and v.startswith("doi:"):
					doi = v[4:].strip()
			if doi and DOIs.get(doi):
				errors.append("This DOI is duplicated by '%s'." % DOIs[doi])
				DOIs[doi] = title
			if not(doi or d.get("UR")):
				errors.append("No DOI or URL available.")
			
			if authors and title and journal and year:
				if d["TY"] != "CHAP" and not(publication_abbreviations.get(journal)):
					errors.append("Missing abbreviation for '%s'. Skipping entry." % journal)
				else:
					# Abbreviate the journal name
					if d["TY"] != "CHAP":
						journal = publication_abbreviations[journal]
					pubEntry = PublicationEntry(d["TY"], authors, title, journal, entry, year, doi, d.get("UR"), d.get("C7"), d.get("T2"))
					pubsBySection[sectiontitle].append(pubEntry)
					
					for author in authors:
						author_publications[author] = author_publications.get(author) or []
						author_publications[author].append(pubEntry)
			else:
				errors.append("Missing crucial information (author, title, journal, or year) - skipping entry.")
			
			if errors and d.get("M3") not in knownIssues:
				colortext.warning("%s (%s)" % (title, sectiontitle))
				for e in errors:
					colortext.error("\t%s" % e)
				#%s. %s. %s. %s. %s" % (authors, title, journal, entry, doi))
	
	# Check author name forms 
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
			if n.lower() == "and":
				maybeMissingPeriodOrFirstName = True	
			if firstPeriod != -1 and firstPeriod != len(n) - 1:
				maybeMissingPeriodOrFirstName = True
			if len(n) == 1:
				maybeMissingPeriodOrFirstName = True
			elif n[1] != ".":
				numberOfFullNames += 1
		if numberOfFullNames < 2:
			maybeMissingPeriodOrFirstName = True
		
		authorline = "%s -> %s" % (author, shortFormatAuthors([author])[0])
		if lastSurname and surname == lastSurname:
			if not(initial):
				colortext.warning(authorline)
			elif initial == lastInitial:
				colortext.warning(authorline)
			else:
				if maybeMissingPeriodOrFirstName:
					colortext.printf(authorline, color = "cyan")
				else:
					print(authorline)
		elif maybeMissingPeriodOrFirstName:
			colortext.printf(authorline, color = "cyan")
		else:
			print(authorline)
		lastSurname = surname
		lastInitial = initial
	
	for sectiontitle in sectionTitles:
		publist.append((sectiontitle, pubsBySection[sectiontitle]))
		
	return publist, author_publications

# List of lab members with publications. This is used to generate personal publications pages.
labmembers = [
	("Kortemme, Tanja", None),
	("Babor, Mariana", None),
	("Eames, Matt", None),
	("Friedland, Gregory D.", "Greg"),
	(['Humphris-Narayanan, Elisabeth L.', 'Humphris, Elisabeth L.'], None),
	("Linares, Anthony J.", None),
	("Lauck, Florian", None),
	("Mandell, Daniel J.", "Dan"),
	("Melero, Cristina", None),
	("Oberdorf, Richard", "Rich"),
	("Ollikainen, Noah", None),
	("Smith, Colin A.", None),
	("Tamsir, Alvin", None),
	("Kraal, Laurens", None),
	("Ritterson, Ryan", None),
	("Hoersch, Daniel", None),
	("Akiva, Eyal", None),
	("Huang, Yao-ming", None),
	("Stein, Amelie", None),
	("Pache, Roland A.", None),
	("Liu, Lin", None),
	("Smeaton, Michael B.", "Mike"),
	("Kapp, Gregory T.", "Greg"),
	("Liu, Sen", None),
	("Barlow, Kyle A.", None),
	("Ó Conchúir, Shane", None),
	("Varela, Rocco", None),
]

def getPublishedMembers():
	return [l[0] for l in labmembers]
			
def getHTML(page):
	webpages = []
	
	# Main publications page
	html = [header]
	count = 0
	publist, author_publications = parsePublist()
	for section in publist:
		sectiontitle = section[0]
		if sectiontitle != "LabMember":	
			html.append(sectionheader % sectiontitle)
			
			sectionpubs = section[1]
			html.append('''                <ol class="style14" style="counter-reset:item %d;" start="%d">''' % (count, count +1))
			for p in sectionpubs:
				# Do not display the year for sections like ' 2011 Publications'
				showyear = not(sectiontitle[0:4].isdigit() and sectiontitle[4:] == " Publications")
				html.append('''                  <li class="publist">%s<br>''' % p.getHTML(showyear))
				count += 1				
			html.append('''                </ol>''')
	html.append(footer)
	webpages.append((page, join(html)))
	
	# Lab members publications pages
	for labmemberp in labmembers:
		labmember_names = labmemberp[0]
		count = 0
		sectionpubs = []
		if type(labmember_names) != type([]):
			labmember_names = [labmember_names]
		for labmember_name in labmember_names:
			sectionpubs.extend(author_publications.get(labmember_name))
		if sectionpubs:
			html = [header]
			firstname = labmemberp[1] or [n for n in labmember_names[0].split(',')[1].split(' ') if n][0]
			if firstname[-1] == "s":
				sectiontitle = "%s's Publications" % firstname
			else:
				sectiontitle = "%s's Publications" % firstname
			pagename = pubpageID(labmemberp[0])
			html.append(sectionheader % sectiontitle)
			html.append('''                <ol class="style14" style="counter-reset:item %d;" start="%d">''' % (count, count +1))
			for p in sectionpubs:
				html.append('''                  <li class="publist">%s<br>''' % p.getHTML())
				count += 1				
			html.append('''                </ol>''')
			html.append(footer)
			webpages.append(("%s-%s" % (page, pagename), join(html)))
	return webpages

#Missing in PubMed:
# Morozov, AV, Kortemme, T, & Baker, D. Evaluation of models of electrostatic interactions in proteins. J. Phys. Chem. B 107, 2075-2090, 2003.
# Ollikainen N, Sentovich E, Coelho C, Kuehlmann A, Kortemme, T. (2009). SAT-based protein design. Proceedings of the 2009 IEEE/ACM International Conference on Computer-Aided Design (ICCAD 2009): 128-35.

#Genome-wide structural mapping of protein interactions reveals differences in abundance- and expression-dependent evolutionary pressures.
#->  Structural Mapping of Protein Interactions Reveals Differences in Evolutionary Pressures Correlated to mRNA Level and Protein Abundance
