#!/usr/bin/env python3

"""\
Parse the per-residue score information from a PDB file produced by rosetta, 
then display that information in a spreadsheet program (e.g. excel).

Usage:
    klab_scores_from_pdb <pdb> [<reference_pdb>] [-s]

Arguments:
    <pdb>
        A PDB file containing a score table produced by Rosetta.  Any score 
        function can be used; the relevant score terms will automatically be 
        extracted.

    <reference_pdb>
        Optionally, a second Rosetta-scored PDB file.  In addition to 
        per-residue scores for both files, the per-residue score differences 
        will also be reported.

Options:
    -s --sort
        Sort the rows in the spreadsheet by total score, rather than simply 
        going in residue order.

If a reference PDB is given, the workbook that will be opened will have three 
sheets: one for each PDB, and one showing the difference between the two.
"""

import os, sys, re, subprocess
import pandas as pd
from pathlib import Path
from tempfile import mkstemp

def scores_from_pdb(pdb_path):
    if pdb_path.suffix == '.gz':
        import gzip
        open = gzip.open
    else:
        import builtins
        open = builtins.open

    with open(pdb_path, 'rt') as file:
        lines = file.readlines()

    table = []
    mode = None
    resni_pattern = re.compile('(\w{3})(?:.*)_(\d+)')

    for line in lines:
        line = line.strip()

        if line.startswith('#BEGIN_POSE_ENERGIES_TABLE'):
            mode = 'header'

        elif line.startswith('#END_POSE_ENERGIES_TABLE'):
            mode = None

        elif mode == 'header':
            header = line.split()[1:]
            mode = 'weights'

        elif mode == 'weights':
            weights = map(float, line.split()[1:])
            mode = 'scores'

        elif mode == 'scores':
            tokens = line.split()
            scores = map(float, tokens[1:])

            row = {}

            if tokens[0] == 'pose':
                row['resi'] = '*'
                row['resn'] = '*'
            else:
                resni_match = resni_pattern.match(tokens[0])
                if not resni_match:
                    raise ValueError(f"encountered unexpected line in score table:\n\n{line}")

                row['resi'] = resni_match.group(2)
                row['resn'] = resni_match.group(1)

            for term, score in zip(header, scores):
                row[term] = score

            table.append(row)

    cols = ['resi', 'resn', *header]
    df = pd.DataFrame(table, columns=cols)
    return df

def open_with_default_app(file):
    if sys.platform == 'linux':
        cmd = 'xdg-open'
    elif sys.platform == 'darwin':
        cmd = 'open'
    elif sys.platform == 'win32':
        cmd = 'start'

    subprocess.run([cmd, file])

def subtract_scores(a, b):
    exclude = ['resi', 'resn']
    include = [x for x in a.columns if x in b.columns and x not in exclude]

    diff = a.copy()
    diff[include] = a[include] - b[include]

    return diff

def main():
    import docopt

    args = docopt.docopt(__doc__)
    pdb_path = Path(args['<pdb>'])
    scores = scores_from_pdb(pdb_path)
    sheets = {
            pdb_path.stem: scores
    }

    if args['<reference_pdb>']:
        ref_path = Path(args['<reference_pdb>'])
        ref_scores = scores_from_pdb(ref_path)
        sheets = {
                f'{pdb_path.stem} − {ref_path.stem}':
                    subtract_scores(scores, ref_scores),
                pdb_path.stem: scores, 
                f'{ref_path.stem} (ref)': ref_scores, 
        }

    try:
        pid = 0
        tmp_fp, tmp_path = mkstemp(suffix=f'.{pdb_path.stem}.xls')

        with pd.ExcelWriter(tmp_path) as xls:
            for name, df in sheets.items():
                if args['--sort']:
                    df = df.sort_values('total', ascending=False)

                df.to_excel(
                        xls, name,
                        index=False,
                        freeze_panes=(1, 0),
                )
            
        pid = os.fork()
        if pid == 0:
            open_with_default_app(tmp_path)

    finally:
        if pid == 0:
            os.remove(tmp_path)


if __name__ == '__main__':
    main()
