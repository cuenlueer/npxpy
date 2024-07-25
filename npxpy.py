# -*- coding: utf-8 -*-
"""
npxpy (formerly nanoAPI)
0.0.0-alpha
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
from typing import Dict, Any, List
import zipfile
from stl import mesh as stl_mesh

class Node:
    def __init__(self, node_type, name, marker=None, properties=None, geometry=None, **kwargs):
        self.id = str(uuid.uuid4())
        self.type = node_type
        self.name = name
        self.position = kwargs.get('position', [0, 0, 0])
        self.rotation = kwargs.get('rotation', [0.0, 0.0, 0.0])
        self.children = kwargs.get('children', [])
        self.children_nodes = []
        # Initialize properties with a default value if none provided
        self.properties = properties if properties is not None else None
        self.geometry = geometry if geometry is not None else None
        # Handle dynamic attributes specific to the node type
        self.unique_attributes = {key: value for key, value in kwargs.items() if key not in ['position', 'rotation', 'children']}
        self.nodeproperties = [] #<------- Marked for demolishing
        
        self.all_descendants = self._generate_all_descendants()
        
        #--------demoliton zoneBEGIN
        if node_type == "marker_alignment":
            self.marker = marker if marker is not None else None
        #--------demoliton zoneEND
        
    def add_child(self, child_node):
        self.children_nodes.append(child_node)
        self.all_descendants = self._generate_all_descendants()  # Update descendants list. Important for .nano-export in Project(Node).
        
        
    #--------demoliton zoneBEGIN

        
    def add_marker_anchor(self, label, position, orientation):
        self.alignment_anchors.append({
            "label": label,
            "position": position,
            "rotation": orientation
        })
    #--------demoliton zoneEND
    
    
    def tree(self, level=0, show_type=True, show_id=False):
        indent = "  " * level
        if show_type == True:
            output = f"{indent}{self.name} ({self.type})"
        else:
            output = f"{indent}{self.name}"
            
        if show_id == True:
            output = output + f" (ID: {self.id})"

        print(output)
        for child in self.children_nodes:
            child.tree(level + 1, show_type, show_id)
    
    
    def deepcopy_node(self, copy_children=True):
        if copy_children:
            copied_node = copy.deepcopy(self)
            self._reset_ids(copied_node)
        else:
            copied_node = copy.copy(self)
            copied_node.id = str(uuid.uuid4())
            copied_node.children_nodes = []
        return copied_node
    
    
    def _reset_ids(self, node):
        node.id = str(uuid.uuid4())
        for child in node.children_nodes:
            self._reset_ids(child)

    
    def grab_nodes(self, node_types_with_indices):
        current_level_nodes = [self]
        for node_type, index in node_types_with_indices:
            next_level_nodes = []
            for node in current_level_nodes:
                filtered_nodes = [child for child in node.children_nodes if child.type == node_type]
                if len(filtered_nodes) > index:
                    next_level_nodes.append(filtered_nodes[index])
            current_level_nodes = next_level_nodes
        return current_level_nodes[0]


    def _generate_all_descendants(self):
        descendants = []
        nodes_to_check = [self]
        while nodes_to_check:
            current_node = nodes_to_check.pop()
            descendants.extend(current_node.children_nodes)
            nodes_to_check.extend(current_node.children_nodes)
        return descendants


    def grab_all_nodes_bfs(self, node_type):
        result = []
        nodes_to_check = [self]
        while nodes_to_check:
            current_node = nodes_to_check.pop(0)  # Dequeue from the front
            if current_node.type == node_type:
                result.append(current_node)
            nodes_to_check.extend(current_node.children_nodes)  # Enqueue children
        return result


        
    def to_dict(self):
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

        if self.type == "marker_alignment":
            node_dict["marker"] = self.marker   #<------- Marked for demolishing
        return node_dict





#Keep in mind that you can dynamically allocate any parameter (i.e., unique attribute)
#inside the subclasses of Node (see below) by initializing with **kwargs!:
#def __init__(self, **kwargs):
#    super().__init__(node_type = 'project', name = 'Project', **kwargs)

class Project(Node):
    def __init__(self, objective, resin, substrate):
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

    def load_resources(self, resources):
        """
        Adds resources to the resources list. The input can be either a list of resources
        or a single resource element.

        Args:
            resources (list or any): A list of resources or a single resource element.
        """
        if not isinstance(resources, list):
            resources = [resources]
        self.resources.extend(resources)

    def load_presets(self, presets):
        """
        Adds presets to the presets list. The input can be either a list of presets
        or a single preset element.

        Args:
            presets (list or any): A list of presets or a single preset element.
        """
        if not isinstance(presets, list):
            presets = [presets]
        self.presets.extend(presets)

    def _create_toml_data(self, presets, resources, nodes):
        data = {
            "presets": [preset.to_dict() for preset in presets],
            "resources": [resource.to_dict() for resource in resources],
            "nodes": [node.to_dict() for node in nodes]
        }
        return toml.dumps(data)

    def _create_project_info(self, project_info_json):
        return json.dumps(project_info_json, indent=4)

    def _add_file_to_zip(self, zip_file, file_path, arcname):
        with open(file_path, 'rb') as f:
            zip_file.writestr(arcname, f.read())

    def nano(self, project_name, path='./', output_7z=False):
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

   
    


class coarse_aligner(Node):
    def __init__(self, name = 'Coarse aligner',
                 residual_threshold = 10.0):
        """
        Initialize the coarse aligner with a name and a residual threshold.
        
        Parameters:
        name (str): The name of the coarse aligner node.
        residual_threshold (float): The residual threshold for alignment.
        """
        super().__init__('coarse_alignment', name, residual_threshold = residual_threshold )
        self.alignment_anchors = []
        
    def add_coarse_anchor(self, label, position):
        """
        Add a single coarse anchor with a label and position.
        
        Parameters:
        label (str): The label for the anchor.
        position (list of float): The position [x, y, z] for the anchor.
        """        
        self.alignment_anchors.append({
            "label": label,
            "position": position,
        })
        
    def make_coarse_anchors_at(self, labels, positions):
        """
        Create multiple coarse anchors at specified positions.

        Parameters:
        labels (list of str): List of labels for the anchors.
        positions (list of list of float): List of positions for the anchors, each position is [x, y, z].

        Returns:
        self: The instance of the coarse_aligner class.

        Raises:
        ValueError: If the number of labels does not match the number of positions.
        """
        if len(labels) != len(positions):
            raise ValueError("The number of labels must match the number of positions.")
        for label, position in zip(labels, positions):
            self.add_coarse_anchor(label, position)
        return self
        
    def to_dict(self):
        node_dict = super().to_dict()
        node_dict['alignment_anchors'] = self.alignment_anchors
        return node_dict




class scene(Node):
    def __init__(self, name = 'Scene', writing_direction_upward = True):
        super().__init__('scene', name, 
                         writing_direction_upward=writing_direction_upward)
    def position_at(self, position = [0,0,0], rotation = [0.0, 0.0, 0.0]):
        """
        Set the current position and rotation of the scene.

        Parameters:
        position (list of float): List of position values [x, y, z].
        rotation (list of float): List of rotation angles [psi, theta, phi].
        
        Returns:
        self: The instance of the scene class.
        """
        self.position = position
        self.rotation = rotation
        return self
    
    
    def translate(self, translation):
        """
        Translate the current position by the specified translation.

        Parameters:
        translation (list of float): List of translation values [dx, dy, dz].
        """
        self.position = [pos + trans for pos, trans in zip(self.position, translation)]


    def rotate(self, rotation):
        """
        Rotate the given angles by the specified rotation and confine them between 0 and 359 degrees.
        
        Parameters:
        angles (list of float): List of angles [psi, theta, phi].
        rotation (list of float): List of rotation angles to apply [d_psi, d_theta, d_phi].
        
        Returns:
        list of float: List of rotated and confined angles.
        """
        rotated_angles = [(angle + rot) % 360 for angle, rot in zip(self.rotation, rotation)]
        self.rotation = rotated_angles
        
    def to_dict(self):
        node_dict = super().to_dict()
        return node_dict
    
    


class group(Node):
    def __init__(self, name = 'Group'):
        super().__init__('group', name)
        
    def position_at(self, position = [0,0,0], rotation = [0.0, 0.0, 0.0]):
        """
        Set the current position and rotation of the group.

        Parameters:
        position (list of float): List of position values [x, y, z].
        rotation (list of float): List of rotation angles [psi, theta, phi].
        
        Returns:
        self: The instance of the scene class.
        """
        self.position = position
        self.rotation = rotation
        return self
    
    
    def translate(self, translation):
        """
        Translate the current position by the specified translation.

        Parameters:
        translation (list of float): List of translation values [dx, dy, dz].
        """
        self.position = [pos + trans for pos, trans in zip(self.position, translation)]


    def rotate(self, rotation):
        """
        Rotate the given angles by the specified rotation and confine them between 0 and 359 degrees.
        
        Parameters:
        angles (list of float): List of angles [psi, theta, phi].
        rotation (list of float): List of rotation angles to apply [d_psi, d_theta, d_phi].
        
        Returns:
        list of float: List of rotated and confined angles.
        """
        rotated_angles = [(angle + rot) % 360 for angle, rot in zip(self.rotation, rotation)]
        self.rotation = rotated_angles
        
# - method for a routine that automatically adds used meshes (resources in general) to a
#   dedicated target_project without the need to allocating them as resource_objects manually.
#   One should be able to turn it on and off. Implement this idealy as a classmethod.
class structure(Node):
    def __init__(self, preset, mesh,
                 size = [100, 100, 100],
                 name = 'Structure',
                 slicing_origin = 'scene_bottom',
                 slicing_offset = 0.0,
                 priority = 0,
                 expose_individually = False,
                 ):
        super().__init__('structure', name, 
                         preset=preset.id,
                         slicing_origin_reference=slicing_origin,
                         slicing_offset=slicing_offset,
                         priority=priority,
                         expose_individually=expose_individually,
                         geometry={'type':'mesh',
                                   'resource' : mesh.id,
                                   'scale' : [size[0]/100,size[1]/100,size[2]/100]})
        
    def position_at(self, position = [0,0,0], rotation = [0.0, 0.0, 0.0]):
        """
        Set the current position and rotation of the object.

        Parameters:
        position (list of float): List of position values [x, y, z].
        rotation (list of float): List of rotation angles [psi, theta, phi].
        
        Returns:
        self: The instance of the structure class.
        """
        self.position = position
        self.rotation = rotation
        return self
    
    
    def translate(self, translation):
        """
        Translate the current position by the specified translation.

        Parameters:
        translation (list of float): List of translation values [dx, dy, dz].
        """
        self.position = [pos + trans for pos, trans in zip(self.position, translation)]


    def rotate(self, rotation):
        """
        Rotate the given angles by the specified rotation and confine them between 0 and 359 degrees.
        
        Parameters:
        angles (list of float): List of angles [psi, theta, phi].
        rotation (list of float): List of rotation angles to apply [d_psi, d_theta, d_phi].
        
        Returns:
        list of float: List of rotated and confined angles.
        """
        rotated_angles = [(angle + rot) % 360 for angle, rot in zip(self.rotation, rotation)]
        self.rotation = rotated_angles
        
    def to_dict(self):
        node_dict = super().to_dict()
        return node_dict
    
    
    
#Todo: make some classmethods here to make...
class interface_aligner(Node):
    """
    Interface aligner class.

    Attributes:
        alignment_anchors (list): Stores the measurement locations (or interface anchors) for interface alignment.
        count (list of int): The number of grid points in [x, y] direction.
        size (list of int): The size of the grid in [width, height].
    
    Methods:
        __init__(self, name='Interface aligner', signal_type='auto', detector_type='auto',
                 pattern='Origin', measure_tilt=False, area_measurement=False,
                 center_stage=True, action_upon_failure='abort', laser_power=0.5,
                 scan_area_res_factors=[1.0,1.0], scan_z_sample_distance=0.1,
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
    def __init__(self, name='Interface aligner', signal_type='auto', detector_type='auto',
                 pattern='Origin', measure_tilt=False, area_measurement=False,
                 center_stage=True, action_upon_failure='abort', laser_power=0.5,
                 scan_area_res_factors=[1.0,1.0], scan_z_sample_distance=0.1,
                 scan_z_sample_count=51):

        """
        Initializes the interface aligner with specified parameters.

        Parameters:
            name (str): Name of the interface aligner.
            signal_type (str): Type of signal, can be 'auto', 'fluorescence', or 'reflection'.
            detector_type (str): Type of detector, can be 'auto', 'confocal', 'camera', or 'camera_legacy'.
            pattern (str): Pattern for alignment, can be 'Origin', 'Grid', or 'Custom'.
            measure_tilt (bool): Whether to measure tilt.
            area_measurement (bool): Whether to measure the area.
            center_stage (bool): Whether to center the stage.
            action_upon_failure (str): Action upon failure, can be 'abort' or 'ignore'.
            laser_power (float): Power of the laser.
            scan_area_res_factors (list of float): Resolution factors for the scan area.
            scan_z_sample_distance (float): Distance between samples in the z-direction.
            scan_z_sample_count (int): Number of samples in the z-direction.
        """
        
        super().__init__('interface_alignment', name,
                         action_upon_failure=action_upon_failure,
                         pattern=pattern,
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
        
    def make_grid(self, count=[5, 5], size=[200, 200]):
        """
        Sets the grid point count and grid size.

        Parameters:
            count (list of int): Number of grid points in [x, y] direction.
            size (list of int): Size of the grid in [width, height].

        Returns:
            self: The instance of the interface_aligner class.
        """
        self.count = count
        self.size = size
        return self
        
    def add_interface_anchor(self, label, position, scan_area_size=None):
        """
        Adds an interface anchor with a given label, position, and scan area size.
        This method only makes sense if pattern = 'Custom'. Otherwise it will be ignored.
        
        Parameters:
            label (str): The label for the anchor.
            position (list of float): The position of the anchor [x, y].
            scan_area_size (list of float or None): The scan area size [width, height]. 
                                                    If None, defaults to [10.0, 10.0]. This parameter is
                                                    only relevant for signal_type = 'reflection' and
                                                    detector_type = 'confocal' with area_measurement = True.
        """
        if scan_area_size is None:
            scan_area_size = [10.0, 10.0]
        
        self.alignment_anchors.append({
            "label": label,
            "position": position,
            "scan_area_size": scan_area_size
        })
        
    def make_interface_anchors_at(self, labels, positions, scan_area_sizes=None):
        """
        Creates multiple measurement locations at specified positions.
        This method only makes sense if pattern = 'Custom'. Otherwise it will be ignored.

        Parameters:
            labels (list of str): List of labels for the measurement locations.
            positions (list of list of float): List of positions for the measurement locations, each position is [x, y].
            scan_area_sizes (list of list of float or None): List of scan area sizes for the measurement locations, 
                                                             each scan area size is [width, height]. If None, 
                                                             defaults to [10.0, 10.0] for each anchor. This parameter is
                                                             only relevant for signal_type = 'reflection' and
                                                             detector_type = 'confocal' with area_measurement = True.

        Returns:
            self: The instance of the interface_aligner class.

        Raises:
            ValueError: If the number of labels does not match the number of positions.
        """
        if len(labels) != len(positions):
            raise ValueError("The number of labels must match the number of positions.")

        if scan_area_sizes is None:
            scan_area_sizes = [None] * len(labels)

        for label, position, scan_area_size in zip(labels, positions, scan_area_sizes):
            self.add_interface_anchor(label, position, scan_area_size)
        return self
        
    def to_dict(self):
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            dict: Dictionary representation of the current state of the object.
        """
        node_dict = super().to_dict()
        node_dict['alignment_anchors'] = self.alignment_anchors
        node_dict['grid_point_count'] = self.count
        node_dict['grid_size'] = self.size
        return node_dict








class Preset:
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

        Returns:
            Preset: The loaded preset instance.
        """
        with open(file_path, 'r') as toml_file:
            data = toml.load(toml_file)

        # Extract the file name without the extension
        name = os.path.splitext(os.path.basename(file_path))[0]

        # Ensure 'name' is not in the data dictionary to avoid conflicts
        if 'name' in data:
            del data['name']
            
        cls_instance = cls(name=name, **data)
        
        if fresh_id == False:
            cls_instance.id = data['id']
        
        return cls_instance

    @classmethod
    def load_multiple(cls, directory_path: str, print_names: bool = False, fresh_id: bool = True) -> List['Preset']:
        """
        Load multiple presets from a directory containing .toml files.

        Parameters:
            directory_path (str): The path to the directory containing .toml files.
            print_names (bool): If True, print the names of the files in the order they are loaded.

        Returns:
            List[Preset]: A list of loaded preset instances.
        """
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
        # Create the base dictionary from __dict__, excluding unique_attributes
        preset_dict = {k: v for k, v in self.__dict__.items() if k != 'unique_attributes'}
        
        # Merge unique_attributes into preset_dict
        preset_dict.update(self.unique_attributes)
        
        return preset_dict

    def export(self, file_path: str = None) -> None:
        """
        Export the preset to a file that can be loaded by nanoPrintX and/or npxpy.
        
        Parameters:
            file_path (str): The path to the .toml file to be created. If not provided, defaults to the current directory with the preset's name.
        """
        if file_path is None:
            file_path = f"{self.name}.toml"
        elif not file_path.endswith('.toml'):
            file_path += '.toml'
        
        data = self.to_dict()
        
        # Write the data to a .toml file
        with open(file_path, 'w') as toml_file:
            toml.dump(data, toml_file)
















class Resource:
    def __init__(self, resource_type, name, path, **kwargs):
        self.id = str(uuid.uuid4())
        self.type = resource_type
        self.name = name
        self.path = self.generate_path(path)
        self.unique_attributes = kwargs
        
        self.fetch_from = path
        
    def generate_path(self, file_path):
        # Compute MD5 hash of the file content
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as file:
            for chunk in iter(lambda: file.read(4096), b""):
                md5_hash.update(chunk)
        
        file_hash = md5_hash.hexdigest()
        # Construct the new path
        target_path = f'resources/{file_hash}/{file_path.split("/")[-1]}'
        return target_path
        
    def to_dict(self):
        resource_dict = {
            "type": self.type,
            "id": self.id,
            "name": self.name,
            "path": self.path,
            **self.unique_attributes
        }
        return resource_dict
    
    
class image(Resource):
    def __init__(self, path,
                 name='image'):
        super().__init__(resource_type = 'image_file',
                         name=name,
                         path=path)


class mesh(Resource):
    def __init__(self, path,
                 name='mesh',
                 translation=[0, 0, 0],
                 auto_center=False,
                 rotation=[0.0, 0.0, 0.0],
                 scale=[1.0, 1.0, 1.0],
                 enhance_mesh=True,
                 simplify_mesh=False,
                 target_ratio=100.0):
        super().__init__(resource_type='mesh_file',
                         name=name,
                         path=path,
                         translation=translation,
                         auto_center=auto_center,
                         rotation=rotation,
                         scale=scale,
                         enhance_mesh=enhance_mesh,
                         simplify_mesh=simplify_mesh,
                         target_ratio=target_ratio)

        
        self.original_triangle_count = self._get_triangle_count(path)

    def _get_triangle_count(self, path):
        try:
            mesh_data = stl_mesh.Mesh.from_file(path)
            return len(mesh_data.vectors)
        except Exception as e:
            print(f"Error reading STL file: {e}")
            return 0

    def to_dict(self):
        resource_dict = super().to_dict()
        resource_dict['properties'] = {'original_triangle_count': self.original_triangle_count}
        return resource_dict







#misc. functions mainly for use if Node is used for project creation instead of the subclasses.
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