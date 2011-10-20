import sys

COLOR_OFF = '\033[0m'
BOLD = 1
UNDERLINE = 4
FLASHING = 5
INVERTED = 7
EFFECTS_ = [BOLD, UNDERLINE, FLASHING, INVERTED] 
EMPTY_TUPLE = (None, None)

colors = {
	# [Color code, dark]
	'lightblue'		: (34, False),
	'blue'			: (34, True),
	'lightgreen'	: (32, False),
	'green'			: (32, True),
	'yellow'		: (33, False),
	'orange'		: (33, True),
	'pink'			: (31, False),
	'red'			: (31, True),
	'cyan'			: (36, False),
	'aqua'			: (36, True),
	'lightpurple'	: (35, False),
	'purple'		: (35, True),
	'grey'			: (30, False),
	'black'			: (30, True),
	'white'			: (37, False),
	'silver'		: (37, True),
}
rainbow_ = ['blue', 'green', 'yellow', 'orange', 'red', 'purple', 'lightblue']
rasta_ = ['red', 'yellow', 'green']

def write(s, color = 'white', bgcolor = 'black', suffix = "", effect = None):
	bgcolor = bgcolor or 'black' # Handier than optional arguments when using compound calls
	color = color or 'white' # Handier than optional arguments when using compound calls
	colorcode, dark = colors.get(color, EMPTY_TUPLE)
	bgcolorcode, bgdark = colors.get(bgcolor, EMPTY_TUPLE)
	if colorcode and bgcolorcode:
		if dark == (effect == BOLD):
			colorcode += 60
		if effect in EFFECTS_:
			colorcode = "%d;%s" % (effect, colorcode)
		bgcolor = bgcolor or ""
		if bgcolor:
			bgcolorcode += 10
			if not bgdark:
				bgcolorcode += 60
			bgcolor = "\033[%sm" % bgcolorcode
		sys.stdout.write('%s\033[%sm%s%s%s' % (bgcolor, colorcode, s, COLOR_OFF, suffix))
	else:
		sys.stdout.write('%s%s' % (s, suffix))

def printf(s, color = 'white', bgcolor = None, suffix = "", effect = None):
	write(s, color = color, bgcolor = bgcolor, suffix = "%s\n" % suffix, effect = effect)

def bar(bgcolor, length, suffix = None):
	str = " " * length
	write(str, bgcolor = bgcolor, suffix = suffix)
	
def error(s, suffix = "\n"):
	write(s, color = 'red', suffix = suffix)
	
def warning(s, suffix = "\n"):
	write(s, color = 'yellow', suffix = suffix)

def message(s, suffix = "\n"):
	write(s, color = 'green', suffix = suffix)

def rainbowprint(s, bgcolor = None, suffix = "\n", effect = None, rainbow = rainbow_):
	wrap = len(rainbow)
	count = 0
	for c in s:
		write(c, color = rainbow[count], bgcolor = bgcolor, effect = effect)
		count += 1
		if count >= wrap:
			count -= wrap
	write(suffix)

def rastaprint(s, bgcolor = None, suffix = "\n", effect = None):
	rainbowprint(s, bgcolor = bgcolor, suffix = suffix, effect = effect, rainbow = rasta_)

if __name__ == "__main__":
	# Test
	chars = 'A'
	count = 0
	for name, data in colors.iteritems():
		write(name, name)
		for effect in EFFECTS_:
			write(name, color = name, bgcolor = 'lightblue', effect = effect)
		print("")
	rainbowprint("Rainbow test")
	printf("\ntest1", color = 'red')
	printf("test2")
	bar('blue', 9, suffix = "\n")

