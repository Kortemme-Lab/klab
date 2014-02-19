import sys
sys.path.insert(0, '../../..')

from tools.bio.pymol.psebuilder import *

b = BatchBuilder()
structures = PDBContainer.from_filename_triple((
    ('Scaffold', '1z1s_DIG5_scaffold.pdb', ['A60', 'A61', 'A62', 'A63', 'A64', 'A65', 'A66', 'A67']),
    ('Design', 'DIG5_1_model.pdb', ['A60', 'A61', 'A62', 'A63', 'A64', 'A65', 'A66', 'A67']),
))

print(structures)
b.run(ScaffoldDesignCrystalBuilder, [structures])