""" Models. """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"


from .model import Model

# Import others in order for them to be registered.
from .main import MainModel
from .notes import NotesModel


# All models
all_models = (
    MainModel,
    NotesModel
)

