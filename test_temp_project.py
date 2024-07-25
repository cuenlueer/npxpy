# -*- coding: utf-8 -*-
"""
Created on Wed Jul 17 11:50:44 2024

@author: CU
"""

import npxpy as n


project_info_json = {
                      "objective": "25x",
                      "resin": "IP-n162",
                      "substrate": "FuSi",
                    }


edit_presets = {"writing_speed" : 220000.0,
                "writing_power" : 50.0,
                "slicing_spacing" : 0.8,
                "hatching_spacing" : 0.3,
                "hatching_angle" : 0.0,
                "hatching_angle_increment" : 0.0,
                "hatching_offset" : 0.0,
                "hatching_offset_increment" : 0.0,
                "hatching_back_n_forth" : True,
                "mesh_z_offset" : 0.0}

preset = n.Preset(name = "25x_IP-n162_anchorage_FuSi_clone", **edit_presets)


resource_mesh = n.mesh(path = "thisisnotresources/combined_file.stl")
resource_image = n.image(path = "thisisnotresources/markers.png")


project = n.Project(objective = project_info_json['objective'],
                    resin = project_info_json['resin'],
                    substrate = project_info_json['substrate'])

project.load_presets([preset])
project.load_resources(resource_mesh)
project.load_resources(resource_image)




labels = ['anchor 0',
          'anchor 1',
          'anchor 2',
          'anchor 3']

positions = [[-60.0, -528.0, 0.0],
             [-130.0, -528.0, 0.0],
             [-60.0, 20.0, 0.0],
             [-130.0, 20.0, 0.0]]


coarse_aligner1 = n.coarse_aligner(residual_threshold = 8).make_coarse_anchors_at(labels, positions)
scene1 = n.scene(writing_direction_upward=False).position_at([10,10,10],[45,45,45])
group1 = n.group().position_at([-10,-10,-10],[30,30,30])


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

scan_area_sizes = [[11.0,11.0],
                   [12.0,14.0],
                   [13.0,13.0],
                   [12.0,12.0],
                   [13.0,11.0],
                   [14.0,12.0],
                   [11.0,11.0],
                   [11.0,11.0]]

interface_aligner1 = n.interface_aligner(pattern = 'Custom', area_measurement=False,
                                         signal_type = 'reflection', detector_type = 'confocal'
                                         ).make_grid([8,8], [133,133])

interface_aligner2 = n.interface_aligner(name = 'myaligner',
             signal_type = 'reflection', detector_type = 'confocal',
             pattern = 'Custom',
             measure_tilt = True,
             area_measurement = True,
             center_stage = True,
             action_upon_failure = 'ignore',
             laser_power = 0.3,
             scan_area_res_factors = [0.9,0.9],
             scan_z_sample_distance = 0.3,
             scan_z_sample_count = 29).make_interface_anchors_at(labels, positions, scan_area_sizes)

coarse_aligner1.add_child(scene1)
scene1.add_child(group1)
group1.add_child(interface_aligner1)
group1.add_child(interface_aligner2)

structure = n.structure(resource_mesh)

interface_aligner1.add_child(structure)

project.add_child(coarse_aligner1)
project.nano('testmeplease')






