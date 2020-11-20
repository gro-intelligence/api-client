from groclient.crop_model import CropModel
from groclient.lib import get_default_logger


logger = get_default_logger()
logger.warning('''
    Deprecation Warning!

    You are importing modules from deprecated `api` module to access Gro
    Intelligence's API.  Please update your code to import from the `groclient`
    module instead.  The `api.client.crop_model` module will be removed by 2021-03-31.

    Replace: api.client.crop_model
       with: groclient.crop_model

    Please reach out to api-support@gro-intelligence.com if you need any help!
''')
