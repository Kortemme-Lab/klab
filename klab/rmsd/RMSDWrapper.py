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
import numpy as np
import scipy.spatial.distance

def pairwise_rmsd(input_pdbs):
    coordinates = np.array( [prody.parsePDB(input_pdb).select('calpha').getCoords() for input_pdb in input_pdbs] )

    rmsd_matrix = pyRMSD.matrixHandler.MatrixHandler().createMatrix(coordinates, pyrmsd_calc)
    print scipy.spatial.distance.squareform( rmsd_matrix.get_data() )


if __name__ == '__main__':
    pdb_dir = os.path.join('..', '..', '.testdata','pdbs')
    input_pdbs = sorted( [os.path.join(pdb_dir, f ) for f in os.listdir(pdb_dir)] )
    pairwise_rmsd( input_pdbs[:2] )
