import os
import glob
import re
import gzip
import json
import subprocess

FUDGE_FACTOR = 81 #

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


def rewrite_score_file(old_filepath, backup_filepath, new_filepath, mapping, nmerage, num_fragments):
    print('')
    lines = read_file(old_filepath).split('\n')

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
            assert(mapping.get(str(residue_id)))
            new_lines.append('%s%s' % (str(mapping[str(residue_id)] + FUDGE_FACTOR).rjust(11), l[11:]))
            assert(len(new_lines[-1]) == len(l))

    colortext.message('Rewriting fragments score file for %d-mers with %d fragments...' % (nmerage, num_fragments))
    os.rename(old_filepath, backup_filepath)
    write_file(new_filepath, '\n'.join(new_lines))
    colortext.message(must_zip_output)
    if os.path.exists(new_filepath + '.gz'):
        os.remove(new_filepath + '.gz')
    if must_zip_output:
        stdout, stderr, errorcode = Popen(os.path.split(new_filepath)[0], ['gzip', os.path.split(new_filepath)[1]])
        assert(errorcode == 0)

def rewrite_fragments_file(old_filepath, backup_filepath, new_filepath, mapping, nmerage, num_fragments):
    print('')
    lines = read_file(old_filepath).split('\n')

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
            assert(mapping.get(str(residue_id)))
            new_lines.append('position:%s%s' % (str(mapping[str(residue_id)] + FUDGE_FACTOR).rjust(13), l[22:]))
            assert(len(new_lines[-1]) == len(l))
        else:
            new_lines.append(l)

    colortext.message('Rewriting fragments file for %d-mers with %d fragments...' % (nmerage, num_fragments))
    os.rename(old_filepath, backup_filepath)
    write_file(new_filepath, '\n'.join(new_lines))
    colortext.message(must_zip_output)
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
        print(mapping)
        print('')
        for d in os.listdir('.'):
            if os.path.isdir(d):
                for f in sorted(glob.glob(os.path.join(d, "*mers")) + glob.glob(os.path.join(d, "*mers.gz"))):
                    if f.find('backup') != -1 or f.find('rewrite') != -1:
                        continue
                    mtchs = re.match('(.*?frags)[.](\d+)[.]score[.](\d+)[.](\d+)mers[.]?(gz)?', f)
                    if mtchs:
                        print(f)
                        assert(mtchs.group(2) == mtchs.group(4))
                        nmerage = int(mtchs.group(2))
                        num_fragments = int(mtchs.group(2))
                        old_filepath = mtchs.group(0)
                        # Kale wanted to change the filename for the scores so that it is easier to distinguish between score and fragments files using glob

                        backup_filepath = '%s.%s.%sbackup.score.%s' % (mtchs.group(1), mtchs.group(3), mtchs.group(4), mtchs.group(5))
                        new_filepath = ('%s.%s.%smers.rewrite.score.%s' % (mtchs.group(1), mtchs.group(3), mtchs.group(4), mtchs.group(5))).replace('.gz', '')
                        rewrite_score_file(old_filepath, backup_filepath, new_filepath, mapping, nmerage, num_fragments)
                    else:
                        mtchs = re.match('(.*)[.](\d+)[.](\d+)mers[.]?(gz)?', f)
                        if mtchs:
                            print(f)
                            nmerage = int(mtchs.group(2))
                            num_fragments = int(mtchs.group(3))
                            old_filepath = mtchs.group(0)
                            backup_filepath= '%s.%s.%sbackup.%s' % (mtchs.group(1), mtchs.group(2), mtchs.group(3), mtchs.group(4))
                            new_filepath= ('%s.%s.%sbackup.rewrite.%s' % (mtchs.group(1), mtchs.group(2), mtchs.group(3), mtchs.group(4))).replace('.gz', '')
                            rewrite_fragments_file(old_filepath, backup_filepath, new_filepath, mapping, nmerage, num_fragments)

#2silA_frags.3.score.200.3mers.gz

        import sys
        sys.exit(0)

        for dirpath, dirnames, filenames in os.walk('.'):
            print(1)
            print(dirpath, dirnames, filenames)
        a='''
            frags.9.score.200.9mers

            for f in glob.glob(os.path.join(scratch_path, "*mers")) + [os.path.join(scratch_path, 'ss_blast')]:
                pass

/2silA_frags.9.score.200.9mers.gz

position:            1 neighbors:          200
position:            9 neighbors:          200

 3fm3 A   220 G L -147.838  140.069  162.241   19.330  -15.590   29.710
 3fm3 A   221 I L -106.823  125.308 -168.239   16.930  -16.440   32.500

EKSVVFKGNTIVGSGSGGTTKYFRIPAMTSKG

9-mers

#query_pos  vall_pos  pdbid c ss  ProfileScoreL1 SecondarySimilarity SolventAccessibility RamaScore Phi Psi ProfileScoreStructL1  TOTAL  FRAG_ID
          1        136  1gen A E           0.59                0.17                 0.14      0.00   0.07   0.36                 0.56    3.500   3743772
          1         57  3m4w A E           0.66                0.16                 0.10      0.01   0.11   0.34                 0.56    3.535    343056
...
         24

3-mers
#query_pos  vall_pos  pdbid c ss  ProfileScoreL1 SecondarySimilarity SolventAccessibility RamaScore Phi Psi ProfileScoreStructL1  TOTAL  FRAG_ID
          1        220  3fm3 A L           0.49                0.28                 0.13      0.00   0.03   0.08                 0.52    1.768   2266884
          1        390  2acx A L           0.39                0.36                 0.13      0.00   0.02   0.03                 0.60    1.786   3077962
...
         30        138  2a9d A L           0.38                0.16                 0.15      0.00   0.11   0.11                 0.50    1.880   1324419

whitespace important?
index specifies *left* index of segment

'''
