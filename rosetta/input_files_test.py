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
                           '3 - 20 A APOLAR\n' + \
                           '22 - 23 A PIKAA ASDF\n' + \
                           '25 A PIKAA Y\n' + \
                           '30 B NATAA\n' + \
                           'C A NATAA\n'

        self.write_temp_resfile(resfile_contents)

        designable_range = range(3, 21) + [22, 23, 25]
        packable_range = designable_range + [30]
        self.assertListEqual(self.rf.designable, designable_range)
        self.assertListEqual(self.rf.packable, packable_range)

    def test_init_from_simple_resfile(self):
        resfile_contents = 'NATRO\nSTART\n\n3 A NATAA\n'

        self.write_temp_resfile(resfile_contents)

        self.assertListEqual(self.rf.designable, [])
        self.assertListEqual(self.rf.packable, [3])

  #   self.assertEqual('foo'.upper(), 'FOO')

  # def test_isupper(self):
  #     self.assertTrue('FOO'.isupper())
  #     self.assertFalse('Foo'.isupper())

  # def test_split(self):
  #     s = 'hello world'
  #     self.assertEqual(s.split(), ['hello', 'world'])
  #     # check that s.split fails when the separator is not a string
  #     with self.assertRaises(TypeError):
  #         s.split(2)

if __name__ == '__main__':
    unittest.main()
