# -*- coding: utf-8 -*-
"""
npxpy.gds
Created on Fri Feb 21 15:54:24 2025

@author: Caghan Uenlueer
Neuromorphic Quantumphotonics
Heidelberg University
E-Mail:	caghan.uenlueer@kip.uni-heidelberg.de

This file is part of npxpy, which is licensed under the MIT License.
"""
import os
import math
import sys
from typing import List, Dict, Tuple, Optional, Callable, Any
from io import StringIO
from functools import wraps
from inspect import signature
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

# Dependency management with improved error reporting
_MISSING_DEPS: List[str] = []
_HAS_PYA = False

try:
    import pya

    _HAS_PYA = True
except ImportError as e:
    raise ImportError(
        "Missing required dependency: 'pya' (Python for KLayout API).\n"
        "Install with: pip install npxpy[gds]\n"
        "or: pip install npxpy[all]"
    ) from e

try:
    import numpy as np

    _HAS_NUMPY = True
except ImportError:
    np = None
    _MISSING_DEPS.append("numpy")

try:
    from shapely.geometry import Polygon, MultiPolygon, box
    from shapely.affinity import translate, rotate
    from shapely.affinity import scale as shapely_scale
    from shapely.ops import unary_union

    _HAS_SHAPELY = True
except ImportError:
    Polygon = MultiPolygon = box = translate = rotate = unary_union = None
    _MISSING_DEPS.append("shapely")

try:
    import trimesh

    _HAS_TRIMESH = True
except ImportError:
    trimesh = None
    _MISSING_DEPS.append("trimesh")

try:
    import PIL

    _HAS_PIL = True
except ImportError:
    PIL = None
    _MISSING_DEPS.append("PIL")


