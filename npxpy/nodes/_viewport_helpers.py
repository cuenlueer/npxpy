# -*- coding: utf-8 -*-
"""
npxpy
Created on Thu Feb 29 11:49:17 2024

@author: Caghan Uenlueer
Neuromorphic Quantumphotonics
Heidelberg University
E-Mail:	caghan.uenlueer@kip.uni-heidelberg.de

This file is part of npxpy, which is licensed under the MIT License.
"""


def _lazy_import():
    try:
        import pyvista as pv

        pv.global_theme.allow_empty_mesh = True
        from pyvistaqt import BackgroundPlotter
        import numpy as np
        from typing import Optional
    except ImportError:
        raise ImportError(
            "Missing extra dependencies.\n"
            "Either install via `pip install npxpy[all]`\n"
            "or via `pip install npxpy[viewport]`"
        )

    class _GroupedPlotter(BackgroundPlotter):
        """
        A custom PyVista BackgroundPlotter that supports grouping of actors,
        enabling group-based visibility toggling.

        Methods
        -------
        add_mesh(mesh, group=None, **kwargs)
            Adds mesh to the plotter and stores actor in group.
        disable_visibility(group)
            Disables visibility of all actors in the specified group.
        enable_visibility(group)
            Enables visibility of all actors in the specified group.
        set_group_visibility(group, visible=True)
            Sets visibility for all actors in a given group.
        """

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.actor_groups = (
                {}
            )  # dictionary to store lists of actors by group
            self.block_groups = (
                {}
            )  # e.g. {group_name: [block_idx1, block_idx2...]}

        def add_mesh(self, mesh, group=None, **kwargs):
            """
            A wrapper around plotter.add_mesh that also associates the actor with a group.
            """
            actor = super().add_mesh(
                mesh, **kwargs
            )  # get the actor from PyVista
            if group is not None:
                if group not in self.actor_groups:
                    self.actor_groups[group] = []
                self.actor_groups[group].append(actor)
            return actor

        def add_composite(self, dataset, group=None, **kwargs):
            """
            Add a composite dataset (e.g. MultiBlock) as a single actor,
            optionally associating all blocks in the dataset with a group name.

            Returns
            -------
            actor : vtkActor or vtkCompositePolyDataMapper2
                The composite actor used for rendering the dataset.
            """
            # Use PyVista's built-in logic for composite data
            actor = super().add_composite(dataset, **kwargs)

            if group is not None:
                # If we want the entire MultiBlock to be considered one 'group',
                # we store all block indices in self.block_groups[group].
                n_blocks = dataset.n_blocks()
                for i in range(n_blocks):
                    self.block_groups.setdefault(group, []).append(i)

            return actor

        def set_group_visibility(self, group, visible=True):
            """
            Toggle visibility of all actors and/or blocks in a given group.
            """
            # 1) Toggle any standard actors in self.actor_groups
            if group in self.actor_groups:
                for actor in self.actor_groups[group]:
                    actor.SetVisibility(visible)

            # 2) Toggle any block indices in self.block_groups (Does not work)
            if group in self.block_groups:
                for block_idx in self.block_groups[group]:  # (Does not work)
                    # PyVista provides set_block_visibility(block_idx, bool)
                    self.set_block_visibility(block_idx, visible)

            self.render()

        def disable(self, *groups):
            for group in groups:
                self.set_group_visibility(group, visible=False)

        def enable(self, *groups):
            for group in groups:
                self.set_group_visibility(group, visible=True)

        def _add_custom_axes(self):
            # your existing logic for custom axes, unchanged
            x_axis_dict = {
                "color": "red",
                "group": "axes",
                "line_width": 2,
            }
            y_axis_dict = {
                "color": "green",
                "group": "axes",
                "line_width": 2,
            }
            z_axis_dict = {
                "color": "blue",
                "group": "axes",
                "line_width": 2,
            }

            xmax = self.bounds[1] if self.bounds[1] > 100 else 100
            ymax = self.bounds[3] if self.bounds[3] > 100 else 100
            zmax = self.bounds[5] if self.bounds[5] > 100 else 100

            x_axis = pv.Line(pointa=(0, 0, 0), pointb=(xmax, 0, 0))
            y_axis = pv.Line(pointa=(0, 0, 0), pointb=(0, ymax, 0))
            z_axis = pv.Line(pointa=(0, 0, 0), pointb=(0, 0, zmax))

            # add_mesh calls for axes are fine (they are separate actors)
            self.add_mesh(x_axis, **x_axis_dict)
            self.add_mesh(y_axis, **y_axis_dict)
            self.add_mesh(z_axis, **z_axis_dict)

    def _apply_transforms(
        mesh: pv.DataSet,
        all_positions: [np.ndarray],
        all_rotations: [np.ndarray],
        vector_x: np.ndarray = np.array([1.0, 0.0, 0.0]),
        vector_y: np.ndarray = np.array([0.0, 1.0, 0.0]),
        vector_z: np.ndarray = np.array([0.0, 0.0, 1.0]),
        pivot: Optional[np.ndarray] = [0, 0, 0],
    ) -> None:
        """
        Applies rotations around a pivot (if provided) and then translates a PyVista mesh.

        Parameters
        ----------
        mesh : pv.DataSet
            The PyVista mesh or dataset to be transformed.
        position : np.ndarray
            The final translation to be applied. Typically the object's position.
        rotation : np.ndarray
            Rotation angles [rot_x, rot_y, rot_z], in degrees, to be applied.
        pivot : np.ndarray, optional
            The point around which to rotate. If None, rotation occurs around the origin (0,0,0).
        in_plane_only : bool, default=False
            If True, only rotate around the Z-axis (e.g., for markers that only rotate in-plane).
        """

        # Rotate about all axes
        # Start with initial triad: e_x, e_y, e_z
        e_x = vector_x
        e_y = vector_y
        e_z = vector_z

        for position, rotation in zip(all_positions, all_rotations):
            pos_wrt_newbasis = (
                position[0] * e_x + position[1] * e_y + position[2] * e_z
            )

            mesh.translate(pos_wrt_newbasis, inplace=True)

            pivot += pos_wrt_newbasis

            mesh.rotate_vector(
                vector=e_y,
                angle=rotation[1],
                point=pivot,
                inplace=True,
                # transform_all_input_vectors=True,
            )

            # 2) Rotate about updated e_y by ry
            e_x = _rodrigues_rotation(e_x, e_y, rotation[1])
            e_z = _rodrigues_rotation(e_z, e_y, rotation[1])
            # e_y remains unchanged when rotating around e_y

            mesh.rotate_vector(
                vector=e_x,
                angle=rotation[0],
                point=pivot,
                inplace=True,
                # transform_all_input_vectors=True,
            )

            # 1) Rotate about current e_x by rx
            e_y = _rodrigues_rotation(e_y, e_x, rotation[0])
            e_z = _rodrigues_rotation(e_z, e_x, rotation[0])
            # e_x itself remains unchanged when rotating around e_x

            mesh.rotate_vector(
                vector=e_z,
                angle=rotation[2],
                point=pivot,
                inplace=True,
                # transform_all_input_vectors=True,
            )

            # 3) Rotate about updated e_z by rz
            e_x = _rodrigues_rotation(e_x, e_z, rotation[2])
            e_y = _rodrigues_rotation(e_y, e_z, rotation[2])
            # e_z remains unchanged when rotating around e_z

        return (e_x, e_y, e_z)

    def _rodrigues_rotation(v, k, theta_deg):
        """
        Rotate a vector v about a (normalized) axis k by theta_deg (degrees),
        using Rodrigues' rotation formula.
        """
        theta = np.deg2rad(theta_deg)
        k = k / np.linalg.norm(k)  # ensure axis is normalized
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)
        # Rodrigues formula: v' = v*cosθ + (k x v)*sinθ + k*(k·v)*(1 - cosθ)
        return (
            v * cos_t + np.cross(k, v) * sin_t + k * np.dot(k, v) * (1 - cos_t)
        )

    class _meshbuilder:
        @staticmethod
        def scene_mesh(objective, ronin_node=False):
            scene_mesh_dict = {
                "color": "lightgrey",
                "line_width": 2,
                "style": "wireframe",
                "opacity": 0.1,
                "group": "scene",
            }
            # Decide on circle radius
            if not ronin_node:
                circle_radius = 280 if objective == "25x" else 139

                return (
                    pv.Circle(radius=circle_radius, resolution=100),
                    scene_mesh_dict,
                )
            else:
                both_circles = pv.PolyData()
                both_circles += pv.Circle(
                    radius=280, resolution=100
                ) + pv.Circle(radius=139, resolution=100)
                return both_circles, scene_mesh_dict

        @staticmethod
        def ca_mesh(coarse_aligner):
            coarse_aligner_mesh_dict = {
                "color": "orange",
                "line_width": 1,
                "group": "coarse_alignment",
            }
            coarse_aligner_meshes = pv.PolyData()
            for anchor_i in coarse_aligner.alignment_anchors:
                # Create a line in the x-direction from (-100,0,0) to (100,0,0).
                line_x = pv.Line(pointa=(-100, 0, 0), pointb=(100, 0, 0))

                # Create a line in the y-direction from (0,-100,0) to (0,100,0).
                line_y = pv.Line(pointa=(0, -100, 0), pointb=(0, 100, 0))

                # Create a line in the z-direction from (0,0,0) to (0,0,500).
                line_z = pv.Line(pointa=(0, 0, 0), pointb=(0, 0, 500))

                label_dummy_label = anchor_i["label"]
                label_dummy_position = anchor_i["position"]
                label = pv.Text3D(
                    f"{label_dummy_label}",
                    height=10,
                    depth=0,
                    center=(0, -120, 0),
                ) + pv.Text3D(
                    f"{label_dummy_position}",
                    height=5,
                    depth=0,
                    center=(0, -130, 0),
                )

                # Combine them into a single mesh (a PolyData with three line segments).
                coarse_aligner_mesh = line_x + line_y + line_z + label

                # no rotation. translation only.
                _apply_transforms(
                    mesh=coarse_aligner_mesh,
                    all_positions=[anchor_i["position"]],
                    all_rotations=[[0, 0, 0]],
                )
                coarse_aligner_meshes += coarse_aligner_mesh

            return coarse_aligner_meshes, coarse_aligner_mesh_dict

        @staticmethod
        def ea_mesh(edgealigner):
            rectangle_dict = {
                "scalars": "gradient",
                "cmap": ["white", "green"],
                "show_edges": False,
                "categories": True,
                "edge_color": "green",
                "smooth_shading": False,
                "opacity": 0.5,
                "line_width": 1,
                "show_scalar_bar": False,
                "group": "edge_alignment",
            }
            dashed_dict = {
                "color": "green",
                "line_width": 1,
                "group": "edge_alignment",
            }

            offsets = [
                anchor["offset"] for anchor in edgealigner.alignment_anchors
            ]
            dashed = pv.Line(
                pointa=(0, 0, 0),
                pointb=(0, 0, 0),
            )
            if all(o < 0 for o in offsets):
                for offset in offsets:
                    for i in range(0, int(min(offsets)) - 1, -10):
                        dashed += pv.Line(
                            pointa=(-5 + i, 0, 0),
                            pointb=(0 + i, 0, 0),
                        )
            elif all(o > 0 for o in offsets):
                for offset in offsets:
                    for i in range(0, int(max(offsets)) + 1, 10):
                        dashed += pv.Line(
                            pointa=(0 + i, 0, 0),
                            pointb=(5 + i, 0, 0),
                        )
            elif all(o == 0 for o in offsets):
                pass
            else:
                for i in range(0, int(min(offsets)) - 1, -10):
                    dashed += pv.Line(
                        pointa=(-5 + i, 0, 0),
                        pointb=(0 + i, 0, 0),
                    )
                for i in range(0, int(max(offsets)) + 1, 10):
                    dashed += pv.Line(
                        pointa=(0 + i, 0, 0),
                        pointb=(5 + i, 0, 0),
                    )

            rectangles = []
            for anchor in edgealigner.alignment_anchors:
                x = anchor["scan_area_size"][0]
                y = anchor["scan_area_size"][1]

                offset = anchor["offset"]

                pointa = [0.5 * x + offset, 0.5 * y, 0.0]
                pointb = [0.5 * x + offset, -0.5 * y, 0.0]
                pointc = [-0.5 * x + offset, -0.5 * y, 0.0]

                rectangle = pv.Rectangle([pointa, pointb, pointc])
                rectangle.point_data["gradient"] = np.array(
                    [
                        0,
                        1,
                        1,
                        0,
                    ]
                )

                x_line = 1.5 * x if 1.5 * x > 10 else 10
                boundary_edges = rectangle.extract_feature_edges(
                    boundary_edges=True,  # Extract outline/boundary
                    feature_edges=False,  # Turn off detection of sharp angles
                    manifold_edges=False,  # Turn off internal manifold edges
                    non_manifold_edges=False,
                ) + pv.Line(
                    pointa=(-0.5 * x_line + offset, 0, 0),
                    pointb=(0.5 * x_line + offset, 0, 0),
                )

                label_mesh = pv.Text3D(
                    anchor["label"],
                    depth=0,
                    height=2.5,
                    center=(offset, 0.5 * (y + 10), 0),
                )

                dashed += boundary_edges + label_mesh
                rectangles.append(rectangle)

            rectangle_dicts = [rectangle_dict for i in range(len(rectangles))]

            edge_aligner_meshes = rectangles + [dashed]
            edge_aligner_meshes_dicts = rectangle_dicts + [dashed_dict]
            return edge_aligner_meshes, edge_aligner_meshes_dicts

        @staticmethod
        def load_mesh(file_path):
            return pv.read(file_path)

        @staticmethod
        def txt_mesh(Text):
            text = Text.text
            font_size = Text.font_size
            height = Text.height

            text_mesh = pv.Text3D(
                string=text,
                depth=height,
                height=font_size * (1 + text.count("\n")),
                center=(0, 0, height / 2),
            )

            text_mesh_dict = {
                "color": Text.color,
                "group": Text._type + "_text",
            }
            return text_mesh, text_mesh_dict

        def sag_surface_z(
            self,
            x: np.ndarray,
            y: np.ndarray,
            h: float,
            rho_x: float,
            rho_y: float,
            kappa_x: float,
            kappa_y: float,
            polynomial_type: str,
            A2n_x: np.ndarray,
            A2n_y: np.ndarray,
            B2n_x: np.ndarray,
            B2n_y: np.ndarray,
        ) -> np.ndarray:
            """
            Compute the sag z(x, y):

            z(x, y) = h
                      - [ x^2 * rho_x + y^2 * rho_y ]
                        / [ 1 + sqrt( 1 - (1 + kappa_x)*(x*rho_x)^2
                                        - (1 + kappa_y)*(y*rho_y)^2 ) ]
                      - sum_{n=1}^N_B [ (B_{2n,x} x^(2n))/rho_x + (B_{2n,y} y^(2n))/rho_y ]
                      + sum_{n=1}^N_A [ A_{2n,x} x^(2n) + A_{2n,y} y^(2n) ]

            BUT the B-terms may or may not have the 1/rho factors, depending on `polynomial_type`:
            - polynomial_type == "Standard": No division by rho_x, rho_y (unscaled B-terms).
            - otherwise (e.g. "Normalized"): B-terms get divided by rho_x, rho_y.

            Parameters
            ----------
            x, y : np.ndarray
                Coordinate arrays (same shape).
            h : float
                Vertex thickness or offset.
            rho_x, rho_y : float
                Curvature (1 / radius) in the x and y directions.
            kappa_x, kappa_y : float
                Conic constants in the x and y directions.
            polynomial_type : str
                - "Standard": B-terms are NOT divided by rho_x, rho_y.
                - anything else: B-terms ARE divided by rho_x, rho_y.
            A2n_x, A2n_y : np.ndarray
                1D coefficient arrays for the A-polynomial expansions in x and y.
            B2n_x, B2n_y : np.ndarray
                1D coefficient arrays for the B-polynomial expansions in x and y.

            Returns
            -------
            z : np.ndarray
                The surface sag (height) at each (x, y).
            """

            # Compute the conic denominator
            #    denom_inside = 1 - (1 + kappa_x)*(rho_x*x)^2 - (1 + kappa_y)*(rho_y*y)^2
            #    denom = 1 + sqrt(denom_inside)  (clipped to avoid negative sqrt)

            denom_inside = (
                1.0
                - (1.0 + kappa_x) * (rho_x * x) ** 2
                - (1.0 + kappa_y) * (rho_y * y) ** 2
            )
            denom_inside = np.clip(denom_inside, a_min=0.0, a_max=None)
            denom = 1.0 + np.sqrt(denom_inside)

            # Conic portion:
            conic_part = (x**2 * rho_x + y**2 * rho_y) / denom

            # Decide how to handle the B-terms depending on polynomial_type

            if polynomial_type == "Standard":
                # B-terms are NOT divided by rho_x, rho_y
                bx_factor = 1.0
                by_factor = 1.0
            else:
                # B-terms ARE divided by rho_x, rho_y (the "normalized" or default case)
                bx_factor = 1.0 / rho_x
                by_factor = 1.0 / rho_y

            # Polynomial terms
            # We have FOUR loops, one for each array:
            #    - A2n_x:  sum_{i}  A_{2n,x} * x^(2n)
            #    - A2n_y:  sum_{i}  A_{2n,y} * y^(2n)
            #    - B2n_x:  sum_{i}  B_{2n,x} * x^(2n) * (optionally 1/rho_x)
            #    - B2n_y:  sum_{i}  B_{2n,y} * y^(2n) * (optionally 1/rho_y)
            #
            #    We do NOT assume len(A2n_x) == len(A2n_y) == len(B2n_x) == len(B2n_y).

            poly_A_x = np.zeros_like(x)
            for i in range(len(A2n_x)):
                # n = i+1 => exponent = 2*n
                n = i + 1
                exp = 2 * n
                poly_A_x += A2n_x[i] * (x**exp)

            poly_A_y = np.zeros_like(y)
            for i in range(len(A2n_y)):
                n = i + 1
                exp = 2 * n
                poly_A_y += A2n_y[i] * (y**exp)

            poly_B_x = np.zeros_like(x)
            for i in range(len(B2n_x)):
                n = i + 1
                exp = 2 * n
                poly_B_x += B2n_x[i] * ((x / bx_factor) ** exp) * bx_factor

            poly_B_y = np.zeros_like(y)
            for i in range(len(B2n_y)):
                n = i + 1
                exp = 2 * n
                poly_B_y += B2n_y[i] * ((y / by_factor) ** exp) * by_factor

            # Combine them:
            poly_A = poly_A_x + poly_A_y
            poly_B = poly_B_x + poly_B_y

            # Final sag
            # z(x,y) = h - conic_part - poly_B + poly_A

            z = h - conic_part - poly_B + poly_A
            return z

        def lens_mesh(
            self,
            radius: float = 100.0,
            height: float = 50.0,
            crop_base: bool = False,
            asymmetric: bool = False,
            curvature: float = 0.01,
            conic_constant: float = 0.01,
            curvature_y: float = 0.01,
            conic_constant_y: float = -1.0,
            # Polynomial terms (default to zero-length arrays => no polynomial additions)
            surface_compensation_factors: np.ndarray = None,
            surface_compensation_factors_y: np.ndarray = None,
            polynomial_type: str = "Normalized",
            polynomial_factors: np.ndarray = None,
            polynomial_factors_y: np.ndarray = None,
            # Discretization:
            nr_radial_segments: int = 50,
            nr_phi_segments: int = 36,
            # A small offset so we never get exactly z=0 (epsilon>0):
            # _epsilon: float = 1e-5,
        ) -> pv.PolyData:
            """
            Construct a PyVista surface/mesh that:
              1) Samples z(x,y) within the circle x^2 + y^2 <= radius^2.
              2) Adds a 'cylindrical complement' from z=0..epsilon wherever the function is
                 undefined or too low.
              3) If crop_base == True, the base is cropped so that the final minimal z equals epsilon.
              4) If asymmetric == False, use the same curvature and conic_constant for x and y.

            Returns
            -------
            mesh : pv.PolyData
                A mesh that (approximately) corresponds to the region below z(x,y) + a small
                cylindrical side/bottom piece from z=0..epsilon.
            """

            # -------------------------------------------------------------------------
            # 1) Handle polynomial arrays
            #
            #    Each polynomial array A2n_x, A2n_y, B2n_x, B2n_y can be None or zero-length,
            #    which implies no polynomial terms in that dimension.
            #    If they are non-empty, we convert them to NumPy arrays.
            # -------------------------------------------------------------------------
            A2n_x = surface_compensation_factors
            A2n_y = surface_compensation_factors_y
            B2n_x = polynomial_factors
            B2n_y = polynomial_factors_y

            if A2n_x is None or len(A2n_x) == 0:
                A2n_x = np.array([])
            else:
                A2n_x = np.array(A2n_x)

            if A2n_y is None or len(A2n_y) == 0:
                A2n_y = np.array([])
            else:
                A2n_y = np.array(A2n_y)

            if B2n_x is None or len(B2n_x) == 0:
                B2n_x = np.array([])
            else:
                B2n_x = np.array(B2n_x)

            if B2n_y is None or len(B2n_y) == 0:
                B2n_y = np.array([])
            else:
                B2n_y = np.array(B2n_y)

            # -------------------------------------------------------------------------
            # 2) If asymmetric == False, treat all y-parameters the same as x-parameters
            #
            #    This means curvature_y = curvature, conic_constant_y = conic_constant,
            #    and for polynomial terms, B2n_y = B2n_x, A2n_y = A2n_x
            # -------------------------------------------------------------------------
            if not asymmetric:
                curvature_y = curvature
                conic_constant_y = conic_constant
                A2n_y = A2n_x
                B2n_y = B2n_x

            # -------------------------------------------------------------------------
            # 3) Create polar grid
            #
            #    - r_vals spans [0..radius], giving radial coordinates
            #    - phi_vals spans [0..2π], giving angular coordinates
            #    - meshgrid produces 2D arrays rr, pp for all (r, phi)
            # -------------------------------------------------------------------------
            r_vals = np.linspace(0, radius, nr_radial_segments)
            phi_vals = np.linspace(0, 2.0 * np.pi, nr_phi_segments)
            rr, pp = np.meshgrid(r_vals, phi_vals)

            # Convert (r, phi) -> Cartesian (x, y)
            XX = rr * np.cos(pp)
            YY = rr * np.sin(pp)

            # -------------------------------------------------------------------------
            # 4) Evaluate z for each (x, y) in the domain
            #
            #    We call sag_surface_z(...) which handles the conic surface plus any
            #    polynomial terms (A, B) in x, y according to polynomial_type.
            # -------------------------------------------------------------------------

            ZZ = self.sag_surface_z(
                XX,
                YY,
                height,
                rho_x=curvature,
                rho_y=curvature_y,
                kappa_x=conic_constant,
                kappa_y=conic_constant_y,
                polynomial_type=polynomial_type,
                A2n_x=A2n_x,
                A2n_y=A2n_y,
                B2n_x=B2n_x,
                B2n_y=B2n_y,
            )

            # -------------------------------------------------------------------------
            # 5) Build a structured PyVista grid from (XX, YY, ZZ)
            #
            #    - Create a StructuredGrid with dimension [nr_radial_segments, nr_phi_segments, 1]
            #    - Convert it to a PolyData surface
            # -------------------------------------------------------------------------
            surf = pv.StructuredGrid()
            surf.points = np.c_[XX.ravel(), YY.ravel(), ZZ.ravel()]
            surf.dimensions = [nr_radial_segments, nr_phi_segments, 1]

            def get_smallest_radius_at_z0():
                radii_at_z0_points = []
                for phi in range(nr_phi_segments):
                    for r in range(nr_radial_segments):
                        current_point = surf.points[
                            (nr_radial_segments * phi) + r
                        ]
                        if (
                            current_point[2] < 0
                        ):  # Get first point on arc where z<0
                            point_before_current_point = surf.points[
                                (nr_radial_segments * phi) + r - 1
                            ]
                            radius_z0 = np.sqrt(
                                point_before_current_point[0] ** 2
                                + point_before_current_point[1] ** 2
                            )
                            radii_at_z0_points.append(radius_z0)
                            break
                if len(radii_at_z0_points) != 0:
                    return min(radii_at_z0_points)
                else:
                    return radius + 1

            surface_mesh = (
                surf.extract_surface()
            )  # Convert to a triangular surface mesh

            # Compute a "small" radius from curvature:
            R_curve_array = np.array(
                [
                    curvature * np.sqrt(1 + conic_constant),
                    curvature_y * np.sqrt(1 + conic_constant_y),
                ]
            )
            R_curv_small = 1 / (max(abs(R_curve_array)))

            radii = [R_curv_small, get_smallest_radius_at_z0(), radius]
            lowest_z_on_surface_mesh = min(surface_mesh.points[:, 2])

            # -------------------------------------------------------------------------
            # 8) Build a disc at the base (z = z_base_disc) and extrude it to form
            #    a bottom or "cylindrical complement"
            # -------------------------------------------------------------------------
            z_base_disc = (
                lowest_z_on_surface_mesh
                if crop_base and lowest_z_on_surface_mesh >= 0
                else 0
            )

            disc_radius = min(radii)
            base_disc = pv.Disc(
                center=(0, 0, z_base_disc),
                inner=0,
                outer=disc_radius,
                r_res=nr_radial_segments + 500,
                c_res=nr_phi_segments + 360,
            )

            # Extrude disc upward until it intersects or "trims" against the main surface
            lens_mesh = base_disc.extrude_trim((0, 0, 1), surface_mesh)

            return lens_mesh

        @staticmethod
        def dc_meshes(domain_size):
            """
            Builds a box and two orthogonal planes with gradient scalars.
            Returns a list of (mesh, dict_of_plot_kwargs).
            """

            L = domain_size[0]
            W = domain_size[1]
            D = domain_size[2]

            # 1) Bounding box
            box = pv.Cube(
                center=(0, W / 2, -D / 2), x_length=L, y_length=W, z_length=D
            )
            box_dict = {
                "color": "white",
                "opacity": 0.1,
                "show_edges": True,
                "edge_color": "red",
                "line_width": 1,
                "group": "dose_compensation",
            }

            # 2) Rectangle on the XY-plane
            xy_plane = pv.Plane(
                center=(0, -25, 0),
                direction=(0, 0, 1),
                i_size=L,
                j_size=50,
                i_resolution=1,
                j_resolution=1,
            )
            # Gradient
            xy_points = xy_plane.points
            center_xy = np.array([0, -D, 0])
            dist_xy = np.linalg.norm(xy_points - center_xy, axis=1)
            xy_plane.point_data["gradient"] = dist_xy
            xy_plane_dict = {
                "scalars": "gradient",
                "cmap": "binary",
                "show_edges": False,
                "smooth_shading": True,
                "opacity": 0.44,
                "show_scalar_bar": False,
                "group": "dose_compensation",
            }

            # 3) Rectangle on the YZ-plane
            yz_plane = pv.Plane(
                center=(0, 0, -D / 2),
                direction=(0, 1, 0),
                i_size=D,
                j_size=L,  # y from 0 to W
                i_resolution=1,
                j_resolution=1,
            )
            # Gradient
            yz_points = yz_plane.points
            center_yz = np.array([0, 0, -D])
            dist_yz = np.linalg.norm(yz_points - center_yz, axis=1)
            yz_plane.point_data["gradient"] = dist_yz
            yz_plane_dict = {
                "scalars": "gradient",
                "cmap": "binary",
                "show_edges": False,
                "smooth_shading": True,
                "opacity": 0.2,
                "show_scalar_bar": False,
                "group": "dose_compensation",
            }

            return [
                (box, box_dict),
                (xy_plane, xy_plane_dict),
                (yz_plane, yz_plane_dict),
            ]

        def make_cross(self, size=1.0):
            """
            Return a small cross (two lines) as a PolyData object.
            """
            # Four points for two line segments
            pts = np.array(
                [
                    [0.0, -size, 0.0],  # bottom
                    [0.0, size, 0.0],  # top
                    [-size, 0.0, 0.0],  # left
                    [size, 0.0, 0.0],  # right
                ]
            )

            # Each line is defined with the format [num_points, p0_index, p1_index]
            # We have two lines:
            #   line 1: points 0 -> 1
            #   line 2: points 2 -> 3
            lines = np.array([2, 0, 1, 2, 2, 3])  # first line  # second line

            cross = pv.PolyData()
            cross.points = pts
            cross.lines = lines
            return cross

        def create_rectangles_mesh(self, anchors):
            """
            Build a single PolyData mesh containing all rectangles from 'anchors'.

            Each anchor must have:
              {
                "label": ...,
                "position": [x, y],
                "scan_area_size": [width, height]
              }

            Returns:
              A pv.PolyData with the combined rectangles, each in the XY-plane (z=0).
            """
            points = []
            faces = []
            p_offset = 0

            for anchor in anchors:
                x, y = anchor["position"]
                w, h = anchor["scan_area_size"]

                # Half-width/half-height to place center at (x, y)
                w2 = w / 2.0
                h2 = h / 2.0

                # Define the 4 corners (p0..p3) of this rectangle in CCW order:
                p0 = (x - w2, y - h2, 0.0)  # bottom-left
                p1 = (x - w2, y + h2, 0.0)  # top-left
                p2 = (x + w2, y + h2, 0.0)  # top-right
                p3 = (x + w2, y - h2, 0.0)  # bottom-right

                # Add them to the global list of points
                points.extend([p0, p1, p2, p3])

                # For a quad, the face array entry is:
                #   [4, p0_idx, p1_idx, p2_idx, p3_idx]
                faces.append(4)
                faces.append(p_offset + 0)
                faces.append(p_offset + 1)
                faces.append(p_offset + 2)
                faces.append(p_offset + 3)

                p_offset += 4

            # Build the combined PolyData
            mesh = pv.PolyData()
            mesh.points = np.array(points, dtype=float)
            mesh.faces = np.array(faces, dtype=np.int64)

            return mesh

        def ia_mesh(self, interface_aligner_node):
            pattern = interface_aligner_node.pattern
            glyphs_dict = {
                "color": "green",
                "line_width": 1,
                "opacity": 0.5,
                "group": interface_aligner_node._type,
            }

            if pattern == "Grid":
                count = interface_aligner_node.count
                size = interface_aligner_node.size
                # Using numpy.linspace for exact boundaries
                x_coords = np.linspace(0, size[0], count[0])
                y_coords = np.linspace(0, size[1], count[1])
            elif pattern == "Origin":
                x_coords = np.array([0])
                y_coords = np.array([0])
            elif pattern == "Custom":
                glyphs_dict = {
                    "color": "beige",
                    "line_width": 2.5,
                    "edge_color": "green",
                    "show_edges": True,
                    "opacity": 0.2,
                    "group": interface_aligner_node._type,
                }
                return (
                    self.create_rectangles_mesh(
                        interface_aligner_node.alignment_anchors
                    ),
                    glyphs_dict,
                )
            else:
                print(
                    "WARNING: Allocated interface aligner pattern no known case!"
                )
                return None

            points_2d = np.array([[x, y] for x in x_coords for y in y_coords])

            # Just append z=0:
            points_3d = np.column_stack([points_2d, np.zeros(len(points_2d))])

            cross_shape = self.make_cross(
                size=5.0
            )  # Size the cross as you like

            # Turn the grid points into a PolyData
            cloud = pv.PolyData(points_3d)

            # Glyph the cross shape at each point
            glyphs = cloud.glyph(geom=cross_shape, scale=False)
            glyphs.translate(
                [-glyphs.center[0], -glyphs.center[1], -glyphs.center[2]],
                inplace=True,
            )
            # Return centered glyphs
            return glyphs, glyphs_dict

        def fa_mesh(self, fiber_core_aligner_node):
            default_height = 250
            fa_mesh_dict = {
                "color": "beige",
                "line_width": 1,
                "opacity": 0.2,
                "group": fiber_core_aligner_node._type,
            }
            return (
                pv.Cylinder(
                    center=(0.0, 0.0, -default_height / 2 - 5.5),
                    direction=(0.0, 0.0, 1.0),
                    radius=fiber_core_aligner_node.fiber_radius,
                    height=default_height,
                    resolution=100,
                    capping=True,
                ),
                fa_mesh_dict,
            )

        @staticmethod
        def ma_mesh(marker_aligner):
            marker_image = pv.read_texture(marker_aligner.image.file_path)
            ma_mesh_dict = {
                "texture": marker_image,
                "smooth_shading": True,
                "group": marker_aligner._type,
            }
            ma_label_dict = {
                "color": "black",
                "opacity": 0.5,
                "group": marker_aligner._type,
            }

            ma_meshes = []
            ma_label_meshes = []
            for marker_i in marker_aligner.alignment_anchors:
                # marker_i_total_position = np.add(
                #    marker_i["position"], total_position
                # )

                # Create the plane for each marker
                plane = pv.Plane(
                    center=(0, 0, 0),
                    direction=(0, 0, 1),
                    i_size=marker_aligner.marker_size[0],
                    j_size=marker_aligner.marker_size[1],
                    i_resolution=1,
                    j_resolution=1,
                )
                # Add the label as a Text3D below it
                label_mesh = pv.Text3D(
                    marker_i["label"],
                    depth=0,
                    height=2.5,
                    center=(0, -0.5 * (marker_aligner.marker_size[1] + 5), 0),
                )

                _apply_transforms(
                    plane,
                    all_positions=[marker_i["position"]],
                    all_rotations=[
                        [0, 0, marker_i["rotation"]]
                    ],  # (in-plane rotation only)
                )

                _apply_transforms(
                    label_mesh,
                    all_positions=[marker_i["position"]],
                    all_rotations=[
                        [0, 0, marker_i["rotation"]]
                    ],  # (in-plane rotation only)
                )

                ma_meshes.append(plane)
                ma_label_meshes.append(label_mesh)

            return ma_meshes, ma_label_meshes, ma_mesh_dict, ma_label_dict

        @staticmethod
        def capture_mesh(capture):
            """
            Create a rectangular mesh and corresponding display properties based on the capture type.

            Parameters
            ----------
            capture : object
                An object with attributes `capture_type` and `scan_area_size`. The `capture_type` determines
                the rectangle geometry, and `scan_area_size` defines its dimensions for certain types.

            Returns
            -------
            tuple
                A tuple containing:
                - pv.PolyData: The rectangular mesh.
                - dict: Dictionary with mesh display properties (edges visibility, color, width, opacity).
            """
            # Default mesh display properties
            capture_mesh_dict = {
                "show_edges": True,
                "edge_color": "cyan",
                "line_width": 2.0,
                "style": "wireframe",
            }

            # Define points for the rectangle based on capture type
            if capture.capture_type == "Confocal":
                point_a = (
                    -capture.scan_area_size[0] / 2,
                    capture.scan_area_size[1] / 2,
                    0.0,
                )
                point_b = (
                    capture.scan_area_size[0] / 2,
                    capture.scan_area_size[1] / 2,
                    0.0,
                )
                point_c = (
                    capture.scan_area_size[0] / 2,
                    -capture.scan_area_size[1] / 2,
                    0.0,
                )
            else:
                point_a = (-180.0, 150.0, 0.0)
                point_b = (180.0, 150.0, 0.0)
                point_c = (180.0, -150.0, 0.0)

            # Create the rectangular mesh
            capture_rect = pv.Rectangle([point_a, point_b, point_c])

            return capture_rect, capture_mesh_dict

    return _GroupedPlotter, _apply_transforms, _meshbuilder, pv.MultiBlock()
