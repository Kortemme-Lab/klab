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
import copy
from klab.latex.util import make_latex_safe
import numpy as np

cwd = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(cwd, 'document_header.tex'), 'r') as f:
    document_header = f.read()
with open(os.path.join(cwd, 'html_document_header.tex'), 'r') as f:
    html_document_header = f.read()

class LatexReport:
    def __init__(self, latex_template_file = None, table_of_contents = True, number_compilations = 3):
        self.latex_template_file = latex_template_file
        self.number_compilations = int( number_compilations )

        self.title_page_title = None
        self.title_page_subtitle = None
        self.abstract_text = []

        self.latex = None

        self.content = []

        self.chapters = []

        self.table_of_contents = table_of_contents

    def set_title_page(self, title = '', subtitle = ''):
        if title != '':
            self.title_page_title = make_latex_safe(title)
        if subtitle != '':
            self.title_page_subtitle = make_latex_safe(subtitle)

    def add_to_abstract(self, abstract_text):
        self.abstract_text.append( make_latex_safe(abstract_text) )

    def extend_abstract(self, abstract_lines):
        self.abstract_text.extend( abstract_lines )

    def add_section_page(self, title = '', subtext = None, clearpage = True):
        self.content.append(
            LatexPageSection(title, subtext, clearpage)
        )

    def add_plot(self, plot_filename, plot_title = None):
        self.content.append(
            LatexPagePlot(plot_filename, plot_title)
        )

    def add_chapter(self, chapter):
        self.chapters.append(chapter)

    def set_latex_from_strings(self, latex_strings):
        self.latex = ''
        for s in latex_strings:
            if s.endswith('\n'):
                self.latex += s
            else:
                self.latex += s + '\n'

    def generate_latex_chapter(self):
        latex_strings = []
        latex_strings.append( '\\chapter{%s}\n\n\\clearpage\n\n' % self.title_page_title )
        if self.title_page_subtitle != '' and self.title_page_subtitle != None:
            latex_strings.append( '\\textbf{%s}\n\n' % self.title_page_subtitle)
        # if self.table_of_contents:
        #     latex_strings.append( '\\minitoc\n\n' )
        if len( self.abstract_text ) > 0:
            latex_strings.extend( self.generate_abstract_lines() )

        for content_obj in self.content:
            latex_strings.append( content_obj.generate_latex() )

        self.set_latex_from_strings( latex_strings )

        return self.latex

    def generate_latex(self, output_type='pdf'):
        if output_type == 'pdf':
            latex_strings = [document_header]
        elif output_type == 'html':
            latex_strings = [html_document_header]

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
        else:
            latex_strings.append('\\begin{document}\n')

        if self.table_of_contents:
            latex_strings.append('\\tableofcontents\n\n\\clearpage\n\n')

        if len( self.abstract_text ) > 0:
            latex_strings.append('\\begin{abstract}\n')
            latex_strings.extend( self.generate_abstract_lines() )
            latex_strings.append('\\end{abstract}\n\n')

        for content_obj in self.content:
            latex_strings.append( content_obj.generate_latex() )

        for chapter_obj in self.chapters:
            latex_strings.append( chapter_obj.generate_latex_chapter() )

        latex_strings.append( '\\end{document}' )

        self.set_latex_from_strings( latex_strings )

        return self.latex

    def generate_abstract_lines(self):
        latex_strings = []
        if len( self.abstract_text ) > 0:
            for abstract_text_paragraph in self.abstract_text:
                latex_strings.append( abstract_text_paragraph + '\n\n' )
        return latex_strings

    def generate_pdf_report(self, report_filepath, copy_tex_file_dir = True, verbose = True, compile_pdf = True):
        self.generate_latex( output_type = 'pdf' )
        out_dir = tempfile.mkdtemp( prefix = '%s-%s-tmp-latex-pdf_' % (time.strftime("%y%m%d"), getpass.getuser()) )
        if verbose:
            print 'Outputting latex files to temporary directory:', out_dir

        tmp_latex_file = os.path.join(out_dir, 'report.tex')
        with open(tmp_latex_file, 'w') as f:
            f.write(self.latex)
        if compile_pdf:
            for x in xrange(self.number_compilations):
                latex_output = subprocess.check_output( ['pdflatex', 'report.tex'], cwd = out_dir )
            tmp_latex_pdf = os.path.join(out_dir, 'report.pdf')
            assert( os.path.isfile(tmp_latex_pdf) )
            shutil.copy( tmp_latex_pdf, report_filepath )

        if copy_tex_file_dir:
            shutil.copytree(
                out_dir,
                os.path.join(os.path.dirname(report_filepath), 'latex_files')
            )
        shutil.rmtree(out_dir)

    def generate_html_report(self, report_filepath):
        self.generate_latex( output_type = 'html' )
        out_dir = tempfile.mkdtemp( prefix = '%s-%s-tmp-latex-html_' % (time.strftime("%y%m%d"), getpass.getuser()) )
        tmp_latex_file = os.path.join(out_dir, 'report.tex')
        with open(tmp_latex_file, 'w') as f:
            f.write(self.latex)
        for x in xrange(self.number_compilations):
            latex_output = subprocess.check_output( ['htlatex', 'report.tex'], cwd = out_dir )
        raise Exception("Output files not yet copied from: " + out_dir)
        shutil.rmtree(out_dir)

    def generate_plaintext(self):
        # Returns saved information as plaintext string
        return_strings = []
        if len( self.abstract_text ) > 0:
            return_strings.append('Abstract:\n')
            for abstract_text_paragraph in self.abstract_text:
                return_strings.append( abstract_text_paragraph + '\n\n' )

        for content_obj in self.content:
            latex_strings.append( content_obj.generate_plaintext() )

        return_str = ''
        for return_string in return_strings:
            if return_string.endswith('\n'):
                return_str += return_string
            else:
                return_str += return_string + '\n'

        return return_str

