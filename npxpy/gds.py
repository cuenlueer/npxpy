# -*- coding: utf-8 -*-
"""
Created on Fri Feb 21 15:54:24 2025

@author: CU
"""
import os
import math
import pya
from typing import List, Dict, Tuple
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, box
from shapely.affinity import translate, rotate
from shapely.ops import unary_union
import trimesh
from npxpy import (
    Scene,
    Project,
    Mesh,
    Image,
    Structure,
    Preset,
    InterfaceAligner,
    CoarseAligner,
    MarkerAligner,
    Group,
)
import PIL
import sys
from io import StringIO
from functools import wraps
from inspect import signature


def verbose_output(verbose_param="_verbose"):
    """Decorator to suppress print statements based on a verbose flag"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get the verbosity flag using function signature
            sig = signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            verbose = bound_args.arguments.get(verbose_param, False)

            # Suppress output if not verbose
            original_stdout = sys.stdout
            if not verbose:
                sys.stdout = StringIO()

            try:
                result = func(*args, **kwargs)
                # Flush suppressed output if needed
                if not verbose:
                    sys.stdout.getvalue()  # Consume captured output
                return result
            finally:
                sys.stdout = original_stdout  # Always restore stdout

        return wrapper

    return decorator


# Load the GDS layout
# (Otpional) Specify custom top cell in GDS by name (type str)
# (Optional) Specify the write field by passing prepared Scene
class _write_field_scene(Scene):
    def __init__(self):
        super().__init__()
        ia = InterfaceAligner(signal_type="auto", measure_tilt=True)
        ia.set_grid(count=[2, 2], size=[180, 180])
        self.add_child(ia)


class GDSParser:
    def __init__(
        self,
        gds_file: str,
    ):
        self.layout = pya.Layout()
        self.layout.read(gds_file)
        self.gds_name = gds_file.split(".")[0]
        self._plot_tiles_flag = False
        self._previous_image_safe_path_marker_aligned_printing = "0/0"

    def _gather_polygons_in_child_cell(self, child_cell, layer_to_print):
        """
        Return a list of NumPy arrays containing polygon coordinates in the given
        cell.
        """
        polygons = []
        for shape in child_cell.shapes(layer_to_print):
            if shape.is_polygon() or shape.is_box():
                poly = shape.dpolygon
                # Convert the polygon's points to a NumPy array
                coords = np.array([(p.x, p.y) for p in poly.each_point_hull()])
                polygons.append(coords)
        return polygons

    def _polygons_to_shapely(self, polygons_np):
        """
        Convert a list of NumPy arrays (each shape (N,2))
        into a list of shapely Polygons.
        """
        shapely_polygons = []
        for arr in polygons_np:
            # Ensure closure if needed, or let Shapely handle it
            # Note: If your arrays are not closed, Shapely still interprets them as closed
            shapely_polygons.append(Polygon(arr))
        return shapely_polygons

    def _tile_polygon(self, ix, iy, tile_size, epsilon):
        """
        Return a shapely Polygon for the tile at (ix, iy),
        where each tile is 100×100, and (0,0) tile is centered around the origin:
           => x in [ix*100 - 50, ix*100 + 50]
           => y in [iy*100 - 50, iy*100 + 50]
        """
        xmin = ix * tile_size - tile_size / 2 - epsilon
        xmax = ix * tile_size + tile_size / 2 + epsilon
        ymin = iy * tile_size - tile_size / 2 - epsilon
        ymax = iy * tile_size + tile_size / 2 + epsilon
        return box(xmin, ymin, xmax, ymax)  # shapely box

    def _get_bounding_box(self, shapely_polygons):
        """
        Returns (min_x, min_y, max_x, max_y) that bounds all given shapely polygons.
        """
        minx = min(poly.bounds[0] for poly in shapely_polygons)
        miny = min(poly.bounds[1] for poly in shapely_polygons)
        maxx = max(poly.bounds[2] for poly in shapely_polygons)
        maxy = max(poly.bounds[3] for poly in shapely_polygons)
        return (minx, miny, maxx, maxy)

    def _tile_indices_for_bounding_box(
        self, minx, miny, maxx, maxy, tile_size
    ):
        """
        Given a bounding box and tile size (100 by default),
        yield (ix, iy) indices that cover all polygons.

        We define tiles so that the tile at (0,0) covers x in [-50, 50], y in [-50, 50].
        That means for a tile index (ix, iy), the tile covers:
            x in [ix*100 - 50, ix*100 + 50]
            y in [iy*100 - 50, iy*100 + 50].
        """
        # Figure out what range of indices we need in x and y directions
        # We shift coordinates so that "center" tile is from -50 to 50, etc.
        # Solve for ix such that ix*100 - 50 <= minx  =>  ix <= (minx + 50)/100.
        # But we need integer steps. We'll take floor for start, ceil for end.

        # X range
        ix_min = math.floor(
            (minx + tile_size / 2) / tile_size
        )  # leftmost tile index
        ix_max = math.ceil(
            (maxx + tile_size / 2) / tile_size
        )  # rightmost tile index

        # Y range
        iy_min = math.floor(
            (miny + tile_size / 2) / tile_size
        )  # bottom tile index
        iy_max = math.ceil(
            (maxy + tile_size / 2) / tile_size
        )  # top tile index

        for ix in range(ix_min, ix_max):
            for iy in range(iy_min, iy_max):
                yield ix, iy

    def _clip_polygons_to_tiles(self, shapely_polygons, tile_size, epsilon):
        """
        Main routine:
          1) Find bounding box of all polygons
          2) Figure out which tiles we need
          3) For each tile, intersect with each polygon
          4) Collect non-empty intersections in a result dictionary

        Returns a dict: {
           (ix, iy): [list of clipped Polygons / MultiPolygons within that tile]
        }
        """
        # 1) bounding box
        minx, miny, maxx, maxy = self._get_bounding_box(shapely_polygons)

        # 2) gather tiles
        tile_dict = {}  # (ix, iy) -> list of shapely geometries
        for ix, iy in self._tile_indices_for_bounding_box(
            minx, miny, maxx, maxy, tile_size
        ):
            tile_poly = self._tile_polygon(ix, iy, tile_size, epsilon)
            # 3) intersect with each polygon
            clipped_list = []
            for poly in shapely_polygons:
                intersection = poly.intersection(tile_poly)
                if not intersection.is_empty:
                    clipped_list.append(intersection)
            # Store if we got any intersection
            if clipped_list:
                tile_dict[(ix, iy)] = clipped_list
        return tile_dict

    def _tile_polygons(self, polygons_np, tile_size, epsilon):
        # 1) Convert to shapely Polygons
        shapely_polys = self._polygons_to_shapely(polygons_np)

        # 2) Clip polygons to tiles
        tile_dict = self._clip_polygons_to_tiles(
            shapely_polys, tile_size=tile_size, epsilon=epsilon
        )

        # Print how many tiles we actually used
        print(f"Number of tiles with content: {len(tile_dict)}")
        for tile_idx, clipped_geoms in tile_dict.items():
            print(
                f"Tile {tile_idx} has {len(clipped_geoms)} clipped polygon(s)"
            )

        # OPTIONAL: Visualize result
        if self._plot_tiles_flag:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(8, 8))

            # Draw each tile that has content
            for (ix, iy), geoms in tile_dict.items():
                tile_poly = self._tile_polygon(
                    ix, iy, tile_size=tile_size, epsilon=epsilon
                )
                # Draw tile boundary
                x_tile, y_tile = tile_poly.exterior.xy
                ax.plot(x_tile, y_tile, "k--", alpha=0.3)

                # Draw clipped polygons
                for geom in geoms:
                    if geom.geom_type == "Polygon":
                        x, y = geom.exterior.xy
                        ax.fill(x, y, alpha=0.5)
                        for hole in geom.interiors:
                            xh, yh = hole.xy
                            ax.fill(xh, yh, color="white")
                    elif geom.geom_type == "MultiPolygon":
                        for part in geom.geoms:
                            x, y = part.exterior.xy
                            ax.fill(x, y, alpha=0.5)
                            for hole in part.interiors:
                                xh, yh = hole.xy
                                ax.fill(xh, yh, color="white")

            ax.set_aspect("equal", "box")
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            ax.set_title(
                f"Polygons clipped to {tile_size}um x {tile_size}um tiles"
            )
            plt.grid(True)
            plt.show()

        return tile_dict

    def _extrude_shapely_geometry(self, geometry, thickness):
        """
        Extrude a Shapely geometry (Polygon or MultiPolygon) by 'thickness'
        along the Z-axis and return a Trimesh mesh.
        """
        meshes = []

        # geometry can be Polygon or MultiPolygon
        if geometry.geom_type == "Polygon":
            # Directly extrude
            mesh = trimesh.creation.extrude_polygon(geometry, thickness)
            meshes.append(mesh)

        elif geometry.geom_type == "MultiPolygon":
            # Extrude each sub-polygon
            for poly in geometry.geoms:
                mesh = trimesh.creation.extrude_polygon(poly, thickness)
                meshes.append(mesh)

        # Combine everything into one mesh
        if len(meshes) == 1:
            return meshes[0]
        elif len(meshes) > 1:
            return trimesh.util.concatenate(meshes)
        else:
            # In case geometry was empty, return None or an empty Trimesh
            return None

    def _tile_polygons_2D_extrusion(
        self, extrusion, tile_dict, child_cell, target_layer, skip_if_exists
    ):

        output_folder = f"{self.gds_name}/{child_cell.name}{target_layer}"
        os.makedirs(output_folder, exist_ok=True)

        for (ix, iy), geoms in tile_dict.items():
            # Generate the tile filename and path
            tile_filename = f"tile_{ix}_{iy}.stl"
            tile_filepath = os.path.join(output_folder, tile_filename)

            # Check if the STL file already exists
            if os.path.exists(tile_filepath) and skip_if_exists:
                print(
                    f"Tile {(ix, iy)} already exists at {tile_filepath}, skipping."
                )
                continue

            # List to collect meshes from each geometry
            tile_meshes = []

            # Extrude each geometry in that tile
            for geom in geoms:
                mesh_3d = self._extrude_shapely_geometry(
                    geometry=geom, thickness=extrusion
                )
                if mesh_3d is not None:
                    tile_meshes.append(mesh_3d)

            # Combine (concatenate) all extruded meshes in this tile
            if len(tile_meshes) == 0:
                # No valid geometry in this tile, skip
                continue
            elif len(tile_meshes) == 1:
                tile_mesh_combined = tile_meshes[0]
            else:
                tile_mesh_combined = trimesh.util.concatenate(tile_meshes)

            # Export to STL
            tile_mesh_combined.export(tile_filepath)
            print(f"Exported tile {(ix, iy)} to {tile_filepath}")

    def _meander_order(self, tile_keys):
        """
        Given an iterable of (ix, iy) tile indices,
        return a list of (ix, iy) in a zigzag (meander) order.

        - Sort by ascending y for the rows.
        - For each consecutive row, alternate the x-direction:
            * row0: left-to-right
            * row1: right-to-left
            * row2: left-to-right
            * ...
        """
        # Group the tile indices by their y
        from collections import defaultdict

        rows = defaultdict(list)
        for ix, iy in tile_keys:
            rows[iy].append(ix)

        # Sort the rows by Y ascending
        sorted_ys = sorted(rows.keys())

        # Build the final list of (ix, iy)
        meandered = []
        for row_i, y in enumerate(sorted_ys):
            x_list = sorted(rows[y])
            # If row_i is odd, reverse the list to create the zigzag
            if row_i % 2 == 1:
                x_list.reverse()

            for x in x_list:
                meandered.append((x, y))

        return meandered

    def _tile_center(self, ix, iy, tile_size):
        """
        Return the center of tile (ix, iy) in the same coordinate system
        that was used for clipping (i.e., each tile is tile_size wide/high).
        """
        cx = ix * tile_size
        cy = iy * tile_size
        return (cx, cy)

    def _build_nano_leaf_group(
        self,
        tile_dict,
        tile_size,
        project,
        preset,
        leaf_cell,
        layer_to_print,
        group_xy,
        rotation,
        write_field_scene=None,
        color="#16506B",
    ):
        # 1) Collect tile keys and meander them
        tile_keys = list(tile_dict.keys())
        meandered_keys = self._meander_order(tile_keys)
        if write_field_scene is None:
            write_field_scene = _write_field_scene()
        else:  # Sleep-deprived much? Time to go to bed...
            try:
                if write_field_scene._type != "scene":
                    raise TypeError(
                        "write_field_scene needs to be of node type scene"
                    )
            except:
                write_field_scene = _write_field_scene()
                UserWarning(
                    "Invalid scene. Default write field going to be applied instead."
                )
        # 2) Build Scenes in meander order
        scenes = []
        meshes = []
        for i, (ix, iy) in enumerate(meandered_keys):
            # tile_{ix}_{iy}.stl is our new naming scheme
            stl_filename = f"{self.gds_name}/{leaf_cell.name}{layer_to_print}/tile_{ix}_{iy}.stl"

            # Compute the tile center
            cx, cy = self._tile_center(ix, iy, tile_size=tile_size)

            # Build the Scene, position = [cx, cy, 0]
            scene = write_field_scene.deepcopy_node(
                name=stl_filename
            ).position_at(position=[cx, cy, 0])

            # Build the Mesh object
            # auto_center=True => internally centers the geometry
            mesh_obj = Mesh(
                stl_filename, name=stl_filename, translation=[-cx, -cy, 0]
            )

            # Prepare for the structure
            # (assuming you have your 'preset' object already loaded)
            structure = Structure(
                name=mesh_obj.name, preset=preset, mesh=mesh_obj, color=color
            )

            # Attach structure to the scene
            scene.append_node(structure)

            # Keep references
            scenes.append(scene)
            meshes.append(mesh_obj)

        project.load_resources(meshes)
        leaf_group = Group(
            name=leaf_cell.name,
            position=[*group_xy, 0],
            rotation=[0, 0, rotation],
        )
        leaf_group.add_child(*scenes)
        return leaf_group

    def _cell_has_direct_polygons(
        self, cell: pya.Cell, layer_to_print: int
    ) -> bool:
        """
        Check if a cell directly contains any polygon shapes on a specific layer.

        Args:
            cell: pya.Cell to check
            layer_to_print: Layer index to examine

        Returns:
            True if cell directly contains polygons on this layer, False otherwise
        """
        for shape in cell.shapes(layer_to_print):
            if shape.is_polygon() or shape.is_box():
                return True
        return False

    groups = []

    def _collect_instance_displacements(self, cell):
        displacements = []
        dbu = self.layout.dbu  # Database unit to micron conversion factor

        for instance in cell.each_inst():
            # Extract array parameters (default to 1 if not an array)
            na = instance.na or 1
            nb = instance.nb or 1
            a_vec = (
                instance.a
            )  # Column displacement vector (in database units)
            b_vec = instance.b  # Row displacement vector

            # Base displacement from the instance's transformation
            base_disp_db = instance.trans.disp  # In database units

            # Iterate over all elements in the array
            for i in range(na):
                for j in range(nb):
                    # Compute total displacement for this array element
                    delta = a_vec * i + b_vec * j
                    total_disp_db = base_disp_db + delta

                    # Convert to microns and add to the list
                    total_disp_micron = total_disp_db.to_dtype(dbu)
                    displacements.append(
                        [total_disp_micron.x, total_disp_micron.y]
                    )

        return displacements

    def gds_printing(
        self,
        project,
        preset,
        cell_name=None,
        write_field_scene=None,
        layer_to_print=(1, 1),
        extrusion=1.0,
        tile_size=220,
        epsilon=0.5,
        color="#16506B",
        _verbose=False,
    ):
        gds_printing_group_raw = self._gds_printing(
            project,
            preset,
            cell_name=cell_name,
            write_field_scene=write_field_scene,
            layer_to_print=layer_to_print,
            extrusion=extrusion,
            tile_size=tile_size,
            epsilon=epsilon,
            color=color,
            _verbose=_verbose,
        )

        # Clean up nodes that do not contain any structures
        gds_printing_group = gds_printing_group_raw.deepcopy_node(
            copy_children=False
        )
        for node in gds_printing_group_raw.children_nodes:
            for node_descendant in node.all_descendants:
                if node_descendant._type == "structure":
                    gds_printing_group.add_child(node)
                    break
        return gds_printing_group

        return gds_printing_group

    @verbose_output()
    def _gds_printing(
        self,
        project,
        preset,
        cell_name=None,
        write_field_scene=None,
        layer_to_print=(1, 1),
        extrusion=1.0,
        tile_size=220,
        epsilon=0.5,
        skip_if_exists=False,
        color="#16506B",
        _verbose=False,
    ):
        cell = (
            self.layout.top_cell()
            if cell_name is None
            else self.get_cell_by_name(cell_name)
        )
        print(f"Cell: {cell.name}")
        cell_group = Group(f"Cell: {cell.name} Layer:{layer_to_print}")
        for instance in cell.each_inst():

            # Get the child cell
            child_cell = self.layout.cell(instance.cell_index)

            # Get the transformation of the instance
            trans = instance.trans

            # Extract the displacement vector (relative translation)
            displacement = trans.disp
            rotation = (
                trans.rot * 90
            )  # outputs are ints (0,1,2,3) for multiples of 90 deg
            # Convert the displacement to microns (if needed)
            displacement_in_microns = displacement.to_dtype(self.layout.dbu)

            print(f"Child cell: {child_cell.name}")
            # print(f"Relative displacement (in database units): {displacement}")
            print(
                f"Relative displacement (in microns): {displacement_in_microns.x, displacement_in_microns.y}"
            )
            print("---")

            if self._cell_has_direct_polygons(child_cell, layer_to_print):
                polygons = self._gather_polygons_in_child_cell(
                    child_cell, layer_to_print
                )
                tile_dict = self._tile_polygons(
                    polygons, tile_size=tile_size, epsilon=epsilon
                )
                self._tile_polygons_2D_extrusion(
                    extrusion=extrusion,
                    tile_dict=tile_dict,
                    child_cell=child_cell,
                    target_layer=layer_to_print,
                    skip_if_exists=skip_if_exists,
                )
                child_cell_group = self._build_nano_leaf_group(
                    tile_dict,
                    tile_size,
                    project,
                    preset,
                    child_cell,
                    group_xy=[
                        displacement_in_microns.x,
                        displacement_in_microns.y,
                    ],
                    rotation=rotation,
                    write_field_scene=write_field_scene,
                    layer_to_print=layer_to_print,
                    color=color,
                )

            else:
                child_cell_group = Group(
                    name=child_cell.name,
                    position=[
                        displacement_in_microns.x,
                        displacement_in_microns.y,
                        0,
                    ],
                    rotation=[0, 0, rotation],
                )
                print("No direct polygons found in top cell")

            #  Do NOT assume you could shove this in the if-statement above
            if not child_cell.is_leaf():
                child_cell_group.add_child(
                    self.gds_printing(
                        project,
                        preset,
                        cell=child_cell,
                        write_field_scene=write_field_scene,
                        layer_to_print=layer_to_print,
                        extrusion=extrusion,
                        tile_size=tile_size,
                        epsilon=epsilon,
                        color=color,
                        _verbose=_verbose,
                    )
                )
            else:
                cell_group.add_child(child_cell_group)

                print("LEAF!")

        return cell_group

    def _decompose(self, geometry):
        """Decompose a geometry into a list of Polygon(s)."""
        if isinstance(geometry, MultiPolygon):
            return list(geometry.geoms)
        elif isinstance(geometry, Polygon):
            return [geometry]
        else:
            raise ValueError("Unsupported geometry type")

    def _get_polygon_coords(self, polygon):
        """Extract all coordinates from a polygon (exterior and interiors)."""
        exterior = list(polygon.exterior.coords)
        interiors = []
        for interior in polygon.interiors:
            interiors.extend(interior.coords)
        return np.array(exterior + interiors)

    def _normalize_polygon(self, polygon):
        """Normalize a polygon's position, rotation, and orientation."""
        # Translate to centroid origin
        centroid = polygon.centroid
        translated = translate(polygon, -centroid.x, -centroid.y)

        # Get coordinates for PCA
        coords = self._get_polygon_coords(translated)
        if len(coords) < 2:
            return translated  # Not enough points for PCA

        # Compute PCA to find the principal axis
        centered = coords - np.mean(coords, axis=0)
        cov = np.cov(centered.T)
        eigenvalues, eigenvectors = np.linalg.eig(cov)
        principal = eigenvectors[:, np.argmax(eigenvalues)]
        angle = np.arctan2(principal[1], principal[0])

        # Rotate to align principal axis with x-axis
        rotated = rotate(translated, -np.degrees(angle), origin=(0, 0))

        # Heuristic to ensure consistent orientation (flip if necessary)
        coords_rotated = list(rotated.exterior.coords)
        if len(coords_rotated) >= 2:
            dx = coords_rotated[1][0] - coords_rotated[0][0]
            dy = coords_rotated[1][1] - coords_rotated[0][1]
            if dx < 0 or (dx == 0 and dy < 0):
                # Reflect across x-axis
                return rotate(rotated, 180, origin=(0, 0))
        return rotated

    def _are_geometries_equivalent(self, geom1, geom2, tolerance=1e-6):
        """Check if two geometries are equivalent in shape and size."""
        # Decompose into individual polygons
        polys1 = self._decompose(geom1)
        polys2 = self._decompose(geom2)
        if len(polys1) != len(polys2):
            return False

        # Normalize and sort polygons for comparison
        def sort_key(p):
            return (-p.area, -p.length, list(p.exterior.coords))

        normalized1 = sorted(
            [self._normalize_polygon(p) for p in polys1], key=sort_key
        )
        normalized2 = sorted(
            [self._normalize_polygon(p) for p in polys2], key=sort_key
        )

        # Compare each pair of polygons
        for p1, p2 in zip(normalized1, normalized2):
            if not p1.equals_exact(p2, tolerance):
                return False
        return True

    def _merge_touching_polygons(self, polygons):
        """
        Merge polygons that touch or intersect, including newly formed ones.
        Returns a list of merged geometries (Polygon/MultiPolygon).
        """
        processed = [False] * len(polygons)
        result = []

        for i in range(len(polygons)):
            if not processed[i]:
                # Start a new connected component
                component = [polygons[i]]
                processed[i] = True
                queue = [i]

                # Find all connected polygons using BFS
                while queue:
                    current_idx = queue.pop(0)
                    current_poly = polygons[current_idx]

                    # Check against all other polygons
                    for j in range(len(polygons)):
                        if not processed[j]:
                            other_poly = polygons[j]
                            if current_poly.intersects(other_poly):
                                component.append(other_poly)
                                processed[j] = True
                                queue.append(j)

                # Merge the component into a single geometry
                merged = unary_union(component)
                result.append(merged)

        return result

    def _ensure_folder_exist_else_create(self, path):
        try:
            if os.path.exists(path):
                pass
            else:
                os.makedirs(path)
        except Exception as e:
            print(f"An error occurred: {e}")

    def marker_aligned_printing(
        self,
        project: Project,
        presets: List[Preset],
        meshes: List[Mesh],
        marker_height: float = 0.33,
        marker_layer: Tuple[int, int] = (10, 10),
        mesh_spots_layers: List[Tuple[int, int]] = [(100, 100)],
        cell_origin_offset: Tuple[float, float] = (0.0, 0.0),
        cell_name=None,
        image_resource: Image = None,
        interface_aligner_node: InterfaceAligner = None,
        marker_aligner_node: MarkerAligner = None,
        colors: List[str] = None,
        marker_aligner_kwargs: Dict = {},
        structure_kwargs: Dict = {},
        _verbose=False,
    ) -> Group:

        colors = ["#16506B"] * len(meshes) if colors is None else colors

        # Check all iterables have same length
        if not (
            len(presets)
            == len(meshes)
            == len(mesh_spots_layers)
            == len(colors)
        ):
            raise ValueError(
                "presets, meshes, mesh_spots_layers, (and colors, if any were passed) must all have the same length"
            )

        # Type checking with try-except conversions
        for i, preset in enumerate(presets):
            if not isinstance(preset, Preset):
                raise TypeError(f"presets[{i}] must be of type Preset")

        for i, mesh in enumerate(meshes):
            if not isinstance(mesh, Mesh):
                raise TypeError(f"meshes[{i}] must be of type Mesh")

        for i, spots in enumerate(mesh_spots_layers):
            try:
                if len(spots) != 2 or not isinstance(spots, tuple):
                    raise ValueError
                int(spots[0]), int(spots[1])
            except (ValueError, TypeError):
                raise TypeError(
                    f"mesh_spots_layers[{i}] must be a tuple of two integers"
                )

        for i, color in enumerate(colors):
            try:
                str(color)
            except Exception as e:
                raise TypeError(
                    f"colors[{i}] must be convertible to string: {str(e)}"
                )

        marker_aligned_printing_group_raw = self._marker_aligned_printing(
            project,
            presets,
            meshes,
            cell_name=cell_name,
            cell_origin_offset=cell_origin_offset,
            image_resource=image_resource,
            interface_aligner_node=interface_aligner_node,
            marker_aligner_node=marker_aligner_node,
            marker_height=marker_height,
            marker_layer=marker_layer,
            mesh_spots_layers=mesh_spots_layers,
            colors=colors,
            marker_aligner_kwargs=marker_aligner_kwargs,
            structure_kwargs=structure_kwargs,
            _verbose=_verbose,
        )

        # Clean up nodes that do not contain any structures
        marker_aligned_printing_group = (
            marker_aligned_printing_group_raw.deepcopy_node(
                copy_children=False
            )
        )
        for node in marker_aligned_printing_group_raw.children_nodes:
            for node_descendant in node.all_descendants:
                if node_descendant._type == "structure":
                    marker_aligned_printing_group.add_child(node)
                    break
        return marker_aligned_printing_group.translate(
            [-cell_origin_offset[0], -cell_origin_offset[1], 0]
        )

    # TODO: Consider exchanging marker part with get_marker_aligner()
    @verbose_output()
    def _marker_aligned_printing(
        self,
        project,
        presets,
        meshes,
        marker_height=0.33,
        cell_origin_offset=(0.0, 0.0),
        marker_layer=(10, 10),
        mesh_spots_layers=[(100, 100)],
        cell_name=None,
        image_resource=None,
        interface_aligner_node=None,
        marker_aligner_node=None,
        colors=["#16506B"],
        marker_aligner_kwargs={},
        structure_kwargs={},
        _verbose=False,
    ):
        cell = (
            self.layout.top_cell()
            if cell_name is None
            else self.get_cell_by_name(cell_name)
        )
        print(f"Cell: {cell.name}")
        cell_group = Group(f"Cell: {cell.name} markers:{marker_layer}")
        for instance in cell.each_inst():

            # Get the child cell
            child_cell = self.layout.cell(instance.cell_index)

            # Get the transformation of the instance
            trans = instance.trans

            # Extract the displacement vector (relative translation)
            displacement = trans.disp
            rotation = (
                trans.rot * 90
            )  # outputs are ints (0,1,2,3) for multiples of 90 deg
            # Convert the displacement to microns (if needed)
            displacement_in_microns = displacement.to_dtype(self.layout.dbu)

            print(f"Child cell: {child_cell.name}")
            # print(f"Relative displacement (in database units): {displacement}")
            print(
                f"Relative displacement (in microns): {displacement_in_microns.x, displacement_in_microns.y}"
            )
            print(f"Rotation: {rotation}, type: {type(rotation)}")
            print("---")

            if self._cell_has_direct_polygons(child_cell, marker_layer):
                child_cell_group = Group(
                    name=child_cell.name,
                    position=[
                        displacement_in_microns.x,
                        displacement_in_microns.y,
                        0,
                    ],
                    rotation=[0, 0, rotation],
                )
                image_file_path = f"./images_{self.gds_name}_{marker_layer}/marker_{marker_layer}.png"
                self._ensure_folder_exist_else_create(
                    f"./images_{self.gds_name}_{marker_layer}"
                )
                scene = Scene(name=child_cell.name)

                polygons = self._gather_polygons_in_child_cell(
                    child_cell, marker_layer
                )
                shapely_polygons = self._polygons_to_shapely(polygons)
                marker_polygons = self._merge_touching_polygons(
                    shapely_polygons
                )
                _, marker_orientations = (
                    self._group_equivalent_polygons_and_output_image(
                        marker_polygons, file_path=image_file_path
                    )
                )

                _image = (
                    Image(name=f"{marker_layer}", file_path=image_file_path)
                    if image_resource is None
                    else image_resource
                )
                if (
                    self._previous_image_safe_path_marker_aligned_printing.split(
                        "/"
                    )[
                        1
                    ]
                    != _image.safe_path.split("/")[1]
                ):

                    self._image = (
                        Image(
                            name=f"{marker_layer}", file_path=image_file_path
                        )
                        if image_resource is None
                        else image_resource
                    )
                    self._previous_image_safe_path_marker_aligned_printing = (
                        self._image.safe_path
                    )
                    project.load_resources(self._image)

                marker_size = [
                    marker_polygons[0].bounds[2]
                    - marker_polygons[0].bounds[0],
                    marker_polygons[0].bounds[3]
                    - marker_polygons[0].bounds[1],
                ]
                marker_positions = [
                    [m_pol.centroid.x, m_pol.centroid.y, marker_height]
                    for m_pol in marker_polygons
                ]

                if "max_outliers" not in marker_aligner_kwargs:
                    marker_aligner_kwargs["max_outliers"] = (
                        len(marker_positions) - 3
                        if len(marker_positions) >= 3
                        else 0
                    )
                marker_aligner = (
                    MarkerAligner(
                        name=f"{marker_layer}",
                        image=self._image,
                        marker_size=marker_size,
                        **marker_aligner_kwargs,
                    )
                    if marker_aligner_node is None
                    else marker_aligner_node.deepcopy_node()
                )

                marker_aligner.set_markers_at(
                    positions=marker_positions,
                    orientations=marker_orientations,
                )

                for mesh, preset, mesh_spots_layer, color in zip(
                    meshes, presets, mesh_spots_layers, colors
                ):
                    if self._cell_has_direct_polygons(
                        child_cell, mesh_spots_layer
                    ):
                        mesh_spots_polygons = (
                            self._gather_polygons_in_child_cell(
                                child_cell, mesh_spots_layer
                            )
                        )
                        mesh_spots_shapely_polygons = (
                            self._polygons_to_shapely(mesh_spots_polygons)
                        )
                        structures = [
                            Structure(
                                mesh=mesh,
                                preset=preset,
                                name=mesh.name,
                                position=[
                                    mesh_spot_shapely_polygon.centroid.x,
                                    mesh_spot_shapely_polygon.centroid.y,
                                    0,
                                ],
                                color=color,
                                **structure_kwargs,
                            )
                            for mesh_spot_shapely_polygon in mesh_spots_shapely_polygons
                        ]
                        marker_aligner.add_child(*structures)

                interface_aligner = (
                    InterfaceAligner()
                    if interface_aligner_node is None
                    else interface_aligner_node.deepcopy_node()
                )

                cell_origin_offset_group = Group(
                    name="cell_origin_offset",
                    position=[
                        cell_origin_offset[0],
                        cell_origin_offset[1],
                        0,
                    ],
                )
                child_cell_group.append_node(
                    scene,
                    interface_aligner,
                    cell_origin_offset_group,
                    marker_aligner,
                )

            else:
                child_cell_group = Group(
                    name=child_cell.name,
                    position=[
                        displacement_in_microns.x,
                        displacement_in_microns.y,
                        0,
                    ],
                    rotation=[0, 0, rotation],
                )
                print("No direct polygons found in top cell")

            #  Do NOT assume you could shove this in the if-statement above
            if not child_cell.is_leaf():
                cell_group.add_child(child_cell_group)
                child_cell_group.add_child(
                    self.marker_aligned_printing(
                        project,
                        presets,
                        meshes,
                        cell=child_cell,
                        image_resource=image_resource,
                        interface_aligner_node=interface_aligner_node,
                        marker_aligner_node=marker_aligner_node,
                        marker_height=marker_height,
                        marker_layer=marker_layer,
                        mesh_spots_layers=mesh_spots_layers,
                        colors=colors,
                        marker_aligner_kwargs=marker_aligner_kwargs,
                        structure_kwargs=structure_kwargs,
                        _verbose=_verbose,
                    )
                )

            else:
                cell_group.add_child(child_cell_group)

                print("LEAF!")

        return cell_group

    def _get_geometry_coords(self, geometry):
        """Extract all coordinates from a geometry (Polygon or MultiPolygon)."""
        coords = []
        if isinstance(geometry, MultiPolygon):
            for polygon in geometry.geoms:
                exterior = list(polygon.exterior.coords)
                coords.extend(exterior)
                for interior in polygon.interiors:
                    coords.extend(interior.coords)
        elif isinstance(geometry, Polygon):
            exterior = list(geometry.exterior.coords)
            coords.extend(exterior)
            for interior in geometry.interiors:
                coords.extend(interior.coords)
        else:
            raise ValueError("Unsupported geometry type")
        return np.array(coords)

    def _normalize_geometry_with_rotation(self, geometry):
        """Normalize a geometry and return the normalized version and rotation applied."""
        centroid = geometry.centroid
        translated = translate(geometry, -centroid.x, -centroid.y)

        coords = self._get_geometry_coords(translated)
        if len(coords) < 2:
            return translated, 0.0

        centered = coords - np.mean(coords, axis=0)
        cov = np.cov(centered.T)
        eigenvalues, eigenvectors = np.linalg.eig(cov)
        principal = eigenvectors[:, np.argmax(eigenvalues)]
        angle_rad = np.arctan2(principal[1], principal[0])
        angle_deg = np.degrees(angle_rad)
        rotated1 = rotate(translated, -angle_deg, origin=(0, 0))

        # Check orientation
        if isinstance(rotated1, MultiPolygon):
            first_poly = rotated1.geoms[0]
            coords_rotated = list(first_poly.exterior.coords)
        else:
            coords_rotated = list(rotated1.exterior.coords)

        flip = False
        if len(coords_rotated) >= 2:
            dx = coords_rotated[1][0] - coords_rotated[0][0]
            dy = coords_rotated[1][1] - coords_rotated[0][1]
            if dx < 0 or (dx == 0 and dy < 0):
                flip = True

        if flip:
            rotated_final = rotate(rotated1, 180, origin=(0, 0))
            total_rotation = -angle_deg + 180
        else:
            rotated_final = rotated1
            total_rotation = -angle_deg

        return rotated_final, total_rotation

    def _group_equivalent_polygons_and_output_image(
        self, polygons, tolerance=1e-6, file_path="./images/marker.png"
    ):
        """
        Groups polygons into equivalence classes based on shape and size, ignoring position and rotation.
        Returns unique representatives and their relative orientations.
        """
        groups = []  # Each entry is (original_geo, rotation, normalized_geo)
        angle_groups = []

        for geo in polygons:
            normalized, rotation = self._normalize_geometry_with_rotation(geo)
            found = False
            for i, (orig_rep, rot_rep, norm_rep) in enumerate(groups):
                if self._are_geometries_equivalent(
                    normalized, norm_rep, tolerance
                ):
                    rel_angle = (rot_rep - rotation) % 360.0
                    angle_groups[i].append(rel_angle)
                    found = True
                    break
            if not found:
                groups.append((geo, rotation, normalized))
                angle_groups.append([0.0])

        unique_geometries = [orig_rep for orig_rep, _, _ in groups]

        # Generate Image for MarkerAligner
        self._save_geometry_as_png(unique_geometries[0], output_file=file_path)

        return unique_geometries, angle_groups[0]  # TODO: Fix this maybe?

    def _calculate_bounds(self, geometry):
        """
        Calculate the bounding box of a Shapely Polygon or MultiPolygon.
        """
        if isinstance(geometry, MultiPolygon):
            # Get bounds for all polygons in the MultiPolygon
            bounds = [polygon.bounds for polygon in geometry.geoms]
            min_x = min(b[0] for b in bounds)
            min_y = min(b[1] for b in bounds)
            max_x = max(b[2] for b in bounds)
            max_y = max(b[3] for b in bounds)
            return min_x, min_y, max_x, max_y
        elif isinstance(geometry, Polygon):
            # Get bounds for a single Polygon
            return geometry.bounds
        else:
            raise ValueError(
                "Unsupported geometry type. Expected Polygon or MultiPolygon."
            )

    def _rescale_coords(self, coords, min_x, min_y, scaling_factor):
        """
        Rescale coordinates based on a scaling factor.
        """
        return [
            ((x - min_x) * scaling_factor, (y - min_y) * scaling_factor)
            for x, y in coords
        ]

    def _draw_polygon(
        self, draw, polygon, min_x, min_y, scaling_factor, fill_color
    ):
        """
        Draw a rescaled polygon (with holes) on an image.
        """
        # Rescale and draw the exterior
        rescaled_exterior = self._rescale_coords(
            polygon.exterior.coords, min_x, min_y, scaling_factor
        )
        draw.polygon(rescaled_exterior, fill=fill_color)

        # Rescale and draw the holes (interiors)
        for interior in polygon.interiors:
            rescaled_interior = self._rescale_coords(
                interior.coords, min_x, min_y, scaling_factor
            )
            draw.polygon(rescaled_interior, fill="white")

    def _save_geometry_as_png(
        self,
        geometry,
        target_resolution=600,
        output_file="output.png",
        fill_color="black",
    ):
        """
        Save a Shapely Polygon or MultiPolygon as a PNG image.
        """
        # Calculate the bounds of the geometry
        min_x, min_y, max_x, max_y = self._calculate_bounds(geometry)

        # Calculate the width and height of the bounding box
        width = max_x - min_x
        height = max_y - min_y

        # Determine the scaling factor to fit the geometry into the target resolution
        scaling_factor = min(
            target_resolution / width, target_resolution / height
        )

        # Calculate the new image size based on the scaling factor
        new_width = int(width * scaling_factor)
        new_height = int(height * scaling_factor)

        # Create a blank image with a white background
        image = PIL.Image.new("RGB", (new_width, new_height), "white")
        draw = PIL.ImageDraw.Draw(image)

        # Draw each polygon in the MultiPolygon (or the single Polygon)
        if isinstance(geometry, MultiPolygon):
            for polygon in geometry.geoms:
                self._draw_polygon(
                    draw, polygon, min_x, min_y, scaling_factor, fill_color
                )
        else:
            self._draw_polygon(
                draw, geometry, min_x, min_y, scaling_factor, fill_color
            )

        # Save the image as a PNG file
        image.save(output_file)
        print(f"Image saved as {output_file}")

    def get_cell_by_name(self, cell_name: str):
        """
        Retrieves a cell by its name.

        Args:
            cell_name (str): Name of the cell to retrieve.

        Returns:
            pya.Cell: The cell object if found, otherwise None.
        """
        # Iterate through all cells in the layout
        for cell in self.layout.each_cell():
            if cell.name == cell_name:
                return cell  # Return the cell if its name matches

        # If the cell is not found, return None
        return None

    def _merged_polygons_and_their_positions(self, child_cell, layer, z_pos):

        polygons = self._gather_polygons_in_child_cell(child_cell, layer)
        shapely_polygons = self._polygons_to_shapely(polygons)
        merged_polygons = self._merge_touching_polygons(shapely_polygons)

        positions = [
            [m_pol.centroid.x, m_pol.centroid.y, z_pos]
            for m_pol in merged_polygons
        ]
        return merged_polygons, positions

    def get_marker_aligner(
        self,
        cell_name,
        project=None,
        marker_layer=(254, 254),
        marker_height=0.33,
        image_resource=None,
        **marker_aligner_kwargs,
    ):
        cell = self.get_cell_by_name(cell_name)
        marker_polygons, marker_positions = (
            self._merged_polygons_and_their_positions(
                cell, marker_layer, marker_height
            )
        )

        image_file_path = f"./images_{self.gds_name}_{marker_layer}/marker_{marker_layer}.png"
        self._ensure_folder_exist_else_create(
            f"./images_{self.gds_name}_{marker_layer}"
        )

        _image = (
            Image(name=f"{marker_layer}", file_path=image_file_path)
            if image_resource is None
            else image_resource
        )
        if project is not None:
            project.load_resources(_image)

        _, marker_orientations = (
            self._group_equivalent_polygons_and_output_image(
                marker_polygons, file_path=image_file_path
            )
        )

        marker_size = [
            marker_polygons[0].bounds[2] - marker_polygons[0].bounds[0],
            marker_polygons[0].bounds[3] - marker_polygons[0].bounds[1],
        ]

        if "max_outliers" not in marker_aligner_kwargs:
            marker_aligner_kwargs["max_outliers"] = (
                len(marker_positions) - 3 if len(marker_positions) >= 3 else 0
            )
        marker_aligner = MarkerAligner(
            name=f"{marker_layer}",
            image=_image,
            marker_size=marker_size,
            **marker_aligner_kwargs,
        )

        marker_aligner.set_markers_at(
            positions=marker_positions,
            orientations=marker_orientations,
        )

        return marker_aligner

    def get_coarse_aligner(
        self, cell_name, coarse_layer=(200, 200), residual_threshold=10.0
    ):
        cell = self.get_cell_by_name(cell_name)
        _, anchor_positions = self._merged_polygons_and_their_positions(
            cell, coarse_layer, 0
        )
        coarse_aligner = CoarseAligner(
            name=f"{cell.name}{coarse_layer}",
            residual_threshold=residual_threshold,
        )
        coarse_aligner.set_coarse_anchors_at(anchor_positions)
        return coarse_aligner

    def get_custom_interface_aligner(
        self,
        cell_name,
        interface_layer=(255, 255),
        scan_area_sizes=None,
        **interface_aligner_kwargs,
    ):
        cell = self.get_cell_by_name(cell_name)
        scan_area_sizes_polygons, anchor_positions = (
            self._merged_polygons_and_their_positions(cell, interface_layer, 0)
        )

        scan_area_sizes = (
            [
                [
                    scan_area_sizes_polygons[i].bounds[2]
                    - scan_area_sizes_polygons[i].bounds[0],
                    scan_area_sizes_polygons[i].bounds[3]
                    - scan_area_sizes_polygons[i].bounds[1],
                ]
                for i in range(len(scan_area_sizes_polygons))
            ]
            if scan_area_sizes is None
            else scan_area_sizes
        )

        interface_aligner = InterfaceAligner(
            name=f"{cell.name}{interface_layer}", **interface_aligner_kwargs
        )
        interface_aligner.set_interface_anchors_at(
            positions=anchor_positions, scan_area_sizes=scan_area_sizes
        )
        return interface_aligner
