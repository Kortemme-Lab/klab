import openbabel as ob

def read_molecules(filepath, single = False):
    in_format = filepath.strip().split( '.' )[-1]
    obconversion = ob.OBConversion()
    obconversion.SetInFormat( in_format )
    obmol = ob.OBMol()

    molecules = []

    notatend = obconversion.ReadFile( obmol, filepath )
    while notatend:
        molecules.append( obmol )
        obmol = ob.OBMol()
        notatend = obconversion.Read( obmol )

    if single:
        assert( len(molecules) == 1 )
        return molecules[0]
    else:
        return molecules

def write_molecule(mol, path, output_format = None):
    if output_format == None:
        output_format = path.strip().split('.')[-1]

    obconversion = ob.OBConversion()
    obconversion.SetOutFormat(output_format)

    with open(path, 'w') as f:
        f.write( obconversion.WriteString(mol) )
