#!/usr/bin/python
# encoding: utf-8
"""
input_files.py
Simple parsers for Rosetta input file types.

Created by Shane O'Connor 2014
"""

import pprint
import re

if __name__ == '__main__':
    import sys
    sys.path.insert(0, '../..')
    from tools.fs.fsio import read_file
    from tools.bio.basics import SimpleMutation
    from tools.general.strutil import parse_range
else:
    from fs.fsio import read_file
    from bio.basics import SimpleMutation
    from general.strutil import parse_range


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
        for l in [l for l in contents.strip().split('\n') if l]:
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


    def parse_loop_line(self, tokens):
        if tokens[0] != 'LOOP':
            raise RosettaFileParsingException('Lines in a loops file must start with the keyword "LOOP".')
        try:
            if tokens[3] == None:
                tokens[3] = 0 # add the default cut point residue number
            res_numbers = map(int, tokens[1:4])
            if min(res_numbers) < 0:
                raise RosettaFileParsingException('The cut point and start and end residues indices must be positive integers.')
            if not((res_numbers[2] == 0) or res_numbers[0] <= res_numbers[2] <= res_numbers[1]):
                raise RosettaFileParsingException('The cut point must lie between the start and end residues.')
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
            if extend_loop not in ['1', '0', 'true', 'false']:
                raise RosettaFileParsingException('The extend loop argument in column 6 is expected to be "true", "false", "0", or "1".')
            extend_loop = extend_loop == '1' or extend_loop == 'true'

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
        assert(start <= end)


    def get_distinct_segments(self, left_offset = 0, right_offset = 0, sequence_length = None):
        '''Returns a list of segments (pairs of start and end positions) based on the loop definitions. The returned segments
            merge overlapping loops e.g. if the loops file contains sections 32-40, 23-30, 28-33, and 43-46 then the returned
            segments will be [(23, 40), (43, 46)].
            This may not be the fastest way to calculate this (numpy?) but that is probably not an issue.

            The offsets are used to select the residues surrounding the loop regions. For example, i.e. if a sequence segment
            is 7 residues long at positions 13-19 and we require 9-mers, we must consider the segment from positions 5-27 so
            that all possible 9-mers are considered.
        '''

        # Create a unique, sorted list of all loop terminus positions
        positions = set()
        for l in self.data:
            assert(l['start'] <= l['end'])
            if sequence_length:
                # If we know the sequence length then we can return valid positions
                positions = positions.union(range(max(1, l['start'] - left_offset + 1), min(sequence_length + 1, l['end'] + 1 + right_offset - 1))) # For clarity, I did not simplify the expressions. The left_offset requires a +1 to be added, the right_offset requires a -1 to be added. The right offset also requires a +1 due to the way Python splicing works.
            else:
                # Otherwise, we may return positions outside the sequence length however Python splicing can handle this gracefully
                positions = positions.union(range(max(1, l['start'] - left_offset + 1), l['end'] + 1 + right_offset - 1)) # For clarity, I did not simplify the expressions. The left_offset requires a +1 to be added, the right_offset requires a -1 to be added. The right offset also requires a +1 due to the way Python splicing works.
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


class SecondaryStructureDefinition(object):
    '''A class to manipulate secondary structure assignment files. These files are not standard Rosetta files; we use them
       for our fragment generation. For that reason, they may change over time until we fix on a flexible format. The
       indices in these files are 1-indexed and use Rosetta numbering i.e. if the first chain has 90 residues and the second
       has 40 residues, a position of 96 refers to the sixth residue of the second chain. The file format is whitespace-separated
       columns. The first column is a residue ID or a residue range. The second column is a string consisting of characters
       'H', 'E', and 'L', representing helix, sheet, and loop structure respectively.
       Comments are allowed. Lines with comments must start with a '#' symbol.
       Example file:
         1339 HEL
         # An expected helix
         1354-1359 H
         # Helix or sheet structure
         1360,1370-1380 HE
       '''

    @staticmethod
    def from_filepath(filepath, ignore_whitespace = True, ignore_errors = False):
        return SecondaryStructureDefinition(read_file(filepath))


    def __init__(self, contents):
        self.data = {}
        self.parse_ss_def_file(contents)


    def parse_ss_def_file(self, contents):
        '''This parser is forgiving and allows leading whitespace.'''
        mapping = {}
        for l in [l.strip() for l in contents.split('\n') if l.strip() and not(l.strip().startswith('#'))]:
            tokens = l.split()
            if len(tokens) != 2:
                raise RosettaFileParsingException('Lines in a secondary structure definition file must have exactly two entries.')

            positions = parse_range(tokens[0])
            ss = sorted(set(tokens[1].upper()))
            for p in positions:
                if mapping.get(p) and mapping[p] != ss:
                    raise RosettaFileParsingException('There are conflicting definitions for residue %d (%s and %s).' % (p, ''.join(mapping[p]), ''.join(ss)))
                mapping[p] = ss
        self.data = mapping


