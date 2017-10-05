# dbus-python system package is needed, so create a virtualenv with --system-site-packages
# Packages needed: boxsdk>=2.0.0a9 oauth2client keyring

import os
import json
import webbrowser
import argparse
import getpass

# Import two classes from the boxsdk module - Client and OAuth2
import boxsdk
from boxsdk import Client
UPLOAD_URL = boxsdk.config.API.UPLOAD_URL

import oauth2client
from oauth2client.contrib.keyring_storage import Storage
from oauth2client import tools

class FolderTraversalException(Exception):
    pass

class BoxAPI:
    def __init__(self):
        storage = Storage('klab_box_sync', getpass.getuser())
        credentials = storage.get()
        if credentials == None:
            parser = argparse.ArgumentParser(parents=[tools.argparser])
            flags = parser.parse_args()
            flow = oauth2client.client.flow_from_clientsecrets('client_secrets.json', scope='', redirect_uri = 'http://localhost:8080')
            credentials = tools.run_flow(flow, storage, flags)

        self.client = Client(credentials)

        self.root_folder = self.client.folder( folder_id = '0' )

    def find_folder_by_name( self, search_folder, name, limit = 1000 ):
        folders = [ f for f in search_folder.get_items( limit = limit ) if f['name'] == name ]
        if len( folders ) != 1:
            raise FolderTraversalException()
        return folders[0]['id']

    def find_folder_path( self, folder_path, limit = 1000 ):
        current_folder_id = '0'
        for folder_name in os.path.normpath(folder_path).split(os.path.sep):
            if len(folder_name) > 0:
                current_folder_id = self.find_folder_by_name( self.client.folder( folder_id = current_folder_id ), folder_name, limit = limit )
        return current_folder_id

    def upload( self,
                destination_folder_id,
                source_path,
                preflight_check = True,
    ):
        file_size = os.stat(source_path).st_size
        if file_size >= 55000000:
            self.chunked_upload( destination_folder_id, source_path, preflight_check = preflight_check )
        else:
            self.client.folder( folder_id = destination_folder_id ).upload( file_path = source_path, preflight_check = preflight_check, preflight_expected_size = file_size )

    def chunked_upload( self,
                        destination_folder_id,
                        source_path,
                        preflight_check = True,
    ):
        destination_folder = self.client.folder( folder_id = destination_folder_id )
        file_size = os.stat(source_path).st_size # KB
        if preflight_check:
            destination_folder.preflight_check( size = file_size, name = os.path.basename(source_path) )

        url = '{0}/files/upload_sessions'.format(UPLOAD_URL)

        data = json.dumps({
            'folder_id' : destination_folder_id,
            'file_size' : file_size,
            'file_name' : os.path.basename(source_path),
        })

        json_response = self.client.session.post(url, data=data, expect_json_response=True)

        return json_response


box = BoxAPI()

upload_folder_id = box.find_folder_path( '/kortemmelab/home/kyleb/test_box' )

### Chunked upload test
# json_response = box.chunked_upload( upload_folder_id, '/home/kyleb/tmp/box_test/myfile' )

# abort_url = json_response.json()['session_endpoints']['abort']
# delete_response = box.client.session.delete( abort_url, expect_json_response = False )
# assert( delete_response.status_code == 204 )
# assert( len(delete_response.content) == 0 )

### Regular upload test
box.upload( upload_folder_id, '/home/kyleb/tmp/box_test/2017-09-08 14.25.04.mp4' )
