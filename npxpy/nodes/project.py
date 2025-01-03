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
import json
from datetime import datetime
import os
from typing import Dict, Any, List, Union, Optional
import zipfile
from npxpy.nodes.node import Node
from npxpy.resources import Resource
from npxpy.preset import Preset
from npxpy.nodes._viewport_helpers import (
    _GroupedPlotter,
    _apply_transforms,
    _meshbuilder,
)


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
        block_render: Optional[Union[str, List[str]]] = [],
    ):
        """
        Opens a PyVista viewport visualizing the print scenes in this project.
        Does not visualize multiplications caused by Arrays.

        Parameters
        ----------
        title : str, optional
            Title to display in the PyVista window. Default is "Project".
        disable_visibility : str or list of str, optional
            One or more group names whose visibility should be disabled.
            E.g., "scene" or ["scene", "coarse_alignment"].
        block_render : str or list of str, optional
            One or more group names whose initial rendering should be disabled
            when calling the method.
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

        # init the meshbuilder
        meshbuilder = _meshbuilder()

        for node in self.all_descendants:
            all_rotations = [
                getattr(ancestor, "rotation", [0, 0, 0])
                for ancestor in node.all_ancestors
            ]
            all_rotations.reverse()

            ancestor_positions = [
                getattr(ancestor, "position", [0, 0, 0])
                for ancestor in node.all_ancestors
            ]
            all_positions = ancestor_positions
            all_positions.reverse()

            if node._type == "scene" and node._type not in block_render:
                scene = node
                # Create the circle representing the scene

                scene_mesh, scene_mesh_dict = _meshbuilder.scene_mesh(
                    self.objective
                )
                # apply first all_ancestors' rots

                _apply_transforms(
                    scene_mesh,
                    all_positions=all_positions + [scene.position],
                    all_rotations=all_rotations + [scene.rotation],
                )

                # Add to plotter as 'scene' group
                plotter.add_mesh(scene_mesh, **scene_mesh_dict)
            # Structure
            if (
                node._type == "structure"
                and node._mesh
                and node._type not in block_render
            ):
                structure = node
                loaded_mesh = _meshbuilder.load_mesh(structure.mesh.file_path)
                # apply initial mesh transformation
                _apply_transforms(
                    mesh=loaded_mesh,
                    all_positions=[structure.mesh.translation],
                    all_rotations=[structure.mesh.rotation],
                )

                # apply all_ancestors' rots and afterwards structure rotation
                _apply_transforms(
                    mesh=loaded_mesh,
                    all_rotations=all_rotations + [structure.rotation],
                    all_positions=all_positions + [structure.position],
                )

                # Add to plotter
                plotter.add_mesh(
                    loaded_mesh, color=structure.color, group=structure._type
                )

            # Text (structure)
            if (
                node._type == "structure"
                and hasattr(node, "font_size")
                and node._type + "_text" not in block_render
            ):
                text_node = node
                text_mesh, text_mesh_dict = _meshbuilder.txt_mesh(text_node)
                # apply all_ancestors' rots and afterwards structure rotation
                _apply_transforms(
                    mesh=text_mesh,
                    all_rotations=all_rotations + [text_node.rotation],
                    all_positions=all_positions + [text_node.position],
                )

                plotter.add_mesh(text_mesh, **text_mesh_dict)

            # Lens (structure)
            elif (
                node._type == "structure"
                and not node._mesh
                and node._type + "_lens" not in block_render
            ):
                lens = node
                geometry = lens.__dict__["geometry"].copy()
                del (
                    geometry["type"],
                    geometry["nr_radial_segments"],
                    geometry["nr_phi_segments"],
                )
                lens_mesh = meshbuilder.lens_mesh(**geometry)

                _apply_transforms(
                    mesh=lens_mesh,
                    all_rotations=all_rotations + [lens.rotation],
                    all_positions=all_positions + [lens.position],
                )

                plotter.add_mesh(lens_mesh, color=lens.color, group=lens._type)

            # Coarse aligners
            if (
                node._type == "coarse_alignment"
                and node._type not in block_render
            ):
                coarse_aligner = node
                coarse_anchor_mesh, coarse_anchor_mesh_dict = (
                    _meshbuilder.ca_mesh(coarse_aligner)
                )
                # for coarse_anchor_mesh in coarse_anchor_meshes:
                # apply all_ancestors' rots and afterwards mesh rotation
                _apply_transforms(
                    mesh=coarse_anchor_mesh,
                    all_rotations=all_rotations,
                    all_positions=all_positions,
                )

                plotter.add_mesh(coarse_anchor_mesh, **coarse_anchor_mesh_dict)
            # interface aligners
            if (
                node._type == "interface_alignment"
                and node._type not in block_render
            ):
                interface_aligner = node

                ia_mesh, ia_mesh_dict = meshbuilder.ia_mesh(
                    interface_aligner_node=interface_aligner
                )

                _apply_transforms(
                    mesh=ia_mesh,
                    all_rotations=all_rotations,
                    all_positions=all_positions,
                )

                plotter.add_mesh(ia_mesh, **ia_mesh_dict)
            # fiber aligners
            if (
                node._type == "fiber_core_alignment"
                and node._type not in block_render
            ):
                fiber_aligner = node
                fa_mesh, fa_mesh_dict = meshbuilder.fa_mesh(fiber_aligner)

                _apply_transforms(
                    mesh=fa_mesh,
                    all_rotations=all_rotations,
                    all_positions=all_positions,
                )

                plotter.add_mesh(fa_mesh, **fa_mesh_dict)
            # Marker aligners
            if (
                node._type == "marker_alignment"
                and node._type not in block_render
            ):
                marker_aligner = node
                ma_meshes, ma_mesh_dict = _meshbuilder.ma_mesh(marker_aligner)

                for ma_mesh in ma_meshes:

                    # apply all_ancestors' rots
                    _apply_transforms(
                        mesh=ma_mesh,
                        all_rotations=all_rotations,
                        all_positions=all_positions,
                    )

                    plotter.add_mesh(ma_mesh, **ma_mesh_dict)

            #  Edge aligners
            if (
                node._type == "edge_alignment"
                and node._type not in block_render
            ):
                edge_aligner = node
                edge_aligner_meshes, edge_aligner_meshes_dicts = (
                    _meshbuilder.ea_mesh(edge_aligner)
                )

                for mesh, mesh_dict in zip(
                    edge_aligner_meshes, edge_aligner_meshes_dicts
                ):

                    _apply_transforms(
                        mesh,
                        all_positions=[edge_aligner.edge_location + [0]],
                        all_rotations=[
                            [0, 0, edge_aligner.edge_orientation]
                        ],  # (in-plane rotation only)
                    )

                    # apply all_ancestors' rots
                    _apply_transforms(
                        mesh,
                        all_rotations=all_rotations,
                        all_positions=all_positions,
                    )

                    plotter.add_mesh(mesh, **mesh_dict)

            # Dose compensation
            if (
                node._type == "dose_compensation"
                and node._type not in block_render
            ):
                dose_compensation = node

                for mesh, kwargs in _meshbuilder.dc_meshes(
                    dose_compensation.domain_size
                ):
                    _apply_transforms(
                        mesh=mesh,
                        all_rotations=all_rotations
                        + [[0, 0, dose_compensation.edge_orientation]],
                        all_positions=all_positions
                        + [dose_compensation.edge_location],
                    )

                    plotter.add_mesh(mesh, **kwargs)

            # Capture
            if node._type == "capture" and node._type not in block_render:
                capture = node

                capt_mesh, capt_mesh_dict = _meshbuilder.capture_mesh(capture)

                _apply_transforms(
                    mesh=capt_mesh,
                    all_rotations=all_rotations,
                    all_positions=all_positions,
                )

                plotter.add_mesh(capt_mesh, **capt_mesh_dict)

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
