# npxpy/__init__.py
import sys
import warnings

# Importing from npxpy module files
from .preset import Preset
from .resources import Image, Mesh

# Importing from npxpy/nodes submodule
from .nodes.project import Project
from .nodes.space import Scene, Group, Array
from .nodes.structures import Structure, Text, Lens
from .nodes.aligners import (
    CoarseAligner,
    InterfaceAligner,
    FiberAligner,
    MarkerAligner,
    EdgeAligner,
)
from .nodes.misc import DoseCompensation, Capture, StageMove, Wait
from ._version import __version__

# Define what should be available when importing npxpy (this is the core)
__all__ = [
    "Preset",
    "Image",
    "Mesh",
    "Project",
    "Scene",
    "Group",
    "Array",
    "Structure",
    "Text",
    "Lens",
    "CoarseAligner",
    "InterfaceAligner",
    "FiberAligner",
    "MarkerAligner",
    "EdgeAligner",
    "DoseCompensation",
    "Capture",
    "StageMove",
    "Wait",
]

# Metadata
__author__ = "Caghan Uenlueer"
__license__ = "MIT"
__email__ = "caghan.uenlueer@kip.uni-heidelberg.de"

# Python version check
if sys.version_info < (3, 7, 0):
    warnings.warn(
        "The installed Python version is outdated. Please upgrade to"
        " Python 3.7 or newer for continued npxpy updates.",
        Warning,
    )
