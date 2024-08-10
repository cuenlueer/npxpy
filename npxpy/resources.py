# -*- coding: utf-8 -*-
"""
npxpy
Created on Thu Feb 29 11:49:17 2024

@author: Caghan Uenlueer
Neuromorphic Quantumphotonics
Heidelberg University
E-Mail:	caghan.uenlueer@kip.uni-heidelberg.de

This file is part of npxpy (formerly nanoAPI), which is licensed under the GNU 
Lesser General Public License v3.0. You can find a copy of this license at
https://www.gnu.org/licenses/lgpl-3.0.html
"""
import uuid
import os
import hashlib
from typing import Dict, Any, List
from stl import mesh as stl_mesh
from pydantic import BaseModel, Field, field_validator

class Resource:
    """
    A class to represent a resource.

    Attributes:
        id (str): Unique identifier for the resource.
        type (str): Type of the resource.
        name (str): Name of the resource.
        path (str): Path where the resource is loaded from.
        unique_attributes (dict): Additional attributes specific to the resource type.
        fetch_from (str): Original path from which the resource was fetched.
    """
    def __init__(self, resource_type: str, name: str, path: str, **kwargs):
        """
        Initialize the resource with the specified parameters.

        Parameters:
            resource_type (str): Type of the resource.
            name (str): Name of the resource.
            path (str): Path where the resource is loaded from.
            **kwargs: Additional keyword arguments for unique attributes.
        """
        if not name or not name.strip():
            raise ValueError("Resource: The 'name' parameter must not be an empty string.")
            
            
        self.id = str(uuid.uuid4())
        self._type = resource_type
        self.name = name
        self.path = self.generate_path(path)
        self.unique_attributes = kwargs
        self.fetch_from = path
        
    def generate_path(self, file_path: str) -> str:
        """
        Generate a path for the resource based on the MD5 hash of the file content.

        Parameters:
            file_path (str): Path to the file.

        Returns:
            str: Generated path for the resource.

        Raises:
            FileNotFoundError: If the file at file_path does not exist.
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as file:
            for chunk in iter(lambda: file.read(4096), b""):
                md5_hash.update(chunk)
        
        file_hash = md5_hash.hexdigest()
        target_path = f'resources/{file_hash}/{os.path.basename(file_path)}'
        return target_path
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            dict: Dictionary representation of the current state of the object.
        """
        resource_dict = {
            "type": self._type,
            "id": self.id,
            "name": self.name,
            "path": self.path,
            **self.unique_attributes
        }
        return resource_dict
    
    
class Image(Resource):
    """
    A class to represent an image resource.
    """
    def __init__(self, path: str, name: str = 'image'):
        """
        Initialize the image resource with the specified parameters.

        Parameters:
            path (str): Path where the image is stored.
            name (str, optional): Name of the image resource. Defaults to 'image'.
        """
        # Ensure the path is valid
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Image file not found: {path}")

        super().__init__(resource_type='image_file', name=name, path=path)

class MeshValidator(BaseModel):
    path: str
    resource_type: str = 'mesh_file'
    name: str = 'mesh'
    translation: List[float] = Field(default_factory=lambda: [0, 0, 0])
    auto_center: bool = False
    rotation: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    scale: List[float] = Field(default_factory=lambda: [1.0, 1.0, 1.0])
    enhance_mesh: bool = True
    simplify_mesh: bool = False
    target_ratio: float = Field(default=100.0, ge=0, le=100)

    @field_validator('path')
    def check_file_exists(cls, v):
        if not os.path.isfile(v):
            raise FileNotFoundError(f"File not found: {v}")
        return v
    
    @field_validator('translation', 'rotation', 'scale')
    def check_list_length(cls, v):
        if len(v) != 3:
            raise ValueError(f"List must have exactly 3 elements, got {len(v)}")
        return v

class Mesh(Resource):
    """
    A class to represent a mesh resource.

    Attributes:
        original_triangle_count (int): The original number of triangles in the mesh.
    """
    def __init__(self, path: str, name: str = 'mesh',
                 translation: List[float] = [0, 0, 0],  # number in um
                 auto_center: bool = False,
                 rotation: List[float] = [0.0, 0.0, 0.0],  # number in deg
                 scale: List[float] = [1.0, 1.0, 1.0],  # scale number
                 enhance_mesh: bool = True,
                 simplify_mesh: bool = False,
                 target_ratio: float = 100.0):
        """
        Initialize the mesh resource with the specified parameters.

        Parameters:
            resource_type (str): Type of the resource.
            path (str): Path where the mesh is stored.
            name (str, optional): Name of the mesh resource. Defaults to 'mesh'.
            translation (List[float], optional): Translation values [x, y, z]. Defaults to [0, 0, 0].
            auto_center (bool, optional): Whether to auto-center the mesh. Defaults to False.
            rotation (List[float], optional): Rotation values [psi, theta, phi]. Defaults to [0.0, 0.0, 0.0].
            scale (List[float], optional): Scale values [x, y, z]. Defaults to [1.0, 1.0, 1.0].
            enhance_mesh (bool, optional): Whether to enhance the mesh. Defaults to True.
            simplify_mesh (bool, optional): Whether to simplify the mesh. Defaults to False.
            target_ratio (float, optional): Target ratio for mesh simplification. Defaults to 100.0.

        Raises:
            ValueError: If target_ratio is not between 0 and 100.
            FileNotFoundError: If the mesh file does not exist.
        """
        # Validate inputs using MeshValidator
        validated_data = MeshValidator(
            path=path, name=name, translation=translation, auto_center=auto_center,
            rotation=rotation, scale=scale, enhance_mesh=enhance_mesh,
            simplify_mesh=simplify_mesh, target_ratio=target_ratio
        ).dict()
        
        # Initialize the Resource part
        super().__init__(**validated_data)

        # Assign validated attributes to self
        self.translation = validated_data['translation']
        self.auto_center = validated_data['auto_center']
        self.rotation = validated_data['rotation']
        self.scale = validated_data['scale']
        self.enhance_mesh = validated_data['enhance_mesh']
        self.simplify_mesh = validated_data['simplify_mesh']
        self.target_ratio = validated_data['target_ratio']

        self.original_triangle_count = self._get_triangle_count(self.fetch_from)

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
        resource_dict['properties'] = {'original_triangle_count': self.original_triangle_count}
        return resource_dict
