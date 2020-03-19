import warnings
warnings.warn(
    ("import api.client.crop_model.* will be deprecated in a future release."
     "Please import gro.crop_model.* instead"),
    PendingDeprecationWarning
)

from gro.crop_model import CropModel as CropModel
