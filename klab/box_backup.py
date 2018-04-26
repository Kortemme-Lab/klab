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
import datetime
import base64
import math
import threading
import queue
import time
import random
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

    def _find_folder_by_name_inner( self, folder_id, name, limit = 500 ):
        search_folder = self.client.folder( folder_id = folder_id )
        offset = 0
        search_folders = search_folder.get_items( limit = limit, offset = offset )
        while len(search_folders) > 0:
            folders = [ f for f in search_folders if f['name'] == name and f['type'] == 'folder' ]
            if len( folders ) == 1:
                return folders[0]['id']
            offset += limit
            search_folders = search_folder.get_items( limit = limit, offset = offset )

        return None

    def create_folder( self, root_folder_id, folder_name ):
        # Creates a folder in Box folder folder_id if it doesn't exist already
        folder_id = self._find_folder_by_name_inner( root_folder_id, folder_name )
        if folder_id == None:
            return self.client.folder( folder_id = root_folder_id ).create_subfolder(folder_name ).id
        else:
            return folder_id

    def find_file( self, folder_id, basename, limit = 500 ):
        '''
        Finds a file based on a box path
        Returns a list of file IDs
        Returns multiple file IDs if the file was split into parts with the extension '.partN' (where N is an integer)
        '''
        search_folder = self.client.folder( folder_id = folder_id )
        offset = 0
        search_items = search_folder.get_items( limit = limit, offset = offset )
        found_files = []
        while len(search_items) > 0:
            files = [ (f['id'], f['name']) for f in search_items if f['name'].startswith( basename ) and f['type'] == 'file' ]
            files.sort()
            for f_id, f_name in files:
                assert(
                    f_name == basename
                    or
                    ( f_name.startswith( basename ) and f_name[len(basename):len(basename)+5] == '.part' )
                )
            found_files.extend( files )
            offset += limit
            search_items = search_folder.get_items( limit = limit, offset = offset )
        return [f[0] for f in found_files]

    def find_folder_path( self, folder_path ):
        current_folder_id = '0'
        for folder_name in os.path.normpath(folder_path).split(os.path.sep):
            if len(folder_name) > 0:
                current_folder_id = self._find_folder_by_name_inner( current_folder_id, folder_name )
        return current_folder_id

    def upload( self,
                destination_folder_id,
                source_path,
                preflight_check = True,
                verify = False, # After upload, check sha1 sums
                lock_file = True, # By default, lock uploaded files to prevent changes (unless manually unlocked)
                maximum_attempts = 5, # Number of times to retry upload after any exception is encountered
                verbose = True,
                chunked_upload_threads = 5,
    ):
        for trial_counter in range( maximum_attempts ):
            try:
                file_size = os.stat(source_path).st_size
                uploaded_file_ids = []
                if file_size >= BOX_MAX_FILE_SIZE:
                    uploaded_file_ids = self._upload_in_splits( destination_folder_id, source_path, preflight_check, verbose = verbose, chunked_upload_threads = chunked_upload_threads )
                else:
                    # File will not be uploaded in splits, and that function will check if each split already exists
                    # So now we are going to check if the file already exists
                    # We won't check if the file is actually the same here, that happens below at the verify step
                    uploaded_box_file_ids = self.find_file( destination_folder_id, os.path.basename( source_path ) )
                    if len(uploaded_box_file_ids) != 1:
                        if file_size >= BOX_MIN_CHUNK_UPLOAD_SIZE: # 55 MB
                            uploaded_file_ids = [ self._chunked_upload( destination_folder_id, source_path, preflight_check = preflight_check, verbose = verbose, upload_threads = chunked_upload_threads, ) ]
                        else:
                            if not self._upload_test_only:
                                uploaded_file_ids = [ self.client.folder( folder_id = destination_folder_id ).upload( file_path = source_path, preflight_check = preflight_check, preflight_expected_size = file_size ).get().response_object['id'] ]

                if lock_file:
                    self.lock_files( uploaded_file_ids )

                if verify:
                    if not self.verify_uploaded_file( destination_folder_id, source_path ):
                        return False

                return True
            except:
                if maximum_attempts > 1 and verbose:
                    print( 'Uploading file {0} failed attempt {1} of {2}'.format(source_path, trial_counter+1, maximum_attempts) )
                elif maximum_attempts == 1:
                    raise

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
                print('Sha1 hash of uploaded file {0} ({1}) does not match'.format(file_info.response_object['name'], file_id) )
                return False

            file_position += uploaded_size
            total_part_size += uploaded_size
            if len(uploaded_box_file_ids) > 1:
                print( 'Finished verifying part {0} of {1} of {2}'.format( i+1, len(uploaded_box_file_ids), file_id ) )

        assert( source_file_size == total_part_size )

        if verbose:
            print( 'Verified uploaded file {0} ({1}) with sha1: {2}'.format(source_path, file_id, total_sha1.hexdigest()) )

        return True

    def _upload_in_splits( self, destination_folder_id, source_path, preflight_check, verbose = True, chunked_upload_threads = 5 ):
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
                if verbose:
                    print ( '\nSkipping upload of split {0} of {1}; already exists'.format( part_count + 1, math.ceil(file_size / split_size) ) )
                uploaded_file_ids.extend( prev_uploaded_file_ids )
            else:
                if verbose:
                    print ( '\nUploading split {0} of {1}'.format( part_count + 1, math.ceil(file_size / split_size) ) )
                uploaded_file_ids.append( self._chunked_upload(
                    destination_folder_id, source_path,
                    dest_file_name = dest_file_name,
                    split_start_byte = split_start_byte,
                    file_size = min(split_size, file_size - split_start_byte), # Take the min of file_size - split_start_byte so that the last part of a split doesn't read into the next split
                    preflight_check = preflight_check,
                    verbose = verbose,
                    upload_threads = chunked_upload_threads,
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
            upload_threads = 5, # Your results may vary
            verbose = True,
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

        reporter = Reporter( 'uploading ' + source_path + ' as ' + dest_file_name, entries = 'chunks', print_output = verbose )
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
                        if verbose:
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
                if verbose:
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
            if verbose:
                print( 'Chunk upload of file {0} (in {1} parts) cancelled'.format(source_path, json_response['total_parts']) )
            raise Exception('Totally failed upload')
        reporter.done()
        if total_hasher.isAlive():
            if verbose:
                print( 'Waiting to compute total hash of file' )
            total_hasher.join()

        while not results_queue.empty():
            part_n, part_response = results_queue.get()
            upload_responses['parts'][part_n] = part_response['part']

        # Commit
        try:
            if verbose:
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
            if verbose:
                print( 'Chunk upload of file {0} (in {1} parts) cancelled'.format(source_path, json_response['total_parts']) )
            raise

        self._current_chunked_upload_abort_url = None

        if self._upload_test_only:
            return None
        else:
            file_ids = self.find_file( destination_folder_id, dest_file_name )
            assert( len(file_ids) == 1 )
            return file_ids[0]

    def upload_path( self, upload_folder_id, fpath, verbose = True, lock_files = True, maximum_attempts = 5, retry_already_uploaded_files = False, write_marker_files = False, outer_upload_threads = 5, upload_in_random_order = True ):
        # Will upload a file, or recursively upload a folder, leaving behind verification files in its wake
        assert( os.path.exists( fpath ) )
        big_batch_threshold = 10 # Verbosity is higher if the total files to upload is less than this

        def find_files_recursive( search_path, outer_folder_id ):
            # This function also creates missing Box folders as it searches the local filesystem
            if os.path.isfile(search_path):
                if search_path.endswith('.uploadedtobox'):
                    return []
                return [ (search_path, outer_folder_id) ]
            else:
                inner_folder_id = box.create_folder( outer_folder_id, os.path.basename(search_path) )
                found_files = []
                for x in os.listdir( search_path ):
                    found_files.extend( find_files_recursive( os.path.join( search_path, x ), inner_folder_id ) )
                return found_files

        if verbose:
            print( 'Recursively searching for files to upload in:', fpath )
        files_to_upload = find_files_recursive( fpath, upload_folder_id )
        if verbose:
            print( 'Found {} files to upload'.format(len(files_to_upload)) )
        if len(files_to_upload) >= big_batch_threshold:
            r = Reporter( 'uploading big batch of files to Box', entries = 'files', eol_char = '\r' )
        else:
            r = Reporter( 'uploading batch of files to Box', entries = 'files', eol_char = '\n' )
        r.set_total_count( len(files_to_upload) )
        files_to_upload.sort()
        files_to_upload_queue = queue.PriorityQueue()
        results_queue = queue.Queue()
        uploads_complete = threading.Event()

        def upload_worker():
            while not uploads_complete.is_set():
                try:
                    i, source_path_upload, folder_to_upload_id, call_upload_verbose, uploaded_marker_file = files_to_upload_queue.get(True, 0.3)
                except queue.Empty:
                    continue

                upload_successful = False
                file_totally_failed = False

                for trial_counter in range( maximum_attempts ):
                    if file_totally_failed:
                        break

                    try:
                        upload_successful = self.upload( folder_to_upload_id, source_path_upload, verify = False, lock_file = lock_files, maximum_attempts = 1, verbose = call_upload_verbose, chunked_upload_threads = 3 )
                    except Exception as e:
                        print(e)
                        upload_successful = False

                    if not upload_successful:
                        if maximum_attempts > 1:
                            print( 'Uploading file {0} failed upload in attempt {1} of {2}'.format(source_path_upload, trial_counter+1, maximum_attempts) )
                        continue

                    try:
                        if not self.verify_uploaded_file( folder_to_upload_id, source_path_upload, verbose = call_upload_verbose ):
                            upload_successful = False
                    except Exception as e:
                        print(e)
                        upload_successful = False

                    if not upload_successful:
                        if maximum_attempts > 1:
                            print( 'Uploading file {0} failed verification in attempt {1} of {2}. Removing and potentially retrying upload.'.format(source_path_upload, trial_counter+1, maximum_attempts) )
                        try:
                            file_ids = self.find_file( folder_to_upload_id, os.path.basename( source_path_upload ) )
                        except Exception as e:
                            print(e)
                            file_ids = []
                        for file_id in file_ids:
                            try:
                                self.client.file( file_id = file_id ).delete()
                            except:
                                print( 'Delete failed, skipping file ' + source_path_upload )
                                file_totally_failed = True
                                upload_successful = False
                        continue

                    break
                results_queue.put( (source_path_upload, folder_to_upload_id, upload_successful, uploaded_marker_file) )
                files_to_upload_queue.task_done()

        if len(files_to_upload) >= big_batch_threshold:
            inner_verbosity = False
        else:
            inner_verbosity = True

        i = 0
        for file_path, inner_folder_id in files_to_upload:
            uploaded_marker_file = file_path + '.uploadedtobox'
            if os.path.isfile( uploaded_marker_file ):
                if retry_already_uploaded_files:
                    os.remove( uploaded_marker_file )
                else:
                    print( 'Skipping already uploaded file: ' + file_path )
                    r.decrement_total_count()
                    continue

            # Since we are putting into a sorted PriorityQueue, we add a random first tuple member if randomness is desired
            if upload_in_random_order:
                worker_args = (random.random(), file_path, inner_folder_id, inner_verbosity, uploaded_marker_file)
            else:
                worker_args = (i, file_path, inner_folder_id, inner_verbosity, uploaded_marker_file)
            files_to_upload_queue.put( worker_args )
            i += 1

        upload_worker_threads = []
        for i in range( outer_upload_threads ):
            t = threading.Thread( target = upload_worker )
            t.start()
            upload_worker_threads.append(t)

        failed_files = queue.PriorityQueue()
        def results_worker():
            while not uploads_complete.is_set():
                try:
                    source_path_upload, folder_to_upload_id, upload_successful, uploaded_marker_file = results_queue.get(True, 0.95)
                except queue.Empty:
                    continue

                if upload_successful:
                    if write_marker_files:
                        try:
                            with open(uploaded_marker_file, 'w') as f:
                                f.write( str( datetime.datetime.now() ) )
                        except:
                            # Sometimes this might fail if we have a permissions error (e.g. uploading a file in a directory where we only have read permission), so we just ignore
                            pass
                else:
                    print( 'Totally failed:', file_path )
                    failed_files.put( file_path )
                    if os.path.isfile(uploaded_marker_file):
                        os.remove(uploaded_marker_file)

                r.increment_report()

        results_worker_thread = threading.Thread( target = results_worker )
        results_worker_thread.start()

        files_to_upload_queue.join()
        uploads_complete.set()
        for t in upload_worker_threads:
            t.join()
        results_worker_thread.join()

        failed_files_list = []
        while not failed_files.empty():
            failed_files_list.append( failed_files.get() )
        return failed_files_list

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
    parser.add_argument('--nolock', dest='lock', action='store_false', help='Do not lock files after upload')
    parser.set_defaults( lock = True )
    parser.set_defaults( markers = False )
    parser.add_argument('--writemarkers', dest='markers', action='store_true', help='Write marker files to indicate an upload succeeded')
    parser.add_argument('destination_folder', help='File path (in Box system) of destination folder')
    parser.add_argument('file_or_folder_to_upload', nargs='+', help='Path (on local file system) of file(s) or folder(s) to upload to Box. If argument is a folder, all files in that folder (non-recursive) will be uploaded to the destination folder.')
    args = parser.parse_args()

    upload_folder_id = box.find_folder_path( args.destination_folder )
    print( 'Upload destination folder id: {0} {1}'.format( upload_folder_id, args.destination_folder ) )

    failed_uploads = []
    for path_to_upload in sorted( args.file_or_folder_to_upload ):
        failed_uploads.extend( box.upload_path( upload_folder_id, path_to_upload, lock_files = args.lock, write_marker_files = args.markers ) )

    if len(failed_uploads) > 0:
        print( '\nAll failed uploads:' )
        print( failed_uploads )
        with open( 'failed_uploads.txt', 'w' ) as f:
            f.write( str(failed_uploads) )
