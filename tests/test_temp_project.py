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
    translation=[-50, 75, 90],
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
    positions,
    labels,
)
coarse_aligner_rot = n.CoarseAligner().set_coarse_anchors_at(
    positions,
    labels,
)
scene1 = n.Scene(writing_direction_upward=False).position_at(
    [1000, 100, 300], [45, 45, 45]
)
group1 = n.Group().position_at([-1000, -10, -8.0], [30, 30, 30])


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
).set_interface_anchors_at(positions, labels, scan_area_sizes)

coarse_aligner1.add_child(scene1)
scene1.add_child(group1)
group1.add_child(interface_aligner1)
group1.add_child(interface_aligner2)


marker_aligner1 = n.MarkerAligner(image=resource_image, marker_size=[8, 8])
# marker_aligner1.add_marker("label", 1, [2, 4, 5])

labels = ["Marker0", "Marker1", "Marker2", "Marker3", "Marker4"]
orientations = [45, 40, 30, 20, 10]
positions = [
    [6.0, 7.0, 8.0],
    [100, 100, 0],
    [100, -100, 0],
    [-100, -100, 0],
    [-100, 100, 0],
]
marker_aligner1.set_markers_at(
    positions,
    orientations,
    labels,
)

interface_aligner1.add_child(marker_aligner1)


structure = n.Structure(
    preset,
    resource_mesh,
    color="pink",
    position=[111, 111, 111],
    rotation=[111, 222, 333],
).auto_load(project)
fiberaligner3 = n.FiberAligner(
    fiber_radius=50, center_stage=False
).measure_tilt([50, 150], 11, 10)
text0 = n.Text(
    preset, priority=1, position=[-11, -33, -44], rotation=[11, 33, 44]
)

edgealigner0 = n.EdgeAligner(
    name="Edge Aligner in Scene",
    edge_location=[111, 222],
    edge_orientation=54.0,
).set_measurements_at(
    labels=[
        "Measurement 1",
        "Measurement 2",
        "Measurement 3",
        "Measurement 4",
    ],
    offsets=[100, -200, -55.2, -88],
    scan_area_sizes=[
        [50, 10.0],
        [3.3, 3.3],
        [1, 5],
        [33, 31],
    ],
)


lens1 = (
    n.Lens(
        preset,
        name="my lens",
        color="lightblue",
        crop_base=True,
        asymmetric=True,
        position=[111, 111, 111],
        rotation=[-45, 0, 0],
        radius=111,
        height=33,
        curvature=0.01,
        conic_constant=-1,
        curvature_y=0.02,
        conic_constant_y=-2,
    )
    .polynomial(
        "Normalized",
        [
            0.1,
            0.2,
            0.3,
            0.4,
        ],
        [0.1, 0.3],
    )
    .surface_compensation([0.001, 1e-7, 1e-13], [0.01])
)

marker_aligner1.add_child(structure)
marker_aligner1.add_child(coarse_aligner_rot)
marker_aligner1.add_child(fiberaligner3)
marker_aligner1.add_child(text0)
marker_aligner1.add_child(edgealigner0)
marker_aligner1.add_child(
    n.DoseCompensation(
        name="DC in Scene",
        edge_location=[222, -111, 111],
        edge_orientation=54,
        domain_size=[80, 160, 250],
        gain_limit=10,
    )
)
marker_aligner1.add_child(lens1)
text1 = n.Text(preset, priority=1)

scene0 = scene1.deepcopy_node()
# structure.add_child(text1)


array1 = n.Array(
    name="my array",
    count=[3, 6],
    spacing=[111, 111.0],
    order="Meander",
    shape="Round",
).position_at(position=[-500, 0, 0], rotation=[0, 0, 45])

children = [
    coarse_aligner1,
    n.DoseCompensation(
        edge_location=[222, -111, 111],
        edge_orientation=54,
        domain_size=[80, 160, 250],
        gain_limit=10,
    ),
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
    text1,
]

project.add_child(*children)

array1.add_child(
    n.Capture("my confocal").confocal(1.1, [55, 111], [121, 121]),
)
project.add_child(array1)

group0 = n.Group().position_at(position=[1111, 1111, 0], rotation=[0, 90, 0])
group0.add_child(
    n.Capture("my capture"),
)
project.add_child(group0)

fiberaligner1 = n.FiberAligner(detection_margin=100)
fiberaligner2 = n.FiberAligner(
    fiber_radius=50, center_stage=False
).measure_tilt([50, 150], 11, 10)
project.add_child(fiberaligner2)
project.add_child(fiberaligner1)
project.nano("test_temp_project")
