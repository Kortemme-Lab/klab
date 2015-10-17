import os
from string import join
import process
import deprecated.rosettahelper as rosettahelper


def breakCommandLine(commandLine, length = 80):
	commandLine = commandLine.replace("%(", "[").replace(")s", "]").replace(")d", "]").replace('{', '(').replace('}', ')')
	tokens = commandLine.split(" ")
	commandLine = []
	currentLine = ''
	for token in tokens:
		if len(currentLine) + len(token) > length:
			commandLine.append(currentLine)
			currentLine = token
		else:
			currentLine += ' %s' % token
	commandLine.append(currentLine)
	commandLine = join(commandLine, "\n")
	return commandLine

class LaTeXDocument(object):
	
	alignments = set(['l', 'c', 'r'])
		
	def __init__(self, document_title, pdf_title = None):
		if not pdf_title:
			pdf_title = document_title
			
		self.quiet = False
		self.outdir = "."
		self.latex = []
		self.latex.append('''
\\documentclass[a4paper,10pt]{article}

\\makeatletter
\\renewcommand\\paragraph{\\@startsection{paragraph}{4}{\\z@}%%
  {-3.25ex\\@plus -1ex \\@minus -.2ex}%%
  {1.5ex \\@plus .2ex}%%
  {\\normalfont\\normalsize\\bfseries}}
\\makeatother

%%\\usepackage{a4wide} - a4wide is a deprecated package
\\usepackage[utf8]{inputenc}
\\usepackage[small,bf]{caption}
\\usepackage{times}
\\usepackage{amsmath,amsthm,amsfonts}
\\usepackage{graphicx}
\\usepackage{rotating}
\\usepackage[usenames,dvipsnames]{color}
\\usepackage{textcomp}
\\definecolor{deepblue}{rgb}{0,0,0.6}
\\usepackage[pdfpagemode=UseNone,pdfstartview=FitH,colorlinks=true,linkcolor=deepblue,urlcolor=deepblue,citecolor=black,pdftitle=%(pdf_title)s]{hyperref} %%for ideal pdf layout and hyperref
\\usepackage{booktabs}
\\usepackage{colortbl}
\\usepackage{multirow}
\\usepackage{listings}
\\usepackage[round]{natbib}
\\bibliographystyle{apalike}
\\renewcommand{\\thefootnote}{\\fnsymbol{footnote}}
\\begin{document}
\\setcounter{page}{1}
\\setcounter{footnote}{0}
\\renewcommand{\\thefootnote}{\\arabic{footnote}}

\\begin{center}
{\\huge %(document_title)s}\\\\[0.5cm]
\\today
\\end{center}''' % vars())

	def save(self, filepath):
		rosettahelper.writeFile(filepath, self.getLaTeXCode())
	
	def log(self, *msg):
		if self.quiet:
			return
		if len(msg) == 1:
			print(msg[0])
		else:
			print(msg)
		print("")
		
	def popen(self, arglist, logstdout = False, logstderr = False):
		processOutput = process.Popen(self.outdir, arglist)
		
		if logstdout:
			self.log("STDOUT START")
			self.log(processOutput.stdout)
			self.log("STDOUT END")
		if logstderr:
			self.log("STDERR START")
			self.log(processOutput.stderr)
			self.log("STDERR END")
		error = processOutput.getError()
		if error:
			raise Exception(error)

	def checkFileExists(self, filename):
		if not os.path.exists(os.path.join(self.outdir, filename)):
			raise Exception("%s does not exist." % filename)

	def compile(self, report_filename):
		prefix = os.path.splitext(report_filename)[0]
		
		latex_filename = "%s.tex" % prefix
		dvi_filename = "%s.dvi" % prefix
		ps_filename = "%s.ps" % prefix
		pdf_filename = "%s.pdf" % prefix
		out_filename = "%s.out" % prefix
		aux_filename = "%s.aux" % prefix
		log_filename = "%s.log" % prefix
		
		rosettahelper.writeFile(latex_filename, self.getLaTeXCode())
		
		for i in range(3):
			self.popen(['latex', '-output-directory', self.outdir, latex_filename], logstdout = True, logstderr = True)
			self.checkFileExists(dvi_filename)
		os.remove(latex_filename)
			
		self.popen(['dvips', '-Ppdf', dvi_filename], logstdout = True, logstderr = True)
		self.checkFileExists(ps_filename)
		os.remove(dvi_filename)
			
		self.popen(['ps2pdf', ps_filename])
		self.checkFileExists(pdf_filename)
		os.remove(ps_filename)
			
		self.PDFReport = rosettahelper.readFile(report_filename)
		self.log('Report saved as %s.' % report_filename)
		
		os.remove(out_filename)
		os.remove(aux_filename)
		os.remove(log_filename)
	
	def compile_pdf(self, report_filename):
		prefix = os.path.splitext(report_filename)[0]
		
		latex_filename = "%s.tex" % prefix
		pdf_filename = "%s.pdf" % prefix
		out_filename = "%s.out" % prefix
		aux_filename = "%s.aux" % prefix
		log_filename = "%s.log" % prefix
		
		rosettahelper.writeFile(latex_filename, self.getLaTeXCode())
		
		for i in range(3):
			self.popen(['pdflatex', '-output-directory', self.outdir, latex_filename], logstdout = False, logstderr = False)
			self.checkFileExists(pdf_filename)
		os.remove(latex_filename)
			
		self.PDFReport = rosettahelper.readFile(report_filename)
		self.log('Report saved as %s.' % report_filename)
		
		os.remove(out_filename)
		os.remove(aux_filename)
		os.remove(log_filename)
		
	def getLaTeXCode(self):
		return join(self.latex + ['''\\end{document}'''], "\n")

	def addSection(self, section_name):
		self.latex.append('''\\section{%(section_name)s}''' % vars()) 
	
	def addSubsection(self, subsection_name):
		self.latex.append('''\\subsection{%(subsection_name)s}''' % vars()) 
	
	def startCenter(self):
		self.latex.append('''\\begin{center}''')

	def endCenter(self):
		self.latex.append('''\\end{center}''')
	
	def clearPage(self):
		self.latex.append('''\\clearpage''')
		
	def addLaTeXCode(self, code):
		self.latex.append(code)

	def getImageText(self, filename, width_cm = None): 
		if width_cm:
			return '''\\includegraphics[width=%(width_cm)dcm]{%(filename)s}''' % vars()
		else:
			return '''\\includegraphics{%(filename)s}''' % vars()

	def getFigureWrappingImageText(self, filename, title, width_cm = None): 
		s = []
		if width_cm:
			return '''\\begin{figure}[h] \\caption{%(title)s} \\includegraphics[width=%(width_cm)dcm]{%(filename)s} \\end{figure}''' % vars()
		else:
			return '''\\begin{figure}[h] \\caption{%(title)s} \\includegraphics{%(filename)s} \\end{figure}''' % vars()

	def addImage(self, filename, width_cm = None):
		self.latex.append(getImageText(filename, width_cm = width_cm)) 

	def addParagraph(self, title):
		self.latex.append('''\\paragraph{%(title)s}''' % vars())
	
	def addTabular(self, table, alignment = 'l'):
		
		assert(alignment in LaTeXDocument.alignments)
		
		num_rows = len(table)
		num_cols = 0
		for i in range(num_rows):
			num_cols = max(num_cols, len(table[i]))
		
		self.latex.append('''\\begin{tabular}{%s}''' % (alignment * num_cols))
		
		for j in range(num_rows):
			row_latex = []
			for k in range(num_cols):
				if k >= len(table[j]):
					row_latex.append(" & " * (num_cols - len(table[j]) - 1))
					break
				else:
					row_latex.append(table[j][k])
			row_latex = "%s\\\\" % join(row_latex, " & ")
			self.latex.append(row_latex)
			
		self.latex.append('''\\end{tabular}''')
	
	def addTable(self, table, first_row_as_headers = True, scalebox = None):
		self.latex.append('''\\begin{table}[ht]''')
		if scalebox:
			self.latex.append('''\\scalebox{0.9}{''')

		if first_row_as_headers:
			pass

		if scalebox:
			self.latex.append('''}''')
		self.latex.append('''\\end{table}''')
			
	def addTypewriterText(self, code, language = None, fontsize = None):
		#code = breakCommandLine(code)
		if fontsize or True:
			self.latex.append('''\\lstset{basicstyle=\\tiny}''')
		if language:
			self.latex.append('''\\begin{lstlisting}[language=%(language)s]''' % vars())
		else:
			self.latex.append('''\\begin{lstlisting}''')
		self.latex.append('''
%(code)s
\\end{lstlisting}''' % vars())
		
	def addImageGrid(self, image_array, num_rows, num_cols):
		num_images = len(image_array)
		if True or len(image_array) > (num_rows * num_cols):
			raise Exception("The size of the array exceeds the specified grid dimensions %d x %d." % (num_rows, num_cols))
		self.latex.append('''
\\begin{figure}
\\resizebox{\\textwidth}{!}{
\\begin{tabular}{%s}''' % ('c' * num_cols))
			#-
		for j in range(num_rows):
			row_latex = []
			for k in range(num_cols):
				image_index = (num_cols * j) + k
				if image_index >= num_images:
					break
				row_latex.append('''\\includegraphics{%s}''' % image_array[image_index])
			row_latex = "%s\\\\" % join(row_latex, " & ")
			self.latex.append(row_latex)
		#-	
		self.latex.append('''
\\end{tabular}
}\\end{figure}''')


