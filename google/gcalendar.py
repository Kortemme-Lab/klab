import sys
print(sys.path)
#sys.path.insert(0, '/admin/google_env/')

from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
import json

import httplib2

class OAuthCredentials(object):

    def __init__(self, oauth_json):
        d = json.loads(oauth_json)
        for k, v in d['web'].iteritems():
            self.__dict__[k] = v
        print(self.__dict__)
        #self.client_id = client_id
        #self.email_address = email_address
        #self.client_secret = client_secret
        #self.redirect_uris = redirect_uris
        #self.javascript_origins = javascript_origins

if __name__ == '__main__':
    # todo: save this as a non-repository file
    pass
