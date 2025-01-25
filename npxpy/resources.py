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
import uuid
import os
import hashlib
from typing import Dict, Any, List
from stl import mesh as stl_mesh


class Resource:
    """
    A class to represent a generic resource.

    Attributes:
        id (str): Unique identifier for the resource.
        name (str): Name of the resource.
        safe_path (str): Path where the resource is stored, based on file hash.
        file_path (str): Original path from where the resource was loaded.
    """

    def __init__(self, resource_type: str, name: str, file_path: str):
        """
        Initialize the resource with the specified parameters.

        Parameters:
            resource_type (str): Type of the resource.
            name (str): Name of the resource.
            file_path (str): Path where the resource is loaded from.
        """
        if not name or not name.strip():
            raise ValueError(
                "Resource: The 'name' parameter must not be an empty string."
            )

        self.id = str(uuid.uuid4())
        self._type = resource_type
        self.name = name
        self.file_path = file_path
        self.safe_path = self.generate_safe_path(file_path)

    @property
    def name(self):
        """Return the name of the resource."""
        return self._name

    @name.setter
    def name(self, value: str):
        """Set the name of the resource with validation to ensure it is a non-empty string."""
        value = str(value)
        if not isinstance(value, str) or not value.strip():
            raise ValueError("name must be a non-empty string.")
        self._name = value

    def generate_safe_path(self, file_path: str) -> str:
        """
        Generate a 'safe' path for the resource based on the MD5 hash of the file content.

        Parameters:
            file_path (str): Path to the file.

        Returns:
            str: Generated safe path for the resource.

        Raises:
            FileNotFoundError: If the file at file_path does not exist.
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        md5_hash = hashlib.md5()
        with open(file_path, "rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                md5_hash.update(chunk)

        file_hash = md5_hash.hexdigest()
        target_path = f"resources/{file_hash}/{os.path.basename(file_path)}"
        return target_path

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            dict: Dictionary representation of the current state of the object.
        """
        return {
            "id": self.id,
            "name": self.name,
            "type": self._type,
            "path": self.safe_path,
        }


class Image(Resource):
    """
    A class to represent an image resource.
    """

    def __init__(self, file_path: str, name: str = "image"):
        """
        Initialize the image resource with the specified parameters.

        Parameters:
            file_path (str): Path where the image is stored.
            name (str, optional): Name of the image resource. Defaults to 'image'.
        """
        # Ensure the file_path is valid
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")

        super().__init__(
            resource_type="image_file", name=name, file_path=file_path
        )