class LaTeXCodePrinter(LaTeXDocument):
	'''Useful to create PDFs for printing source code since Linux generally sucks at this. Example of usage:

    code = """
// blah blah blah
"""
    codeprinter = latex.LaTeXCodePrinter('my\_stuff', code)
    codeprinter.compile_pdf("codetest.pdf")

    '''

	header = '''
\\documentclass[a4paper,10pt]{article}

\usepackage[margin=0.5in]{geometry}
\\usepackage{color}
\\usepackage{xcolor,listings}
\\lstset{ %
language=C++,                % choose the language of the code
basicstyle=\\footnotesize,       % the size of the fonts that are used for the code
numbers=left,                   % where to put the line-numbers
numberstyle=\\footnotesize,      % the size of the fonts that are used for the line-numbers
stepnumber=1,                   % the step between two line-numbers. If it is 1 each line will be numbered
numbersep=5pt,                  % how far the line-numbers are from the code
backgroundcolor=\\color{white},  % choose the background color. You must add \\usepackage{color}
showspaces=false,               % show spaces adding particular underscores
showstringspaces=false,         % underline spaces within strings
showtabs=false,                 % show tabs within strings adding particular underscores
frame=none,           % adds a frame around the code. Some valid values are 'single', 'none'
tabsize=2,          % sets default tabsize to 2 spaces
captionpos=b,           % sets the caption-position to bottom
breaklines=true,        % sets automatic line breaking
breakatwhitespace=false,    % sets if automatic breaks should only happen at whitespace
keywordstyle=\\color{blue}\\bfseries,
commentstyle=\\color{green},
stringstyle=\\ttfamily\color{red!50!brown},
escapeinside={\\%*}{*)}          % if you want to add a comment within your code
}

\\begin{document}

\\setcounter{page}{1}
\\setcounter{footnote}{0}
\\renewcommand{\\thefootnote}{\\arabic{footnote}}
'''
	title = '''
\\begin{center}
{\\huge %(document_title)s}\\\\[0.5cm]
\\today
\\end{center}

\\begin{lstlisting}
'''

	footer = '''
\\end{lstlisting}
\\end{document}
'''

	def __init__(self, document_title, code, pdf_title = None):
		if not pdf_title:
			pdf_title = document_title
		self.quiet = False
		self.outdir = "."
		self.code = code
		self.document_title = document_title

	def getLaTeXCode(self):
		return LaTeXCodePrinter.header + (LaTeXCodePrinter.title % self.__dict__) + self.code + LaTeXCodePrinter.footer

	def compile_pdf(self, report_filename):
		prefix = os.path.splitext(report_filename)[0]

		latex_filename = "%s.tex" % prefix
		pdf_filename = "%s.pdf" % prefix
		out_filename = "%s.out" % prefix
		aux_filename = "%s.aux" % prefix
		log_filename = "%s.log" % prefix

		rosettahelper.writeFile(latex_filename, self.getLaTeXCode())

		for i in range(3):
			self.popen(['pdflatex', '-output-directory', self.outdir, latex_filename], logstdout = False, logstderr = False)
			self.checkFileExists(pdf_filename)
		os.remove(latex_filename)

		self.PDFReport = rosettahelper.readFile(report_filename)
		self.log('Report saved as %s.' % report_filename)

		os.remove(out_filename)
		os.remove(aux_filename)
		os.remove(log_filename)
