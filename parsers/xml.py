#!/usr/bin/python
# encoding: utf-8
"""
xml.py
XML helper functions.

Created by Shane O'Connor 2013
"""

### Single value parsers
#  Parse the sole value from an XML tag. Assert that only one value exists and that it has the expected type.
###

def parse_singular_float(t, tag_name):
    '''Parses the sole floating point value with name tag_name in tag t. Heavy-handed with the asserts.'''
    pos = t.getElementsByTagName(tag_name)
    assert(len(pos) == 1)
    pos = pos[0]
    assert(len(pos.childNodes) == 1)
    return float(pos.childNodes[0].data)

def parse_singular_int(t, tag_name):
    '''Parses the sole integer value with name tag_name in tag t. Heavy-handed with the asserts.'''
    pos = t.getElementsByTagName(tag_name)
    assert(len(pos) == 1)
    pos = pos[0]
    assert(len(pos.childNodes) == 1)
    v = pos.childNodes[0].data
    assert(v.isdigit()) # no floats allowed
    return int(v)

def parse_singular_alphabetic_character(t, tag_name):
    '''Parses the sole alphabetic character value with name tag_name in tag t. Heavy-handed with the asserts.'''
    pos = t.getElementsByTagName(tag_name)
    assert(len(pos) == 1)
    pos = pos[0]
    assert(len(pos.childNodes) == 1)
    v = pos.childNodes[0].data
    assert(len(v) == 1 and v >= 'A' and 'v' <= 'z') # no floats allowed
    return v

def parse_singular_string(t, tag_name):
    '''Parses the sole string value with name tag_name in tag t. Heavy-handed with the asserts.'''
    pos = t.getElementsByTagName(tag_name)
    assert(len(pos) == 1)
    pos = pos[0]
    assert(len(pos.childNodes) == 1)
    return pos.childNodes[0].data

def fast_iter(context, func, **kwargs):
    # fast_iter is useful if you need to free memory while iterating through a
    # very large XML file.
    #
    # http://www.ibm.com/developerworks/xml/library/x-hiperfparse/
    # Author: Liza Daly
    # Modifed by: Shane O'Connor (added func_data).
    #
    # context should be the result of a call to lxml.etree.iterparse.
    # func is a reference to a function.
    # See bio/pdbtm.py for an example use.
    for event, elem in context:
        func(elem, **kwargs)
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]
    del context