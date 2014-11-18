#!/usr/bin/python
# encoding: utf-8
"""
structures.py
Generic data structures.

Created by Shane O'Connor 2014
"""

import collections


class Bunch(object):
    '''Common Python idiom.'''
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

    def keys(self):
        return self.__dict__.keys()

    def __getitem__(self, key):
        return self.__dict__.__getitem__(key)

    def get(self, item):
        return self.__dict__.get(item, None)

    def pprint(self):
        # todo: only works for one level at present
        import pprint
        return pprint.pformat(self.__dict__)

class NestedBunch(Bunch):
    '''A class to turn a dict into an object with dot accessors e.g.
         nb = NestedBunch({'k1' : {'k2' : v}})
         nb.k1.k2 # returns v
       Handles simple data types and subclasses of dict which behave appropriately e.g. JSON.
    '''
    def __init__(self, d):
        for k, v in d.iteritems():
            if isinstance(v, dict): self.__dict__[k] = self.__class__(v)
            else: self.__dict__[k] = v

    @classmethod
    def from_JSON(cls, json_string):
        import json
        return cls(json.loads(json_string))

    def __repr__(self):
        return str(self.__dict__)


class NonStrictNestedBunch(NestedBunch):
    '''Similar to a NestedBunch but we allow shallow lookups for elements which do not exist.'''

    def __nonzero__(self):
        return len(self.__dict__) != 0

    def __getattr__(self, key):
        return self.__dict__.get(key)

class DeepNonStrictNestedBunch(NonStrictNestedBunch):
    '''Similar to a NonStrictNestedBunch but we allow deep lookups for elements which do not exist.'''

    def __getattr__(self, key):
        return self.__dict__.get(key, NonStrictNestedBunch({}))



class nested_dict(dict):

    @staticmethod
    def from_dict(d):
        n = nested_dict()
        if isinstance(d, collections.Mapping):
            for k, v in d.iteritems():
                n[k] = v
        else:
            n[d] = None
        return n

    def update(self, u):
        ''' Works like dict.update(dict) but handles nested dicts.
            From http://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth.
        '''
        for k, v in u.iteritems():
            if isinstance(v, collections.Mapping):
                r = nested_dict.from_dict(self.get(k, {}))
                r.update(v)
                self[k] = r
            elif isinstance(self, collections.Mapping):
                self[k] = u[k]
            else:
                self.__dict__ = dict(k = u[k])


if __name__ == '__main__':
    n_1 = nested_dict({1 : 'one', 2 : 'two'})
    n_2 = nested_dict({1: {3: 'three', 2 : 'II'}, 'spam' : 'My brain hurts!'})
    n_1.update(n_2)
    print(n_1)

    # The motivating use-case for nested_dict
    a = nested_dict({
        "redirect_output"   : True,
        "pidfile"           : None,
        "AdminEmail"        : "support@kortemmelab.ucsf.edu",
        "ContactEmail"      : "support@kortemmelab.ucsf.edu",
        "ContactName"       : "Website administrator",
        "Database"  : {
            "MySQL"  : {
                "Host"      : "localhost",
                "Port"      : "3306",
                "Socket"    : "/var/lib/mysql/mysql.sock"
            }
        }
    })
    b = nested_dict({
        "redirect_output"   : False,
        "pidfile"           : "/tmp/scheduler_rosettadaemon.pid",
        "Database"  : {
            "MySQL"  : {
                "Host"           : "kortemmelab",
                "Database"       : "rosettaweb",
                "User"           : "rosettaweb",
                "Password"       : "mypass",
                "JobTable"       : "backrub"
            }
        }
    })
    a.update(b)
    import pprint
    pprint.pprint(a)

    nb = NestedBunch({'web' : {'test' : {'inner_test' : 1}, 'flat' : 2}, 'sibling' : 3})
    print(nb.web.test.inner_test)
    print(nb.web.flat)
    print(nb.sibling)

