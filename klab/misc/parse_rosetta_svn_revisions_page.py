#!/usr/bin/python
# encoding: utf-8
"""
parse_rosetta_svn_revisions_page.py
A simple script to parse the HTML from https://svn.rosettacommons.org/trac.
Using SVN log would probably have made more sense but this was quick to implement.

Created by Shane O'Connor 2014
"""

import sys
sys.path.insert(0, '../..')

import datetime
import re
import pprint
from klab.fs.fsio import read_file
from klab import colortext
from klab.db.mysql import DatabaseInterface

write_to_db = False
SVN_pages = [
    'SVN_revisions_55111-49112.html',
    'SVN49112-43113.html',
    'SVN43112-37113.html',
    'SVN6112-1.html',
    'SVN13112-6113.html',
    'SVN19112-13113.html',
    'SVN25112-19113.html',
    'SVN31112-25113.html',
    'SVN37112-31113.html',
    'SVN43112-37113.html',
]

passwd = read_file('pw').strip()
revdb = DatabaseInterface(
    {},
    isInnoDB = True,
    numTries = 32,
    host = "guybrush.ucsf.edu",
    db = "RevViewer",
    user = 'revviewer',
    passwd = passwd,
    port = 3306,
    unix_socket = "/var/lib/mysql/mysql.sock",
    use_utf = True)

for p in SVN_pages:
    contents = read_file(p)
    tbody_idx = contents.find('<tbody>')
    contents = contents[tbody_idx + 7:]

    mtchs = re.match('(.*?)</table>\s+<div class="buttons">', contents, re.DOTALL)
    contents = mtchs.group(1)
    mtchs = re.split('<tr class="[odd|even] verbose">', contents, re.DOTALL)

    chunks = []
    while contents:
        assert(len(contents) < 9999999999999)
        odd_idx = contents.find('<tr class="odd verbose">')
        even_idx = contents.find('<tr class="even verbose">')
        first_chunk = min(odd_idx, even_idx)
        record = None
        if odd_idx != -1 and even_idx != -1:
            record = contents[min(odd_idx, even_idx):max(odd_idx, even_idx)]
            contents = contents[max(odd_idx, even_idx):]
        elif odd_idx != -1:
            record = contents[odd_idx:]
            contents = None
        elif even_idx != -1:
            record = contents[even_idx:]
            contents = None
        else:
            contents = None
            continue
        chunks.append(record)

    rev_numbers = []
    for section in chunks:
        if section.find('<td class="rev">') == -1:
            break
        header_section = section[:section.find('<td class="log"')]
        message_section = section[section.find('<td class="log"'):]

        tr_class = re.match('\s*<tr class="(.*?)">', header_section, re.DOTALL)
        assert(tr_class.group(1).find('verbose') != -1)

        rev_number = re.match('.*?https://svn.rosettacommons.org/trac/changeset/(\d+)/.*?">', header_section, re.DOTALL)
        rev_number = int(rev_number.group(1))

        DisplayName = re.match('.*?<td class="author">(.*?)</td>.*">', header_section, re.DOTALL)
        DisplayName = DisplayName.group(1)

        # Use UTC time
        CommitTime = re.match('.*?<td class="age">.*?title="(.*?) in Timeline".*">', header_section, re.DOTALL)
        CommitTime = CommitTime.group(1)
        tstr = CommitTime[:19]
        tzstr = CommitTime[19:]
        assert(tzstr.split(':')[1] == '00')
        offset = int(tzstr.split(':')[0])
        CommitTime = datetime.datetime.strptime(tstr, '%Y-%m-%dT%H:%M:%S')
        CommitTime += datetime.timedelta(minutes = -offset * 60)

        #'</td>\s*</tr>'
        message = re.match('.*?<td class="log".*?>(.*?)</td>\s*</tr>\s*', message_section, re.DOTALL)
        message = message.group(1)
        message = message.replace('\n', ' ')
        message = message.replace('<br>', '\n')
        message = message.replace('</p>', '\n')
        message = message.replace('<p>', '')
        message = re.sub('  ', ' ', message).strip()
        message = re.sub('\n\n', '\n', message)
        Message = '\n'.join([l.strip() for l in message.split('\n')])

        record = dict(
            ID = rev_number,
            Hash = None,
            DisplayName = DisplayName,
            Message = Message,
            CommitTime = CommitTime,
            BuildPassed = None,
            UnitTestsPassed = None,
            IntegrationTestsPassed = None,
            sfxn_fingerprint_Passed = None,
        )
        if write_to_db:
            print(rev_number, DisplayName, CommitTime)
            revdb.insertDictIfNew('Commit', record, ['ID'])
        else:
            pprint.pprint(record)




