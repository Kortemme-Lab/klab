#!/usr/bin/python2
# -*- coding: latin-1 -*-
"""
ris.py
RIS (ReferenceManager) parsing functions.
This pulls together some code I wrote for the Gen9 project and our lab website code into a more generally useful package.

Created by Shane O'Connor 2013
"""
import sys
import re
if __name__ == '__main__':
    sys.path.insert(0, '../..')
import datetime
import traceback
import urllib2

from publication import PublicationInterface, publication_abbreviations
from klab import colortext

lsttype = type([])
strtype = type("")
unicode_type = type(u"")
doi_regex = re.compile('10.\d+/.+')

taglist = [
    u'TY',#  - Type of reference (must be the first tag)
    u'A2',#  - Secondary Author (each author on its own line preceded by the tag)
    u'A3',#  - Tertiary Author (each author on its own line preceded by the tag)
    u'A4',#  - Subsidiary Author (each author on its own line preceded by the tag)
    u'AB',#  - Abstract
    u'AD',#  - Author Address
    u'AN',#  - Accession Number
    u'AU',#  - Author (each author on its own line preceded by the tag)
    u'C1',#  - Custom 1
    u'C2',#  - Custom 2
    u'C3',#  - Custom 3
    u'C4',#  - Custom 4
    u'C5',#  - Custom 5
    u'C6',#  - Custom 6
    u'C7',#  - Custom 7
    u'C8',#  - Custom 8
    u'CA',#  - Caption
    u'CN',#  - Call Number
    u'CY',#  - Place Published
    u'DA',#  - Date
    u'DB',#  - Name of Database
    u'DO',#  - DOI
    u'DP',#  - Database Provider
    u'EP',#  - End Page
    u'ET',#  - Edition
    u'IS',#  - Number
    u'JO',#  - Journal name
    u'J2',#  - Alternate Title (this field is used for the abbreviated title of a book or journal name)
    u'KW',#  - Keywords (keywords should be entered each on its own line preceded by the tag)
    u'L1',#  - File Attachments (this is a link to a local file on the users system not a URL link)
    u'L4',#  - Figure (this is also meant to be a link to a local file on the users's system and not a URL link)
    u'LA',#  - Language
    u'LB',#  - Label
    u'M1',#  - Number
    u'M3',#  - Type of Work
    u'N1',#  - Notes
    u'N2',#  - Abstract
    u'NV',#  - Number of Volumes
    u'OP',#  - Original Publication
    u'PB',#  - Publisher
    u'PY',#  - Year
    u'RI',#  - Reviewed Item
    u'RN',#  - Research Notes
    u'RP',#  - Reprint Edition
    u'SE',#  - Section
    u'SN',#  - ISBN/ISSN
    u'SP',#  - Start Page
    u'ST',#  - Short Title
    u'T2',#  - Secondary Title
    u'T3',#  - Tertiary Title
    u'TA',#  - Translated Author
    u'TI',#  - Title
    u'TT',#  - Translated Title
    u'UR',#  - URL
    u'VL',#  - Volume
    u'Y2',#  - Access Date
    u'BT',#  - Title Primary.
    u'ER',#  - End of Reference (must be the last tag)
     #
    u'VO', # - Volume?
    u'ID', # Seems to be doi
    u'L3', # Link?
    u'J1', # ?
    # Seemingly non-canonical tags
    u'T1', # Misspelling of TI
    u'A1', # Used for authors
    u'Y1', # Used for date
    u'JF', # Used for journal
    u'JA', # Used for journal
    # Canonical?
    u'U1', # Used custom field results
    u'U2', # Used custom field results
    u'U3', # Used custom field results
    u'U4', # Used custom field results
    u'U5', # Used custom field results
]

tag_map = {
    u'AU' : 'authors',
    u'A1' : 'authors',
    u'TY' : 'publication_type',
    u'T1' : 'title',
    u'TI' : 'title',
    u'T2' : 'subtitle',
    u'JO' : 'journal',
    u'JA' : 'journal',
    u'J2' : 'journal',
    u'JF' : 'journal',
    u'VL' : 'volume',
    u'IS' : 'issue',
    u'Y1' : 'date',
    u'PY' : 'date',
    u'M3' : 'doi',
    u'UR' : 'url',
    u'SP' : 'startpage',
    u'EP' : 'endpage',
}


