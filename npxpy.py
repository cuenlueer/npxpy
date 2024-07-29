# -*- coding: utf-8 -*-
"""
npxpy (formerly nanoAPI)
0.0.1
Created on Thu Feb 29 11:49:17 2024

@author: Caghan Uenlueer
6C 69 66 65 20 69 73 20 74 65 6D 70 6F 72 61 72 79 2E 20 63 6F 64 65 20 69 73 20 65 74 65 72 6E 61 6C

This file is part of npxpy (formerly nanoAPI), which is licensed under the GNU Lesser General Public License v3.0.
You can find a copy of this license at https://www.gnu.org/licenses/lgpl-3.0.html
"""
import toml
import uuid
import json
import subprocess
from datetime import datetime
import os
import shutil
import hashlib
import copy
from typing import Dict, Any, List, Optional, Tuple
import zipfile
from stl import mesh as stl_mesh


class Node:
    """
    A class to represent a generic node with various attributes and methods for managing node hierarchy.

    Attributes:
        id (str): Unique identifier for the node.
        type (str): Type of the node.
        name (str): Name of the node.
        position (List[float]): Position of the node [x, y, z].
        rotation (List[float]): Rotation of the node [psi, theta, phi].
        children (List[str]): List of children node IDs.
        children_nodes (List[Node]): List of children nodes.
        properties (Any): Properties of the node.
        geometry (Any): Geometry of the node.
        unique_attributes (Dict[str, Any]): Additional dynamic attributes.
        all_descendants (List[Node]): List of all descendant nodes.
    """
    def __init__(self, node_type: str, name: str, properties: Any = None, geometry: Any = None, **kwargs: Any):
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
        self.type = node_type
        self.name = name
        self.position = kwargs.get('position', [0, 0, 0])
        self.rotation = kwargs.get('rotation', [0.0, 0.0, 0.0])
        self.children = kwargs.get('children', [])
        self.children_nodes: List[Node] = []
        self.properties = properties
        self.geometry = geometry
        self.unique_attributes = {key: value for key, value in kwargs.items() if key not in ['position', 'rotation', 'children']}
        self.all_descendants = self._generate_all_descendants()

    def add_child(self, child_node: 'Node'):
        """
        Add a child node to the current node.

        Parameters:
            child_node (Node): The child node to add.
        """
        self.children_nodes.append(child_node)
        self.all_descendants = self._generate_all_descendants()  # Update descendants list

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
        output = f"{indent}{self.name} ({self.type})" if show_type else f"{indent}{self.name}"
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
                filtered_nodes = [child for child in node.children_nodes if child.type == node_type]
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
            if current_node.type == node_type:
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
        self.all_descendants = self._generate_all_descendants()  # Update descendants list

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
            "type": self.type,
            "id": self.id,
            "name": self.name,
            "position": self.position,
            "rotation": self.rotation,
            "children": self.children,
            "properties": self.properties,
            "geometry": self.geometry,
            **self.unique_attributes
        }
        return node_dict





#Keep in mind that you can dynamically allocate any parameter (i.e., unique attribute)
#inside the subclasses of Node (see below) by initializing with **kwargs!:
#def __init__(self, **kwargs):
#    super().__init__(node_type = 'project', name = 'Project', **kwargs)