class Mesh(Resource):
    """
    A class to represent a mesh resource with attributes such as translation, rotation, scale, etc.

    Attributes:
        translation (List[float]): Translation values [x, y, z].
        rotation (List[float]): Rotation values [psi, theta, phi].
        scale (List[float]): Scale values [x, y, z].
        enhance_mesh (bool): Whether to enhance the mesh.
        simplify_mesh (bool): Whether to simplify the mesh.
        target_ratio (float): Target ratio for mesh simplification.
    """

    def __init__(
        self,
        file_path: str,
        name: str = "mesh",
        translation: List[float] = [0, 0, 0],
        auto_center: bool = False,
        rotation: List[float] = [0.0, 0.0, 0.0],
        scale: List[float] = [1.0, 1.0, 1.0],
        enhance_mesh: bool = True,
        simplify_mesh: bool = False,
        target_ratio: float = 100.0,
    ):
        """
        Initialize the mesh resource with the specified parameters.

        Parameters:
            file_path (str): Path where the mesh is stored (original file location).
            name (str, optional): Name of the mesh resource. Defaults to 'mesh'.
            translation (List[float], optional): Translation values [x, y, z]. Defaults to [0, 0, 0].
            auto_center (bool, optional): Whether to auto-center the mesh. Defaults to False.
            rotation (List[float], optional): Rotation values [psi, theta, phi]. Defaults to [0.0, 0.0, 0.0].
            scale (List[float], optional): Scale values [x, y, z]. Defaults to [1.0, 1.0, 1.0].
            enhance_mesh (bool, optional): Whether to enhance the mesh. Defaults to True.
            simplify_mesh (bool, optional): Whether to simplify the mesh. Defaults to False.
            target_ratio (float, optional): Target ratio for mesh simplification. Defaults to 100.0.
        """
        super().__init__(
            resource_type="mesh_file", name=name, file_path=file_path
        )

        # Set attributes with validation
        self.translation = translation
        self.auto_center = auto_center
        self.rotation = rotation
        self.scale = scale
        self.enhance_mesh = enhance_mesh
        self.simplify_mesh = simplify_mesh
        self.target_ratio = target_ratio
        self.original_triangle_count = self._get_triangle_count(file_path)

        # Load the mesh data
        self.mesh_data = stl_mesh.Mesh.from_file(file_path)

        # Apply auto-centering if enabled
        if self.auto_center:
            self._auto_center()

    @property
    def translation(self):
        return self._translation

    @translation.setter
    def translation(self, value: List[Any]):
        if len(value) != 3:
            raise ValueError(
                "Translation must have exactly 3 elements [x, y, z]"
            )
        try:
            self._translation = [float(v) for v in value]
        except ValueError:
            raise ValueError("Translation elements must be numeric values.")

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, value: List[Any]):
        if len(value) != 3:
            raise ValueError(
                "Rotation must have exactly 3 elements [psi, theta, phi]"
            )
        try:
            self._rotation = [float(v) for v in value]
        except ValueError:
            raise ValueError("Rotation elements must be numeric values.")

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value: List[Any]):
        if len(value) != 3:
            raise ValueError("Scale must have exactly 3 elements [x, y, z]")
        try:
            self._scale = [float(v) for v in value]
        except ValueError:
            raise ValueError("Scale elements must be numeric values.")

    @property
    def target_ratio(self):
        return self._target_ratio

    @target_ratio.setter
    def target_ratio(self, value: Any):
        try:
            value = float(value)
        except ValueError:
            raise ValueError("Target ratio must be a numeric value.")
        if not (0 <= value <= 100):
            raise ValueError("Target ratio must be between 0 and 100")
        self._target_ratio = value

    def _auto_center(self):
        """
        Auto-center the mesh by translating it so the bounding box center aligns with the origin
        in the x and y axes, and the lowest z coordinate is set to 0.
        """
        all_vertices = self.mesh_data.vectors.reshape(-1, 3)

        # Calculate the min and max coordinates for bounding box
        min_coords = all_vertices.min(axis=0)
        max_coords = all_vertices.max(axis=0)

        # Center x and y by calculating the bounding box center
        bounding_box_center = (min_coords + max_coords) / 2.0
        bounding_box_center[2] = min_coords[2]  # For z, use the lowest point

        # Calculate the translation
        translation = -bounding_box_center
        translation[2] = -min_coords[
            2
        ]  # Translate only enough to set the lowest z to 0

        # Apply the translation to the mesh
        self.mesh_data.translate(translation)

        # Update translation property to reflect the applied translation
        self.translation = [
            t + c for t, c in zip(self.translation, translation)
        ]

    def _get_triangle_count(self, path: str) -> int:
        """
        Get the number of triangles in the mesh.

        Parameters:
            path (str): Path to the mesh file.

        Returns:
            int: Number of triangles in the mesh.

        Raises:
            FileNotFoundError: If the mesh file does not exist.
            Exception: If there is an error reading the STL file.
        """
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Mesh file not found: {path}")

        try:
            mesh_data = stl_mesh.Mesh.from_file(path)
            return len(mesh_data.vectors)
        except Exception as e:
            raise Exception(f"Error reading STL file: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            dict: Dictionary representation of the current state of the object.
        """
        resource_dict = super().to_dict()
        resource_dict.update(
            {
                "translation": self.translation,
                "auto_center": self.auto_center,
                "rotation": self.rotation,
                "scale": self.scale,
                "enhance_mesh": self.enhance_mesh,
                "simplify_mesh": self.simplify_mesh,
                "target_ratio": self.target_ratio,
                "properties": {
                    "original_triangle_count": self.original_triangle_count
                },
            }
        )
        return resource_dict
