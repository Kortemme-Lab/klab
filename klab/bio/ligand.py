#!/usr/bin/python
# encoding: utf-8
"""
ligand.py
Basic parsing for the PDB ligand .cif and XML formats.

Created by Shane O'Connor 2015
"""

import os
from io import BytesIO
import re
import copy
from PIL import Image

from klab.bio.rcsb import retrieve_ligand_cif, retrieve_pdb_ligand_info, retrieve_ligand_diagram
from klab.fs.fsio import read_file, write_file
from klab import colortext



class Ligand(object):

    '''A class used to store ligand information from the RCSB. The most useful way to use this class is to call
       Ligand.retrieve_data_from_rcsb to lookup the RCSB for the ligand data.'''

    def __init__(self, ligand_code):
        self.PDBCode = ligand_code
        self.LigandCode = None
        self.Formula = None
        self.MolecularWeight = None
        self.LigandType = None
        self.Diagram = None
        self.SimilarCompoundsDiagram = None
        self.InChI = None
        self.InChIKey = None
        self.pdb_id = None

         # These fields are not filled in automatically
        self.Solubility = None
        self.CellPermeability = None
        self.AssaysToDetermineConcentrationInCells = None
        self.ProductionInCells = None
        self.ProductionInCellsNotes = None

        # These fields are not guaranteed to be filled in
        self.Diagram = None
        self.SimilarCompoundsDiagram = None

        self.descriptors = []
        self.identifiers = []
        self.synonyms = []


    def __repr__(self):
        s =  'Ligand      : {0}, {1}, {2}\n'.format(self.PDBCode, self.LigandCode, self.Formula)
        if self.synonyms:
            s += '              AKA {0}\n'.format(', '.join(self.synonyms))
        s += 'Type        : {0}\n'.format(self.LigandType)
        s += 'Weight      : {0} g/mol\n'.format(self.MolecularWeight)
        s += 'InChI       : {0} ({1})\n'.format(self.InChI, self.InChIKey)
        if self.descriptors:
            s += 'Descriptors :\n'
            for d in self.descriptors:
                s += '              {0}    ({1}, {2} {3})\n'.format(d['Descriptor'], d['DescriptorType'], d['Program'], d['Version'])
        if self.identifiers:
            s += 'Identifiers :\n'
            for i in self.identifiers:
                s += '              {0}    ({1}, {2} {3})\n'.format(i['Identifier'], i['IDType'], i['Program'], i['Version'])
        if self.Diagram:
            file = BytesIO(self.Diagram)
            img = Image.open(file)
            w, h = img.size
            s += 'Diagram     : {0}x{1}'.format(w,h)
        if self.pdb_id:
            s += '\nAss. PDB    : {0}'.format(self.pdb_id)
        return s


    @classmethod
    def retrieve_data_from_rcsb(cls, ligand_code, pdb_id = None, silent = True, cached_dir = None):
        '''Retrieve a file from the RCSB.'''
        if not silent:
            colortext.printf("Retrieving data from RCSB")
        if cached_dir:
            assert(os.path.exists(cached_dir))

        ligand_info, pdb_ligand_info, pdb_ligand_info_path = None, None, None
        ligand_info_path = os.path.join(cached_dir, '{0}.cif'.format(ligand_code))
        if cached_dir:
            if os.path.exists(ligand_info_path):
                ligand_info = read_file(ligand_info_path)
        if not ligand_info:
            ligand_info = retrieve_ligand_cif(ligand_code)
            if cached_dir:
                write_file(ligand_info_path, ligand_info)

        # Parse .cif
        l = cls(ligand_code)
        l.parse_cif(ligand_info)
        l.pdb_id = pdb_id or l.pdb_id

        # Parse PDB XML
        if l.pdb_id:
            pdb_ligand_info_path = os.path.join(cached_dir, '{0}.pdb.ligandinfo'.format(l.pdb_id.lower()))
            if cached_dir:
                if os.path.exists(pdb_ligand_info_path):
                    pdb_ligand_info = read_file(pdb_ligand_info_path)
        if l.pdb_id:
            pdb_ligand_info = retrieve_pdb_ligand_info(l.pdb_id)
            if cached_dir:
                write_file(pdb_ligand_info_path, pdb_ligand_info)
        if pdb_ligand_info:
            l.parse_pdb_ligand_info(pdb_ligand_info)

        # Retrive the diagram image
        l.get_diagram()

        return l


    def parse_cif(self, cif):
        '''See http://www.iucr.org/__data/iucr/cif/standard/cifstd4.html, Acta Cryst. (1991). A47, 655-685.'''
        found_cif_header = False
        found_cif_descriptors = False
        found_cif_identifiers = False
        for block in cif.split('#'):
            if block.find('_chem_comp.id') != -1:
                assert(not found_cif_header)
                self.parse_cif_header(block)
                found_cif_header = True
            elif block.find('_chem_comp_atom.model_Cartn_x') != -1:
                continue
            elif block.find('_chem_comp_atom.pdbx_stereo_config') != -1:
                continue
            elif block.find('_pdbx_chem_comp_descriptor.comp_id') != -1:
                assert(not found_cif_descriptors)
                self.parse_cif_descriptor(block)
                found_cif_descriptors = True
            elif block.find('_pdbx_chem_comp_identifier.comp_id') != -1:
                assert(not found_cif_identifiers)
                self.parse_cif_identifier(block)
                found_cif_identifiers = True
            elif block.find('_pdbx_chem_comp_audit.comp_id') != -1:
                continue
            else:
                continue


    def parse_cif_header(self, b):
        header = {}
        for l in [l.strip() for l in b.split('\n') if l.strip()]:
            idx = l.find(' ')
            k = l[:idx]
            v = l[idx:].strip()
            header[k] = v
        assert(self.PDBCode.upper() == header['_chem_comp.id'])

        self.LigandCode = header['_chem_comp.name'].replace('"', '')
        self.Formula = header['_chem_comp.formula'].replace('"', '')
        self.MolecularWeight = header['_chem_comp.formula_weight']
        self.LigandType = header['_chem_comp.type'].replace('"', '')
        self.pdb_id = header['_chem_comp.pdbx_model_coordinates_db_code']

        if not header['_chem_comp.id'] == header['_chem_comp.three_letter_code']:
            raise Exception('Handle this case.')
        if header.get('_chem_comp.pdbx_synonyms') != '?':
            self.synonyms = [s.strip() for s in header['_chem_comp.pdbx_synonyms'].replace('"', '').split(';')]


    @staticmethod
    def parse_loop_section(b, expected_headers = None, header_map = {}):
        columns = []
        descriptors = []
        lines = [l.strip() for l in b.split('\n') if l.strip()]
        assert(lines[0] == 'loop_')
        for l in lines[1:]:
            if l[0] == '_':
                assert(len(l.split()) == 1)
                columns.append(l)
            elif l[0] == ';':
                # "A data item is assumed to be of data type text if it extends over more than one line, i.e. it starts and ends with a semicolon as the first character of a line."
                assert(len(descriptors) > 0)
                if descriptors[-1][-1] != ' ':
                    descriptors[-1] += ' '
                descriptors[-1] += '"' + l[1:]
            else:
                descriptors.append(l)
        if expected_headers:
            assert(columns == expected_headers)
        num_columns = len(columns)

        data = []
        for d in descriptors:
            tokens = []
            current_token = ''
            instr = False
            for c in d:
                if c == ' ':
                    if instr:
                        current_token += c
                    elif current_token:
                        tokens.append(current_token.strip())
                        current_token = ''
                elif (c == '"'):
                    if instr:
                        tokens.append(current_token.strip())
                        current_token = ''
                        instr = False
                    else:
                        instr = True
                else:
                    current_token += c
            if current_token:
                tokens.append(current_token.strip())
            assert(len(columns) == len(tokens))
            dct = {}
            for x in range(len(columns)):
                dct[header_map.get(columns[x], columns[x])] = tokens[x]
            data.append(dct)
        return data


    def parse_cif_descriptor(self, b):
        descriptors = Ligand.parse_loop_section(b,
                                expected_headers = ['_pdbx_chem_comp_descriptor.comp_id', '_pdbx_chem_comp_descriptor.type', '_pdbx_chem_comp_descriptor.program', '_pdbx_chem_comp_descriptor.program_version', '_pdbx_chem_comp_descriptor.descriptor'],
                                header_map = {
                                    '_pdbx_chem_comp_descriptor.comp_id' : 'PDBCode',
                                    '_pdbx_chem_comp_descriptor.type' : 'DescriptorType',
                                    '_pdbx_chem_comp_descriptor.program' : 'Program',
                                    '_pdbx_chem_comp_descriptor.program_version' : 'Version',
                                    '_pdbx_chem_comp_descriptor.descriptor' : 'Descriptor',
                                })

        inchi_record = [d for d in descriptors if d['DescriptorType'] == 'InChI']
        assert(len(inchi_record) == 1)
        inchi_key_record = [d for d in descriptors if d['DescriptorType'] == 'InChIKey']
        assert(len(inchi_key_record) == 1)
        self.InChI = inchi_record[0]['Descriptor']
        self.InChIKey = inchi_key_record[0]['Descriptor']
        for d in descriptors:
            assert(d['PDBCode'] == self.PDBCode)
        self.descriptors = descriptors


    def parse_cif_identifier(self, b):
        identifiers = Ligand.parse_loop_section(b,
                                expected_headers = ['_pdbx_chem_comp_identifier.comp_id', '_pdbx_chem_comp_identifier.type', '_pdbx_chem_comp_identifier.program', '_pdbx_chem_comp_identifier.program_version', '_pdbx_chem_comp_identifier.identifier'],
                                header_map = {
                                    '_pdbx_chem_comp_identifier.comp_id' : 'PDBCode',
                                    '_pdbx_chem_comp_identifier.type' : 'IDType',
                                    '_pdbx_chem_comp_identifier.program' : 'Program',
                                    '_pdbx_chem_comp_identifier.program_version' : 'Version',
                                    '_pdbx_chem_comp_identifier.identifier' : 'Identifier',
                                })
        self.identifiers = identifiers
        for i in identifiers:
            assert(i['PDBCode'] == self.PDBCode)


    def parse_pdb_ligand_info(self, pdb_ligand_info):
        '''This only parses the ligand type as all the other information should be in the .cif file. The XML file has
           proper capitalization whereas the .cif file uses all caps for the ligand type.'''
        mtchs = re.findall('(<ligand.*?</ligand>)', pdb_ligand_info, re.DOTALL)
        for m in mtchs:
            if m.upper().find('CHEMICALID="{0}"'.format(self.PDBCode.upper())) != -1:
                ligand_type = re.match('<ligand.*?\stype="(.*?)".*?>', m, re.DOTALL)
                if ligand_type:
                    self.LigandType = ligand_type.group(1)


    def get_diagram(self):
        '''In-memory usage:
               1. write_file(out_file, self.Diagram, ftype = 'wb')
               2. from io import BytesIO
                  from PIL import Image
                  file = BytesIO(self.Diagram)
                  img = Image.open(file)
        '''
        self.Diagram = retrieve_ligand_diagram(self.PDBCode)



