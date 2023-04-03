from groclient.client import GroClient
from groclient.crop_model import CropModel
from groclient.experimental import Experimental

# Do a runtime lookup to get the groclient package version info.
__version__ = lib.get_version_info().get('api-client-version', 'unknown')
