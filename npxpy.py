# -*- coding: utf-8 -*-
"""
npxpy (formerly nanoAPI)
v0.0.4-alpha
Created on Thu Feb 29 11:49:17 2024

@author: Caghan Uenlueer
Neuromorphic Quantumphotonics
Heidelberg University
E-Mail:	caghan.uenlueer@kip.uni-heidelberg.de

This file is part of npxpy (formerly nanoAPI), which is licensed under the GNU Lesser General Public License v3.0.
You can find a copy of this license at https://www.gnu.org/licenses/lgpl-3.0.html
"""
import toml
import uuid
import json
from datetime import datetime
import os
import hashlib
import copy
from typing import Dict, Any, List, Optional, Tuple, Union
import zipfile
from stl import mesh as stl_mesh
from pydantic import BaseModel, Field, ValidationError, model_validator, field_validator





class Preset(BaseModel):
    """
    A class to represent a preset with various parameters related to writing and hatching settings.
    
    Attributes:
        name (str): Name of the preset.
        valid_objectives (List[str]): Valid objectives for the preset.
        valid_resins (List[str]): Valid resins for the preset.
        valid_substrates (List[str]): Valid substrates for the preset.
        writing_speed (float): Writing speed.
        writing_power (float): Writing power.
        slicing_spacing (float): Slicing spacing.
        hatching_spacing (float): Hatching spacing.
        hatching_angle (float): Hatching angle.
        hatching_angle_increment (float): Hatching angle increment.
        hatching_offset (float): Hatching offset.
        hatching_offset_increment (float): Hatching offset increment.
        hatching_back_n_forth (bool): Whether hatching is back and forth.
        mesh_z_offset (float): Mesh Z offset.
        grayscale_layer_profile_nr_layers (float): Number of layers for grayscale layer profile.
        grayscale_writing_power_minimum (float): Minimum writing power for grayscale.
        grayscale_exponent (float): Grayscale exponent.
        unique_attributes (Dict[str, Any]): Additional dynamic attributes.
    """
    class Config:
        extra = 'allow'
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = '25x_IP-n162'
    valid_objectives: List[str] = Field(default_factory=lambda: ["25x"])
    valid_resins: List[str] = Field(default_factory=lambda: ["IP-n162"])
    valid_substrates: List[str] = Field(default_factory=lambda: ["*"])
    writing_speed: float = Field(gt=0, default=250000.0)
    writing_power: float = Field(ge=0, default=50.0)
    slicing_spacing: float = Field(gt=0, default=0.8)
    hatching_spacing: float = Field(gt=0, default=0.3)
    hatching_angle: float = 0.0
    hatching_angle_increment: float = 0.0
    hatching_offset: float = 0.0
    hatching_offset_increment: float = 0.0
    hatching_back_n_forth: bool = True
    mesh_z_offset: float = 0.0
    grayscale_multilayer_enabled: bool = False
    grayscale_layer_profile_nr_layers: float = Field(ge=0, default=6)
    grayscale_writing_power_minimum: float = Field(ge=0, default=0.0)
    grayscale_exponent: float = Field(gt=0, default=1.0)
    unique_attributes: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='before')
    def validate_list(cls, values):
        for key in ['valid_objectives', 'valid_resins', 'valid_substrates']:
            if isinstance(values.get(key), str):
                values[key] = [values[key]]
        return values

    @model_validator(mode='after')
    def validate_values(cls, values):
        valid_objectives = {'25x', '63x', '*'}
        valid_resins = {'IP-PDMS', 'IPX-S', 'IP-L', 'IP-n162', 'IP-Dip2', 'IP-Dip', 'IP-S', 'IP-Visio', '*'}
        valid_substrates = {'*', 'FuSi', 'Si'}

        if not set(values.valid_objectives).issubset(valid_objectives):
            raise ValueError(f"Invalid valid_objectives: {values.valid_objectives}")
        if not set(values.valid_resins).issubset(valid_resins):
            raise ValueError(f"Invalid valid_resins: {values.valid_resins}")
        if not set(values.valid_substrates).issubset(valid_substrates):
            raise ValueError(f"Invalid valid_substrates: {values.valid_substrates}")

        return values

    def set_grayscale_multilayer(
        self, 
        grayscale_layer_profile_nr_layers: float = 6.0, 
        grayscale_writing_power_minimum: float = 0.0, 
        grayscale_exponent: float = 1.0
    ) -> 'Preset':
        """
        Enable grayscale multilayer and set the related attributes.

        Parameters:
            grayscale_layer_profile_nr_layers (float): Number of layers for grayscale layer profile.
            grayscale_writing_power_minimum (float): Minimum writing power for grayscale.
            grayscale_exponent (float): Grayscale exponent.

        Returns:
            Preset: The instance with updated grayscale multilayer settings.

        Raises:
            ValueError: If any of the parameters are invalid.
        """
        if grayscale_layer_profile_nr_layers < 0:
            raise ValueError("grayscale_layer_profile_nr_layers must be greater or equal to 0.")
        if grayscale_writing_power_minimum < 0:
            raise ValueError("grayscale_writing_power_minimum must be greater or equal to 0.")
        if grayscale_exponent <= 0:
            raise ValueError("grayscale_exponent must be greater than 0.")

        self.grayscale_multilayer_enabled = True
        self.grayscale_layer_profile_nr_layers = grayscale_layer_profile_nr_layers
        self.grayscale_writing_power_minimum = grayscale_writing_power_minimum
        self.grayscale_exponent = grayscale_exponent
        return self

    def duplicate(self) -> 'Preset':
        """
        Create a duplicate of the current preset instance.

        Returns:
            Preset: A duplicate of the current preset instance.
        """
        duplicate = copy.copy(self)
        duplicate.id = str(uuid.uuid4())
        return duplicate

    @classmethod
    def load_single(cls, file_path: str, fresh_id: bool = True) -> 'Preset':
        """
        Load a single preset from a .toml file.

        Parameters:
            file_path (str): The path to the .toml file.
            fresh_id (bool): Whether to assign a fresh ID to the loaded preset.

        Returns:
            Preset: The loaded preset instance.

        Raises:
            FileNotFoundError: If the file at file_path does not exist.
            toml.TomlDecodeError: If there is an error decoding the TOML file.
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r') as toml_file:
            data = toml.load(toml_file)

        # Extract the file name without the extension
        name = os.path.splitext(os.path.basename(file_path))[0]

        # Get the valid fields of the model
        valid_fields = cls.__fields__.keys()

        # Filter out invalid keys from data
        valid_data = {key: value for key, value in data.items() if key in valid_fields}

        try:
            cls_instance = cls(name=name, **valid_data)
        except ValidationError as e:
            raise ValidationError(model=cls, errors=e.errors())

        if not fresh_id:
            cls_instance.id = data.get('id', cls_instance.id)

        return cls_instance

    @classmethod
    def load_multiple(cls, directory_path: str, print_names: bool = False, fresh_id: bool = True) -> List['Preset']:
        """
        Load multiple presets from a directory containing .toml files.

        Parameters:
            directory_path (str): The path to the directory containing .toml files.
            print_names (bool): If True, print the names of the files in the order they are loaded.
            fresh_id (bool): Whether to assign fresh IDs to the loaded presets.

        Returns:
            List[Preset]: A list of loaded preset instances.

        Raises:
            FileNotFoundError: If the directory_path does not exist.
        """
        if not os.path.isdir(directory_path):
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        presets = []
        for file_name in sorted(os.listdir(directory_path)):
            if file_name.endswith('.toml'):
                file_path = os.path.join(directory_path, file_name)
                preset = cls.load_single(file_path, fresh_id)
                presets.append(preset)
                if print_names:
                    print(file_name)
        return presets

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the preset and its unique attributes to a dictionary format.

        Returns:
            Dict[str, Any]: Dictionary representation of the preset.
        """
        preset_dict = self.dict(exclude={'unique_attributes'})
        preset_dict.update(self.unique_attributes)
        return preset_dict

    def export(self, file_path: str = None) -> None:
        """
        Export the preset to a file that can be loaded by nanoPrintX and/or npxpy.

        Parameters:
            file_path (str): The path to the .toml file to be created. If not provided,
                             defaults to the current directory with the preset's name.

        Raises:
            IOError: If there is an error writing to the file.
        """
        if file_path is None:
            file_path = f"{self.name}.toml"
        elif not file_path.endswith('.toml'):
            file_path += '.toml'

        data = self.to_dict()

        with open(file_path, 'w') as toml_file:
            toml.dump(data, toml_file)







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
                 target_ratio: float = 100.0                 ):
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

