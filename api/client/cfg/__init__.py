from groclient.cfg import *
from groclient.lib import get_default_logger


logger = get_default_logger()
logger.warning('''
    Deprecation Warning!

    You are importing modules from deprecated `api` module to access Gro
    Intelligence's API.  Please update your code to import from the `groclient`
    module instead.  The `api.client.cfg` module will be removed by 2021-03-31.

    Replace: api.client.cfg
       with: groclient.cfg

    Please reach out to api-support@gro-intelligence.com if you need any help!
''')
