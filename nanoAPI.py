# -*- coding: utf-8 -*-
"""
Created on Thu Feb 29 11:49:17 2024

@author: Caghan (work)
life is temporary. code is eternal
"""
import toml
import uuid
import json

# Node-objects are basically all objects that are represented in the treeview in nanoscribeX's GUI
# properties, geometry and marker have to be passed as dicts! I have implemented it in Node differently for
# marker. However, that is rather arbitrary and probably not neccessary. I can fix that later on but first
# testing in mandatory before proceeding with adjustemnts for the code.

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
        self.path = path
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
"""
# Example usage
node = Node(
    node_type="interface_alignment",
    name="Interface aligner 1",
    grid_point_count=[4.0, 4.0],
    grid_size=[200, 200],
    action_upon_failure="abort"
    # Other unique attributes can be added here as needed
)

node.add_alignment_anchor("marker 1", [-130.0, -30.0], [10.0, 10.0])
# Add more alignment anchors as needed

# Convert to dict for serialization (e.g., to TOML)
node_dict = node.to_dict()

# You can then serialize node_dict to a TOML file using a TOML library
"""
