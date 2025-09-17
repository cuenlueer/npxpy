import npxpy


def generate_menger_sponge_positions(order=3, smallest_cube_size=10.0):
    """
    Generates the positions for all cubes in a Menger sponge of a given order.

    Parameters:
    - order (int): The order of the Menger sponge (default is 3).
    - smallest_cube_size (float): The size of the smallest cube (voxel), default is 20.0 units.

    Returns:
    - List of tuples: Each tuple represents the (x, y, z) origin of a cube.
    """
    divisions = 3**order  # Total number of divisions per axis
    positions = []

    for x in range(divisions):
        for y in range(divisions):
            for z in range(divisions):
                cx, cy, cz = x, y, z
                is_solid = True
                for _ in range(order):
                    if ((cx % 3 == 1) + (cy % 3 == 1) + (cz % 3 == 1)) >= 2:
                        is_solid = False
                        break
                    cx //= 3
                    cy //= 3
                    cz //= 3
                if is_solid:
                    # Calculate the position by scaling with the smallest cube size
                    pos = (
                        x * smallest_cube_size,
                        y * smallest_cube_size,
                        z * smallest_cube_size,
                    )
                    positions.append(pos)
    return positions


menger_sponge_order = 3
voxel_cube_size = 1  # in micrometer

#  Initialize the presets and resources that you want to use in this project.
preset = npxpy.Preset.load_single(file_path="25x_IP-n162_surface_menger.toml")
#  Load cylinders to sweep and marker.
voxel_cube = npxpy.Mesh(
    file_path=f"voxel_cube_{voxel_cube_size}um.stl",
    name=f"voxel_cube_{voxel_cube_size}um",
)
#  Initialize your project and load your presets and resources into it.
project = npxpy.Project(objective="25x", resin="IP-n162", substrate="FuSi")
project.load_presets(preset)
project.load_resources(voxel_cube)

#  Interface alignment
interface_aligner_labels = [
    "marker 0",
    "marker 1",
    "marker 2",
    "marker 3",
]
interface_aligner_positions = [
    [135.0, 0.0],
    [0.0, 135.0],
    [-135.0, 0.0],
    [0.0, -135.0],
]

interface_aligner = npxpy.InterfaceAligner(name="Interface Aligner")
interface_aligner.set_interface_anchors_at(
    labels=interface_aligner_labels, positions=interface_aligner_positions
)

#  Initializing printing scene
scene = npxpy.Scene(
    name="scene_0",
    position=[0, 0, 0],
    writing_direction_upward=True,
)

project.add_child(scene).append_node(interface_aligner)

menger_sponge_voxel_positions = generate_menger_sponge_positions(
    order=menger_sponge_order, smallest_cube_size=voxel_cube_size
)


for pos in menger_sponge_voxel_positions:
    voxel_cube_structure = npxpy.Structure(
        mesh=voxel_cube, preset=preset, name=f"{voxel_cube.name}_{pos}"
    ).position_at(position=list(pos))
    voxel_cube_structure.translate(
        [
            -(voxel_cube_size * 3**menger_sponge_order) / 2,
            -(voxel_cube_size * 3**menger_sponge_order) / 2,
            0,
        ]
    )
    interface_aligner.add_child(voxel_cube_structure)


# Export project to NANO file
project.nano(
    f"menger_sponge_M{menger_sponge_order}_{voxel_cube_size}um_single_scene"
)