class Project(Node):
    """
    A class to manage project nodes.

    Attributes:
        presets (list): List of presets for the project.
        resources (list): List of resources for the project.
        project_info (dict): Information about the project including author, objective, resin, substrate, and creation date.
    """
    def __init__(self, objective: str, resin: str, substrate: str):
        """
        Initialize the project with the specified parameters.

        Parameters:
            objective (str): Objective of the project.
            resin (str): Resin used in the project.
            substrate (str): Substrate used in the project.
        """
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

    def load_resources(self, resources: Any):
        """
        Adds resources to the resources list. The input can be either a list of resources
        or a single resource element.

        Args:
            resources (list or any): A list of resources or a single resource element.
        """
        if not isinstance(resources, list):
            resources = [resources]
        self.resources.extend(resources)

    def load_presets(self, presets: Any):
        """
        Adds presets to the presets list. The input can be either a list of presets
        or a single preset element.

        Args:
            presets (list or any): A list of presets or a single preset element.
        """
        if not isinstance(presets, list):
            presets = [presets]
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

    def nano(self, project_name: str, path: str = './', output_7z: bool = False):
        """
        Creates a .nano file for the project.

        This method collects the current presets and resources, saves them into a .toml file, and packages them
        along with project information into a .nano file (a .zip archive with a custom extension).

        Args:
            project_name (str): The name of the project, used as the base name for the .nano file.
            path (str, optional): The directory path where the .nano file will be created. Defaults to './'.
            output_7z (bool, optional): If True, prints the stdout and stderr of the 7z command. Defaults to False.
        """
        print('npxpy: Attempting to create .nano-file...')

        # Ensure the path ends with a slash
        if not path.endswith('/'):
            path += '/'

        # Prepare paths and data
        nano_file_path = os.path.join(path, f'{project_name}.nano')
        toml_data = self._create_toml_data(self.presets, self.resources, [self] + self.all_descendants)
        project_info_data = self._create_project_info(self.project_info)

        with zipfile.ZipFile(nano_file_path, 'w', zipfile.ZIP_DEFLATED) as nano_zip:
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


class CoarseAligner(Node):
    """
    A class to manage coarse alignment nodes.

    Attributes:
        alignment_anchors (list): List of alignment anchors.
    """
    def __init__(self, name: str = 'Coarse aligner', residual_threshold: float = 10.0):
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
        
    def make_coarse_anchors_at(self, labels: List[str], positions: List[List[float]]):
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


