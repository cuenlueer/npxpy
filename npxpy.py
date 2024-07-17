# -*- coding: utf-8 -*-
"""
npxpy
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

    def add_interface_anchor(self, label, position, scan_area_size):
        self.alignment_anchors.append({
            "label": label,
            "position": position,
            "scan_area_size": scan_area_size
        })
        
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
            node_dict["marker"] = self.marker
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
        self.resources = resources
    
    def load_presets(self, presets = []):
        self.presets = presets
    
    
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
    def __init__(self, name = 'Coarse aligner', residual_threshold = 10.0):
        """
        Initialize the CoarseAligner with a name and a residual threshold.
        
        Parameters:
        name (str): The name of the coarse aligner node.
        residual_threshold (float): The residual threshold for alignment.
        """
        super().__init__('coarse_alignment', name, residual_threshold)
        self.residual_threshold = residual_threshold
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
        self: The instance of the CoarseAligner class.

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
        node_dict['residual_threshold'] = self.residual_threshold
        node_dict['alignment_anchors'] = self.alignment_anchors
        return node_dict



class scene(Node):
    def __init__(self, name = 'Scene', writing_direction_upward = True):
        super().__init__('scene', name)
        self.writing_direction_upward = writing_direction_upward
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
        node_dict['writing_direction_upward'] = self.writing_direction_upward
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











