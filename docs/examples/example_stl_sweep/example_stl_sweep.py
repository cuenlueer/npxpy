import npxpy
import os

################################################################################
# Example: Setting up a sweep of STL files with different design parameters
#
# This script demonstrates how to:
# 1. Initialize a project with given printing parameters (objective, resin, substrate).
# 2. Load presets and various resources such as meshes and images.
# 3. Configure and add aligners (coarse aligner, interface aligner, marker aligner).
# 4. Arrange a grid of scenes, each containing a 3D structure (in this example, cylinders),
#    and add textual labels describing the structure parameters.
# 5. Finally, export the entire project configuration as a .nano file.
#
# Throughout this script, we will:
# - Go through each step in detail.
# - Clearly comment the code to provide insights into the workflow and reasoning.
#
# NOTE: Before running this script, ensure you have the following:
# - A valid `25x_IP-n162_cylinders.toml` preset file.
# - A `meshes/` directory containing the prepared cylinder mesh files
#   (cylinder_0.stl, cylinder_1.stl, etc.).
# - The `marker.png` image file that will be used by the marker aligner.
# - The `npxpy` library installed in your environment.
################################################################################

# ------------------------------------------------------------------------------
# Step 1: Loading the Preset and Resources
# ------------------------------------------------------------------------------

# Load a preset (configuration file) that defines parameters such as laser settings,
# writing parameters, and resin properties. This file is crucial for printing setup.
preset = npxpy.Preset.load_single(file_path="25x_IP-n162_cylinders.toml")

# Load cylinder meshes. The `meshes/` directory contains a series of mesh files
# whose filenames end with a numeric index (`cylinder_0.stl, cylinder_1.stl, ...`).
# We sort the filenames by their numeric suffix to maintain a known order.
# Otherwise the ordering would be lexicographical.
cylinder_meshes = [
    npxpy.Mesh(file_path=f"meshes/{mesh}", name=f"{mesh}")
    for mesh in sorted(
        os.listdir("meshes"), key=lambda x: int(x.split(".")[0].split("_")[-1])
    )
]

# Load a marker image, which will be used by the marker aligner to detect
# orientation and positioning.
marker = npxpy.Image(file_path="marker.png", name="marker_image")

# ------------------------------------------------------------------------------
# Step 2: Initializing the Project
# ------------------------------------------------------------------------------

# Initialize the project with metadata according to installment at the QXa:
# - objective: e.g., a 25x microscope objective
# - resin: e.g., "IP-n162" (a commercially available photoresist)
# - substrate: e.g., "FuSi" (fused silica)
project = npxpy.Project(objective="25x", resin="IP-n162", substrate="FuSi")

# Load the preset and other resources into the project.
project.load_presets(preset)
project.load_resources(marker)
project.load_resources(cylinder_meshes)

# ------------------------------------------------------------------------------
# Step 3: Setting Up the Coarse Aligner
# ------------------------------------------------------------------------------

# A coarse aligner is used to define a rough coordinate system for subsequent alignments.
# We define four "coarse anchor" points in the sample coordinate space.
coarse_aligner_labels = ["anchor 0", "anchor 1", "anchor 2", "anchor 3"]
coarse_aligner_positions = [
    [-100.0, -100.0, 0.0],
    [1900.0, -100.0, 0.0],
    [1900.0, 1900.0, 0.0],
    [-100.0, 1900.0, 0.0],
]

# Initialize the coarse aligner with a residual threshold
# (tolerance for misalignment in micrometer).
coarse_aligner = npxpy.CoarseAligner(residual_threshold=5)
coarse_aligner.set_coarse_anchors_at(
    labels=coarse_aligner_labels, positions=coarse_aligner_positions
)

# Add the coarse aligner to the project.
project.add_child(coarse_aligner)

# ------------------------------------------------------------------------------
# Step 4: Setting Up the Interface Aligner
# ------------------------------------------------------------------------------

# The interface aligner adjusts the coordinate system to the printing interface
# (e.g., coverslip, substrate).
# Here we define four interface anchor points in 2D space, i.e., the interface.
interface_aligner_labels = ["marker 0", "marker 1", "marker 2", "marker 3"]
interface_aligner_positions = [
    [0.0, 50.0],
    [50.0, 0.0],
    [-50.0, 0.0],
    [0.0, -50.0],
]

interface_aligner = npxpy.InterfaceAligner(
    name="Interface Aligner",
    measure_tilt=True,
)
interface_aligner.set_interface_anchors_at(
    labels=interface_aligner_labels,
    positions=interface_aligner_positions,
)

# ------------------------------------------------------------------------------
# Step 5: Setting Up the Marker Aligner
# ------------------------------------------------------------------------------

# The marker aligner uses an image (like our loaded `marker.png`) and
# specified marker positions to finely tune alignment on the previously found plane.
# In this example, we define four marker positions and their orientations.
# Note: The marker_size needs to be set such that it coincides with the size on
# the substrate.
marker_aligner_labels = ["marker 0", "marker 1", "marker 2", "marker 3"]
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

