from groclient import GroClient as BatchClient
from groclient.client import BatchError
from groclient.lib import get_default_logger


logger = get_default_logger()
logger.warning('''
    Deprecation Warning!

    You are importing modules from deprecated `api` module to access Gro
    Intelligence's API.  Please update your code to import from the `groclient`
    module instead.  The `api.client.batch_client` module will be removed by 2021-03-31.

    Replace: api.client.batch_client.BatchClient
       with: groclient.client.GroClient

    Please reach out to api-support@gro-intelligence.com if you need any help!
''')