#Implementation of validator not foolproof. However, it still ensures an instance of control while initialization.
class NodeValidator(BaseModel):

    name: str
    properties: Dict[str, Any] = {}
    geometry: Dict[str, Any] = {}
    position: List[float] = [0.0, 0.0, 0.0]
    rotation: List[float] = [0.0, 0.0, 0.0]

    @field_validator('position', 'rotation')
    def check_list_length(cls, v):
        if len(v) != 3:
            raise ValueError(f"List must have exactly 3 elements, got {len(v)}")
        return v
    
    @field_validator('name')
    def check_name_not_empty(cls, v):
        if not v.strip():
            raise Warning("Name must not be an empty string")
        return v

    
class Node:
    """
    A class to represent a node object of nanoPrintX with various attributes and methods for managing node hierarchy.

    Attributes:
        type (str): Type of the node.
        name (str): Name of the node.
        position (List[float]): Position of the node [x, y, z].
        rotation (List[float]): Rotation of the node [psi, theta, phi].
        children (List[str]): List of children node IDs.
        children_nodes (List[Node]): List of children nodes.
        properties (Any): Properties of the node.
        geometry (Any): Geometry of the node.
        unique_attributes (Dict[str, Any]): Additional dynamic attributes.
    """
    def __init__(self, node_type: str,
                 name: str,
                 properties: Dict[str, Any] = {}, 
                 geometry: Dict[str, Any] = {}, 
                 position: List[float] = [0.0, 0.0, 0.0],
                 rotation: List[float] = [0.0, 0.0, 0.0],
                 **kwargs: Any):
        """
        Initialize a Node instance with the specified parameters.

        Parameters:
            node_type (str): Type of the node.
            name (str): Name of the node.
            properties (Any, optional): Properties of the node. Defaults to None.
            geometry (Any, optional): Geometry of the node. Defaults to None.
            **kwargs (Any): Additional dynamic attributes.
        """
        
        self.id = str(uuid.uuid4())
        self._type = node_type
        validated_data = NodeValidator(
                         
                         name=name,
                         properties=properties,
                         geometry=geometry,
                         position=position,
                         rotation=rotation
                         ).dict()
        self.name = validated_data['name']
        self.position = validated_data['position']
        self.rotation = validated_data['rotation']
        self.properties = validated_data['properties']
        self.geometry = validated_data['geometry']
        
        self.children: List[str] = kwargs.get('children', [])
        self.children_nodes: List[Node] = []
        self.all_descendants: List[Node] = self._generate_all_descendants()
        
        self.parents_nodes: List[Node] = []
        self.all_ancestors: List[Node] = []
        
        self.unique_attributes = {key: value for key, value in kwargs.items() if key not in ['children']}
        
    def add_child(self, child_node: 'Node'):
        """
        Add a child node to the current node.

        Parameters:
            child_node (Node): The child node to add.
        """
        if self._type == 'structure':
            raise ValueError('Structure objects (including Text and Lens) are terminal nodes! They cannot have children!')
        if child_node._type == 'project':
            raise ValueError('A project node can never be a child to any node!')

        if child_node._type == 'structure':
            if not self._has_ancestor_of_type('scene'):
                print('WARNING: Structures have to be inside Scene nodes!')
        elif child_node._type == 'scene':
            if self._has_ancestor_of_type('scene'):
                raise ValueError('Nested scenes are not allowed!')
                
        child_node.parents_nodes.append(self)
        self.children_nodes.append(child_node)
        self.all_descendants = self._generate_all_descendants()  # Update descendants list
        child_node.all_ancestors = child_node._generate_all_ancestors()  # Update ancestors list
        
        for i in self.all_descendants + child_node.all_ancestors:  # update for the whole batch of nodes their ancestors and descendants
            i.all_descendants = i._generate_all_descendants()
            i.all_ancestors = i._generate_all_ancestors()
        return self

    def _has_ancestor_of_type(self, node_type: str) -> bool:
        """
        Check if the current node has an ancestor of the specified type.

        Parameters:
            node_type (str): The type of the ancestor node to check for.

        Returns:
            bool: True if an ancestor of the specified type exists, False otherwise.
        """
        current_node = self
        while current_node:
            if current_node._type == node_type:
                return True
            current_node = getattr(current_node, 'parent', None)  # Assumes a parent attribute is set for each node
        return False
 
    def tree(self, level: int = 0, show_type: bool = True, show_id: bool = False, is_last: bool = True, prefix: str = ''):
        """
        Print the tree structure of the node and its descendants.

        Parameters:
            level (int, optional): The current level in the tree. Defaults to 0.
            show_type (bool, optional): Whether to show the node type. Defaults to True.
            show_id (bool, optional): Whether to show the node ID. Defaults to False.
            is_last (bool, optional): Whether the node is the last child. Defaults to True.
            prefix (str, optional): The prefix for the current level. Defaults to ''.
        """
        indent = '' if level == 0 else prefix + ('└' if is_last else '├') + '──'
        output = f"{indent}{self.name} ({self._type})" if show_type else f"{indent}{self.name}"
        if show_id:
            output += f" (ID: {self.id})"
        print(output)
        new_prefix = prefix + ('    ' if is_last else '│   ')
        child_count = len(self.children_nodes)
        for index, child in enumerate(self.children_nodes):
            child.tree(level + 1, show_type, show_id, is_last=(index == child_count - 1), prefix=new_prefix)

    def deepcopy_node(self, copy_children: bool = True) -> 'Node':
        """
        Create a deep copy of the node.

        Parameters:
            copy_children (bool, optional): Whether to copy children nodes. Defaults to True.

        Returns:
            Node: A deep copy of the current node.
        """
        if copy_children:
            copied_node = copy.deepcopy(self)
            self._reset_ids(copied_node)
        else:
            copied_node = copy.copy(self)
            copied_node.id = str(uuid.uuid4())
            copied_node.children_nodes = []
        return copied_node

    def _reset_ids(self, node: 'Node'):
        """
        Reset the IDs of the node and its descendants.

        Parameters:
            node (Node): The node to reset IDs for.
        """
        node.id = str(uuid.uuid4())
        for child in node.children_nodes:
            self._reset_ids(child)

    def grab_nodes(self, node_types_with_indices: List[Tuple[str, int]]) -> 'Node':
        """
        Grab nodes based on the specified types and indices.

        Parameters:
            node_types_with_indices (List[Tuple[str, int]]): List of tuples containing node type and index.

        Returns:
            Node: The node found based on the specified types and indices.
        """
        current_level_nodes = [self]
        for node_type, index in node_types_with_indices:
            next_level_nodes = []
            for node in current_level_nodes:
                filtered_nodes = [child for child in node.children_nodes if child._type == node_type]
                if len(filtered_nodes) > index:
                    next_level_nodes.append(filtered_nodes[index])
            current_level_nodes = next_level_nodes
        return current_level_nodes[0]

    def _generate_all_descendants(self) -> List['Node']:
        """
        Generate a list of all descendant nodes.

        Returns:
            List[Node]: List of all descendant nodes.
        """
        descendants = []
        nodes_to_check = [self]
        while nodes_to_check:
            current_node = nodes_to_check.pop()
            descendants.extend(current_node.children_nodes)
            nodes_to_check.extend(current_node.children_nodes)
        return descendants
    
    def _generate_all_ancestors(self) -> List['Node']:
        """
        Generate a list of all ancestor nodes.

        Returns:
            List[Node]: List of all descendant nodes.
        """
        ancestors = []
        nodes_to_check = [self]
        while nodes_to_check:
            current_node = nodes_to_check.pop()
            ancestors.extend(current_node.parents_nodes)
            nodes_to_check.extend(current_node.parents_nodes)
        return ancestors

    def grab_all_nodes_bfs(self, node_type: str) -> List['Node']:
        """
        Grab all nodes of the specified type using breadth-first search.

        Parameters:
            node_type (str): The type of nodes to grab.

        Returns:
            List[Node]: List of nodes of the specified type.
        """
        result = []
        nodes_to_check = [self]
        while nodes_to_check:
            current_node = nodes_to_check.pop(0)  # Dequeue from the front
            if current_node._type == node_type:
                result.append(current_node)
            nodes_to_check.extend(current_node.children_nodes)  # Enqueue children
        return result

    def append_node(self, node_to_append: 'Node'):
        """
        Append a node to the deepest descendant.

        Parameters:
            node_to_append (Node): The node to append.
        """
        grandest_grandchild = self._find_grandest_grandchild(self)
        grandest_grandchild.add_child(node_to_append)

    def _find_grandest_grandchild(self, current_node: 'Node') -> 'Node':
        """
        Find the deepest descendant node.

        Parameters:
            current_node (Node): The current node to start the search from.

        Returns:
            Node: The deepest descendant node.
        """
        if not current_node.children_nodes:
            return current_node
        else:
            grandest_children = [self._find_grandest_grandchild(child) for child in current_node.children_nodes]
            return max(grandest_children, key=lambda node: self._depth(node))

    def _depth(self, node: 'Node') -> int:
        """
        Calculate the depth of a node.

        Parameters:
            node (Node): The node to calculate the depth for.

        Returns:
            int: The depth of the node.
        """
        depth = 0
        current = node
        while current.children_nodes:
            current = current.children_nodes[0]
            depth += 1
        return depth

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the node and its attributes to a dictionary format.

        Returns:
            Dict[str, Any]: Dictionary representation of the node.
        """
        self.children = [i.id for i in self.children_nodes]
        node_dict = {
            "type": self._type,
            "id": self.id,
            "name": self.name,
            "position": self.position,
            "rotation": self.rotation,
            "children": self.children,
            "properties": self.properties,
            "geometry": self.geometry,
            **self.unique_attributes
        }
        
        valid_data = NodeValidator(
                         
                         name=node_dict['name'],
                         properties=node_dict['properties'],
                         geometry=node_dict['geometry'],
                         position=node_dict['position'],
                         rotation=node_dict['rotation']
                         ).dict()
        node_dict.update(valid_data)
        
        return node_dict




class Project(Node):
    """
    Class: project nodes.

    Attributes:
        presets (list): List of presets for the project.
        resources (list): List of resources for the project.
        project_info (dict): Information about the project including author, objective, resin, substrate, and creation date.
    """
    def __init__(self, objective: str,  # '25x' or '63x' or '*'
                 resin: str,  # can be 'IP-PDMS', 'IPX-S', 'IP-L', 'IP-n162', 'IP-Dip2', 'IP-Dip', 'IP-S', 'IP-Vision', '*'
                 substrate: str  # '*', 'Si' and 'FuSi'
                 ):
        """
        Initialize the project with the specified parameters.

        Parameters:
            objective (str): Objective of the project.
            resin (str): Resin used in the project.
            substrate (str): Substrate used in the project.

        Raises:
            ValueError: If any of the parameters have invalid values.
        """
        valid_objectives = {'25x', '63x', '*'}
        valid_resins = {'IP-PDMS', 'IPX-S', 'IP-L', 'IP-n162', 'IP-Dip2', 'IP-Dip', 'IP-S', 'IP-Vision', '*'}
        valid_substrates = {'*', 'Si', 'FuSi'}

        if objective not in valid_objectives:
            raise ValueError(f"Invalid objective: {objective}. Must be one of {valid_objectives}.")
        if resin not in valid_resins:
            raise ValueError(f"Invalid resin: {resin}. Must be one of {valid_resins}.")
        if substrate not in valid_substrates:
            raise ValueError(f"Invalid substrate: {substrate}. Must be one of {valid_substrates}.")

        super().__init__(node_type='project', name='Project',
                         objective=objective, resin=resin, substrate=substrate)

        self.presets = []
        self.resources = []
        self.project_info = {
            "author": os.getlogin(),
            "objective": objective,
            "resin": resin,
            "substrate": substrate,
            "creation_date": datetime.now().replace(microsecond=0).isoformat()
        }

    def load_resources(self, resources: Union[Resource, List[Resource]]):  # This has to be an object from the class Resource (including inheriting classes)!
        """
        Adds resources to the resources list. The input can be either a list of resources
        or a single resource element.

        Args:
            resources (Resource or list): A list of resources or a single resource element.

        Raises:
            TypeError: If the resources are not of type Resource or list of Resource.
        """
        if not isinstance(resources, list):
            resources = [resources]

        if not all(isinstance(resource, Resource) for resource in resources):
            raise TypeError("All resources must be instances of the Resource class or its subclasses.")

        self.resources.extend(resources)

    def load_presets(self, presets: Union[Preset, List[Preset]]):  # This has to be an object from the class Preset!
        """
        Adds presets to the presets list. The input can be either a list of presets
        or a single preset element.

        Args:
            presets (Preset or list): A list of presets or a single preset element.

        Raises:
            TypeError: If the presets are not of type Preset or list of Preset.
        """
        if not isinstance(presets, list):
            presets = [presets]

        if not all(isinstance(preset, Preset) for preset in presets):
            raise TypeError("All presets must be instances of the Preset class.")

        self.presets.extend(presets)

    def _create_toml_data(self, presets: List[Any], resources: List[Any], nodes: List[Node]) -> str:
        """
        Creates TOML data for the project.

        Args:
            presets (list): List of presets.
            resources (list): List of resources.
            nodes (list): List of nodes.

        Returns:
            str: TOML data as a string.
        """
        data = {
            "presets": [preset.to_dict() for preset in presets],
            "resources": [resource.to_dict() for resource in resources],
            "nodes": [node.to_dict() for node in nodes]
        }
        return toml.dumps(data)

    def _create_project_info(self, project_info_json: Dict[str, Any]) -> str:
        """
        Creates JSON data for project info.

        Args:
            project_info_json (dict): Project information dictionary.

        Returns:
            str: JSON data as a string.
        """
        return json.dumps(project_info_json, indent=4)

    def _add_file_to_zip(self, zip_file: zipfile.ZipFile, file_path: str, arcname: str):
        """
        Adds a file to a zip archive.

        Args:
            zip_file (zipfile.ZipFile): The zip file object.
            file_path (str): Path to the file to add.
            arcname (str): Archive name of the file in the zip.
        """
        with open(file_path, 'rb') as f:
            zip_file.writestr(arcname, f.read())

    def nano(self, project_name: str = 'Project', path: str = './'):
        """
        Creates a .nano file for the project.

        This method collects the current presets and resources, saves them into a .toml file, and packages them
        along with project information into a .nano file (a .zip archive with a custom extension).

        Args:
            project_name (str): The name of the project, used as the base name for the .nano file.
            path (str, optional): The directory path where the .nano file will be created. Defaults to './'.
        """
        print('npxpy: Attempting to create .nano-file...')

        # Ensure the path ends with a slash
        if not path.endswith('/'):
            path += '/'

        # Prepare paths and data
        nano_file_path = os.path.join(path, f'{project_name}.nano')
        toml_data = self._create_toml_data(self.presets, self.resources, [self] + self.all_descendants)
        project_info_data = self._create_project_info(self.project_info)

        with zipfile.ZipFile(nano_file_path, 'w', zipfile.ZIP_STORED) as nano_zip:
            # Add the __main__.toml to the zip file
            nano_zip.writestr('__main__.toml', toml_data)
            
            # Add the project_info.json to the zip file
            nano_zip.writestr('project_info.json', project_info_data)

            # Add the resources to the zip file
            for resource in self.resources:
                src_path = resource.fetch_from
                arcname = resource.path
                if os.path.isfile(src_path):
                    self._add_file_to_zip(nano_zip, src_path, arcname)
                else:
                    print(f'File not found: {src_path}')

        print('npxpy: .nano-file created successfully.')


class Scene(Node):
    """
    scene nodes.

    Attributes:
        position (List[float]): Position of the scene [x, y, z].
        rotation (List[float]): Rotation of the scene [psi, theta, phi].
    """
    def __init__(self, name: str = 'Scene', position: List[float] = [0, 0, 0], rotation: List[float] = [0.0, 0.0, 0.0], writing_direction_upward: bool = True):
        """
        Initialize the scene with a name and writing direction.

        Parameters:
            name (str): The name of the scene node.
            position (List[float]): Initial position of the scene [x, y, z].
            rotation (List[float]): Initial rotation of the scene [psi, theta, phi].
            writing_direction_upward (bool): Writing direction of the scene.
        """
        super().__init__('scene', name, position=position, rotation=rotation, writing_direction_upward=writing_direction_upward)
        
    def position_at(self, position: List[float] = [0, 0, 0], rotation: List[float] = [0.0, 0.0, 0.0]):
        """
        Set the current position and rotation of the scene.

        Parameters:
            position (List[float]): List of position values [x, y, z].
            rotation (List[float]): List of rotation angles [psi, theta, phi].

        Returns:
            self: The instance of the Scene class.

        Raises:
            ValueError: If position or rotation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(position) != 3:
            raise ValueError("position must be a list of three elements.")
        if not all(isinstance(p, (int, float)) for p in position):
            raise ValueError("All position elements must be numbers.")
        
        if len(rotation) != 3:
            raise ValueError("rotation must be a list of three elements.")
        if not all(isinstance(r, (int, float)) for r in rotation):
            raise ValueError("All rotation elements must be numbers.")
        
        self.position = position
        self.rotation = rotation
        return self
    
    def translate(self, translation: List[float]):
        """
        Translate the current position by the specified translation.

        Parameters:
            translation (List[float]): List of translation values [dx, dy, dz].

        Raises:
            ValueError: If translation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(translation) != 3:
            raise ValueError("translation must be a list of three elements.")
        if not all(isinstance(t, (int, float)) for t in translation):
            raise ValueError("All translation elements must be numbers.")
        
        self.position = [pos + trans for pos, trans in zip(self.position, translation)]

    def rotate(self, rotation: List[float]):
        """
        Rotate the scene by the specified rotation angles.

        Parameters:
            rotation (List[float]): List of rotation angles to apply [d_psi, d_theta, d_phi].

        Raises:
            ValueError: If rotation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(rotation) != 3:
            raise ValueError("rotation must be a list of three elements.")
        if not all(isinstance(r, (int, float)) for r in rotation):
            raise ValueError("All rotation elements must be numbers.")
        
        self.rotation = [(angle + rot) % 360 for angle, rot in zip(self.rotation, rotation)]
        
    def to_dict(self) -> Dict:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            dict: Dictionary representation of the current state of the object.
        """
        node_dict = super().to_dict()
        return node_dict


class Group(Node):
    """
    Class: group nodes.

    Attributes:
        position (List[float]): Position of the group [x, y, z].
        rotation (List[float]): Rotation of the group [psi, theta, phi].
    """
    def __init__(self, name: str = 'Group', position: List[float] = [0, 0, 0], rotation: List[float] = [0.0, 0.0, 0.0]):
        """
        Initialize the group with a name.

        Parameters:
            name (str): The name of the group node.
        """
        super().__init__('group', name, position=position, rotation=rotation)

        
    def position_at(self, position: List[float] = [0, 0, 0], rotation: List[float] = [0.0, 0.0, 0.0]):
        """
        Set the current position and rotation of the group.

        Parameters:
            position (List[float]): List of position values [x, y, z].
            rotation (List[float]): List of rotation angles [psi, theta, phi].

        Returns:
            self: The instance of the Group class.

        Raises:
            ValueError: If position or rotation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(position) != 3:
            raise ValueError("position must be a list of three elements.")
        if not all(isinstance(p, (int, float)) for p in position):
            raise ValueError("All position elements must be numbers.")
        
        if len(rotation) != 3:
            raise ValueError("rotation must be a list of three elements.")
        if not all(isinstance(r, (int, float)) for r in rotation):
            raise ValueError("All rotation elements must be numbers.")
        
        self.position = position
        self.rotation = rotation
        return self
    
    def translate(self, translation: List[float]):
        """
        Translate the current position by the specified translation.

        Parameters:
            translation (List[float]): List of translation values [dx, dy, dz].

        Raises:
            ValueError: If translation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(translation) != 3:
            raise ValueError("translation must be a list of three elements.")
        if not all(isinstance(t, (int, float)) for t in translation):
            raise ValueError("All translation elements must be numbers.")
        
        self.position = [pos + trans for pos, trans in zip(self.position, translation)]

    def rotate(self, rotation: List[float]):
        """
        Rotate the group by the specified rotation angles.

        Parameters:
            rotation (List[float]): List of rotation angles to apply [d_psi, d_theta, d_phi].

        Raises:
            ValueError: If rotation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(rotation) != 3:
            raise ValueError("rotation must be a list of three elements.")
        if not all(isinstance(r, (int, float)) for r in rotation):
            raise ValueError("All rotation elements must be numbers.")
        
        self.rotation = [(angle + rot) % 360 for angle, rot in zip(self.rotation, rotation)]
        
    def to_dict(self) -> Dict:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            dict: Dictionary representation of the current state of the object.
        """
        node_dict = super().to_dict()
        return node_dict


class Array(Node):
    """
    Class: array nodes.

    Attributes:
        position (List[float]): Position of the array [x, y, z].
        rotation (List[float]): Rotation of the array [psi, theta, phi].
        count (List[int]): Number of grid points in [x, y] direction.
        spacing (List[float]): Spacing of the grid in [width, height].
        order (str): Order of the array ('Lexical' or 'Meander').
        shape (str): Shape of the array ('Rectangular' or 'Round').
    """
    def __init__(self, name: str = 'Array', position: List[float] = [0, 0, 0], rotation: List[float] = [0.0, 0.0, 0.0],
                 count: List[int] = [5, 5], spacing: List[float] = [100.0, 100.0],
                 order: str = "Lexical", shape: str = 'Rectangular'):
        """
        Initialize the array with a name, position, rotation, count, spacing, order, and shape.

        Parameters:
            name (str): The name of the array node.
            position (List[float]): Initial position of the array [x, y, z].
            rotation (List[float]): Initial rotation of the array [psi, theta, phi].
            count (List[int]): Number of grid points in [x, y] direction. Must be integers and greater than zero.
            spacing (List[float]): Spacing of the grid in [width, height]. Can be integers or floats.
            order (str): Order of the array. Can only be 'Lexical' or 'Meander'.
            shape (str): Shape of the array. Can only be 'Rectangular' or 'Round'.

        Raises:
            ValueError: If count elements are not integers or not greater than zero.
                        If spacing elements are not numbers.
                        If order is not 'Lexical' or 'Meander'.
                        If shape is not 'Rectangular' or 'Round'.
        """
        if not all(isinstance(c, int) and c > 0 for c in count):
            raise ValueError("All count elements must be integers greater than zero.")
        if not all(isinstance(s, (int, float)) for s in spacing):
            raise ValueError("All spacing elements must be numbers.")
        if order not in ['Lexical', 'Meander']:
            raise ValueError("order must be either 'Lexical' or 'Meander'.")
        if shape not in ['Rectangular', 'Round']:
            raise ValueError("shape must be either 'Rectangular' or 'Round'.")

        super().__init__('array', name=name, position=position, rotation=rotation,
                         order=order, shape=shape, count=count, spacing=spacing)
        
    def set_grid(self, count: List[int] = [5, 5], spacing: List[float] = [200.0, 200.0]):
        """
        Sets the grid point count and spacing.

        Parameters:
            count (List[int]): Number of grid points in [x, y] direction.
            spacing (List[float]): Spacing of the grid in [width, height].

        Returns:
            self: The instance of the Array class.

        Raises:
            ValueError: If count or spacing does not contain exactly two elements.
                        If count elements are not integers or not greater than zero.
                        If spacing elements are not numbers.
        """
        if len(count) != 2 or len(spacing) != 2:
            raise ValueError("count and spacing must each be lists of two elements.")
        if not all(isinstance(c, int) and c > 0 for c in count):
            raise ValueError("All count elements must be integers greater than zero.")
        if not all(isinstance(s, (int, float)) for s in spacing):
            raise ValueError("All spacing elements must be numbers.")
        
        self.count = count
        self.spacing = spacing
        return self
        
    def position_at(self, position: List[float] = [0, 0, 0], rotation: List[float] = [0.0, 0.0, 0.0]):
        """
        Set the current position and rotation of the array.

        Parameters:
            position (List[float]): List of position values [x, y, z].
            rotation (List[float]): List of rotation angles [psi, theta, phi].

        Returns:
            self: The instance of the Array class.

        Raises:
            ValueError: If position or rotation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(position) != 3:
            raise ValueError("position must be a list of three elements.")
        if not all(isinstance(p, (int, float)) for p in position):
            raise ValueError("All position elements must be numbers.")
        
        if len(rotation) != 3:
            raise ValueError("rotation must be a list of three elements.")
        if not all(isinstance(r, (int, float)) for r in rotation):
            raise ValueError("All rotation elements must be numbers.")
        
        self.position = position
        self.rotation = rotation
        return self
    
    def translate(self, translation: List[float]):
        """
        Translate the current position by the specified translation.

        Parameters:
            translation (List[float]): List of translation values [dx, dy, dz].

        Raises:
            ValueError: If translation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(translation) != 3:
            raise ValueError("translation must be a list of three elements.")
        if not all(isinstance(t, (int, float)) for t in translation):
            raise ValueError("All translation elements must be numbers.")
        
        self.position = [pos + trans for pos, trans in zip(self.position, translation)]

    def rotate(self, rotation: List[float]):
        """
        Rotate the array by the specified rotation angles.

        Parameters:
            rotation (List[float]): List of rotation angles to apply [d_psi, d_theta, d_phi].

        Raises:
            ValueError: If rotation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(rotation) != 3:
            raise ValueError("rotation must be a list of three elements.")
        if not all(isinstance(r, (int, float)) for r in rotation):
            raise ValueError("All rotation elements must be numbers.")
        
        self.rotation = [(angle + rot) % 360 for angle, rot in zip(self.rotation, rotation)]
    
    def to_dict(self) -> Dict:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            dict: Dictionary representation of the current state of the object.
        """
        node_dict = super().to_dict()
        return node_dict



class Structure(Node):
    def __init__(self, 
                 preset, #only objects from class Preset are allowed!
                 mesh, #only objects from class Mesh are allowed!
                 project: Optional[Project] = None,
                 auto_load_presets: bool = False,
                 auto_load_resources: bool = False,
                 size: List[float] = [100.0, 100.0, 100.0], # okay if int
                 name: str = 'Structure',
                 slicing_origin: str = 'scene_bottom',
                 slicing_offset: float = 0.0, # okay if int
                 priority: int = 0,
                 expose_individually: bool = False):
        """
        Initialize a Structure node.

        Parameters:
        preset (Resource): The preset associated with the structure.
        mesh (Resource): The mesh object to be used for the structure.
        project (Optional[Node]): The project context, if any, necessary for auto-loading resources.
        auto_load_presets (bool): Flag to auto-load presets.
        auto_load_resources (bool): Flag to auto-load resources.
        size (List[int]): The size (scaling) of the structure in micrometers [x, y, z].
        name (str): The name of the structure.
        slicing_origin (str): The origin for slicing. Must be one of 'structure_center', 'zero', 
                              'scene_top', 'scene_bottom', 'structure_top', 'structure_bottom', 'scene_center'.
        slicing_offset (float): The offset for slicing.
        priority (int): The priority of the structure. Must be >= 0.
        expose_individually (bool): Flag to expose the structure individually.
        """
        if priority < 0:
            raise ValueError("Priority must be greater than or equal to 0.")
        
        valid_slicing_origins = {'structure_center', 'zero', 'scene_top', 
                                 'scene_bottom', 'structure_top', 
                                 'structure_bottom', 'scene_center'}
        if slicing_origin not in valid_slicing_origins:
            raise ValueError(f"slicing_origin must be one of {valid_slicing_origins}")
        
        super().__init__('structure', 
                         name, 
                         preset=preset.id, 
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
        
        self._mesh=True
 
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

    def position_at(self, position: List[float] = [0, 0, 0], rotation: List[float] = [0.0, 0.0, 0.0]):
        """
        Set the current position and rotation of the array.

        Parameters:
            position (List[float]): List of position values [x, y, z].
            rotation (List[float]): List of rotation angles [psi, theta, phi].

        Returns:
            self: The instance of the Array class.

        Raises:
            ValueError: If position or rotation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(position) != 3:
            raise ValueError("position must be a list of three elements.")
        if not all(isinstance(p, (int, float)) for p in position):
            raise ValueError("All position elements must be numbers.")
        
        if len(rotation) != 3:
            raise ValueError("rotation must be a list of three elements.")
        if not all(isinstance(r, (int, float)) for r in rotation):
            raise ValueError("All rotation elements must be numbers.")
        
        self.position = position
        self.rotation = rotation
        return self

    def translate(self, translation: List[float]):
        """
        Translate the current position by the specified translation.

        Parameters:
            translation (List[float]): List of translation values [dx, dy, dz].

        Raises:
            ValueError: If translation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(translation) != 3:
            raise ValueError("translation must be a list of three elements.")
        if not all(isinstance(t, (int, float)) for t in translation):
            raise ValueError("All translation elements must be numbers.")
        
        self.position = [pos + trans for pos, trans in zip(self.position, translation)]

    def rotate(self, rotation: List[float]):
        """
        Rotate the array by the specified rotation angles.

        Parameters:
            rotation (List[float]): List of rotation angles to apply [d_psi, d_theta, d_phi].

        Raises:
            ValueError: If rotation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(rotation) != 3:
            raise ValueError("rotation must be a list of three elements.")
        if not all(isinstance(r, (int, float)) for r in rotation):
            raise ValueError("All rotation elements must be numbers.")
        
        self.rotation = [(angle + rot) % 360 for angle, rot in zip(self.rotation, rotation)]

    def to_dict(self) -> dict:
        """
        Convert the structure to a dictionary representation.

        Returns:
        dict: The dictionary representation of the structure.
        """
        if self._mesh:
            self.geometry={'type': 'mesh',
                            'resource': self.mesh.id,
                            'scale': [self.size[0]/100, self.size[1]/100, self.size[2]/100]}
        node_dict = super().to_dict()
        node_dict['geometry'] = self.geometry
        return node_dict


