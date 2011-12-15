from string import join
import publications

header = '''
      <td style="width: 100%">
        <table style="width: 100%;" border="0" cellpadding="0" cellspacing="0"> 
          <tbody> 
            <tr valign="top">
              <td style="width: 486px;">
                <img src="img/people.jpg" alt="" style="border: 0px solid ; width: 271px; height: 35px;">
                <br> 
                <br>'''

footer = '''
              </td>
            </tr>
          </tbody>
        </table>
      </td>'''

p_tanja = {
	"name"		:	"Tanja Kortemme",
	"image"		:	"img/tanja.jpg",
	"text"		:	"My main scientific interests range from the details of the physical interactions between atoms and molecules to the architecture and evolution of interaction networks in complex biological systems.",
	"degrees"	:	[
		('Vordiplom (BS)', 'Chemistry,<br>Physical Chemistry', 'University of Hannover, Germany'),
		('Diplom (MSc)', 'Biophysics', 'Stanford University / University of Hannover'),
		('Dr.rer.nat (Ph.D.)', 'Biochemistry', 'EMBL Heidelberg / University of Hannover'),
	],
	"degree_w"	:	("", "width:100px;", "width:168px;"),
	"extratext"	:	"Postdoctoral work in computational and structural biology at EMBL Heidelberg and the Howard Hughes Medical Institute, University of Washington, Seattle",
	"caption"	:	"",
	"mouseover"	:	"",
	"pub_name"	:	"Kortemme, Tanja"
}

p_daniel = {
	"name"		:	"Daniel Hoersch",
	"image"		:	"img/daniel.jpg",
	"text"		:	"Groups II chaperonins are molecular machines employing the energy of ATP hydrolysis to mediate protein folding in eukaryotes and archea via a still largely enigmatic mechanism. I am currently working on a project using an engineering approach towards elucidating chaperonin mechanism with two interrelated goals: First, to test functional hypotheses derived from recent high-resolution structures of group II chaperonins in multiple conformations; and second, to convert a model chaperonin, the biochemically tractable archeal Mm-cpn, from an ATP- to a light-driven machine.",
	"degrees"	:	[
		('Vordiplom (BS)', 'Physics', 'Ludwig-Maximilians-Universitaet, Germany'),
		('Diplom (MSc)', 'Physics', 'Freie Universitaet Berlin, Germany'),
		('Dr.rer.nat. (Ph.D.)', 'Physics', 'Freie Universitaet Berlin, Germany'),
	],
	"degree_w"	:	("", "width:50px;", ""),
	"extratext"	:	"Postdoctoral work in molecular biophysics at Freie Universitaet Berlin",
	"caption"	:	"This is no figure caption.",
	"mouseover"	:	"Onward!",
	"pub_name"	:	"Hoersch, Daniel",
	"fellowship"	:	"DFG postdoctoral fellow",
}

p_eyal = {
	"name"		:	"Eyal Akiva",
	"image"		:	"img/eyal.jpg",
	"text"		:	"I am interested in the underlying principles of protein-protein interaction specificity. I intend to focus on deciphering the balance between features that enhance wild-type associations and the features that weaken undesired associations between proteins. To this end, I will use structural computation and genetic/biochemical methods to study a model system. I hope to reveal both residue-level and system-wide determinants of specificity. Such findings will hopefully lead to better understanding of protein-protein interactions and allow us to design more specific interactions.",
	"degrees"	:	[
		('Bachelor of Science', 'Biology and Computer Science', 'Bar Ilan University, Israel'),
		('Master of Science', 'Human Genetics and Bioinformatics', 'The Hebrew University of Jerusalem, Israel'),
		('Ph.D.', 'Bioinformatics', 'The Hebrew University of Jerusalem, Israel'),
	],
	"degree_w"	:	("width:120px;", "width:120px;", "width:160px;"),
	"extratext"	:	"",
	"caption"	:	"Fig. 1: EYL-1 expressed in the high salinity background of the pacific ocean",
	"mouseover"	:	"Onward!",
	"pub_name"	:	"Akiva, Eyal",
}

p_amelie = {
	"name"		:	"Amelie Stein",
	"image"		:	"img/amelie.jpg",
	"text"		:	"I study protein interactions to elucidate which molecular and cellular factors determine the high specificity observed in such interactions, currently focusing on yeast Gsp1 and bacterial two-component signal transduction systems.",
	"degrees"	:	[
		('Bachelor of Science', 'Computer Science / Bioinformatics', 'University of Tübingen, Germany'),
		('Master of Science', 'Computer Science / Bioinformatics', 'University of Tübingen, Germany and UNC Chapel Hill, NC, USA'),
		('Ph.D.', 'Bioinformatics / Biomedicine', 'IRB Barcelona and Universitat Pompeu Fabra, Barcelona, Spain'),
	],
	"degree_w"	:	("width:120px;", "width:120px;", "width:160px;"),
	"extratext"	:	"Postdoctoral work in structural and computational biology at IRB Barcelona",
	"caption"	:	"Usually I'm more colorful.",
	"mouseover"	:	None,
	"pub_name"	:	"Stein, Amelie",
	"fellowship"	:	"EMBO postdoctoral fellow",
}

