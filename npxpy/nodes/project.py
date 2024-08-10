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
import toml
import json
from datetime import datetime
import os
from typing import Dict, Any, List, Union
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
    def __init__(self, objective: str,  # '25x' or '63x' or '*'
                 resin: str,  # can be 'IP-PDMS', 'IPX-S', 'IP-L', 'IP-n162', 'IP-Dip2', 'IP-Dip', 'IP-S', 'IP-Vision', '*'
                 substrate: str  # '*', 'Si' and 'FuSi'
                 ):
        """
        Initialize the project with the specified parameters.

        Parameters:
            objective (str): Objective of the project.
            resin (str): Resin used in the project.
            substrate (str): Substrate used in the project.

        Raises:
            ValueError: If any of the parameters have invalid values.
        """
        valid_objectives = {'25x', '63x', '*'}
        valid_resins = {'IP-PDMS', 'IPX-S', 'IP-L', 'IP-n162', 'IP-Dip2', 'IP-Dip', 'IP-S', 'IP-Vision', '*'}
        valid_substrates = {'*', 'Si', 'FuSi'}

        if objective not in valid_objectives:
            raise ValueError(f"Invalid objective: {objective}. Must be one of {valid_objectives}.")
        if resin not in valid_resins:
            raise ValueError(f"Invalid resin: {resin}. Must be one of {valid_resins}.")
        if substrate not in valid_substrates:
            raise ValueError(f"Invalid substrate: {substrate}. Must be one of {valid_substrates}.")

        super().__init__(node_type='project', name='Project',
                         objective=objective, resin=resin, substrate=substrate)

        self.presets = []
        self.resources = []
        self.project_info = {
            "author": os.getlogin(),
            "objective": objective,
            "resin": resin,
            "substrate": substrate,
            "creation_date": datetime.now().replace(microsecond=0).isoformat()
        }

    def load_resources(self, resources: Union[Resource, List[Resource]]):  # This has to be an object from the class Resource (including inheriting classes)!
        """
        Adds resources to the resources list. The input can be either a list of resources
        or a single resource element.

        Args:
            resources (Resource or list): A list of resources or a single resource element.

        Raises:
            TypeError: If the resources are not of type Resource or list of Resource.
        """
        if not isinstance(resources, list):
            resources = [resources]

        if not all(isinstance(resource, Resource) for resource in resources):
            raise TypeError("All resources must be instances of the Resource class or its subclasses.")

        self.resources.extend(resources)

    def load_presets(self, presets: Union[Preset, List[Preset]]):  # This has to be an object from the class Preset!
        """
        Adds presets to the presets list. The input can be either a list of presets
        or a single preset element.

        Args:
            presets (Preset or list): A list of presets or a single preset element.

        Raises:
            TypeError: If the presets are not of type Preset or list of Preset.
        """
        if not isinstance(presets, list):
            presets = [presets]

        if not all(isinstance(preset, Preset) for preset in presets):
            raise TypeError("All presets must be instances of the Preset class.")

        self.presets.extend(presets)

    def _create_toml_data(self, presets: List[Any], resources: List[Any], nodes: List[Node]) -> str:
        """
        Creates TOML data for the project.

        Args:
            presets (list): List of presets.
            resources (list): List of resources.
            nodes (list): List of nodes.

        Returns:
            str: TOML data as a string.
        """
        data = {
            "presets": [preset.to_dict() for preset in presets],
            "resources": [resource.to_dict() for resource in resources],
            "nodes": [node.to_dict() for node in nodes]
        }
        return toml.dumps(data)

    def _create_project_info(self, project_info_json: Dict[str, Any]) -> str:
        """
        Creates JSON data for project info.

        Args:
            project_info_json (dict): Project information dictionary.

        Returns:
            str: JSON data as a string.
        """
        return json.dumps(project_info_json, indent=4)

    def _add_file_to_zip(self, zip_file: zipfile.ZipFile, file_path: str, arcname: str):
        """
        Adds a file to a zip archive.

        Args:
            zip_file (zipfile.ZipFile): The zip file object.
            file_path (str): Path to the file to add.
            arcname (str): Archive name of the file in the zip.
        """
        with open(file_path, 'rb') as f:
            zip_file.writestr(arcname, f.read())

    def nano(self, project_name: str = 'Project', path: str = './'):
        """
        Creates a .nano file for the project.

        This method collects the current presets and resources, saves them into a .toml file, and packages them
        along with project information into a .nano file.

        Args:
            project_name (str): The name of the project, used as the base name for the .nano file.
            path (str, optional): The directory path where the .nano file will be created. Defaults to './'.
        """
        print('npxpy: Attempting to create .nano-file...')

        # Ensure the path ends with a slash
        if not path.endswith('/'):
            path += '/'

        # Prepare paths and data
        nano_file_path = os.path.join(path, f'{project_name}.nano')
        toml_data = self._create_toml_data(self.presets, self.resources, [self] + self.all_descendants)
        project_info_data = self._create_project_info(self.project_info)

        with zipfile.ZipFile(nano_file_path, 'w', zipfile.ZIP_STORED) as nano_zip:
            # Add the __main__.toml to the zip file
            nano_zip.writestr('__main__.toml', toml_data)
            
            # Add the project_info.json to the zip file
            nano_zip.writestr('project_info.json', project_info_data)

            # Add the resources to the zip file
            for resource in self.resources:
                src_path = resource.fetch_from
                arcname = resource.path
                if os.path.isfile(src_path):
                    self._add_file_to_zip(nano_zip, src_path, arcname)
                else:
                    print(f'File not found: {src_path}')

        print('npxpy: .nano-file created successfully.')