import sys
import os

def get_file_lines(filepath):
    output_handle = open(filepath, 'r')
    contents = output_handle.read()
    output_handle.close()
    return contents.splitlines()

if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) != 1:
        raise Exception('Expected 1 argument, a PDB file.')
    filename = args[0]
    if not os.path.exists(filename):
        raise Exception('%s does not exist.')
    new_lines = []
    new_chain_ids = sorted(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'], reverse = True)
    chain_map = {}
    found_chains = set()
    for line in get_file_lines(filename):
        if line.startswith('ATOM  ') or line.startswith('HETATM'):
            chain_id = line[21]
            if chain_id not in chain_map:
                chain_map[chain_id] = new_chain_ids.pop() # this will fail after 26 ids have been used up
            new_lines.append('%s%s%s' % (line[:21], chain_map[chain_id], line[22:]))
        else:
            new_lines.append(line)
    print('\n'.join(new_lines))