# Introductory Example
![](example0_viewport.png)

---

## Overview
The code provided in this section is the introductory example as given on the Github repository's [Readme](https://github.com/cuenlueer/npxpy/blob/main/README.md)
and the documentation's [Home tab](https://cuenlueer.github.io/npxpy/).

**This script:**

- **Loads printing presets and resources**:  
  - Reads a `.toml` preset file and initializes custom presets with parameters like writing speed, power, and hatching settings.  
  - Imports a 3D mesh (`example_mesh.stl`) and a marker image (`example_marker.png`).  

- **Sets up alignment configurations**:  
  - Defines `CoarseAligner` and `MarkerAligner` nodes for nano-printing alignment, with manual anchor positions.  
  - Integrates GDS cell data (`gds_file.gds`) to create a custom `InterfaceAligner` with anchor positions/scan sizes defined by polygons in a GDS file.  

- **Organizes the printing hierarchy**:  
  - Initializes a `Scene` with upward writing direction and attaches a `Structure` (using the mesh and preset).  
  - Builds a node hierarchy with coarse alignment, scene, interface alignment, and marker alignment.  

- **Duplicates and modifies scenes**:  
  - Clones scenes, translates their positions, and updates their presets/names for multi-scene arrangements.  

- **Exports the project**:  
  - Generates a `.nano` file for and validates node hierarchy via `project.tree()`.

**Prerequisites**

**Files/Directories**:  
- `preset_from_file.toml` (preset configuration).  
- `example_mesh.stl` (3D structure mesh).  
- `example_marker.png` (alignment marker image).  
- `gds_file.gds` (GDSII design for interface alignment).  

**Python Packages**:  
- `npxpy` installed with key `all`: `pip install npxpy[all]`.  
- `shapely` & `gdshelpers` (for GDS parsing and geometry operations).

You can download the full example below:

---

[Download full example](example_README.zip){ .md-button .md-button--primary}

---

## Full Implementation

```python
import npxpy

#  Initialize the presets and resources that you want to use in this project.
#  You can either load presets directly from a .toml...
preset_from_file = npxpy.Preset.load_single(file_path="preset_from_file.toml")

#  ... or initialize it inside of your script.
edit_presets = {
    "writing_speed": 220000.0,
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

preset_from_args = npxpy.Preset(name="preset_from_args", **edit_presets)

#  Load your resources simply via path to their directories.
stl_mesh = npxpy.Mesh(file_path="./example_mesh.stl", name="stl_structure")
marker = npxpy.Image(file_path="./example_marker.png", name="marker_image")

#  Initialize your project and load your presets and resources into it.
project = npxpy.Project(objective="25x", resin="IP-n162", substrate="FuSi")
project.load_presets(preset_from_file, preset_from_args)
project.load_resources(stl_mesh, marker)

#  Prepare the nodes of your project as usual.
#  Setup alignment nodes
coarse_aligner = npxpy.CoarseAligner(residual_threshold=8)
marker_aligner = npxpy.MarkerAligner(
    name="Marker Aligner", image=marker, marker_size=[10, 10]
)

# Set anchors manually...
ca_positions = [
    [200.0, 200.0, 0.0],
    [200.0, -200.0, 0.0],
    [-200.0, -200.0, 0.0],
    [-200.0, 200.0, 0.0],
]

ma_positions = [
    [0, 200, 0.33],
    [200, 0, 0.33],
    [0, -200, 0.33],
    [-200, 0, 0.33],
]

coarse_aligner.set_coarse_anchors_at(ca_positions)
marker_aligner.set_markers_at(ma_positions)

#  ... or incorporate them in a GDS-design and read them in.
import npxpy.gds

gds = npxpy.gds.GDSParser("gds_file.gds")

interface_aligner = gds.get_custom_interface_aligner(
    cell_name="cell_with_print_scene",
    interface_layer=(1, 0),
    signal_type="reflection",
    detector_type="confocal",
    area_measurement=True,
    measure_tilt=True,
)

#  Initiale printing scene
scene = npxpy.Scene(name="scene", writing_direction_upward=True)

#  Initialize structure with desired preset and mesh defined above.
structure = npxpy.Structure(
    name="structure", preset=preset_from_file, mesh=stl_mesh
)

#  Arrange hierarchy of all nodes as desired either with .add_child()...
coarse_aligner.add_child(scene.add_child(interface_aligner))

#  ...or more conveniently by using .append_node() to append
#  consecutively to the lowest node.
scene.append_node(marker_aligner, structure)

#  Eventually, add all highest-order nodes of interest
#  (here only coarse_aligner) to project.
project.add_child(coarse_aligner)

#  After allocating your nodes, you can copy, manipulate and add additional
#  instances as you like.
scene_1 = scene.deepcopy_node(copy_children=True)
scene_1.name = "scene_1"
scene_1.translate([254.0, 300.0, 0.0])

#  You can access descendants/ancestors as you go via semantically ordered lists.
structure_1 = scene_1.all_descendants[-1]
structure_1.preset = preset_from_args
structure_1.name = "structure_1"

coarse_aligner.add_child(scene_1)

#  Checking the node order can be done as well
project.tree()

#  Export your project to a .nano-file.
project.nano(project_name="my_project")

```

In addition, you can regard your project in the viewport.

```python
#  Check Project in Viewport

project.viewport()

```

![](example0_viewport.png)