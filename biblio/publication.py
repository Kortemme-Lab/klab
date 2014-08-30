#!/usr/bin/python2
# -*- coding: latin-1 -*-
"""
doi.py
A generic class to represent a publication. The other publication classes (DOI, PubMed, RIS) should inherit from this
and implement the API functions.

Created by Shane O'Connor 2014
"""

from os.path import commonprefix

publication_abbreviations = {
    #"Advances in Protein Chemistry"                      : "Adv Protein Chem",
    "ACS Chemical Biology"                                      : "ACS Chem Biol",
    "Analytical Chemistry"                                      : "Analyt Chem",
    "Aquatic Toxicology"                                        : "Aquatic Toxicol",
    "Biochemical and Biophysical Research Communications"       : "Biochem Biophys Res Comms",
    "Biochemical Journal"                                       : "Biochem J", # http://www.efm.leeds.ac.uk/~mark/ISIabbr/B_abrvjt.html
    "Biochemistry"                                              : "Biochemistry",
    "Biochimica et Biophysica Acta (BBA) - Protein Structure"   : "BBA-Protein Struct M", # this was incorporated into the journal below
    "Biochimica et Biophysica Acta (BBA) - Protein Structure and Molecular Enzymology" : "BBA-Protein Struct M",
    "Bioconjugate Chemistry"                                    : "Bioconjugate Chem",
    "Bioinformatics"                                            : "Bioinformatics",
    "Biological Chemistry"                                      : "Biol Chem", # http://www.efm.leeds.ac.uk/~mark/ISIabbr/B_abrvjt.html
    "Bioorganic & Medicinal Chemistry"                          : "Bioorg Med Chem",
    "Biophysical Chemistry"                                     : "Biophys Chem", # http://www.efm.leeds.ac.uk/~mark/ISIabbr/B_abrvjt.html
    "Biophysical Journal"                                       : "Biophys Journal",
    "Biopolymers"                                       : "Biopolymers", # http://www.efm.leeds.ac.uk/~mark/ISIabbr/B_abrvjt.html
    "BMC Evolutionary Biology"                            : "BMC Evol Biol",
    "BMC Systems Biology"                                : "BMC Sys Biol",
    "Cell"                                                : "Cell",
    "Chemistry & Biology"                                : "Chem Biol",
    "Chemical Research in Toxicology"                    : "Chem Res Toxicol",
    "Comprehensive Biophysics"                            : "Comprehensive Biophysics",
    "Current Opinion in Chemical Biology"                : "Curr Opin Chem Biol",
    "Current Opinion in Structural Biology"                : "Curr Opin Struct Biol",
    "Current Opinion in Biotechnology"                    : "Curr Opin Biotechnol",
    "EMBO Reports"                                        : "EMBO Rep",
    "Environmental and Molecular Mutagenesis"            : "Environ Mol Mutagen",
    "European Journal of Biochemistry" : "Eur J Biochem", # site:www.efm.leeds.ac.uk "European Journal of Biochemistry"
    "FEBS Journal"                                        : "FEBS Journal",
    "FEBS Letters"                                        : "FEBS Letters",
    "Folding and Design"                             : "Folding and Design", # I am unsure what the abbreviation is
    "Genome Biology"                                    : "Genome Biology",
    "Genome Research"                                    : "Genome Research",
    "Integrative and Comparative Biology"                : "Integr and Comparative Biol",
    "International Journal of Biological Macromolecules" : "Int J Biol Macromol", #http://www.efm.leeds.ac.uk/~mark/ISIabbr/I_abrvjt.html
    "Journal of Biochemistry"                           : 'J Biochem',
    "Journal of Biological Chemistry"                    : "J Biol Chem",
    "Journal of Biomedical & Laboratory Sciences"        : "J Biomed Lab Sci",
    "Journal of Biotechnology"                          : "J Biotechnol", # http://www.efm.leeds.ac.uk/~mark/ISIabbr/J_abrvjt.html
    "Journal of Chemical Information and Modeling"        : "J Chem Inf Model",
    "Journal of Computational Biology"                    : "J Comp Biol",
    # This is a book series? If so, don't abbreviate. "Methods in Enzymology"                                : "Meth Enzym",
    "Journal of Molecular Biology"                        : "J Mol Biol",
    "Journal of Protein Chemistry"                           : "J Protein Chem", # http://www.efm.leeds.ac.uk/~mark/ISIabbr/J_abrvjt.html
    "Journal of the American Chemical Society"            : "J Am Chem Soc", # http://www.efm.leeds.ac.uk/~mark/ISIabbr/J_abrvjt.html
    "Metabolomics"                                        : "Metabolomics",
    "Molecular & Cellular Proteomics"                    : "Mol Cell Proteomics",
    "Molecular Cell"                                    : "Mol Cell",
    "Molecular Systems Biology"                            : "Mol Syst Biol",
    "Nature"                                            : "Nature",
    "Nature Biotechnology"                                : "Nat Biotech",
    "Nature Chemical Biology"                             : "Nat Chem Biol",
    "Nature Methods"                                     : "Nat Methods",
    "Nature Structural & Molecular Biology"             : "Nat Struct Mol Biol",
    "Nucleic Acids Research"                            : "Nucleic Acids Res",
    "NeuroToxicology"                                    : "NeuroToxicol",
    "Physical Review E"                                    : "Phys Rev E",
    "Physical Chemistry Chemical Physics"                : "Phys Chem Chem Phys",
    "PLoS Biology"                                         : "PLoS Biol",
    "PLoS Computational Biology"                         : "PLoS Comput Biol",
    "PLoS ONE"                                            : "PLoS ONE",
    "Proceedings of the 9th International Congress of Therapeutic Drug Monitoring & Clinical Toxicology" : "Ther Drug Mon",
    "Proceedings of the National Academy of Sciences"    : "Proc Natl Acad Sci U S A",
    'Protein Engineering' : 'Protein Eng', # Renamed to PEDS (below) in 2004
    'Protein Engineering, Design and Selection' : 'Protein Eng Des Sel', # http://www.bioxbio.com/if/html/PROTEIN-ENG-DES-SEL.html
    "Protein and Peptide Letters" : "Protein Pept Lett", # http://www.efm.leeds.ac.uk/~mark/ISIabbr/P_abrvjt.html
    "Protein Science"                                    : "Protein Sci",
    "Proteins: Structure, Function, and Bioinformatics"    : "Proteins",
    "Proteomics"                                        : "Proteomics",
    "Science's STKE : signal transduction knowledge environment"        : "Sci STKE",
    "Science"                                            : "Science",
    "Spectroscopy: An International Journal"            : "Spectr Int J",
    "Structure"                                            : "Structure",
    "The EMBO Journal"                                   : "EMBO J",
    "The Journal of Physical Chemistry B"                 : "J Phys Chem B",
    "The Journal of Cell Biology"                        : "J Cell Biol",
    "The Journal of Immunology"                            : "J Immunol",
    "Proceedings of the 2009 IEEE/ACM International Conference on Computer-Aided Design (ICCAD 2009)"    : "Proceedings of the 2009 IEEE/ACM International Conference on Computer-Aided Design (ICCAD 2009)",
}