class RISEntry(PublicationInterface):

    record_types = {
        'JOUR' : 'Journal',
        'JFULL' : 'Journal',
        'EJOUR' : 'Journal',
        'CHAP' : 'Book',
        'BOOK' : 'Book',
        'EBOOK' : 'Book',
        'ECHAP' : 'Book',
        'EDBOOK' : 'Book',
        'CONF' : 'Conference',
        'CPAPER' : 'Conference',
        'THES' : 'Dissertation',
        'RPRT' : 'Report',
        'STAND' : 'Standard',
        'DBASE' : 'Database',
    }

    def __init__(self, RIS, quiet = True, lenient_on_tag_order = False):
        if type(RIS) != unicode_type:
            raise Exception("RIS records should always be passed as unicode.")

        self.RIS = RIS
        self.quiet = quiet

        # Setting member elements explicitly here so that developers can see which variable are expected to be set after parsing
        self.publication_type = None
        self.authors = []
        self.ReferralURL = None
        self.title = None
        self.subtitle = None
        self.journal = None
        self.volume = None
        self.issue = None
        self.startpage = None
        self.endpage = None
        self.date = None
        self.year = None
        self.doi = None
        self.url = None
        self.errors, self.warnings = self.parse(lenient_on_tag_order = lenient_on_tag_order)


    def parse(self, lenient_on_tag_order = False):
        errors = []
        warnings = []
        d = {}
        for v in tag_map.values():
            d[v] = []

        RIS = self.RIS
        lines = [l.strip() for l in RIS.split("\n") if l.strip()]

        # Check the first entry
        if not lenient_on_tag_order:
            if lines[0][0:5] != 'TY  -':
                raise Exception("Bad RIS record. Expected a TY entry as the first entry, received '%s' instead." % lines[0])
            if lines[-1][0:5] != 'ER  -':
                raise Exception("Bad RIS record. Expected an ER entry as the last entry, received '%s' instead." % lines[-1])

        # Parse the record
        tag_data = {}
        for line in lines:
            tag_type = line[0:2]

            if not tag_type in taglist:
                # Note: I removed 'elif key == "DOI": key = "M3"' from the old code - this may be required here if this is something I added to the RIS records (it breaks the RIS format)
                raise Exception(u"Unrecognized bibliography tag '%s'." % tag_type)
            if not (line[2:5] == '  -'): # there should be a space at position 5 as well but besides stripping above, some RIS entries do not have this for the 'ER' line
                raise Exception("Unexpected characters '%s' at positions 2-4." % line[2:5])

            content = line[5:].strip()
            if content:
                tag_data[tag_type] = tag_data.get(tag_type, [])
                tag_data[tag_type].append(content)

                if tag_type in tag_map:
                    if tag_type == 'JO':
                        d["journal"].insert(-1, content) # give precedence to the JO entry over the other journal tags
                    else:
                        d[tag_map[tag_type]].append(content)

        for k, v in tag_data.iteritems():
            if len(v) == 1:
                tag_data[k] = v[0]

        for k, v in d.iteritems():
            # Remove
            if len(v) == 0:
                d[k] = None
            elif len(v) == 1 and k != 'authors':
                d[k] = v[0]
            elif len(set(v)) == 1 and k != 'authors':
                d[k] = v[0]
            elif len(v) > 1:
                if k == 'journal':
                    d[k] = v[0]
                elif k == 'date':
                    found = False
                    for val in v:
                        if len(val.split("/")) == 3 or len(val.split("/")) == 4:
                            found = True
                            d[k] = val
                        if not found:
                            d[k] = v[0]
                    assert(found)
                elif k == 'url':
                    d[k] = v[0]
                else:
                    assert(k in ['authors'])
        assert(type(d['authors'] == lsttype))

        d['year'] = None
        if not d['date']:
            raise Exception("Error: The RIS record is missing information about the publication date.")
        else:
            try:
                pubdate = d['date']
                tokens = [t for t in pubdate.split("/")]
                if len(tokens) == 4: # YYYY/MM/DD/other info
                    tokens = tokens[0:3]
                tokens = map(int, [t for t in tokens if t])
                assert (1 <= len(tokens) <= 3)
                if len(tokens) > 1:
                    assert (1 <= tokens[1] <= 12)
                assert (1900 <= tokens[0] <= datetime.datetime.today().year)
                d['year'] = tokens[0]
                if len(tokens) == 3:
                    assert (1 <= tokens[2] <= 31)
                    d['date'] = datetime.date(tokens[0], tokens[1], tokens[2])
            except Exception, e:
                if not self.quiet:
                    print(traceback.format_exc())
                raise colortext.Exception("Exception in date line '%s'.\n %s" % (d['date'].strip(), str(e)))

        if not d['year']:
            errors.append("The year of publication could not be determined.")

        author_order = 0
        authors = []
        for author in d['authors']:
            surname = author.split(",")[0].strip()
            firstnames = author.split(",")[1].strip().split()
            firstname = firstnames[0]
            middlenames = []
            if len(firstnames) > 1:
                middlenames = firstnames[1:]

            assert (firstname)
            assert (surname)
            details = {
                "AuthorOrder": author_order,
                "FirstName": firstname,
                "MiddleNames": middlenames,
                "Surname": surname,
            }
            authors.append(details)
            author_order += 1
        d['authors'] = authors

        if d['publication_type'] == "JOUR" or d['publication_type'] == "CONF":
            pass # d['journal'] already set to JO, JA, J2, or JF data
        elif d['publication_type'] == "CHAP":
            d['journal'] = tag_data.get("BT")
        else:
            errors.append("Could not determine publication type.")

        for k, v in d.iteritems():
            self.__setattr__(k, v)


        if d['volume']:
            if not(d['issue']) and d['publication_type'] != "CHAP":
                errors.append("No issue found.")

        if not (PublicationInterface.get_page_range_in_abbreviated_format(self.startpage, self.endpage)):
            warnings.append("No start or endpage found.")
        #Doesn't seem to make sense for electronic journals without an endpage
        #elif not(self.startpage and self.endpage and self.startpage.isdigit() and self.endpage.isdigit()):
        #    warnings.append("No start or endpage found.")

        if not(self.journal):
            errors.append("No journal name found.")

        # doi parsing
        if not(self.doi):
            doi = None
            for k, v in tag_data.iteritems():
                if type(v) == type(u''):
                    if v.startswith("doi:"):
                        self.doi = v[4:].strip()
                        break
                    else:
                        doi_idx = v.find('dx.doi.org/')
                        if doi_idx != -1:
                            self.doi = urllib2.unquote(tag_data['UR'][doi_idx+(len('dx.doi.org/')):])
                            break
        if self.doi and self.doi.startswith("doi:"):
            self.doi = self.doi[4:].strip()

        if not self.doi:
            if not tag_data.get("UR"):
                errors.append("No DOI or URL available.")
            else:
                warnings.append("No DOI available.")
        else:
            if not doi_regex.match(self.doi):
                errors.append("Invalid doi string '%s'." % self.doi)
                self.doi = None

        if not(self.authors and self.title and self.journal and self.year):
            errors.append("Missing crucial information (author, title, journal, or year) - skipping entry.")
        else:
            if self.publication_type != "CHAP" and not(publication_abbreviations.get(self.journal)):
                matched = False
                normalized_journal_name = PublicationInterface._normalize_journal_name(self.journal)
                for k, v in publication_abbreviations.iteritems():
                    if PublicationInterface._normalize_journal_name(k) == normalized_journal_name or PublicationInterface._normalize_journal_name(v) == normalized_journal_name:
                        self.journal = k
                        matched = True
                        break
                if not matched:
                    errors.append("Missing abbreviation for journal '%s'." % self.journal)
                else:
                    assert(publication_abbreviations.get(self.journal))

        return errors, warnings


    def format(self, abbreviate_journal = True, abbreviate_author_names = True, show_year = True, html = True, allow_errors = False):
        raise Exception('This function is deprecated in favor of PublicationInterface.to_string. Some functionality needs to be added to that function e.g. ReferralURL_link.')
        if self.errors and not allow_errors:
            if not self.quiet:
                colortext.error("There were parsing errors: %s" % self.errors)
            return None

        # Abbreviate the journal name
        journal = self.journal
        if abbreviate_journal and self.publication_type != "CHAP":
            journal = publication_abbreviations.get(self.journal, self.journal)

        # Abbreviate the authors' names
        authors_str = None
        if abbreviate_author_names:
            authors_str = ", ".join(self.get_author_names_in_short_format())
        else:
            raise Exception("This code needs to be written with whatever is needed.")

        # Create string for the publication year
        year_str = ""
        if show_year:
            year_str = ", %s" % self.year

        ReferralURL_link = ""
        if self.ReferralURL:
            ReferralURL_link = " <a class='publist' href='%s'>[free download]</a>" % self.ReferralURL

        titlesuffix = '.'
        if self.publication_type == "CHAP":
            titlesuffix = " in"

        # The entry format is fixed. This could be passed as a variable for different styles.
        entry = ""
        if self.volume:
            entry = self.volume
            if self.subtitle:
                entry += " (%s)" % self.subtitle
            if self.issue:
                entry += "(%s)" % self.issue

            pagerange = PublicationInterface.get_page_range_in_abbreviated_format(self.startpage, self.endpage)
            if pagerange:
                entry += ":%s" % pagerange
        else:
            if self.startpage and self.endpage and self.startpage.isdigit() and self.endpage.isdigit():
                if self.subtitle:
                    entry = " (%s)" % self.subtitle
                pagerange = PublicationInterface.get_page_range_in_abbreviated_format(self.startpage, self.endpage)
                if pagerange:
                    entry += ":%s" % pagerange

        s = ['%s. ' % authors_str]
        if html:
            if self.doi:
                s.append('%s%s %s %s%s.' % (self.title, titlesuffix, self.journal, entry, year_str))
                s.append('doi: <a class="publication_doi" href="http://dx.doi.org/%s">%s</a>''' % (self.doi, self.doi))
                s.append(ReferralURL_link)
            elif self.url:
                s.append('<a class="publication_link" href="%s">%s</a>%s' % (self.url, self.title, titlesuffix))
                s.append('%s %s%s.' % (self.journal, entry, year_str))
                s.append(ReferralURL_link)
            else:
                s.append('%s%s %s %s%s.' % (self.title, titlesuffix, self.journal, entry, year_str))
                s.append(ReferralURL_link)
        else:
            s.append('%s%s %s %s%s.' % (self.title, titlesuffix, self.journal, entry, year_str))
            if self.doi:
                s.append('doi: %s' % self.doi)
            elif self.url:
                s.append('url: %s' % self.url)
        return " ".join(s)

    def get_earliest_date(self):
        return str(self.date).replace('-', '/')

    def get_url(self):
        if self.doi:
            return 'http://dx.doi.org/%s' % self.doi
        elif self.url:
            return self.url
        return None

    def get_year(self):
        return self.year

    def to_dict(self):
        '''A representation of that publication data that matches the schema we use in our databases.'''

        author_list = []
        for author in self.authors:
            author_list.append(
                dict(
                    AuthorOrder = author['AuthorOrder'] + 1, # we should always use 1-based indexing but since this is shared code, I do not want to change the logic above without checking to make sure I don't break dependencies
                    FirstName = author['FirstName'],
                    MiddleNames = ' '.join(author['MiddleNames']), # this is the main difference with the code above - the database expects a string, we maintain a list
                    Surname = author['Surname']
                )
            )

        pub_url = None
        if self.url or self.doi:
            pub_url = self.url or ('http://dx.doi.org/%s' % self.doi)

        return dict(
            Title = self.title,
            PublicationName = self.journal,
            Volume = self.volume,
            Issue = self.issue,
            StartPage = self.startpage,
            EndPage = self.endpage,
            PublicationYear = self.year,
            PublicationDate = self.date,
            RIS = self.RIS,
            DOI = self.doi,
            PubMedID = None,
            URL = pub_url,
            ISSN = None, # eight-digit number
            authors = author_list,
            #
            RecordType = RISEntry.record_types.get(self.publication_type)
        )


if __name__ == '__main__':
    import codecs
    test_ris = codecs.open('ris.test.txt', 'r', "utf-8" ).read()
    big_ris = "\n".join([l.strip() for l in test_ris.split("\n") if l.strip() and l[0] != '#'])
    list_o_ris = [l.strip() for l in big_ris.split("ER  -")[1:] if l.strip()]
    for pub in list_o_ris:
        r = RISEntry(pub + "\nER  - ")
        f = r.format(html = False)
    colortext.message("Test passed.")