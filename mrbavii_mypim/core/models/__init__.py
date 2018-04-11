""" Models. """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"


__all__ = ["all_models", "models_map"]

from mrbaviirc.util.sort import depends_sort
from mrbaviirc.util.imp import import_submodules_symbolref

# Import all submodules and get the MODELS from each
all_models = import_submodules_symbolref(__package__, "MODELS", recursive=False)
models_map = { i.MODEL_NAME: i for i in all_models }

# Update the all_models tuple to be sorted
_depends = { i.MODEL_NAME : i.MODEL_DEPENDS for i in all_models }
_sorted = depends_sort(_depends)

all_models = tuple(models_map[i] for i in _sorted)