p_roland = {
	"name"		:	"Roland Pache",
	"image"		:	"img/roland.png",
	"text"		:	"During my PhD, I developed a powerful novel method for the alignment of protein interaction networks, called NetAligner. This method allows to easily compare networks of arbitrary topology, including protein complexes, pathways and whole interactomes, with a wide range of possible applications. For my postdoc, I moved from the field of Network Biology over to Structural Biology, basically changing from a 2D perspective on studying protein interactions to a 3D one. I am now mostly interested in protein loop modeling by robotics-inspired conformational sampling, as well as in the design of protein interactions and molecular biosensors.",
	"degrees"	:	[
		('Bachelor of Science', 'Computer Science (Bioinformatics)', 'University of Tübingen, Germany'),
		('Master of Science', 'Computer Science (Bioinformatics)', 'University of Tübingen, Germany'),
		('Ph.D.', 'Biomedicine (Bioinformatics)', 'University of Barcelona, Spain'),
	],
	"degree_w"	:	("width:120px;", "width:120px;", "width:160px;"),
	"extratext"	:	"",
	"caption"	:	"In my free time I practice Aikido and explore the world of photography.",
	"mouseover"	:	None,
	"pub_name"	:	"Pache, Roland",
}

p_ming = {
	"name"		:	"Yao-ming Huang",
	"image"		:	"img/ming.jpg",
	"text"		:	"My research surrounds the relationship between protein sequences and protein structures. In particular I study the usage of HMMSTR structure prediction in improving sequence alignment, the engineering of green fluorescent protein as a potential peptide biosensor, and the development of computational protein design algorithms.",
	"degrees"	:	[
		('Bachelor of Science', 'Medical Technology', 'National Taiwan University, Taipei, Taiwan'),
		('Master of Science', '	Molecular Biology / Biochemistry', 'National Taiwan University, Taipei, Taiwan'),
		('Ph.D.', 'Structural Biology / Bioinformatics', 'Rensselaer Polytechnic Institute, New York, USA'),
	],
	"degree_w"	:	("width:120px;", "width:120px;", "width:160px;"),
	"extratext"	:	"Postdoctoral research in structural and computational biology at Rensselaer Polytechnic Institute",
	"caption"	:	"",
	"mouseover"	:	None,
	"pub_name"	:	"Huang, Yao-ming",
}

p_lin = {
	"name"		:	"Lin Liu",
	"image"		:	"img/lin.png",
	"text"		:	"I work on development and application of computational methods for the prediction of protein structures and the design of protein interactions. In particular, I apply robotics-based algorithms for modeling of protein conformations and for multi-constraint protein design, developed in the Kortemme lab, and apply these methodologies to experimental model system. I also test predictions experimentally on the CypA system.",
	"degrees"	:	[
		('Bachelor of Science', 'Biological Science', 'University of Science and Technology of China, Hefei, China'),
		('Ph.D.', 'Molecular Biophysics and Structural Biology', 'University of Pittsurgh, Pittsburgh, PA, USA'),
	],
	"degree_w"	:	("width:120px;", "width:120px;", "width:160px;"),
	"extratext"	:	"",
	"caption"	:	"I am a super fan of Raymond Lam ^_^",
	"mouseover"	:	None,
	"pub_name"	:	"Liu, Lin",
}

p_cristina = {
	"name"		:	"Cristina Melero",
	"image"		:	"img/cristina.jpg",
	"text"		:	"I apply a combination of computational and experimental approaches to protein-protein interactions in PDZ domain containing proteins. My work will help to elucidate the contributions of specific residues to both affinity and specificity in PDZ-ligand interactions. More generally, we hope to understand how PDZ domain containing proteins help organize multimeric complexes involved in essential cellular processes.",
	"degrees"	:	[
		('Bachelor of Science', 'Physical Chemistry ', 'Complutense University, Madrid'),
	],
	"degree_w"	:	("width:120px;", "width:120px;", "width:160px;"),
	"extratext"	:	"",
	"caption"	:	"During my free time, I enjoy hiking, biking and other outdoors activties. I also love big white dogs, as you can see (dog not shown).",
	"mouseover"	:	"I swear I have a dog",
	"pub_name"	:	"Melero, Cristina",
}

p_rich = {
	"name"		:	"Rich Oberdorf",
	"image"		:	"img/rich.jpg",
	"text"		:	"Although there is a strong global relationship between mean protein abundance and abundance noise, there is also important structure in the degree to which individual proteins deviate from this global correspondence that suggests selection for high or low noise in the expression of specific proteins. Noisy gene expression could impair cell function by disrupting cell signaling and regulation. Conversely, stochasticity in gene expression could be beneficially exploited to enhance cellular diversity or be required for successful transitioning between states. While some consequences of cellular variability on organism fitness have been suggested, direct tests have been limited. My work seeks to directly test the effects of varying expression noise levels by establishing systematic methods for manipulating expression variation while preserving mean expression and measuring the fitness effects that result from such perturbations.",
	"degrees"	:	[
		('Bachelor of Science', 'Physics and Mathematics', 'Brandeis University'),
	],
	"degree_w"	:	("width:140px;", "width:140px;", "width:140px;"),
	"extratext"	:	"",
	"caption"	:	"I am but a man, hanging off the edge of an enormous protein.",
	"mouseover"	:	"Wiiiiiiiiii!",
	"pub_name"	:	"Oberdorf, Richard",
}


