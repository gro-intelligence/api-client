try:
    # Python 3.3+
    from unittest.mock import patch, MagicMock
except ImportError:
    # Python 2.7
    from mock import patch, MagicMock
from datetime import date
from unittest import TestCase

from groclient import Experimental

MOCK_HOST = "pytest.groclient.url"
MOCK_TOKEN = "pytest.groclient.token"

class ExperimentalTests(TestCase):
    def setUp(self):
        self.client = Experimental(MOCK_HOST, MOCK_TOKEN)
        self.assertTrue(isinstance(self.client, Experimental))