def verbose_output(verbose_param: str = "_verbose") -> Callable:
    """Decorator to suppress print statements based on verbosity flag.

    Args:
        verbose_param: Name of the verbosity parameter in the decorated function

    Returns:
        Callable: Decorated function with output suppression
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Callable:
            sig = signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            verbose: bool = bound_args.arguments.get(verbose_param, False)

            original_stdout = sys.stdout
            if not verbose:
                sys.stdout = StringIO()

            try:
                result = func(*args, **kwargs)
                if not verbose:
                    sys.stdout.getvalue()  # Consume captured output
                return result
            finally:
                sys.stdout = original_stdout

        return wrapper

    return decorator


class _write_field_scene(Scene):
    """Custom scene configuration for write field operations."""

    def __init__(self) -> None:
        """Initialize a default write field scene with interface aligner."""
        super().__init__(name="default_write_field")
        ia = InterfaceAligner(signal_type="auto", measure_tilt=True)
        ia.set_grid(count=[2, 2], size=[180.0, 180.0])
        self.add_child(ia)


class GDSParser:
    """Parser for GDSII layout files with dependency management and validation.

    Attributes:
        gds_file (str): Path to the loaded GDSII file
        layout (pya.Layout): Parsed GDSII layout object
        gds_name (str): Base name of the GDS file without extension
    """

    _REQUIRED_DEPS: List[str] = ["numpy", "shapely", "trimesh", "PIL"]

    def __init__(self, gds_file: str) -> None:
        """Initialize GDS parser with file validation and dependency checks.

        Args:
            gds_file: Path to GDSII file to load

        Raises:
            ImportError: If required dependencies are missing
            FileNotFoundError: If specified file doesn't exist
            ValueError: For invalid file types or parsing errors
        """
        self.gds_file = gds_file  # Validated through property setter
        self._layout = pya.Layout()
        self._layout.read(gds_file)  # Let pya exceptions bubble up
        self._plot_tiles_flag = False
        self._previous_image_safe_path_marker_aligned_printing = "0/0"
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """Verify required dependencies are installed.

        Raises:
            ImportError: With list of missing dependencies
        """
        missing = [dep for dep in self._REQUIRED_DEPS if dep in _MISSING_DEPS]
        if missing:
            raise ImportError(
                f"Missing required dependencies: {', '.join(missing)}\n"
                "Install either with: pip install npxpy[gds]\n"
                "or with: pip install npxpy[all]"
            )

    @property
    def gds_file(self) -> str:
        """Get path to loaded GDS file."""
        return self._gds_file

    @property
    def layout(self) -> pya.Layout:
        """Get parsed GDS layout object."""
        return self._layout

    @property
    def gds_name(self) -> str:
        """Get base name of GDS file without extension."""
        base = os.path.basename(self.gds_file)
        return os.path.splitext(base)[0]

    @gds_file.setter
    def gds_file(self, value: str) -> None:
        """Validate and set new GDS file path.

        Args:
            value: Path to new GDS file

        Raises:
            TypeError: For non-string input
            FileNotFoundError: If file doesn't exist
            ValueError: For non-GDS file extension
        """
        if not isinstance(value, str):
            raise TypeError(f"Expected string path, got {type(value)}")

        norm_path = os.path.normpath(value)
        if not os.path.isfile(norm_path):
            raise FileNotFoundError(f"GDS file not found: {norm_path}")

        if not value.lower().endswith(".gds"):
            raise ValueError("File must have .gds extension")

        self._gds_file = norm_path

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

    def _extrude_shapely_geometry(
        self,
        geometry,
        thickness,
        hollow=False,
        hollow_scale=0.9,
        hollow_shift_z=0.0,
    ):
        """
        Extrude a Shapely geometry (Polygon or MultiPolygon) into a Trimesh mesh.
        Optionally create a hollow mesh by scaling and shifting an inner copy.

        Args:
            geometry: Shapely Polygon or MultiPolygon.
            thickness: Z-axis extrusion height.
            hollow: If True, generate a hollow mesh (default: False).
            hollow_scale: Scaling factor for inner geometry (0 < scale < 1).
            hollow_shift_z: Z-axis shift for inner geometry (relative to base).

        Returns:
            Trimesh mesh or None if geometry is empty.
        """

        # Validate hollow parameters
        if hollow:
            if hollow_scale <= 0 or hollow_scale >= 1:
                raise ValueError(
                    "hollow_scale must be between 0 and 1 (exclusive)"
                )
            if not (-thickness <= hollow_shift_z <= thickness):
                raise ValueError(
                    "hollow_shift_z must be within [-thickness, thickness]"
                )

        # Create the original solid mesh
        meshes = []
        if geometry.geom_type == "Polygon":
            mesh = trimesh.creation.extrude_polygon(geometry, thickness)
            meshes.append(mesh)
        elif geometry.geom_type == "MultiPolygon":
            for poly in geometry.geoms:
                mesh = trimesh.creation.extrude_polygon(poly, thickness)
                meshes.append(mesh)

        if not meshes:
            return None  # Empty geometry

        outer_mesh = (
            meshes[0] if len(meshes) == 1 else trimesh.util.concatenate(meshes)
        )

        # Early return if not hollow
        if not hollow:
            return outer_mesh

        # Create inner geometry (scaled)
        if geometry.geom_type == "Polygon":
            inner_geom = shapely_scale(
                geometry,
                xfact=hollow_scale,
                yfact=hollow_scale,
                origin="center",
            )
        else:  # MultiPolygon
            inner_geoms = [
                shapely_scale(
                    poly,
                    xfact=hollow_scale,
                    yfact=hollow_scale,
                    origin="center",
                )
                for poly in geometry.geoms
            ]
            inner_geom = (
                MultiPolygon(inner_geoms)
                if len(inner_geoms) > 1
                else inner_geoms[0]
            )

        # Extrude inner geometry and apply Z-shift
        inner_meshes = []
        if inner_geom.geom_type == "Polygon":
            inner_mesh = trimesh.creation.extrude_polygon(
                inner_geom, thickness
            )
            inner_meshes.append(inner_mesh)
        elif inner_geom.geom_type == "MultiPolygon":
            for poly in inner_geom.geoms:
                inner_mesh = trimesh.creation.extrude_polygon(poly, thickness)
                inner_meshes.append(inner_mesh)

        if not inner_meshes:
            return outer_mesh  # Fallback if inner geometry is empty

        inner_mesh = (
            inner_meshes[0]
            if len(inner_meshes) == 1
            else trimesh.util.concatenate(inner_meshes)
        )
        inner_mesh.apply_translation([0, 0, hollow_shift_z])

        # Boolean subtraction (hollowing)
        try:
            hollow_mesh = outer_mesh.difference(inner_mesh, engine="blender")
            return hollow_mesh
        except Exception:
            # Fallback to solid mesh if boolean operation fails
            return outer_mesh

    def gds_printing(
        self,
        project: Project,
        preset: Preset,
        cell_name: Optional[str] = None,
        write_field_scene: Optional[Scene] = None,
        layer: Tuple[int, int] = (1, 0),
        epsilon: float = 1.0,
        tile_size: Tuple[float, float] = (200.0, 200.0),
        extrusion: float = 20.0,
        skip_if_exists: bool = False,
        color: str = "#16506B",
        iterate_over_each_polygon: bool = False,
        hollow: bool = False,
        hollow_scale: float = 0.9,
        hollow_shift_z: float = -2.0,
        layer_to_print=None,
        _verbose: bool = False,
    ) -> Group:
        """
        Process GDS layout to generate tiled scenes for 3D printing.

        This method processes a GDS layout, divides it into tiles, creates 3D extrusions
        from the polygons, and generates scenes for each tile with appropriate positioning.

        Args:
            project: Project instance to which generated meshes are loaded to.
            preset: Preset instance for printing.
            cell_name: Name of the cell in GDS to process.
            write_field_scene: Scene template for writing fields.
            layer: Layer containing polygons that are supposed to be extruded and printed.
            extrusion: Thickness for 3D extrusion.
            tile_size: Size of each tile in micrometers.
            epsilon: Overlap value between tiles in micrometers.
            skip_if_exists: Skip processing if output files already exist.
            color: Color for generated structures in viewer.
            iterate_over_each_polygon: Tile each polygon individually if True
            hollow: Create hollow structures if True
            hollow_scale: Scaling factor for hollow structures
            hollow_shift_z: Z-axis shift for hollow structures
            _verbose: Verbose output flag (for debugging/developing)

        Returns:
            Group: Group instance containing all generated tile scenes.

        Raises:
            ValueError: Invalid input parameters
            TypeError: Incorrect argument types
            RuntimeError: Polygon processing failure
        """
        # Input validation
        if not isinstance(project, Project):
            raise TypeError("project must be a Project instance")
        if not isinstance(preset, Preset):
            raise TypeError("preset must be a Preset instance")
        if cell_name is not None and not isinstance(cell_name, str):
            raise TypeError("cell_name must be a string or None")
        if write_field_scene is not None and not isinstance(
            write_field_scene, Scene
        ):
            raise TypeError(
                "write_field_scene must be a Scene instance or None"
            )
        if layer == (1, 0) and layer_to_print is not None:
            DeprecationWarning(
                "Argument layer_to_print is deprecated and will "
                "be removed in a future release. Use layer instead."
            )
            layer = layer_to_print
        elif layer_to_print is not None:
            DeprecationWarning(
                "Argument layer_to_print is deprecated and will be removed "
                "in a future release. Argument layer will be used instead. "
            )
        # Validate layer_to_print structure and content
        if not isinstance(layer, tuple) or len(layer) != 2:
            raise TypeError("layer must be a tuple of two integers")
        if not all(isinstance(x, int) for x in layer):
            raise TypeError("Both elements in layer must be integers")

        # Validate numerical parameters
        if not isinstance(extrusion, (int, float)):
            raise TypeError("extrusion must be a numeric value")
        if not isinstance(tile_size, tuple) or len(layer) != 2:
            raise TypeError("tile_size must be a tuple of two integers")
        if not all(isinstance(x, (int, float)) for x in tile_size):
            raise TypeError(
                "All elements in tile_size must be numbers (int or float)"
            )
        if not all(x > 0 for x in tile_size):
            raise ValueError("All elements in tile_size must be positive")

        if not isinstance(epsilon, (int, float)):
            raise TypeError("epsilon must be a numeric value")
        if epsilon < 0:
            raise ValueError("epsilon must be non-negative")
        if not isinstance(hollow_scale, (int, float)):
            raise TypeError(
                "hollow_scale must be a numeric value between 0 and 1."
            )
        if hollow_scale < 0 or hollow_scale > 1:
            raise TypeError(
                "hollow_scale must be a numeric value between 0 and 1."
            )
        if not isinstance(hollow_shift_z, (int, float)):
            raise TypeError("hollow_shift_z must be a numeric value.")

        # Validate boolean parameters
        if not isinstance(skip_if_exists, bool):
            raise TypeError("skip_if_exists must be a boolean")
        if not isinstance(iterate_over_each_polygon, bool):
            raise TypeError("iterate_over_each_polygon must be a boolean")
        if not isinstance(hollow, bool):
            raise TypeError("hollow must be a boolean")
        if not isinstance(_verbose, bool):
            raise TypeError("_verbose must be a boolean")

        gds_printing_group = self._gds_printing_new(
            project,
            preset,
            cell_name=cell_name,
            write_field_scene=write_field_scene,
            layer=layer,
            extrusion=extrusion,
            hollow=hollow,
            hollow_scale=hollow_scale,
            hollow_shift_z=hollow_shift_z,
            tile_size=tile_size,
            epsilon=epsilon,
            skip_if_exists=skip_if_exists,
            color=color,
            iterate_over_each_polygon=iterate_over_each_polygon,
            _verbose=_verbose,
        )

        return gds_printing_group

    @verbose_output()
    def _gds_printing_new(
        self,
        project: Project,
        preset: Preset,
        cell_name: Optional[str] = None,
        write_field_scene: Optional[Scene] = None,
        layer: Tuple[int, int] = (1, 0),
        epsilon: float = 1.0,
        tile_size: Tuple[float, float] = (200.0, 200.0),
        extrusion: float = 20.0,
        skip_if_exists: bool = False,
        color: str = "#16506B",
        iterate_over_each_polygon: bool = True,
        hollow: bool = True,
        hollow_scale: float = 0.9,
        hollow_shift_z: float = -2.0,
        _verbose: bool = False,
    ) -> Group:
        """
        Process GDS layout to generate tiled scenes for 3D printing.

        This method processes a GDS layout, divides it into tiles, creates 3D extrusions
        from the polygons, and generates scenes for each tile with appropriate positioning.

        Args:
            project: Project configuration object
            preset: Preset configuration for structures
            cell_name: Name of the cell to process (optional)
            write_field_scene: Scene template for writing fields (optional)
            layer: Layer specification to process
            epsilon: Overlap value between tiles
            tile_size: Size of each tile in micrometers
            extrusion: Thickness for 3D extrusion
            skip_if_exists: Skip processing if output files already exist
            color: Color for generated structures
            iterate_over_each_polygon: Process each polygon individually if True
            hollow: Create hollow structures if True
            hollow_scale: Scaling factor for hollow structures
            hollow_shift_z: Z-axis shift for hollow structures
            _verbose: Verbose output flag

        Returns:
            Group: Group containing all generated tiled scenes
        """
        # Load the GDS file
        #        self.layout.read(self.gds_path)

        # Get the specified layer
        layer_index = self.layout.layer(*layer)
        gds_name = os.path.splitext(os.path.basename(self.gds_file))[0]

        # Get the top cell
        top_cell = (
            self.layout.top_cell()
            if cell_name is None
            else self.get_cell_by_name(cell_name=cell_name)
        )

        shapes_iter = top_cell.begin_shapes_rec(layer_index)
        tiles = []
        results = []
        meshes_npx = []
        scenes_npx = []
        output_group = Group(
            name=gds_name
            + "_"
            + top_cell.name
            + f"_layer_{layer[0]}_{layer[1]}"
        )

        # Check if passed write field is a valid scene
        if write_field_scene is None:
            write_field_scene = _write_field_scene()
        elif write_field_scene._type != "scene":
            write_field_scene = _write_field_scene()
            UserWarning(
                "Invalid scene. Default write field going to be applied instead."
            )

        # Convert from um to dbu
        epsilon_dbu = epsilon * 1000
        tile_size_dbu = (tile_size[0] * 1000, tile_size[1] * 1000)

        # Create a region from all shapes on the layer
        region_all = pya.Region(shapes_iter)
        iterable = region_all.each() if iterate_over_each_polygon else [0]

        for poly in iterable:
            # Get the region to process
            if iterate_over_each_polygon:
                region = pya.Region(poly)
            else:
                region = region_all

            bbox = region.bbox()
            x_min, y_min = bbox.left, bbox.bottom
            x_max, y_max = bbox.right, bbox.top

            # Calculate number of tiles needed
            tile_width, tile_height = tile_size_dbu
            num_x = int(np.ceil((x_max - x_min) / (tile_width - epsilon_dbu)))
            num_y = int(np.ceil((y_max - y_min) / (tile_height - epsilon_dbu)))

            # Generate tiles in meander order
            for j in range(num_y):
                # Alternate direction for meander pattern
                x_indices = (
                    range(num_x) if j % 2 == 0 else reversed(range(num_x))
                )

                for i in x_indices:
                    # Calculate tile boundaries with overlap
                    x1 = x_min + i * (tile_width - epsilon_dbu)
                    y1 = y_min + j * (tile_height - epsilon_dbu)
                    x2 = x1 + tile_width
                    y2 = y1 + tile_height

                    # Create tile box
                    tile_box = pya.Box(x1, y1, x2, y2)
                    tiles.append((i, j, tile_box))

            # Process each tile
            for i, j, tile_box in tiles:
                # Create region for the tile
                tile_region = pya.Region(tile_box)

                # Extract polygons that intersect with the tile
                extracted = region & tile_region

                # Merge overlapping/adjacent polygons
                extracted.merge()

                # Skip empty tiles
                if extracted.is_empty():
                    continue

                # Convert to Shapely polygons
                shapely_polygons = []
                for poly in extracted.each():
                    # Get polygon points
                    points = []
                    for point in poly.each_point_hull():
                        points.append((point.x / 1000, point.y / 1000))

                    # Create Shapely polygon (close the ring if needed)
                    if points[0] != points[-1]:
                        points.append(points[0])

                    shapely_polygons.append(Polygon(points))

                # Create MultiPolygon from all polygons in the tile
                multipolygon = MultiPolygon(shapely_polygons)

                # Calculate tile center
                center_x = extracted.bbox().center().x / 1000
                center_y = extracted.bbox().center().y / 1000

                # Create 3D extrusions/meshes
                tile_meshes = []
                mesh_3d = self._extrude_shapely_geometry(
                    geometry=multipolygon,
                    thickness=extrusion,
                    hollow=hollow,
                    hollow_scale=hollow_scale,
                    hollow_shift_z=hollow_shift_z,
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
                output_folder = (
                    f"{gds_name}/{top_cell.name}{layer}_ext{extrusion}"
                )
                os.makedirs(output_folder, exist_ok=True)

                tile_filename = (
                    f"tile_{i}_{j}_center_{int(center_x)}_{int(center_y)}.stl"
                )
                tile_filepath = os.path.join(output_folder, tile_filename)

                # Check if the STL file already exists and export if not
                if os.path.exists(tile_filepath) and skip_if_exists:
                    print(
                        f"Tile {(i, j)} already exists at {tile_filepath}, skipping."
                    )
                else:
                    tile_mesh_combined.export(tile_filepath)

                # npx-API goes below here
                mesh_npx = Mesh(
                    file_path=tile_filepath,
                    name=tile_filename.split(".")[0],
                    auto_center=True,
                )
                meshes_npx.append(mesh_npx)
                structure_npx = Structure(
                    preset,
                    mesh_npx,
                    name=tile_filename.split(".")[0],
                    color=color,
                )
                scene_npx = write_field_scene.deepcopy_node(name=mesh_npx.name)
                scene_npx.position = [center_x, center_y, 0]
                scene_npx.append_node(structure_npx)
                scenes_npx.append(scene_npx)

                # Add to results (not part of any npx-related things)
                results.append(((i, j), (center_x, center_y), multipolygon))

        output_group.add_child(*scenes_npx)

        # Print information about each tile if verbose
        for (i, j), center, multipolygon in results:
            print(f"Tile ({i}, {j}) at center {center}:")
            print(f"  Contains {len(multipolygon.geoms)} polygons")
            print(f"  Total area: {multipolygon.area}")
            print()
        project.load_resources(meshes_npx)
        return output_group

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

    @verbose_output()
    def get_scenes(
        self,
        scene_layer: Tuple[int, int],
        project: Project,
        presets: Optional[List[Preset]] = None,
        meshes: Optional[List[Mesh]] = None,
        marker_layer: Optional[Tuple[int, int]] = None,
        marker_region_layer: Optional[Tuple[int, int]] = None,
        marker_height: float = 0.33,
        image_resource: Optional[str] = None,
        marker_aligner_node: Optional[MarkerAligner] = None,
        interface_aligner_node: Optional[InterfaceAligner] = None,
        interface_aligner_layer: Optional[Tuple[int, int]] = None,
        mesh_spots_layers: Optional[List[Tuple[int, int]]] = None,
        cell_name: Optional[str] = None,
        colors: Optional[List[str]] = None,
        structure_kwargs: Optional[Dict[str, Any]] = None,
        remove_scenes_without_mesh: bool = False,
        _verbose: bool = False,
    ) -> Group:
        """
        Process scenes from GDS layout and generate structured print scenes.

        This method takes a scene layer as designation for the print scene and checks
        for markers lying inside the scene as provided by marker_layer.
        In case the marker pattern consists of disjoint polygons,
        it is necessary to provide a marker_region_layer that defines the
        image frame for every single marker to ensure correct image generation.
        Markers may have different orientations but always have to have the same
        size/shape per layer.

        Args:
            scene_layer: Layer specification for scene regions
            project: Project instance in which read-out markers from GDS are loaded to.
            presets: Bijective list of Preset instances for each mesh (referred to by index; optional)
            meshes: List of mesh objects (optional)
            marker_layer: Layer specification for markers
            marker_region_layer: Layer specification for marker regions
            marker_height: Height value for markers
            image_resource: Path to an alternative image resource (optional)
            marker_aligner_node: Custom marker alignment node (optional)
            interface_aligner_node: Custom interface alignment node (optional)
            interface_aligner_layer: Layer specification for interface alignment (optional)
            mesh_spots_layers: List of layer specifications for mesh spots (optional)
            cell_name: Name of the GDS cell to process (optional)
            colors: Bijective list of colors for structures (optional)
            structure_kwargs: Additional dictionary for keyword arguments for all structures
            remove_scenes_without_mesh: Removes all scenes that do not contain any meshes as structure nodes.
            _verbose: Verbose output flag

        Returns:
            Group: Group node containing all generated scenes
        """
        # Initialize default values
        structure_kwargs = structure_kwargs or {}

        # Check if all interface aligner related parameters are None
        _no_interfacealigner_if_all_None = all(
            v is None
            for v in [
                meshes,
                marker_layer,
                interface_aligner_node,
                interface_aligner_layer,
            ]
        )

        # Validation checks
        if marker_layer is None and marker_region_layer is not None:
            raise ValueError(
                "marker_layer must not be None if a marker_region_layer was specified.\n"
                "Either specify a marker_layer or set marker_region_layer=None as well."
            )

        if marker_layer is None:
            marker_layer = (1_000_000, 1_000_000)

        # Input layers
        _marker_layer = self.layout.layer(*marker_layer)  # Target shapes
        _marker_region_layer = (
            self.layout.layer(*marker_region_layer)
            if marker_region_layer is not None
            else self.layout.layer(*marker_layer)
        )  # Target regions
        _scene_layer = self.layout.layer(*scene_layer)  # Region definition

        # Create regions
        top_cell = (
            self.layout.top_cell()
            if cell_name is None
            else self.get_cell_by_name(cell_name=cell_name)
        )
        scene_region = pya.Region(top_cell.begin_shapes_rec(_scene_layer))
        marker_region = pya.Region(top_cell.begin_shapes_rec(_marker_layer))
        marker_region_region = pya.Region(
            top_cell.begin_shapes_rec(_marker_region_layer)
        )

        if interface_aligner_layer is not None:
            _interface_aligner_layer = self.layout.layer(
                *interface_aligner_layer
            )
            ia_region = pya.Region(
                top_cell.begin_shapes_rec(_interface_aligner_layer)
            )

        if mesh_spots_layers is not None:
            _mesh_spots_layers = [
                self.layout.layer(*mesh_spots_layer)
                for mesh_spots_layer in mesh_spots_layers
            ]
            mesh_spots_regions = [
                pya.Region(top_cell.begin_shapes_rec(_mesh_spots_layer))
                for _mesh_spots_layer in _mesh_spots_layers
            ]

        # Compute the intersection to reduce sample size
        marker_region_region_in_scene_region = (
            marker_region_region & scene_region
        )
        marker_region_in_scene_region = marker_region & scene_region

        # Iterate through all polygon patches in scene layer
        all_scenes = []
        file_path = None  # resets file_path each run to ensure the directory gets recreated and not skipped

        for idx, scene in enumerate(scene_region.each()):
            single_scene_reg = pya.Region(scene)
            # Determine absolute centroid position of scene(s)
            scene_pos = (
                single_scene_reg.bbox().center().x / 1000,
                single_scene_reg.bbox().center().y / 1000,
                0,
            )

            # Prepare Scene with interface alignment
            scene_npx = Scene(
                position=scene_pos,
                name=f"scene_{scene_layer[0]}_{scene_layer[1]}_{idx}",
            )
            interface_aligner_npx = (
                InterfaceAligner()
                if interface_aligner_node is None
                else interface_aligner_node.deepcopy_node(copy_children=False)
            )

            # Return only scenes if all listed are None
            if not _no_interfacealigner_if_all_None:
                interface_aligner_npx.name = (
                    f"ia_in_scene_{scene_layer[0]}_{scene_layer[1]}_{idx}"
                )
                scene_npx.append_node(interface_aligner_npx)

            # Pass alignment anchors and scan area sizes from polygons in interface alignment layer
            # if any was specified
            if interface_aligner_layer is not None:
                ia_regions_in_single_scene = ia_region & single_scene_reg
                ia_anchor_pos_list = [
                    [
                        ia_region_poly.bbox().center().x / 1000 - scene_pos[0],
                        ia_region_poly.bbox().center().y / 1000 - scene_pos[1],
                    ]
                    for ia_region_poly in ia_regions_in_single_scene.each()
                ]
                ia_scan_area_sizes = [
                    [
                        ia_region_poly.bbox().width() / 1000,
                        ia_region_poly.bbox().height() / 1000,
                    ]
                    for ia_region_poly in ia_regions_in_single_scene.each()
                ]
                interface_aligner_npx.set_interface_anchors_at(
                    positions=ia_anchor_pos_list,
                    scan_area_sizes=ia_scan_area_sizes,
                )
                interface_aligner_npx.name = f"ia_{interface_aligner_layer[0]}_{interface_aligner_layer[1]}_in_scene_{scene_layer[0]}_{scene_layer[1]}_{idx}"

            # Process all positions defined by mesh spots per layer if any were given
            all_structures = []
            if mesh_spots_layers is not None and meshes is not None:
                # TODO: assert colors (in general all) len to be equal to each other!
                colors = (
                    len(mesh_spots_layers) * ["yellow"]
                    if colors is None
                    else colors
                )
                presets = (
                    len(mesh_spots_layers) * [Preset()]
                    if presets is None
                    else presets
                )
                for mesh_spots_region, mesh, preset, color, name in zip(
                    mesh_spots_regions,
                    meshes,
                    presets,
                    colors,
                    mesh_spots_layers,
                ):
                    mesh_spots_in_single_scene_reg = (
                        mesh_spots_region & single_scene_reg
                    )
                    ms_pos_single_layer_positions = [
                        [
                            ms_region_poly.bbox().center().x / 1000
                            - scene_pos[0],
                            ms_region_poly.bbox().center().y / 1000
                            - scene_pos[1],
                            0 - scene_pos[2],
                        ]
                        for ms_region_poly in mesh_spots_in_single_scene_reg
                    ]

                    # Assign meshes to structures and append them to current scene
                    structures = [
                        Structure(
                            name=mesh.name + "_in_" + f"{name}",
                            mesh=mesh,
                            preset=preset,
                            color=color,
                            position=position,
                            **structure_kwargs,
                        )
                        for position in ms_pos_single_layer_positions
                    ]
                    all_structures.extend(structures)
            elif meshes is not None:
                colors = len(meshes) * ["red"] if colors is None else colors
                presets = (
                    len(meshes) * [Preset()] if presets is None else presets
                )
                structures = [
                    Structure(
                        mesh=mesh,
                        preset=preset,
                        color=color,
                        name=mesh.name,
                        **structure_kwargs,
                    )
                    for mesh, preset, color in zip(meshes, presets, colors)
                ]
                all_structures.extend(structures)

            # Get marker_region parts within this specific single scene
            marker_regions_in_single_scene = (
                marker_region_region_in_scene_region & single_scene_reg
            )

            if marker_region_layer is None:
                marker_regions_in_single_scene.merge()

            # Create list containing relative coordinates of markers in respective scene
            marker_pos_list = [
                [
                    marker_region_poly.bbox().center().x / 1000 - scene_pos[0],
                    marker_region_poly.bbox().center().y / 1000 - scene_pos[1],
                    marker_height,
                ]
                for marker_region_poly in marker_regions_in_single_scene.each()
            ]

            # Additional processing per patch
            if not marker_regions_in_single_scene.is_empty():
                # Collect shapes and convert to Shapely polygons
                polygons_to_unify = []
                shapely_polys = []

                for marker_region in marker_regions_in_single_scene.each():
                    single_marker_reg = pya.Region(marker_region)
                    single_marker_reg_iter = pya.RecursiveShapeIterator(
                        self.layout, top_cell, _marker_layer, single_marker_reg
                    )
                    polygons_to_unify = []
                    while not single_marker_reg_iter.at_end():
                        marker_shape = single_marker_reg_iter.shape()
                        marker_trans = single_marker_reg_iter.trans()

                        if (
                            marker_shape.is_polygon()
                            or marker_shape.is_box()
                            or marker_shape.is_path()
                        ):
                            klayout_poly = marker_shape.polygon.transformed(
                                marker_trans
                            )

                            # Extract hull points
                            hull_points = list(klayout_poly.each_point_hull())
                            exterior = [(p.x, p.y) for p in hull_points]

                            # Extract holes
                            interiors = []
                            for h in range(klayout_poly.holes()):
                                hole_points = list(
                                    klayout_poly.each_point_hole(h)
                                )
                                interiors.append(
                                    [(p.x, p.y) for p in hole_points]
                                )

                            # Create Shapely polygon
                            poly = Polygon(exterior, interiors)
                            polygons_to_unify.append(poly)

                        single_marker_reg_iter.next()

                    shapely_polys.append(MultiPolygon(polygons_to_unify))

                img_dir = f"./images_{self.gds_name}_scene_{scene_layer[0]}_{scene_layer[1]}"
                png_name = f"marker_{marker_layer[0]}_{marker_layer[1]}.png"
                if file_path != os.path.join(img_dir, png_name):
                    file_path = os.path.join(img_dir, png_name)
                    os.makedirs(img_dir, exist_ok=True)
                    _, marker_orientations = (
                        self._group_equivalent_polygons_and_output_image(
                            shapely_polys, file_path=file_path
                        )
                    )
                    assert len(marker_orientations) == len(marker_pos_list), (
                        "marker position count does not coincide with marker "
                        "orientation count. Marker layer polygons are probably "
                        "not grouped properly.\n"
                        f"len of marker_orientations : {len(marker_orientations)}\n"
                        f"len of marker_pos_list : {len(marker_pos_list)}"
                    )

                    image_resource = (
                        Image(file_path, png_name)
                        if image_resource is None
                        else image_resource
                    )
                    project.load_resources(image_resource)

                    marker_aligner_npx = (
                        MarkerAligner(
                            image_resource,
                            marker_size=[
                                single_marker_reg.bbox().width() / 1000,
                                single_marker_reg.bbox().height() / 1000,
                            ],
                            max_outliers=len(marker_pos_list) - 3,
                        )
                        if marker_aligner_node is None
                        else marker_aligner_node.deepcopy_node()
                    )
                    marker_aligner_npx.set_markers_at(
                        marker_pos_list, marker_orientations
                    )
                # TODO: Positons DO NOT get passed to copied_marker_aligner as intended! Needs fixing!

                copied_marker_aligner_npx = marker_aligner_npx.deepcopy_node(
                    name=f"marker_{marker_layer[0]}_{marker_layer[1]}_in_scene_{scene_layer[0]}_{scene_layer[1]}_{idx}"
                ).add_child(*all_structures)
                scene_npx.append_node(copied_marker_aligner_npx)
            # Append would not work so add in this case
            elif not all_structures == [] and scene_npx.children_nodes == []:
                scene_npx.add_child(*all_structures)
            elif not all_structures == []:
                scene_npx.children_nodes[0].add_child(*all_structures)
            all_scenes.append(scene_npx)

        # Remove scenes that do not have any mesh in them if flag is True
        if remove_scenes_without_mesh:
            all_scenes = [
                scene
                for scene in all_scenes
                if len(scene.grab_all_nodes_bfs("structure")) > 0
            ]

        output_group = Group(f"scene_layer_{scene_layer[0]}_{scene_layer[1]}")
        output_group.add_child(*all_scenes)

        return output_group

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

    def get_cell_by_name(self, cell_name: str) -> pya.Cell:
        """Retrieve a cell by its name from the GDS layout.

        Args:
            cell_name: Name of the cell to retrieve. Case-sensitive.

        Returns:
            pya.Cell: The requested cell object.

        Raises:
            TypeError: If input is not a string
            KeyError: If no cell with specified name exists
        """
        # Input validation
        if not isinstance(cell_name, str):
            raise TypeError(
                f"Expected string for cell name, got {type(cell_name)}"
            )

        # Efficient search using layout's cell dictionary
        cell = self.layout.cell(cell_name)
        if cell is None:
            available_cells = [c.name for c in self.layout.each_cell()]
            raise KeyError(
                f"Cell '{cell_name}' not found in GDS layout. "
                f"Available cells: {', '.join(available_cells[:5])}..."
            )
        return cell

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
        cell_name: str,
        project: Optional[Project] = None,
        marker_layer: Tuple[int, int] = (254, 254),
        marker_height: float = 0.33,
        image_resource: Optional[Image] = None,
        **marker_aligner_kwargs: Dict,
    ) -> MarkerAligner:
        """Create and configure a MarkerAligner from GDS markers.

        Args:
            cell_name: Name of the cell containing markers
            project: Optional Project for resource management
            marker_layer: Layer/datatype tuple for marker identification
            marker_height: Z-height for marker polygons
            image_resource: Optional pre-configured Image resource
            **marker_aligner_kwargs: Additional MarkerAligner configuration

        Returns:
            Configured MarkerAligner instance

        Raises:
            ValueError: If no markers found or invalid input dimensions
            TypeError: For invalid input types
            RuntimeError: If image processing fails
        """
        # Input validation
        if not isinstance(marker_layer, tuple) or len(marker_layer) != 2:
            raise TypeError("marker_layer must be a (int, int) tuple")
        if marker_height < 0:
            raise ValueError("marker_height must be non-negative")

        try:
            cell = self.get_cell_by_name(cell_name)
        except KeyError as e:
            raise ValueError(f"Cell '{cell_name}' not found in layout") from e

        # Polygon processing
        marker_polygons, marker_positions = (
            self._merged_polygons_and_their_positions(
                cell, marker_layer, marker_height
            )
        )

        if not marker_polygons:
            raise ValueError(f"No markers found on layer {marker_layer}")
        if len(marker_positions) < 3:
            raise ValueError("At least 3 markers required for alignment")

        # Image resource handling
        image_dir = f"./images_{self.gds_name}_{marker_layer}"
        self._ensure_folder_exist_else_create(image_dir)

        image_file_path = os.path.join(image_dir, f"marker_{marker_layer}.png")
        _image = image_resource or Image(
            name=str(marker_layer), file_path=image_file_path
        )

        if project is not None:
            if not isinstance(project, Project):
                raise TypeError("project must be a Project instance")
            project.load_resources(_image)

        # Marker processing
        _, marker_orientations = (
            self._group_equivalent_polygons_and_output_image(
                marker_polygons, file_path=image_file_path
            )
        )

        try:
            marker_size = [
                marker_polygons[0].bounds[2] - marker_polygons[0].bounds[0],
                marker_polygons[0].bounds[3] - marker_polygons[0].bounds[1],
            ]
        except:
            UserWarning(
                "Failed to calculate marker sizes based on GDS-polygons."
                " Default [5.0,5.0] will be used instead."
            )
            marker_size = [5.0, 5.0]

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
        self,
        cell_name: str,
        coarse_layer: Tuple[int, int] = (200, 200),
        residual_threshold: float = 10.0,
    ) -> CoarseAligner:
        """Create a CoarseAligner from anchor points in GDS.

        Args:
            cell_name: Name of the cell containing coarse alignment features
            coarse_layer: Layer/datatype tuple for anchor identification
            residual_threshold: Maximum allowed alignment residual

        Returns:
            Configured CoarseAligner instance

        Raises:
            ValueError: If no anchors found or invalid threshold
        """
        if not isinstance(coarse_layer, tuple) or len(coarse_layer) != 2:
            raise TypeError("marker_layer must be a (int, int) tuple")
        if residual_threshold <= 0:
            raise ValueError("residual_threshold must be positive")

        cell = self.get_cell_by_name(cell_name)
        _, anchor_positions = self._merged_polygons_and_their_positions(
            cell, coarse_layer, 0
        )

        return CoarseAligner(
            name=f"{cell.name}{coarse_layer}",
            residual_threshold=residual_threshold,
        ).set_coarse_anchors_at(anchor_positions)

    def get_custom_interface_aligner(
        self,
        cell_name: str,
        interface_layer: Tuple[int, int] = (255, 255),
        scan_area_sizes: Optional[List[List[float]]] = None,
        **interface_aligner_kwargs: Dict,
    ) -> InterfaceAligner:
        """Create an InterfaceAligner with custom scan areas from GDS.

        Args:
            cell_name: Name of the cell containing interface features
            interface_layer: Layer/datatype tuple for scan areas
            scan_area_sizes: Optional list of [width, height] pairs
            **interface_aligner_kwargs: Additional InterfaceAligner config

        Returns:
            Configured InterfaceAligner instance
        """
        if not isinstance(interface_layer, tuple) or len(interface_layer) != 2:
            raise TypeError("marker_layer must be a (int, int) tuple")

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

        return InterfaceAligner(
            name=f"{cell.name}{interface_layer}",
            **interface_aligner_kwargs,
        ).set_interface_anchors_at(
            positions=anchor_positions,
            scan_area_sizes=scan_area_sizes,
        )
