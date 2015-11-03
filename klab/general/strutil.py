#!/usr/bin/python
# encoding: utf-8
"""
strutil.py
Utility functions for string manipulation.

Created by Shane O'Connor 2014
"""


def remove_trailing_line_whitespace(content):
    return ('\n'.join([l.strip() for l in content.split('\n')])).strip()


def parse_range(s, range_separator = '-'):
    ''' Parses the string s which contains indices and ranges and returns the explicit list of integers defined by s.
        Written by Laurens Kraal 2014.
    '''
    return reduce(lambda x,y: x+y, (map(lambda r: (range(int(r.split(range_separator)[0]), int(r.split(range_separator)[1])+1)) if range_separator in r else [int(r)], s.split(','))))


def parse_range_pairs(s, range_separator = '-', convert_to_tuple = True):
    ''' Based on parse_range but instead returns a list of lists with the ranges. A single index n is returned as a range (n, n)
        whereas a range m-n is returned as (m, n) if m <= n, else (n, m).
    '''
    result = map(sorted,
       map(lambda r:
            (int(r.split(range_separator)[0]), int(r.split(range_separator)[1])) if range_separator in r
            else (int(r), int(r)),
            s.split(',')))
    if convert_to_tuple:
        return tuple(map(tuple, result))
    return result


def merge_range_pairs(prs):
    '''Takes in a list of pairs specifying ranges and returns a sorted list of merged, sorted ranges.'''
    new_prs = []
    sprs = [sorted(p) for p in prs]
    sprs = sorted(sprs)
    merged = False
    x = 0
    while x < len(sprs):
        newx = x + 1
        new_pair = list(sprs[x])
        for y in range(x + 1, len(sprs)):
            if new_pair[0] <= sprs[y][0] - 1 <= new_pair[1]:
                new_pair[0] = min(new_pair[0], sprs[y][0])
                new_pair[1] = max(new_pair[1], sprs[y][1])
                newx = y + 1
        if new_pair not in new_prs:
            new_prs.append(new_pair)
        x = newx
    return new_prs


def split_pdb_residue(s):
    '''Splits a PDB residue into the numeric and insertion code components.'''
    if s.isdigit():
        return (int(s), ' ')
    else:
        assert(s[:-1].isdigit())
        return ((s[:-1], s[-1]))


def merge_pdb_range_pairs(prs):
    '''Takes in a list of PDB residue IDs (including insertion codes) specifying ranges and returns a sorted list of merged, sorted ranges.
       This works as above but we have to split the residues into pairs as  "1A" > "19".
    '''
    new_prs = []
    sprs = [sorted((split_pdb_residue(p[0]), split_pdb_residue(p[1]))) for p in prs]
    sprs = sorted(sprs)
    merged = False
    x = 0
    from klab import colortext
    while x < len(sprs):
        newx = x + 1
        new_pair = list(sprs[x])
        for y in range(x + 1, len(sprs)):
            if new_pair[0] <= (sprs[y][0][0] - 1, sprs[y][0][1]) <= new_pair[1]:
                new_pair[0] = min(new_pair[0], sprs[y][0])
                new_pair[1] = max(new_pair[1], sprs[y][1])
                newx = y + 1
        if new_pair not in new_prs:
            new_prs.append(new_pair)
        x = newx
    return new_prs


if __name__ == '__main__':
    class BadException(Exception): pass
    assert(parse_range('5,12..15,17', range_separator = '..') == [5] + range(12,16) + [17])
    assert(parse_range('5-15,17') == range(5,16) + [17])
    assert(parse_range('1,3-10,12') == [1] + range(3, 11) + [12])
    try:
        assert(parse_range('5.3-15,17') == range(5,16) + [17])
        raise BadException()
    except BadException: raise
    except Exception: pass

    assert(parse_range_pairs('3,5-15,17') == ((3, 3), (5, 15), (17, 17)))
    assert(parse_range_pairs('3,15-5,17') == ((3, 3), (5, 15), (17, 17)))
    assert(parse_range_pairs('3,15-5,17', convert_to_tuple = False) == [[3, 3], [5, 15], [17, 17]])

    assert(merge_range_pairs([(2,2), (3,86)]) == [[2, 86]])
    assert(merge_range_pairs([(2,2), (3,86), (89,100)]) == [[2, 86], [89, 100]])
    assert(merge_range_pairs([(2,2), (3,86), (5,7), (81,88)]) == [[2, 88]])
    assert(merge_range_pairs([(2,2), (-7, -9), (-10,-7), (-1, 4), (3, 10)]) == [[-10, -7], [-1,10]])
