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
if __name__ == '__main__':
    sys.path.insert(0, '..')
import colortext
from mysql import DatabaseInterface

class IntermediateField(object):

    def __init__(self, field_name, field_type, not_null = False, default_type = None, default_value = None, comment = None):
        self.field_name = field_name
        self.field_type = field_type
        self.not_null = not_null
        self.default_type = default_type
        self.default_value = default_value
        self.comment = comment

    def to_sql_alchemy(self, typedefs):
        s = ''
        s += self.field_name + ' = Column('

        is_string_type = None
        is_numeric_type = None

        if self.field_type.startswith('varchar'):
            mtchs = re.match("varchar[(](\d+)[)]", self.field_type)
            assert(mtchs)
            length = int(mtchs.group(1))
            s += 'Unicode(%d)' % length
            is_string_type = True
            typedefs['sqlalchemy.types'].add('Unicode')

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

    def get_sqlalchemy_schema(self):
        colortext.warning(' *** SQLAlchemy schema ***')
        schema = []
        print(self.intermediate_schema)

        typedefs = {'sqlalchemy.types' : set(), 'sqlalchemy.dialects.mysql' : set()}


        for tbl in self.tables:

            colortext.message(tbl)

            print(self.db_interface.execute("SHOW CREATE TABLE %s" % tbl))[0]['Create Table']
            print('')
            code = []
            code.append("class %s(DeclarativeBase):" % tbl)
            code.append("__tablename__ = '%s'\n" % tbl)
            print('\n'.join(code))

            intermediate_table = self.intermediate_schema[tbl]
            for field in intermediate_table:
                s = field.to_sql_alchemy(typedefs)
                code.append(s)
                print(s)
            code.append('')
            print('')
            schema.extend(code)

        imports = []
        for module, types in sorted(typedefs.iteritems()):
            print(len(schema))
            imports.append('from %s import %s' % (module, ', '.join(sorted(types))))
            print(len(schema))
        schema = imports + [''] + schema

        colortext.message('*** SQLAlchemy schema ***')
        print('\n'.join(schema))

    def _create_intermediate_schema(self, tbl):
        code = (self.db_interface.execute("SHOW CREATE TABLE %s" % tbl))
        assert(len(code) == 1)
        schema = code[0]['Create Table']
        #colortext.message(tbl)

        #print(schema)
        fields = [f for f in map(string.strip, schema[schema.find('(') + 1:schema.find('PRIMARY KEY')].strip().split('\n')) if f.strip()]
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

            not_null = False
            if remaining_description.find('NOT NULL') != -1:
                not_null = True
                remaining_description = remaining_description.replace('NOT NULL', '').strip()

            default = False
            default_type = None
            default_value = None
            if remaining_description.find('default NULL') != -1:
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
                    colortext.error('Unexpected default value string.')
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
            self.intermediate_schema[tbl].append(IntermediateField(field_name, field_type, not_null = not_null, default_type = default_type, default_value = default_value, comment = comment))

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