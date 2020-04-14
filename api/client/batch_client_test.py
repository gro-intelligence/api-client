from unittest import TestCase
from api.client.batch_client import BatchClient

MOCK_HOST = 'pytest.groclient.url'
MOCK_TOKEN = 'pytest.groclient.token'

class BatchClientTests(TestCase):
    def test_initialization(self):
        client = BatchClient(MOCK_HOST, MOCK_TOKEN)
        self.assertIsInstance(client, BatchClient)
