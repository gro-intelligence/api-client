from api.client.lib import get_default_logger
logger = get_default_logger()
logger.warning('''
    Deprecation Warning:
    Please import from the gro package instead of api.client.
    The api.client package will be removed in a future update.
''')