class Text(Structure):
    def __init__(self, preset, #only objects from class Preset are allowed!
                 name: str = 'Text', #Has to have a name!
                 text = 'Text', # Has to have text!
                 font_size = 10.0, # Okay if int. must be greater 0
                 height = 5.0, # Okay if int. must be greater 0
                 slicing_origin: str = 'scene_bottom',
                 slicing_offset: float = 0.0, 
                 priority: int = 0,
                 expose_individually: bool = False): 
        
        super().__init__(preset = preset, mesh=None, name=name,
                         slicing_origin = slicing_origin,
                         slicing_offset = slicing_offset,
                         priority=priority,
                         expose_individually=expose_individually)
        self.text = text
        self.font_size = font_size
        self.height = height
        
        self._mesh=False
    def to_dict(self) -> dict:
        self.geometry = {'type': 'text',
                         'text': self.text,
                         'font_size': self.font_size,
                         'height' : self.height}
        node_dict = super().to_dict()
        node_dict['geometry'] = self.geometry
        return node_dict
        
    
class Lens(Structure):
    def __init__(self, preset,
                 name: str = 'Lens', #Has to have a name!
                 radius = 100.0, # Okay if int. must be greater 0
                 height = 50.0, # Okay if int. must be greater 0
                 crop_base = False,
                 asymmetric = False,
                 curvature = 0.01, # Okay if int.
                 conic_constant = 0.01, # Okay if int.
                 curvature_y = 0.01, # Okay if int.
                 conic_constant_y = -1.0, # Okay if int.
                 nr_radial_segments = 500, #has to be int!
                 nr_phi_segments = 360, #has to be int!
                 slicing_origin: str = 'scene_bottom',
                 slicing_offset: float = 0.0, 
                 priority: int = 0, 
                 expose_individually: bool = False):
    
        super().__init__(preset = preset, mesh=None, name=name,
                         slicing_origin = slicing_origin,
                         slicing_offset = slicing_offset,
                         priority=priority,
                         expose_individually=expose_individually)
        
        self.name = name
        self.radius = radius
        self.height = height
        self.crop_base = crop_base
        self.asymmetric = asymmetric #if this is False, the lens is considered being radialy symmetric. non-y-values are in this case considered! Passing y-values is allowed but have no effect.
        self.curvature = curvature
        self.conic_constant = conic_constant
        self.curvature_y =  curvature_y
        self.conic_constant_y = conic_constant_y
        
        self.polynomial_type = 'Normalized'
        #Can be either 'Normalized' or 'Standard'. The latter has units um^-(2n+1) where n is index in passed list to polynomial_factors (or polynomial_factors_y if asymmetric). Former has no units. Both can be any number
        self.polynomial_factors = []
        self.polynomial_factors_y = []
        
        self.surface_compensation_factors = [] #has units um^-(2n+1) where n is index in passed list (must contain numbers) to it
        self.surface_compensation_factors_y = [] #has units um^-(2n+1) where n is index in passed list (must contain numbers) to it
        
        
        
        self.nr_radial_segments = nr_radial_segments
        self.nr_phi_segments = nr_phi_segments
        
        self._mesh=False
        
    def polynomial(self, polynomial_type = 'Normalized', polynomial_factors = [0,0,0], polynomial_factors_y = [0,0,0]): #passed lists can have arbitrary length!
        self.polynomial_type = polynomial_type
        self.polynomial_factors = polynomial_factors
        if self.asymmetric:
            self.polynomial_factors_y = polynomial_factors_y
        return self
        
    def surface_compensation(self, surface_compensation_factors = [0,0,0], surface_compensation_factors_y = [0,0,0]):#passed lists can have arbitrary length!
        self.surface_compensation_factors = surface_compensation_factors
        if self.asymmetric:
            self.surface_compensation_factors_y = surface_compensation_factors_y
        return self
        
    def to_dict(self) -> dict:
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
    
    
class CoarseAligner(Node):
    """
    Class: coarse alignment nodes.

    Attributes:
        alignment_anchors (list): List of alignment anchors.
    """
    def __init__(self, name: str = 'Coarse aligner',
                 residual_threshold: float = 10.0 # must be greater 0
                 ):
        """
        Initialize the coarse aligner with a name and a residual threshold.

        Parameters:
            name (str): The name of the coarse aligner node.
            residual_threshold (float): The residual threshold for alignment.
        """
        super().__init__('coarse_alignment', name, residual_threshold=residual_threshold)
        self.alignment_anchors = []
        
    def add_coarse_anchor(self, label: str, position: List[float]):
        """
        Add a single coarse anchor with a label and position.

        Parameters:
            label (str): The label for the anchor.
            position (List[float]): The position [x, y, z] for the anchor.

        Raises:
            ValueError: If position does not contain exactly three elements.
        """
        if len(position) != 3:
            raise ValueError("position must be a list of three elements.")
        self.alignment_anchors.append({
            "label": label,
            "position": position,
        })
        
    def set_coarse_anchors_at(self, labels: List[str], positions: List[List[float]]):
        """
        Create multiple coarse anchors at specified positions.

        Parameters:
            labels (List[str]): List of labels for the anchors.
            positions (List[List[float]]): List of positions for the anchors, each position is [x, y, z].

        Returns:
            self: The instance of the CoarseAligner class.

        Raises:
            ValueError: If the number of labels does not match the number of positions.
        """
        if len(labels) != len(positions):
            raise ValueError("The number of labels must match the number of positions.")
        for label, position in zip(labels, positions):
            self.add_coarse_anchor(label, position)
        return self
        
    def to_dict(self) -> Dict:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            dict: Dictionary representation of the current state of the object.
        """
        node_dict = super().to_dict()
        node_dict['alignment_anchors'] = self.alignment_anchors
        return node_dict

    
class InterfaceAligner(Node):
    """
    Interface aligner class.

    Attributes:
        alignment_anchors (list): Stores the measurement locations (or interface anchors) for interface alignment.
        count (list of int): The number of grid points in [x, y] direction.
        size (list of int): The size of the grid in [width, height].
    
    Methods:
        __init__(self, name='Interface aligner', signal_type='auto', detector_type='auto',
                 measure_tilt=False, area_measurement=False, center_stage=True,
                 action_upon_failure='abort', laser_power=0.5,
                 scan_area_res_factors=[1.0, 1.0], scan_z_sample_distance=0.1,
                 scan_z_sample_count=51):
            Initializes the interface aligner with specified parameters.
        
        set_grid(self, count=[5, 5], size=[200, 200]):
            Sets the grid point count and grid size.
        
        add_interface_anchor(self, label, position, scan_area_size=None):
            Adds an interface anchor with a given label, position, and scan area size.
        
        set_interface_anchors_at(self, labels, positions, scan_area_sizes=None):
            Creates multiple measurement locations at specified positions.

        to_dict(self):
            Converts the current state of the object into a dictionary representation.
    """

    def __init__(self, name: str = 'Interface aligner',
                 signal_type: str = 'auto',
                 detector_type: str = 'auto',
                 measure_tilt: bool = False,
                 area_measurement: bool = False,
                 center_stage: bool = True,
                 action_upon_failure: str = 'abort',
                 laser_power: float = 0.5,
                 scan_area_res_factors: List[float] = [1.0, 1.0],
                 scan_z_sample_distance: float = 0.1,
                 scan_z_sample_count: int = 51):
        """
        Initializes the interface aligner with specified parameters.

        Parameters:
            name (str): Name of the interface aligner.
            signal_type (str): Type of signal, can be 'auto', 'fluorescence', or 'reflection'.
            detector_type (str): Type of detector, can be 'auto', 'confocal', 'camera', or 'camera_legacy'.
            measure_tilt (bool): Whether to measure tilt.
            area_measurement (bool): Whether to measure the area.
            center_stage (bool): Whether to center the stage.
            action_upon_failure (str): Action upon failure, can be 'abort' or 'ignore'.
            laser_power (float): Power of the laser.
            scan_area_res_factors (List[float]): Resolution factors for the scan area.
            scan_z_sample_distance (float): Distance between samples in the z-direction.
            scan_z_sample_count (int): Number of samples in the z-direction.

        Raises:
            ValueError: If scan_z_sample_count is less than 1.
        """
        if scan_z_sample_count < 1:
            raise ValueError("scan_z_sample_count must be at least 1.")
        
        if signal_type not in ['auto', 'fluorescence', 'reflection']:
            raise ValueError('signal_type must be "auto", "fluorescence", or "reflection".')
        
        if detector_type not in ['auto', 'confocal', 'camera', 'camera_legacy']:
            raise ValueError('detector_type must be "auto", "confocal", "camera", or "camera_legacy".')

        super().__init__('interface_alignment', name,
                         action_upon_failure=action_upon_failure,
                         measure_tilt=measure_tilt,
                         area_measurement=area_measurement,
                         properties={'signal_type': signal_type,
                                     'detector_type': detector_type},
                         center_stage=center_stage,
                         laser_power=laser_power,
                         scan_area_res_factors=scan_area_res_factors,
                         scan_z_sample_distance=scan_z_sample_distance,
                         scan_z_sample_count=scan_z_sample_count)
        
        self.alignment_anchors = []
        self.count = [5, 5]
        self.size = [200.0, 200.0]
        self.pattern = 'Origin'
        
    def set_grid(self, count: List[int] = [5, 5], size: List[float] = [200.0, 200.0]):
        """
        Sets the grid point count and grid size.

        Parameters:
            count (List[int]): Number of grid points in [x, y] direction.
            size (List[int]): Size of the grid in [width, height].

        Returns:
            self: The instance of the InterfaceAligner class.
        """
        if len(count) != 2 or len(size) != 2:
            raise ValueError("count and size must each be lists of two elements.")
        if self.pattern != 'Grid':
            self.pattern = 'Grid'
        
        self.count = count
        self.size = size
        return self
        
    def add_interface_anchor(self, label: str, position: List[float], scan_area_size: List[float] = None):
        """
        Adds an interface anchor with a given label, position, and scan area size.
        
        Parameters:
            label (str): The label for the anchor.
            position (List[float]): The position of the anchor [x, y].
            scan_area_size (List[float] or None): The scan area size [width, height]. 
                                                  If None, defaults to [10.0, 10.0]. This parameter is
                                                  only relevant for signal_type = 'reflection' and
                                                  detector_type = 'confocal' with area_measurement = True.

        Raises:
            ValueError: If position does not contain exactly two elements.
        """
        if len(position) != 2:
            raise ValueError("position must be a list of two elements.")
        
        if self.pattern != 'Custom':
            self.pattern = 'Custom'
        
        if scan_area_size is None:
            scan_area_size = [10.0, 10.0]
        
        self.alignment_anchors.append({
            "label": label,
            "position": position,
            "scan_area_size": scan_area_size
        })
        
    def set_interface_anchors_at(self, labels: List[str], positions: List[List[float]], scan_area_sizes: List[List[float]] = None):
        """
        Creates multiple measurement locations at specified positions.
        This method only works if pattern = 'Custom'. Otherwise user input will be overridden.

        Parameters:
            labels (List[str]): List of labels for the measurement locations.
            positions (List[List[float]]): List of positions for the measurement locations, each position is [x, y].
            scan_area_sizes (List[List[float]] or None): List of scan area sizes for the measurement locations, 
                                                         each scan area size is [width, height]. If None, 
                                                         defaults to [10.0, 10.0] for each anchor. This parameter is
                                                         only relevant for signal_type = 'reflection' and
                                                         detector_type = 'confocal' with area_measurement = True.

        Returns:
            self: The instance of the InterfaceAligner class.

        Raises:
            ValueError: If the number of labels does not match the number of positions.
        """
        if len(labels) != len(positions):
            raise ValueError("The number of labels must match the number of positions.")
        
        if scan_area_sizes is None:
            scan_area_sizes = [[10.0, 10.0]] * len(labels)
        
        for label, position, scan_area_size in zip(labels, positions, scan_area_sizes):
            self.add_interface_anchor(label, position, scan_area_size)
        return self
        
    def to_dict(self) -> Dict:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            dict: Dictionary representation of the current state of the object.
        """
        node_dict = super().to_dict()
        node_dict['alignment_anchors'] = self.alignment_anchors
        node_dict['grid_point_count'] = self.count
        node_dict['grid_size'] = self.size
        node_dict['pattern'] = self.pattern
        return node_dict


