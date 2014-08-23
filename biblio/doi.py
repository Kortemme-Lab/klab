#!/usr/bin/python2
# -*- coding: latin-1 -*-
"""
doi.py
DOI handling functions.
This module gets publication data from a DOI identifier.
It currently hinges on the CrossRef.org website POST format. This can be inspected by looking at the POST requests when
using the form on the webpage. At present, it resolves to this format:
   http://www.crossref.org/guestquery?queryType=doi&restype=unixref&doi=10.5555%2F12345678&doi_search=Search
described here
   http://www.crossref.org/schema/documentation/unixref1.0/unixref.html
   http://www.crossref.org/schema/documentation/unixref1.1/unixref1.1.html

Note: xml.dom.minidom is slow but incredibly easy to write/follow. I think it should be fine for our scale of use (occassionally
parsing a few, small files). xml.sax could be a lot faster for huge amounts of files (or not) so if speed becomes an issue
then that would be a good place to start.

Created by Shane O'Connor 2014
"""
import sys
import re
if __name__ == '__main__':
    sys.path.insert(0, '../..')
import datetime
import urllib2
import json
from xml.dom.minidom import parse, parseString

from tools.comms.http import get_resource
from tools import colortext

class DOIRetrievalException(Exception): pass
class RecordTypeParsingNotImplementedException(Exception): pass
class UnexpectedRecordTypeException(Exception): pass
class NoAuthorsFoundException(Exception): pass
class CrossRefException(Exception): pass

