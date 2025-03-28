# -*- coding: utf-8 -*-
"""
npxpy
Created on Thu Feb 29 11:49:17 2024

@author: Caghan Uenlueer
Neuromorphic Quantumphotonics
Heidelberg University
E-Mail:	caghan.uenlueer@kip.uni-heidelberg.de

This file is part of npxpy, which is licensed under the MIT License.
"""
from typing import List, Optional, Union, TypeVar
from npxpy.nodes.node import Node
from npxpy.resources import Mesh
from npxpy.preset import Preset
from npxpy.nodes.project import Project
from npxpy.nodes.space import _GatekeeperSpace

Struct = TypeVar(
    "Struct", bound="Structure"
)  # Define a type variable for the class


class Structure(_GatekeeperSpace):
    """
    A class representing a structure node.

    Attributes:
        preset (Preset): The preset associated with the structure.
        mesh (Mesh): The mesh object used for the structure.
        load_preset (bool): Flag to auto-load presets.
        load_mesh (bool): Flag to auto-load resources.
        size (List[Union[float, int]]): The size (scaling) of the structure.
        name (str): The name of the structure.
        slicing_origin (str): The origin for slicing.
        slicing_offset (Union[float, int]): The offset for slicing.
        priority (int): The priority of the structure.
        expose_individually (bool): Flag to expose the structure individually.
        position (List[Union[float, int]]): Position of the structure.
        rotation (List[Union[float, int]]): Rotation of the structure.
    """

    def __init__(
        self,
        preset: Preset,
        mesh: Mesh,
        size: List[Union[float, int]] = [100.0, 100.0, 100.0],
        name: str = "Structure",
        slicing_origin: str = "scene_bottom",
        slicing_offset: Union[float, int] = 0.0,
        priority: int = 0,
        expose_individually: bool = False,
        position: List[Union[float, int]] = [0, 0, 0],
        rotation: List[Union[float, int]] = [0.0, 0.0, 0.0],
        color="#16506B",
    ):
        """
        Initialize a Structure node.

        Parameters:
            preset (Optional[Preset]): The preset associated with the structure.
            mesh (Optional[Mesh]): The mesh object to be used for the structure.
            load_preset (bool): Flag to auto-load presets.
            load_mesh (bool): Flag to auto-load resources.
            size (List[Union[float, int]]): The size of the structure in micrometers [x, y, z].
            name (str): The name of the structure.
            slicing_origin (str): The origin for slicing. Must be one of
                                  'structure_center', 'zero', 'scene_top', 'scene_bottom',
                                  'structure_top', 'structure_bottom', 'scene_center'.
            slicing_offset (Union[float, int]): The offset for slicing.
            priority (int): The priority of the structure. Must be >= 0.
            expose_individually (bool): Flag to expose the structure individually.
            position (List[Union[float, int]]): The position of the structure [x, y, z].
            rotation (List[Union[float, int]]): The rotation of the structure [psi, theta, phi].
        """
        super().__init__(
            "structure",
            name,
        )

        # Setters for attributes with validation
        self.slicing_origin_reference = slicing_origin
        self.slicing_offset = slicing_offset
        self.priority = priority
        self.expose_individually = expose_individually
        self.preset = preset
        self.mesh = mesh
        self.project = None
        self.size = size
        self.position = position
        self.rotation = rotation
        self.color = color

        self._mesh = True

    @property
    def slicing_origin(self):
        """The origin for slicing."""
        return self._slicing_origin

    @slicing_origin.setter
    def slicing_origin(self, value: str):
        if not isinstance(value, str) or value not in [
            "zero",
            "structure_top",
            "scene_center",
            "structure_center",
            "scene_top",
            "structure_bottom",
            "scene_bottom",
        ]:
            valids = [
                "zero",
                "structure_top",
                "scene_center",
                "structure_center",
                "scene_top",
                "structure_bottom",
                "scene_bottom",
            ]
            raise TypeError(
                "slicing_origin must be a string. "
                f"Valid inputs are: {valids}"
            )
        # Add any specific value constraints here if needed (e.g., valid slicing origins)
        self._slicing_origin = value

    @property
    def slicing_offset(self):
        """The offset for slicing."""
        return self._slicing_offset

    @slicing_offset.setter
    def slicing_offset(self, value: Union[float, int]):
        if not isinstance(value, (float, int)):
            raise TypeError("slicing_offset must be a float or an int.")
        self._slicing_offset = value

    @property
    def priority(self):
        """The priority of the structure."""
        return self._priority

    @priority.setter
    def priority(self, value: int):
        if not isinstance(value, int):
            raise TypeError("priority must be an integer.")
        if value < 0:
            raise ValueError("priority must be greater than or equal to 0.")
        self._priority = value

    @property
    def expose_individually(self):
        """Flag to expose the structure individually."""
        return self._expose_individually

    @expose_individually.setter
    def expose_individually(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("expose_individually must be a boolean.")
        self._expose_individually = value

    # Setters with validation
    @property
    def preset(self):
        """The preset used for the structure."""
        return self._preset

    @preset.setter
    def preset(self, value: Optional[Preset]):
        if value is not None and not isinstance(value, Preset):
            raise TypeError("preset must be an instance of Preset or None.")
        self._preset = value

    @property
    def mesh(self):
        """The mesh used for the structure."""
        return self._mesh_obj

    @mesh.setter
    def mesh(self, value: Optional[Mesh]):
        if value is not None and not isinstance(value, Mesh):
            raise TypeError("mesh must be an instance of Mesh or None.")
        self._mesh_obj = value

    @property
    def project(self):
        """The project context associated with the structure."""
        return self._project

    @project.setter
    def project(self, value: Optional[Project]):
        if value is not None and not isinstance(value, Project):
            raise TypeError("project must be an instance of Project or None.")
        self._project = value

    @property
    def load_preset(self):
        """Flag to determine whether presets are auto-loaded."""
        return self._load_preset

    @load_preset.setter
    def load_preset(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("load_preset must be a boolean.")
        self._load_preset = value

    @property
    def load_mesh(self):
        """Flag to determine whether resources are auto-loaded."""
        return self._load_mesh

    @load_mesh.setter
    def load_mesh(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("load_mesh must be a boolean.")
        self._load_mesh = value

    @property
    def size(self):
        """The size (scaling) of the structure."""
        return self._size

    @size.setter
    def size(self, value: List[Union[float, int]]):
        if not all(isinstance(s, (float, int)) for s in value):
            raise TypeError("All size elements must be float or int.")
        self._size = value

    @property
    def color(self):
        """The color of the structure inside the viewport."""
        return self._color

    @color.setter
    def color(self, value: str):
        if not isinstance(value, str):
            raise TypeError(
                "color must be a string. A non-valid string will default to black."
            )
        self._color = value

    def position_at(
        self,
        position: List[Union[float, int]] = [0, 0, 0],
        rotation: List[Union[float, int]] = None,
    ):
        """
        Set the current position and rotation of the structure.

        Parameters:
            position (List[Union[float, int]]): Position values [x, y, z].
            rotation (List[Union[float, int]]): Rotation values [psi, theta, phi].

        Returns:
            self: The updated Structure object.
        """
        if rotation is not None:
            self.position = position
            self.rotation = rotation
        else:
            self.position = position
        return self

    def translate(self, translation: List[Union[float, int]]):
        """
        Translate the structure by the specified values.

        Parameters:
            translation (List[Union[float, int]]): Translation values [dx, dy, dz].
        """
        if len(translation) != 3 or not all(
            isinstance(t, (float, int)) for t in translation
        ):
            raise ValueError(
                "Translation must be a list of three numeric elements."
            )
        self.position = [p + t for p, t in zip(self.position, translation)]
        return self

    def rotate(self, rotation: List[Union[float, int]]):
        """
        Rotate the structure by the specified values.

        Parameters:
            rotation (List[Union[float, int]]): Rotation angles to apply [d_psi, d_theta, d_phi].
        """
        if len(rotation) != 3 or not all(
            isinstance(r, (float, int)) for r in rotation
        ):
            raise ValueError(
                "Rotation must be a list of three numeric elements."
            )
        self.rotation = [
            (r + delta) % 360 for r, delta in zip(self.rotation, rotation)
        ]
        return self

    def auto_load(
        self: Struct,
        project: Project,
        load_mesh: bool = True,
        load_preset: bool = True,
    ) -> Struct:
        """
        Load passed presets and meshes to passed project if the flags are set.
        """
        self.project = project
        self.load_mesh = load_mesh
        self.load_preset = load_preset

        if self.load_preset:
            self.project.load_presets(self.preset)

        if self.load_mesh:
            if self.mesh._type != "mesh_file":
                raise TypeError(
                    "Images are used only for MarkerAligner class."
                )
            self.project.load_resources(self.mesh)
        return self

    def to_dict(self) -> dict:
        """
        Convert the structure to a dictionary representation.

        Returns:
            dict: The dictionary representation of the structure.
        """
        if self._mesh:
            self.geometry = {
                "type": "mesh",
                "resource": self.mesh.id,
                "scale": [
                    self.size[0] / 100,
                    self.size[1] / 100,
                    self.size[2] / 100,
                ],
            }
        node_dict = super().to_dict()
        node_dict["preset"] = self.preset.id if self.preset else None
        node_dict["properties"] = {"color": self.color}
        node_dict["geometry"] = self.geometry
        node_dict["slicing_origin_reference"] = self.slicing_origin_reference
        node_dict["slicing_offset"] = self.slicing_offset
        node_dict["priority"] = self.priority
        node_dict["expose_individually"] = self.expose_individually

        return node_dict


class Text(Structure):
    """
    A class representing a text node.

    Attributes:
        text (str): The text content.
        font_size (Union[float, int]): The font size of the text.
        height (Union[float, int]): The height of the text.
    """

    def __init__(
        self,
        preset: Preset,
        name: str = "Text",
        text: str = "Text",
        font_size: Union[float, int] = 10.0,
        height: Union[float, int] = 5.0,
        slicing_origin: str = "scene_bottom",
        slicing_offset: Union[float, int] = 0.0,
        priority: int = 0,
        expose_individually: bool = False,
        position: List[Union[float, int]] = [0, 0, 0],
        rotation: List[Union[float, int]] = [0.0, 0.0, 0.0],
        color="lightblue",
    ):
        """
        Initialize a Text node.

        Parameters:
            preset (Preset): The preset associated with the text.
            name (str): The name of the text.
            text (str): The text content.
            font_size (Union[float, int]): The font size of the text. Must be greater than 0.
            height (Union[float, int]): The height of the text. Must be greater than 0.
            slicing_origin (str): The origin for slicing. Must be one of
                                  'structure_center', 'zero', 'scene_top', 'scene_bottom',
                                  'structure_top', 'structure_bottom', 'scene_center'.
            slicing_offset (Union[float, int]): The offset for slicing.
            priority (int): The priority of the text. Must be >= 0.
            expose_individually (bool): Flag to expose the text individually.
            position (List[Union[float, int]]): The position of the text [x, y, z].
            rotation (List[Union[float, int]]): The rotation of the text [psi, theta, phi].
        """
        super().__init__(
            preset=preset,
            mesh=None,
            name=name,
            slicing_origin=slicing_origin,
            slicing_offset=slicing_offset,
            priority=priority,
            expose_individually=expose_individually,
            position=position,
            rotation=rotation,
            color=color,
        )

        # Setters for validation
        self.text = text
        self.font_size = font_size
        self.height = height

        self.load_mesh = False
        self.load_preset = True

        #  This guy sits in Structure. Ensures no mesh is passed.
        self._mesh = False

    @property
    def text(self):
        """The text content of the node."""
        return self._text

    @text.setter
    def text(self, value: str):
        if not isinstance(value, str):
            raise TypeError("text must be a string.")
        self._text = value

    @property
    def font_size(self):
        """The font size of the text."""
        return self._font_size

    @font_size.setter
    def font_size(self, value: Union[float, int]):
        if not isinstance(value, (float, int)) or value <= 0:
            raise ValueError("font_size must be a positive number.")
        self._font_size = value

    @property
    def height(self):
        """The height of the text."""
        return self._height

    @height.setter
    def height(self, value: Union[float, int]):
        if not isinstance(value, (float, int)) or value <= 0:
            raise ValueError("height must be a positive number.")
        self._height = value

    def auto_load(
        self,
        project: Project,
    ):
        """
        Load passed presets to passed project if the flags are set.
        """
        self.project = project

        if self.load_preset:
            self.project.load_presets(self.preset)

        if self.load_mesh:
            if self.mesh._type != "mesh_file":
                raise TypeError(
                    "Images are used only for MarkerAligner class."
                )
            self.project.load_resources(self.mesh)
        return self

    def to_dict(self) -> dict:
        """
        Convert the text to a dictionary representation.

        Returns:
            dict: The dictionary representation of the text.
        """
        self.geometry = {
            "type": "text",
            "text": self.text,
            "font_size": self.font_size,
            "height": self.height,
        }
        node_dict = super().to_dict()
        node_dict["geometry"] = self.geometry
        return node_dict


class Lens(Structure):
    """
    A class representing a lens node with specific optical properties.

    Attributes:
        radius (Union[float, int]): The radius of the lens.
        height (Union[float, int]): The height of the lens.
        crop_base (bool): Flag indicating whether the base of the lens should be cropped.
        asymmetric (bool): Flag indicating whether the lens is asymmetric.
        curvature (Union[float, int]): The curvature of the lens.
        conic_constant (Union[float, int]): The conic constant of the lens.
        curvature_y (Union[float, int]): The curvature of the lens in the Y direction (for asymmetric lenses).
        conic_constant_y (Union[float, int]): The conic constant in the Y direction.
        nr_radial_segments (int): The number of radial segments.
        nr_phi_segments (int): The number of phi segments.
    """

    def __init__(
        self,
        preset: Preset,
        name: str = "Lens",
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
        slicing_origin: str = "scene_bottom",
        slicing_offset: Union[float, int] = 0.0,
        priority: int = 0,
        expose_individually: bool = False,
        position: List[Union[float, int]] = [0.0, 0.0, 0.0],
        rotation: List[Union[float, int]] = [0.0, 0.0, 0.0],
        color="lightblue",
    ):
        """
        Initialize a Lens node with optical properties.

        Parameters:
            preset (Preset): The preset associated with the lens.
            name (str): The name of the lens.
            radius (Union[float, int]): The radius of the lens. Must be > 0.
            height (Union[float, int]): The height of the lens. Must be > 0.
            crop_base (bool): Whether to crop the base of the lens.
            asymmetric (bool): Whether the lens is asymmetric.
            curvature (Union[float, int]): The curvature of the lens.
            conic_constant (Union[float, int]): The conic constant of the lens.
            curvature_y (Union[float, int]): The curvature in the Y direction (if asymmetric).
            conic_constant_y (Union[float, int]): The conic constant in the Y direction.
            nr_radial_segments (int): The number of radial segments.
            nr_phi_segments (int): The number of phi segments.
            slicing_origin (str): The slicing origin.
            slicing_offset (Union[float, int]): The slicing offset.
            priority (int): The priority of the lens.
            expose_individually (bool): Whether to expose the lens individually.
            position (List[Union[float, int]]): The position of the lens [x, y, z].
            rotation (List[Union[float, int]]): The rotation of the lens [psi, theta, phi].
        """
        super().__init__(
            preset=preset,
            mesh=None,
            name=name,
            slicing_origin=slicing_origin,
            slicing_offset=slicing_offset,
            priority=priority,
            expose_individually=expose_individually,
            rotation=rotation,
            position=position,
            color=color,
        )

        # Setters for validation
        self.radius = radius
        self.height = height
        self.crop_base = crop_base
        self.asymmetric = asymmetric
        self.curvature = curvature
        self.conic_constant = conic_constant
        self.curvature_y = curvature_y
        self.conic_constant_y = conic_constant_y
        self.nr_radial_segments = nr_radial_segments
        self.nr_phi_segments = nr_phi_segments

        self.polynomial_type = "Normalized"
        self.polynomial_factors = []
        self.polynomial_factors_y = []

        self.surface_compensation_factors = []
        self.surface_compensation_factors_y = []

        self.load_mesh = False
        self.load_preset = True

        #  This guy sits in Structure. Ensures no mesh is passed.
        self._mesh = False

    # Setters with validation for Lens-specific attributes
    @property
    def radius(self):
        """The radius of the lens."""
        return self._radius

    @radius.setter
    def radius(self, value: Union[float, int]):
        if not isinstance(value, (float, int)) or value <= 0:
            raise ValueError("radius must be a positive number.")
        self._radius = value

    @property
    def height(self):
        """The height of the lens."""
        return self._height

    @height.setter
    def height(self, value: Union[float, int]):
        if not isinstance(value, (float, int)) or value <= 0:
            raise ValueError("height must be a positive number.")
        self._height = value

    @property
    def crop_base(self):
        """Whether the lens base should be cropped."""
        return self._crop_base

    @crop_base.setter
    def crop_base(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("crop_base must be a boolean.")
        self._crop_base = value

    @property
    def asymmetric(self):
        """Whether the lens is asymmetric."""
        return self._asymmetric

    @asymmetric.setter
    def asymmetric(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("asymmetric must be a boolean.")
        self._asymmetric = value

    @property
    def curvature(self):
        """The curvature of the lens."""
        return self._curvature

    @curvature.setter
    def curvature(self, value: Union[float, int]):
        if not isinstance(value, (float, int)):
            raise TypeError("curvature must be a float or an int.")
        self._curvature = value

    @property
    def conic_constant(self):
        """The conic constant of the lens."""
        return self._conic_constant

    @conic_constant.setter
    def conic_constant(self, value: Union[float, int]):
        if not isinstance(value, (float, int)):
            raise TypeError("conic_constant must be a float or an int.")
        self._conic_constant = value

    @property
    def curvature_y(self):
        """The curvature of the lens in the Y direction."""
        return self._curvature_y

    @curvature_y.setter
    def curvature_y(self, value: Union[float, int]):
        if not isinstance(value, (float, int)):
            raise TypeError("curvature_y must be a float or an int.")
        self._curvature_y = value

    @property
    def conic_constant_y(self):
        """The conic constant in the Y direction."""
        return self._conic_constant_y

    @conic_constant_y.setter
    def conic_constant_y(self, value: Union[float, int]):
        if not isinstance(value, (float, int)):
            raise TypeError("conic_constant_y must be a float or an int.")
        self._conic_constant_y = value

    @property
    def nr_radial_segments(self):
        """The number of radial segments for the lens."""
        return self._nr_radial_segments

    @nr_radial_segments.setter
    def nr_radial_segments(self, value: int):
        if not isinstance(value, int):
            raise TypeError("nr_radial_segments must be an int.")
        self._nr_radial_segments = value

    @property
    def nr_phi_segments(self):
        """The number of phi segments for the lens."""
        return self._nr_phi_segments

    @nr_phi_segments.setter
    def nr_phi_segments(self, value: int):
        if not isinstance(value, int):
            raise TypeError("nr_phi_segments must be an int.")
        self._nr_phi_segments = value

    @property
    def polynomial_type(self):
        """The type of polynomial ('Normalized' or 'Standard')."""
        return self._polynomial_type

    @polynomial_type.setter
    def polynomial_type(self, value: str):
        if value not in ["Normalized", "Standard"]:
            raise ValueError(
                "polynomial_type must be either 'Normalized' or 'Standard'."
            )
        self._polynomial_type = value

    @property
    def polynomial_factors(self):
        """List of polynomial factors."""
        return self._polynomial_factors

    @polynomial_factors.setter
    def polynomial_factors(self, value: List[Union[float, int]]):
        if not all(isinstance(f, (float, int)) for f in value):
            raise TypeError(
                "All polynomial_factors elements must be float or int."
            )
        self._polynomial_factors = value

    @property
    def polynomial_factors_y(self):
        """Polynomial factors for Y axis (if asymmetric)."""
        return self._polynomial_factors_y

    @polynomial_factors_y.setter
    def polynomial_factors_y(self, value: List[Union[float, int]]):
        if not all(isinstance(f, (float, int)) for f in value):
            raise TypeError(
                "All polynomial_factors_y elements must be float or int."
            )
        self._polynomial_factors_y = value

    # Setters for surface_compensation_factors and surface_compensation_factors_y

    @property
    def surface_compensation_factors(self):
        """List of surface compensation factors."""
        return self._surface_compensation_factors

    @surface_compensation_factors.setter
    def surface_compensation_factors(self, value: List[Union[float, int]]):
        if not all(isinstance(f, (float, int)) for f in value):
            raise TypeError(
                "All surface_compensation_factors elements must be float or int."
            )
        self._surface_compensation_factors = value

    @property
    def surface_compensation_factors_y(self):
        """Surface compensation factors for Y axis (if asymmetric)."""
        return self._surface_compensation_factors_y

    @surface_compensation_factors_y.setter
    def surface_compensation_factors_y(self, value: List[Union[float, int]]):
        if not all(isinstance(f, (float, int)) for f in value):
            raise TypeError(
                "All surface_compensation_factors_y elements must be float or int."
            )
        self._surface_compensation_factors_y = value

    def polynomial(
        self,
        polynomial_type: str = "Normalized",
        polynomial_factors: List[Union[float, int]] = [0, 0, 0],
        polynomial_factors_y: List[Union[float, int]] = [0, 0, 0],
    ):
        """
        Set the polynomial factors for the lens.

        Parameters:
            polynomial_type (str): The type of polynomial.
            polynomial_factors (List[Union[float, int]]):
                List of polynomial factors.
            polynomial_factors_y (List[Union[float, int]]):
                Polynomial factors for Y axis (if asymmetric).

        Returns:
            self: The updated Lens object.
        """
        self.polynomial_type = polynomial_type  # Use setter for validation
        self.polynomial_factors = (
            polynomial_factors  # Use setter for validation
        )
        if self.asymmetric:
            self.polynomial_factors_y = (
                polynomial_factors_y  # Use setter for validation
            )
        return self

    def surface_compensation(
        self,
        surface_compensation_factors: List[Union[float, int]] = [0, 0, 0],
        surface_compensation_factors_y: List[Union[float, int]] = [0, 0, 0],
    ):
        """
        Set the surface compensation factors for the lens.

        Parameters:
            surface_compensation_factors (List[Union[float, int]]):
                Surface compensation factors.
            surface_compensation_factors_y (List[Union[float, int]]):
                Surface compensation factors for Y axis (if asymmetric).

        Returns:
            self: The updated Lens object.
        """
        self.surface_compensation_factors = (
            surface_compensation_factors  # Use setter for validation
        )
        if self.asymmetric:
            self.surface_compensation_factors_y = (
                surface_compensation_factors_y  # Use setter for validation
            )
        return self

    def auto_load(
        self,
        project: Project,
    ):
        """
        Load passed presets to passed project if the flags are set.
        """
        self.project = project

        if self.load_preset:
            self.project.load_presets(self.preset)

        if self.load_mesh:
            if self.mesh._type != "mesh_file":
                raise TypeError(
                    "Images are used only for MarkerAligner class."
                )
            self.project.load_resources(self.mesh)
        return self

    def to_dict(self) -> dict:
        """
        Convert the lens to a dictionary representation.

        Returns:
            dict: The dictionary representation of the lens.
        """
        self.geometry = {
            "type": "lens",
            "radius": self.radius,
            "height": self.height,
            "crop_base": self.crop_base,
            "asymmetric": self.asymmetric,
            "curvature": self.curvature,
            "conic_constant": self.conic_constant,
            "curvature_y": self.curvature_y,
            "conic_constant_y": self.conic_constant_y,
            "polynomial_type": self.polynomial_type,
            "polynomial_factors": self.polynomial_factors,
            "polynomial_factors_y": self.polynomial_factors_y,
            "surface_compensation_factors": self.surface_compensation_factors,
            "surface_compensation_factors_y": self.surface_compensation_factors_y,
            "nr_radial_segments": self.nr_radial_segments,
            "nr_phi_segments": self.nr_phi_segments,
        }

        node_dict = super().to_dict()
        node_dict["geometry"] = self.geometry
        return node_dict
