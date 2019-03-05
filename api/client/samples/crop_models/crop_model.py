from __future__ import division
from builtins import map
from builtins import str
from builtins import zip
import pandas
import unicodecsv
from api.client import crop_model

# Deprecated: moved to api.client.crop_model, use that directly.
class CropModel(crop_model.CropModel):

    def __init__(self, api_host, access_token):
        super(CropModel, self).__init__(api_host, access_token)
    
