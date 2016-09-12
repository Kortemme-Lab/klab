#!/usr/bin/python
# encoding: utf-8
"""
sqlalchemy.py
Functions to make SQLAlchemy easier to set up with a MySQL database.

This module contains very rudimentary conversion functions from MySQL schemas to SQL Alchemy Python classes.
It has only been tested on a simple database. It only handles a handful of MySQL types at present and does not create
unique, foreign, or primary keys in the Python classes. Please feel free to help complete this module but as I will
only be adding to it on a need-only basis.

Created by Shane O'Connor 2014
"""

import sys
import string
import re
import traceback
import copy

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine, and_
from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.collections import InstrumentedList

if __name__ == '__main__':
    sys.path.insert(0, '..')
from klab import colortext
from mysql import DatabaseInterface



# @todo. This module saves time creating SQLAlchemy class definitions. It is still very basic however (and hacked together).
#        The next improvement should be to handle foreign key constraint definitions e.g. turn
#             CONSTRAINT `PDBResidue_ibfk_1` FOREIGN KEY (`PDBFileID`, `Chain`) REFERENCES `PDBChain` (`PDBFileID`, `Chain`)
#        into
#             PDBFileID = Column(..., ForeignKey('PDBChain.PDBFileID'))
#        Depending on the schema, a field may be involved in multiple foreign key constraints.
#        It may make more sense to use relationships here instead e.g.
#             pdb_chain = relationship("PDBChain", foreign_keys=[PDBFileID, Chain])
#        but I need to read the documentation.


def row_to_dict(r, keep_relationships = False):
    '''Converts an SQLAlchemy record to a Python dict. We assume that _sa_instance_state exists and is the only value we do not care about.
       If DeclarativeBase is passed then all DeclarativeBase objects (e.g. those created by relationships) are also removed.
    '''
    d = {}
    if not keep_relationships:
        # only returns the table columns
        t = r.__table__
        for c in [c.name for c in list(sqlalchemy_inspect(t).columns)]:
            d[c] = getattr(r, c)
        return d
    else:
        # keeps all objects including those of type DeclarativeBase or InstrumentedList and the _sa_instance_state object
        return copy.deepcopy(r.__dict__)


def get_single_record_from_query(result_set):
    '''A helper function to return the single result from a query. This is a variation of SQLAlchemy's <result_set>.one()
       function. We assume that either a result does not exist or exactly one exists (one() assumes that exactly one exists).
       Returns None in the former case and the result in the latter case.
    '''
    assert(result_set.count() <= 1)
    if result_set.count() == 1:
        return result_set[0]


