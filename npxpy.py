# -*- coding: utf-8 -*-
"""
npxpy (formerly nanoAPI)
0.0.0-alpha
Created on Thu Feb 29 11:49:17 2024

@author: Caghan Uenlueer
6C 69 66 65 20 69 73 20 74 65 6D 70 6F 72 61 72 79 2E 20 63 6F 64 65 20 69 73 20 65 74 65 72 6E 61 6C

This file is part of npxpy, which is licensed under the GNU Lesser General Public License v3.0.
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

# Node-objects are basically all objects that are represented in the treeview in nanoscribeX's GUI
# properties, geometry and marker have to be passed as dicts! I have implemented it in Node differently for
# marker. However, that is rather arbitrary and probably not neccessary. I can fix that later on but first
# testing in mandatory before proceeding with adjustments for the code.
# UPDATE20240326: Tests were successful!

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
        # Convert node and its unique attributes to dictionary format, including alignment anchors
        # This is useful for insitu-readout but essential for generating the .toml later via save_nodes_to_toml!
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
        super().__init__(node_type = 'project', name = 'Project',
                         objective = objective, resin = resin, substrate = substrate)

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
    
    
    def _save_to_toml(self, presets, resources, nodes, filename="__main__.toml"):
        data = {
            "presets": [preset.to_dict() for preset in presets],
            "resources": [resource.to_dict() for resource in resources],
            "nodes": [node.to_dict() for node in nodes]
            }
        with open(filename, 'w') as toml_file:
            toml.dump(data, toml_file)

    def _create_project_info(self, project_info_json, file_name="project_info.json"):
        with open(file_name, 'w') as file:
            json.dump(project_info_json, file)


    def nano(self, project_name, path='./', output_7z=False):
        """
        Creates a .nano file for the project.

        This method collects the current presets and resources, saves them into a .toml file, and packages them
        along with project information into a .nano file (a .zip archive with a custom extension). Optionally,
        it can output the details of the 7z process.

        Args:
            project_name (str): The name of the project, used as the base name for the .nano file.
            path (str, optional): The directory path where the .nano file will be created. Defaults to './'.
            output_7z (bool, optional): If True, prints the stdout and stderr of the 7z command. Defaults to False.

        Returns:
            subprocess.CompletedProcess: The result of the 7z command if successful.
            subprocess.CalledProcessError: The error object if the 7z command fails.

        Raises:
            FileNotFoundError: If a file to be deleted during cleanup is not found.
            Exception: For other exceptions during the cleanup process.
        """
        print('npxpy: Attempting to create .nano-file...')
        
        # Ensure the path ends with a slash
        if not path.endswith('/'):
            path += '/'
        
        self._save_to_toml(presets = self.presets, resources = self.resources, nodes = [self]+self.all_descendants)
        self._create_project_info(project_info_json = self.project_info)
        
        
        # Define the command
        cmd = ['7z', 'a', '-tzip', '-mx0',
               os.path.join(path, f'{project_name}.nano'),  
               os.path.join(path, '__main__.toml'),       
               os.path.join(path, 'project_info.json'),   
               os.path.join(path, 'resources')]
        
        try:
            # Run the command
            process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            print('npxpy: .nano-file created.')
            
            # Clean up the files
            try:
                os.remove(os.path.join(path, '__main__.toml'))
                os.remove(os.path.join(path, 'project_info.json'))
            except FileNotFoundError as e:
                print(f'File not found: {e.filename}')
            except Exception as e:
                print(f'An error occurred during cleanup: {e}')
            
            # Optional 7z output
            if output_7z:
                output = process.stdout.decode()
                error = process.stderr.decode()
                print(output, error)
            
            return process
        except subprocess.CalledProcessError as e:
            print(f'An error occurred during the creation of the .nano-file: {e.stderr.decode()}')
            return e    

   
    


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
    def __init__(self, name, properties=None, **kwargs):
        self.id = str(uuid.uuid4())
        self.name = name
        self.valid_objectives = kwargs.get('valid_objectives', [name.split("_")[0]])
        self.valid_resins = kwargs.get('valid_resins', [name.split("_")[1]])
        self.valid_substrates = kwargs.get('valid_substrates', ["*"])
        # Initialize properties with a default value if none provided
        # This thing is not like the other gals! it is a sub-structure in the nodes, i.e., [node.properties]
        self.properties = properties if properties is not None else None
        # Handle dynamic attributes specific to the node type
        # Since not all params are the same for every note dynamic handling is paramount!
        # Some of the params are the same though and those are above (position, rotation, etc.)
        self.unique_attributes = {key: value for key, value in kwargs.items() if key not in ['position', 'rotation', 'children']}
        self.alignment_anchors = []
        self.nodeproperties = []
        
    def to_dict(self):
        # Convert node and its unique attributes to dictionary format, including alignment anchors
        # This is useful for insitu-readout but essential for generating the .toml later via save_nodes_to_toml!
        preset_dict = {
            "id": self.id,
            "name": self.name,
            "valid_objectives": self.valid_objectives,
            "valid_resins": self.valid_resins,
            "valid_substrates": self.valid_substrates,
            "properties": self.properties,
            **self.unique_attributes
        }

        return preset_dict

















class Resource:
    def __init__(self, resource_type, name, path, properties=None, **kwargs):
        self.id = str(uuid.uuid4())
        self.type = resource_type
        self.name = name
        self.path = 'resources/'+path
        if resource_type == 'mesh_file':
            self.translation = kwargs.get('translation', [0, 0, 0])
            self.auto_center = kwargs.get('auto_center', False)
            self.rotation = kwargs.get('rotation', [0.0, 0.0, 0.0])
            self.scale = kwargs.get('scale', [1.0, 1.0, 1.0])
            self.enhance_mesh = kwargs.get('enhance_mesh', True)
            self.simplify_mesh = kwargs.get('simplify_mesh', False)
            self.target_ratio = kwargs.get('target_ratio', 100.0)
        # Initialize properties with a default value if none provided
        # This thing is not like the other gals! it is a sub-structure in the nodes, i.e., [node.properties]
        self.properties = properties if properties is not None else None
        # Handle dynamic attributes specific to the node type
        # Since not all params are the same for every note dynamic handling is paramount!
        # Some of the params are the same though and those are above (position, rotation, etc.)
        self.unique_attributes = {key: value for key, value in kwargs.items() if key not in ['position', 'rotation', 'children']}
        self.alignment_anchors = []
        self.nodeproperties = []
        
    def to_dict(self):
        # Convert node and its unique attributes to dictionary format, including alignment anchors
        # This is useful for insitu-readout but essential for generating the .toml later via save_nodes_to_toml!
        if self.type == 'mesh_file':
          resource_dict = {
              "type": self.type,
              "id": self.id,
              "name": self.name,
              "path": self.path,
              "translation": self.translation,
              "auto_center": self.auto_center,
              "rotation": self.rotation,
              "scale": self.scale,
              "enhance_mesh": self.enhance_mesh,
              "simplify_mesh": self.simplify_mesh,
              "target_ratio": self.target_ratio,
              "properties": self.properties,
              **self.unique_attributes
          }
        else:
          resource_dict = {
              "type": self.type,
              "id": self.id,
              "name": self.name,
              "path": self.path,
              "properties": self.properties,
              **self.unique_attributes
          }
        return resource_dict










#misc. functions mainly for use if Node is used for project creation instead of the subclasses

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