p_colin = {
	"name"		:	"Colin Smith",
	"image"		:	"img/colin.jpg",
	"text"		:	"My research centers around the functionally relevant loop motions of proteins in their native state. I am developing and evaluating models which capture and efficiently sample those motions in all-atom simulations. Using Monte Carlo and other techniques, I am interested in improving our ability to accurately predict the free energies of transitions on the microsecond time scale. Towards that end, I aim to develop model systems for experimentally testing and refining our  techniques for prediction/design of directed flexibility. Longer term, I want to engineer a local allosteric switch into a protein which is not currently allosterically regulated.",
	"degrees"	:	[
		('Bachelor of Arts', 'Biology and Computer Science', 'New York University'),
	],
	"degree_w"	:	("width:140px;", "width:140px;", "width:144px;"),
	"extratext"	:	"",
	"caption"	:	"My other scientific interest is studying self-induced hypothermia while swimming in San Francisco Bay.",
	"mouseover"	:	"Boo!",
	"pub_name"	:	"Smith, Colin A.",
}

p_ryan = {
	"name"		:	"Ryan Ritterson",
	"image"		:	"img/ryan.jpg",
	"text"		:	"I am principally interested in the computational reengineering and redesign of biological objects to both answer difficult scientific questions as well as solve interesting problems in both biological systems and larger abiotic contexts. Currently, I am seeking ways to pry out new knowledge about the relationship between cadherin-mediated adhesion and cell to cell signaling, with the hope of both learning more about how the two processes are interrelated and perhaps discovering novel ways of controlling them.",
	"degrees"	:	[
		('Bachelor of Science', 'Computational Engineering Science', 'UC Berkeley'),
	],
	"degree_w"	:	("width:145px;", "width:157px;", "width:130px;"),
	"extratext"	:	"",
	"caption"	:	"I would start a company that would build a hydrogen infrastructure so we can move our economy off petroleum.",
	"mouseover"	:	"I only wanna be with you",
	"pub_name"	:	"Ritterson, Ryan",
}

p_noah = {
	"name"		:	"Noah Ollikainen",
	"image"		:	"img/noah.jpg",
	"text"		:	"I'm currently developing efficient algorithms for protein interface design.  Specifically, I am working on a new deterministic approach that can handle multiple constraints and still converge to the global minimum energy conformation in a short amount of time.  I plan to apply this approach to engineer proteins with altered interaction specificities.",
	"degrees"	:	[
		('Bachelor of Science', 'Bioinformatics', 'UCSD'),
	],
	"degree_w"	:	("width:145px;", "width:157px;", "width:130px;"),
	"extratext"	:	"",
	"caption"	:	"I can't find my glasses!",
	"mouseover"	:	"...or can I?",
	"pub_name"	:	"Ollikainen, Noah",
	"fellowship"	:	"NSF graduate fellow",
}

p_laurens = {
	"name"		:	"Laurens Kraal",
	"image"		:	"img/laurens.jpg",
	"text"		:	"My academic interests comprise synthetic biology, microbial ecology, microbial interactions and genome organization. Using comparative genomics on the plethora of microbial genomes currently available, my computational research aims to identify functional clusters and protein interaction networks that are specific to either phylogeny or ecology. Experimentally, I hope to validate my findings using synthetic biology and whole genome engineering.",
	"degrees"	:	[
		('Bachelor of Arts', 'Theoretical Philosophy', 'University of Groningen'),
		('Bachelor of Science', 'Molecular Biology', 'University of Groningen'),
		('Master of Science', 'Biomedical Sciences', 'Utrecht University'),
	],
	"degree_w"	:	("width:145px;", "width:157px;", "width:130px;"),
	"extratext"	:	"",
	"caption"	:	"I want to 3D print my thesis",
	"mouseover"	:	"...or maybe IMAX",
	"pub_name"	:	"Kraal, Laurens",
	"fellowship"	:	"ARCS graduate fellow",
}

p_debbie = {
	"name"		:	"Debbie Jeon",
	"image"		:	"img/debbie.jpg",
	"text"		:	"My work focuses on the S. cerevisiae Ran homolog Gsp1, trying to isolate which residues contribute to interactions with Gsp1's 57 known interaction partners. Our experimental strategy can be broken into three parts: computational predictions of mutations, which are subsequently cloned and recombined into the yeast genome, and finally followed by E-MAP analysis of the genetic interactions each mutation causes. As each mutant should generate a unique data set of genetic interactions, we hope to attribute specific functions to each mutation we make. For the subset of mutations that generate the most interesting phenotypes, we will follow up the E-MAPs with biochemical methods to verify our computational predictions in more detail, both to learn more details about Gsp1 function and the accuracy of our computational prediction methods.",
	"degrees"	:	[
		('Bachelor of Arts', 'Molecular Biology and Spanish', 'Claremont McKenna College'),
	],
	"degree_w"	:	("width:110px;", "width:100px;", "width:160px;"),
	"extratext"	:	"",
	"caption"	:	"I like cupcakes.",
	"mouseover"	:	"Chocolate... vanilla... you name it!",
	"pub_name"	:	"Jeon, Debbie",
}

