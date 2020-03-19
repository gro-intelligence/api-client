import warnings
warnings.warn(
    ("import api.client.gro_client.* will be deprecated in a future release."
     "Please import gro.client.* instead"),
    PendingDeprecationWarning
)

from gro.client import GroClient as GroClient