class DOI(object):
    ''' A class to retrieve information about a journal publication (only journals at present until I get more test cases) from a DOI string.
    Instantiate an object with a DOI string e.g. "a = DOI('10.1371/journal.pone.0063906')". The information is stored in
    the issue and article members of the object in a hierarchical format similar to what is returned by the CrossRef website e.g.
       issue:
         issue_date:
           online: 2013-05-22 00:00:00
         issn: 1932-6203
         volume: 8
         full_title: PLoS ONE
         abbrev_title: PLoS ONE
         issue: 5
        article:
         authors:
           {'surname': u'Lyskov', 'given_name': u'Sergey'}
           {'surname': u'Chou', 'given_name': u'Fang-Chieh'}
           {'surname': u'Conch\xfair', 'given_name': u'Shane \xd3.'}
           {'surname': u'Der', 'given_name': u'Bryan S.'}
           {'surname': u'Drew', 'given_name': u'Kevin'}
           {'surname': u'Kuroda', 'given_name': u'Daisuke'}
           {'surname': u'Xu', 'given_name': u'Jianqing'}
           {'surname': u'Weitzner', 'given_name': u'Brian D.'}
           {'surname': u'Renfrew', 'given_name': u'P. Douglas'}
           {'surname': u'Sripakdeevong', 'given_name': u'Parin'}
           {'surname': u'Borgo', 'given_name': u'Benjamin'}
           {'surname': u'Havranek', 'given_name': u'James J.'}
           {'surname': u'Kuhlman', 'given_name': u'Brian'}
           {'surname': u'Kortemme', 'given_name': u'Tanja'}
           {'surname': u'Bonneau', 'given_name': u'Richard'}
           {'surname': u'Gray', 'given_name': u'Jeffrey J.'}
           {'surname': u'Das', 'given_name': u'Rhiju'}
         issue_date:
           online: 2013-05-22 00:00:00
         title: Serverification of Molecular Modeling Applications: The Rosetta Online Server That Includes Everyone (ROSIE)
    '''

    def __init__(self, doi):

        # Allow for 'doi:10.1038/nature12443' or '10.1038/nature12443'
        doi = doi.strip()
        if doi.lower().startswith('doi:'):
            doi = doi[4:].strip()

        self.issue = {}
        self.article = {}
        self.published_dates = []
        self.doi = doi
        self.data = self.get_info()

        self.parse()


    # Record retrieval


    def get_info(self):
        'Retrieve the data from CrossRef.'
        escaped_doi = urllib2.quote(self.doi, '')
        html = get_resource("www.crossref.org", '/guestquery?queryType=doi&restype=unixref&doi=%s&doi_search=Search' % escaped_doi)

        xml_matches = []
        for m in re.finditer('(<doi_records>.*?</doi_records>)', html, re.DOTALL):
            xml_matches.append(m.group(0))

        if len(xml_matches) == 0:
            raise DOIRetrievalException('No matches found for the DOI "%s".' % self.doi)
        elif len(xml_matches) == 1:
            return xml_matches[0]
        else:
            raise DOIRetrievalException('Multiple (%d) matches found for the DOI "%s".' % (len(xml_matches), self.doi))


    # Helper functions


    def extract_node_data(self, tag, fieldnames):
        #print(colortext.make(str(fieldnames), 'cyan'))
        if tag and len(tag) == 1:
            return self.extract_node_data_2(tag[0], fieldnames)


    def extract_node_data_2(self, tag, fieldnames):
        d = {}
        for f in fieldnames:
            t = tag.getElementsByTagName(f)
            if len(t) > 0:
                d[f] = t[0].childNodes[0].nodeValue
        return d


    # Main parsing function

    def parse(self):
        data = self.data
        try:
            self._dom = parseString(data)
        except Exception, e:
            raise DOIRetrievalException("An error occurred while parsing the XML for the DOI record.\n%s" % str(e))

        try:
            main_tag = self._dom.getElementsByTagName("doi_records")
            assert(len(main_tag) == 1)
            record_tag = main_tag[0].getElementsByTagName("doi_record")
            assert(len(record_tag) == 1)
            crossref_tag = record_tag[0].getElementsByTagName("crossref")
            assert(len(crossref_tag) == 1)
        except Exception, e:
            raise DOIRetrievalException("The XML format does not fit the expected format.\n%s" % str(e))

        crossref_tag = crossref_tag[0]
        child_nodes = []
        for c in xrange(len(crossref_tag.childNodes)):
            if crossref_tag.childNodes[c].toxml().strip():
                child_nodes.append(crossref_tag.childNodes[c].nodeName)

        if len(child_nodes) == 0:
            raise(RecordTypeParsingNotImplementedException('Could not find any entries in the CrossRef record to parse.'))
        if len(child_nodes) > 1:
            raise(RecordTypeParsingNotImplementedException('Multiple entries were found in the CrossRef record. This case is not currently handled.'))
        else:
            tag_type = child_nodes[0]
            self.record_type = tag_type
            if tag_type == 'journal':
                journal_tag = crossref_tag.getElementsByTagName("journal")
                if len(journal_tag) == 1:
                    return self.parse_journal_data_xml(journal_tag[0])
            elif tag_type in ['book', 'conference', 'sa_component', 'dissertation', 'report-paper', 'standard', 'database']:
                print(self.data)
                raise(RecordTypeParsingNotImplementedException("The CrossRef record is for a publication of type '%s'. This case is not currently handled." % tag_type))
            elif tag_type == 'error':
                error_tag = crossref_tag.getElementsByTagName("error")
                if len(error_tag) == 1:
                    error_msg = None
                    try: error_msg = error_tag[0].childNodes[0].nodeValue
                    except: pass
                    if error_msg:
                        raise(CrossRefException("A CrossRef exception occurred: '%s'." % error_msg))
                    else:
                        raise(CrossRefException("An unknown CrossRef exception occurred."))
                else:
                    raise(CrossRefException("An unknown CrossRef exception occurred."))
            else:
                print(self.data)
                raise(UnexpectedRecordTypeException("An expected CrossRef record was found ('%s'). This case is not currently handled." % tag_type))


    # Parsing functions for specific record types
    # todo: Only the journal type is added now. When I add more record types, figure out the overlap with other types
    # (using the XSD - http://doi.crossref.org/schemas/crossref4.3.0.xsd) and separate out the blocks below into common
    # functions e.g. author name parsing from the contributors tag.
    #
    # contributor tags are common to the journal, conference, book, series, report-paper, standard, and database types.
    # person_name is used by the contributor type and used in dissertation (rather than an enclosing contributor tag).
    #
    # It makes sense to separate these out into a contributor tag parsing function and an person_name parsing function.
    #
    # Look here also: http://doi.crossref.org/schemas/common4.3.0.xsd as that spec defines the subtypes like contributors.

    def parse_journal_data_xml(self, journal_tag):
        self.issue['meta_data'] = self.extract_node_data(journal_tag.getElementsByTagName("journal_metadata"), ['full_title', 'abbrev_title', 'issn'])
        journal_issue_tag = journal_tag.getElementsByTagName("journal_issue")
        assert(len(journal_issue_tag) <= 1)
        if len(journal_issue_tag) == 1:
            journal_issue_tag = journal_issue_tag[0]
            publication_dates = journal_issue_tag.getElementsByTagName("publication_date")
            for publication_date in publication_dates:
                media_type = publication_date.getAttribute('media_type').strip() or 'unknown_media'
                if media_type:
                    self.issue['__issue_date'] = self.issue.get('__issue_date', {})
                    self.issue['__issue_date'][media_type] = self.extract_node_data_2(publication_date, ['year', 'month', 'day'])

            volume_tag = journal_issue_tag.getElementsByTagName("journal_volume")
            if len(volume_tag) == 1:
                self.issue['volume'] = int(volume_tag[0].getElementsByTagName("volume")[0].childNodes[0].nodeValue) # this type-cast may be too strong e.g. for electronic editions
            issue_tag = journal_issue_tag.getElementsByTagName("issue")
            if len(issue_tag) == 1:
                self.issue['issue'] = issue_tag[0].childNodes[0].nodeValue # not necessarily an int e.g. pmid:23193287 / doi:10.1093/nar/gks1195

        # Parse Journal Article information
        article_tag = journal_tag.getElementsByTagName("journal_article")
        if len(article_tag) == 1:
            article_tag = article_tag[0]

            # Titles
            # A hack to deal with titles with embedded HTML
            tag = article_tag.getElementsByTagName("titles")
            if tag and len(tag) == 1:
                inner_tag = tag[0].getElementsByTagName('title')
                if inner_tag and len(inner_tag) == 1:
                    inner_tag_xml = inner_tag[0].toxml()
                    article_title = ' '.join(inner_tag_xml.replace('<title>', '').replace('</title>', '').split())
                    idx = article_title.find('<![CDATA[')
                    if idx != -1:
                        right_idx = article_title[idx+9:].find(']]>') + 9
                        if right_idx != -1:
                            article_title = ('%s %s' % (article_title[idx+9:right_idx], article_title[right_idx+3:])).strip()
                    self.article['title'] = article_title

                inner_tag = tag[0].getElementsByTagName('subtitle')
                if inner_tag and len(inner_tag) == 1:
                    inner_tag_xml = inner_tag[0].toxml()
                    article_subtitle = ' '.join(inner_tag_xml.replace('<subtitle>', '').replace('</subtitle>', '').split())
                    idx = article_subtitle.find('<![CDATA[')
                    if idx != -1:
                        right_idx = article_subtitle[idx+9:].find(']]>') + 9
                        if right_idx != -1:
                            article_subtitle = ('%s %s' % (article_subtitle[idx+9:right_idx], article_subtitle[right_idx+3:])).strip()
                    self.article['subtitle'] = article_subtitle


            #title_data = self.extract_node_data(article_tag.getElementsByTagName("titles"), ['title', 'subtitle'])
            #if title_data.get('title'):
            #    self.article['title'] = title_data['title']
            #    self.article['subtitle'] = title_data['subtitle']

            publication_dates = article_tag.getElementsByTagName("publication_date") or []
            for publication_date in publication_dates:
                media_type = publication_date.getAttribute('media_type').strip() or 'unknown_media'
                if media_type:
                    self.article['__issue_date'] = self.article.get('__issue_date', {})
                    self.article['__issue_date'][media_type] = self.extract_node_data_2(publication_date, ['year', 'month', 'day'])

            self.article['authors'] = []
            if article_tag.getElementsByTagName("contributors"):
                for contributor in article_tag.getElementsByTagName("contributors")[0].getElementsByTagName("person_name"):
                    if contributor.getAttribute('contributor_role') == "author":
                        fields = self.extract_node_data_2(contributor, ['given_name', 'surname'])

                        # A hack to fix bad records e.g. 10.1016/j.neuro.2006.03.023 where the authors' names are all in uppercase.
                        # Note that in this case, it does not fix the missing apostrophe in "O'Gara" or the missing hyphen/capitalization in "Leigh-Logan".
                        for k, v in fields.iteritems():
                            if v.isupper():
                                fields[k] = v.title()

                        self.article['authors'].append(fields)

            if not self.article['authors']:
                raise NoAuthorsFoundException('Could not find any authors in the CrossRef record.')

            article_pages =  self.extract_node_data(article_tag.getElementsByTagName("pages"), ['first_page', 'last_page']) or {}
            for k, v in article_pages.iteritems():
                self.article[k] = v


        # Convert dates
        for media_type, date_fields in self.issue.get('__issue_date', {}).iteritems():
            for t_, v_ in date_fields.iteritems():
                date_fields[t_] = int(v_)
            self.issue['issue_date'] = self.issue.get('issue_date', {})
            if date_fields.get('year') and date_fields.get('month') and date_fields.get('day'):
                dt = datetime.date(date_fields['year'], date_fields['month'], date_fields['day'])
                self.issue['issue_date'][media_type] = dt
                self.published_dates.append(dt)

        for media_type, date_fields in self.article.get('__issue_date', {}).iteritems():
            for t_, v_ in date_fields.iteritems():
                date_fields[t_] = int(v_)
            self.article['issue_date'] = self.article.get('issue_date', {})
            if date_fields.get('year') and date_fields.get('month') and date_fields.get('day'):
                dt = datetime.date(date_fields['year'], date_fields['month'], date_fields['day'])
                self.article['issue_date'][media_type] = dt
                self.published_dates.append(dt)

        # Move the issue meta_data to the top issue level
        for k, v in (self.issue['meta_data'] or {}).iteritems():
            assert(k not in self.issue)
            self.issue[k] = v
        del self.issue['meta_data']


    # String printing / data retrieval functions

    def get_pubmed_id(self):
        return None

    def get_url(self):
        return 'http://dx.doi.org/%s' % self.doi


    def get_earliest_date(self):
        if self.published_dates:
            return str(sorted(self.published_dates)[0]).replace('-', '/')
        return None


    def get_year(self):
        article_date = self.issue.get('__issue_date') or self.article.get('__issue_date')
        if article_date:
            for media_type, fields in article_date.iteritems():
                if fields.get('year'):
                    # break on the first found year
                    return str(fields.get('year'))
        return None


    def to_json(self):
        '''A representation of that publication data that matches the schema we use in our databases.'''
        if not self.record_type == 'journal':
            # todo: it may be worthwhile creating subclasses for each entry type (journal, conference, etc.) with a common
            # API e.g. to_json which creates output appropriately
            raise Exception('This function has only been tested on journal entries at present.')

        author_list = []
        authors = self.article.get('authors', [])
        for x in range(len(authors)):
            author = authors[x]
            first_name = None
            middle_names = None
            if author.get('given_name'):
                names = author['given_name'].split()
                first_name = names[0]
                middle_names = (' '.join(names[1:])) or None
            author_list.append(
                dict(
                    AuthorOrder = x + 1,
                    FirstName = first_name,
                    MiddleNames = middle_names,
                    Surname = author.get('surname')
                )
            )

        return json.dumps(dict(
            Title = self.article.get('title'),
            PublicationName = self.issue.get('full_title'),
            Volume = self.issue.get('volume'),
            Issue = self.issue.get('issue'),
            StartPage = self.article.get('first_page'),
            EndPage = self.article.get('last_page'),
            PublicationYear = self.get_year(),
            PublicationDate = self.get_earliest_date(),
            RIS = None,
            DOI = self.doi,
            PubMedID = self.get_pubmed_id(),
            URL = 'http://dx.doi.org/%s' % self.doi,
            ISSN = None, # eight-digit number
            authors = author_list,
        ))


    def to_string(self, html = False, add_url = False):

        if not self.record_type == 'journal':
            raise Exception('This function has only been tested on journal entries at present.')

        author_str = []
        for author in self.article.get('authors', []):
            author_str.append(('%s %s' % (author.get('given_name'), author.get('surname'))).strip())
        author_str = (', '.join(author_str))
        if html and author_str:
            author_str = '<span class="publication_authors">%s.</span>' % author_str

        title_str = self.article.get('title', '')
        if title_str:
            if add_url:
                title_str = '<a href="%s" target="_blank">%s</a>' % (self.get_url(), title_str)
        if html and title_str:
            title_str = '<span class="publication_title">%s.</span>' % title_str

        issue_str = ''
        if self.issue.get('full_title'):
            issue_str += self.issue['full_title']
            if self.issue.get('volume'):
                if self.issue.get('issue'):
                    issue_str += ' %s(%s)' % (self.issue['volume'], self.issue['issue'])
                else:
                    issue_str += ' %s' % self.issue['volume']
                if self.article.get('first_page'):
                    issue_str += ':%s' % self.article['first_page']
                    if self.article.get('last_page'):
                        issue_str += '-%s' % self.article['last_page']
        if html and issue_str:
            issue_str = '<span class="publication_issue">%s.</span>' % issue_str

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


    def __repr__(self):
        s = ['issue']
        for k, v in self.issue.iteritems():
            if not k.startswith('__'):
                if type(v) == type(self.issue):
                    s.append(' %s:' % k)
                    for k_, v_ in v.iteritems():
                        s.append('   %s: %s' % (k_, str(v_)))
                else:
                    s.append(' %s: %s' % (k, str(v)))

        s.append('article')
        for k, v in self.article.iteritems():
            if not k.startswith('__'):
                if type(v) == type(self.issue):
                    s.append(' %s:' % k)
                    for k_, v_ in v.iteritems():
                        s.append('   %s: %s' % (k_, str(v_)))
                elif type(v) == type(s):
                    s.append(' %s:' % k)
                    for v_ in v:
                        s.append('   %s' % str(v_))
                else:
                    s.append(' %s: %s' % (k, str(v)))

        return "\n".join(s)


