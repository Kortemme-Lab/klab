# Run from main klab directory like:
# python -m unittest rosetta.input_files_test

import input_files

import os
import tempfile
import unittest
from bio.basics import SimpleMutation

class TestResfile(unittest.TestCase):

    def setUp(self):
        self.resfile_contents = 'NATRO\nSTART\n\n' + \
                           '3 - 20 A ALLAA\n' + \
                           '22 - 23 A PIKAA ASDF\n' + \
                           '25 A PIKAA Y\n' + \
                           '27 A NOTAA C\n' + \
                           '30B B NATAA\n' + \
                           '* C NATAA\n'

        self.write_temp_resfile(self.resfile_contents)

    def tearDown(self):
        os.remove(self.temp_resfile)

    def write_temp_resfile(self, resfile_contents):
        self.temp_resfile = None
        with tempfile.NamedTemporaryFile(delete = False) as f:
            self.temp_resfile = f.name
            f.write(resfile_contents)

        self.rf = input_files.Resfile(self.temp_resfile)

    def test_init_from_resfile(self):
        designable_range = range(3, 21) + [22, 23, 25, 27]
        packable_range = designable_range + ['30B']
        designable_range_str = sorted([str(x) for x in designable_range])
        packable_range_str = sorted([str(x) for x in packable_range])

        self.assertListEqual(self.rf.designable, designable_range_str)
        self.assertListEqual(self.rf.packable, packable_range_str)

        self.assertListEqual(self.rf.global_commands, ['NATRO'])

        design = { 'A' : designable_range_str }
        repack = { 'B' : ['30B'], 'C' : ['*'] }
        self.assertDictEqual(self.rf.design_positions, design)
        self.assertDictEqual(self.rf.repack_positions, repack)

        for chain in self.rf.design:
            for resnum in self.rf.design[chain]:
                resnum_int = int(resnum)
                if resnum_int >= 3 and resnum_int <= 20:
                    self.assertEqual(self.rf.design[chain][resnum], self.rf.allaa_set)
                elif resnum_int == 22 or resnum_int == 23:
                    self.assertEqual(self.rf.design[chain][resnum], set(['A', 'S', 'D', 'F']))
                elif resnum_int == 25:
                    self.assertEqual(self.rf.design[chain][resnum], set(['Y']))
                elif resnum_int == 27:
                    check_set = set(self.rf.allaa_set)
                    check_set.remove('C')
                    self.assertEqual(self.rf.design[chain][resnum], check_set)

    def test_init_from_simple_resfile(self):
        # This mostly tests what the Resfile class in input_files did
        # before the commits of July 21 2015
        os.remove(self.temp_resfile) # Remove default resfile created by setUp
        resfile_contents = 'NATRO\nSTART\n\n3 A NATAA\n'

        self.write_temp_resfile(resfile_contents)

        self.assertListEqual(self.rf.global_commands, ['NATRO'])

        self.assertListEqual(self.rf.designable, [])
        self.assertListEqual(self.rf.packable, ['3'])

    def test_init_from_mutageneses(self):
        mutations = [
            SimpleMutation('A', '1', 'S', 'Z'),
            SimpleMutation('P', '3', 'W', 'Z')
        ]

        rf = input_files.Resfile.from_mutageneses(mutations)

        designable_range = ['1', '3']
        packable_range = ['1', '3']
        self.assertListEqual(rf.designable, designable_range)
        self.assertListEqual(rf.packable, packable_range)

        self.assertListEqual(rf.global_commands, ['NATRO'])

        design = { 'Z' : designable_range }
        repack = {}
        self.assertDictEqual(rf.design_positions, design)
        self.assertDictEqual(rf.repack_positions, repack)

        self.assertDictEqual(rf.design, {'Z': {'1': set(['S']), '3': set(['W'])}} )
        self.assertDictEqual(rf.repack, {})

    def test_repr(self):
        original_rf_repr = str(self.rf)
        original_rf = self.rf
        os.remove(self.temp_resfile) # Remove default resfile created by setUp
        self.write_temp_resfile(original_rf_repr)
        self.assertMultiLineEqual(original_rf_repr, str(self.rf))
        self.assertEquals(original_rf, self.rf)

    def test_chains(self):
        self.assertListEqual(self.rf.chains, ['A', 'B', 'C'])

    def test_residues(self):
        self.assertListEqual(self.rf.residues,
                             sorted(['3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15',
                              '16', '17', '18', '19', '20', '22', '23', '25', '27', '30B', '*'])
        )
    # def test_design_or_repack_dict(self):
    #     print self.rf.design_or_repack_dict

if __name__ == '__main__':
    unittest.main()
