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
import uuid
import os
import copy
from typing import Dict, Any, List
from pydantic import BaseModel, Field, ValidationError, model_validator

class Preset(BaseModel):
    """
    A class to represent a preset with various parameters related to writing and hatching settings.
    
    Attributes:
        name (str): Name of the preset.
        valid_objectives (List[str]): Valid objectives for the preset.
        valid_resins (List[str]): Valid resins for the preset.
        valid_substrates (List[str]): Valid substrates for the preset.
        writing_speed (float): Writing speed.
        writing_power (float): Writing power.
        slicing_spacing (float): Slicing spacing.
        hatching_spacing (float): Hatching spacing.
        hatching_angle (float): Hatching angle.
        hatching_angle_increment (float): Hatching angle increment.
        hatching_offset (float): Hatching offset.
        hatching_offset_increment (float): Hatching offset increment.
        hatching_back_n_forth (bool): Whether hatching is back and forth.
        mesh_z_offset (float): Mesh Z offset.
        grayscale_layer_profile_nr_layers (float): Number of layers for grayscale layer profile.
        grayscale_writing_power_minimum (float): Minimum writing power for grayscale.
        grayscale_exponent (float): Grayscale exponent.
        unique_attributes (Dict[str, Any]): Additional dynamic attributes.
    """
    class Config:
        extra = 'allow'
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = '25x_IP-n162'
    valid_objectives: List[str] = Field(default_factory=lambda: ["25x"])
    valid_resins: List[str] = Field(default_factory=lambda: ["IP-n162"])
    valid_substrates: List[str] = Field(default_factory=lambda: ["*"])
    writing_speed: float = Field(gt=0, default=250000.0)
    writing_power: float = Field(ge=0, default=50.0)
    slicing_spacing: float = Field(gt=0, default=0.8)
    hatching_spacing: float = Field(gt=0, default=0.3)
    hatching_angle: float = 0.0
    hatching_angle_increment: float = 0.0
    hatching_offset: float = 0.0
    hatching_offset_increment: float = 0.0
    hatching_back_n_forth: bool = True
    mesh_z_offset: float = 0.0
    grayscale_multilayer_enabled: bool = False
    grayscale_layer_profile_nr_layers: float = Field(ge=0, default=6)
    grayscale_writing_power_minimum: float = Field(ge=0, default=0.0)
    grayscale_exponent: float = Field(gt=0, default=1.0)
    unique_attributes: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='before')
    def validate_list(cls, values):
        for key in ['valid_objectives', 'valid_resins', 'valid_substrates']:
            if isinstance(values.get(key), str):
                values[key] = [values[key]]
        return values

    @model_validator(mode='after')
    def validate_values(cls, values):
        valid_objectives = {'25x', '63x', '*'}
        valid_resins = {'IP-PDMS', 'IPX-S', 'IP-L', 'IP-n162', 'IP-Dip2', 'IP-Dip', 'IP-S', 'IP-Visio', '*'}
        valid_substrates = {'*', 'FuSi', 'Si'}

        if not set(values.valid_objectives).issubset(valid_objectives):
            raise ValueError(f"Invalid valid_objectives: {values.valid_objectives}")
        if not set(values.valid_resins).issubset(valid_resins):
            raise ValueError(f"Invalid valid_resins: {values.valid_resins}")
        if not set(values.valid_substrates).issubset(valid_substrates):
            raise ValueError(f"Invalid valid_substrates: {values.valid_substrates}")

        return values

    def set_grayscale_multilayer(
        self, 
        grayscale_layer_profile_nr_layers: float = 6.0, 
        grayscale_writing_power_minimum: float = 0.0, 
        grayscale_exponent: float = 1.0
    ) -> 'Preset':
        """
        Enable grayscale multilayer and set the related attributes.

        Parameters:
            grayscale_layer_profile_nr_layers (float): Number of layers for grayscale layer profile.
            grayscale_writing_power_minimum (float): Minimum writing power for grayscale.
            grayscale_exponent (float): Grayscale exponent.

        Returns:
            Preset: The instance with updated grayscale multilayer settings.

        Raises:
            ValueError: If any of the parameters are invalid.
        """
        if grayscale_layer_profile_nr_layers < 0:
            raise ValueError("grayscale_layer_profile_nr_layers must be greater or equal to 0.")
        if grayscale_writing_power_minimum < 0:
            raise ValueError("grayscale_writing_power_minimum must be greater or equal to 0.")
        if grayscale_exponent <= 0:
            raise ValueError("grayscale_exponent must be greater than 0.")

        self.grayscale_multilayer_enabled = True
        self.grayscale_layer_profile_nr_layers = grayscale_layer_profile_nr_layers
        self.grayscale_writing_power_minimum = grayscale_writing_power_minimum
        self.grayscale_exponent = grayscale_exponent
        return self

    def duplicate(self) -> 'Preset':
        """
        Create a duplicate of the current preset instance.

        Returns:
            Preset: A duplicate of the current preset instance.
        """
        duplicate = copy.copy(self)
        duplicate.id = str(uuid.uuid4())
        return duplicate

    @classmethod
    def load_single(cls, file_path: str, fresh_id: bool = True) -> 'Preset':
        """
        Load a single preset from a .toml file.

        Parameters:
            file_path (str): The path to the .toml file.
            fresh_id (bool): Whether to assign a fresh ID to the loaded preset.

        Returns:
            Preset: The loaded preset instance.

        Raises:
            FileNotFoundError: If the file at file_path does not exist.
            toml.TomlDecodeError: If there is an error decoding the TOML file.
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r') as toml_file:
            data = toml.load(toml_file)

        # Get the valid fields of the model
        valid_fields = cls.__fields__.keys()

        # Filter out invalid keys from data
        valid_data = {key: value for key, value in data.items() if key in valid_fields}

        if 'name' not in valid_data:
            # Extract the file name without the extension if not in .toml
            name = os.path.splitext(os.path.basename(file_path))[0]
        else:
            name = valid_data.pop('name')

        try:
            cls_instance = cls(name=name, **valid_data)
        except ValidationError as e:
            raise ValidationError(model=cls, errors=e.errors())

        if not fresh_id:
            cls_instance.id = data.get('id', cls_instance.id)

        return cls_instance

    @classmethod
    def load_multiple(cls, directory_path: str, print_names: bool = False, fresh_id: bool = True) -> List['Preset']:
        """
        Load multiple presets from a directory containing .toml files.

        Parameters:
            directory_path (str): The path to the directory containing .toml files.
            print_names (bool): If True, print the names of the files in the order they are loaded.
            fresh_id (bool): Whether to assign fresh IDs to the loaded presets.

        Returns:
            List[Preset]: A list of loaded preset instances.

        Raises:
            FileNotFoundError: If the directory_path does not exist.
        """
        if not os.path.isdir(directory_path):
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        presets = []
        for file_name in sorted(os.listdir(directory_path)):
            if file_name.endswith('.toml'):
                file_path = os.path.join(directory_path, file_name)
                preset = cls.load_single(file_path, fresh_id)
                presets.append(preset)
                if print_names:
                    print(file_name)
        return presets

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the preset and its unique attributes to a dictionary format.

        Returns:
            Dict[str, Any]: Dictionary representation of the preset.
        """
        preset_dict = self.dict(exclude={'unique_attributes'})
        preset_dict.update(self.unique_attributes)
        return preset_dict

    def export(self, file_path: str = None) -> None:
        """
        Export the preset to a file that can be loaded by nanoPrintX and/or npxpy.

        Parameters:
            file_path (str): The path to the .toml file to be created. If not provided,
                             defaults to the current directory with the preset's name.

        Raises:
            IOError: If there is an error writing to the file.
        """
        if file_path is None:
            file_path = f"{self.name}.toml"
        elif not file_path.endswith('.toml'):
            file_path += '.toml'

        data = self.to_dict()

        with open(file_path, 'w') as toml_file:
            toml.dump(data, toml_file)