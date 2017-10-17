#!/usr/bin/python3

# The MIT License (MIT)
#
# Copyright (c) 2017 Kyle Barlow
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

'''

box_backup.py

Pip requirements: boxsdk>=2.0.0a9 oauth2client keyring

System package requirement: python-dbus system package is needed to use keyring with Linux, so create a virtualenv with --system-site-packages. You probably already have this.

'''

import os
import sys
import json
import webbrowser
import argparse
import getpass
import hashlib
import base64
import math
import threading
import queue
import time
from io import DEFAULT_BUFFER_SIZE

import boxsdk
from boxsdk import Client, LoggingClient
UPLOAD_URL = boxsdk.config.API.UPLOAD_URL
BOX_MAX_FILE_SIZE = 10737418240 # 10 GiB. The max is actually 15 GB, but 10 seems like a nice round number
BOX_MIN_CHUNK_UPLOAD_SIZE = 60000000 # 60 MB. Current min is actually 50 MB.

MAX_CHUNK_ATTEMPTS = 5 # Maximum number of times to try uploading a particular chunk
CLIENT_SECRETS_PATH = '/kortemmelab/shared/box-client_secrets.json'

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
        self._current_chunked_upload_abort_url = None

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
            flow = oauth2client.client.flow_from_clientsecrets(CLIENT_SECRETS_PATH, scope='', redirect_uri = 'http://localhost:8080')
            self.credentials = tools.run_flow(flow, storage, flags)

        self.oauth_connector = OAuthConnector(self.credentials)
        self.client = Client( self.oauth_connector ) # Replace this with LoggingClient for debugging

        self.root_folder = self.client.folder( folder_id = '0' )
        self._upload_test_only = False # Don't perform actual uploads if True. Was used to debug memory leaks.

    def find_folder_by_name( self, folder_id, name, limit = 500 ):
        search_folder = self.client.folder( folder_id = folder_id )
        folders = [ f for f in search_folder.get_items( limit = limit ) if f['name'] == name and f['type'] == 'folder' ]
        if len( folders ) != 1:
            raise FolderTraversalException()
        return folders[0]['id']

    def find_file( self, folder_id, basename, limit = 500 ):
        '''
        Finds a file based on a box path
        Returns a list of file IDs
        Returns multiple file IDs if the file was split into parts with the extension '.partN' (where N is an integer)
        '''
        search_folder = self.client.folder( folder_id = folder_id )
        files = [ (f['id'], f['name']) for f in search_folder.get_items( limit = limit ) if f['name'].startswith( basename ) and f['type'] == 'file' ]
        files.sort()
        for f_id, f_name in files:
            assert(
                f_name == basename
                or
                ( f_name.startswith( basename ) and f_name[len(basename):len(basename)+5] == '.part' )
            )
        return [f[0] for f in files]

    def find_folder_path( self, folder_path, limit = 500 ):
        current_folder_id = '0'
        for folder_name in os.path.normpath(folder_path).split(os.path.sep):
            if len(folder_name) > 0:
                current_folder_id = self.find_folder_by_name( current_folder_id, folder_name, limit = limit )
        return current_folder_id

    def upload( self,
                destination_folder_id,
                source_path,
                preflight_check = True,
                verify = False, # After upload, check sha1 sums
                lock_file = True, # By default, lock uploaded files to prevent changes (unless manually unlocked)
                maximum_attemps = 3, # Number of times to retry upload after any exception is encountered
    ):
        for trial_counter in range( maximum_attemps ):
            try:
                file_size = os.stat(source_path).st_size
                uploaded_file_ids = []
                if file_size >= BOX_MAX_FILE_SIZE:
                    uploaded_file_ids = self._upload_in_splits( destination_folder_id, source_path, preflight_check )
                else:
                    # File will not be uploaded in splits, and that function will check if each split already exists
                    # So now we are going to check if the file already exists
                    # We won't check if the file is actually the same here, that happens below at the verify step
                    uploaded_box_file_ids = self.find_file( destination_folder_id, os.path.basename( source_path ) )
                    if len(uploaded_box_file_ids) != 1:
                        if file_size >= BOX_MIN_CHUNK_UPLOAD_SIZE: # 55 MB
                            uploaded_file_ids = [ self._chunked_upload( destination_folder_id, source_path, preflight_check = preflight_check ) ]
                        else:
                            if not self._upload_test_only:
                                uploaded_file_ids = [ self.client.folder( folder_id = destination_folder_id ).upload( file_path = source_path, preflight_check = preflight_check, preflight_expected_size = file_size ).get().response_object['id'] ]

                if lock_file:
                    self.lock_files( uploaded_file_ids )

                if verify:
                    assert( self.verify_uploaded_file( destination_folder_id, source_path ) )

                return True
            except:
                print( 'Uploading file {0} failed attempt {1} of {2}'.format(source_path, trial_counter+1, maximum_attemps) )

        return False

    def lock_files( self, file_ids, prevent_download = False ):
        for file_id in file_ids:
            self.lock_file( file_id, prevent_download = prevent_download )

    def lock_file( self, file_id, prevent_download = False ):
        self.client.file( file_id = file_id ).lock()

    def verify_uploaded_file(
            self,
            destination_folder_id,
            source_path,
            verbose = True,
    ):
        '''
        Verifies the integrity of a file uploaded to Box
        '''
        source_file_size = os.stat(source_path).st_size

        total_part_size = 0
        file_position = 0
        uploaded_box_file_ids = self.find_file( destination_folder_id, os.path.basename( source_path ) )
        total_sha1 = hashlib.sha1()
        for i, file_id in enumerate(uploaded_box_file_ids):
            file_info = self.client.file( file_id = file_id ).get()
            uploaded_sha1 = file_info.response_object['sha1']
            uploaded_size = file_info.response_object['size']

            part_sha1 = read_sha1( source_path, start_byte = file_position, read_size = uploaded_size, extra_hashers = [total_sha1] )
            if part_sha1.hexdigest() != uploaded_sha1:
                print( '\n' )
                print( 'Part sha1: ' + part_sha1.hexdigest() )
                print( 'Uploaded sha1: ' + uploaded_sha1 )
                raise Exception('Sha1 hash of uploaded file {0} ({1}) does not match'.format(file_info.response_object['name'], file_id) )
            file_position += uploaded_size
            total_part_size += uploaded_size
            if len(uploaded_box_file_ids) > 1:
                print( 'Finished verifying part {0} of {1} of {2}'.format( i+1, len(uploaded_box_file_ids), file_id ) )

        assert( source_file_size == total_part_size )

        if verbose:
            print( 'Verified uploaded file {0} ({1}) with sha1: {2}'.format(source_path, file_id, total_sha1.hexdigest()) )

        return True

    def _upload_in_splits( self, destination_folder_id, source_path, preflight_check ):
        '''
        Since Box has a maximum file size limit (15 GB at time of writing),
        we need to split files larger than this into smaller parts, and chunk upload each part
        '''
        file_size = os.stat(source_path).st_size
        split_size = BOX_MAX_FILE_SIZE

        # Make sure that the last split piece is still big enough for a chunked upload
        while file_size % split_size < BOX_MIN_CHUNK_UPLOAD_SIZE:
            split_size -= 1000
            if split_size < BOX_MIN_CHUNK_UPLOAD_SIZE:
                raise Exception('Lazy programming error')

        split_start_byte = 0
        part_count = 0
        uploaded_file_ids = []
        while split_start_byte < file_size:
            dest_file_name = '{0}.part{1}'.format( os.path.basename(source_path), part_count)
            prev_uploaded_file_ids = self.find_file( destination_folder_id, dest_file_name )
            if len( prev_uploaded_file_ids ) == 1:
                print ( '\nSkipping upload of split {0} of {1}; already exists'.format( part_count + 1, math.ceil(file_size / split_size) ) )
                uploaded_file_ids.extend( prev_uploaded_file_ids )
            else:
                print ( '\nUploading split {0} of {1}'.format( part_count + 1, math.ceil(file_size / split_size) ) )
                uploaded_file_ids.append( self._chunked_upload(
                    destination_folder_id, source_path,
                    dest_file_name = dest_file_name,
                    split_start_byte = split_start_byte,
                    file_size = min(split_size, file_size - split_start_byte), # Take the min of file_size - split_start_byte so that the last part of a split doesn't read into the next split
                    preflight_check = preflight_check,
                ) )
            part_count += 1
            split_start_byte += split_size

        return uploaded_file_ids

    def _abort_chunked_upload(self):
        delete_response = box.client.session.delete( self._current_chunked_upload_abort_url, expect_json_response = False )
        assert( delete_response.status_code == 204 )
        assert( len(delete_response.content) == 0 )
        self._current_chunked_upload_abort_url = None

    def _chunked_upload(
            self,
            destination_folder_id,
            source_path,
            dest_file_name = None,
            split_start_byte = 0,
            file_size = None,
            preflight_check = True,
            upload_threads = 4, # Your results may vary
    ):
        dest_file_name = dest_file_name or os.path.basename( source_path )
        file_size = file_size or os.stat(source_path).st_size
        destination_folder = self.client.folder( folder_id = destination_folder_id )

        if preflight_check and not self._upload_test_only:
            destination_folder.preflight_check( size = file_size, name = dest_file_name )

        url = '{0}/files/upload_sessions'.format(UPLOAD_URL)

        data = json.dumps({
            'folder_id' : destination_folder_id,
            'file_size' : file_size,
            'file_name' : dest_file_name,
        })

        if self._upload_test_only:
            json_response = {
                'id' : 0,
                'part_size' : 5000000, # 5 MB
                'session_endpoints' : { 'abort' : None },
                'total_parts' : math.ceil( float(file_size) / float(5000000) ),
            }
        else:
            json_response = self.client.session.post(url, data=data, expect_json_response=True).json()

        self._current_chunked_upload_abort_url = json_response['session_endpoints']['abort']
        upload_responses = {
            'create' : json_response,
            'parts' : {},
        }

        session_id = json_response['id']
        part_size = json_response['part_size']

        reporter = Reporter( 'uploading ' + source_path + ' as ' + dest_file_name, entries = 'chunks' )
        reporter.set_total_count( json_response['total_parts'] )

        uploads_complete = threading.Event()
        totally_failed = threading.Event()
        chunk_queue = queue.PriorityQueue()
        results_queue = queue.PriorityQueue()

        def upload_worker():
            while (not uploads_complete.is_set()) and (not totally_failed.is_set()):
                try:
                    part_n, args = chunk_queue.get(True, 0.3)
                except queue.Empty:
                    continue

                source_path, start_byte, header_start_byte, read_amount, attempt_number = args
                attempt_number += 1
                try:
                    sha1 = hashlib.sha1()

                    with open( source_path, 'rb' ) as f:
                        f.seek( start_byte )
                        data = f.read( read_amount )
                        sha1.update(data)

                    headers['digest'] = 'sha=' + base64.b64encode(sha1.digest()).decode()
                    headers['content-range'] = 'bytes {0}-{1}/{2}'.format( header_start_byte, header_start_byte + len(data) - 1, file_size )
                    if self._upload_test_only:
                        results_queue.put( (part_n, {'part' : part_n}) )
                    else:
                        part_response = self.client.session.put(url, headers = headers, data = data, expect_json_response = True)

                        results_queue.put( (part_n, dict(part_response.json())) )
                    reporter.increment_report()
                except:
                    if attempt_number >= MAX_CHUNK_ATTEMPTS:
                        print( '\nSetting total failure after attempt {0} for part_n {1}\n'.format( attempt_number, part_n ) )
                        totally_failed.set()
                    else:
                        chunk_queue.put( (part_n, (source_path, start_byte, header_start_byte, read_amount, attempt_number) ) )
                chunk_queue.task_done()

        upload_worker_threads = []
        for i in range( upload_threads ):
            t = threading.Thread( target = upload_worker )
            t.start()
            upload_worker_threads.append(t)

        for part_n in range( json_response['total_parts'] ):
            header_start_byte = part_n * part_size
            start_byte = split_start_byte + header_start_byte
            url = '{0}/files/upload_sessions/{1}'.format( UPLOAD_URL, session_id )

            headers = {
                'content-type' : 'application/octet-stream',
            }

            read_amount = min(part_size, file_size - header_start_byte) # Make sure the last part of a split doesn't read into the next split
            if not read_amount > 0:
                print(read_amount, part_size, file_size, start_byte)
                raise Exception('read_amount failure')

            upload_args = (source_path, start_byte, header_start_byte, read_amount, 0) # Last 0 is attempt number
            chunk_queue.put( (part_n, upload_args) )

        total_sha = hashlib.sha1()
        def read_total_hash_worker():
            # We are reading the file for a second time just for hashing here, but that seems
            # better than trying to save the whole file in memory for hashing at the end.
            # The upload should be slower and ongoing in the background as well
            for part_n in range( json_response['total_parts'] ):
                if totally_failed.is_set():
                    break

                header_start_byte = part_n * part_size
                start_byte = split_start_byte + part_n * part_size
                read_amount = min(part_size, file_size - header_start_byte) # Make sure the last part of a split doesn't read into the next split
                with open( source_path, 'rb' ) as f:
                    f.seek( start_byte )
                    data = f.read( read_amount )
                    total_sha.update(data)

        total_hasher = threading.Thread( target = read_total_hash_worker )
        total_hasher.start()

        # Wait for everything to finish or fail
        chunk_queue.join()
        uploads_complete.set()
        if totally_failed.is_set():
            # Cancel chunked upload upon exception
            self._abort_chunked_upload()
            print( 'Chunk upload of file {0} (in {1} parts) cancelled'.format(source_path, json_response['total_parts']) )
            raise Exception('Totally failed upload')
        reporter.done()
        if total_hasher.isAlive():
            print( 'Waiting to compute total hash of file' )
            total_hasher.join()

        while not results_queue.empty():
            part_n, part_response = results_queue.get()
            upload_responses['parts'][part_n] = part_response['part']

        # Commit
        try:
            print( 'Committing file upload' )
            url = '{0}/files/upload_sessions/{1}/commit'.format( UPLOAD_URL, session_id )
            data = json.dumps({
                'parts' : [ upload_responses['parts'][part_n] for part_n in range( json_response['total_parts'] ) ],
            })
            headers = {}
            headers['digest'] = 'sha=' + base64.b64encode(total_sha.digest()).decode()
            if self._upload_test_only:
                commit_response = {}
            else:
                commit_response = self.client.session.post(url, headers=headers, data=data, expect_json_response=True).json()
            upload_responses['commit'] = commit_response
        except:
            # Cancel chunked upload upon exception
            self._abort_chunked_upload()
            print( 'Chunk upload of file {0} (in {1} parts) cancelled'.format(source_path, json_response['total_parts']) )
            raise

        self._current_chunked_upload_abort_url = None

        if self._upload_test_only:
            return None
        else:
            file_ids = self.find_file( destination_folder_id, dest_file_name )
            assert( len(file_ids) == 1 )
            return file_ids[0]