p_shane = {
	"name"		:	"Shane O'Connor",
	"image"		:	"img/shane.jpg",
	"text"		:	"My interest is in using scripting to build frameworks around the scientific software used in the lab with the goal of allowing rapid-prototyping and development. My background includes work on garbage collection in a memory-managed scripting language. I maintain and update the Backrub webserver and take care of some IT administrative tasks.",
	"degrees"	:	[
		('Bachelor of Arts', 'Information and Communications Technology', 'Trinity College Dublin, Ireland'),
		('Ph.D.', 'Computer Science', 'Trinity College Dublin, Ireland'),
	],
	"degree_w"	:	("width:110px;", "width:100px;", "width:160px;"),
	"extratext"	:	"Postdoctoral work in commercial scripting engines for console-based videogame development at Trinity College Dublin, Ireland",
	"caption"	:	"Have you tried turning it off and on again?",
	"mouseover"	:	"Yeah, you need to turn it on.",
	"pub_name"	:	"Ó Conchúir, Shane",
}

p_bob = {
	"name"		:	"",
	"image"		:	"img/.jpg",
	"text"		:	"",
	"degrees"	:	[
		('Bachelor of Science', '', ''),
		('Master of Science', '', ''),
		('Ph.D.', '', ''),
	],
	"degree_w"	:	("width:110px;", "width:120px;", "width:160px;"),
	"extratext"	:	"",
	"caption"	:	"",
	"mouseover"	:	None,
	"pub_name"	:	", ",
}

# This list creates the sections for current members of the group
peopleByGroup = [
	('Principal Investigator', (p_tanja,)),
	('Postdoctoral Scholars', (p_daniel, p_eyal, p_amelie, p_roland, p_ming, p_lin)),
	('Specialist', (p_cristina,)),
	('Graduate Students', (p_rich, p_colin, p_ryan, p_noah, p_laurens)),
	('Staff Research Associate', (p_debbie,)),
	('Software Engineer', (p_shane,))
]

pastRotationStudents = [
	{"name" : 'Joel Karpiak', "course" : 'CCB', "rotation" : 'Winter 2010',},
	{"name" : 'Ian Vaughn', "course" : 'Biophysics', "rotation" : 'Fall 2009',},
	{"name" : 'Geoff Rollins', "course" : 'Biophysics', "rotation" : 'Winter 2009',},
	{"name" : 'Rocco Varela', "course" : 'BMI', "rotation" : 'Winter 2009',},
	{"name" : 'Roxana Ordonez', "course" : 'BMI', "rotation" : 'Summer 2008',},
	{"name" : 'Elaine Kirshke', "course" : 'Biophysics', "rotation" : 'Winter 2008',},
	{"name" : 'Charles Kehoe', "course" : 'BMI', "rotation" : 'Winter 2008',},
	{"name" : 'Jaline Gerardin', "course" : 'Biophysics', "rotation" : 'Fall 2007',},
	{"name" : 'Alvin Tamsir', "course" : 'Tetrad', "rotation" : 'Spring 2007', "pub_name" : 'Tamsir, Alvin'},
	{"name" : 'Sheel Dandekar', "course" : 'Biophysics', "rotation" : 'Spring 2006',},
	{"name" : 'Reid Williams', "course" : 'Biophysics', "rotation" : 'Fall 2006',},
	{"name" : 'Dan Gray', "course" : 'CCB', "rotation" : 'Fall 2006',},
	{"name" : 'Michael Hicks', "course" : 'PSPG', "rotation" : 'Winter 2005',},
	{"name" : 'Chris McClendon', "course" : 'Biophysics', "rotation" : 'Fall 2005',},
	{"name" : 'Ian Harwood', "course" : 'Biophysics', "rotation" : 'Spring 2005',},
	{"name" : 'Kareen Riviere', "course" : 'PSPG', "rotation" : 'Winter 2005',},
	{"name" : 'Mike Keiser', "course" : 'BMI', "rotation" : 'Fall 2004',},
]

