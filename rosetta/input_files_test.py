# Run from main tools directory like:
# python -m unittest rosetta.input_files_test

import input_files

import os
import tempfile
import unittest

class TestResfile(unittest.TestCase):

    def write_temp_resfile(self, resfile_contents):
        self.temp_resfile = None
        with tempfile.NamedTemporaryFile(delete = False) as f:
            self.temp_resfile = f.name
            f.write(resfile_contents)

        self.rf = input_files.Resfile(self.temp_resfile)

    def tearDown(self):
        os.remove(self.temp_resfile)
        self.temp_resfile = None
        
    def test_init_from_resfile(self):
        resfile_contents = 'NATRO\nSTART\n\n' + \
                           '3 - 20 A ALLAA\n' + \
                           '22 - 23 A PIKAA ASDF\n' + \
                           '25 A PIKAA Y\n' + \
                           '27 A NOTAA C\n' + \
                           '30 B NATAA\n' + \
                           '* C NATAA\n'

        self.write_temp_resfile(resfile_contents)

        designable_range = range(3, 21) + [22, 23, 25, 27]
        packable_range = designable_range + [30]
        self.assertListEqual(self.rf.designable, designable_range)
        self.assertListEqual(self.rf.packable, packable_range)

        self.assertListEqual(self.rf.global_commands, ['NATRO'])
        
        design = { 'A' : range(3, 21) + [22, 23, 25, 27] }
        repack = { 'B' : [30], 'C' : ['*'] }
        self.assertDictEqual(self.rf.design_positions, design)
        self.assertDictEqual(self.rf.repack_positions, repack)

        for chain in self.rf.design:
            for resnum in self.rf.design[chain]:
                if resnum >= 3 and resnum <= 20:
                    self.assertEqual(self.rf.design[chain][resnum], self.rf.allaa_set)
                elif resnum == 22 or resnum == 23:
                    self.assertEqual(self.rf.design[chain][resnum], set(['A', 'S', 'D', 'F']))
                elif resnum == 25:
                    self.assertEqual(self.rf.design[chain][resnum], set(['Y']))
                elif resnum == 27:
                    check_set = set(self.rf.allaa_set)
                    check_set.remove('C')
                    self.assertEqual(self.rf.design[chain][resnum], check_set)
                    
        
    def test_init_from_simple_resfile(self):
        # This mostly tests what the Resfile class in input_files did
        # before the commits of July 21 2015
        resfile_contents = 'NATRO\nSTART\n\n3 A NATAA\n'

        self.write_temp_resfile(resfile_contents)

        self.assertListEqual(self.rf.global_commands, ['NATRO'])

        self.assertListEqual(self.rf.designable, [])
        self.assertListEqual(self.rf.packable, [3])

if __name__ == '__main__':
    unittest.main()