class FiberAligner(Node):
    def __init__(self, name = 'Fiber aligner',
                 fiber_radius = 63.5,  #number in um. must be grater 0
                 center_stage = True,
                 action_upon_failure = 'abort', #can be 'abort' 'ignore'
                 illumination_name = "process_led_1", 
                 core_signal_lower_threshold = 0.05,
                 core_signal_range = [0.1, 0.9],
                 detection_margin = 6.3500000000000005 #must be number greater 0. unit in um
                 ):
        super().__init__(node_type = 'fiber_core_alignment', name=name,
                       fiber_radius=fiber_radius,
                       center_stage=center_stage,
                       action_upon_failure = action_upon_failure,
                       illumination_name =illumination_name,
                       core_signal_lower_threshold =core_signal_lower_threshold,
                       core_signal_range =core_signal_range,
                       core_position_offset_tolerance =detection_margin)
        
        self.detect_light_direction = False
        self.z_scan_range = [10, 100] # has to be list of two entries that are number. The second entry must be greater than 0 AND greater than the first value! all units um
        self.z_scan_range_sample_count = 1 # has to be greater 0 integer 
        self.z_scan_range_scan_count = 1 # has to be greater 0 integer
        
        
    def measure_tilt(self, z_scan_range=[10, 100], z_scan_range_sample_count = 3, z_scan_range_scan_count = 1):
        self.detect_light_direction = True
        self.z_scan_range = z_scan_range # has to be list of two entries that are number. The second entry must be greater than 0 AND greater than the first value! all units um
        self.z_scan_range_sample_count = z_scan_range_sample_count # has to be greater 0 integer 
        self.z_scan_range_scan_count = z_scan_range_scan_count # has to be greater 0 integer 
        
        return self
    def to_dict(self) -> Dict:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            dict: Dictionary representation of the current state of the object.
        """
        node_dict = super().to_dict()
        node_dict['detect_light_direction'] = self.detect_light_direction
        node_dict['z_scan_range'] = self.z_scan_range
        node_dict['z_scan_range_sample_count'] = self.z_scan_range_sample_count
        node_dict['z_scan_range_scan_count'] = self.z_scan_range_scan_count
        return node_dict


class MarkerAligner(Node):
    """
    Marker aligner class

    Attributes:
        image (Resources): Image object that the marker gets assigned.
        name (str): Name of the marker aligner.
        marker_size (List[float]): Size of markers in micrometers. Marker size must be greater than 0.
        center_stage (bool): Centers stage if true.
        action_upon_failure (str): 'abort' or 'ignore' at failure (not yet implemented!).
        laser_power (float): Laser power in mW.
        scan_area_size (List[float]): Scan area size in micrometers.
        scan_area_res_factors (List[float]): Resolution factors in scanned area.
        detection_margin (float): Additional margin around marker imaging field in micrometers.
        correlation_threshold (float): Correlation threshold below which abort is triggered in percent.
        residual_threshold (float): Residual threshold of marker image.
        max_outliers (int): Maximum amount of markers that are allowed to be outliers.
        orthonormalize (bool): Whether to orthonormalize or not.
        z_scan_sample_count (int): Number of z samples to be taken.
        z_scan_sample_distance (float): Sampling distance in micrometers for z samples to be apart from each other.
        z_scan_sample_mode (str): "correlation" or "intensity" for scan_z_sample_mode.
        measure_z (bool): Whether to measure z or not.
    """

    def __init__(self, image, 
                 name: str = 'Marker aligner',
                 marker_size: List[float] = [0.0, 0.0],
                 center_stage: bool = True,
                 action_upon_failure: str = 'abort',
                 laser_power: float = 0.5,
                 scan_area_size: List[float] = [10.0, 10.0],
                 scan_area_res_factors: List[float] = [2.0, 2.0],
                 detection_margin: float = 5.0,
                 correlation_threshold: float = 60.0,
                 residual_threshold: float = 0.5,
                 max_outliers: int = 0,
                 orthonormalize: bool = True,
                 z_scan_sample_count: int = 1,
                 z_scan_sample_distance: float = 0.5,
                 z_scan_sample_mode: str = 'correlation',
                 measure_z: bool = False):
        """
        Initializes the MarkerAligner with the provided parameters.
        
        Raises:
            ValueError: If marker_size is not greater than 0, if z_scan_sample_count is less than 1,
                        or if z_scan_sample_mode is not "correlation" or "intensity".
        """
        if marker_size[0] <= 0 or marker_size[1] <= 0:
            raise ValueError("marker_size must be greater than 0.")
        if z_scan_sample_count < 1:
            raise ValueError("z_scan_sample_count must be at least 1.")
        if z_scan_sample_mode not in ['correlation', 'intensity']:
            raise ValueError('z_scan_sample_mode must be either "correlation" or "intensity".')
        
        super().__init__('marker_alignment', name,
                         action_upon_failure=action_upon_failure,
                         marker={'image': image.id,
                                 'size': marker_size},
                         center_stage=center_stage,
                         laser_power=laser_power,
                         scan_area_size=scan_area_size,
                         scan_area_res_factors=scan_area_res_factors,
                         detection_margin=detection_margin,
                         correlation_threshold=correlation_threshold,
                         residual_threshold=residual_threshold,
                         max_outliers=max_outliers,
                         orthonormalize=orthonormalize,
                         z_scan_sample_distance=z_scan_sample_distance,
                         z_scan_sample_count=z_scan_sample_count,
                         z_scan_optimization_mode=z_scan_sample_mode,
                         measure_z=measure_z)
        
        self.alignment_anchors = []

    def add_marker(self, label: str, orientation: float, position: List[float]):
        """
        Adds a marker to the alignment anchors.

        Args:
            label (str): The label of the marker.
            orientation (float): The orientation of the marker in degrees.
            position (List[float]): The position of the marker in micrometers.

        Raises:
            ValueError: If position does not contain exactly two elements.
        """
        if len(position) != 2:
            raise ValueError("position must be a list of two elements.")
        self.alignment_anchors.append({
            "label": label,
            "position": position,
            "rotation": orientation
        })
        
    def set_markers_at(self, labels: List[str], orientations: List[float], positions: List[List[float]]):
        """
        Creates multiple markers at specified positions with given orientations.

        Args:
            labels (List[str]): List of labels for the markers.
            orientations (List[float]): List of orientations for the markers in degrees.
            positions (List[List[float]]): List of positions for the markers in micrometers.

        Returns:
            MarkerAligner: The current instance with added markers.

        Raises:
            ValueError: If the lengths of labels, orientations, and positions do not match.
        """
        if len(labels) != len(positions) or len(labels) != len(orientations):
            raise ValueError("The number of labels, positions, and orientations must match.")
        
        for label, orientation, position in zip(labels, orientations, positions):
            self.add_marker(label, orientation, position)
        return self
    
    def to_dict(self) -> Dict:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            dict: Dictionary representation of the current state of the object.
        """
        node_dict = super().to_dict()
        node_dict['alignment_anchors'] = self.alignment_anchors
        return node_dict



