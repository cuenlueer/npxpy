# -*- coding: utf-8 -*-
"""
npxpy
Created on Thu Feb 29 11:49:17 2024

@author: Caghan Uenlueer
Neuromorphic Quantumphotonics
Heidelberg University
E-Mail:	caghan.uenlueer@kip.uni-heidelberg.de

This file is part of npxpy (formerly nanoAPI), which is licensed under the GNU Lesser General Public License v3.0.
You can find a copy of this license at https://www.gnu.org/licenses/lgpl-3.0.html
"""
import pytomlpp as toml
import pyvista as pv
from pyvistaqt import BackgroundPlotter
import numpy as np
import json
from datetime import datetime
import os
from typing import Dict, Any, List, Union, Optional
import zipfile
from npxpy.nodes.node import Node
from npxpy.resources import Resource
from npxpy.preset import Preset


class Project(Node):
    """
    Class: project nodes.

    Attributes:
        presets (list): List of presets for the project.
        resources (list): List of resources for the project.
        project_info (dict): Information about the project including author, objective, resin, substrate, and creation date.
    """

    def __init__(self, objective: str, resin: str, substrate: str):
        """
        Initialize the project with the specified parameters.

        Parameters:
            objective (str): Objective of the project.
            resin (str): Resin used in the project.
            substrate (str): Substrate used in the project.

        Raises:
            ValueError: If any of the parameters have invalid values.
        """
        super().__init__(node_type="project", name="Project")

        self.objective = objective
        self.resin = resin
        self.substrate = substrate

        self._presets = []
        self._resources = []
        self.project_info = {
            "author": os.getlogin(),
            "objective": objective,
            "resist": resin,
            "substrate": substrate,
            "creation_date": datetime.now().replace(microsecond=0).isoformat(),
        }
        self._visibility_in_plotter_disabled = []

    # Setters for the attributes with validation
    @property
    def objective(self):
        return self._objective

    @objective.setter
    def objective(self, value: str):
        valid_objectives = {"25x", "63x", "*"}
        if value not in valid_objectives:
            raise ValueError(
                f"Invalid objective: {value}. Must be one of {valid_objectives}."
            )
        self._objective = value

    @property
    def resin(self):
        return self._resin

    @resin.setter
    def resin(self, value: str):
        valid_resins = {
            "IP-PDMS",
            "IPX-S",
            "IP-L",
            "IP-n162",
            "IP-Dip2",
            "IP-Dip",
            "IP-S",
            "IP-Visio",
            "*",
        }
        if value not in valid_resins:
            raise ValueError(
                f"Invalid resin: {value}. Must be one of {valid_resins}."
            )
        self._resin = value

    @property
    def substrate(self):
        return self._substrate

    @substrate.setter
    def substrate(self, value: str):
        valid_substrates = {"*", "Si", "FuSi"}
        if value not in valid_substrates:
            raise ValueError(
                f"Invalid substrate: {value}. Must be one of {valid_substrates}."
            )
        self._substrate = value

    # Read-only public properties
    @property
    def presets(self):
        """Get the list of presets."""
        return self._presets

    @property
    def resources(self):
        """Get the list of resources."""
        return self._resources

    @property
    def _visibility_in_plotter_disabled(self):
        return self.__visibility_in_plotter_disabled

    @_visibility_in_plotter_disabled.setter
    def _visibility_in_plotter_disabled(self, value):
        # Check if value is already an iterable (but not a string!)
        # If it's not an iterable (or is just a single string), wrap it in a list.
        if isinstance(value, str) or not hasattr(value, "__iter__"):
            value = [value]

        # Optionally convert it to a list if it's, say, a tuple or another iterable
        self.__visibility_in_plotter_disabled = list(value)

    def load_resources(self, resources: Union[Resource, List[Resource]]):
        """
        Adds resources to the resources list.
        """
        if not isinstance(resources, list):
            resources = [resources]

        if not all(isinstance(resource, Resource) for resource in resources):
            raise TypeError(
                "All resources must be instances of the Resource class or its subclasses."
            )

        self._resources.extend(resources)  # Modifies the internal _resources

    def load_presets(self, presets: Union[Preset, List[Preset]]):
        """
        Adds presets to the presets list.
        """
        if not isinstance(presets, list):
            presets = [presets]

        if not all(isinstance(preset, Preset) for preset in presets):
            raise TypeError(
                "All presets must be instances of the Preset class."
            )

        self._presets.extend(presets)  # Modifies the internal _presets

    def _create_toml_data(
        self, presets: List[Any], resources: List[Any], nodes: List[Node]
    ) -> str:
        """
        Creates TOML data for the project.
        """
        data = {
            "presets": [preset.to_dict() for preset in presets],
            "resources": [resource.to_dict() for resource in resources],
            "nodes": [node.to_dict() for node in nodes],
        }
        return toml.dumps(data)

    def _create_project_info(self, project_info_json: Dict[str, Any]) -> str:
        """
        Creates JSON data for project info.
        """
        return json.dumps(project_info_json, indent=4)

    def _add_file_to_zip(
        self, zip_file: zipfile.ZipFile, file_path: str, arcname: str
    ):
        """
        Adds a file to a zip archive.
        """
        with open(file_path, "rb") as f:
            zip_file.writestr(arcname, f.read())

    def nano(self, project_name: str = "Project", path: str = "./"):
        """
        Creates a .nano file for the project.
        """
        print("npxpy: Attempting to create .nano-file...")

        # Ensure the path ends with a slash
        if not path.endswith("/"):
            path += "/"

        # Prepare paths and data
        nano_file_path = os.path.join(path, f"{project_name}.nano")
        toml_data = self._create_toml_data(
            self._presets, self._resources, [self] + self.all_descendants
        )
        project_info_data = self._create_project_info(self.project_info)

        with zipfile.ZipFile(
            nano_file_path, "w", zipfile.ZIP_STORED
        ) as nano_zip:
            # Add the __main__.toml to the zip file
            nano_zip.writestr("__main__.toml", toml_data)

            # Add the project_info.json to the zip file
            nano_zip.writestr("project_info.json", project_info_data)

            # Add the resources to the zip file
            for resource in self._resources:
                src_path = resource.file_path
                arcname = resource.safe_path
                if os.path.isfile(src_path):
                    self._add_file_to_zip(nano_zip, src_path, arcname)
                else:
                    print(f"File not found: {src_path}")

        print("npxpy: .nano-file created successfully.")

    def viewport(
        self,
        title: str = "Project",
        disable_visibility: Optional[Union[str, List[str]]] = None,
    ):
        """
        Opens a PyVista viewport visualizing the print scenes in this project.

        Parameters
        ----------
        title : str, optional
            Title to display in the PyVista window. Default is "Project".
        disable_visibility : str or list of str, optional
            One or more group names whose visibility should be disabled.
            E.g., "scene" or ["scene", "coarse_alignment"].

        Returns
        -------
        _GroupedPlotter
            The customized plotter instance after drawing all meshes.

        Examples
        --------
        >>> # Basic usage without disabling any groups
        >>> my_project.viewport()

        >>> # Disable visibility for scenes and coarse alignments
        >>> my_project.viewport(disable_visibility=["scene", "coarse_alignment"])
        """
        if disable_visibility is None:
            disable_visibility = []

        # Create the plotter
        plotter = _GroupedPlotter(
            title=f"npxpy - Project Viewport ({title})",
            update_app_icon=False,
        )

        # Grid, axes, background
        plotter.show_grid(
            grid="back",
            location="outer",
            color="gray",
            xtitle="x",
            ytitle="y",
            ztitle="z",
            show_zlabels=True,
            padding=0.1,
            font_size=8,
        )
        plotter.show_axes()
        plotter.view_isometric()
        plotter.set_background("white")

        # Add logo widget
        HERE = os.path.dirname(__file__)
        TWO_LEVELS_UP = os.path.abspath(os.path.join(HERE, "..", ".."))
        plotter.add_logo_widget(
            logo=os.path.join(TWO_LEVELS_UP, "docs/images/logo.png"),
            opacity=0.75,
            size=(0.15, 0.15),
            position=(0.84, 0.86),
        )

        for node in self.all_descendants:
            all_rotations = [
                getattr(ancestor, "rotation", [0, 0, 0])
                for ancestor in node.all_ancestors
            ]
            all_rotations.reverse()
            # if node._type == "structure":
            #  print(all_rotations)

            ancestor_positions = [
                getattr(ancestor, "position", [0, 0, 0])
                for ancestor in node.all_ancestors
            ]
            total_position = [
                sum(elements) for elements in zip(*ancestor_positions)
            ]
            print(total_position)
            if node._type == "scene":
                scene = node
                # Decide on circle radius
                circle_radius = 280 if self.objective == "25x" else 139

                circle_center = np.add(scene.position, total_position)

                # Create the circle representing the scene
                scene_view = pv.Circle(radius=circle_radius, resolution=100)

                # apply first all_ancestors' rots

                final_basis = _apply_transforms(
                    mesh=scene_view,
                    vector_x=np.array([1.0, 0.0, 0.0]),
                    vector_y=np.array([0.0, 1.0, 0.0]),
                    vector_z=np.array([0.0, 0.0, 1.0]),
                    all_rotations=all_rotations,
                    position=[0, 0, 0],
                )

                _apply_transforms(
                    scene_view,
                    position=circle_center,
                    all_rotations=[scene.rotation],
                    vector_x=final_basis[0],
                    vector_y=final_basis[1],
                    vector_z=final_basis[2],
                )

                # Add to plotter as 'scene' group
                plotter.add_mesh(
                    scene_view,
                    color="lightgrey",
                    line_width=2,
                    style="wireframe",
                    opacity=0.1,
                    group=scene._type,
                )

            if node._type == "structure" and node._mesh:
                structure = node
                loaded_mesh = pv.read(structure.mesh.file_path)

                total_struct_position = np.add(
                    structure.position, total_position
                )

                _apply_transforms(
                    mesh=loaded_mesh,
                    all_rotations=[structure.mesh.rotation],
                    vector_x=np.array([1.0, 0.0, 0.0]),
                    vector_y=np.array([0.0, 1.0, 0.0]),
                    vector_z=np.array([0.0, 0.0, 1.0]),
                )

                # apply all_ancestors' rots and afterwards mesh rotation
                _ = _apply_transforms(
                    mesh=loaded_mesh,
                    vector_x=np.array([1.0, 0.0, 0.0]),
                    vector_y=np.array([0.0, 1.0, 0.0]),
                    vector_z=np.array([0.0, 0.0, 1.0]),
                    all_rotations=all_rotations + [structure.rotation],
                    position=total_struct_position,
                )

                # Add to plotter
                plotter.add_mesh(
                    loaded_mesh, color=structure.color, group=structure._type
                )

            # Marker aligners (in-plane rotation only)
            if node._type == "marker_alignment":
                marker_aligner = node
                marker_image = pv.read_texture(marker_aligner.image.file_path)

                for marker_i in marker_aligner.alignment_anchors:
                    marker_i_total_position = np.add(
                        marker_i["position"], total_position
                    )

                    # Create the plane for each marker
                    plane = pv.Plane(
                        center=(0, 0, 0),
                        direction=(0, 0, 1),
                        i_size=marker_aligner.marker_size[0],
                        j_size=marker_aligner.marker_size[1],
                        i_resolution=1,
                        j_resolution=1,
                    )
                    # apply all_ancestors' rots
                    final_basis = _apply_transforms(
                        mesh=plane,
                        vector_x=np.array([1.0, 0.0, 0.0]),
                        vector_y=np.array([0.0, 1.0, 0.0]),
                        vector_z=np.array([0.0, 0.0, 1.0]),
                        all_rotations=all_rotations,
                        position=[0, 0, 0],
                    )

                    _apply_transforms(
                        plane,
                        position=marker_i_total_position,
                        all_rotations=[[0, 0, marker_i["rotation"]]],
                        vector_x=final_basis[0],
                        vector_y=final_basis[1],
                        vector_z=final_basis[2],
                    )

                    plotter.add_mesh(
                        plane,
                        texture=marker_image,
                        smooth_shading=True,
                        group=marker_aligner._type,
                    )

            # Coarse aligners
            if node._type == "coarse_alignment":
                coarse_aligner = node
                for anchor_i in coarse_aligner.alignment_anchors:
                    # Create a line from (0,0,0) to (0,0,100), then transform
                    coarse_anchor_mesh = pv.Line((0, 0, 0), (0, 0, 100))
                    anchor_pos = np.add(anchor_i["position"], total_position)

                    _apply_transforms(
                        coarse_anchor_mesh,
                        position=anchor_pos,
                        all_rotations=[[0, 0, 0]],
                        vector_x=np.array([1, 0, 0]),
                        vector_y=np.array([0, 1, 0]),
                        vector_z=np.array([0, 0, 1]),
                    )

                    # apply all_ancestors' rots and afterwards mesh rotation
                    final_basis = _apply_transforms(
                        mesh=coarse_anchor_mesh,
                        vector_x=np.array([1.0, 0.0, 0.0]),
                        vector_y=np.array([0.0, 1.0, 0.0]),
                        vector_z=np.array([0.0, 0.0, 1.0]),
                        all_rotations=all_rotations,
                        position=[0, 0, 0],
                    )

                    plotter.add_mesh(
                        coarse_anchor_mesh,
                        color="orange",
                        line_width=10,
                        opacity=0.5,
                        group=coarse_aligner._type,
                    )

        # Disable visibility for certain groups if requested
        self._visibility_in_plotter_disabled = disable_visibility
        for grp in self._visibility_in_plotter_disabled:
            plotter.disable_visibility(grp)

        # Show the viewport
        plotter.show()
        return plotter

    def to_dict(self) -> Dict:
        """
        Convert the Project object into a dictionary.
        """
        node_dict = super().to_dict()
        node_dict.update(
            {
                "objective": self.objective,
                "resin": self.resin,
                "substrate": self.substrate,
            }
        )
        return node_dict


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
        self.actor_groups = {}  # dictionary to store lists of actors by group

    def add_mesh(self, mesh, group=None, **kwargs):
        """
        A wrapper around plotter.add_mesh that also associates the actor with a group.
        """
        actor = super().add_mesh(mesh, **kwargs)  # get the actor from PyVista
        if group is not None:
            if group not in self.actor_groups:
                self.actor_groups[group] = []
            self.actor_groups[group].append(actor)
        return actor

    def set_group_visibility(self, group, visible=True):
        """
        Toggle visibility of all actors in a given group.
        """
        if group not in self.actor_groups:
            return  # group doesn't exist, do nothing
        for actor in self.actor_groups[group]:
            actor.SetVisibility(visible)
        self.render()

    def disable_visibility(self, group):
        self.set_group_visibility(group, visible=False)

    def enable_visibility(self, group):
        self.set_group_visibility(group, visible=True)


def _apply_transforms(
    mesh: pv.DataSet,
    all_rotations: [np.ndarray],
    vector_x: np.ndarray,
    vector_y: np.ndarray,
    vector_z: np.ndarray,
    position: Optional[np.ndarray] = [0, 0, 0],
    pivot: Optional[np.ndarray] = [0, 0, 0],
    in_plane_only: bool = False,
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

    for rotation in all_rotations:

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

    mesh.translate(position, inplace=True)
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
    return v * cos_t + np.cross(k, v) * sin_t + k * np.dot(k, v) * (1 - cos_t)
