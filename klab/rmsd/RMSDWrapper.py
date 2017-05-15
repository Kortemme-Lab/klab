import pyRMSD
from pyRMSD.matrixHandler import MatrixHandler
import pyRMSD.RMSDCalculator
from pyRMSD.availableCalculators import availableCalculators
# Use CUDA for GPU calculations, if avialable
if 'QCP_CUDA_MEM_CALCULATOR' in availableCalculators():
    pyrmsd_calc = 'QCP_CUDA_MEM_CALCULATOR'
else:
    pyrmsd_calc = 'QCP_SERIAL_CALCULATOR'

import pyRMSD
import prody
import os
import sys
import numpy as np
import scipy.spatial.distance

# Disable
def blockPrint():
    sys.stdout = open(os.devnull, 'w')

# Restore
def enablePrint():
    sys.stdout = sys.__stdout__

def pairwise_rmsd(input_pdbs):
    coordinates = np.array( [prody.parsePDB(input_pdb).select('calpha').getCoords() for input_pdb in input_pdbs] )

    blockPrint()
    rmsd_matrix = pyRMSD.matrixHandler.MatrixHandler().createMatrix(coordinates, pyrmsd_calc)
    enablePrint()
    print scipy.spatial.distance.squareform( rmsd_matrix.get_data() )

def pairwise_rmsd_of_coords(coords):
    coordinates = np.array( coords )

    blockPrint()
    rmsd_matrix = pyRMSD.matrixHandler.MatrixHandler().createMatrix(coordinates, pyrmsd_calc)
    enablePrint()

    # return scipy.spatial.distance.squareform( rmsd_matrix.get_data() )
    return rmsd_matrix

def rmsd( coords_1, coords_2):
    blockPrint()
    rmsd_matrix = pyRMSD.matrixHandler.MatrixHandler().createMatrix(np.array([coords_1, coords_2]), pyrmsd_calc)
    enablePrint()
    return scipy.spatial.distance.squareform( rmsd_matrix.get_data() )[0][1]

if __name__ == '__main__':
    pdb_dir = os.path.join('..', '..', '.testdata','pdbs')
    input_pdbs = sorted( [os.path.join(pdb_dir, f ) for f in os.listdir(pdb_dir)] )
    pairwise_rmsd( input_pdbs[:2] )
