#!/usr/bin/python2
# -*- coding: latin-1 -*-
"""
pubmed.py
PubMed handling functions.
This module gets publication data from a PubMed identifier, relying heavily on the doi.py module.

This module is a simple parser for the NCBI ID converter API:
 http://www.ncbi.nlm.nih.gov/pmc/tools/id-converter-api/
using their web API e.g.
?http://www.pubmedcentral.nih.gov/utils/idconv/v1.0/?ids=23193287
which returns XML.

Note: Like the doi module, I use xml.dom.minidom which is slow but the XML files are extremely small.

Created by Shane O'Connor 2014
"""

import sys
if __name__ == '__main__':
    sys.path.insert(0, '../..')
import urllib2
from xml.dom.minidom import parse, parseString

from doi import DOI
from klab.comms.http import get_resource
from klab import colortext

converter_types = ['pmcid', 'pmid', 'mid', 'doi']


class PubMedIDRetrievalException(Exception): pass
class NoCorrespondingDOIMappingException(Exception): pass
class PubMedConverterTypeException(Exception):
    '''Exception class thrown when incorrect conversion types are passed.'''
    def __init__(self, bad_type):
        self.bad_type = bad_type

    def __str__(self):
        return "\nThe type '%s' is not a valid type for the PubMed ID Converter API (or else this code needs to be updated).\nValid types are: '%s'." % (self.bad_type, "', '".join(converter_types))


def convert(ids, from_type):
    '''Uses the NCBI IP Converter API to converts a list of publication IDs in the same format e.g. DOI identifiers to
    another format e.g. PubMed identifiers.
        ids is a list of IDs of the type from_type e.g. a from_type of 'doi' specifies DOI identifiers.
        The function returns a Python dict with the mappings from the input IDs to IDs of all other types.
    '''

    if from_type not in converter_types:
        raise PubMedConverterTypeException(from_type)

    # Avoid multiple requests of the same ID
    mapping = {}
    ids = list(set(ids))

    # Request the mapping from the server
    query_string = "?ids=%s&idtype=%s" % (urllib2.quote(",".join(ids), ''), from_type)
    xml = get_resource("www.ncbi.nlm.nih.gov", '/pmc/utils/idconv/v1.0/%s' % query_string).strip()

    # Parse the response
    try:
        _dom = parseString(xml)
        main_tag = _dom.getElementsByTagName("pmcids")
        assert(len(main_tag) == 1)
        main_tag = main_tag[0]
        request_status = main_tag.getAttribute('status')
    except Exception, e:
        raise PubMedIDRetrievalException('An error occurred retrieving the XML from the PubMed ID Converter API: %s.' % str(e))

    if request_status == 'ok':
        for record_tag in main_tag.getElementsByTagName("record"):
            attributes = record_tag.attributes
            record_keys = attributes.keys()
            assert('requested-id' in record_keys)
            from_key = attributes['requested-id'].value
            assert(from_key not in mapping)
            mapping[from_key] = {}
            for k in record_keys:
                if k != 'requested-id':
                    mapping[from_key][k] = attributes[k].value
    else:
        # todo: parse the error tag here to print more details
        raise PubMedIDRetrievalException('The request to the PubMed ID Converter API failed. Please check that the IDs are of the correct types.')

    return mapping


def convert_single(ID, from_type, to_type):
    '''Convenience function wrapper for convert. Takes a single ID and converts it from from_type to to_type.
       The return value is the ID in the scheme of to_type.'''

    if from_type not in converter_types:
        raise PubMedConverterTypeException(from_type)
    if to_type not in converter_types:
        raise PubMedConverterTypeException(to_type)

    results = convert([ID], from_type)
    if ID in results:
        return results[ID].get(to_type)
    else:
        return results[ID.upper()].get(to_type)


class PubMed(DOI):
    '''This is essentially a wrapper onto the DOI class.'''
    def __init__(self, pubmed_id):

        # Allow for 'pmid:23717507' or '23717507'
        self.pubmed_id = pubmed_id
        pubmed_id = pubmed_id.strip()
        if pubmed_id.lower().startswith('pmid:'):
            pubmed_id = pubmed_id[5:].strip()

        # Convert the PMID to a DOI identifier
        if not pubmed_id.isdigit():
            raise PubMedIDRetrievalException("PubMed identifiers are expected to be numeric strings with or without a prefix of 'pmid'. The passed value '%s' does not meet this requirement." % pubmed_id)
        doi = convert_single(pubmed_id, 'pmid', 'doi')

        if doi == None:
            raise NoCorrespondingDOIMappingException
        else:
            super(PubMed, self).__init__(doi)

    def get_pubmed_id(self):
        return self.pubmed_id


if __name__ == '__main__':

    colortext.message('\nRetrieving the mapping for PMC3531190 and PMC3245039.')
    print(convert(['PMC3531190,PMC3245039'], 'pmcid'))

    print('')
    pubmed_IDs = ('23717507', '23193287', '24005320')
    for p in pubmed_IDs:
        colortext.message(p)
        pubmed = PubMed(p)
        print('{0}\n'.format(pubmed))


# Example XML response
# <pmcids status="ok">
#    <request idtype="pmcid" pmcids="PMC3531190,PMC3245039" versions="yes">ids=PMC3531190%2CPMC3245039;idtype=pmcid</request>
#    <record requested-id="PMC3531190" pmcid="PMC3531190" pmid="23193287" doi="10.1093/nar/gks1195">
#        <versions>
#            <version pmcid="PMC3531190.1" current="true"/>
#        </versions>
#    </record>
#    <record requested-id="PMC3245039" pmcid="PMC3245039" pmid="22144687" doi="10.1093/nar/gkr1202">
#        <versions>
#            <version pmcid="PMC3245039.1" current="true"/>
#        </versions>
#    </record>
# </pmcids>