def read_sha1(
    file_path,
    buf_size = None,
    start_byte = 0,
    read_size = None,
    extra_hashers = [], # update(data) will be called on all of these
):
    '''
    Determines the sha1 hash of a file in chunks, to prevent loading the entire file at once into memory
    '''
    read_size = read_size or os.stat(file_path).st_size
    buf_size = buf_size or DEFAULT_BUFFER_SIZE

    data_read = 0
    total_sha1 = hashlib.sha1()
    while data_read < read_size:
        with open( file_path, 'rb', buffering = 0 ) as f:
            f.seek( start_byte )
            data = f.read( min(buf_size, read_size - data_read) )
            assert( len(data) > 0 )
            total_sha1.update( data )
            for hasher in extra_hashers:
                hasher.update( data )
            data_read += len(data)
            start_byte += len(data)
    assert( data_read == read_size )

    return total_sha1

if __name__ == '__main__':
    import argparse

    box = BoxAPI()

    parser = argparse.ArgumentParser(description='Upload files to Box')
    parser.add_argument('--verify', dest='verify', action='store_true', help='Verify file upload was successful by recomputing sha1 sums and comparing to sha1 sums of uploaded file (including file splits, if file was split). Could be pretty slow!')
    parser.set_defaults( verify = False )
    parser.add_argument('--nolock', dest='lock', action='store_false', help='Do not lock files after upload')
    parser.set_defaults( lock = True )
    parser.add_argument('destination_folder', help='File path (in Box system) of destination folder')
    parser.add_argument('file_to_upload', nargs='+', help='Path (on local file system) of file(s) to upload to Box')
    args = parser.parse_args()

    upload_folder_id = box.find_folder_path( args.destination_folder )
    print( 'Upload destination folder id: {0} {1}'.format( upload_folder_id, args.destination_folder ) )

    failed_uploads = []
    for file_to_upload in args.file_to_upload:
        if not box.upload( upload_folder_id, file_to_upload, verify = args.verify, lock_file = args.lock ):
            failed_uploads.append( file_to_upload )

    if len(failed_uploads) > 0:
        print( '\nAll failed uploads:' )
        print( failed_uploads )
