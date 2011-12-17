from string import join
import publications
import news
import people
import research
import contact 

import sys
sys.path.insert(0, "../backrub/common")
import mainpagehtml 

def indexHTML(page):
	F = open(page + ".html", 'r')
	str = F.read()
	F.close()
	return [(page, str)]

def makePage(page, d, debug = True):
	testprefix = "test-"
	for pagehtml in d["generator"](page):
		if pagehtml:
			html = []
			html.append(mainpagehtml.header % d)
			html.append(mainpagehtml.leftpane % vars())
			html.append(pagehtml[1])
			html.append(mainpagehtml.footer % d)
			if debug:
				F = open("/var/www/html/%s%s.html" % (testprefix, pagehtml[0]), "w")
			else:
				F = open("/var/www/html/%s.html" % pagehtml[0], "w")
			F.write(join(html, "\n"))
			F.close()

def main():
	websitepages = {
		'index'			: {'pagename' : 'Home',			'validation' : mainpagehtml.strict401,	'generator' : indexHTML},
		'publications'	: {'pagename' : 'Publications', 'validation' : '', 						'generator' : publications.getHTML},
		'people'		: {'pagename' : 'People',		'validation' : mainpagehtml.strict401,	'generator' : people.getHTML},
		'research'		: {'pagename' : 'Research',		'validation' : mainpagehtml.strict401,	'generator' : research.getHTML},
		'news'			: {'pagename' : 'News',			'validation' : mainpagehtml.strict401,	'generator' : news.getHTML},
		'contact'		: {'pagename' : 'Contact',		'validation' : mainpagehtml.strict401,	'generator' : contact.getHTML},
	}
	
	for p, d in websitepages.iteritems():
		makePage(p, d)

main()