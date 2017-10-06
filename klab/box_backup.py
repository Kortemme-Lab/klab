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
import math

# Import two classes from the boxsdk module - Client and OAuth2
import boxsdk
from boxsdk import Client, LoggingClient
# from boxsdk.util.multipart_stream import MultipartStream
UPLOAD_URL = boxsdk.config.API.UPLOAD_URL
BOX_MAX_FILE_SIZE = 10000000000 # 10 GB. The max is actually 15 GB, but 10 seems like a nice round number
BOX_MIN_CHUNK_UPLOAD_SIZE = 55000000 # 55 MB. Current min is actually 50 MB.

import oauth2client
from oauth2client.contrib.keyring_storage import Storage
from oauth2client import tools

from Reporter import Reporter

class FolderTraversalException(Exception):
    pass

class OAuthConnector(boxsdk.OAuth2):
    '''
    Overrides the Box OAuth class with calls to the matching oauth2client Credentials functions
    '''
    def __init__(
            self,
            credentials
    ):
        self._credentials = credentials

    @property
    def access_token(self):
        """
        Get the current access token.
        :return:
            current access token
        :rtype:
            `unicode`
        """
        return self._credentials.get_access_token().access_token

    def get_authorization_url(self, redirect_url):
        raise Exception('Not implemented')

    def authenticate(self, auth_code):
        """
        :return:
            (access_token, refresh_token)
        :rtype:
            (`unicode`, `unicode`)
        """
        return self.access_token, None

    def refresh(self, access_token_to_refresh):
        return self.access_token, None

    def send_token_request(self, data, access_token, expect_refresh_token=True):
        """
        :return:
            The access token and refresh token.
        :rtype:
            (`unicode`, `unicode`)
        """
        return self.access_token, None

    def revoke(self):
        """
        Revoke the authorization for the current access/refresh token pair.
        """
        http = transport.get_http_object()
        self._credentials.revoke(http)

class BoxAPI:
    def __init__(self):
        storage = Storage('klab_box_sync', getpass.getuser())
        self.credentials = storage.get()
        if self.credentials == None:
            parser = argparse.ArgumentParser(parents=[tools.argparser])
            flags = parser.parse_args()
            flow = oauth2client.client.flow_from_clientsecrets('client_secrets.json', scope='', redirect_uri = 'http://localhost:8080')
            self.credentials = tools.run_flow(flow, storage, flags)

        self.oauth_connector = OAuthConnector(self.credentials)
        self.client = Client( self.oauth_connector ) # Replace this with LoggingClient for debugging

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
        if file_size >= BOX_MAX_FILE_SIZE:
            self._upload_in_splits( destination_folder_id, source_path, preflight_check )
        if file_size >= BOX_MIN_CHUNK_UPLOAD_SIZE: # 55 MB
            self._chunked_upload( destination_folder_id, source_path, preflight_check = preflight_check )
        else:
            self.client.folder( folder_id = destination_folder_id ).upload( file_path = source_path, preflight_check = preflight_check, preflight_expected_size = file_size )

    def _upload_in_splits( self, destination_folder_id, source_path, preflight_check ):
        '''
        Since Box has a maximum file size limit (15 GB at time of writing),
        we need to split files larger than this into smaller parts, and chunk upload each part
        '''
        file_size = os.stat(source_path).st_size
        split_size = BOX_MAX_FILE_SIZE

        # Make sure that the last split piece is still big enough for a chunked upload
        while file_size % BOX_MAX_FILE_SIZE < BOX_MIN_CHUNK_UPLOAD_SIZE:
            split_size -= 1000
            if split_size < 1000000000: # 1 GB
                raise Exception('Lazy programming error')

        split_start_byte = 0
        part_count = 0
        while split_start_byte < file_size:
            print ( '\nUploading split {0} of {1}'.format( part_count, math.ceil(file_size / split_size) ) )
            self._chunked_upload(
                destination_folder_id, source_path,
                dest_file_name = '{0}.part{1}'.format( os.path.basename(source_path), part_count),
                split_start_byte = split_start_byte,
                file_size = min(split_size, file_size - split_start_byte), # Take the min of file_size - split_start_byte so that the last part of a split doesn't read into the next split
                preflight_check = preflight_check,
            )
            part_count += 1
            split_start_byte += split_size

    def _chunked_upload( self,
                         destination_folder_id,
                         source_path,
                         dest_file_name = None,
                         split_start_byte = 0,
                         file_size = None,
                         preflight_check = True,
    ):
        dest_file_name = dest_file_name or os.path.basename( source_path )
        file_size = file_size or os.stat(source_path).st_size
        destination_folder = self.client.folder( folder_id = destination_folder_id )

        if preflight_check:
            destination_folder.preflight_check( size = file_size, name = dest_file_name )

        url = '{0}/files/upload_sessions'.format(UPLOAD_URL)

        data = json.dumps({
            'folder_id' : destination_folder_id,
            'file_size' : file_size,
            'file_name' : dest_file_name,
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

            reporter = Reporter( 'uploading ' + source_path ' as ' + dest_file_name, entries = 'chunks' )
            reporter.set_total_count( json_response.json()['total_parts'] )
            for part_n in range( json_response.json()['total_parts'] ):
                start_byte = split_start_byte + part_n * part_size
                url = '{0}/files/upload_sessions/{1}'.format( UPLOAD_URL, session_id )

                headers = {
                    'content-type' : 'application/octet-stream',
                }

                sha1 = hashlib.sha1()

                with open( source_path, 'rb' ) as f:
                    f.seek( start_byte )
                    data = f.read( min(part_size, file_size - start_byte) ) # Take the min of file_size - split_start_byte so that the last part of a split doesn't read into the next split
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

upload_folder_id = box.find_folder_path( '/kortemmelab/alumni/adata' )
print( 'upload folder id:', upload_folder_id )

### Chunked upload test
files_to_upload = [ '/kortemmelab/alumni/adata/ajl02004.tar.gz' ]
for fpath in files_to_upload:
    box.upload( upload_folder_id, fpath )

### Regular upload test
# box.upload( upload_folder_id, '/home/kyleb/tmp/box_test/2017-09-08 14.25.04.mp4' )