class PublicationInterface(object):

    def __init__(self): pass


    @staticmethod
    def get_author_name_in_short_format(author):
        names = []
        if author.get('FirstName'):
            names.append(author['FirstName'])
        if author.get('MiddleNames'):
            names.extend(author['MiddleNames'].split())
        initials = ''.join([n[0] for n in names])
        return "%s, %s" % (author['Surname'], initials)


    @staticmethod
    def get_page_range_in_abbreviated_format(startpage, endpage):
        if startpage and endpage:
            # Abbreviate e.g. '6026-6029' to '6026-9'.
            endpage_prefix = commonprefix([startpage, endpage])
            if len(endpage_prefix) == len(endpage):
                return startpage
            else:
                endpage = endpage[len(endpage_prefix):]
            return "%s-%s" % (startpage, endpage)
        elif startpage or endpage:
            return startpage or endpage
        else:
            return ''


    @staticmethod
    def _normalize_journal_name(j):
        return j.strip().replace(".", "").replace(",", "").replace("  ", "").lower()


    def to_dict(self): raise Exception('This function needs to be implemented by the subclasses.')
    def get_earliest_date(self): raise Exception('This function needs to be implemented by the subclasses.')
    def get_year(self): raise Exception('This function needs to be implemented by the subclasses.')
    def get_url(self): raise Exception('This function needs to be implemented by the subclasses.')
    def to_json(self):
        import json
        return json.dumps(self.to_dict())

    def to_string(self, abbreviate_journal = True, html = False, add_url = False):
        d = self.to_dict()

        author_str = ', '.join([PublicationInterface.get_author_name_in_short_format(author) for author in d['authors']])
        #    author_str.append(('%s %s' % (author.get('Surname'), initials or '').strip()))
        #author_str = (', '.join(author_str))
        if html and author_str:
            author_str = '<span class="publication_authors">%s.</span>' % author_str

        title_str = d.get('Title', '')
        if title_str:
            if add_url:
                title_str = '<a href="%s" target="_blank">%s</a>' % (self.get_url(), title_str)
        if title_str:
            if html:
                if d['RecordType'] == "Book":
                    title_str = '<span class="publication_title">%s</span> <span>in</span>' % title_str
                else:
                    title_str = '<span class="publication_title">%s.</span>' % title_str
            else:
                if d['RecordType'] == "Book":
                    title_str += ' in'

        issue_str = ''
        if d.get('PublicationName'):
            if abbreviate_journal and d['RecordType'] == "Journal":
                issue_str += publication_abbreviations.get(PublicationInterface._normalize_journal_name(d['PublicationName']), d['PublicationName'])
            else:
                issue_str += d['PublicationName']
            if d.get('Volume'):
                if d.get('Issue'):
                    issue_str += ' %(Volume)s(%(Issue)s)' % d
                else:
                    issue_str += ' %(Volume)s' % d
                page_string = PublicationInterface.get_page_range_in_abbreviated_format(d.get('StartPage'), d.get('EndPage'))
                if page_string:
                    issue_str += ':%s' % page_string
        if html and issue_str:
            issue_str = '<span class="publication_issue">%s.</span>' % issue_str

        if title_str and issue_str:
            if html or d['RecordType'] == "Book":
                article_str = '%s %s' % (title_str, issue_str)
            else:
                article_str = '%s. %s' % (title_str, issue_str)

        earliest_date = self.get_earliest_date()
        if earliest_date:
            article_date = earliest_date
        else:
            article_date = self.get_year()
        if html and article_date:
            article_date = '<span class="publication_date">%s.</span>' % article_date

        s = None
        if html:
            s = ' '.join([c for c in [author_str, title_str, issue_str, article_date] if c])
        else:
            s = '. '.join([c for c in [author_str, title_str, issue_str, article_date] if c])
            if s:
                s = s + '.'
        return s
