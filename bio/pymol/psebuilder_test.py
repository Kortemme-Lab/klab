import sys
sys.path.insert(0, '../../..')

from tools.bio.pymol.psebuilder import *

b = BatchBuilder()
structures = PDBContainer.from_filename_tuples(
    ('Scaffold', '1z1s_DIG5_scaffold.pdb'),
    ('Design', 'DIG5_1_model.pdb'),
)
b.run(GenericBuilder, structures)