# contents of test_app.py, a simple test for our API retrieval
import pytest
import requests


# Prevent `requests` from making any inadvertent API calls in tests
@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    monkeypatch.delattr("requests.sessions.Session.request")
