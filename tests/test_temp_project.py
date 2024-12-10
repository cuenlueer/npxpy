# -*- coding: utf-8 -*-
"""
Created on Wed Jul 17 11:50:44 2024

@author: CU
"""

import npxpy as n


project = n.Project(objective="25x", resin="IP-n162", substrate="FuSi")

edit_presets = {
    "writing_speed": "220000.0",
    "writing_power": 50.0,
    "slicing_spacing": 0.8,
    "hatching_spacing": 0.3,
    "hatching_angle": 0.0,
    "hatching_angle_increment": 0.0,
    "hatching_offset": 0.0,
    "hatching_offset_increment": 0.0,
    "hatching_back_n_forth": True,
    "mesh_z_offset": 0.0,
}

preset = n.Preset(name="supervalidname", **edit_presets)


resource_mesh = n.Mesh(
    name=" .",
    file_path="test_resources/5416ba193f0bacf1e37be08d5c249914/combined_file.stl",
    rotation=[25, 85, "20"],
)
resource_image = n.Image(
    name=".",
    file_path="test_resources/78eab7abd2cd201630ba30ed5a7ef4fc/markers.png",
)


project.load_resources(resource_image)


labels = ["anchor 0", "anchor 1", "anchor 2", "anchor 3"]

positions = [
    [-60.0, -528.0, 0.0],
    [-130.0, -528.0, 0.0],
    [-60.0, 20.0, 0.0],
    [-130.0, 20.0, 0.0],
]


coarse_aligner1 = n.CoarseAligner(residual_threshold=8).set_coarse_anchors_at(
    labels, positions
)
scene1 = n.Scene(writing_direction_upward=False).position_at(
    [10, 10, 10], [45, 45, 45]
)
group1 = n.Group().position_at([-10, -10, -8.0], [30, 30, 30])


labels = [
    "marker 0",
    "marker 1",
    "marker 2",
    "marker 3",
    "marker 4",
    "marker 5",
    "marker 6",
    "marker 7",
]

positions = [
    [-130.0, -30.0],
    [-130.0, 30.0],
    [-60.0, -30.0],
    [-60.0, 30.0],
    [-130.0, -60.0],
    [-130.0, 60.0],
    [-60.0, -60.0],
    [-60.0, 60.0],
]

scan_area_sizes = [
    [11.0, 11.0],
    [12.0, 14.0],
    [13.0, 13.0],
    [12.0, 12.0],
    [13.0, 11.0],
    [14.0, 12.0],
    [11.0, 11.0],
    [11.0, 11.0],
]

interface_aligner1 = n.InterfaceAligner(
    name="interface_aligner1",
    area_measurement=False,
    signal_type="reflection",
    detector_type="confocal",
).set_grid([8, 8], [133, 133])

interface_aligner2 = n.InterfaceAligner(
    name="myaligner",
    signal_type="reflection",
    detector_type="confocal",
    measure_tilt=True,
    area_measurement=True,
    center_stage=True,
    action_upon_failure="ignore",
    laser_power=0.3,
    scan_area_res_factors=[0.9, 0.9],
    scan_z_sample_distance=0.3,
    scan_z_sample_count=29,
).set_interface_anchors_at(labels, positions, scan_area_sizes)

coarse_aligner1.add_child(scene1)
scene1.add_child(group1)
group1.add_child(interface_aligner1)
group1.add_child(interface_aligner2)


marker_aligner1 = n.MarkerAligner(image=resource_image, marker_size=[8, 8])
# marker_aligner1.add_marker("label", 1, [2, 4, 5])
marker_aligner1.set_markers_at(["label"], [3], [[6, 7, 8]])
interface_aligner1.add_child(marker_aligner1)


structure = n.Structure(
    preset,
    resource_mesh,
    project,
    auto_load_presets=True,
    auto_load_resources=True,
)
marker_aligner1.add_child(structure)

text1 = n.Text(preset, priority=1)
lens1 = (
    n.Lens(preset, name="my lens", asymmetric=True)
    .polynomial("Standard", [1, 2, 3, 4, 5, 6], [1, 2, 3, 4])
    .surface_compensation([1, 1, 1], [86, 99, 43, 4])
)
# structure.add_child(text1)


array1 = n.Array(
    name="my array",
    count=[3, 6],
    spacing=[25, 25.0],
    order="Meander",
    shape="Round",
)

children = [
    coarse_aligner1,
    n.DoseCompensation(),
    n.StageMove(
        stage_position=[
            1,
            11,
            111,
        ]
    ),
    n.EdgeAligner(
        name="Random Edge Aligner",
        edge_location=[15.5, 42.3],
        edge_orientation=35.0,
        center_stage=False,
        action_upon_failure="ignore",
        laser_power=0.8,
        scan_area_res_factors=[1.5, 2.0],
        scan_z_sample_distance=0.15,
        scan_z_sample_count=60,
        outlier_threshold=8.5,
    ).set_measurements_at(
        labels=["Measurement 1", "Measurement 2"],
        offsets=[0.5, 1.0],
        scan_area_sizes=[[10.0, 15.0], [12.0, 18.0]],
    ),
    n.Wait(wait_time=88),
    n.Capture("my capture"),
    n.Capture("my confocal").confocal(1.1, [111, 111], [121, 121]),
    text1,
    lens1,
]
for child in children:
    project.add_child(child)

project.add_child(array1)

fiberaligner1 = n.FiberAligner(detection_margin=100)
fiberaligner2 = n.FiberAligner(
    fiber_radius=50, center_stage=False
).measure_tilt([50, 150], 11, 10)
project.add_child(fiberaligner2)
project.add_child(fiberaligner1)
project.nano("test_temp_project")