def get_or_create_in_transaction(tsession, model, values, missing_columns = [], variable_columns = [], updatable_columns = [], only_use_supplied_columns = False, read_only = False):
    '''
    Uses the SQLAlchemy model to retrieve an existing record based on the supplied field values or, if there is no
    existing record, to create a new database record.

    :param tsession: An SQLAlchemy transactioned session
    :param model: The name of the SQLAlchemy class representing the table
    :param values: A dict of values which will be used to populate the fields of the model
    :param missing_columns: Elements of missing_columns are expected to be fields in the model but are left blank regardless of whether they exist in values. This is useful for auto_increment fields.
    :param updatable_columns: If these are specified, they are treated as missing columns in the record matching and if a record is found, these fields will be updated
    :param variable_columns: If these are specified, they are treated as missing columns in the record matching but are not updated. A good use of these are for datetime fields which default to the current datetime
    :param read_only: If this is set then we query the database and return an instance if one exists but we do not create a new record.
    :return:

    Note: This function is a convenience function and is NOT efficient. The "tsession.query(model).filter_by(**pruned_values)"
          call is only (sometimes) efficient if an index exists on the keys of pruned_values. If any of the fields of pruned_values are
          large (even if otherwise deferred/loaded lazily) then you will incur a performance hit on lookup. You may need
          to reconsider any calls to this function in inner loops of your code.'''


    values = copy.deepcopy(values) # todo: this does not seem to be necessary since we do not seem to be writing

    fieldnames = [c.name for c in list(sqlalchemy_inspect(model).columns)]
    for c in missing_columns:
        fieldnames.remove(c)
    for c in updatable_columns:
        fieldnames.remove(c)
    for c in variable_columns:
        if c in fieldnames:
            fieldnames.remove(c)

    if only_use_supplied_columns:
        fieldnames = sorted(set(fieldnames).intersection(set(values.keys())))
    else:
        unexpected_fields = set(values.keys()).difference(set(fieldnames)).difference(set(variable_columns)).difference(set(updatable_columns))
        if unexpected_fields:
            raise Exception("The fields '{0}' were passed but not found in the schema for table {1}.".format("', '".join(sorted(unexpected_fields)), model.__dict__['__tablename__']))

    pruned_values = {}
    for k in set(values.keys()).intersection(set(fieldnames)):
        v = values[k]
        pruned_values[k] = v

    instance = tsession.query(model).filter_by(**pruned_values)
    if instance.count() > 1:
        raise Exception('Multiple records were found with the search criteria.')
    instance = instance.first()

    if instance:
        if read_only == False:
            for c in updatable_columns:
                setattr(instance, c, values[c])
            tsession.flush()
        return instance
    else:
        if read_only == False:
            if sorted(pruned_values.keys()) != sorted(fieldnames):
                # When adding new records, we require that all necessary fields are present
                raise Exception('Some required fields are missing: {0}. Either supply these fields or add them to the missing_columns list.'.format(set(fieldnames).difference(pruned_values.keys())))
            instance = model(**pruned_values)
            tsession.add(instance)
            tsession.flush()
            return instance
        return None


def get_or_create_in_transaction_wrapper(tsession, model, values, missing_columns = [], variable_columns = [], updatable_columns = [], only_use_supplied_columns = False, read_only = False):
    '''This function can be used to determine which calling method is spending time in get_or_create_in_transaction when profiling the database API.
       Switch out calls to get_or_create_in_transaction to get_or_create_in_transaction_wrapper in the suspected functions to determine where the pain lies.'''
    return get_or_create_in_transaction(tsession, model, values, missing_columns = missing_columns, variable_columns = variable_columns, updatable_columns = updatable_columns, only_use_supplied_columns = only_use_supplied_columns, read_only = read_only)


class IntermediateField(object):


    def __init__(self, field_name, field_type, not_null = False, default_type = None, default_value = None, comment = None, is_primary_key = False, unicode_collation_or_character_set = False):
        self.field_name = field_name
        self.field_type = field_type
        self.not_null = not_null
        self.default_type = default_type
        self.default_value = default_value
        self.comment = comment
        self.is_primary_key = is_primary_key
        self.unicode_collation_or_character_set = unicode_collation_or_character_set


    def to_sql_alchemy(self, typedefs):
        s = ''
        s += self.field_name + ' = Column('

        is_string_type = None
        is_numeric_type = None

        if self.field_type.startswith('varchar'):
            mtchs = re.match("varchar[(](\d+)[)]", self.field_type)
            assert(mtchs)
            length = int(mtchs.group(1))
            is_string_type = True
            if self.unicode_collation_or_character_set:
                s += 'Unicode(%d)' % length
                typedefs['sqlalchemy.types'].add('Unicode')
            else:
                typedefs['sqlalchemy.types'].add('String')
                s += 'String(%d)' % length

        elif self.field_type == 'double':
            s += 'DOUBLE'
            is_numeric_type = True
            typedefs['sqlalchemy.dialects.mysql'].add('DOUBLE')

        elif self.field_type == 'float':
            s += 'Float'
            is_numeric_type = True
            typedefs['sqlalchemy.types'].add('Float')

        elif self.field_type == 'longtext' or self.field_type == 'text' or self.field_type == 'mediumtext':
            s += 'Text'
            is_numeric_type = True
            typedefs['sqlalchemy.types'].add('Text')

        elif self.field_type == 'date' or self.field_type == 'datetime':
            s += 'DateTime'
            is_numeric_type = True
            typedefs['sqlalchemy.types'].add('DateTime')

        elif self.field_type == 'timestamp':
            s += 'TIMESTAMP'
            is_numeric_type = True
            typedefs['sqlalchemy.types'].add('TIMESTAMP')

        elif self.field_type.startswith('enum('):
            s += self.field_type.replace('enum', 'Enum')
            is_string_type = True
            typedefs['sqlalchemy.types'].add('Enum')

        elif self.field_type.startswith('int(') or self.field_type.startswith('bigint('):
            s += 'Integer'
            is_numeric_type = True
            typedefs['sqlalchemy.types'].add('Integer')

        elif self.field_type.startswith('tinyint('):
            s += self.field_type.upper()
            is_numeric_type = True
            typedefs['sqlalchemy.dialects.mysql'].add('TINYINT')

        elif self.field_type == 'blob':
            s += 'BLOB'
            is_numeric_type = True
            typedefs['sqlalchemy.dialects.mysql'].add('BLOB')

        elif self.field_type == 'longblob':
            s += 'LONGBLOB'
            is_numeric_type = True
            typedefs['sqlalchemy.dialects.mysql'].add('LONGBLOB')

        else:
            raise Exception("Unhandled type: '%s'" % self.field_type)

        if self.not_null:
            s += ', nullable=False'
        else:
            s += ', nullable=True'

        if self.is_primary_key:
            s += ', primary_key=True'

        if self.default_type != None:
            if self.default_type == 'string':
                if is_string_type:
                    s += ", default=u'%s'" % self.default_value
                elif is_numeric_type:
                    s += ", default=%s" % self.default_value
                else:
                    assert(0)

        s += ')'
        return s


