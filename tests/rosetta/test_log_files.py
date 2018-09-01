#!/usr/bin/env python3

from pytest import approx
from klab.rosetta.log_files import LoopModelingTrajectory

def test_loop_modeling_log():
    with open('loop_modeling_log.stdout') as file:
        stdout = file.read()

    traj = LoopModelingTrajectory.from_path('loop_modeling_log.stdout')

    assert traj.scores['build'] == approx(-157.192)
    assert traj.rmsds['build'] == approx(7.729)
    assert traj.times['build'] == 6

    assert traj.scores['centroid'] == approx(-186.183)
    assert traj.rmsds['centroid'] == approx(7.229)
    assert traj.times['centroid'] == 473

    assert traj.scores['fullatom'] == approx(-400.970)
    assert traj.rmsds['fullatom'] == approx(8.618)
    assert traj.times['fullatom'] == 7335

    assert traj.moves['build'][0] == {
            'iteration': '1',
            'proposed': True,
            'accepted': True,
            'score': approx(-102.348),
            'rmsd': approx(7.331),
            'time': 5,
            'temperature': None,
            'scorefxn': None,
    }

    assert traj.moves['centroid'][-2] == {
            'iteration': '5,319,1',
            'proposed': True,
            'accepted': True,
            'score': approx(-182.855),
            'rmsd': approx(3.915),
            'time': 473,
            'temperature': approx(1.000),
            'scorefxn': approx({
                'chainbreak': 16.65,
                'fa_rep': 0.00,
                'rama': 0.10,
                'rama2b': 0.00,
            })
    }
    assert traj.moves['centroid'][-1] == {
            'iteration': '5,320,1',
            'proposed': True,
            'accepted': True,
            'score': approx(-182.878),
            'rmsd': approx(3.914),
            'time': 473,
            'temperature': approx(1.000),
            'scorefxn': approx({
                'chainbreak': 16.65,
                'fa_rep': 0.00,
                'rama': 0.10,
                'rama2b': 0.00,
            })
    }
    assert traj.moves['fullatom'][-2] == {
            'iteration': '5,160,1',
            'proposed': True,
            'accepted': False,
            'score': approx(-400.593),
            'rmsd': approx(8.622),
            'time': 7323,
            'temperature': approx(0.500),
            'scorefxn': approx({
                'chainbreak': 16.65,
                'fa_rep': 0.55,
                'rama': 0.00,
                'rama2b': 0.00,
            })
    }
    assert traj.moves['fullatom'][-1] == {
            'iteration': '5,160,2',
            'proposed': True,
            'accepted': False,
            'score': approx(-400.593),
            'rmsd': approx(8.622),
            'time': 7327,
            'temperature': approx(0.500),
            'scorefxn': approx({
                'chainbreak': 16.65,
                'fa_rep': 0.55,
                'rama': 0.00,
                'rama2b': 0.00,
            })
    }

def test_loop_modeling_stage():
    nothing  = 'protocols.loop_modeler.LoopModeler: *******************************************'
    build    = 'protocols.loop_modeler.LoopModeler:    Build Stage                             '
    centroid = 'protocols.loop_modeler.LoopModeler:    Centroid Stage                          '
    fullatom = 'protocols.loop_modeler.LoopModeler:    Fullatom Stage                          '

    assert LoopModelingTrajectory.parse_stage(nothing)  ==  None
    assert LoopModelingTrajectory.parse_stage(build)    == 'build'
    assert LoopModelingTrajectory.parse_stage(centroid) == 'centroid'
    assert LoopModelingTrajectory.parse_stage(fullatom) == 'fullatom'

def test_loop_modeling_ramp_sfxn():
    line = 'protocols.loop_modeling.LoopProtocol: Ramp score function:  score: -151.357 REU; chainbreak: 3.33; fa_rep: 0.00; rama: 0.10; rama2b: 0.00; '
    assert LoopModelingTrajectory.parse_ramp_sfxn(line) == approx({
            'chainbreak': 3.33,
            'fa_rep': 0.00,
            'rama': 0.10,
            'rama2b': 0.00,
    })

def test_loop_modeling_ramp_temp():
    line = 'protocols.loop_modeling.LoopProtocol: Ramp temperature:     temperature: 1.999; '
    assert LoopModelingTrajectory.parse_ramp_temp(line) == approx(1.999)

def test_loop_modeling_move():
    line = 'protocols.loop_modeling.LoopProtocol: Propose move:         iteration: 1,1,1; proposed: 1; accepted: 0; score: -151.357 REU; RMSD: 7.729 Å; time: 1 s; '
    assert LoopModelingTrajectory.parse_move(line, None, None) == {
            'iteration': '1,1,1',
            'proposed': True,
            'accepted': False,
            'score': approx(-151.357),
            'rmsd': approx(7.729),
            'time': 1,
            'temperature': None,
            'scorefxn': None,
    }

def test_loop_modeling_final_score():
    line = 'protocols.loop_modeling.LoopProtocol: Final Score: -186.183 REU; Chainbreak: 0.008 REU'
    assert LoopModelingTrajectory.parse_final_score(line) == approx(-186.183)

def test_loop_modeling_final_rmsd():
    line = 'protocols.loop_modeling.LoopProtocol: Final RMSD: 7.229 Å (all loops, backbone heavy atom, no superposition)'
    assert LoopModelingTrajectory.parse_final_rmsd(line) == approx(7.229)

def test_loop_modeling_elapsed_time():
    line = 'protocols.loop_modeling.LoopProtocol: Elapsed Time: 473 sec'
    assert LoopModelingTrajectory.parse_elapsed_time(line) == approx(473)