labAlumni = [
	{"name" : 'Colin Smith', "qualification" : "PhD", "period" : '2006-2011', "currentJob" : 'Postdoc', "jobLocation" : 'Max Planck Institute Goettingen, Germany', "pub_name" : "Smith, Colin A."},
	{"name" : 'Dan Mandell', "qualification" : "PhD", "period" : '2005-2011', "currentJob" : 'Postdoc', "jobLocation" : 'Harvard University', "pub_name" : 'Mandell, Daniel J.',},
	{"name" : 'Matt Eames', "qualification" : "PhD", "period" : '2005-2011', "currentJob" : 'Patent Scientist', "jobLocation" : 'Davis Wright Tremaine', "pub_name" : 'Eames, Matt',},
	{"name" : 'Sen Liu', "qualification" : "PhD", "period" : '2008-2010', "currentJob" : 'Associate Professor', "jobLocation" : 'Three Gorges University, China',},
	{"name" : 'Florian Lauck', "qualification" : "MSc", "period" : '2008-2010', "currentJob" : 'Specialist', "jobLocation" : 'UCSF', "pub_name" : 'Lauck, Florian',},
	{"name" : 'Michael Michalik', "qualification" : None, "period" : '2009-2010', "currentJob" : 'Graduate Program', "jobLocation" : 'University of Bonn, Germany',},
	{"name" : 'Thomas Bliska', "qualification" : None, "period" : '2010', "currentJob" : 'Undergraduate', "jobLocation" : 'Williams College',},
	{"name" : 'Aaron Nichols', "qualification" : None, "period" : '2010', "currentJob" : 'Undergraduate', "jobLocation" : 'UC Riverside',},
	{"name" : 'Elisabeth Humphris', "qualification" : "PhD", "period" : '2005-2009', "currentJob" : 'Postdoc', "jobLocation" : 'Yale', "pub_name" : 'Humphris, Elisabeth L.',},
	{"name" : 'Matt Chroust', "qualification" : None, "period" : '2009', "currentJob" : 'Dentistry Graduate Program', "jobLocation" : 'UCSF',},
	{"name" : 'Mariana Babor', "qualification" : "PhD", "period" : '2006-2009', "currentJob" : '', "jobLocation" : 'Burnham Institute San Diego', "pub_name" : 'Babor, Mariana',},
	{"name" : 'Greg Kapp', "qualification" : "PhD", "period" : '2004-2009', "currentJob" : 'Scientist', "jobLocation" : 'Omniox Inc.',},
	{"name" : 'Greg Friedland', "qualification" : "PhD", "period" : '2004-2008', "currentJob" : 'Postdoc', "jobLocation" : 'Joint Bioenergy Institute & UC Berkeley', "pub_name" : 'Friedland, Gregory D.',},
	{"name" : 'Catherine Shi', "qualification" : None, "period" : '2008', "currentJob" : 'iPQB graduate program', "jobLocation" : 'UCSF',},
	{"name" : 'Anthony Linares ', "qualification" : None, "period" : '2006, 2007', "currentJob" : 'MD/PhD program', "jobLocation" : 'UCLA', "pub_name" : 'Linares, Anthony J.',},
	{"name" : 'David Lomelin ', "qualification" : None, "period" : '2004-2006', "currentJob" : 'BMI graduate program', "jobLocation" : 'UCSF',},
	{"name" : 'Loren Baugh', "qualification" : "PhD", "period" : '2004-2005', "currentJob" : 'Postdoc', "jobLocation" : 'University of Washington Seattle',},
]

def sectionHeader(title):
	return '''
                <span class="u_group_header">%(title)s</span>
                <br>''' % vars() 

def ruledSectionHeader(title, width = 486):
	return sectionHeader(title) + '''
                <hr style="margin-left:0px; text-align:left; width: %(width)spx; height: 1px;">''' % vars()

def getPeopleHTML():
	html = []
	publishedMembers = publications.getPublishedMembers()
	print("*", publishedMembers)
	for pgroup in peopleByGroup:
		groupname = pgroup[0]
		people = pgroup[1]
		html.append(ruledSectionHeader(groupname))
		#'''
        #        <span class="u_group_header">%(groupname)s</span>
        #        <br> 
        #        <hr style="margin-left:0px; text-align:left; width: 486px; height: 1px;">''' % vars())
		for person in people:
			name = person["name"]
			firstname = person["name"].split(" ")[0]
			pimage = person["image"]
			ptext = person["text"]
			pfellowship = person.get("fellowship") or ""
			if pfellowship:
				pfellowship = '''<div style="text-align:left" class="u_people_fellowship">%s</div><br>''' % pfellowship
			ptitle = person.get("mouseover") or name
			pcaption = person.get("caption") or ""
			publink_open = ""
			publink_close = ""
			if person.get("pub_name") and person["pub_name"] in publishedMembers:
				print(person)
				pagename = publications.pubpageID(person["pub_name"])
				publink_open = "<a href='test-publications-%s.html'>" % pagename
				publink_close = "</a>"
			html.append('''
                <table style="text-align: left; width: 481px; height: 191px;" border="0" cellpadding="0" cellspacing="2"> 
                  <tbody> 
                    <tr> 
                      <td style="height: 28px; background-color: rgb(51, 102, 255); width: 369px;">
                        <span class="u_name">&nbsp;%(name)s</span>
                      </td> 
                      <td style="line-height:3px; vertical-align: top; width: 100px; height: 157px;" colspan="1" rowspan="2">
                        %(publink_open)s<img style="width: 100px; height: 110px;" alt="%(firstname)s" title="%(ptitle)s" src="%(pimage)s">%(publink_close)s
                        <span class="body_people">%(pcaption)s</span>
                      </td> 
                    </tr> 
                    <tr> 
                      <td style="vertical-align: top; width: 369px; height: 157px;">
                        <span class="u_people_text">%(ptext)s</span>
                        <br> 
                        <br> 
                        %(pfellowship)s
                        <table cellpadding="0" cellspacing="0" style="line-height:3px; text-align:left; width:100%%; border:0;"> 
                          <tbody>''' % vars())

			for degree in person["degrees"]:
				qualification = degree[0]
				subjects = degree[1]
				institutes = degree[2]
				
				c1width = person["degree_w"][0]
				c2width = person["degree_w"][1]
				c3width = person["degree_w"][2]
				
				html.append('''
                            <tr class="people_qual" style="line-height:3px;"> 
                              <td style="vertical-align: top;%(c1width)s"><span class="degrees_people">%(qualification)s&nbsp;&nbsp;&nbsp;</span></td> 
                              <td style="vertical-align: top;%(c2width)s"><span class="degrees_people">%(subjects)s&nbsp;&nbsp;</span></td> 
                              <td style="vertical-align: top;%(c3width)s"><span class="degrees_people">%(institutes)s</span></td> 
                            </tr>''' % vars())
			if person.get("extratext"):
				html.append('''
                            <tr class="people_qual"> 
                              <td style="height: 40px; width: 169px;" colspan="3">
                                <span class="degrees_people">%(extratext)s
                                  <br> 
                                </span>
                              </td> 
                            </tr>''' % person)
			html.append(''' 
                          </tbody> 
                        </table> 
                        <br>
                      </td> 
                    </tr> 
                  </tbody> 
                </table>''')
	return html

