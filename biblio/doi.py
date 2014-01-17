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

Created by Shane O'Connor 2014
"""
import sys
import re
if __name__ == '__main__':
    sys.path.insert(0, '../..')
import datetime
import urllib2
from xml.dom.minidom import parse, parseString

from tools.comms.http import get_resource
from tools.fs.io import read_file, write_file
from tools import colortext


class DOIRetrievalException(Exception): pass

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
        self.issue = {}
        self.article = {}
        self.doi = doi
        data = self.get_info()
        self.parse(data)

    def extract_node_data(self, tag, fieldnames):
        d = {}
        if tag and len(tag) == 1:
            return self.extract_node_data_2(tag[0], fieldnames)

    def extract_node_data_2(self, tag, fieldnames):
        d = {}
        for f in fieldnames:
            t = tag.getElementsByTagName(f)
            if len(t) > 0:
                d[f] = t[0].childNodes[0].nodeValue
        return d

    def parse_journal_data_xml(self, journal_tag):
        d = {}

        self.issue['meta_data'] = self.extract_node_data(journal_tag.getElementsByTagName("journal_metadata"), ['full_title', 'abbrev_title', 'issn'])
        journal_issue_tag = journal_tag.getElementsByTagName("journal_issue")
        assert(len(journal_issue_tag) <= 1)
        if len(journal_issue_tag) == 1:
            journal_issue_tag = journal_issue_tag[0]
            publication_dates = journal_issue_tag.getElementsByTagName("publication_date")
            for publication_date in publication_dates:
                media_type = publication_date.getAttribute('media_type').strip()
                if media_type:
                    self.issue['__issue_date'] = self.issue.get('__issue_date', {})
                    self.issue['__issue_date'][media_type] = self.extract_node_data_2(publication_date, ['year', 'month', 'day'])

            volume_tag = journal_issue_tag.getElementsByTagName("journal_volume")
            if len(volume_tag) == 1:
                self.issue['volume'] = int(volume_tag[0].getElementsByTagName("volume")[0].childNodes[0].nodeValue) # this type-cast may be too strong e.g. for electronic editions
            issue_tag = journal_issue_tag.getElementsByTagName("issue")
            if len(issue_tag) == 1:
                self.issue['issue'] = int(issue_tag[0].childNodes[0].nodeValue)

        article_tag = journal_tag.getElementsByTagName("journal_article")
        if len(article_tag) == 1:
            article_tag = article_tag[0]
            title_data = self.extract_node_data(article_tag.getElementsByTagName("titles"), ['title'])
            if title_data.get('title'):
                self.article['title'] = title_data['title']

            publication_dates = article_tag.getElementsByTagName("publication_date")
            for publication_date in publication_dates:
                media_type = publication_date.getAttribute('media_type').strip()
                if media_type:
                    self.article['__issue_date'] = self.article.get('__issue_date', {})
                    self.article['__issue_date'][media_type] = self.extract_node_data_2(publication_date, ['year', 'month', 'day'])

            self.article['authors'] = []
            for contributor in article_tag.getElementsByTagName("contributors")[0].getElementsByTagName("person_name"):
                if contributor.getAttribute('contributor_role') == "author":
                    fields = self.extract_node_data_2(contributor, ['given_name', 'surname'])
                    self.article['authors'].append(fields)

        # Convert dates
        for k, dct in self.issue.get('__issue_date', {}).iteritems():
            for t_, v_ in dct.iteritems():
                date_fields = self.issue['__issue_date'][k]
                date_fields[t_] = int(v_)
            date_fields = dct
            self.issue['issue_date'] = self.issue.get('issue_date', {})
            if date_fields.get('year') and date_fields.get('month') and date_fields.get('day'):
                self.issue['issue_date'][k] = datetime.datetime(date_fields['year'], date_fields['month'], date_fields['day'])

        for k, dct in self.article.get('__issue_date', {}).iteritems():
            for t_, v_ in dct.iteritems():
                self.article['__issue_date'][k][t_] = int(v_)
                date_fields[t_] = int(v_)
            self.article['issue_date'] = self.article.get('issue_date', {})
            if date_fields.get('year') and date_fields.get('month') and date_fields.get('day'):
                self.article['issue_date'][k] = datetime.datetime(date_fields['year'], date_fields['month'], date_fields['day'])

        # Move the issue meta_data to the top issue level
        for k, v in self.issue['meta_data'].iteritems():
            assert(k not in self.issue)
            self.issue[k] = v
        del self.issue['meta_data']


    def parse(self, data):
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

        journal_tag = crossref_tag[0].getElementsByTagName("journal")
        if len(journal_tag) == 1:
            return self.parse_journal_data_xml(journal_tag[0])


        protein_Existence_tags = entry_tag.getElementsByTagName("proteinExistence")
        assert(len(protein_Existence_tags) == 1)
        self.existence_type = protein_Existence_tags[0].getAttribute('type')


    def get_info(self):
        escaped_doi = urllib2.quote(self.doi, '')
        html = get_resource("www.crossref.org", '/guestquery?queryType=doi&restype=unixref&doi=%s&doi_search=Search' % escaped_doi)

        xml_matches = []
        for m in re.finditer('(<doi_records>.*?</doi_records>)', html, re.DOTALL):
            xml_matches.append(m.group(0))

        if len(xml_matches) == 0:
            raise DOIRetrievalException('No matches found for the DOI "%s".' % self.doi)
        elif len(xml_matches) == 1:
            write_file('test.xml', xml_matches[0])
            return xml_matches[0]
        else:
            raise DOIRetrievalException('Multiple (%d) matches found for the DOI "%s".' % (len(xml_matches), self.doi))

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
    d = DOI('10.1371/journal.pone.0063906')
    print(d)
