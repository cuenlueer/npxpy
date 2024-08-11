![](images/logo.svg)
# npxpy

npxpy is a versatile open source Python package that enables you to build projects (NANO files) for the 3D direct laser 
lithography system **Nanoscribe Quantum X align** (**QXa**) via CLI/Scripts. It is designed such that it emulates the logic of Nanoscribe's
GUI software *nanoPrintX*, making the application additionally user-friendly to experienced users of the **QXa**.

## Table of Contents
- [Installation](#installation)
- [Features and Usage](#usageandfeatures)
- [Documentation](#documentation)
- [How to Cite npxpy](#howtocitenpxpy)
- [License](#license)

## Installation
You can install ```npxpy``` via ```pip```:
```
pip install npxpy
```

## Features and Usage
npxpy comes implemented with all core elements known from *nanoPrintX*:

- **Presets**
- **Resources**
  - Images
  - Meshes
- **Nodes**
  - **Spacial nodes:** 
    - Scene
    - Group
    - Array
  - **Structure nodes:** 
    - Structure
    - Text
    - Lens
  - **Aligner nodes:**
    - Coarse aligner
    - Interface aligner
    - Fiber aligner
    - Marker aligner
    - Edge aligner
  - **Miscellaneous nodes:**
    - Dose compensation
    - Capture
    - Stage move
    - Wait

A simple example for a project can look like the one below.

```python
import npxpy

#  Initialize the presets and resources that you want to use in this project.
#  You can either load presets directly from a .toml...
preset_from_file = npxpy.Preset.load_single(file_path = 'preset_from_file.toml')

#  ... or initialize it inside of your script.
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

preset_from_args = npxpy.Preset(name = 'preset_from_args', **edit_presets)

#  Load your resources simply via path to their directories. 
stl_mesh = npxpy.Mesh(path = './example_mesh.stl', name = 'stl_structure_0')
marker = npxpy.Image(path = './example_marker.png', name = 'marker_image')

#  Initialize your project and load your presets and resources into it.
project = npxpy.Project(objective = '25x', resin = 'IP-n162', substrate = 'FuSi')
project.load_presets([preset_from_file, preset_from_args])
project.load_resources([stl_mesh, marker])

#  Prepare the nodes of your project as you would in nanoPrintX-Treeview.
#  Starting with the coarse aligner.
coarse_aligner = npxpy.CoarseAligner(residual_threshold = 8)

ca_labels = ['anchor 0',
          'anchor 1',
          'anchor 2',
          'anchor 3']
ca_positions = [[200.0, 200.0, 0.0],
             [200.0, -200.0, 0.0],
             [-200.0, -200.0, 0.0],
             [-200.0, 200.0, 0.0]]

coarse_aligner.set_coarse_anchors_at(ca_labels, ca_positions)

#  Initializing printing scene
scene_0 = npxpy.Scene(name = 'scene_0', writing_direction_upward=True)

#  Interface alignment
interface_aligner = npxpy.InterfaceAligner(name = 'Interface Aligner')

ia_labels = ['marker 0',
          'marker 1',
          'marker 2',
          'marker 3',
          'marker 4',
          'marker 5',
          'marker 6',
          'marker 7']

ia_positions = [[-130.0, -30.0],
             [-130.0, 30.0],
             [-60.0, -30.0],
             [-60.0, 30.0],
             [-130.0, -60.0],
             [-130.0, 60.0],
             [-60.0, -60.0],
             [-60.0, 60.0]]

interface_aligner.set_interface_anchors_at(ia_labels, ia_positions)

#  Marker alignment
marker_aligner = npxpy.MarkerAligner(name = 'Marker Aligner',
                                     image = marker, marker_size=[10,10])

#  Initialize structure with desired preset and mesh defined above.
structure_0 = npxpy.Structure(name = 'structure_0', 
                              preset = preset_from_file, mesh = stl_mesh)

#  Arrange hierarchy of all nodes as desired either with .add_child()...
coarse_aligner.add_child(scene_0)
scene_0.add_child(interface_aligner)

#  ...or more conveniently by using .append_node() to append
#  directly to the lowest node.
scene_0.append_node(marker_aligner)
#
scene_0.append_node(structure_0)

#  Eventually, add all highest-order nodes of interest
#  (here only coarse_aligner) to project.
project.add_child(coarse_aligner)

#  After allocating your nodes, you can copy, manipulate and add additional
#  instances as you like.
scene_1 = scene_0.deepcopy_node(copy_children = True)
scene_1.name = 'scene_1'
scene_1.position = [254, 300, 0]

#  You can access descendants/ancestors as you go via semantically ordered lists.
structure_1 = scene_1.all_descendants[-1]
structure_1.preset = preset_from_args
structure_1.name = 'structure_1'

coarse_aligner.add_child(scene_1)

#  Export your project to a .nano-file.
project.nano(project_name = 'my_project')
```
Features like a CLI-treeview are also available for keeping track of your project even without an external
GUI!
```python
In: project.tree()
Out: Project (project)
        └──Coarse aligner (coarse_alignment)
            ├──scene_0 (scene)
            │   └──Interface Aligner (interface_alignment)
            │       └──Marker Aligner (marker_alignment)
            │           └──structure_0 (structure)
            └──scene_1 (scene)
                └──Interface Aligner (interface_alignment)
                    └──Marker Aligner (marker_alignment)
                        └──structure_1 (structure)

In:  scene_0.tree()
Out: scene_0 (scene)
        └──Interface Aligner (interface_alignment)
            └──Marker Aligner (marker_alignment)
                └──structure_0 (structure)
```
## [Documentation](heregoesthelink!)
To see more functionalities and examples of npxpy, make sure to check the provided [documentation](heregoesthelink!).

## License

This project is licensed under the GNU Lesser General Public License v3.0 (LGPL-3.0) - see the [LICENSE](https://github.com/cuenlueer/nanoAPI/blob/main/LICENSE) file for details.
### What This Means for Users and Contributors

- **Freedom to Use:** You are free to use this software in your projects, commercial or otherwise, as long as you comply with the LGPL-3.0 terms.

- **Modifying the Library:** If you modify this library, you must distribute your modifications under the same LGPL-3.0 license. Your modifications must be documented, and the modified library must be available for users to access, use, and link against.

- **Linking to Proprietary Code:** You can link this library with proprietary code, forming a combined work. The proprietary code will not be subject to the terms of LGPL, provided the LGPL library is not modified and is used as a dynamically linked module.

- **Contribution and Distribution:** If you contribute to this project, your contributions will be under the same LGPL-3.0 license. If you distribute this library, either in original or modified form, you must do so under the LGPL-3.0, ensuring that recipients have access to the source code of the library and the rights to modify it.

For more details on your rights and responsibilities under this license, please review the [LICENSE](https://github.com/cuenlueer/nanoAPI/blob/main/LICENSE) file.