class LatexPage(object):
    def generate_plaintext(self):
        return ''

class LatexPageSection(LatexPage):
    def __init__(self, title, subtext = None, clearpage = True):
        self.title = make_latex_safe(title)
        self.clearpage = clearpage
        if subtext:
            self.subtext = make_latex_safe(subtext)
        else:
            self.subtext = None
        self.section_latex_func = 'section'

    def generate_latex(self):
        return_str = ''
        if self.clearpage:
            return_str += '\n\\clearpage\n\n'
        return_str += '\\%s{%s}\n' % (self.section_latex_func, self.title)
        if self.subtext:
            return_str += '\\textit{%s}\n' % self.subtext
        return_str += '\n'
        return return_str

    def generate_plaintext(self):
        return_str = ''
        if self.clearpage:
            return_str += '\n\n'
        return_str += '\n\n%s %s\n\n' % (self.section_latex_func.upper(), self.title)
        if self.subtext:
            return_str = return_str[:-1] + '%s' % self.subtext
        return_str += '\n\n'
        return return_str

class LatexSubSection(LatexPageSection):
    def __init__(self, title, subtext = None, clearpage = False):
        super(LatexSubSection, self).__init__(title, subtext, clearpage)
        self.section_latex_func = 'subsection'

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
        return_str = '\\begin{figure}[H]\n'
        return_str += '  \\includegraphics[width=\\textwidth]{{%s}%s}\n' % (os.path.splitext(self.plot_filename)[0], os.path.splitext(self.plot_filename)[1])
        if self.plot_title != '':
            return_str += '  \\caption{%s}\n' % self.plot_title
        return_str += '\\end{figure}\n'
        return return_str

