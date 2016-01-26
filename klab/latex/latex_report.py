#!/usr/bin/env python2

# The MIT License (MIT)
#
# Copyright (c) 2015 Kyle Barlow
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import sys
import os
import time
import getpass
import tempfile
import subprocess
import shutil
from klab.latex.util import make_latex_safe

cwd = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(cwd, 'document_header.tex'), 'r') as f:
    document_header = f.read()

class LatexReport:
    def __init__(self, latex_template_file = None, table_of_contents = False, number_compilations = 3):
        self.latex_template_file = latex_template_file
        self.number_compilations = int( number_compilations )

        self.title_page_title = None
        self.title_page_subtitle = None
        self.abstract_text = None

        self.latex = None

        self.content = []

        self.table_of_contents = table_of_contents

    def set_title_page(self, title = '', subtitle = ''):
        self.title_page_title = make_latex_safe(title)
        self.title_page_subtitle = make_latex_safe(subtitle)

    def set_abstract(self, abstract_text):
        self.abstract_text = make_latex_safe(abstract_text)

    def add_section_page(self, title = '', subtext = None, clearpage = True):
        self.content.append(
            LatexPageSection(title, subtext, clearpage)
        )

    def add_plot(self, plot_filename, plot_title = None):
        self.content.append(
            LatexPagePlot(plot_filename, plot_title)
        )

    def generate_latex(self):
        latex_strings = [document_header]
        make_title_page = False
        if self.title_page_title != None and self.title_page_title != '':
            latex_strings.append( '\\title{%s}' % self.title_page_title )
            make_title_page = True
        if self.title_page_subtitle != None and self.title_page_subtitle != '':
            latex_strings.append( '\\subtitle{%s}' % self.title_page_subtitle )
            make_title_page = True
        if make_title_page:
            latex_strings.append('\\date{\\today}')
            latex_strings.append('\\begin{document}\n\\maketitle')

        if self.table_of_contents:
            latex_strings.append('\\tableofcontents')

        for content_obj in self.content:
            latex_strings.append( content_obj.generate_latex() )

        latex_strings.append( '\\end{document}' )

        self.latex = ''
        for s in latex_strings:
            if s.endswith('\n'):
                self.latex += s
            else:
                self.latex += s + '\n'

    def generate_pdf_report(self, report_filepath):
        self.generate_latex()
        out_dir = tempfile.mkdtemp( prefix = '%s-%s-tmp-latex_' % (time.strftime("%y%m%d"), getpass.getuser()) )
        tmp_latex_file = os.path.join(out_dir, 'report.tex')
        with open(tmp_latex_file, 'w') as f:
            f.write(self.latex)
        for x in xrange(self.number_compilations):
            latex_output = subprocess.check_output( ['pdflatex', 'report.tex'], cwd = out_dir )
        tmp_latex_pdf = os.path.join(out_dir, 'report.pdf')
        assert( os.path.isfile(tmp_latex_pdf) )
        shutil.copy( tmp_latex_pdf, report_filepath )
        shutil.rmtree(out_dir)

class LatexPage:
    pass

class LatexPageSection(LatexPage):
    def __init__(self, title, subtext, clearpage):
        self.title = make_latex_safe(title)
        self.clearpage = clearpage
        if subtext:
            self.subtext = make_latex_safe(subtext)
        else:
            self.subtext = None

    def generate_latex(self):
        return_str = '\\section{%s}' % self.title
        if self.subtext:
            return_str += '\n\\textit{%s}\n' % self.subtext
        return_str += '\n'
        if self.clearpage:
            return_str += '\\clearpage'
        return return_str

class LatexPagePlot(LatexPage):
    def __init__(self, plot_filename, plot_title):
        plot_filename = os.path.abspath( plot_filename )
        if not os.path.isfile( plot_filename ):
            print
            print plot_filename
            raise Exception('Above plot filename is not a file!')
        self.plot_filename = plot_filename
        if plot_title:
            self.plot_title = make_latex_safe(plot_title)
        else:
            self.plot_title = ''

    def generate_latex(self):
        return_str = '\\begin{figure}[H]'
        return_str += '  \\includegraphics[width=\\textwidth]{{%s}%s}' % (os.path.splitext(self.plot_filename)[0], os.path.splitext(self.plot_filename)[1])
        if self.plot_title != '':
            return_str += '  \\caption{%s}' % self.plot_title
        return_str += '\\end{figure}'
        return return_str
