#!/usr/bin/python
# encoding: utf-8
"""
xml.py
Basic objects for bioinformatics.

Created by Shane O'Connor 2013
"""

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

def parse_singular_character(t, tag_name):
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

