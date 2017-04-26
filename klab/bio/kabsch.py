#!/usr/bin/env python2
# encoding: utf-8

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

import random
import numpy as np
from klab.rmsd.RMSDWrapper import rmsd

def centroid(X):
    """
    Calculate the centroid from a matrix X
    """
    C = np.sum(X, axis=0) / len(X)
    return C

def calc_rotation_translation_matrices( ref_coords, new_coords ):
    new = np.matrix(new_coords)
    ref = np.matrix(ref_coords)

    # Create the centroid of new and ref which is the geometric center of a
    # N-dimensional region and translate new and ref onto that center.
    # http://en.wikipedia.org/wiki/Centroid
    new_centroid = centroid(new)
    ref_centroid = centroid(ref)
    new -= new_centroid
    ref -= ref_centroid

    # Compute translation vector (matrix)
    T = ref_centroid - new_centroid

    # Computation of the covariance matrix
    C = np.dot(np.transpose(new), ref)

    # Computation of the optimal rotation matrix
    # This can be done using singular value decomposition (SVD)
    # Getting the sign of the det(V)*(W) to decide
    # whether we need to correct our rotation matrix to ensure a
    # right-handed coordinate system.
    # And finally calculating the optimal rotation matrix U
    # see http://en.wikipedia.org/wiki/Kabsch_algorithm
    V, S, W = np.linalg.svd(C)
    d = (np.linalg.det(V) * np.linalg.det(W)) < 0.0

    if d:
        S[-1] = -S[-1]
        V[:, -1] = -V[:, -1]

    # Create Rotation matrix U
    U = np.dot(V, W)

    return (U, new_centroid, ref_centroid)

def kabsch( ref_coords, moving_coords):
    U, new_centroid, ref_centroid = calc_rotation_translation_matrices( ref_coords, moving_coords )
    moving_coords = np.matrix( moving_coords )
    new_coords = moving_coords - new_centroid
    new_coords = np.dot( new_coords, U )
    new_coords += ref_centroid
    return new_coords

def bakan_bahar_ensemble_align(coords, tolerance = 0.001, verbose = False ):
    '''
    input: a list of coordinates in the format:
    [
      [ (x, y, z), (x, y, z), (x, y, z) ], # atoms in model 1
      [ (x, y, z), (x, y, z), (x, y, z) ], # atoms in model 2
      # etc.
    ]
    '''
    rmsd_tolerance = float("inf")
    average_struct_coords = np.array( random.choice(coords) )
    cycle_count = 0
    while( rmsd_tolerance > tolerance ):
        if verbose:
            print 'Cycle %d alignment, current tolerance: %.4f (threshold %.4f)' % (cycle_count, rmsd_tolerance, tolerance)
        old_average_struct_coords = average_struct_coords
        coords = np.array([ kabsch( average_struct_coords, x ) for x in coords ])
        average_struct_coords = np.mean( coords, axis = 0 )
        rmsd_tolerance = rmsd( old_average_struct_coords, average_struct_coords )
        cycle_count += 1
    return coords
