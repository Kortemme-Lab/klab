#!/usr/bin/python
# encoding: utf-8
"""
strutil.py
Utility functions for string manipulation. 
"""

def parse_range(s, range_separator = '-'):
    ''' Parses the string s which contains indices and ranges and returns the explicit list of integers defined by s.
        Written by Laurens Kraal 2014.
    '''
    return reduce(lambda x,y: x+y, (map(lambda r: (range(int(r.split(range_separator)[0]), int(r.split(range_separator)[1])+1)) if range_separator in r else [int(r)], s.split(','))))

if __name__ == '__main__':
    assert(parse_range('5,12..15,17', range_separator = '..') == [5] + range(12,16) + [17])
    assert(parse_range('5-15,17') == range(5,16) + [17])
    assert(parse_range('1,3-10,12') == [1] + range(3, 11) + [12])