class LatexText(LatexPage):
    # Each "text" object will be turned into a paragraph
    def __init__ (self, text, color = None):
        self.text = []
        self.color = color
        if text:
            self.add_text(text)

    def add_text(self, text):
        self.text.append( make_latex_safe(text.strip()) )

    def generate_latex(self):
        if self.color:
            return_str = '{\\color{%s} ' % self.color
        else:
            return_str = ''

        return_str += self.generate_plaintext()

        if self.color:
            return_str += '}'
        return return_str

    def generate_plaintext(self):
        return_str = ''
        if len(self.text) > 1:
            for text in self.text[:-1]:
                return_str += text + '\n\n'
        return_str += self.text[-1] + '\n'
        return return_str

class LatexTable(LatexPage):
    def __init__ (self, header_row, data_rows, header_text = None, column_format = None):
        self.num_columns = len(header_row)
        for data_row in data_rows:
            if self.num_columns != len(data_row):
                print 'Header row:', header_row
                print 'Data row:', data_row
                raise Exception('This data row has a different number of columns than the header row')

        self.set_column_format(column_format)

        self.header_row = [make_latex_safe( x.strip() ) for x in header_row]
        self.data_rows = [[make_latex_safe( x.strip() ) for x in data_row] for data_row in data_rows]
        if header_text:
            self.header_text = make_latex_safe( header_text.strip() )
        else:
            self.header_text = None

    def set_column_format(self, column_format):
        self.column_format = column_format
        if column_format:
            assert( len(column_format) == self.num_columns )

    def generate_latex(self):
        if self.column_format:
            column_format = ' '.join( self.column_format )
        else:
            column_format = ( 'c ' * self.num_columns )

        return_str = '\n\n'
        return_str += '\\begin{table}[H]\\begin{center}\n'
        return_str += '\\begin{tabular}{ %s}\n' % column_format
        return_str += self.row_to_latex_row(self.header_row)
        return_str += '\\hline\n'
        for row in self.data_rows:
            return_str += self.row_to_latex_row(row)
        return_str += '\\end{tabular}\n'
        if self.header_text:
            return_str += '\\caption{%s}\n' % self.header_text
        return_str += '\\end{center}\\end{table}\n\n\n'
        return return_str

    def generate_plaintext(self):
        l = copy.deepcopy(self.data_rows)
        l.insert(0, self.header_row)
        return format_list_table(l)

    def row_to_latex_row(self, row):
        return_str = ''
        if len(row) > 1:
            for x in row[:-1]:
                return_str += '%s & ' % str(x)
        if len(row) > 0:
            return_str += '%s' % str(row[-1])
        return_str += '\\\\\n'
        return return_str


class LatexPandasTable(LatexTable):
    def __init__ (self, df, caption_text = None, header = True, float_format = None, sparsify = True):
        self.df = df
        if caption_text:
            self.caption_text = make_latex_safe( caption_text )
        else:
            self.caption_text = caption_text
        self.header = header
        self.float_format = float_format
        self.sparsify = sparsify

    def generate_latex(self):
        latex = '\\begin{table}[H]\n'
        latex += self.df.to_latex( header = self.header, float_format = self.float_format, sparsify = self.sparsify )
        if self.caption_text:
            latex += '\\caption{%s}\n' % str(self.caption_text)
        latex += '\\end{table}\n'
        return latex

def format_list_table(data):
    max_lengths = []
    strings_to_print = []
    for i, l in enumerate(data):
        strings_to_print.append([])
        for j, s in enumerate(l):
            s = str(s)
            strings_to_print[i].append(s)
            s_len = len(s)
            while len(max_lengths) < j+1:
                max_lengths.append(0)
            if s_len > max_lengths[j]:
                max_lengths[j] = s_len

    return_str = ''
    for row in strings_to_print:
        row_str = ''
        for i, x in enumerate(row):
            if i >= len(row) - 2:
                row_str += '%s\t' % x.ljust(max_lengths[i])
            else:
                row_str += '%s\t' % x.rjust(max_lengths[i])

        return_str += row_str[:-1] + '\n' # Remove trailing space
    return return_str
