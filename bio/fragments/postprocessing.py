import os
import glob
import re
import gzip
import json
import subprocess

FUDGE_FACTOR = 81 # !!!

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

def is_valid_fragment(original_residue_id, mapping, nmerage):
    for r in mapping['segment_list']:
        r = sorted(r)
        if r[0] - nmerage + 1 <= original_residue_id <= r[1] + nmerage - 1:
            return True
    return False

def rewrite_score_file(old_filepath, backup_filepath, new_filepath, mapping, nmerage, num_fragments):
    lines = read_file(old_filepath).split('\n')

    reverse_mapping = mapping['reverse_mapping']
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
            if is_valid_fragment(original_residue_id, mapping, nmerage):
                new_lines.append('%s%s' % (str(reverse_mapping[str(residue_id)] + FUDGE_FACTOR).rjust(11), l[11:]))
                assert(len(new_lines[-1]) == len(l))

    colortext.message('Rewriting fragments score file %s for %d-mers with %d fragments...' % (old_filepath, nmerage, num_fragments))
    os.rename(old_filepath, backup_filepath)
    write_file(new_filepath, '\n'.join(new_lines))
    if os.path.exists(new_filepath + '.gz'):
        os.remove(new_filepath + '.gz')
    if must_zip_output:
        stdout, stderr, errorcode = Popen(os.path.split(new_filepath)[0], ['gzip', os.path.split(new_filepath)[1]])
        assert(errorcode == 0)

def rewrite_fragments_file(old_filepath, backup_filepath, new_filepath, mapping, nmerage, num_fragments):
    lines = read_file(old_filepath).split('\n')

    reverse_mapping = mapping['reverse_mapping']
    return

    must_zip_output = old_filepath.endswith('.gz')
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
            new_lines.append('position:%s%s' % (str(reverse_mapping[str(residue_id)] + FUDGE_FACTOR).rjust(13), l[22:]))
            assert(len(new_lines[-1]) == len(l))
        else:
            new_lines.append(l)

    colortext.message('Rewriting fragments file %s for %d-mers with %d fragments...' % (old_filepath, nmerage, num_fragments))
    os.rename(old_filepath, backup_filepath)
    write_file(new_filepath, '\n'.join(new_lines))
    if os.path.exists(new_filepath + '.gz'):
        os.remove(new_filepath + '.gz')
    if must_zip_output:
        stdout, stderr, errorcode = Popen(os.path.split(new_filepath)[0], ['gzip', os.path.split(new_filepath)[1]])
        assert(errorcode == 0)

if __name__ == '__main__':
    import sys
    sys.path.insert(0, '../../../..')
    import colortext
    if os.path.exists('segment_map.json'):
        mapping = json.loads(open('segment_map.json').read())
        for d in sorted(os.listdir('.')):
            if os.path.isdir(d):
                for f in sorted(glob.glob(os.path.join(d, "*mers")) + glob.glob(os.path.join(d, "*mers.gz"))):
                    if f.find('backup') != -1 or f.find('rewrite') != -1:
                        continue
                    mtchs = re.match('(.*?frags)[.](\d+)[.]score[.](\d+)[.](\d+)mers[.]?(gz)?', f)
                    if mtchs:
                        assert(mtchs.group(2) == mtchs.group(4))
                        nmerage = int(mtchs.group(2))
                        num_fragments = int(mtchs.group(3))
                        old_filepath = mtchs.group(0)
                        # Kale wanted to change the filename for the scores so that it is easier to distinguish between score and fragments files using glob

                        backup_filepath = '%s.%s.%smers.backup.score.%s' % (mtchs.group(1), mtchs.group(3), mtchs.group(4), mtchs.group(5))
                        new_filepath = ('%s.%s.%smers.rewrite.score.%s' % (mtchs.group(1), mtchs.group(3), mtchs.group(4), mtchs.group(5))).replace('.gz', '')
                        rewrite_score_file(old_filepath, backup_filepath, new_filepath, mapping, nmerage, num_fragments)
                    else:
                        mtchs = re.match('(.*)[.](\d+)[.](\d+)mers[.]?(gz)?', f)
                        if mtchs:
                            nmerage = int(mtchs.group(3))
                            num_fragments = int(mtchs.group(2))
                            old_filepath = mtchs.group(0)
                            backup_filepath= '%s.%s.%smers.backup.%s' % (mtchs.group(1), mtchs.group(2), mtchs.group(3), mtchs.group(4))
                            new_filepath= ('%s.%s.%smers.rewrite.%s' % (mtchs.group(1), mtchs.group(2), mtchs.group(3), mtchs.group(4))).replace('.gz', '')
                            rewrite_fragments_file(old_filepath, backup_filepath, new_filepath, mapping, nmerage, num_fragments)