class Scene(Node):
    """
    A class to manage scene nodes.

    Attributes:
        position (List[float]): Position of the scene [x, y, z].
        rotation (List[float]): Rotation of the scene [psi, theta, phi].
    """
    def __init__(self, name: str = 'Scene', writing_direction_upward: bool = True):
        """
        Initialize the scene with a name and writing direction.

        Parameters:
            name (str): The name of the scene node.
            writing_direction_upward (bool): Writing direction of the scene.
        """
        super().__init__('scene', name, writing_direction_upward=writing_direction_upward)
        self.position = [0, 0, 0]
        self.rotation = [0.0, 0.0, 0.0]
        
    def position_at(self, position: List[float] = [0, 0, 0], rotation: List[float] = [0.0, 0.0, 0.0]):
        """
        Set the current position and rotation of the scene.

        Parameters:
            position (List[float]): List of position values [x, y, z].
            rotation (List[float]): List of rotation angles [psi, theta, phi].

        Returns:
            self: The instance of the Scene class.
        """
        if len(position) != 3:
            raise ValueError("position must be a list of three elements.")
        if len(rotation) != 3:
            raise ValueError("rotation must be a list of three elements.")
        self.position = position
        self.rotation = rotation
        return self
    
    def translate(self, translation: List[float]):
        """
        Translate the current position by the specified translation.

        Parameters:
            translation (List[float]): List of translation values [dx, dy, dz].

        Raises:
            ValueError: If translation does not contain exactly three elements.
        """
        if len(translation) != 3:
            raise ValueError("translation must be a list of three elements.")
        self.position = [pos + trans for pos, trans in zip(self.position, translation)]

    def rotate(self, rotation: List[float]):
        """
        Rotate the scene by the specified rotation angles.

        Parameters:
            rotation (List[float]): List of rotation angles to apply [d_psi, d_theta, d_phi].

        Raises:
            ValueError: If rotation does not contain exactly three elements.
        """
        if len(rotation) != 3:
            raise ValueError("rotation must be a list of three elements.")
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
    A class to manage group nodes.

    Attributes:
        position (List[float]): Position of the group [x, y, z].
        rotation (List[float]): Rotation of the group [psi, theta, phi].
    """
    def __init__(self, name: str = 'Group'):
        """
        Initialize the group with a name.

        Parameters:
            name (str): The name of the group node.
        """
        super().__init__('group', name)
        self.position = [0, 0, 0]
        self.rotation = [0.0, 0.0, 0.0]
        
    def position_at(self, position: List[float] = [0, 0, 0], rotation: List[float] = [0.0, 0.0, 0.0]):
        """
        Set the current position and rotation of the group.

        Parameters:
            position (List[float]): List of position values [x, y, z].
            rotation (List[float]): List of rotation angles [psi, theta, phi].

        Returns:
            self: The instance of the Group class.
        """
        if len(position) != 3:
            raise ValueError("position must be a list of three elements.")
        if len(rotation) != 3:
            raise ValueError("rotation must be a list of three elements.")
        self.position = position
        self.rotation = rotation
        return self
    
    def translate(self, translation: List[float]):
        """
        Translate the current position by the specified translation.

        Parameters:
            translation (List[float]): List of translation values [dx, dy, dz].

        Raises:
            ValueError: If translation does not contain exactly three elements.
        """
        if len(translation) != 3:
            raise ValueError("translation must be a list of three elements.")
        self.position = [pos + trans for pos, trans in zip(self.position, translation)]

    def rotate(self, rotation: List[float]):
        """
        Rotate the group by the specified rotation angles.

        Parameters:
            rotation (List[float]): List of rotation angles to apply [d_psi, d_theta, d_phi].

        Raises:
            ValueError: If rotation does not contain exactly three elements.
        """
        if len(rotation) != 3:
            raise ValueError("rotation must be a list of three elements.")
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
                 preset, 
                 mesh,
                 project: Optional[Node] = None,
                 auto_load_presets: bool = False,
                 auto_load_resources: bool = False,
                 size: List[int] = [100, 100, 100],
                 name: str = 'Structure',
                 slicing_origin: str = 'scene_bottom',
                 slicing_offset: float = 0.0, 
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
        
        super().__init__('structure', name, preset=preset.id, slicing_origin_reference=slicing_origin,
                         slicing_offset=slicing_offset, priority=priority, expose_individually=expose_individually,
                         geometry={'type': 'mesh', 'resource': mesh.id,
                                   'scale': [size[0]/100, size[1]/100, size[2]/100]})
        self.mesh = mesh
        self.preset = preset
        self.project = project
        self.auto_load_presets = auto_load_presets
        self.auto_load_resources = auto_load_resources
        
        if (auto_load_presets or auto_load_resources) and project:
            self._load_resources()

    def _load_resources(self) -> None:
        """Load presets and resources if the respective flags are set."""
        if self.auto_load_presets:
            self.project.load_presets(self.preset)
            
        if self.auto_load_resources:
            if self.mesh.type != 'mesh_file':
                raise TypeError("Images are supposed to be used for MarkerAligner() class only.")
            self.project.load_resources(self.mesh)

    def position_at(self, position: List[float] = [0, 0, 0], rotation: List[float] = [0.0, 0.0, 0.0]) -> 'Structure':
        """
        Set the current position and rotation of the object.

        Parameters:
        position (List[float]): List of position values [x, y, z].
        rotation (List[float]): List of rotation angles [psi, theta, phi].
        
        Returns:
        Structure: The instance of the Structure class.
        """
        self.position = position
        self.rotation = rotation
        return self

    def translate(self, translation: List[float]) -> None:
        """
        Translate the current position by the specified translation.

        Parameters:
        translation (List[float]): List of translation values [dx, dy, dz].
        """
        self.position = [pos + trans for pos, trans in zip(self.position, translation)]

    def rotate(self, rotation: List[float]) -> None:
        """
        Rotate the current angles by the specified rotation and confine them between 0 and 359 degrees.
        
        Parameters:
        rotation (List[float]): List of rotation angles to apply [d_psi, d_theta, d_phi].
        """
        rotated_angles = [(angle + rot) % 360 for angle, rot in zip(self.rotation, rotation)]
        self.rotation = rotated_angles

    def to_dict(self) -> dict:
        """
        Convert the structure to a dictionary representation.

        Returns:
        dict: The dictionary representation of the structure.
        """
        node_dict = super().to_dict()
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
        
        make_grid(self, count=[5, 5], size=[200, 200]):
            Sets the grid point count and grid size.
        
        add_interface_anchor(self, label, position, scan_area_size=None):
            Adds an interface anchor with a given label, position, and scan area size.
        
        make_interface_anchors_at(self, labels, positions, scan_area_sizes=None):
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
        self.size = [200, 200]
        self.pattern = 'Origin'
        
    def make_grid(self, count: List[int] = [5, 5], size: List[int] = [200, 200]):
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
        
    def make_interface_anchors_at(self, labels: List[str], positions: List[List[float]], scan_area_sizes: List[List[float]] = None):
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
        
    def make_markers_at(self, labels: List[str], orientations: List[float], positions: List[List[float]]):
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





class Preset:
    """
    A class to represent a preset with various parameters related to writing and hatching settings.

    Attributes:
        id (str): Unique identifier for the preset.
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
        grayscale_multilayer_enabled (bool): Whether grayscale multilayer is enabled.
        grayscale_layer_profile_nr_layers (int): Number of layers for grayscale layer profile.
        grayscale_writing_power_minimum (float): Minimum writing power for grayscale.
        grayscale_exponent (float): Grayscale exponent.
        unique_attributes (Dict[str, Any]): Additional dynamic attributes.
    """
    def __init__(self, 
                 name: str = '25x_IP-n162',
                 valid_objectives: str = "25x",
                 valid_resins: str = "IP-n162",
                 valid_substrates: str = "*",
                 writing_speed: float = 250000.0,
                 writing_power: float = 50.0,
                 slicing_spacing: float = 0.8,
                 hatching_spacing: float = 0.3,
                 hatching_angle: float = 0.0,
                 hatching_angle_increment: float = 0.0,
                 hatching_offset: float = 0.0,
                 hatching_offset_increment: float = 0.0,
                 hatching_back_n_forth: bool = True,
                 mesh_z_offset: float = 0.0,
                 grayscale_multilayer_enabled: bool = False,
                 grayscale_layer_profile_nr_layers: int = 6,
                 grayscale_writing_power_minimum: float = 0.0,
                 grayscale_exponent: float = 1.0,
                 **kwargs: Any):
        """
        Initialize a Preset instance with various parameters related to writing and hatching settings.
        
        Parameters:
            name (str): Name of the preset.
            valid_objectives (str): Valid objectives for the preset.
            valid_resins (str): Valid resins for the preset.
            valid_substrates (str): Valid substrates for the preset.
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
            grayscale_multilayer_enabled (bool): Whether grayscale multilayer is enabled.
            grayscale_layer_profile_nr_layers (int): Number of layers for grayscale layer profile.
            grayscale_writing_power_minimum (float): Minimum writing power for grayscale.
            grayscale_exponent (float): Grayscale exponent.
            **kwargs (Any): Additional dynamic attributes.
        """
        self.id = str(uuid.uuid4())
        self.name = name
        
        self.valid_objectives = [valid_objectives]
        self.valid_resins = [valid_resins]
        self.valid_substrates = [valid_substrates]
        
        self.writing_speed = writing_speed
        self.writing_power = writing_power
        self.slicing_spacing = slicing_spacing
        self.hatching_spacing = hatching_spacing
        self.hatching_angle = hatching_angle
        self.hatching_angle_increment = hatching_angle_increment
        self.hatching_offset = hatching_offset
        self.hatching_offset_increment = hatching_offset_increment
        self.hatching_back_n_forth = hatching_back_n_forth
        self.mesh_z_offset = mesh_z_offset
        self.grayscale_multilayer_enabled = grayscale_multilayer_enabled
        self.grayscale_layer_profile_nr_layers = grayscale_layer_profile_nr_layers
        self.grayscale_writing_power_minimum = grayscale_writing_power_minimum
        self.grayscale_exponent = grayscale_exponent
        
        self.unique_attributes = kwargs

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

        # Ensure 'name' is not in the data dictionary to avoid conflicts
        if 'name' in data:
            del data['name']
            
        cls_instance = cls(name=name, **data)
        
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
        preset_dict = {k: v for k, v in self.__dict__.items() if k != 'unique_attributes'}
        preset_dict.update(self.unique_attributes)
        return preset_dict

    def export(self, file_path: str = None) -> None:
        """
        Export the preset to a file that can be loaded by nanoPrintX and/or npxpy.
        
        Parameters:
            file_path (str): The path to the .toml file to be created. If not provided, defaults to the current directory with the preset's name.
        
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
        self.id = str(uuid.uuid4())
        self.type = resource_type
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
            "type": self.type,
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
        super().__init__(resource_type='image_file', name=name, path=path)