class Resfile (object):
    # Contains no support for noncanonical commands
    # Contains no support for insertion codes

    def __init__(self, input_resfile = None, input_mutageneses = None):
        self.allaa = 'ACDEFGHIKLMNPQRSTVWY'
        self.allaa_set = set()
        for aa in self.allaa:
            self.allaa_set.add(aa)
            
        self.polar = 'DEHHKNQRST'
        self.polar_set = set()
        for aa in self.polar:
            self.polar_set.add(aa)
            
        self.apolar = 'ACFGILMPVWY'
        self.apolar_set = set()
        for aa in self.apolar:
            self.apolar_set.add(aa)
        
        self.design = {}
        self.repack = {}
        self.global_commands = []
        
        if input_resfile:
            self.__init_from_file(input_resfile)
        elif input_mutageneses:
            raise Exception("Not yet implemented")
        else:
            raise Exception("The Resfile __init__ function needs either an input resfile argument or mutageneses")

    def __init_from_file(self, filename):
        index_pattern = '^(\d+)\s+'
        range_pattern = '^(\d+)\s+[-]\s+(\d+)\s+'
        wildcard_pattern = '^[*]\s+'
        command_pattern = '({}|{}|{})([A-Z])\s+([A-Z]+)\s*([A-Z]*)'.format(
            index_pattern, range_pattern, wildcard_pattern)

        before_start = True
        with open(filename) as file:
            for line in file:
                if before_start:
                    if line.lower().startswith('start'):
                        before_start = False
                    else:
                        self.global_commands.append( line.strip() )
                else:
                    index_match = re.match(index_pattern, line)
                    range_match = re.match(range_pattern, line)
                    wildcard_match = re.match(wildcard_pattern, line)
                    command_match = re.match(command_pattern, line)

                    if not command_match: continue

                    command = command_match.groups()[5].upper()
                    chain = command_match.groups()[4].upper()

                    if command_match.groups()[2]:
                        range_start = int(command_match.groups()[2])
                    else:
                        range_start = None

                    if command_match.groups()[3]:
                        range_end = int(command_match.groups()[3])
                    else:
                        range_end = None

                    if command_match.groups()[1]:
                        range_singleton = int(command_match.groups()[1])
                    else:
                        range_singleton = None

                    # Process chain/residue range
                    new_residues = []

                    if range_start and range_end:
                        new_residues.extend( range(range_start, range_end+1) )
                    elif range_singleton:
                        new_residues.append( range_singleton )
                    elif wildcard_match:
                        new_residues.append( '*' )
                    else:
                        raise Exception('No reference to residue number or range found')

                    if command == 'NATRO':
                        # Useless do-nothing command
                        continue
                    elif command == 'NATAA':
                        # Repack only command
                        if chain not in self.repack:
                            self.repack[chain] = []
                        self.repack[chain].extend( new_residues )
                    else:
                        # Design command
                        if chain not in self.design:
                            self.design[chain] = {}
                        for resnum in new_residues:
                            if command == 'ALLAA':
                                self.design[chain][resnum] = self.allaa_set
                            elif command == 'PIKAA':
                                allowed_restypes = set()
                                for restype in command_match.groups()[6].upper():
                                    allowed_restypes.add(restype)
                                self.design[chain][resnum] = allowed_restypes
                            elif command == 'NOTAA':
                                allowed_restypes = set(self.allaa_set)
                                for restype in command_match.groups()[6].upper():
                                    allowed_restypes.remove(restype)
                                self.design[chain][resnum] = allowed_restypes
                            elif command == 'POLAR':
                                self.design[chain][resnum] = self.polar_set
                            elif command == 'APOLAR':
                                self.design[chain][resnum] = self.apolar_set
                            else:
                                raise Exception("Error: command %s not recognized" % command)
    
    @property
    def designable(self):
        # This method only returns residue numbers, and nothing to do with chains
        # Any wild card chain commands will be ignored by this function
        return_list = []
        for chain in self.design:
            for residue in self.design[chain]:
                if residue != '*':
                    return_list.append(residue)
        return sorted(return_list)

    @property
    def packable(self):
        # This method only returns residue numbers, and nothing to do with chains
        # Any wild card chain commands will be ignored by this function
        return_list = []
        for chain in self.repack:
            for residue in self.repack[chain]:
                if residue != '*':
                    return_list.append(residue)
        return sorted(return_list + self.designable)

    @property
    def design_positions(self):
        return_dict = {}
        for chain in self.design:
            return_dict[chain] = sorted(self.design[chain].keys())
        return return_dict

    @property
    def repack_positions(self):
        return self.repack
    
    @staticmethod
    def from_mutagenesis(mutations):
        '''This is a special case (the common case) of from_mutations where there is only one mutagenesis/mutation group.'''
        return Resfile.from_mutageneses([mutations])

    @staticmethod
    def from_mutageneses(mutation_groups):
        '''mutation_groups is expected to be a list containing lists of SimpleMutation objects.'''
        return Resfile(input_mutageneses = mutation_groups)

