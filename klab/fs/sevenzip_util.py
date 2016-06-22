import subprocess
import os

# These arguments to 7zip have been shown by Shane to work well on files with redundant information (like PDBS)
default_7zip_compression_args = [
    '7z',
    'a',
    '-t7z',
    '-m0=lzma2',
    '-mx=9',
    '-mfb=64',
    '-md=64m',
    '-ms=on'
]

def sevenzip_directory(input_directory, output_directory = None):
    if output_directory == None:
        output_directory = os.path.dirname(input_directory)
    archive_name = os.path.join(output_directory, os.path.basename(input_directory)) + '.7z'
    args = list(default_7zip_compression_args)
    args.extend( [
        archive_name, input_directory
    ])
    zip_output = subprocess.check_output(args)
    return archive_name
