#!/usr/bin/env python2
# encoding: utf-8

# The MIT License (MIT)
#
# Copyright (c) 2010-2015 Shane O'Connor
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


# Note: This code is currently untested.


class ProteinProteinComplex(object):
    '''A class to represent the notion of protein-protein complex and return records which store the data for a specific
       database schema.

       Suggested usage:

            ppcomplex = ProteinProteinComplex(...)
            ppcomplex.add_pdb_set(...)
            ...
            ppcomplex.add_pdb_set(...)
            complex_id = db_api.add_complex(ppcomplex.get_complex())
            for pdb_set in ppcomplex.get_pdb_sets():
                db_api.add_pdb_set(pdb_set['pdb_set'])
                for chain_record in pdb_set['chain_records']:
                    db_api.add_chain_record(chain_record)
    '''

    def __init__(self, lname, lshortname, rname, rshortname, lhtmlname = None, rhtmlname = None,
                 id = None,
                 functional_class_id = None, functional_class_id_ppdbm = None,
                 difficulty_ppdbm = None,
                 is_wildtype = None, wildtype_complex = None,
                 notes = None, warnings = None
                 ):

        self.id = id # can be used for database entry

        # Partner 1
        self.lname = lname
        self.lshortname = lshortname
        self.lhtmlname = lhtmlname

        # Partner 2
        self.rname = rname
        self.rshortname = rshortname
        self.rhtmlname = rhtmlname

        # Classification
        self.functional_class_id = functional_class_id             # Generic
        self.functional_class_id_ppdbm = functional_class_id_ppdbm # Protein-Protein Docking Benchmark

        # Benchmark ratings
        self.difficulty_ppdbm = difficulty_ppdbm # Protein-Protein Docking Benchmark

        # Relationships
        self.is_wildtype = is_wildtype
        self.wildtype_complex = wildtype_complex

        # Notes
        self.notes = notes
        self.warnings = warnings

        self.pdb_sets = []


    def add_pdb_set(self, pdb_names, lchains, rchains, is_complex, notes = None):
        '''lchains and rchains should be lists of pairs (p, c, n) where p is a PDB object (bio/pdb.py:PDB), c is a chain
           identifier, and n is the NMR model number (or zero if this is not applicable).
           (character). This allows us to represent combinations of unbound chains.
           is_complex should be set to True if the PDB chains collectively form a complex.'''

        # If PDB objects differ and is_complex is set, raise an exception
        # This is not foolproof - we use the PDB object reference which could differ if the same PDB were loaded more than
        # once and passed in. However, that would be bad practice and this check is much cheaper than comparing the PDB content.
        if len(set([pc[0] for pc in lchains + rchains])) > 1 and is_complex:
            raise Exception('The PDB set cannot be marked as a complex as it is defined using multiple PDB objects.')

        # Check for unique occurrences of PDB chains (same caveat applies as above)
        all_chains = [(pc[0], pc[1]) for pc in lchains + rchains]
        if not len(all_chains) == len(set(all_chains)):
            raise Exception('Each PDB chain should be included at most once.')

        # Make sure that the chains exist in the PDB objects
        for pc in lchains + rchains:
            assert(pc[0] in pdb_names)
            assert(pc[1] in pc[0].atom_sequences)

        # Create the metadata
        set_number = len(self.pdb_sets)
        pdb_set = dict(
            set_number = set_number,
            is_complex = is_complex,
            notes = notes,
            chains = dict(L = [], R = []),
            pdb_set_id = None
        )

        # Add the PDB chains
        pdb_set_id = []
        for chain_set_def in ((lchains, 'L'), (rchains, 'R')):
            for pc in sorted(chain_set_def[0]):
                chain_set = pdb_set['chains'][chain_set_def[1]]
                nmr_model = None
                if len(pc) > 2:
                    nmr_model = pc[2]
                chain_set.append(dict(
                    chain_index = len(chain_set),
                    pdb_file_id = pdb_names[pc[0]],
                    chain_id = pc[1],
                    nmr_model = nmr_model,
                ))
                pdb_set_id.append('{0}:{1}:{2}:{3}'.format(chain_set_def[0], pdb_names[pc[0]], pc[1], nmr_model))
        pdb_set['pdb_set_id'] = sorted(pdb_set_id)
        print(pdb_set['pdb_set_id'])

        # Make sure we do not already have this set defined (the Complex should contain a unique list of bags of chains).
        if pdb_set['pdb_set_id'] in [ps['pdb_set_id'] for ps in self.pdb_sets]:
            raise Exception('This PDB set has already been defined (same PDB chains/NMR models).')

        self.pdb_sets.append(pdb_set)


    @db_entry
    def get_complex(self):
        '''Returns the record for the complex definition to be used for database storage.'''
        d = dict(
            LName = self.lname,
            LShortName = self.lshortname,
            LHTMLName = self.lhtmlname,
            RName = self.rname,
            RShortName = self.rshortname,
            RHTMLName = self.rhtmlname,
            FunctionalClassID = self.functional_class_id,
            PPDBMFunctionalClassID = self.functional_class_id_ppdbm,
            PPDBMDifficulty = self.difficulty_ppdbm,
            IsWildType = self.is_wildtype,
            WildTypeComplexID = self.wildtype_complex,
            Notes = self.notes,
            Warnings = self.warnings,
        )
        if self.id:
            d['ID'] = self.id
        return d


    @db_entry
    def get_pdb_sets(self):
        '''Return a record to be used for database storage. This only makes sense if self.id is set. See usage example
           above.'''

        assert(self.id != None)

        data = []
        for pdb_set in self.pdb_sets:

            pdb_set_record = dict(
                PPComplexID = self.id,
                SetNumber = pdb_set['set_number'],
                IsComplex = pdb_set['is_complex'],
                Notes = pdb_set['notes'],
            )

            chain_records = []
            for side, chain_details in sorted(pdb_set['chains'].iteritems()):
                chain_records.append(dict(
                    PPComplexID = self.id,
                    SetNumber = pdb_set['set_number'],
                    Side = side,
                    ChainIndex = chain_details['chain_index'],
                    PDBFileID = chain_details['pdb_file_id'],
                    Chain = chain_details['chain_id'],
                    NMRModel = chain_details['nmr_model'],
                ))

            data.append(dict(pdb_set = pdb_set_record, chain_records = chain_records))

        return data