class Mutfile (object):
    '''Note: This class behaves differently to Resfile. It stores mutation information using the SimpleMutation class.

       Rosetta mutfiles are text files split into sections where each section contains a number of mutations i.e. each
       section defines one mutagenesis.
       Mutfile objects represent the contents of these files by storing the mutations as a list of SimpleMutation lists.
    '''

    header_pattern = '^total\s+(\d+)\s*(?:#.*)?$'
    mutation_group_header_pattern = '^\s*(\d+)\s*(?:#.*)?$'
    mutation_pattern = '^\s*([A-Z])\s+(\d+)\s+([A-Z])\s*(?:#.*)?$'


    @staticmethod
    def from_file(filepath):
        return Mutfile(open(filepath).read())


    @staticmethod
    def from_mutagenesis(mutations):
        '''This is a special case (the common case) of from_mutations where there is only one mutagenesis/mutation group.'''
        return Mutfile.from_mutageneses([mutations])


    @staticmethod
    def from_mutageneses(mutation_groups):
        '''mutation_groups is expected to be a list containing lists of SimpleMutation objects.'''
        mf = Mutfile()
        mf.mutation_groups = mutation_groups
        return mf


    def __repr__(self):
        '''Creates a mutfile from the set of mutation groups.'''
        s = []

        # Header
        total_number_of_mutations = sum([len(mg) for mg in self.mutation_groups])
        s.append('total %d' % total_number_of_mutations)

        # Mutation groups
        for mg in self.mutation_groups:
            assert(len(mg) > 0)
            s.append('%d' % len(mg))
            # Mutation list
            for m in mg:
                s.append('%(WildTypeAA)s %(ResidueID)d %(MutantAA)s' % m.__dict__)

        s.append('')
        return '\n'.join(s)


    def __init__(self, mutfile_content = None):

        self.mutation_groups = []
        if mutfile_content:
            # Parse the file header
            mutfile_content = mutfile_content.strip()
            data_lines = [l for l in mutfile_content.split('\n') if l.strip()]
            try:
                num_mutations = int(re.match(Mutfile.header_pattern, data_lines[0]).group(1))
            except:
                raise RosettaFileParsingException('The mutfile has a bad header (expected "total n" where n is an integer).')

            line_counter, mutation_groups = 1, []
            while True:
                if line_counter >= len(data_lines):
                    break

                mutation_group_number = len(mutation_groups) + 1

                # Parse the group header
                try:
                    group_header = data_lines[line_counter]
                    line_counter += 1
                    num_mutations_in_group = int(re.match(Mutfile.mutation_group_header_pattern, group_header).group(1))
                    if num_mutations_in_group < 1:
                        raise RosettaFileParsingException('The mutfile has a record in mutation group %d: the number of reported mutations must be an integer greater than zero.' % mutation_group_number)
                except:
                    raise RosettaFileParsingException('The mutfile has a bad header for mutation group %d.' % mutation_group_number)

                # Parse the mutations in the group
                try:
                    mutations = []
                    for mutation_line in data_lines[line_counter: line_counter + num_mutations_in_group]:
                        mtch = re.match(Mutfile.mutation_pattern, mutation_line)
                        mutations.append(SimpleMutation(mtch.group(1), int(mtch.group(2)), mtch.group(3)))
                    mutation_groups.append(mutations)
                    line_counter += num_mutations_in_group
                except:
                    raise RosettaFileParsingException('An exception occurred while parsing the mutations for mutation group %d.' % mutation_group_number)

            if sum([len(mg) for mg in mutation_groups]) != num_mutations:
                raise RosettaFileParsingException('A total of %d mutations were expected from the file header but the file contained %d mutations.' % (num_mutations, sum([len(mg) for mg in mutation_groups])))

            self.mutation_groups = mutation_groups


    def get_total_mutation_count(self):
        return sum([len(mg) for mg in self.mutation_groups])




if __name__ == '__main__':

    p = LoopsFile('''
LOOP 23 30
LOOP -1 30 26
LOOP 26 23 27 4
LOOP 23 30 26 2 TrUe
''',ignore_errors = True)
    for r in p.data:
        print(r)

    ss = SecondaryStructureDefinition('''
# Comments are allowed. A line has two columns: the first specifies the residue(s),
# the second specifies the expected secondary structure using H(elix), E(xtended/sheet),
# or L(oop). The second column is case-insensitive.
#
# A single residue, any structure
1339 Hel
# An expected helix
1354-1359 H
# A helical or sheet structure
1360,1370-1380 HE
        ''')
    for p, ss_def in sorted(ss.data.iteritems()):
        print('%s: %s' % (p, ''.join(ss_def)))


    mf = Mutfile('''
total 3 #this is the total number of mutations being made.
2 # the number of mutations made
G 1 A # the wild-type aa, the residue number, and the mutant aa
W 6 Y # the wild-type aa, the residue number, and the mutant aa
1 #the number of mutations
F 10 Y # the wild-type aa, the residue number, and the mutant aa''')
    pprint.pprint(mf.mutation_groups)
    normalized_content = str(mf)
    print(normalized_content)
    mf = Mutfile(normalized_content)
    pprint.pprint(mf.mutation_groups)
    normalized_content_2 = str(mf)
    assert(normalized_content_2 == normalized_content) # fixed-point check
