import os
import glob
import re
import gzip
import json
import subprocess

def read_file(filepath, binary = False):
    if binary:
        output_handle = open(filepath, 'rb')
    elif filepath.endswith('.gz'):
        output_handle = gzip.open(filepath, 'r')
    else:
        output_handle = open(filepath, 'r')
    contents = output_handle.read()
    output_handle.close()
    return contents

def write_file(filepath, contents, ftype = 'w'):
    output_handle = open(filepath, ftype)
    output_handle.write(contents)
    output_handle.close()

def Popen(outdir, args):
    subp = subprocess.Popen([str(arg) for arg in args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=outdir, env={'SPARKSXDIR' : '/netapp/home/klabqb3backrub/tools/sparks-x'})
    output = subp.communicate()
    return output[0], output[1], subp.returncode # 0 is stdout, 1 is stderr

def is_valid_fragment(original_residue_id, mapping, frag_sizes):
    '''A function which determines whether a residue ID (original_residue_id) should be included in the nmer files generated by the mapping.'''
    for r in mapping['segment_list']:
        r = sorted(r)
        if r[0] - frag_sizes + 1 <= original_residue_id <= r[1] + frag_sizes - 1:
            return True
    return False

def rewrite_score_file(task_dir, old_filepath, backup_filepath, new_filepath, mapping, frag_sizes, num_fragments):
    lines = read_file(old_filepath).split('\n')

    reverse_mapping = mapping['reverse_mapping'].get(task_dir) or mapping['reverse_mapping']['FASTA']
    must_zip_output = old_filepath.endswith('.gz')
    new_lines = []
    for l in lines:
        if l.startswith('#') or not(l.strip()):
            new_lines.append(l)
        else:
            tokens = l.split()
            assert(len(tokens) == 14)
            assert(l[:11].strip().isdigit())
            assert(l[11] == ' ')
            residue_id = int(l[:11])
            original_residue_id = reverse_mapping.get(str(residue_id))
            assert(original_residue_id != None)
            # Prune records which are not needed for these nmers
            if is_valid_fragment(original_residue_id, mapping, frag_sizes):
                new_lines.append('%s%s' % (str(reverse_mapping[str(residue_id)]).rjust(11), l[11:]))
                assert(len(new_lines[-1]) == len(l))

    print('Rewriting fragments score file %s for %d-mers with %d fragments...' % (old_filepath, frag_sizes, num_fragments))
    os.rename(old_filepath, backup_filepath)
    write_file(new_filepath, '\n'.join(new_lines))
    if os.path.exists(new_filepath + '.gz'):
        os.remove(new_filepath + '.gz')
    if must_zip_output:
        stdout, stderr, errorcode = Popen(os.path.split(new_filepath)[0], ['gzip', os.path.split(new_filepath)[1]])
        assert(errorcode == 0)

def rewrite_fragments_file(task_dir, old_filepath, backup_filepath, new_filepath, mapping, frag_sizes, num_fragments):
    lines = read_file(old_filepath).split('\n')

    reverse_mapping = mapping['reverse_mapping'].get(task_dir) or mapping['reverse_mapping']['FASTA']
    must_zip_output = old_filepath.endswith('.gz')

    # Rewrite the position: lines i.e. renumber the fragments in the file
    new_lines = []
    for l in lines:
        if l.startswith('position:'):
            assert(l.find('neighbors:') != -1)
            assert(l.find('neighbors:') != -1)
            tokens = l.split()
            assert(len(tokens) == 4)
            assert(l[9:22].strip().isdigit())
            assert(l[22] == ' ')
            residue_id = int(l[9:22])
            assert(reverse_mapping.get(str(residue_id)))
            new_lines.append('position:%s%s' % (str(reverse_mapping[str(residue_id)]).rjust(13), l[22:]))
            assert(len(new_lines[-1]) == len(l))
        else:
            new_lines.append(l)

    # Prune records which are not needed for these nmers
    new_content = '%s_grog_' % '\n'.join(new_lines)
    fragment_score_blocks = re.findall('(position:.*?)(?=position:|_grog_)', new_content, re.DOTALL)
    new_blocks = []
    for b in fragment_score_blocks:
        assert(b.startswith('position:'))
        residue_id = int(b.split('\n')[0][9:].split()[0])
        if is_valid_fragment(residue_id, mapping, frag_sizes):
            new_blocks.append(b)
    new_blocks = ''.join(new_blocks)

    print('Rewriting fragments file %s for %d-mers with %d fragments...' % (old_filepath, frag_sizes, num_fragments))
    os.rename(old_filepath, backup_filepath)
    write_file(new_filepath, new_blocks)
    if os.path.exists(new_filepath + '.gz'):
        os.remove(new_filepath + '.gz')
    if must_zip_output:
        stdout, stderr, errorcode = Popen(os.path.split(new_filepath)[0], ['gzip', os.path.split(new_filepath)[1]])
        assert(errorcode == 0)
        return new_filepath + '.gz'
    return new_filepath

def filter_fragments_file_by_secondary_structure(fragments_filepath, new_filepath, mapping, frag_sizes):

    stats = []
    must_zip_output = fragments_filepath.endswith('.gz')

    all_fragments = read_file(fragments_filepath) + '_grog_'
    fragment_score_blocks = re.findall('(position:.*?)(?=position:|_grog_)', all_fragments, re.DOTALL)
    new_blocks = []
    for b in fragment_score_blocks:
        # Iterate over the set of positions
        assert(b.startswith('position:'))
        header_line =  b.split('\n')[0]
        header_tokens = header_line.split()
        start_residue_id = int(header_tokens[1])
        num_fragments = int(header_tokens[3])

        new_block = []
        position_fragments = [pf for pf in b.split('\n\n') if pf.strip()]
        assert(len(position_fragments) == num_fragments + 1)
        assert(position_fragments[0].find('position:') != -1)

        for pf in position_fragments[1:]:
            # Iterate over the set of fragments per position
            passed_filter = True
            pflines = [l for l in pf.split('\n') if l.strip()]
            assert(len(pflines) == frag_sizes)
            c = start_residue_id
            for pfline in pflines:
                if str(c) in mapping:
                    expected_secondary_structure = mapping[str(c)]
                    fragment_secondary_structure = pfline.strip().split()[4]
                    if fragment_secondary_structure not in expected_secondary_structure:
                        passed_filter = False
                c += 1
            if passed_filter:
                new_block.append(pf)

        new_num_neighbors = len(new_block)
        if new_num_neighbors == 0:
            sys.stderr.write('WARNING: The block starting at position %d has no fragments remaining aftering filtering by secondary structure.\n' % start_residue_id)

        # Add the header by default
        mtchs = re.match('^(position:\s+\d+\s+neighbors:)(\s+\d+)(\s)*$', header_line)
        assert(mtchs)
        new_header_line = '%s%s%s' % (mtchs.group(1), str(new_num_neighbors).rjust(len(mtchs.group(2))), mtchs.group(3) or '')
        new_block.insert(0, new_header_line)
        new_blocks.append('\n\n'.join(new_block))
        stats.append(map(str, (start_residue_id, num_fragments, new_num_neighbors)))
    new_blocks = '\n\n'.join(new_blocks)

    s = 'Secondary structure filtering summary (%dmers)' % frag_sizes
    print('\n%s\n%s' % (s, len(s) * '*'))
    print('Residue ID     Number of fragments      Number of fragments after filtering')
    for stat in stats:
        print('%s%s%s' % (stat[0].ljust(15), stat[1].ljust(25), stat[2].ljust(0)))

    print('\nRewriting fragments file %s as %s for %d-mers with %d fragments...\n' % (fragments_filepath, new_filepath, frag_sizes, num_fragments))
    write_file(new_filepath, new_blocks)
    if os.path.exists(new_filepath + '.gz'):
        os.remove(new_filepath + '.gz')
    if must_zip_output:
        stdout, stderr, errorcode = Popen(os.path.split(new_filepath)[0], ['gzip', os.path.split(new_filepath)[1]])
        assert(errorcode == 0)
        return new_filepath + '.gz'
    return new_filepath

def post_process(task_dir):
    # Keep track of the files generated during post-processing, so we can 
    # report the final paths to the user in such a way that the user won't have 
    # to know which post-processing steps actually happened.

    frag_libs = {}

    # Load the segment map, if it exists.

    segment_map = None
    if os.path.exists('segment_map.json'):
        with open('segment_map.json') as file:
            segment_map = json.load(file)

    # Load the secondary structure filter, if it exists.

    ss_filter = None
    if os.path.exists('ss_filter.json'):
        with open('ss_filter.json') as file:
            ss_filter = json.load(file)['secondary_structure_filter']

    # Post-process each file one by one:

    frag_paths = \
        glob.glob(os.path.join(task_dir, "*mers")) + \
        glob.glob(os.path.join(task_dir, "*mers.gz"))

    for frag_path in frag_paths:

        # Perform any post-processing on the fragment file itself.  Keep track 
        # of the path to the most processed file, which is presumably the file 
        # the end-user will be the most interested in, so we can record it in a 
        # JSON file at the end.

        frag_match = re.match('(....)[.](\d+)[.](\d+)mers[.]?(gz)?', os.path.basename(frag_path))

        if frag_match:
            processed_path = frag_path
            frag_sizes = int(frag_match.group(3))
            num_fragments = int(frag_match.group(2))

            # If a segment map exists, use it to reindex the fragment file.  

            if segment_map:
                old_filepath = frag_match.group(0)
                backup_filepath = '%s.%s.%smers.backup.%s' % (frag_match.group(1), frag_match.group(2), frag_match.group(3), frag_match.group(4))
                new_filepath = ('%s.%s.%smers.rewrite.%s' % (frag_match.group(1), frag_match.group(2), frag_match.group(3), frag_match.group(4))).replace('.gz', '')
                processed_path = rewrite_fragments_file(task_dir, old_filepath, backup_filepath, new_filepath, segment_map, frag_sizes, num_fragments)

            # If a secondary structure filter exists, use it to remove any 
            # fragments that don't have the specified secondary structure.

            if ss_filter:
                new_filepath = ('%s.%s.%smers.rewrite.%s' % (frag_match.group(1), frag_match.group(2), frag_match.group(3), frag_match.group(4))).replace('.gz', '')
                processed_path = filter_fragments_file_by_secondary_structure(processed_path, new_filepath, ss_filter, frag_sizes)

            # Record the processed fragment file and some useful metadata.

            frag_libs[processed_path] = {
                    'frag_sizes': frag_sizes,
                    'num_fragments': num_fragments,
            }

        # Kale wanted to change the filename for the scores so that it is 
        # easier to distinguish between score and fragments files using glob.

        score_match = re.match('(...._frags)[.](\d+)[.]score[.](\d+)[.](\d+)mers[.]?(gz)?', os.path.basename(frag_path))

        if score_match and segment_map:
            assert score_match.group(2) == score_match.group(4)
            frag_sizes = int(score_match.group(2))
            num_fragments = int(score_match.group(3))
            old_filepath = score_match.group(0)
            backup_filepath = '%s.%s.%smers.backup.score.%s' % (score_match.group(1), score_match.group(3), score_match.group(4), score_match.group(5))
            new_filepath = ('%s.%s.%smers.rewrite.score.%s' % (score_match.group(1), score_match.group(3), score_match.group(4), score_match.group(5))).replace('.gz', '')
            rewrite_score_file(task_dir, old_filepath, backup_filepath, new_filepath, segment_map, frag_sizes, num_fragments)

    with open(os.path.join(task_dir, 'fragment_file_map.json'), 'w') as file:
        json.dump(frag_libs, file)


