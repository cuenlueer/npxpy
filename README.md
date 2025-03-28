<p align="center">
    <img src="https://raw.githubusercontent.com/cuenlueer/npxpy/e1f01ab85a470d2ed1aeef534a21cc6dd2aad524/docs/images/logo.svg">
</p>

[![semantic-release: conventional](https://img.shields.io/badge/semantic--release-conventional-e10079?logo=semantic-release)](https://github.com/semantic-release/semantic-release)
[![DOI](https://zenodo.org/badge/776090967.svg)](https://doi.org/10.5281/zenodo.15038194)


# npxpy
npxpy is a versatile open source Python package that enables you to build projects (NANO files) for the 3D direct laser 
lithography system **Nanoscribe Quantum X align** (**QXa**) via CLI/Scripts. It is designed such that it adheres to the
same workflow logic as Nanoscribe's GUI software *nanoPrintX*, making the application additionally user-friendly to
experienced users of the **QXa**.

## Table of Contents
- [Installation](#installation)
- [Features and Usage](#usageandfeatures)
- [Documentation](#documentation)
- [How to Cite npxpy](#howtocitenpxpy)
- [License](#license)

## Installation
You can install ```npxpy``` via ```pip``` together with all features (recommended) :
```
pip install npxpy[all]
```
It is recommended to install ```npxpy``` in a virtual environment to prevent dependency issues.  
A more selective installation with respect to features like the 3D-viewport or GDS-parsing is possible as well by
exchanging ```[all]``` with ```[viewport]``` and ```[gds]```, respectively. If you are interested in a light-weight
installation you are able to install only the core features of ```npxpy``` via:
```
pip install npxpy
```
Beware that the light-weight installation lacks the other aforementioned features entirely. 

## Features and Usage
Straightforward print project preparation with usual workflow logic is embeded in the Python-software ecosystem
with extras like GDS-parsing for high workflow integration.
```python
>>> import npxpy
>>> #  Initialize the presets and resources that you want to use in this project.
>>> #  You can either load presets directly from a .toml...
>>> preset_from_file = npxpy.Preset.load_single(file_path="preset_from_file.toml")
>>> 
>>> #  ... or initialize it inside of your script.
>>> edit_presets = {
...     "writing_speed": 220000.0,
...     "writing_power": 50.0,
...     "slicing_spacing": 0.8,
...     "hatching_spacing": 0.3,
...     "hatching_angle": 0.0,
...     "hatching_angle_increment": 0.0,
...     "hatching_offset": 0.0,
...     "hatching_offset_increment": 0.0,
...     "hatching_back_n_forth": True,
...     "mesh_z_offset": 0.0,
... }
>>> 
>>> preset_from_args = npxpy.Preset(name="preset_from_args", **edit_presets)
>>> 
>>> #  Load your resources simply via path to their directories.
>>> stl_mesh = npxpy.Mesh(file_path="./example_mesh.stl", name="stl_structure")
>>> marker = npxpy.Image(file_path="./example_marker.png", name="marker_image")
>>> 
>>> #  Initialize your project and load your presets and resources into it.
>>> project = npxpy.Project(objective="25x", resin="IP-n162", substrate="FuSi")
>>> project.load_presets(preset_from_file, preset_from_args)
>>> project.load_resources(stl_mesh, marker)
>>> 
>>> #  Prepare the nodes of your project as usual.
>>> #  Setup alignment nodes
>>> coarse_aligner = npxpy.CoarseAligner(residual_threshold=8)
>>> marker_aligner = npxpy.MarkerAligner(
...     name="Marker Aligner", image=marker, marker_size=[10, 10]
... )
>>> 
>>> # Set anchors manually...
>>> ca_positions = [
...     [200.0, 200.0, 0.0],
...     [200.0, -200.0, 0.0],
...     [-200.0, -200.0, 0.0],
...     [-200.0, 200.0, 0.0],
... ]
>>> ma_positions = [
...     [0, 200, 0.33],
...     [200, 0, 0.33],
...     [0, -200, 0.33],
...     [-200, 0, 0.33],
... ]
>>> 
>>> coarse_aligner.set_coarse_anchors_at(ca_positions)
>>> marker_aligner.set_markers_at(ma_positions)
>>> 
>>> #  ... or incorporate them in a GDS-design and read them in.
>>> import npxpy.gds
>>> 
>>> gds = npxpy.gds.GDSParser("gds_file.gds")
>>> 
>>> interface_aligner = gds.get_custom_interface_aligner(
...     cell_name="cell_with_print_scene",
...     interface_layer=(1, 0),
...     signal_type="reflection",
...     detector_type="confocal",
...     area_measurement=True,
...     measure_tilt=True,
... )
>>> 
>>> #  Initialize printing scene
>>> scene = npxpy.Scene(name="scene", writing_direction_upward=True)
>>> 
>>> #  Initialize structure with desired preset and mesh defined above.
>>> structure = npxpy.Structure(
...     name="structure", preset=preset_from_file, mesh=stl_mesh
... )
>>> 
>>> #  Arrange hierarchy of all nodes as desired either with .add_child()...
>>> coarse_aligner.add_child(scene.add_child(interface_aligner))
>>> 
>>> #  ...or more conveniently by using .append_node() to append
>>> #  consecutively to the lowest node.
>>> scene.append_node(marker_aligner, structure)
>>> 
>>> #  Eventually, add all highest-order nodes of interest
>>> #  (here only coarse_aligner) to project.
>>> project.add_child(coarse_aligner)
>>> 
>>> #  After allocating your nodes, you can copy, manipulate and add additional
>>> #  instances as you like.
>>> scene_1 = scene.deepcopy_node(copy_children=True)
>>> scene_1.name = "scene_1"
>>> scene_1.translate([254.0, 300.0, 0.0])
>>> 
>>> #  You can access descendants/ancestors as you go via semantically ordered lists.
>>> structure_1 = scene_1.all_descendants[-1]
>>> structure_1.preset = preset_from_args
>>> structure_1.name = "structure_1"
>>> 
>>> coarse_aligner.add_child(scene_1)
>>> 
>>> #  Checking the node order can be done as well
>>> project.tree() 
```
```
Project (project)
    └──Coarse aligner (coarse_alignment)
        ├──scene (scene)
        │   └──cell_with_print_scene(1, 0) (interface_alignment)
        │       └──Marker Aligner (marker_alignment)
        │           └──structure (structure)
        └──scene_1 (scene)
            └──cell_with_print_scene(1, 0) (interface_alignment)
                └──Marker Aligner (marker_alignment)
                    └──structure_1 (structure)
```
```python
>>> #  Export your project to a .nano-file.
>>> project.nano(project_name="my_project")
```
Features like a viewport based on ```pyvistaqt``` are also available for keeping track of your project visually as well.
```python
>>> viewport = project.viewport()
```
<p align="center">
    <img src="https://raw.githubusercontent.com/cuenlueer/npxpy/refs/heads/main/docs/examples/example_README/example0_viewport.png">
</p>

## [Documentation](https://cuenlueer.github.io/npxpy/)
To view more functionalities and use case examples of npxpy, refer to the the provided [documentation](https://cuenlueer.github.io/npxpy/).

## [How to Cite](https://doi.org/10.5281/zenodo.15038194)
[![DOI](https://zenodo.org/badge/776090967.svg)](https://doi.org/10.5281/zenodo.15038194)

If npxpy contributes to your research, software, or project, we kindly request that you cite it in your
publications using the provided DOI above.

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/cuenlueer/nanoAPI/blob/main/LICENSE)
file for details.  
**TL;DR:** You may use, modify, and distribute this software freely, provided the license and copyright notice are included.
### What This Means for Users and Contributors

- **Freedom to Use:** You are free to use this software in any project (commercial, personal, or otherwise) without
restrictions, as long as the MIT License terms are met.

- **Modifications and Derivatives:** You may modify the code, create derivative works, and distribute them under any
license of your choice. The only requirements are:
  - Include the original MIT License and copyright notice with your distribution.
  - Clearly state any significant changes made to the original code.
- **Linking and Distribution:** You may link this software with proprietary code or other open-source projects without
restrictions. No obligations apply to the proprietary components of your project.

- **Contribution:** By contributing to this project, you agree that your contributions will be licensed under the
MIT License. This ensures your changes remain freely usable by others under the same terms.

For more details on your rights and responsibilities under this license, please review the [LICENSE](https://github.com/cuenlueer/nanoAPI/blob/main/LICENSE) file.
