import sys
import os
import time
import pprint

sys.path.insert(0, os.path.join('..', '..'))

from klab import colortext
from klab.bio.cache import PDBCache


# Simple test
colortext.message('\nSimple test')
c = PDBCache(max_capacity = 10)
for x in xrange(100):
    c.add_pdb_contents('%04d' % x, str(x * x - 1))
pprint.pprint(c.pdb_contents)
time.sleep(0.010)

# PDB test
colortext.message('\nPDB test')
c = PDBCache(cache_dir = '/tmp', max_capacity = None)
for pdb_id in ['1A22', '1A4Y', '1ACB', '1AHW', '1AK4', '1BRS', '1CBW']:
    c.get_pdb_contents(pdb_id)
pprint.pprint(c.pdb_contents) # there should be 7 PDBs
assert(sorted(c.pdb_contents.keys()) == sorted(['1A22', '1A4Y', '1ACB', '1AHW', '1AK4', '1BRS', '1CBW']))

c.max_capacity = 4
c.get_pdb_contents('1CHO') # this should get the new PDB and truncate the list to 4 elements
pprint.pprint(c.pdb_contents) # there should be 4 PDBs
assert(sorted(c.pdb_contents.keys()) == sorted(['1AK4', '1BRS', '1CBW', '1CHO']))

# Re-read in an old file which was thrown away above - this should trigger another file read and erase an older entry
c.get_pdb_contents('1A22')
pprint.pprint(c.pdb_contents) # there should be 4 PDBs
assert(sorted(c.pdb_contents.keys()) == sorted(['1BRS', '1CBW', '1CHO', '1A22']))

# Re-read in an old file which was thrown away above - this should trigger another file read and erase an older entry
c.get_pdb_contents('1BRS') # refresh the access time for 1BRS, currently the oldest file in the cache
c.get_pdb_contents('1A4Y') # read in a new (relative to the cache contents) PDB file. This should kick out the oldest file which is not '1CBW'
pprint.pprint(c.pdb_contents) # there should be 4 PDBs
assert(sorted(c.pdb_contents.keys()) == sorted(['1BRS', '1CHO', '1A22', '1A4Y']))
