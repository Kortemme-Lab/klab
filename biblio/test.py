#!/usr/bin/python2
# -*- coding: latin-1 -*-
"""
test.py
Test code for these modules.

Created by Shane O'Connor 2014
"""


if __name__ == '__main__':
    import sys
    sys.path.insert(0, '../..')

    from tools import colortext
    from doi import DOI, RecordTypeParsingNotImplementedException, CrossRefException

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
    for d in test_journal_DOIs:
        try_count += 1
        #if try_count > 7:
        #    break
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
