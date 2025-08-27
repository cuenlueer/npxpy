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
import pytomlpp as toml
import json
from datetime import datetime
import os
from typing import Dict, Any, List, Union
import zipfile
from npxpy.nodes.node import Node
from npxpy.resources import Resource
from npxpy.preset import Preset
import warnings


class Project(Node):
    """
    Class: project nodes.

    Attributes:
        presets (list): List of presets for the project.
        resources (list): List of resources for the project.
        project_info (dict): Information about the project including author, objective, resin, substrate, and creation date.
    """

    def __init__(
        self,
        objective: str,
        resin: str,
        substrate: str,
        auto_load_presets: bool = False,
        auto_load_meshes: bool = False,
        auto_load_images: bool = False,
    ):
        """
        Initialize the project with the specified parameters.

        Parameters:
            objective (str): Objective of the project.
            resin (str): Resin used in the project.
            substrate (str): Substrate used in the project.
            auto_load_presets (bool): Whether or not to automatically load any attached presets.
            auto_load_meshes (bool): Whether or not to automatically load any attached meshes.
            auto_load_images (bool): Whether or not to automatically load any attached images.

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
        self._loaded_resource_ids = set()
        self._loaded_preset_ids = set()
        self._auto_load_presets = auto_load_presets
        self._auto_load_meshes = auto_load_meshes
        self._auto_load_images = auto_load_images

    # Setters for the attributes with validation
    @property
    def objective(self):
        return self._objective

    @objective.setter
    def objective(self, value: str):
        valid_objectives = {
            "10x",
            "25x",
            "63x",
            "*",
        }
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

    def load_resources(self, *resourcess: Union[Resource, List[Resource]]):
        """
        Adds resources to the resources list, skipping duplicates based on UUID.
        """
        for resources in resourcess:
            if not isinstance(resources, list):
                resources = [resources]

            if not all(
                isinstance(resource, Resource) for resource in resources
            ):
                raise TypeError(
                    "All resources must be instances of the Resource class or its subclasses."
                )

            for resource in resources:
                if resource.id in self._loaded_resource_ids:
                    warnings.warn(
                        f"Resource with ID {resource.id} already loaded. Skipping."
                    )
                    continue
                self._resources.append(resource)
                self._loaded_resource_ids.add(resource.id)

    def load_presets(self, *presetss: Union[Preset, List[Preset]]):
        """
        Adds presets to the presets list, skipping duplicates based on UUID.
        """
        for presets in presetss:
            if not isinstance(presets, list):
                presets = [presets]

            if not all(isinstance(preset, Preset) for preset in presets):
                raise TypeError(
                    "All presets must be instances of the Preset class."
                )

            for preset in presets:
                if preset.id in self._loaded_preset_ids:
                    warnings.warn(
                        f"Preset with ID {preset.id} already loaded. Skipping."
                    )
                    continue
                self._presets.append(preset)
                self._loaded_preset_ids.add(preset.id)

    def _auto_load_resources_presets(self):
        """
        Loads all Resource/Preset nodes into the Project node they
        are attached to.
        """
        all_structures = self.grab_all_nodes_bfs("structure")
        all_marker_aligners = self.grab_all_nodes_bfs("marker_alignment")

        if self._auto_load_meshes:
            all_meshes = [
                structure.mesh
                for structure in all_structures
                if structure._mesh
            ]
            self.load_resources(all_meshes)

        if self._auto_load_presets:
            all_presets = [structure.preset for structure in all_structures]
            self.load_presets(all_presets)

        if self._auto_load_images:
            all_images = [
                marker_aligner.image for marker_aligner in all_marker_aligners
            ]
            self.load_resources(all_images)

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

        # Trigger user warning if project contains structures outside scenes
        for i_node in self.all_descendants:
            if i_node._type == "structure":
                if not "scene" in [i._type for i in self.all_ancestors]:
                    UserWarning("Structures have to be inside Scene nodes!")

        # Autoload presets/resources if desired
        if any(
            [
                self._auto_load_images,
                self._auto_load_meshes,
                self._auto_load_presets,
            ]
        ):
            self._auto_load_resources_presets()

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
            already_zipped_resources = set()
            for resource in self._resources:
                src_path = resource.file_path
                arcname = resource.safe_path
                if (
                    os.path.isfile(src_path)
                    and arcname not in already_zipped_resources
                ):
                    self._add_file_to_zip(nano_zip, src_path, arcname)
                    already_zipped_resources.add(arcname)
                elif not os.path.isfile(src_path):
                    print(f"File not found: {src_path}")
                else:
                    print(f"File already loaded: {src_path}")
        print("npxpy: .nano-file created successfully.")

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
