import sys
sys.path.insert(0, "../..")
from tools.bio.pdb import PDB
from tools.fs.io import read_file
from tools import colortext

from pdbml import PDBML

px = PDBML(read_file('../.testdata/1A2C.xml'), read_file('../.testdata/1A2C.pdb'))
print(px.xml_version)
sys.exit(0)

p = PDB('../.testdata/1H38.pdb')
p = PDB('../.testdata/1ZC8.pdb')
p = PDB('../.testdata/4IHY.pdb')
#p = PDB('../.testdata/2GRB.pdb')
p = PDB('../.testdata/1J1M.pdb')
p = PDB('../.testdata/1H38.pdb')
#print(p.structure_lines)

colortext.message("Resolution")
print(p.get_resolution())

colortext.message("Techniques")
print(p.get_techniques())

colortext.message("References")
refs = p.get_DB_references()
for pdb_id, details in sorted(refs.iteritems()):
    print(pdb_id)
    for db, chain_details in sorted(details.iteritems()):
        print("  %s" % db)
        for chain_id, subdetails in sorted(chain_details.iteritems()):
            print("    Chain %s" % chain_id)
            for k, v in sorted(subdetails.iteritems()):
                if k == 'PDBtoDB_mapping':
                    print("      PDBtoDB_mapping:")
                    for mpng in v:
                        print("          dbRange :  %s -> %s" % (mpng['dbRange'][0].rjust(5), mpng['dbRange'][1].ljust(5)))
                        print("          PDBRange:  %s -> %s" % (mpng['PDBRange'][0].rjust(5), mpng['PDBRange'][1].ljust(5)))

                else:
                    print("      %s: %s" % (k, v))


colortext.message("Molecule information")
molecules = p.get_molecules_and_source()
for m in molecules:
    colortext.warning("Molecule %d" % m['MoleculeID'])
    for k, v in m.iteritems():
        if k != 'MoleculeID':
            print("  %s: %s" % (k,v))

colortext.message("Journal information")
for k,v in p.get_journal().iteritems():
    print("%s : %s" % (k.ljust(20), v))

colortext.message("PDB format version")
print(p.format_version)

sys.exit(0)

colortext.message("SEQRES sequences")
sequences, chains_in_order = p.get_SEQRES_sequences()
for chain_id in chains_in_order:
    colortext.warning("%s (%s)" % (chain_id, p.chain_types[chain_id]))
    print(sequences[chain_id])

colortext.message("get_all_sequences")
print(p.get_all_sequences('~/Rosetta3.5/rosetta_source/build/src/release/linux/3.8/64/x86/gcc/4.7/default/rosetta_scripts.default.linuxgccrelease', '~/Rosetta3.5/rosetta_database/', False))

#print(p.get_pdb_to_rosetta_residue_map('/guybrushhome/Rosetta3.5/rosetta_source/build/src/release/linux/3.8/64/x86/gcc/4.7/default/rosetta_scripts.default.linuxgccrelease', '/guybrushhome/Rosetta3.5/rosetta_database/', False))


sys.exit(0)

colortext.message("GetRosettaResidueMap")
print(p.GetRosettaResidueMap())


colortext.message("Chains")
print(",".join(p.get_ATOM_and_HETATM_chains()))


sys.exit(0)

for testpdb in ['2GRB', '4IHY', '1ZC8', '1H38']:
    p = PDB('../.testdata/%s.pdb' % testpdb)
    colortext.message("SEQRES sequences for %s" % testpdb)
    sequences, chains_in_order = p.get_SEQRES_sequences()
    for chain_id in chains_in_order:
        colortext.warning("%s (%s)" % (chain_id, p.chain_types[chain_id]))
        print(sequences[chain_id])


p = PDB('../.testdata/2GRB.pdb')
sequences, chains_in_order = p.get_SEQRES_sequences()
assert(p.chain_types['A'] == 'RNA')
assert(sequences['A'] == 'UGIGGU')

p = PDB('../.testdata/4IHY.pdb')
sequences, chains_in_order = p.get_SEQRES_sequences()
assert(p.chain_types['A'] == 'Protein')
assert(p.chain_types['C'] == 'DNA')
assert(sequences['C'] == 'AAATTTGTTTGIICICTGAGCAAATTT')

p = PDB('../.testdata/1ZC8.pdb')
sequences, chains_in_order = p.get_SEQRES_sequences()
assert(p.chain_types['K'] == 'Protein')
assert(p.chain_types['I'] == 'DNA')
assert(p.chain_types['F'] == 'RNA')
assert(sequences['F'] == 'CUUUAGCAGCUUAAUAACCUGCUUAGAGC')
assert(sequences['I'] == 'AUCGCGUGGAAGCCCUGCCUGGGGUUGAAGCGUUAAAACUUAAUCAGGC')

p = PDB('../.testdata/1H38.pdb')
sequences, chains_in_order = p.get_SEQRES_sequences()
assert(p.chain_types['D'] == 'Protein')
assert(p.chain_types['E'] == 'DNA')
assert(p.chain_types['F'] == 'RNA')
assert(sequences['E'] == 'GGGAATCGACATCGCCGC')
assert(sequences['F'] == 'AACUGCGGCGAU')
