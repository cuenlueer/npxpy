import numpy as np
from stl import mesh
import pyvista as pv
from copy import deepcopy


def generate_menger_sponge_positions(order=3, smallest_cube_size=20.0):
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


def main(order=3, smallest_cube_size=20.0, stl_filename="voxel_cube.stl"):
    """
    Generates a Menger sponge, loads the voxel STL, and visualizes it using PyVista.

    Parameters:
    - order (int): The order of the Menger sponge (default is 3).
    - smallest_cube_size (float): The size of the smallest cube (voxel), default is 20.0 units.
    - stl_filename (str): Path to the voxel STL file (default is 'voxel_cube.stl').
    """
    # Generate positions for the Menger sponge
    positions = generate_menger_sponge_positions(
        order=order, smallest_cube_size=smallest_cube_size
    )
    print(
        f"Number of cubes in Menger sponge of order {order}: {len(positions)}"
    )

    # Load the voxel cube STL
    try:
        voxel_mesh = mesh.Mesh.from_file(stl_filename)
    except FileNotFoundError:
        print(f"Error: The file '{stl_filename}' was not found.")
        return

    # Initialize a PyVista plotter
    plotter = pv.Plotter()

    # Append all voxel meshes at their respective positions
    for pos in positions:
        # Create a translated copy of the voxel mesh
        translated_mesh = deepcopy(voxel_mesh)
        translated_mesh.vectors += pos
        # Convert numpy-stl mesh to PyVista mesh
        points = translated_mesh.vectors.reshape(-1, 3)
        faces = np.arange(len(points)).reshape(-1, 3)
        faces = np.hstack([np.full((faces.shape[0], 1), 3), faces])

        pv_mesh = pv.PolyData(points, faces)
        plotter.add_mesh(pv_mesh, color="orange", show_edges=False)

    # Set plotter properties for better visualization
    plotter.set_background("white")
    plotter.show_grid()
    plotter.show_axes()

    # Display the plot
    plotter.show()


if __name__ == "__main__":
    # You can change the order here if needed
    main(order=3, smallest_cube_size=20.0, stl_filename="voxel_cube.stl")
