""" Views """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"


from .view import View

# Import all views
from .notes import NotesView

# List all views
all_views = (
    NotesView,
)
