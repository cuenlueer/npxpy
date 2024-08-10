# -*- coding: utf-8 -*-
"""
npxpy
Created on Thu Feb 29 11:49:17 2024

@author: Caghan Uenlueer
Neuromorphic Quantumphotonics
Heidelberg University
E-Mail:	caghan.uenlueer@kip.uni-heidelberg.de

This file is part of npxpy (formerly nanoAPI), which is licensed under the GNU Lesser General Public License v3.0.
You can find a copy of this license at https://www.gnu.org/licenses/lgpl-3.0.html
"""
from typing import List, Optional, Union
from npxpy.nodes.node import Node
from npxpy.resources import Mesh
from npxpy.preset import Preset
from npxpy.nodes.project import Project

class Structure(Node):
    def __init__(self, 
                 preset: Optional[Preset] = None,  # only objects from class Preset are allowed!
                 mesh: Optional[Mesh] = None,  # only objects from class Mesh are allowed!
                 project: Optional[Project] = None,
                 auto_load_presets: bool = False,
                 auto_load_resources: bool = False,
                 size: List[Union[float, int]] = [100.0, 100.0, 100.0],  # okay if int
                 name: str = 'Structure',
                 slicing_origin: str = 'scene_bottom',
                 slicing_offset: Union[float, int] = 0.0,  # okay if int
                 priority: int = 0,
                 expose_individually: bool = False):
        """
        Initialize a Structure node.

        Parameters:
        preset (Preset): The preset associated with the structure.
        mesh (Mesh): The mesh object to be used for the structure.
        project (Optional[Project]): The project context, if any, necessary for auto-loading resources.
        auto_load_presets (bool): Flag to auto-load presets.
        auto_load_resources (bool): Flag to auto-load resources.
        size (List[Union[float, int]]): The size (scaling) of the structure in micrometers [x, y, z].
        name (str): The name of the structure.
        slicing_origin (str): The origin for slicing. Must be one of 'structure_center', 'zero', 
                              'scene_top', 'scene_bottom', 'structure_top', 'structure_bottom', 'scene_center'.
        slicing_offset (Union[float, int]): The offset for slicing.
        priority (int): The priority of the structure. Must be >= 0.
        expose_individually (bool): Flag to expose the structure individually.
        """
        if mesh is not None and not isinstance(preset, Preset):
            raise TypeError("preset must be an instance of Preset or None.")
        if mesh is not None and not isinstance(mesh, Mesh):
            raise TypeError("mesh must be an instance of Mesh or None.")
        if project is not None and not isinstance(project, Project):
            raise TypeError("project must be an instance of Project or None.")
        if not isinstance(auto_load_presets, bool):
            raise TypeError("auto_load_presets must be a boolean.")
        if not isinstance(auto_load_resources, bool):
            raise TypeError("auto_load_resources must be a boolean.")
        if not all(isinstance(s, (float, int)) for s in size):
            raise TypeError("All size elements must be float or int.")
        if not isinstance(name, str):
            raise TypeError("name must be a string.")
        if not isinstance(slicing_origin, str):
            raise TypeError("slicing_origin must be a string.")
        if not isinstance(slicing_offset, (float, int)):
            raise TypeError("slicing_offset must be a float or an int.")
        if not isinstance(priority, int):
            raise TypeError("priority must be an integer.")
        if priority < 0:
            raise ValueError("priority must be greater than or equal to 0.")
        if not isinstance(expose_individually, bool):
            raise TypeError("expose_individually must be a boolean.")

        valid_slicing_origins = {'structure_center', 'zero', 'scene_top', 
                                 'scene_bottom', 'structure_top', 
                                 'structure_bottom', 'scene_center'}
        if slicing_origin not in valid_slicing_origins:
            raise ValueError(f"slicing_origin must be one of {valid_slicing_origins}")

        super().__init__('structure', 
                         name, 
                         slicing_origin_reference=slicing_origin,
                         slicing_offset=slicing_offset, 
                         priority=priority,
                         expose_individually=expose_individually)
        self.mesh = mesh
        self.size = size
        self.preset = preset
        self.project = project
        self.auto_load_presets = auto_load_presets
        self.auto_load_resources = auto_load_resources
        
        self._mesh = True

        if (auto_load_presets or auto_load_resources) and project:
            self._load_resources()

    def _load_resources(self) -> None:
        """Load presets and resources if the respective flags are set."""
        if self.auto_load_presets:
            self.project.load_presets(self.preset)
            
        if self.auto_load_resources:
            if self.mesh._type != 'mesh_file':
                raise TypeError("Images are supposed to be used for MarkerAligner() class only.")
            self.project.load_resources(self.mesh)

    def position_at(self, position: List[Union[float, int]] = [0, 0, 0], rotation: List[Union[float, int]] = [0.0, 0.0, 0.0]):
        """
        Set the current position and rotation of the structure.

        Parameters:
            position (List[Union[float, int]]): List of position values [x, y, z].
            rotation (List[Union[float, int]]): List of rotation angles [psi, theta, phi].

        Returns:
            self: The instance of the Structure class.

        Raises:
            ValueError: If position or rotation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(position) != 3:
            raise ValueError("position must be a list of three elements.")
        if not all(isinstance(p, (float, int)) for p in position):
            raise ValueError("All position elements must be numbers.")
        
        if len(rotation) != 3:
            raise ValueError("rotation must be a list of three elements.")
        if not all(isinstance(r, (float, int)) for r in rotation):
            raise ValueError("All rotation elements must be numbers.")
        
        self.position = position
        self.rotation = rotation
        return self

    def translate(self, translation: List[Union[float, int]]):
        """
        Translate the current position by the specified translation.

        Parameters:
            translation (List[Union[float, int]]): List of translation values [dx, dy, dz].

        Raises:
            ValueError: If translation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(translation) != 3:
            raise ValueError("translation must be a list of three elements.")
        if not all(isinstance(t, (float, int)) for t in translation):
            raise ValueError("All translation elements must be numbers.")
        
        self.position = [pos + trans for pos, trans in zip(self.position, translation)]

    def rotate(self, rotation: List[Union[float, int]]):
        """
        Rotate the structure by the specified rotation angles.

        Parameters:
            rotation (List[Union[float, int]]): List of rotation angles to apply [d_psi, d_theta, d_phi].

        Raises:
            ValueError: If rotation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(rotation) != 3:
            raise ValueError("rotation must be a list of three elements.")
        if not all(isinstance(r, (float, int)) for r in rotation):
            raise ValueError("All rotation elements must be numbers.")
        
        self.rotation = [(angle + rot) % 360 for angle, rot in zip(self.rotation, rotation)]

    def to_dict(self) -> dict:
        """
        Convert the structure to a dictionary representation.

        Returns:
        dict: The dictionary representation of the structure.
        """
        if self._mesh:
            self.geometry = {
                'type': 'mesh',
                'resource': self.mesh.id,
                'scale': [self.size[0] / 100, self.size[1] / 100, self.size[2] / 100]
            }
        node_dict = super().to_dict()
        node_dict['preset'] = self.preset.id
        node_dict['geometry'] = self.geometry
        return node_dict

class Text(Structure):
    def __init__(self, preset: Preset,
                 name: str = 'Text',
                 text: str = 'Text',
                 font_size: Union[float, int] = 10.0,
                 height: Union[float, int] = 5.0,
                 slicing_origin: str = 'scene_bottom',
                 slicing_offset: Union[float, int] = 0.0,
                 priority: int = 0,
                 expose_individually: bool = False):
        """
        Initialize a Text node.

        Parameters:
        preset (Preset): The preset associated with the text.
        name (str): The name of the text.
        text (str): The text content.
        font_size (Union[float, int]): The font size of the text. Must be greater than 0.
        height (Union[float, int]): The height of the text. Must be greater than 0.
        slicing_origin (str): The origin for slicing. Must be one of 'structure_center', 'zero', 
                              'scene_top', 'scene_bottom', 'structure_top', 'structure_bottom', 'scene_center'.
        slicing_offset (Union[float, int]): The offset for slicing.
        priority (int): The priority of the text. Must be >= 0.
        expose_individually (bool): Flag to expose the text individually.
        """
        if not isinstance(text, str):
            raise TypeError("text must be a string.")
        if not isinstance(font_size, (float, int)) or font_size <= 0:
            raise ValueError("font_size must be a positive number.")
        if not isinstance(height, (float, int)) or height <= 0:
            raise ValueError("height must be a positive number.")
        
        super().__init__(preset=preset, mesh=None, name=name,
                         slicing_origin=slicing_origin,
                         slicing_offset=slicing_offset,
                         priority=priority,
                         expose_individually=expose_individually)
        self.text = text
        self.font_size = font_size
        self.height = height
        
        self._mesh = False

    def to_dict(self) -> dict:
        """
        Convert the text to a dictionary representation.

        Returns:
        dict: The dictionary representation of the text.
        """
        self.geometry = {'type': 'text',
                         'text': self.text,
                         'font_size': self.font_size,
                         'height': self.height}
        node_dict = super().to_dict()
        node_dict['geometry'] = self.geometry
        return node_dict


class Lens(Structure):
    def __init__(self, preset: Preset,
                 name: str = 'Lens',
                 radius: Union[float, int] = 100.0,
                 height: Union[float, int] = 50.0,
                 crop_base: bool = False,
                 asymmetric: bool = False,
                 curvature: Union[float, int] = 0.01,
                 conic_constant: Union[float, int] = 0.01,
                 curvature_y: Union[float, int] = 0.01,
                 conic_constant_y: Union[float, int] = -1.0,
                 nr_radial_segments: int = 500,
                 nr_phi_segments: int = 360,
                 slicing_origin: str = 'scene_bottom',
                 slicing_offset: Union[float, int] = 0.0,
                 priority: int = 0,
                 expose_individually: bool = False):
        """
        Initialize a Lens node.

        Parameters:
        preset (Preset): The preset associated with the lens.
        name (str): The name of the lens.
        radius (Union[float, int]): The radius of the lens. Must be greater than 0.
        height (Union[float, int]): The height of the lens. Must be greater than 0.
        crop_base (bool): Flag to indicate if the base should be cropped.
        asymmetric (bool): Flag to indicate if the lens is asymmetric.
        curvature (Union[float, int]): The curvature of the lens.
        conic_constant (Union[float, int]): The conic constant of the lens.
        curvature_y (Union[float, int]): The curvature of the lens in the y direction.
        conic_constant_y (Union[float, int]): The conic constant of the lens in the y direction.
        nr_radial_segments (int): The number of radial segments.
        nr_phi_segments (int): The number of phi segments.
        slicing_origin (str): The origin for slicing. Must be one of 'structure_center', 'zero', 
                              'scene_top', 'scene_bottom', 'structure_top', 'structure_bottom', 'scene_center'.
        slicing_offset (Union[float, int]): The offset for slicing.
        priority (int): The priority of the lens. Must be >= 0.
        expose_individually (bool): Flag to expose the lens individually.
        """
        if not isinstance(radius, (float, int)) or radius <= 0:
            raise ValueError("radius must be a positive number.")
        if not isinstance(height, (float, int)) or height <= 0:
            raise ValueError("height must be a positive number.")
        if not isinstance(crop_base, bool):
            raise TypeError("crop_base must be a boolean.")
        if not isinstance(asymmetric, bool):
            raise TypeError("asymmetric must be a boolean.")
        if not isinstance(curvature, (float, int)):
            raise TypeError("curvature must be a float or an int.")
        if not isinstance(conic_constant, (float, int)):
            raise TypeError("conic_constant must be a float or an int.")
        if not isinstance(curvature_y, (float, int)):
            raise TypeError("curvature_y must be a float or an int.")
        if not isinstance(conic_constant_y, (float, int)):
            raise TypeError("conic_constant_y must be a float or an int.")
        if not isinstance(nr_radial_segments, int):
            raise TypeError("nr_radial_segments must be an int.")
        if not isinstance(nr_phi_segments, int):
            raise TypeError("nr_phi_segments must be an int.")
        
        super().__init__(preset=preset, mesh=None, name=name,
                         slicing_origin=slicing_origin,
                         slicing_offset=slicing_offset,
                         priority=priority,
                         expose_individually=expose_individually)
        
        self.radius = radius
        self.height = height
        self.crop_base = crop_base
        self.asymmetric = asymmetric
        self.curvature = curvature
        self.conic_constant = conic_constant
        self.curvature_y = curvature_y
        self.conic_constant_y = conic_constant_y
        
        self.polynomial_type = 'Normalized'
        self.polynomial_factors = []
        self.polynomial_factors_y = []
        
        self.surface_compensation_factors = []
        self.surface_compensation_factors_y = []
        
        self.nr_radial_segments = nr_radial_segments
        self.nr_phi_segments = nr_phi_segments
        
        self._mesh = False

    def polynomial(self, polynomial_type: str = 'Normalized',
                   polynomial_factors: List[Union[float, int]] = [0, 0, 0],
                   polynomial_factors_y: List[Union[float, int]] = [0, 0, 0]):
        """
        Set the polynomial factors for the lens.

        Parameters:
        polynomial_type (str): The type of polynomial, either 'Normalized' or 'Standard'.
        polynomial_factors (List[Union[float, int]]): List of polynomial factors.
        polynomial_factors_y (List[Union[float, int]]): List of polynomial factors for y-axis, if asymmetric.

        Returns:
        self: The instance of the Lens class.
        """
        if not isinstance(polynomial_type, str):
            raise TypeError("polynomial_type must be a string.")
        if not all(isinstance(f, (float, int)) for f in polynomial_factors):
            raise TypeError("All polynomial_factors elements must be float or int.")
        if not all(isinstance(f, (float, int)) for f in polynomial_factors_y):
            raise TypeError("All polynomial_factors_y elements must be float or int.")
        
        self.polynomial_type = polynomial_type
        self.polynomial_factors = polynomial_factors
        if self.asymmetric:
            self.polynomial_factors_y = polynomial_factors_y
        return self

    def surface_compensation(self, surface_compensation_factors: List[Union[float, int]] = [0, 0, 0],
                             surface_compensation_factors_y: List[Union[float, int]] = [0, 0, 0]):
        """
        Set the surface compensation factors for the lens.

        Parameters:
        surface_compensation_factors (List[Union[float, int]]): List of surface compensation factors.
        surface_compensation_factors_y (List[Union[float, int]]): List of surface compensation factors for y-axis, if asymmetric.

        Returns:
        self: The instance of the Lens class.
        """
        if not all(isinstance(f, (float, int)) for f in surface_compensation_factors):
            raise TypeError("All surface_compensation_factors elements must be float or int.")
        if not all(isinstance(f, (float, int)) for f in surface_compensation_factors_y):
            raise TypeError("All surface_compensation_factors_y elements must be float or int.")
        
        self.surface_compensation_factors = surface_compensation_factors
        if self.asymmetric:
            self.surface_compensation_factors_y = surface_compensation_factors_y
        return self

    def to_dict(self) -> dict:
        """
        Convert the lens to a dictionary representation.

        Returns:
        dict: The dictionary representation of the lens.
        """
        self.geometry = {
            'type': 'lens',
            'radius': self.radius,
            'height': self.height,
            'crop_base': self.crop_base,
            'asymmetric': self.asymmetric,
            'curvature': self.curvature,
            'conic_constant': self.conic_constant,
            'curvature_y': self.curvature_y,
            'conic_constant_y': self.conic_constant_y,
            'polynomial_type': self.polynomial_type,
            'polynomial_factors': self.polynomial_factors,
            'polynomial_factors_y': self.polynomial_factors_y,
            'surface_compensation_factors': self.surface_compensation_factors,
            'surface_compensation_factors_y': self.surface_compensation_factors_y,
            'nr_radial_segments': self.nr_radial_segments,
            'nr_phi_segments': self.nr_phi_segments
        }

        node_dict = super().to_dict()
        node_dict['geometry'] = self.geometry
        return node_dict