def getPastRotationStudentsHTML():
	html = [sectionHeader("Past Rotation Students")]
	html.append('                <div class="u_people_text">')
	html.append('                <table cellspacing="0">')
	html.append('                  <tr><td colspan="3"><hr></td></tr>')
	for student in pastRotationStudents:
		publink_open = ""
		publink_close = ""
		if student.get("pub_name"):
			pagename = publications.pubpageID(student["pub_name"])
			publink_open = "<a class='publist' href='test-publications-%s.html'>" % pagename
			publink_close = "</a>"
		pname = student["name"]
		pcourse = student["course"]
		protation = student["rotation"]
		html.append("                  <tr><td>%(publink_open)s%(pname)s%(publink_close)s, %(pcourse)s, %(protation)s</td></tr>" % vars())
	html.append('                </table>')
	html.append('                </div>')
	html.append('                <br>')
	return html

def getLabAlumniHTML():
	html = [sectionHeader("Lab Alumni")]
	html.append('                <div class="u_people_text">')

	html.append('                <table>')
	html.append('                  <tr><td colspan="3"><hr></td></tr>')
	for alumnus in labAlumni:
		publink_open = ""
		publink_close = ""
		html.append('                  <tr>')
		if alumnus.get("pub_name"):
			pagename = publications.pubpageID(alumnus["pub_name"])
			publink_open = "<a class='publist' href='test-publications-%s.html'>" % pagename
			publink_close = "</a>"
		
		pname = alumnus["name"]
		pqual = alumnus["qualification"]
		if pqual:
			pname += ", %s" % pqual 
		
		pperiod = alumnus["period"]
		
		if alumnus.get("currentJob"):
			pcurrentPost = "%(currentJob)s, %(jobLocation)s" % alumnus
		else:
			pcurrentPost = alumnus["jobLocation"]
		
		html.append('                    <td style="width:180px;">%(publink_open)s%(pname)s%(publink_close)s</td>' % vars())
		html.append('                    <td style="width:100px;">%(pperiod)s</td>' % vars())
		html.append('                    <td>%(pcurrentPost)s</td>' % vars())
		html.append('                  </tr>')
	html.append('                </table>')
	html.append('                </div>')
	html.append('                <br>')
	return html

def getHTML(page):
	html = [header]
	#for item in news_items:
	#	tm = item[0]
	#	event = item[1]
	#	html.append(item_html % vars())
	html.extend(getPeopleHTML())
	html.extend(getPastRotationStudentsHTML())
	html.extend(getLabAlumniHTML())
	html.append(footer)
	return [(page, join(html))]



