import collections

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
