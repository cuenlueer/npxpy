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
from typing import Dict, Any, List, Union
from npxpy.nodes.node import Node


class DoseCompensation(Node):
    """
    A class to represent dose compensation with various attributes and methods
    for managing dose settings.

    Attributes:
        edge_location (List[Union[float, int]]): Location of the edge [x, y, z] in micrometers.
        edge_orientation (Union[float, int]): Orientation of the edge in degrees.
        domain_size (List[Union[float, int]]): Size of the domain [width, height, depth] in micrometers.
        gain_limit (Union[float, int]): Gain limit for the dose compensation.
    """

    def __init__(
        self,
        name: str = "Dose compensation 1",
        edge_location: List[Union[float, int]] = [0.0, 0.0, 0.0],
        edge_orientation: Union[float, int] = 0.0,
        domain_size: List[Union[float, int]] = [200.0, 100.0, 100.0],
        gain_limit: Union[float, int] = 2.0,
    ):
        """
        Initialize the dose compensation with the specified parameters.

        Parameters:
            name (str): Name of the dose compensation.
            edge_location (List[Union[float, int]]): Location of the edge [x, y, z] in micrometers.
            edge_orientation (Union[float, int]): Orientation of the edge in degrees.
            domain_size (List[Union[float, int]]): Size of the domain [width, height, depth] in micrometers.
            gain_limit (Union[float, int]): Gain limit, must be >= 1.
        """
        super().__init__(node_type="dose_compensation", name=name)
        self.edge_location = edge_location
        self.edge_orientation = edge_orientation
        self.domain_size = domain_size
        self.gain_limit = gain_limit

    @property
    def edge_location(self):
        """Get the location of the edge."""
        return self._edge_location

    @edge_location.setter
    def edge_location(self, value: List[Union[float, int]]):
        """
        Set the location of the edge.

        Parameters:
            value (List[Union[float, int]]): The edge location [x, y, z].

        Raises:
            TypeError: If edge_location is not a list of three numbers.
        """
        if len(value) != 3 or not all(
            isinstance(val, (float, int)) for val in value
        ):
            raise TypeError("edge_location must be a list of three numbers.")
        self._edge_location = value

    @property
    def edge_orientation(self):
        """Get the edge orientation."""
        return self._edge_orientation

    @edge_orientation.setter
    def edge_orientation(self, value: Union[float, int]):
        """
        Set the edge orientation.

        Parameters:
            value (Union[float, int]): The edge orientation in degrees.

        Raises:
            TypeError: If the value is not a number.
        """
        if not isinstance(value, (float, int)):
            raise TypeError("edge_orientation must be a float or an int.")
        self._edge_orientation = value

    @property
    def domain_size(self):
        """Get the size of the domain."""
        return self._domain_size

    @domain_size.setter
    def domain_size(self, value: List[Union[float, int]]):
        """
        Set the domain size.

        Parameters:
            value (List[Union[float, int]]): The domain size [width, height, depth].

        Raises:
            TypeError: If domain_size is not a list of three numbers.
            ValueError: If any element in domain_size is <= 0.
        """
        if len(value) != 3 or not all(
            isinstance(val, (float, int)) for val in value
        ):
            raise TypeError("domain_size must be a list of three numbers.")
        if any(size <= 0 for size in value):
            raise ValueError(
                "All elements in domain_size must be greater than 0."
            )
        self._domain_size = value

    @property
    def gain_limit(self):
        """Get the gain limit."""
        return self._gain_limit

    @gain_limit.setter
    def gain_limit(self, value: Union[float, int]):
        """
        Set the gain limit.

        Parameters:
            value (Union[float, int]): The gain limit.

        Raises:
            ValueError: If the gain limit is less than 1.
        """
        if value < 1:
            raise ValueError("gain_limit must be greater than or equal to 1.")
        self._gain_limit = value

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the DoseCompensation object into a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the object.
        """
        node_dict = super().to_dict()  # Get the basic dict from Node
        node_dict.update(
            {
                "position_local_cos": self.edge_location,
                "z_rotation_local_cos": self.edge_orientation,
                "size": self.domain_size,
                "gain_limit": self.gain_limit,
            }
        )
        return node_dict


class Capture(Node):
    """
    A class to represent a capture node with attributes and methods for managing
    capture settings.

    Attributes:
        capture_type (str): The type of capture (e.g., 'Camera', 'Confocal').
        laser_power (float): The laser power for the capture.
        scan_area_size (List[float]): The size of the scan area [width, height].
        scan_area_res_factors (List[float]): The resolution factors for the scan area.
    """

    def __init__(self, name: str = "Capture"):
        """
        Initialize the capture node.

        Parameters:
            name (str): Name of the capture node.
        """
        super().__init__(node_type="capture", name=name)
        self.capture_type = "Camera"
        self._laser_power = None
        self._scan_area_size = None
        self._scan_area_res_factors = None
        self.laser_power = 0.5  # Using setter for validation
        self.scan_area_size = [100.0, 100.0]  # Using setter for validation
        self.scan_area_res_factors = [1.0, 1.0]  # Using setter for validation

    @property
    def laser_power(self):
        """Get the laser power."""
        return self._laser_power

    @laser_power.setter
    def laser_power(self, value: float):
        """
        Set the laser power.

        Parameters:
            value (float): The laser power, must be greater or equal to 0.

        Raises:
            ValueError: If laser_power is less than 0.
        """
        if not isinstance(value, (float, int)) or value < 0:
            raise ValueError("laser_power must be greater or equal to 0.")
        self._laser_power = value

    @property
    def scan_area_size(self):
        """Get the scan area size."""
        return self._scan_area_size

    @scan_area_size.setter
    def scan_area_size(self, value: List[float]):
        """
        Set the scan area size.

        Parameters:
            value (List[float]): The scan area size [width, height].

        Raises:
            ValueError: If any value in scan_area_size is less than 0.
        """
        if len(value) != 2 or not all(
            isinstance(size, (float, int)) for size in value
        ):
            raise TypeError(
                "scan_area_size must be a list of two numbers greater or equal to 0."
            )
        if any(size < 0 for size in value):
            raise ValueError(
                "All elements in scan_area_size must be greater or equal to 0."
            )
        self._scan_area_size = value

    @property
    def scan_area_res_factors(self):
        """Get the scan area resolution factors."""
        return self._scan_area_res_factors

    @scan_area_res_factors.setter
    def scan_area_res_factors(self, value: List[float]):
        """
        Set the scan area resolution factors.

        Parameters:
            value (List[float]): The scan area resolution factors [factor_x, factor_y].

        Raises:
            ValueError: If any value in scan_area_res_factors is less than or equal to 0.
        """
        if len(value) != 2 or not all(
            isinstance(factor, (float, int)) for factor in value
        ):
            raise TypeError(
                "scan_area_res_factors must be a list of two numbers greater than 0."
            )
        if any(factor <= 0 for factor in value):
            raise ValueError(
                "All elements in scan_area_res_factors must be greater than 0."
            )
        self._scan_area_res_factors = value

    def confocal(
        self,
        laser_power: float = 0.5,
        scan_area_size: List[float] = [100.0, 100.0],
        scan_area_res_factors: List[float] = [1.0, 1.0],
    ) -> "Capture":
        """
        Configure the capture node for confocal capture.

        Parameters:
            laser_power (float): The laser power, must be greater or equal to 0.
            scan_area_size (List[float]): The scan area size [width, height].
            scan_area_res_factors (List[float]): The resolution factors for the scan area.

        Returns:
            Capture: The updated Capture object.
        """
        self.laser_power = laser_power
        self.scan_area_size = scan_area_size
        self.scan_area_res_factors = scan_area_res_factors
        self.capture_type = "Confocal"
        return self

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Capture object into a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the Capture object.
        """
        node_dict = super().to_dict()  # Get the basic dict from Node
        node_dict.update(
            {
                "capture_type": self.capture_type,
                "laser_power": self.laser_power,
                "scan_area_size": self.scan_area_size,
                "scan_area_res_factors": self.scan_area_res_factors,
            }
        )
        return node_dict


