class Molecule:
    def __init__(self, pdb_path, molecule_name, chain = None):
        self.atom_types = []
        self.atom_type_nums = []
        self.coords = []
        self.molecule_name = molecule_name
        self.chain = chain
        self.lines = []
        self.resnum = None

        with open(pdb_path, 'r') as f:
            for line in f:
                residue_name = line[17:20].strip()
                if line.startswith('HETATM') and residue_name == self.molecule_name:
                    chain = line[21]
                    if self.chain and self.chain != chain:
                        continue

                    resnum = long( line[22:26].strip() )
                    if self.resnum == None:
                        self.resnum = resnum
                    else:
                        assert( resnum == self.resnum )

                    name = line[12:16].strip()
                    self.atom_types.append( name[0] )
                    self.atom_type_nums.append( name[1:] )

                    x = float( line[30:38].strip() )
                    y = float( line[38:46].strip() )

                    z = float( line[46:54].strip() )
                    self.names.append( name )
                    self.coords.append( (x, y, z) )
                    self.lines.append(line)

    def lines_to_write(self):
        coords_as_strings = self.coords_as_strings
        lines = []
        for i, line in enumerate(self.lines):
            if self.chain:
                chain = self.chain
            else:
                chain = line[21]
            lines.append(
                line[:21] + chain +
                string.rjust( '%d' % self.resnum, 4) +
                line[26:30] +
                coords_as_strings[i][0] +
                coords_as_strings[i][1] +
                coords_as_strings[i][2] +
                line[54:]
            )
        return lines

    def write_to_file(self, pdb_path, file_mode = 'w'):
        with open(pdb_path, file_mode) as f:
            for line in self.lines_to_write():
                f.write(line)

    @property
    def coords_as_strings(self):
        ret = []
        for coords in self.coords:
            x, y, z = coords
            x = '%.3f' % x
            y = '%.3f' % y
            z = '%.3f' % z

            x = string.rjust(x, 8)
            y = string.rjust(y, 8)
            z = string.rjust(z, 8)

            ret.append( (x, y, z) )
        return ret

    def get_coords_for_name(self, atom_name):
        index = self.get_index_for_name(atom_name)
        return self.coords[index]

    def set_coords_for_name(self, atom_name, new_coords):
        assert( len(new_coords) == 3 )
        index = self.get_index_for_name(atom_name)
        self.coords[index] = new_coords

    def get_index_for_name(self, atom_name):
        names = self.names
        names_set = set(names)
        assert( len(names) == len(names_set) )
        index = names.index(atom_name)
        return index

    @property
    def names(self):
        return [ '%s%s' % (x,y) for x,y in zip(self.atom_types, self.atom_type_nums) ]

    @property
    def names_set(self):
        s = set()
        for name in self.names:
            assert( name not in s )
            s.add(name)
        return s

    def align_to_other(self, other, mapping, self_root_pair, other_root_pair = None):
        '''
        root atoms are atom which all other unmapped atoms will be mapped off of
        '''
        if other_root_pair == None:
            other_root_pair = self_root_pair

        assert( len(self_root_pair) == 2 )
        assert( len(other_root_pair) == 2 )

        unmoved_atom_names = []
        new_coord0 = None
        new_coord1 = None
        for atom in self.names:
            if atom == self_root_pair[0]:
                assert( new_coord0 == None )
                new_coord0 = self.get_coords_for_name(atom)
            elif atom == self_root_pair[1]:
                assert( new_coord1 == None )
                new_coord1 = self.get_coords_for_name(atom)

            if atom in mapping:
                other_atom = mapping[atom]
                self.set_coords_for_name( atom, other.get_coords_for_name(other_atom) )
            else:
                unmoved_atom_names.append(atom)

        # Move unmoved coordinates after all other atoms have been moved (so that
        # references will have been moved already)
        assert( new_coord0 != None )
        assert( new_coord1 != None )
        ref_coord0 = other.get_coords_for_name( other_root_pair[0] )
        ref_coord1 = other.get_coords_for_name( other_root_pair[1] )

        # Calculate translation and rotation matrices
        U, new_centroid, ref_centroid = calc_rotation_translation_matrices( (ref_coord0, ref_coord1), (new_coord0, new_coord1) )
        for atom in unmoved_atom_names:
            original_coord = self.get_coords_for_name(atom)
            self.set_coords_for_name( atom, rotate_and_translate_coord(original_coord, U, new_centroid, ref_centroid) )
        self.chain = other.chain

    def replace_in_pdb(self, pdb_path, name_to_replace):
        # First pass to read lines, remove old molecule, and find position to insert
        lines = []
        position_to_insert = None
        with open(pdb_path, 'r') as f:
            for line in f:
                residue_name = line[17:20].strip()
                if len(line) >= 22:
                    chain = line[21]
                else:
                    chain = None
                if line.startswith('HETATM') and residue_name == name_to_replace and chain == self.chain:
                    if not position_to_insert:
                        position_to_insert = len(lines)
                        self.resnum = long( line[22:26].strip() ) # Change resnum to match molecule to replace
                elif line.startswith('HETNAM'):
                    lines.append( line.replace(name_to_replace, self.molecule_name) )
                elif not line.startswith('CONECT'):
                    lines.append(line)
        assert( position_to_insert != None )

        # Insert lines for this molecule
        lines = lines[:position_to_insert] + self.lines_to_write() + lines[position_to_insert:]

        # Renumber atoms
        lines = renumber_atoms(lines)

        # Now overwrite
        with open(pdb_path, 'w') as f:
            for line in lines:
                f.write(line)

def rotate_and_translate_coord(original_coord, U, new_centroid, ref_centroid):
    original_coord = np.matrix(original_coord)
    new_coord = original_coord - new_centroid
    new_coord = np.dot(new_coord, U)
    new_coord += ref_centroid
    new_coord = new_coord.A.flatten()
    return new_coord

def calc_rotation_translation_matrices( ref_coords, new_coords ):
    new = np.matrix(new_coords)
    ref = np.matrix(ref_coords)

    # Create the centroid of new and ref which is the geometric center of a
    # N-dimensional region and translate new and ref onto that center.
    # http://en.wikipedia.org/wiki/Centroid
    new_centroid = centroid(new)
    ref_centroid = centroid(ref)
    new -= new_centroid
    ref -= ref_centroid

    # Compute translation vector (matrix)
    T = ref_centroid - new_centroid

    # Computation of the covariance matrix
    C = np.dot(np.transpose(new), ref)

    # Computation of the optimal rotation matrix
    # This can be done using singular value decomposition (SVD)
    # Getting the sign of the det(V)*(W) to decide
    # whether we need to correct our rotation matrix to ensure a
    # right-handed coordinate system.
    # And finally calculating the optimal rotation matrix U
    # see http://en.wikipedia.org/wiki/Kabsch_algorithm
    V, S, W = np.linalg.svd(C)
    d = (np.linalg.det(V) * np.linalg.det(W)) < 0.0

    if d:
        S[-1] = -S[-1]
        V[:, -1] = -V[:, -1]

    # Create Rotation matrix U
    U = np.dot(V, W)

    return (U, new_centroid, ref_centroid)

def centroid(X):
    """
    Calculate the centroid from a matrix X
    """
    C = np.sum(X, axis=0) / len(X)
    return C
