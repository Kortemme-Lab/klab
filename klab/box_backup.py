# dbus-python system package is needed, so create a virtualenv with --system-site-packages
# Packages needed: boxsdk>=2.0.0a9 oauth2client keyring

import os
import sys
import json
import webbrowser
import argparse
import getpass
import hashlib
import base64

# Import two classes from the boxsdk module - Client and OAuth2
import boxsdk
from boxsdk import Client
# from boxsdk.util.multipart_stream import MultipartStream
UPLOAD_URL = boxsdk.config.API.UPLOAD_URL

import oauth2client
from oauth2client.contrib.keyring_storage import Storage
from oauth2client import tools

from Reporter import Reporter

class FolderTraversalException(Exception):
    pass

class BoxAPI:
    def __init__(self):
        storage = Storage('klab_box_sync', getpass.getuser())
        self.credentials = storage.get()
        if self.credentials == None:
            parser = argparse.ArgumentParser(parents=[tools.argparser])
            flags = parser.parse_args()
            flow = oauth2client.client.flow_from_clientsecrets('client_secrets.json', scope='', redirect_uri = 'http://localhost:8080')
            self.credentials = tools.run_flow(flow, storage, flags)

        # We need to check if our access has expired here, because we are
        # authorizing outside of boxsdk and boxsdk will not be able to refresh later
        # if the token has expired
        if self.credentials.access_token_expired:
            self.credentials.get_access_token()

        self.client = Client(self.credentials)

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
        file_size = os.stat(source_path).st_size
        if preflight_check:
            destination_folder.preflight_check( size = file_size, name = os.path.basename(source_path) )

        url = '{0}/files/upload_sessions'.format(UPLOAD_URL)

        data = json.dumps({
            'folder_id' : destination_folder_id,
            'file_size' : file_size,
            'file_name' : os.path.basename(source_path),
        })

        json_response = self.client.session.post(url, data=data, expect_json_response=True)
        abort_url = json_response.json()['session_endpoints']['abort']
        upload_responses = {
            'create' : json_response.json(),
            'parts' : {},
        }

        try:
            session_id = json_response.json()['id']
            part_size = json_response.json()['part_size']

            total_sha = hashlib.sha1()

            reporter = Reporter( 'uploading ' + source_path, entries = 'chunks' )
            reporter.set_total_count( json_response.json()['total_parts'] )
            for part_n in range( json_response.json()['total_parts'] ):
                start_byte = part_n * part_size
                url = '{0}/files/upload_sessions/{1}'.format( UPLOAD_URL, session_id )

                headers = {
                    'content-type' : 'application/octet-stream',
                }

                sha1 = hashlib.sha1()

                with open( source_path, 'rb' ) as f:
                    f.seek( start_byte )
                    data = f.read( part_size )
                    sha1.update(data)
                    total_sha.update(data)

                headers['digest'] = 'sha=' + base64.b64encode(sha1.digest()).decode()
                headers['content-range'] = 'bytes {0}-{1}/{2}'.format( start_byte, start_byte + len(data) - 1, file_size )
                part_response = self.client.session.put(url, headers = headers, data = data, expect_json_response = True)

                upload_responses['parts'][part_n] = part_response.json()['part']
                reporter.increment_report()

            # Commit
            url = '{0}/files/upload_sessions/{1}/commit'.format( UPLOAD_URL, session_id )
            data = json.dumps({
                'parts' : [ upload_responses['parts'][part_n] for part_n in range( json_response.json()['total_parts'] ) ],
            })
            headers = {}
            headers['digest'] = 'sha=' + base64.b64encode(total_sha.digest()).decode()
            commit_response = self.client.session.post(url, headers=headers, data=data, expect_json_response=True)
            upload_responses['commit'] = commit_response.json()
            reporter.done()
        except:
            # Cancel chunked upload upon exception
            delete_response = box.client.session.delete( abort_url, expect_json_response = False )
            assert( delete_response.status_code == 204 )
            assert( len(delete_response.content) == 0 )
            print( 'Chunk upload of file {0} cancelled by calling abort url {1}'.format(source_path, abort_url) )
            raise

        return upload_responses


box = BoxAPI()

upload_folder_id = box.find_folder_path( '/kortemmelab/home/kyleb/test_box' )
print( 'upload folder id:', upload_folder_id )

### Chunked upload test
upload_responses = box.chunked_upload( upload_folder_id, '/home/kyleb/tmp/box_test/2017-09-11 14.22.30.mp4' )

### Regular upload test
# box.upload( upload_folder_id, '/home/kyleb/tmp/box_test/2017-09-08 14.25.04.mp4' )
