#!/usr/bin/env python3

# Utilities for parsing the log files from certain protocols.

import re
from pathlib import Path

class LoopModelingTrajectory:
    prefix = 'protocols.loop_modeling.Loop(Builder|Protocol): '
    stage_prefix = 'protocols.loop_modeler.LoopModeler: '

    shared_pats = {
            'index': '[,0-9]+',
            'int': '[0-9]+',
            'float': '[-.0-9]+',
            'bool': '[01]',
    }

    build_pat = re.compile(stage_prefix + '\s*Build Stage')
    centroid_pat = re.compile(stage_prefix + '\s*Centroid Stage')
    fullatom_pat = re.compile(stage_prefix + '\s*Fullatom Stage')
    ramp_sfxn_pat = re.compile(prefix +
            'Ramp score function:\s*'
                'score: (?P<score>{float}) REU; '
                'chainbreak: (?P<chainbreak>{float}); '
                'fa_rep: (?P<fa_rep>{float}); '
                'rama: (?P<rama>{float}); '
                'rama2b: (?P<rama2b>{float});'
            .format(**shared_pats),
    )
    ramp_temp_pat = re.compile(prefix +
            'Ramp temperature:\s*'
                'temperature: (?P<temperature>{float});'
            .format(**shared_pats),
    )
    propose_move_pat = re.compile(prefix +
            'Propose move:\s*'
                'iteration: (?P<iteration>{index}); '
                'proposed: (?P<proposed>{bool}); '
                'accepted: (?P<accepted>{bool}); '
                'score: (?P<score>{float}) REU; '
                '(RMSD: (?P<rmsd>{float}) Å; )?'
                'time: (?P<time>{float}) s;'
            .format(**shared_pats),
    )
    final_score_pat = re.compile(prefix + 
            'Final Score:\s*(?P<score>{float}) REU; '
            'Chainbreak:\s*(?P<chainbreak>{float}) REU'
            .format(**shared_pats),
    )
    final_rmsd_pat = re.compile(prefix + 
            'Final RMSD:\s*(?P<rmsd>{float}) Å '
            '\(all loops, backbone heavy atom, no superposition\)'
            .format(**shared_pats),
    )
    elapsed_time_path = re.compile(prefix + 
            'Elapsed Time:\s*(?P<time>{int}) sec'
            .format(**shared_pats),
    )

    @classmethod
    def from_path(cls, path, *args, **kwargs):
        with open(path) as file:
            stdout = file.read()
            return cls(stdout, *args, **kwargs)

    @classmethod
    def from_stdout(cls, stdout, *args, **kwargs):
        return cls(stdout, *args, **kwargs)


    def __init__(self, stdout):
        self.scores = {}
        self.rmsds = {}
        self.moves = {}
        self.times = {}

        lines = stdout.split('\n')

        curr_stage = None
        curr_sfxn = None
        curr_temp = None

        for line in lines:
            curr_stage = self.parse_stage(line) or curr_stage
            curr_sfxn = self.parse_ramp_sfxn(line) or curr_sfxn
            curr_temp = self.parse_ramp_temp(line) or curr_temp

            if not curr_stage:
                continue

            move = self.parse_move(line, curr_sfxn, curr_temp)
            if move:
                self.moves.setdefault(curr_stage, []).append(move)

            self.scores[curr_stage] = \
                    self.parse_final_score(line) or self.scores.get(curr_stage)
            self.rmsds[curr_stage] = \
                    self.parse_final_rmsd(line) or self.rmsds.get(curr_stage)
            self.times[curr_stage] = \
                    self.parse_elapsed_time(line) or self.times.get(curr_stage)

    @classmethod
    def parse_stage(cls, line):
        if cls.build_pat.match(line):
            return 'build'
        if cls.centroid_pat.match(line):
            return 'centroid'
        if cls.fullatom_pat.match(line):
            return 'fullatom'

    @classmethod
    def parse_ramp_sfxn(cls, line):
        ramp_sfxn = cls.ramp_sfxn_pat.match(line)
        if ramp_sfxn:
            return {
                    'chainbreak': float(ramp_sfxn.group('chainbreak')),
                    'fa_rep': float(ramp_sfxn.group('fa_rep')),
                    'rama': float(ramp_sfxn.group('rama')),
                    'rama2b': float(ramp_sfxn.group('rama2b')),
            }

    @classmethod
    def parse_ramp_temp(cls, line):
        ramp_temp = cls.ramp_temp_pat.match(line)
        if ramp_temp:
            return float(ramp_temp.group('temperature'))

    @classmethod
    def parse_move(cls, line, curr_sfxn, curr_temp):
        propose_move = cls.propose_move_pat.match(line)
        if propose_move:
            return {
                    'iteration': propose_move.group('iteration'),
                    'proposed': propose_move.group('proposed') == '1',
                    'accepted': propose_move.group('accepted') == '1',
                    'score': float(propose_move.group('score')),
                    'rmsd': float(propose_move.group('rmsd')),
                    'time': float(propose_move.group('time')),
                    'temperature': curr_temp,
                    'scorefxn': curr_sfxn,
            }
    @classmethod
    def parse_final_score(cls, line):
        final_score = cls.final_score_pat.match(line)
        if final_score:
            return float(final_score.group('score'))

    @classmethod
    def parse_final_rmsd(cls, line):
        final_rmsd = cls.final_rmsd_pat.match(line)
        if final_rmsd:
            return float(final_rmsd.group('rmsd'))
            
    @classmethod
    def parse_elapsed_time(cls, line):
        elapsed_time = cls.elapsed_time_path.match(line)
        if elapsed_time:
            return float(elapsed_time.group('time'))
    
