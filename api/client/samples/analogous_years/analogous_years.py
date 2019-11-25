from get_data import get_data
from transformation import tsfresh_feature_extraction
from metric import euclidean_dist_matrix
from result import result

entity = 0

matrix = euclidean_dist_matrix(tsfresh_feature_extraction(get_data(entity)))

print(matrix)
print(result(matrix, 2019))

