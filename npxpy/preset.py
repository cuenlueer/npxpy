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
import uuid
import os
import copy
from typing import Dict, Any, List


class Preset:
    """
    A class to represent a preset with various parameters related to writing
    and hatching settings.

    Attributes:
        id (str): Unique identifier for the preset.
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
    """

    def __init__(
        self,
        name: str = "25x_IP-n162_default",
        valid_objectives: List[str] = None,
        valid_resins: List[str] = None,
        valid_substrates: List[str] = None,
        writing_speed: float = 250000.0,
        writing_power: float = 50.0,
        slicing_spacing: float = 0.8,
        hatching_spacing: float = 0.3,
        hatching_angle: float = 0.0,
        hatching_angle_increment: float = 0.0,
        hatching_offset: float = 0.0,
        hatching_offset_increment: float = 0.0,
        hatching_back_n_forth: bool = True,
        mesh_z_offset: float = 0.0,
    ):

        # Default lists for valid_objectives, valid_resins, valid_substrates
        self._valid_objectives = None
        self._valid_resins = None
        self._valid_substrates = None

        # Set attributes via setters
        self.name = name
        self.valid_objectives = (
            valid_objectives if valid_objectives else ["25x"]
        )
        self.valid_resins = valid_resins if valid_resins else ["IP-n162"]
        self.valid_substrates = valid_substrates if valid_substrates else ["*"]
        self.writing_speed = writing_speed
        self.writing_power = writing_power
        self.slicing_spacing = slicing_spacing
        self.hatching_spacing = hatching_spacing
        self.hatching_angle = hatching_angle
        self.hatching_angle_increment = hatching_angle_increment
        self.hatching_offset = hatching_offset
        self.hatching_offset_increment = hatching_offset_increment
        self.hatching_back_n_forth = hatching_back_n_forth
        self.mesh_z_offset = mesh_z_offset
        self.grayscale_multilayer_enabled = False
        self.grayscale_layer_profile_nr_layers = 6
        self.grayscale_writing_power_minimum = 0.0
        self.grayscale_exponent = 1.0
        self.id = str(uuid.uuid4())

    # Setters and validation logic for all attributes
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        value = str(value)
        if not isinstance(value, str) or not value.strip():
            raise ValueError("name must be a non-empty string.")
        self._name = value

    @property
    def valid_objectives(self):
        return self._valid_objectives

    @valid_objectives.setter
    def valid_objectives(self, value):
        valid_objectives_set = {"25x", "63x", "*"}
        if not set(value).issubset(valid_objectives_set):
            raise ValueError(f"Invalid valid_objectives: {value}")
        self._valid_objectives = value

    @property
    def valid_resins(self):
        return self._valid_resins

    @valid_resins.setter
    def valid_resins(self, value):
        valid_resins_set = {
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
        if not set(value).issubset(valid_resins_set):
            raise ValueError(f"Invalid valid_resins: {value}")
        self._valid_resins = value

    @property
    def valid_substrates(self):
        return self._valid_substrates

    @valid_substrates.setter
    def valid_substrates(self, value):
        valid_substrates_set = {"*", "FuSi", "Si"}
        if not set(value).issubset(valid_substrates_set):
            raise ValueError(f"Invalid valid_substrates: {value}")
        self._valid_substrates = value

    @property
    def writing_speed(self):
        return self._writing_speed

    @writing_speed.setter
    def writing_speed(self, value):
        value = float(value)  # Type coercion
        if value <= 0:
            raise ValueError(
                f"writing_speed must be greater than 0. Got {value}"
            )
        self._writing_speed = value

    @property
    def writing_power(self):
        return self._writing_power

    @writing_power.setter
    def writing_power(self, value):
        value = float(value)  # Type coercion
        if value < 0:
            raise ValueError(
                f"writing_power must be greater or equal to 0. Got {value}"
            )
        self._writing_power = value

    @property
    def slicing_spacing(self):
        return self._slicing_spacing

    @slicing_spacing.setter
    def slicing_spacing(self, value):
        value = float(value)
        if value <= 0:
            raise ValueError(
                f"slicing_spacing must be greater than 0. Got {value}"
            )
        self._slicing_spacing = value

    @property
    def hatching_spacing(self):
        return self._hatching_spacing

    @hatching_spacing.setter
    def hatching_spacing(self, value):
        value = float(value)
        if value <= 0:
            raise ValueError(
                f"hatching_spacing must be greater than 0. Got {value}"
            )
        self._hatching_spacing = value

    @property
    def hatching_angle(self):
        return self._hatching_angle

    @hatching_angle.setter
    def hatching_angle(self, value):
        self._hatching_angle = float(value)

    @property
    def hatching_angle_increment(self):
        return self._hatching_angle_increment

    @hatching_angle_increment.setter
    def hatching_angle_increment(self, value):
        self._hatching_angle_increment = float(value)

    @property
    def hatching_offset(self):
        return self._hatching_offset

    @hatching_offset.setter
    def hatching_offset(self, value):
        self._hatching_offset = float(value)

    @property
    def hatching_offset_increment(self):
        return self._hatching_offset_increment

    @hatching_offset_increment.setter
    def hatching_offset_increment(self, value):
        self._hatching_offset_increment = float(value)

    @property
    def hatching_back_n_forth(self):
        return self._hatching_back_n_forth

    @hatching_back_n_forth.setter
    def hatching_back_n_forth(self, value):
        if not isinstance(value, bool):
            raise ValueError(
                f"hatching_back_n_forth must be a boolean. Got {type(value).__name__}"
            )
        self._hatching_back_n_forth = value

    @property
    def mesh_z_offset(self):
        return self._mesh_z_offset

    @mesh_z_offset.setter
    def mesh_z_offset(self, value):
        self._mesh_z_offset = float(value)

    @property
    def grayscale_layer_profile_nr_layers(self):
        return self._grayscale_layer_profile_nr_layers

    @grayscale_layer_profile_nr_layers.setter
    def grayscale_layer_profile_nr_layers(self, value):
        value = float(value)
        if value < 0:
            raise ValueError(
                f"grayscale_layer_profile_nr_layers must be greater or equal to 0. Got {value}"
            )
        self._grayscale_layer_profile_nr_layers = value

    @property
    def grayscale_writing_power_minimum(self):
        return self._grayscale_writing_power_minimum

    @grayscale_writing_power_minimum.setter
    def grayscale_writing_power_minimum(self, value):
        value = float(value)
        if value < 0:
            raise ValueError(
                f"grayscale_writing_power_minimum must be greater or equal to 0. Got {value}"
            )
        self._grayscale_writing_power_minimum = value

    @property
    def grayscale_exponent(self):
        return self._grayscale_exponent

    @grayscale_exponent.setter
    def grayscale_exponent(self, value):
        value = float(value)
        if value <= 0:
            raise ValueError(
                f"grayscale_exponent must be greater than 0. Got {value}"
            )
        self._grayscale_exponent = value

    def set_grayscale_multilayer(
        self,
        grayscale_layer_profile_nr_layers: float = 6.0,
        grayscale_writing_power_minimum: float = 0.0,
        grayscale_exponent: float = 1.0,
    ) -> "Preset":
        """
        Enable grayscale multilayer and set the related attributes.
        grayscale_layer_profile_nr_layers (float): Number of layers for
            grayscale layer profile.
        grayscale_writing_power_minimum (float): Minimum writing power for
            grayscale.
        grayscale_exponent (float): Grayscale exponent.
        """
        self.grayscale_layer_profile_nr_layers = (
            grayscale_layer_profile_nr_layers
        )
        self.grayscale_writing_power_minimum = grayscale_writing_power_minimum
        self.grayscale_exponent = grayscale_exponent
        self.grayscale_multilayer_enabled = True
        return self

    def duplicate(self) -> "Preset":
        """
        Create a duplicate of the current preset instance.

        Returns:
            Preset: A duplicate of the current preset instance.
        """
        duplicate = copy.copy(self)
        duplicate.id = str(uuid.uuid4())
        return duplicate

    @classmethod
    def load_single(cls, file_path: str, fresh_id: bool = True) -> "Preset":
        """
        Load a single preset from a valid .toml file containing
        preset data only.

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

        with open(file_path, "r") as toml_file:
            data = toml.load(toml_file)

        # Create a new Preset instance using the setters
        try:
            instance = cls(
                name=data.get(
                    "name", os.path.splitext(os.path.basename(file_path))[0]
                ),
                valid_objectives=data.get("valid_objectives", ["25x"]),
                valid_resins=data.get("valid_resins", ["IP-n162"]),
                valid_substrates=data.get("valid_substrates", ["*"]),
                writing_speed=data.get("writing_speed", 250000.0),
                writing_power=data.get("writing_power", 50.0),
                slicing_spacing=data.get("slicing_spacing", 0.8),
                hatching_spacing=data.get("hatching_spacing", 0.3),
                hatching_angle=data.get("hatching_angle", 0.0),
                hatching_angle_increment=data.get(
                    "hatching_angle_increment", 0.0
                ),
                hatching_offset=data.get("hatching_offset", 0.0),
                hatching_offset_increment=data.get(
                    "hatching_offset_increment", 0.0
                ),
                hatching_back_n_forth=data.get("hatching_back_n_forth", True),
                mesh_z_offset=data.get("mesh_z_offset", 0.0),
            )

            instance.grayscale_multilayer_enabled = data.get(
                "grayscale_multilayer_enabled", False
            )
            instance.grayscale_layer_profile_nr_layers = data.get(
                "grayscale_layer_profile_nr_layers", 6
            )
            instance.grayscale_writing_power_minimum = data.get(
                "grayscale_writing_power_minimum", 0.0
            )
            instance.grayscale_exponent = data.get("grayscale_exponent", 1.0)

        except Exception as e:
            raise ValueError(
                f"Error creating Preset from file {file_path}: {e}"
            )

        # Optionally assign a new ID if fresh_id is True
        if not fresh_id:
            instance.id = data.get("id", instance.id)

        return instance

    @classmethod
    def load_multiple(
        cls,
        directory_path: str,
        print_names: bool = False,
        fresh_id: bool = True,
    ) -> List["Preset"]:
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
            if file_name.endswith(".toml"):
                file_path = os.path.join(directory_path, file_name)
                preset = cls.load_single(file_path, fresh_id)
                presets.append(preset)
                if print_names:
                    print(file_name)
        return presets

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the preset to a dictionary format.

        Returns:
            Dict[str, Any]: Dictionary representation of the preset, including
                            attributes starting with '_', but excluding attributes with '__'.
                            Leading '_' is removed from keys in the resulting dictionary.
        """
        preset_dict = {}

        for attr_name, attr_value in self.__dict__.items():
            # Skip attributes that start with two underscores
            # Ensures functional backend implementations via self.__interals
            if attr_name.startswith("__"):
                continue

            # Remove leading single underscore if present
            if attr_name.startswith("_"):
                key = attr_name[1:]  # Remove the leading '_'
            else:
                key = attr_name

            preset_dict[key] = attr_value

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
        elif not file_path.endswith(".toml"):
            file_path += ".toml"

        data = self.to_dict()

        with open(file_path, "w") as toml_file:
            toml.dump(data, toml_file)