class StageMove(Node):
    """
    A class to represent a stage move node with a specified stage position.

    Attributes:
        target_position (List[float]): The target position of the stage [x, y, z].
    """

    def __init__(
        self,
        name: str = "Stage move",
        stage_position: List[float] = [0.0, 0.0, 0.0],
    ):
        """
        Initialize the stage move node.

        Parameters:
            name (str): Name of the stage move node.
            stage_position (List[float]): Target position of the stage [x, y, z].
        """
        super().__init__(node_type="stage_move", name=name)
        self.stage_position = stage_position

    @property
    def stage_position(self):
        """Get the stage position."""
        return self._stage_position

    @stage_position.setter
    def stage_position(self, value: List[float]):
        """
        Set the stage position.

        Parameters:
            value (List[float]): The target stage position [x, y, z].

        Raises:
            TypeError: If stage_position is not a list of three numbers.
        """
        if len(value) != 3 or not all(
            isinstance(val, (float, int)) for val in value
        ):
            raise TypeError("stage_position must be a list of three numbers.")
        self._stage_position = value

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the StageMove object into a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the object.
        """
        node_dict = super().to_dict()  # Get the basic dict from Node
        node_dict["target_position"] = self.stage_position
        return node_dict


class Wait(Node):
    """
    A class to represent a wait node with a specified wait time.

    Attributes:
        wait_time (float): The wait time in seconds.
    """

    def __init__(self, name: str = "Wait", wait_time: float = 1.0):
        """
        Initialize the wait node.

        Parameters:
            name (str): Name of the wait node.
            wait_time (float): Wait time in seconds, must be greater than 0.
        """
        super().__init__(node_type="wait", name=name)
        self.wait_time = wait_time

    @property
    def wait_time(self):
        """Get the wait time."""
        return self._wait_time

    @wait_time.setter
    def wait_time(self, value: float):
        """
        Set the wait time.

        Parameters:
            value (float): The wait time in seconds.

        Raises:
            ValueError: If the wait time is not greater than 0.
        """
        if value <= 0:
            raise ValueError("wait_time must be a positive number.")
        self._wait_time = value

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Wait object into a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the object.
        """
        node_dict = super().to_dict()  # Get the basic dict from Node
        node_dict["wait_time"] = self.wait_time
        return node_dict
