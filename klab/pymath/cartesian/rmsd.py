import numpy

def compute_rmsd_by_matrix(dataframe_1, dataframe_2, use_assertion = False):
    '''Computes the RMSD of two pandas dataframes. The dataframes are expected to be of equal dimensions and use_assertion
       can be set to assert that the row indices match. '''
    if use_assertion: assert([i for i in dataframe_1.index] == [i for i in dataframe_2.index]) # Note: this assertion creates garbage memory allocations
    num_points = dataframe_1.shape[0]
    return numpy.linalg.norm(dataframe_1 - dataframe_2) / numpy.sqrt(num_points)