class Mesh(Resource):
    """
    A class to represent a mesh resource.

    Attributes:
        original_triangle_count (int): The original number of triangles in the mesh.
    """
    def __init__(self, path: str, name: str = 'mesh', translation: List[float] = [0, 0, 0],
                 auto_center: bool = False, rotation: List[float] = [0.0, 0.0, 0.0],
                 scale: List[float] = [1.0, 1.0, 1.0], enhance_mesh: bool = True,
                 simplify_mesh: bool = False, target_ratio: float = 100.0):
        """
        Initialize the mesh resource with the specified parameters.

        Parameters:
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
        """
        if not (0 <= target_ratio <= 100):
            raise ValueError("target_ratio must be between 0 and 100.")
        
        super().__init__(resource_type='mesh_file', name=name, path=path,
                         translation=translation, auto_center=auto_center,
                         rotation=rotation, scale=scale, enhance_mesh=enhance_mesh,
                         simplify_mesh=simplify_mesh, target_ratio=target_ratio)

        self.original_triangle_count = self._get_triangle_count(path)

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
            print(f"Error reading STL file: {e}")
            return 0

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            dict: Dictionary representation of the current state of the object.
        """
        resource_dict = super().to_dict()
        resource_dict['properties'] = {'original_triangle_count': self.original_triangle_count}
        return resource_dict







#Below starts: misc. functions mainly for use if Node is used for project creation instead of the subclasses.
# In general those can be considered obsolete by most users.

def copy_files_to_resource_directory(source_directory, target_directory="./resources"):
    # Quick breakdown of this function:
    # Skip directories
    # Calculate MD5 hash
    # Create a sub-directory for the hash if it doesn't exist
    # Copy the file to the new directory
    # NOTE: This function is only of interest if you want to adapt to NanoScribe's fail-safe naming convention!
    # NOTE: Sticking to this way of naming/sorting might make things a bit more complicated.
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)
    
    for filename in os.listdir(source_directory):
        file_path = os.path.join(source_directory, filename)
        
        
        if os.path.isdir(file_path):
            continue
        
        
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        
        hash_directory = os.path.join(target_directory, file_hash)
        if not os.path.exists(hash_directory):
            os.makedirs(hash_directory)
        
        
        shutil.copy(file_path, os.path.join(hash_directory, filename))

    

def save_to_toml(presets, resources, nodes, filename="__main__.toml"):
    data = {
        "presets": [preset.to_dict() for preset in presets],
        "resources": [resource.to_dict() for resource in resources],
        "nodes": [node.to_dict() for node in nodes]
        }
    with open(filename, 'w') as toml_file:
        toml.dump(data, toml_file)

def project_info(project_info_json, file_name="project_info.json"):
    with open(file_name, 'w') as file:
        json.dump(project_info_json, file)


def nano_file_gen(project_name, path = './', output_7z = False):
    print('npxpy: Attempting to create .nano-file...')
    #time.sleep(1)
    cmd = ['7z', 'a', '-tzip', '-mx0',
           f'{path}{project_name}.nano',  
           f'{path}__main__.toml',       
           f'{path}project_info.json',   
           f'{path}resources']
    
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print('npxpy: .nano-file created.')
    #This part is just for cleaning up the 'mess'
    #time.sleep(1)
    os.remove('__main__.toml')
    os.remove('project_info.json')
    #optional 7z output if necessary
    output = process.stdout.decode()
    error = process.stderr.decode()
    if output_7z == True:
        print(output, error)
    return process