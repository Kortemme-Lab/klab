#!/usr/bin/python
# encoding: utf-8
"""
gauth.py
Google API Authentication classes.

Created by Shane O'Connor 2015
"""

import json
from klab.general.structures import NestedBunch, NonStrictNestedBunch, DeepNonStrictNestedBunch

class OAuthCredentials(NestedBunch):

    @staticmethod
    def from_JSON(oauth_json, type = "service"):
        '''At the time of writing, keys include:
            client_secret, client_email, redirect_uris (list), client_x509_cert_url, client_id, javascript_origins (list)
            auth_provider_x509_cert_url, auth_uri, token_uri.'''
        assert(type == "service" or type == "web")
        return NestedBunch(json.loads(oauth_json)[type])

