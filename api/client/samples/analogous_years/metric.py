
import pandas as pd
import numpy as np
from scipy.spatial.distance import euclidean, squareform, pdist

def euclidean_dist_matrix(dataframe):
    return pd.DataFrame(squareform(pdist(dataframe)))
    