class EdgeAligner(Node):
    """
    A class to represent an edge aligner with various attributes and methods for managing edge alignment.

    Attributes:
        alignment_anchors (List[Dict[str, Any]]): List of alignment anchors.
    """
    def __init__(self, 
                 node_type: str = 'edge_alignment',
                 name: str = 'Edge aligner',
                 edge_location: List[float] = [0.0, 0.0],  # in micrometers
                 edge_orientation: float = 0.0,  # in degrees
                 center_stage: bool = True,
                 action_upon_failure: str = 'abort',  # can be 'abort' or 'ignore'
                 laser_power: float = 0.5,  # must be >= 0
                 scan_area_res_factors: List[float] = [1.0, 1.0],  # must be greater than zero
                 scan_z_sample_distance: float = 0.1,
                 scan_z_sample_count: int = 51,  # must be greater than zero
                 outlier_threshold: float = 10.0):  # value must be in percent (0 <= 100)
        """
        Initialize the edge aligner with the specified parameters.

        Parameters:
            node_type (str): Type of the node.
            name (str): Name of the edge aligner.
            edge_location (List[float]): Location of the edge [x, y] in micrometers.
            edge_orientation (float): Orientation of the edge in degrees.
            center_stage (bool): Whether to center the stage.
            action_upon_failure (str): Action upon failure, can be 'abort' or 'ignore'.
            laser_power (float): Power of the laser, must be >= 0.
            scan_area_res_factors (List[float]): Resolution factors for the scan area, must be greater than zero.
            scan_z_sample_distance (float): Distance between samples in the z-direction.
            scan_z_sample_count (int): Number of samples in the z-direction, must be greater than zero.
            outlier_threshold (float): Outlier threshold in percent (0 <= 100).

        Raises:
            ValueError: If scan_z_sample_count is less than 1.
        """
        super().__init__(node_type=node_type,
                         name=name,
                         properties={'xy_position_local_cos': edge_location,
                                     'z_rotation_local_cos': edge_orientation,
                                     'center_stage': center_stage,
                                     'action_upon_failure': action_upon_failure,
                                     'laser_power': laser_power,
                                     'scan_area_res_factors': scan_area_res_factors,
                                     'scan_z_sample_distance': scan_z_sample_distance,
                                     'scan_z_sample_count': scan_z_sample_count,
                                     'outlier_threshold': outlier_threshold})
        
        self.alignment_anchors = []
        
        if scan_z_sample_count < 1:
            raise ValueError("scan_z_sample_count must be at least 1.")
        if scan_z_sample_distance <= 0:
            raise ValueError("scan_z_sample_distance must be greater 0.")
        if laser_power < 0:
            raise ValueError("laser_power must be greater than or equal to 0.")
        if not all(factor > 0 for factor in scan_area_res_factors):
            raise ValueError("All elements in scan_area_res_factors must be greater than 0.")
        if not (0 <= outlier_threshold <= 100):
            raise ValueError("outlier_threshold must be between 0 and 100.")

    def add_measurement(self, label: str, offset: float, scan_area_size: List[float]):
        """
        Add a measurement with a label, offset, and scan area size.

        Parameters:
            label (str): The label for the measurement.
            offset (float): The offset for the measurement.
            scan_area_size (List[float]): The scan area size [width, height].

        Raises:
            ValueError: If scan_area_size does not contain exactly two elements or if X <= 0 or Y < 0.
        """
        if len(scan_area_size) != 2:
            raise ValueError("scan_area_size must be a list of two elements.")
        if scan_area_size[0] <= 0:
            raise ValueError("The width (X) in scan_area_size must be greater than or equal to 0.")
        if scan_area_size[1] < 0:
            raise ValueError("The height (Y) in scan_area_size must be greater than 0.")
        
        self.alignment_anchors.append({
            "label": label,
            "offset": offset,
            "scan_area_size": scan_area_size
        })
    
    def set_measurements_at(self, labels: List[str], offsets: List[float], scan_area_sizes: List[List[float]]):
        """
        Set multiple measurements at specified positions.

        Parameters:
            labels (List[str]): List of labels for the measurements.
            offsets (List[float]): List of offsets for the measurements.
            scan_area_sizes (List[List[float]]): List of scan area sizes for the measurements.

        Returns:
            EdgeAligner: The instance of the EdgeAligner class.

        Raises:
            ValueError: If the lengths of labels, offsets, and scan_area_sizes do not match.
        """
        if len(labels) != len(scan_area_sizes) or len(labels) != len(offsets):
            raise ValueError("The number of labels, offsets, and scan_area_sizes must match.")
        
        for label, offset, scan_area_size in zip(labels, offsets, scan_area_sizes):
            self.add_measurement(label, offset, scan_area_size)
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary representation of the current state of the object.
        """
        node_dict = super().to_dict()
        node_dict['alignment_anchors'] = self.alignment_anchors
        return node_dict



class DoseCompensation(Node):
    """
    A class to represent dose compensation with various attributes and methods for managing dose settings.

    Attributes:
        alignment_anchors (List[Dict[str, Any]]): List of alignment anchors.
    """
    def __init__(self, 
                 name: str = 'Dose compensation 1',
                 edge_location: List[float] = [0.0, 0.0, 0.0],  # in micrometers
                 edge_orientation: float = 0.0,  # in degrees
                 domain_size: List[float] = [200.0, 100.0, 100.0],  # in micrometers, must be > 0
                 gain_limit: float = 2.0):  # must be >= 1
        """
        Initialize the dose compensation with the specified parameters.

        Parameters:
            name (str): Name of the dose compensation.
            edge_location (List[float]): Location of the edge [x, y, z] in micrometers.
            edge_orientation (float): Orientation of the edge in degrees.
            domain_size (List[float]): Size of the domain [width, height, depth] in micrometers, must be > 0.
            gain_limit (float): Gain limit, must be >= 1.

        Raises:
            ValueError: If domain_size contains non-positive values or if gain_limit is less than 1.
        """
        if any(size <= 0 for size in domain_size):
            raise ValueError("All elements in domain_size must be greater than 0.")
        if gain_limit < 1:
            raise ValueError("gain_limit must be greater than or equal to 1.")
        
        super().__init__(node_type='dose_compensation',
                         name=name,
                         position_local_cos=edge_location,
                         z_rotation_local_cos=edge_orientation,
                         size=domain_size,
                         gain_limit=gain_limit)


class Capture(Node):
    """
    A class to represent a capture node with attributes and methods for managing capture settings.

    Attributes:
        capture_type (str): The type of capture (e.g., 'Camera', 'Confocal').
        laser_power (float): The laser power for the capture.
        scan_area_size (List[float]): The size of the scan area [width, height].
        scan_area_ref_factors (List[float]): The resolution factors for the scan area.
    """
    def __init__(self, name: str = 'Capture'):
        """
        Initialize the capture node with the specified parameters.

        Parameters:
            name (str): Name of the capture node.
        """
        super().__init__(node_type='capture', name=name)
        self.capture_type = 'Camera'
        self.laser_power = 0.5
        self.scan_area_size = [100, 100]
        self.scan_area_ref_factors = [1.0, 1.0]
        
    def confocal(self, laser_power: float = 0.5,  # greater or equal to 0
                 scan_area_size: List[float] = [100, 100],  # greater or equal to 0
                 scan_area_ref_factors: List[float] = [1.0, 1.0]):  # greater than 0
        """
        Configure the capture node for confocal capture.

        Parameters:
            laser_power (float): The laser power, must be greater or equal to 0.
            scan_area_size (List[float]): The scan area size [width, height], must be greater or equal to 0.
            scan_area_ref_factors (List[float]): The resolution factors for the scan area, must be greater than 0.

        Returns:
            Capture: The instance of the Capture class.

        Raises:
            ValueError: If any parameter value is not valid.
        """
        if laser_power < 0:
            raise ValueError("laser_power must be greater or equal to 0.")
        if any(size < 0 for size in scan_area_size):
            raise ValueError("All elements in scan_area_size must be greater or equal to 0.")
        if any(factor <= 0 for factor in scan_area_ref_factors):
            raise ValueError("All elements in scan_area_ref_factors must be greater than 0.")
        
        self.laser_power = laser_power
        self.scan_area_size = scan_area_size
        self.scan_area_ref_factors = scan_area_ref_factors
        self.capture_type = 'Confocal'
        
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary representation of the current state of the object.
        """
        node_dict = super().to_dict()
        node_dict['capture_type'] = self.capture_type
        node_dict['laser_power'] = self.laser_power
        node_dict['scan_area_size'] = self.scan_area_size
        node_dict['scan_area_ref_factors'] = self.scan_area_ref_factors
        return node_dict


