#!/usr/bin/python
# encoding: utf-8
"""
input_files.py
Simple parsers for Rosetta input file types.

Created by Shane O'Connor 2014
"""

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

def parse_loop_file(contents, ignore_whitespace = True, ignore_errors = True):
    '''This parser is forgiving and allows leading whitespace.'''
    records = []
    for l in contents.strip().split('\n'):
        if ignore_whitespace:
            l = l.strip()
        tokens = l.split()
        if len(tokens) < 4:
            if ignore_errors:
                continue
            else:
                raise RosettaFileParsingException('Lines in a loops file must have at least four entries.')
        if tokens[0] != 'LOOP':
            raise RosettaFileParsingException('Lines in a loops file must start with the keyword "LOOP".')
        try:
            res_numbers = map(int, tokens[1:4])
        except:
            raise RosettaFileParsingException('Integers are expected in columns 2-4 of loops files.')

        skip_rate = None
        if len(tokens) > 4:
            try:
                skip_rate = float(tokens[4])
            except:
                raise RosettaFileParsingException('The skip rate in column 5 is expected to be a floating-point number.')

        extend_loop = False
        if len(tokens) > 5:
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
        if not((d['start'] <= d['cut_point'] <= d['end']) and (d['start'] < d['end'])):
            raise RosettaFileParsingException('The cut point must lie between the start and end residues and the start and end residues must differ.')
        records.append(d)
    return records


if __name__ == '__main__':

    for r in parse_loop_file('''
LOOP 23 30 26
LOOP 26 27 27 4
LOOP 23 30 26 2 TrUe
'''):
        print(r)