class PDBLigand(Ligand):

    '''A subclass of Ligand used to represent instances of ligands in a PDB file.
       To save time processing the same ligand code multiple times per PDB, a Ligand object can be created and then instances
       formed using the instantiate_from_ligand function.
    '''

    def __init__(self, ligand_code, chain_id = None, sequence_id = None, pdb_ligand_code = None):
        super(PDBLigand, self).__init__(ligand_code)
        self.PDBLigandCode = pdb_ligand_code or ligand_code
        self.Chain = None
        self.SequenceID = None
        self.set_id(chain_id, sequence_id)


    def set_id(self, chain_id, sequence_id):
        if sequence_id:
            assert(len(sequence_id) == 5 and sequence_id[:4].strip().isdigit())
            self.SequenceID = sequence_id
        if sequence_id:
            assert(len(chain_id) == 1)
            self.Chain = chain_id


    def __repr__(self):
        s = super(PDBLigand, self).__repr__()
        if self.Chain and self.SequenceID:
            s += '\nSequence ID : {0}{1}'.format(self.Chain, self.SequenceID)
        if self.PDBLigandCode and self.PDBLigandCode != self.LigandCode:
            s += '\nPDB code    : {0}'.format(self.PDBLigandCode)
        return s


    @classmethod
    def instantiate_from_ligand(cls, ligand, chain_id, sequence_id, pdb_ligand_code = None):
        l = cls(ligand.LigandCode)
        l.__dict__ = copy.deepcopy(ligand.__dict__)
        l.PDBLigandCode = pdb_ligand_code or l.LigandCode
        l.set_id(chain_id, sequence_id)
        return l


    @classmethod
    def retrieve_data_from_rcsb(cls, ligand_code, pdb_id, chain_id, sequence_id, pdb_ligand_code = None, silent = True, cached_dir = None):
        l = super(PDBLigand, cls).retrieve_data_from_rcsb(ligand_code, pdb_id = pdb_id, silent = silent, cached_dir = cached_dir)
        l.pdb_id = pdb_id
        l.PDBLigandCode = pdb_ligand_code or l.LigandCode
        l.set_id(chain_id, sequence_id)
        return l



class SimplePDBLigand():
    '''A simple container class for the basic ligand properties described in PDB files. The Ligand and PDBLigand classes
       have more features.'''

    def __init__(self, ligand_code, sequence_id, description = None, chain_id = None, names = [], formula = None):
        assert(len(sequence_id) == 5)
        self.PDBCode = ligand_code
        self.Chain = chain_id
        self.SequenceID = sequence_id
        self.Description = description
        self.Names = names
        self.Formula = formula


    def __repr__(self):
        s = ['{0}{1}: {2}'.format(self.Chain or ' ', self.SequenceID, self.ID)]
        if self.Formula:
            s.append(self.Formula)
        if self.Description:
            s.append(self.Description)
        if self.Names:
            s.append('(' + ', '.join([n for n in self.Names]) + ')')
        return ', '.join(s)