class StageMove(Node):
    """
    A class to represent a stage move node with a specified stage position.

    Attributes:
        target_position (List[float]): The target position of the stage [x, y, z].
    """
    def __init__(self, 
                 name: str = 'Stage move', 
                 stage_position: List[float] = [0.0, 0.0, 0.0]):
        """
        Initialize the stage move node with the specified parameters.

        Parameters:
            name (str): Name of the stage move node.
            stage_position (List[float]): Target position of the stage [x, y, z].

        Raises:
            ValueError: If stage_position does not contain exactly three elements.
        """
        if len(stage_position) != 3:
            raise ValueError("stage_position must be a list of three elements.")
        
        super().__init__(node_type='stage_move',
                         name=name,
                         target_position=stage_position)


class Wait(Node):
    """
    A class to represent a wait node with a specified wait time.

    Attributes:
        wait_time (float): The wait time in seconds.
    """
    def __init__(self, 
                 name: str = 'Wait', 
                 wait_time: float = 1.0):
        """
        Initialize the wait node with the specified parameters.

        Parameters:
            name (str): Name of the wait node.
            wait_time (float): Wait time in seconds, must be greater than 0.

        Raises:
            ValueError: If wait_time is not greater than 0.
        """
        if wait_time <= 0:
            raise ValueError("wait_time must be greater than 0.")
        
        super().__init__(node_type='wait', 
                         name=name,
                         wait_time=wait_time)