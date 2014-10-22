#!/usr/bin/python
# encoding: utf-8
"""
input_files.py
Simple parsers for Rosetta input file types.

Created by Shane O'Connor 2014
"""

from fs.fsio import read_file

class RosettaFileParsingException(Exception): pass


# Loops file
# From https://www.rosettacommons.org/docs/latest/loops-file.html
# column1  "LOOP":     Literally the string LOOP, identifying this line as a loop
#                      In the future loop specification files may take other data.
# column2  "integer":  Loop start residue number
# column3  "integer":  Loop end residue number
# column4  "integer":  Cut point residue number, >=startRes, <=endRes. Default or 0: let LoopRebuild choose cutpoint randomly.
# column5  "float":    Skip rate. default - never skip
# column6  "boolean":  Extend loop. Default false

class RosettaFileParsingException(Exception): pass

class LoopsFile(object):
    '''A class to manipulate loops files. Note that the indices in these files are 1-indexed i.e. A start position of 5
        refers to the fifth residue of the sequence.'''


    @staticmethod
    def from_filepath(filepath, ignore_whitespace = True, ignore_errors = False):
        return LoopsFile(read_file(filepath), ignore_whitespace = ignore_whitespace, ignore_errors = ignore_errors)


    def __init__(self, contents, ignore_whitespace = True, ignore_errors = False):
        self.data = []
        self.parse_loops_file(contents, ignore_whitespace = ignore_whitespace, ignore_errors = ignore_errors)


    def parse_loops_file(self, contents, ignore_whitespace = True, ignore_errors = False):
        '''This parser is forgiving and allows leading whitespace.'''
        for l in contents.strip().split('\n'):
            try:
                if ignore_whitespace:
                    l = l.strip()
                tokens = l.split()
                if len(tokens) < 3:
                    raise RosettaFileParsingException('Lines in a loops file must have at least three entries.')
                if len(tokens) < 4:
                    tokens.append(None)
                self.data.append(self.parse_loop_line(tokens))
            except:
                if ignore_errors:
                    continue
                else:
                    raise
        return self.data


    def parse_loop_line(self, tokens):
        if tokens[0] != 'LOOP':
            raise RosettaFileParsingException('Lines in a loops file must start with the keyword "LOOP".')
        try:
            if tokens[3] == None:
                tokens[3] = 0 # add the default cut point residue number
            res_numbers = map(int, tokens[1:4])
            if min(res_numbers) < 0:
                raise RosettaFileParsingException('The cut point and start and end residues indices must be positive integers.')
            if not(((res_numbers[2] == 0) or res_numbers[0] <= res_numbers[2] <= res_numbers[1]) and (res_numbers[0] < res_numbers[1])):
                raise RosettaFileParsingException('The cut point must lie between the start and end residues and the start and end residues must differ.')
        except:
            raise RosettaFileParsingException('Integers are expected in columns 2-4 of loops files.')

        skip_rate = None
        if len(tokens) > 4 and tokens[4] != None:
            try:
                skip_rate = float(tokens[4])
            except:
                raise RosettaFileParsingException('The skip rate in column 5 is expected to be a floating-point number.')

        extend_loop = False
        if len(tokens) > 5 and tokens[5] != None:
            extend_loop = tokens[5].lower() # allow some typos
            if extend_loop not in ['true', 'false']:
                raise RosettaFileParsingException('The extend loop argument in column 6 is expected to be "true" or "false".')
            extend_loop = extend_loop == 'true'

        d = dict(
            start = res_numbers[0],
            end = res_numbers[1],
            cut_point = res_numbers[2],
            skip_rate = skip_rate,
            extend_loop = extend_loop
        )
        return d


    def add(self, start, end, cut_point = None, skip_rate = None, extend_loop = None):
        '''Add a new loop definition.'''
        self.data.append(self.parse_loop_line(['LOOP', start, end, cut_point, skip_rate, extend_loop]))
        assert(start < end)


    def get_distinct_segments_from_loops_file(self):
        '''Returns a list of segments (pairs of start and end positions) based on the loop definitions. The returned segments
            merge overlapping loops e.g. if the loops file contains sections 32-40, 23-30, 28-33, and 43-46 then the returned
            segments will be [(23, 40), (43, 46)].
            This may not be the fastest way to calculate this (numpy?) but that is probably not an issue.
        '''

        # Create a unique, sorted list of all loop terminus positions
        positions = set()
        for l in self.data:
            assert(l['start'] < l['end'])
            positions = positions.union(range(l['start'], l['end'] + 1))
        positions = sorted(positions)

        # Iterate through the list to define the segments
        segments = []
        current_start = None
        last_position = None
        for p in positions:
            if current_start == None:
                current_start = p
                last_position = p
            else:
                if p == last_position + 1:
                    last_position = p
                else:
                    segments.append((current_start, last_position))
                    current_start = p
                    last_position = p
        if current_start and last_position:
            segments.append((current_start, last_position))
        return segments


if __name__ == '__main__':

    p = LoopsFile('''
LOOP 23 30
LOOP -1 30 26
LOOP 26 23 27 4
LOOP 23 30 26 2 TrUe
''',ignore_errors = True)
    for r in p.data:
        print(r)
