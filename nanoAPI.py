# -*- coding: utf-8 -*-
"""
nanoAPI
0.0.0-alpha
Created on Thu Feb 29 11:49:17 2024

@author: Caghan Uenlueer
6C 69 66 65 20 69 73 20 74 65 6D 70 6F 72 61 72 79 2E 20 63 6F 64 65 20 69 73 20 65 74 65 72 6E 61 6C

This file is part of nanoAPI, which is licensed under the GNU Lesser General Public License v3.0.
You can find a copy of this license at https://www.gnu.org/licenses/lgpl-3.0.html
"""
import toml
import uuid
import json
import subprocess
import time
import os
import shutil
import hashlib

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
        # Initialize properties with a default value if none provided
        self.properties = properties if properties is not None else None
        self.geometry = geometry if geometry is not None else None
        # Handle dynamic attributes specific to the node type
        self.unique_attributes = {key: value for key, value in kwargs.items() if key not in ['position', 'rotation', 'children']}
        self.alignment_anchors = []
        self.nodeproperties = []
        
        if node_type == "marker_alignment":
            self.marker = marker if marker is not None else None

        
    def add_child(self, child_node):
        self.children.append(child_node.id)


    def add_coarse_anchor(self, label, position):
        self.alignment_anchors.append({
            "label": label,
            "position": position,
        })
    
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
        
    def to_dict(self):
        # Convert node and its unique attributes to dictionary format, including alignment anchors
        # This is useful for insitu-readout but essential for generating the .toml later via save_nodes_to_toml!
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
        if self.alignment_anchors:
            node_dict["alignment_anchors"] = self.alignment_anchors
        if self.type == "marker_alignment":
            node_dict["marker"] = self.marker
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
    print('nanoAPI: Attempting to create .nano-file...')
    time.sleep(1)
    cmd = ['7z', 'a', '-tzip', '-mx0',
           f'{path}{project_name}.nano',  
           f'{path}__main__.toml',       
           f'{path}project_info.json',   
           f'{path}resources']
    
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print('nanoAPI: .nano-file created.')
    #This part is just for cleaning up the 'mess'
    time.sleep(1)
    os.remove('__main__.toml')
    os.remove('project_info.json')
    #optional 7z output if necessary
    output = process.stdout.decode()
    error = process.stderr.decode()
    if output_7z == True:
        print(output, error)
    return process
