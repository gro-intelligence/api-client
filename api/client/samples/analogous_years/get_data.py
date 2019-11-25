import os
import pandas as pd
import numpy as np

from api.client.gro_client import GroClient

API_HOST = 'api.gro-intelligence.com'
ACCESS_TOKEN = os.environ['GROAPI_TOKEN']
client = GroClient(API_HOST, ACCESS_TOKEN)



def get_data(entity):
    '''
    :param entity: metric_id, item_id, region_id
    :return: a pandas dataframe with time series data
    '''
    data = client.get_data_points(**{'metric_id': 2100031,
                                                 'item_id': 2039, 
                                                 'region_id': 1107, 
                                                 'source_id': 35, 
                                                 'frequency_id': 1}
                                             )
    data = pd.DataFrame(data)
    #data['year'] = data.apply(lambda x: str(x['end_date'].year), axis = 1)
    #data['dayofyear'] = data.apply(lambda x: int(x['end_ate'].dayofyear), axis = 1)
    return data