old ='''
<!--
                <table style="text-align: left; width: 481px;" border="0"
 cellpadding="0" cellspacing="2"> 
                  <tbody> 
                    <tr> 
                      <td cellpadding="0"
 style="background-color: rgb(51, 102, 255); width: 369px; height: 28px;"><span class="name">&nbsp;Greg Friedland</td> 
                      <td
 style="vertical-align: top; width: 100px; height: 148px;" colspan="1"
 rowspan="2"><img style="width: 100px; height: 110px;" alt="Greg F."
 title="Struggling to stay awake" src="img/gregf.jpg"><span class="body">I like to rock climb and play power ballads on guitar.</span></td> 
                    </tr> 
                    <tr> 
                      <td
 style="vertical-align: top; width: 369px; height: 148px;"><span class="people_text">I'm working on extending our computational model of a protein from a  
single static structure to a dynamic ensemble of structures.  To  
achieve this I'm using our simplified all-atom potential to develop a  
model for protein motions that explains NMR measurements of protein  
dynamics.  We hope this will help us understand the types of motions  
proteins make in solution and what the functional consequences are of  
such motions.</span><br> 
                        <br> 
                        <table
 border="0" cellpadding="0" cellspacing="0" style="text-align: left; width: 100%;"> 
                          <tbody> 
                            <tr> 
                              <td style="width: 120px;"><span class="degrees">Bachelor of Arts </span></td> 
                              <td style="width: 205px;"><span class="degrees">Computer Science and Physics </span></td> 
                              <td style="width: 144px;"><span class="degrees">Dartmouth College</span></td> 
                            </tr> 
                          </tbody> 
                        </table> 
                        <br> </td> 
                    </tr> 
                  </tbody> 
                </table> 
-->


                
<!--
                <table style="text-align: left; width: 481px;" border="0"
 cellpadding="0" cellspacing="2"> 
                  <tbody> 
                    <tr> 
                      <td cellpadding="0"
 style="background-color: rgb(51, 102, 255); width: 369px; height: 28px;"><span class="name">&nbsp;Florian Lauck</td> 
                      <td
 style="vertical-align: top; width: 100px; height: 148px;" colspan="1"
 rowspan="2"><img style="width: 100px; height: 110px;" alt="Florian"
 title="Zing!" src="img/florian.jpg"><span class="body">Surprisingly, I prefer a lager to a stout.</span></td> 
                    </tr> 
                    <tr> 
                      <td
 style="vertical-align: top; width: 369px; height: 148px;"><span class="people_text">I'm working on computational methods for the prediction of protein interfaces,
particularly in order to make them available to the public.</span><br> 
                        <br> 
                        <table style="text-align: left; width: 100%;"
 border="0" cellpadding="0" cellspacing="0"> 
                          <tbody> 
                            <tr> 
                              <td style="width: 104px;"><span class="degrees">Bachelor of Science </span></td> 
                              <td style="width: 96px;"><span class="degrees">Bioinformatics </span></td> 
                              <td style="width: 160px;"><span class="degrees">Saarland University, Germany</span></td> 
                            </tr> 
                            <tr> 
                              <td style="width: 104px;"><span class="degrees">Master of Science </span></td> 
                              <td style="width: 96px;"><span class="degrees">Bioinformatics </span></td> 
                              <td style="width: 160px;"><span class="degrees">Saarland University, Germany</span></td> 
                            </tr> 
                          </tbody> 
                        </table> 
                        <br> </td> 
                    </tr> 
                  </tbody> 
                </table>-->



<!--
                <table style="text-align: left; width: 481px;" border="0"
 cellpadding="0" cellspacing="2"> 
                  <tbody> 

                    <tr> 
                      <td cellpadding="0"
 style="height: 28px; background-color: rgb(51, 102, 255); width: 369px;"><span class="name">&nbsp;Greg Kapp</td> 
                      <td
 style="height: 86px; vertical-align: top; width: 100px;" colspan="1"
 rowspan="2"><img style="width: 100px; height: 110px;" alt="Greg K."
 title="Philly Phanatic, Legomaniac" src="img/gregk.jpg"><span class="body">I have attended Major League Baseball games in 12 major league parks (9 currently active parks).</span></td> 
                    </tr> 
                    <tr> 
                      <td
 style="height: 86px; vertical-align: top; width: 369px;"><span class="people_text">I am working with our computational protein design tools to build new interfaces between cell signaling proteins. Currently I am constructing and experimentally testing the redesigned specificity between small Rho-family GTPases and their exchange factors. Eventually, we would like to reintroduce these new protein-protein interactions into living cells and use them to modulate cellular behavior.</span><br> 
                        <br> 
                        <table style="text-align: left; width: 100%;"
 border="0" cellpadding="0" cellspacing="0"> 
                          <tbody> 
                            <tr> 
                              <td><span class="degrees">Bachelor of Science, Arts</span></td> 
                              <td><span class="degrees">Biology, Chemistry</span></td> 
                              <td><span class="degrees">University of Richmond</span></td> 
                            </tr> 
                            <tr> 
                              <td style="vertical-align: top;"><span class="degrees">Ph.D.</span></td> 
                              <td style="vertical-align: top;"><span class="degrees">Biochemistry</span></td> 
                              <td style="vertical-align: top;"><span class="degrees">Duke University Medical Center<br> 
                                </span></td> 
                            </tr> 
                          </tbody> 
                        </table> 
                        <br> </td> 
                    </tr> 
                  </tbody> 
                </table> 
-->
<!--            <table style="text-align: left; width: 481px;" border="0"
 cellpadding="0" cellspacing="2"> 
                  <tbody> 
                    <tr> 
                      <td cellpadding="0"
 style="background-color: rgb(51, 102, 255); width: 369px; height: 28px;"><span class="name">&nbsp;Matt Eames</td> 
                      <td
 style="vertical-align: top; width: 100px; height: 148px;" colspan="1"
 rowspan="2"><img style="width: 100px; height: 110px;" alt="Matt"
 title="I'm the captain" src="img/matt.jpg"><span class="body">I play for keeps.</span></td> 
                    </tr> 
                    <tr> 
                      <td
 style="vertical-align: top; width: 369px; height: 148px;"><span class="people_text">
I am experimentally quantifying the effects of mutation on <br> the cost and benefit of protein expression. Using the lac operon of Escherichia coli, I specifically target residues affecting functional, translational, and folding efficiency <br> and measure their corresponding changes to fitness.
<br> 
                        <br> 
                        <table
 border="0" cellpadding="0" cellspacing="0" style="text-align: left; width: 100%;"> 
                          <tbody> 
                            <tr> 
                              <td style="width: 150px;"><span class="degrees">Bachelor of Science </span></td> 
                              <td style="width: 100px;"><span class="degrees">Physics </span></td> 
                              <td style="width: 144px;"><span class="degrees">University of Virginia</span></td> 
                            </tr> 
                            <tr valign="top"> 
                              <td style="width: 150px;"><span class="degrees">Ph.D. </span></td> 
                              <td style="width: 100px;"><span class="degrees">Biophysics </span></td> 
                              <td style="width: 144px;"><span class="degrees">Univeristy of California, San Francisco</span></td> 
                            </tr> 
                          </tbody> 
                        </table> 
                        <br> </td> 
                    </tr> 
                  </tbody> 
                </table>
-->
<!--      <table style="text-align: left; width: 481px;" border="0"
 cellpadding="0" cellspacing="2"> 
                  <tbody> 
                    <tr> 
                      <td cellpadding="0"
 style="background-color: rgb(51, 102, 255); width: 369px; height: 28px;"><span class="name">&nbsp;Dan Mandell</td> 
                      <td
 style="vertical-align: top; width: 100px; height: 148px;" colspan="1"
 rowspan="2"><img style="width: 100px; height: 110px;" alt="Dan"
 title="Stop all the downloadin'" src="img/dan.jpg"><span class="body">Well look what we got here.</span></td> 
                    </tr> 
                    <tr> 
                      <td
 style="vertical-align: top; width: 369px; height: 148px;"><span class="people_text">I have developed a procedure derived from robotic kinematics to model flexibility in proteins and protein interfaces. I am coupling this technique with computational sequence design to predict proteins with new and modified functions. On the practical side, I am applying these methods to design biosensors for small molecules, which may be therapeutics, biofuels, or other value-added chemicals.</span><br>
 <br> 
                        <table
 border="0" cellpadding="0" cellspacing="0" style="text-align: left; width: 100%;"> 
                          <tbody> 
                            <tr> 
                              <td style="width: 130px;"><span class="degrees">Bachelor of Science </span></td> 
                              <td style="width: 140px;"><span class="degrees">Symbolic Systems  </span></td> 
                              <td style="width: 144px;"><span class="degrees">Stanford University</span></td> 
                            </tr> 
              <tr> 
                              <td style="width: 130px;"><span class="degrees">Master of Science </span></td> 
                              <td style="width: 140px;"><span class="degrees">Artificial Intelligence </span></td> 
                              <td style="width: 144px;"><span class="degrees">University of Edinburgh, UK</span></td> 
                            </tr> 
                            <tr valign="top"> 
                              <td style="width: 130px;"><span class="degrees">Ph.D. </span></td> 
                              <td style="width: 100px;"><span class="degrees">Biological and Medical Informatics</span></td> 
                              <td style="width: 144px;"><span class="degrees">University of California, San Francisco</span></td> 
                            </tr> 
                          </tbody> 
                        </table> 
                        <br> </td> 
                    </tr> 
                  </tbody> 
                </table> 
-->

<!--            <table style="text-align: left; width: 481px;" border="0"
 cellpadding="0" cellspacing="2"> 
                  <tbody> 
                    <tr> 
                      <td cellpadding="0"
 style="height: 28px; background-color: rgb(51, 102, 255); width: 369px;"><span class="name">&nbsp;Sen Liu</td> 
                      <td
 style="height: 86px; vertical-align: top; width: 100px;" colspan="1"
 rowspan="2"><img style="width: 100px; height: 110px;" alt="Sen"
 title="Onward!" src="img/sen.jpg"><span class="body">Nice bridge.</span></td> 
                    </tr> 
                    <tr> 
                      <td
 style="height: 86px; vertical-align: top; width: 369px;"><span class="people_text">I am interested in the design of protein structures and functions. To do this, I will use experimental and computational approaches.  At present, I'm working on the design of orthogonal interaction pairs of the critical GTPases and their natural partners involved in cell migration.  We hope the success on these designs can be used to control cell behaviors, and used in synthetic biology studies.
</span><br> 
                        <br> 
                        <table style="text-align: left; width: 100%;"
 border="0" cellpadding="0" cellspacing="0"> 
                          <tbody> 
                            <tr> 
                              <td><span class="degrees">Bachelor of Science</span></td> 
                              <td><span class="degrees">Biotechnology</span></td> 
                              <td><span class="degrees">China Three Gorges University</span></td> 
                            </tr> 
                            <tr> 
                              <td><span class="degrees">Ph.D.</span></td> 
                              <td><span class="degrees">Physical Chemistry</span></td> 
                              <td><span class="degrees">Peking University, China</span></td> 
                            </tr> 
                          </tbody> 
                        </table> 
                        <br> </td> 
                    </tr> 
                  </tbody> 
                </table> 
-->'''