# ------------------------------------------------------------------------------
# Step 6: Creating a Base Scene for Sweeping Parameters
# ------------------------------------------------------------------------------

# We'll create a "base" scene that includes the interface and marker aligners.
# Later, we'll copy this scene multiple times to create a grid of scenes that
# can be populated with the structures exhibiting varying parameters.
sweep_scene = npxpy.Scene(name="scene_0", writing_direction_upward=True)

# Append the aligners to the scene node so that they apply to all structures within that scene.
sweep_scene.append_node(interface_aligner)
sweep_scene.append_node(marker_aligner)

# ------------------------------------------------------------------------------
# Step 7: Generating a Grid of Scenes
# ------------------------------------------------------------------------------

# We want to arrange 10 x 10 scenes (100 scenes total), each displaced by a
# certain pitch in x- and y-direction.
# Each scene will contain one of the cylinders and a text label describing its parameters.

# Generate positions for each scene in a grid layout as specified by x/y-count
# and x/y-pitch.
count_x = 10
pitch_x = 200  # 200 µm spacing in x-direction
count_y = 10
pitch_y = 200  # 200 µm spacing in y-direction

sweep_scenes_positions = [
    [x, y, 0]
    for y in range(0, count_y * pitch_y, pitch_y)
    for x in range(0, count_x * pitch_x, pitch_x)
]

# Generate textual labels corresponding to the parameters of each cylinder.
# Here, radius (r) from 5 to 50 (steps of 5), and height (h) from 10 to 100 (steps of 10).
# This creates a sequence of parameter strings like "r=5\nh=10", "r=5\nh=20", ..., "r=50\nh=100".
text_labels = [
    f"r={r}\nh={h}"
    for r in range(5, 55, 5)  # radius steps: 5, 10, 15, ..., 50
    for h in range(10, 110, 10)  # height steps: 10, 20, 30, ..., 100
]

# Create a separate scene instance for each position in the grid.
# Each is a deep copy of the base `sweep_scene`, maintaining the earlier defined
# and attached aligner structure.
sweep_scenes_list = [
    sweep_scene.deepcopy_node().position_at(position=pos, rotation=[0, 0, 0])
    for pos in sweep_scenes_positions
]

# ------------------------------------------------------------------------------
# Step 8: Adding Cylinders and Labels to the Scenes
# ------------------------------------------------------------------------------

# For each cylinder and corresponding scene, we:
# - Create a structure node assigning the mesh and preset.
# - Add a textual label below the structure.
# - Attach these nodes to the scene hierarchy.

# Loop over the cylinder meshes, the newly created scenes, and the text labels simultaneously.
for cylinder, scene_instance, text in zip(
    cylinder_meshes, sweep_scenes_list, text_labels
):
    # Create a structure from the cylinder mesh using the loaded preset.
    cylinder_structure = npxpy.Structure(
        name=cylinder.name, preset=preset, mesh=cylinder
    )

    # Add the cylinder structure to the scene.
    scene_instance.append_node(cylinder_structure)

    # Create a text label that shows the parameters (r and h) and the
    # STL-file name corresponding to the respective cylinder in the current scene.
    text_label = npxpy.Text(
        position=cylinder_structure.position,
        text=f"{text}\n{cylinder_structure.name}",
        preset=preset,
    )

    # Shift the label slightly below the cylinder so they don't overlap visually.
    text_label.translate([0, -75, 0])

    # Grab the marker aligner node within the current scene hierarchy
    # so all alignment steps applied to the cylinder are applied to the text as well.
    marker_aligner_in_scene = scene_instance.grab_all_nodes_bfs(
        "marker_alignment"
    )[0]
    marker_aligner_in_scene.add_child(text_label)

    # Finally, add the fully populated scene (with structure and label) to the coarse aligner.
    coarse_aligner.add_child(scene_instance)

# ------------------------------------------------------------------------------
# Step 9: Exporting the Project
# ------------------------------------------------------------------------------

# Once all scenes, structures, aligners, and presets are set up, we export the entire project.
# The `.nano` file can be opened with nanoPrintX for a final visual check and/or
# uploaded directly to the QXa for printing.
project.nano(project_name="cylinder_params_sweep")

################################################################################
# End of Example
#
# In this script, we learned how to:
# - Initialize an npxpy project with given presets.
# - Load resources like meshes and marker images.
# - Set up various aligners to define and refine the coordinate system.
# - Create a grid of scenes containing different structures and text labels.
# - Export the final setup as a .nano file.
#
# For further exploration, consider:
# - Adjusting parameters (pitches, counts, preset settings).
# - Adding different meshes and/or combining multiple structures.
# - Experimenting with different alignment strategies and marker images.
################################################################################
