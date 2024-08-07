# npxpy/__init__.py

import sys

# Importing from npxpy module files
from .preset import Preset
from .resources import Image, Mesh

# Importing from npxpy/nodes submodule
from .nodes.project import Project
from .nodes.space import Scene, Group, Array
from .nodes.structures import Structure, Text, Lens
from .nodes.aligners import (
    CoarseAligner, InterfaceAligner, FiberAligner, MarkerAligner, EdgeAligner
)
from .nodes.misc import DoseCompensation, Capture, StageMove, Wait

# Define what should be available when importing npxpy
__all__ = [
    'Preset', 'Image', 'Mesh',
    'Project', 'Scene', 'Group', 'Array',
    'Structure', 'Text', 'Lens',
    'CoarseAligner', 'InterfaceAligner', 'FiberAligner', 'MarkerAligner', 'EdgeAligner',
    'DoseCompensation', 'Capture', 'StageMove', 'Wait'
]

# Version info
__version__ = '0.1.0'
version_info = (0, 1, 0)

# Metadata
__author__ = 'Caghan Uenlueer'
__license__ = 'LGPLv3'
__email__ = 'caghan.uenlueer@kip.uni-heidelberg.com'

# Python version check
if sys.version_info < (3, 5, 0):
    warnings.warn(
        'The installed Python version reached its end-of-life. Please upgrade to a newer Python version for receiving '
        'further npxpy updates.', Warning
    )