class MySQLSchemaConverter(object):

    def __init__(self, user, host, db, passwd, port = 3306, socket = '/var/lib/mysql/mysql.sock'):
        try:
            self.db_interface = DatabaseInterface({}, isInnoDB=True, numTries=1, host=host, db=db, user=user, passwd=passwd, port=3306,
                     unix_socket=socket, passwdfile=None, use_utf=False, use_locking=True)
        except Exception, e:
            colortext.error('An exception was thrown trying to connect to the database.')
            colortext.warning(str(e))
            print(traceback.format_exc())
            sys.exit(1)

        self.intermediate_schema = {}
        self.tables = self.db_interface.TableNames
        self._parse_schema()


    def _parse_schema(self):
        for tbl in self.tables:
            self._create_intermediate_schema(tbl)


    def get_sqlalchemy_schema(self, restrict_to_tables = []):
        colortext.warning(' *** MySQL schema ***')
        schema = []
        #print(self.intermediate_schema)

        typedefs = {'sqlalchemy.types' : set(), 'sqlalchemy.dialects.mysql' : set()}

        for tbl in self.tables:
            if (not restrict_to_tables) or (tbl in restrict_to_tables):
                colortext.message(tbl)

                print(self.db_interface.execute("SHOW CREATE TABLE %s" % tbl))[0]['Create Table']
                print('')
                code = []
                code.append("class %s(DeclarativeBase):" % tbl)
                code.append("    __tablename__ = '%s'\n" % tbl)
                #print('\n'.join(code))

                intermediate_table = self.intermediate_schema[tbl]
                for field in intermediate_table:
                    s = field.to_sql_alchemy(typedefs)
                    code.append('    {0}'.format(s))
                    #print(s)
                code.append('\n')
                #print('')
                schema.extend(code)

        imports = []
        for module, types in sorted(typedefs.iteritems()):
            imports.append('from %s import %s' % (module, ', '.join(sorted(types))))
        schema = imports + [''] + schema

        colortext.warning('*** SQLAlchemy class definitions ***')
        print('\n'.join(schema))


    def _create_intermediate_schema(self, tbl):
        code = (self.db_interface.execute("SHOW CREATE TABLE %s" % tbl))
        assert(len(code) == 1)
        schema = code[0]['Create Table']
        #colortext.message(tbl)

        #print(schema)

        #print(schema)
        fields = [f for f in map(string.strip, schema[schema.find('(') + 1:schema.find('PRIMARY KEY')].strip().split('\n')) if f.strip()]

        pk_fields = re.match('.*PRIMARY\s+KEY\s*[(](.*?)[)]\s*[,)].*', schema, re.DOTALL)
        assert(pk_fields)
        pk_fields = [s.strip() for s in pk_fields.group(1).replace('`', '').split(',') if s.strip()]


        #colortext.warning(fields)
        for f in fields:
            #print('')
            #colortext.message(f)
            if f.endswith(','):
                f = f[:-1]

            field_name = f.split()[0].replace('`', '')
            if f.split()[1].startswith('enum('):
                mtchs = re.match(".* (enum[(].*?[)])(.*)", f)
                assert(mtchs)
                #print('ENUM', mtchs.group(1))
                field_type = mtchs.group(1)
                remaining_description = mtchs.group(2)
            else:
                field_type = f.split()[1]
                remaining_description = (' '.join(f.split()[2:])).strip()

            unicode_collation_or_character_set = False
            if remaining_description.find('utf') != -1:
                unicode_collation_or_character_set = True

            not_null = False
            if remaining_description.find('NOT NULL') != -1:
                not_null = True
                remaining_description = remaining_description.replace('NOT NULL', '').strip()

            default = False
            default_type = None
            default_value = None
            if remaining_description.find('default CURRENT_TIMESTAMP') != -1:
                default_type = 'TIMESTAMP'
                default_value = None
                remaining_description = remaining_description.replace('default CURRENT_TIMESTAMP', '')
            elif remaining_description.find('default NULL') != -1:
                default_type = 'null'
                default_value = None
                remaining_description = remaining_description.replace('default NULL', '')
            elif remaining_description.find('default') != -1:
                mtchs = re.match(".*default '(.*?)'.*", remaining_description)
                if mtchs:
                    #print('mtchs', mtchs.group(1))
                    default_type = 'string'
                    default_value = mtchs.group(1)
                    remaining_description = remaining_description.replace("default '%s'" % default_value, "")
                else:
                    colortext.error('Unexpected default value string: "{0}".'.format(remaining_description))
                    pass
                    #mtchs = re.match(".*default (.*?)(\s.*)*$", remaining_description)
                    #if mtchs:
                    #    print('mtchs non-string', mtchs.group(1))
                    #    if mtchs.group(1) == 'NULL':
                    #        default_type = 'null'
                    #        default_value = None
                    #        remaining_description = remaining_description.replace('')

            comment = None
            mtchs = re.match(".*(COMMENT '.*?').*", remaining_description)
            if mtchs:
                comment = mtchs.group(1)
                remaining_description = remaining_description.replace(mtchs.group(1), "")

            remaining_description = remaining_description.strip()

            self.intermediate_schema[tbl] = self.intermediate_schema.get(tbl, [])
            self.intermediate_schema[tbl].append(IntermediateField(field_name, field_type, not_null = not_null, default_type = default_type, default_value = default_value, comment = comment, is_primary_key = field_name in pk_fields, unicode_collation_or_character_set = unicode_collation_or_character_set))

            #print('field_name : %s' % field_name)
            #print('field_type : %s' % field_type)
            #print('not_null : %s' % not_null)

            if default_type != None:
                pass
                #print('default: %s, %s' % (default_type, default_value))
            #print('comment : %s' % comment)
            if remaining_description:
                #colortext.error('remaining_description : %s' % remaining_description)
                pass
        #print('\n')


if __name__ == '__main__':
    script_name = sys.argv[0]
    args = sys.argv[1:]
    if 4 > len(args) or len(args) > 6:
        print('Usage             : %s [user] [host] [db] [passwd]' % script_name)
        print('Optional arguments: %s [user] [host] [db] [passwd] [port] [socket]' % script_name)
    else:
        user = args[0]
        host = args[1]
        db = args[2]
        passwd = args[3]
        port = 3306
        socket = '/var/lib/mysql/mysql.sock'
        if len(args) == 6:
            socket = args[5]
        if len(args) >= 5:
            try:
                port = int(args[4])
            except:
                colortext.error('Error: Port must be a numeric string.')
                sys.exit(1)
        sc = MySQLSchemaConverter(user, host, db, passwd, port, socket)
        sc.get_sqlalchemy_schema()
