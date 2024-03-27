# -*- coding: utf-8 -*-
"""
Created on Thu Feb 29 12:20:59 2024

@author: Caghan (work)
"""

import nanoAPI as n
from datetime import datetime
import os

project_info_json = {
                      "author": "Caghan (work)",
                      "objective": "25x",
                      "resist": "IP-n162",
                      "substrate": "FuSi",
                      "creation_date": datetime.now().replace(microsecond=0).isoformat()
                    }


#Presets/Resources_________________________________________________________

edit_presets = {"writing_speed" : 250000.0,
                "writing_power" : 50.0,
                "slicing_spacing" : 0.8,
                "hatching_spacing" : 0.3,
                "hatching_angle" : 0.0,
                "hatching_angle_increment" : 0.0,
                "hatching_offset" : 0.0,
                "hatching_offset_increment" : 0.0,
                "hatching_back_n_forth" : True,
                "mesh_z_offset" : 0.0}

preset = n.Preset("25x_IP-n162_anchorage_FuSi_clone", **edit_presets)




resource_mesh = n.Resource(resource_type = "mesh_file",
                           name = "structure",
                           path = "5416ba193f0bacf1e37be08d5c249914/combined_file.stl")

resource_image = n.Resource(resource_type = "image_file",
                            name = "markers_1",
                            path = "78eab7abd2cd201630ba30ed5a7ef4fc/markers.png")





#Tree view_________________________________________________________

project = n.Node(node_type='project',
                 name = 'Project 1',
                 objective = project_info_json['objective'],
                 resin = project_info_json['resist'],
                 substrate = project_info_json['substrate'])

#-----------------------------------------------

coarse_aligner1 = n.Node(node_type = 'coarse_alignment',
                        name = "Coarse aligner 1",
                        residual_threshold = 10.0,
                        orthonormalize = True # here-to-stay value
                        ) 
labels = ['anchor 0',
          'anchor 1',
          'anchor 2',
          'anchor 3']

positions = [[-60.0, -528.0, 0.0],
             [-130.0, -528.0, 0.0],
             [-60.0, 20.0, 0.0],
             [-130.0, 20.0, 0.0]]

for label, position in zip(labels,positions):
    coarse_aligner1.add_coarse_anchor(label, position)
    
#-----------------------------------------------


scene1 = n.Node('scene',
                "Scene 1",
                writing_direction_upward = True)
#-----------------------------------------------
group1 = n.Node('group',
                'Group 1')
#-----------------------------------------------
array1 = n.Node('array',
                'Array 1')
#-----------------------------------------------



interface_aligner1 = n.Node(node_type = 'interface_alignment',
                            name = 'Interface aligner 1',
                            action_upon_failure = "abort",
                            #scan_area_res_factors = [1.0,1.0], # here-to-stay value
                            #laser_power = 0.5, #hts value
                            #scan_area_size = [10.0,10.0], #hts value
                            #scan_z_sample_distance = 0.1, #hts value
                            #scan_z_sample_count = 51, #hts value
                            properties = {"signal_type": "fluorescence"},
                            pattern = "Custom",
                            #area_measurement = False, # here-to-stay
                            measure_tilt = True) 

labels = ['marker 0',
          'marker 1',
          'marker 2',
          'marker 3',
          'marker 4',
          'marker 5',
          'marker 6',
          'marker 7']

positions = [[-130.0, -30.0],
             [-130.0, 30.0],
             [-60.0, -30.0],
             [-60.0, 30.0],
             [-130.0, -60.0],
             [-130.0, 60.0],
             [-60.0, -60.0],
             [-60.0, 60.0]]

scan_area_sizes = [[10.0,10.0],
                   [10.0,10.0],
                   [10.0,10.0],
                   [10.0,10.0],
                   [10.0,10.0],
                   [10.0,10.0],
                   [10.0,10.0],
                   [10.0,10.0]]

for label, position, scan_area_size in zip(labels,positions,scan_area_sizes):
    interface_aligner1.add_interface_anchor(label, position,scan_area_size)

#-----------------------------------------------

marker_aligner_defualt = {
    "scan_area_res_factors" : [2,2],
    "laser_power" : 0.5,
    "detection_margin" : 5.0,
    "correlation_threshold" : 60.0,
    "residual_threshold" : 0.5,
    "max_outliers" : 0,
    "orthonormalize" : True,
    "z_scan_sample_count" : 1,
    "z_scan_sample_distance" : 0.5,
    "z_scan_optimization_mode" : "correlation",
    "measure_z" : False,
    }

marker_dict = {
    "image": resource_image.id,
    "size": [5.0,5.0]
    }

marker_aligner1 = n.Node(node_type = "marker_alignment",
                         name = "Marker aligner 1",
                         marker = marker_dict,
                         **marker_aligner_defualt)

labels = ['marker 0',
          'marker 1',
          'marker 2',
          'marker 3']

positions = [[-60.0, -20.0, 0.0],
             [-130.0, -20.0, 0.0],
             [-60.0, 20.0, 0.0],
             [-130.0, 20.0, 0.0]]

rotations = [0.0,
             0.0,
             0.0,
             0.0]

for label, position, rotation in zip(labels,positions,rotations):
    marker_aligner1.add_marker_anchor(label, position, rotation)

structure1 = n.Node(node_type = "structure",
                    name = "test",
                    preset = preset.id,
                    slicing_origin_reference = "scene_bottom",
                    slicing_offset = 0.0,
                    priority = 0,
                    expose_individually = False,
                    geometry = {"type" : "mesh",
                                "resource" : resource_mesh.id,
                                "scale" : [1.0,1.0,1.0]})













# assign all node objects as parents and children


project.add_child(coarse_aligner1)
coarse_aligner1.add_child(scene1)
scene1.add_child(group1)
group1.add_child(array1)
array1.add_child(interface_aligner1)
interface_aligner1.add_child(marker_aligner1)
marker_aligner1.add_child(structure1)





n.save_to_toml([preset],
                    [resource_mesh,
                    resource_image],
                        [project,
                        coarse_aligner1,
                        scene1, group1,
                        array1,
                        interface_aligner1,
                        marker_aligner1,
                        structure1])

n.project_info(project_info_json)

n.nano_file_gen('project_example')