# -*- coding: utf-8 -*-
"""
Created on Sat Dec  7 14:26:54 2024

@author: CU
"""
import npxpy
import os
from shapely.geometry import Polygon, MultiPolygon
from gdshelpers.geometry.chip import Cell
from gdshelpers.parts.text import Text
import numpy as np


def create_marker_pattern(center, size):
    # center: (x, y), ignoring any z component
    x, y = center[0], center[1]
    half_size = size / 2
    square1 = Polygon(
        [
            (x - half_size, y),
            (x, y),
            (x, y + half_size),
            (x - half_size, y + half_size),
        ]
    )
    square2 = Polygon(
        [
            (x, y - half_size),
            (x + half_size, y - half_size),
            (x + half_size, y),
            (x, y),
        ]
    )
    return MultiPolygon([square1, square2])


def create_marker_cell(name, positions):
    cell = Cell(name)
    marker_size = 13
    for pos in positions:
        # Extract only the x, y coordinates (ignore the third value)
        pattern = create_marker_pattern((pos[0], pos[1]), marker_size)
        cell.add_to_layer(1, pattern)
    return cell


#  Initialize the presets and resources that you want to use in this project.
preset = npxpy.Preset.load_single(file_path="25x_IP-n162_cylinders.toml")
#  Load cylinders to sweep and marker.
cylinder_meshes = [
    npxpy.Mesh(file_path=f"meshes/{mesh}", name=f"{mesh}")
    for mesh in sorted(
        os.listdir("meshes"), key=lambda x: int(x.split(".")[0].split("_")[-1])
    )
]
marker = npxpy.Image(file_path="marker.png", name="marker_image")

#  Initialize your project and load your presets and resources into it.
project = npxpy.Project(objective="25x", resin="IP-n162", substrate="FuSi")
project.load_presets(preset)
project.load_resources(marker)
project.load_resources(cylinder_meshes)

#  Initialize GDS cell for markers on chip
gds_cell = Cell("sweep_scene_array")

#  Initialize the coarse aligner.
coarse_aligner_labels = ["anchor 0", "anchor 1", "anchor 2", "anchor 3"]
coarse_aligner_positions = [
    [-100.0, -100.0, 0.0],
    [1900.0, -100.0, 0.0],
    [1900.0, 1900.0, 0.0],
    [-100.0, 1900.0, 0.0],
]

coarse_aligner = npxpy.CoarseAligner(residual_threshold=5)
coarse_aligner.set_coarse_anchors_at(
    labels=coarse_aligner_labels, positions=coarse_aligner_positions
)
project.add_child(coarse_aligner)

# Specify size of four frame markers
frame_marker_size = 25

for pos, label in zip(coarse_aligner_positions, coarse_aligner_labels):
    frame_pattern = create_marker_pattern(pos, frame_marker_size)
    gds_cell_frame_pattern = Cell(label)
    gds_cell_frame_pattern.add_to_layer(1, frame_pattern)
    gds_cell_frame_pattern.add_to_layer(
        1,
        Text(
            origin=tuple(np.array(pos[:-1]) - np.array([0, 25])),
            height=5,
            text=label,
            alignment="center-center",
        ),
    )
    gds_cell.add_cell(gds_cell_frame_pattern)

#  Interface alignment
interface_aligner_labels = [
    "marker 0",
    "marker 1",
    "marker 2",
    "marker 3",
]
interface_aligner_positions = [
    [0.0, 50.0],
    [50.0, 0.0],
    [-50.0, 0.0],
    [0.0, -50.0],
]

interface_aligner = npxpy.InterfaceAligner(name="Interface Aligner")
interface_aligner.set_interface_anchors_at(
    labels=interface_aligner_labels, positions=interface_aligner_positions
)

#  Marker alignment
marker_aligner_labels = [
    "marker 0",
    "marker 1",
    "marker 2",
    "marker 3",
]
marker_aligner_orientations = [0.0, 0.0, 0.0, 0.0]

marker_aligner_positions = [
    [-50.0, -50.0, 0.0],
    [-50.0, 50.0, 0.0],
    [50.0, 50.0, 0.0],
    [50.0, -50.0, 0.0],
]

marker_aligner = npxpy.MarkerAligner(
    name="Marker Aligner", image=marker, marker_size=[13, 13]
)
marker_aligner.set_markers_at(
    labels=marker_aligner_labels,
    orientations=marker_aligner_orientations,
    positions=marker_aligner_positions,
)

#  Initializing printing scene
# Arrange hierarchy of sweep-scene as a dummy to fill with the cylinders
sweep_scene = npxpy.Scene(name="scene_0", writing_direction_upward=True)
sweep_scene.append_node(interface_aligner)
sweep_scene.append_node(marker_aligner)

# Arrange amount (10x10) of scenes for structures with 200um pitch in x and y
count_x = 10
pitch_x = 200
count_y = 10
pitch_y = 200

sweep_scenes_positions = [
    [x, y, 0]
    for y in range(0, count_y * pitch_y, pitch_y)
    for x in range(0, count_x * pitch_x, pitch_x)
]

# Adding text labels indicating cylinder parameters below respective cylinder
text_labels = [
    f"r={r}\nh={h}" for r in range(5, 55, 5) for h in range(10, 110, 10)
]

sweep_scenes_list = [
    sweep_scene.deepcopy_node().position_at(position=pos, rotation=[0, 0, 0])
    for pos in sweep_scenes_positions
]

# Initialize structures with desired preset and cylinders defined above

for cylinder, sweep_scene, text in zip(
    cylinder_meshes, sweep_scenes_list, text_labels
):
    cylinder_structure = npxpy.Structure(
        name=cylinder.name, preset=preset, mesh=cylinder
    )
    sweep_scene.append_node(cylinder_structure)

    text_label = npxpy.Text(
        position=cylinder_structure.position,
        text=f"{text}\n{cylinder_structure.name}",
        preset=preset,
    )
    text_label.translate([0, -75, 0])
    marker_aligner_in_scene = sweep_scene.grab_all_nodes_bfs(
        "marker_alignment"
    )[0]
    marker_aligner_in_scene.add_child(text_label)
    coarse_aligner.add_child(sweep_scene)

    gds_marker_cell = create_marker_cell(
        cylinder_structure.name, marker_aligner_positions
    )
    gds_cell.add_cell(gds_marker_cell, origin=tuple(sweep_scene.position[:-1]))

#  Export your project to a .nano-file
project.nano(project_name="cylinder_params_sweep")
# Save cell(s) to GDS
gds_cell.save("cylinder_params_sweep.gds")