if __name__ == '__main__':

    test_journal_DOIs = [
        # Journals
        '10.1371/journal.pone.0097279',
        '10.1002/pro.2421', # The title has embedded HTML and bad white-spacing
        '10.1093/bioinformatics/btt735',
        '10.1109/TCBB.2013.113', # the title is contained inside a CDATA block
        '10.1038/nnano.2013.242',
        '10.1021/ja404992r',
        '10.1371/journal.pone.0063090',
        '10.1073/pnas.1300327110',
        '10.1371/journal.pone.0063906',
        '10.1016/j.str.2012.10.007',
        '10.1371/journal.pcbi.1002639',
        '10.1126/science.1219083',
        '10.1073/pnas.1114487109',
        '10.1038/nature10719',
        '10.1016/j.cell.2011.07.038',
        '10.1371/journal.pone.0020451',
        '10.1002/pro.632',
        '10.1016/j.jmb.2010.12.019',
        '10.1016/j.jmb.2010.07.032',
        '10.1083/jcb.201004060',
        '10.1093/nar/gkq369',
        '10.1016/j.sbi.2010.02.004',
        '10.1038/nchembio.251',
        '10.1016/j.copbio.2009.07.006',
        '10.1038/nmeth0809-551',
        '10.1371/journal.pcbi.1000393',
        '10.1038/msb.2009.9',
        '10.1016/j.str.2008.12.014',
        '10.1002/prot.22293',
        '10.1016/j.str.2008.11.004',
        '10.1016/j.str.2008.09.012',
        '10.1074/jbc.M806370200',
        '10.1016/j.jmb.2008.05.006',
        '10.1016/j.jmb.2008.05.023',
        '10.1016/j.jmb.2007.11.020',
        '10.1371/journal.pcbi.0030164',
        '10.1074/jbc.M704513200',
        '10.1016/j.str.2007.09.010',
        '10.1016/j.jmb.2006.05.022',
        '10.1016/j.chembiol.2006.03.007',
        '10.1074/jbc.M510454200',
        '10.1073/pnas.0608127103',
        '10.1073/pnas.0600489103',
        '10.1073/pnas.202485799',
        '10.1016/S1097-2765(02)00690-1',
        '10.1002/prot.10384',
        '10.1038/nsmb749',
        '10.1016/j.cbpa.2003.12.008',
        '10.1016/S0022-2836(03)00021-4',
        '10.1021/jp0267555',
        '10.1126/stke.2192004pl2',
        '10.1073/pnas.0307578101',
        '10.1093/nar/gkh785',
        '10.1002/prot.20347',
        '10.1016/S0969-2126(03)00047-9',
        '10.1016/S1097-2765(03)00365-4',
        '10.1021/bi034873s',
        '10.1021/bi00072a010',
        '10.1002/pro.5560030514',
        '10.1126/science.281.5374.253',
        '10.1016/S0968-0896(98)00215-6',
        '10.1016/S0959-440X(99)80069-4',
        '10.1006/jmbi.1996.0155',
        '10.1006/jmbi.2000.3618',
        '10.1016/S0022-2836(02)00706-4',
        '10.1006/jmbi.1995.0592',
        '10.1021/bi9617724',
        '10.1021/bi973101r',
        '10.4049/jimmunol.1101494',
        '10.1126/science.1205822',
        '10.1021/jp800282x',
        '10.1371/journal.pbio.1000450',
        '10.1101/gr.074344.107',
        '10.1186/1471-2148-7-24',
        '10.1093/icb/icl035',
        '10.1103/PhysRevE.74.051801',
        '10.1021/bi101413v',
        '10.1021/bi9012897',
        '10.1039/B821345C',
        '10.1021/bi801397e',
        '10.1021/jp801174z',
        '10.1529/biophysj.107.106633',
        '10.1021/bi051448l',
        '10.1093/bioinformatics/btq495',
        '10.1073/pnas.0801207105',
        '10.1186/gb-2006-7-12-r125',
        '10.1021/cb3006402',
        '10.1002/pro.735',
        '10.1021/bi100975z',
        '10.1021/bi802027g',
        '10.1093/bioinformatics/bti828',
        '10.1074/jbc.M401675200',
        '10.1016/j.str.2011.03.009',
        '10.1016/j.sbi.2011.01.005',
        '10.1371/journal.pone.0031220',
        '10.1074/mcp.M111.014969',
        '10.1093/nar/gks446',
        '10.1038/embor.2010.171',
        '10.1093/nar/gkq962',
        '10.1371/journal.pcbi.1000789',
        '10.1093/nar/gkq194',
        '10.1016/j.str.2010.08.001',
        '10.1111/j.1742-4658.2009.07251.x',
        '10.1093/nar/gkn690',
        '10.1021/ci800174c',
        '10.1371/journal.pone.0002524',
        '10.1016/j.febslet.2008.02.020',
        '10.1093/nar/gki037',
        '10.1186/1752-0509-3-74',
        '10.1002/pmic.200700966',
        '10.1016/j.febslet.2008.02.014',
        '10.1089/cmb.2007.0178',
        '10.3233/SPE-2008-0361', # No DOI record in CrossRef (the DOI is valid)
        '10.1016/j.bbrc.2007.04.113',
        '10.1007/s11306-006-0028-0',
        '10.1021/ac051437y',
        '10.1021/ac051312t',
        '10.1021/ja210118w',
        '10.1002/prot.23225',
        '10.1002/prot.22518',
        '10.1073/pnas.0906652106',
        '10.1074/jbc.M504922200',
        '10.1186/gb-2004-5-10-r80',
        '10.1038/nchembio.522',
        '10.1002/em.20559',
        '10.1021/bi902169q',
        '10.1021/tx9000896',
        '10.1021/bi800925e',
        '10.1021/bc7004363',
        '10.1093/nar/gkm974',
        '10.1016/j.neuro.2006.03.023', # the authors' names are all in uppercase
        '10.1016/j.aquatox.2004.04.006',
        '10.1038/nbt.1755',
        '10.1093/nar/gkt673',
        '10.1016/j.sbi.2013.07.004',
        '10.1016/j.cell.2013.02.044',
        '10.1042/BST20120056',
        '10.1002/pro.2071',
        '10.1073/pnas.1120028109',
        '10.1016/j.sbi.2010.03.007',
        '10.1074/jbc.M803219200',
        '10.1371/journal.ppat.1004204',
        '10.1016/j.cell.2014.04.034',
        '10.1038/nchembio.1554',
        '10.1042/BST20130055',
        '10.1038/nature13404',
        '10.1073/pnas.1321126111',
        '10.1038/nchembio.1498',
        '10.1093/protein/gzt061', # has both online and print dates so it is a good one to test our code to choose the earliest date
        '10.1038/nature12966',
        '10.1515/hsz-2013-0230',
        '10.1016/j.str.2013.08.009',
        '10.1073/pnas.1314045110',
        '10.1016/j.jmb.2013.06.035',
        '10.1038/nature12443',
        '10.1021/ja403503m',
        '10.1007/s10858-013-9762-6',
        '10.1016/j.str.2013.08.005',
        '10.1002/prot.24463',
        '10.1002/pro.2389',
        '10.1016/j.jmb.2013.10.012',
        '10.1007/s10858-013-9772-4',
        '10.1021/cb4004892',
        '10.1002/prot.24356',
        '10.1038/nmeth.2648',
        '10.1002/anie.201204077',
        '10.1126/science.1234150',
        '10.1371/journal.ppat.1003245',
        '10.1002/pro.2267',
        '10.1002/prot.24374',
        '10.1021/sb300061x',
        '10.1038/ncomms3974',
        '10.1038/nchembio.1276',
        '10.1021/cb3006227',
        '10.1038/nature12007',
        '10.1371/journal.ppat.1003307',
        '10.1371/journal.pone.0059004',
        '10.1021/ja3037367',
        '10.1038/nature11600',
        '10.1038/nbt.2214',
        '10.1002/pro.2059',
        '10.1007/s10969-012-9129-3',
        '10.1038/nchembio.777',
        '10.1002/jcc.23069',
        '10.1021/ja3094795',
        '10.1038/nbt.2109',
        '10.1126/science.1219364',
        '10.1038/nature11079',
        '10.1038/nature10349',
        '10.1038/nsmb.2119',
        '10.1002/prot.22921',
        '10.1038/nature10154',
        '10.1002/prot.23046',
        '10.1002/pro.604',
        '10.1002/pro.462',
        '10.1021/jp037711e',
    ]

    test_book_DOIs = [
        # I do not currently have a parser for these cases
        '10.1016/B978-0-12-394292-0.00004-7',
        '10.1016/B978-0-12-394292-0.00006-0',
        '10.1016/B978-0-12-381270-4.00019-6',
        '10.1016/S0065-3233(05)72001-5',
        '10.5772/52250',
        '10.1007/978-1-62703-968-0_17',
        '10.1016/B978-0-12-394292-0.00001-1',
        '10.1016/B978-0-12-394292-0.00006-0',
    ]

    try_count = 0
    print(len(test_journal_DOIs))
    for d in test_journal_DOIs[10:]:
        try_count += 1
        if try_count > 7:
            break
        try:
            print('')
            colortext.message(d)
            doi = DOI(d)
            #colortext.warning(doi)
            #print(doi.data)
            #colortext.message('print_string')
            print(colortext.make(doi.to_string(html=False), 'cyan'))
            #print(colortext.make(str(doi), 'orange'))
            colortext.warning(doi.issue.get('__issue_date') or doi.article.get('__issue_date'))
            colortext.warning(doi.get_earliest_date())
            url_string = 'www.crossref.org/guestquery?queryType=doi&restype=unixref&doi=%s&doi_search=Search' % d
            print(url_string)
            if not (doi.issue.get('__issue_date') or doi.article.get('__issue_date')):
                break
            j = doi.to_json()
            print('')
        except RecordTypeParsingNotImplementedException, e:
            colortext.error('Unhandled type: %s' % str(e))
            print('')
            continue
        except CrossRefException, e:
            colortext.error('CrossRef exception: %s' % str(e))
            print('')
            continue
    print('\n\n\n')
