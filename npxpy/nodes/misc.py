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
from typing import Dict, Any, List, Union
from npxpy.nodes.node import Node

class DoseCompensation(Node):
    """
    A class to represent dose compensation with various attributes and methods for managing dose settings.

    Attributes:
        alignment_anchors (List[Dict[str, Any]]): List of alignment anchors.
    """
    def __init__(self, 
                 name: str = 'Dose compensation 1',
                 edge_location: List[Union[float, int]] = [0.0, 0.0, 0.0],
                 edge_orientation: Union[float, int] = 0.0,
                 domain_size: List[Union[float, int]] = [200.0, 100.0, 100.0],
                 gain_limit: Union[float, int] = 2.0):
        """
        Initialize the dose compensation with the specified parameters.

        Parameters:
            name (str): Name of the dose compensation.
            edge_location (List[Union[float, int]]): Location of the edge [x, y, z] in micrometers.
            edge_orientation (Union[float, int]): Orientation of the edge in degrees.
            domain_size (List[Union[float, int]]): Size of the domain [width, height, depth] in micrometers, must be > 0.
            gain_limit (Union[float, int]): Gain limit, must be >= 1.

        Raises:
            ValueError: If domain_size contains non-positive values or if gain_limit is less than 1.
            TypeError: If any parameter is not of the correct type.
        """
        if not isinstance(name, str):
            raise TypeError("name must be a string.")
        if not isinstance(edge_location, list) or len(edge_location) != 3 or not all(isinstance(val, (float, int)) for val in edge_location):
            raise TypeError("edge_location must be a list of three numbers.")
        if not isinstance(edge_orientation, (float, int)):
            raise TypeError("edge_orientation must be a float or an int.")
        if not isinstance(domain_size, list) or len(domain_size) != 3 or not all(isinstance(val, (float, int)) for val in domain_size):
            raise TypeError("domain_size must be a list of three numbers.")
        if any(size <= 0 for size in domain_size):
            raise ValueError("All elements in domain_size must be greater than 0.")
        if not isinstance(gain_limit, (float, int)) or gain_limit < 1:
            raise ValueError("gain_limit must be greater than or equal to 1.")

        super().__init__(node_type='dose_compensation',
                         name=name,
                         position_local_cos=edge_location,
                         z_rotation_local_cos=edge_orientation,
                         size=domain_size,
                         gain_limit=gain_limit)
        
class Capture(Node):
    """
    A class to represent a capture node with attributes and methods for managing capture settings.

    Attributes:
        capture_type (str): The type of capture (e.g., 'Camera', 'Confocal').
        laser_power (float): The laser power for the capture.
        scan_area_size (List[float]): The size of the scan area [width, height].
        scan_area_ref_factors (List[float]): The resolution factors for the scan area.
    """
    def __init__(self, name: str = 'Capture'):
        """
        Initialize the capture node with the specified parameters.

        Parameters:
            name (str): Name of the capture node.
        """
        if not isinstance(name, str):
            raise TypeError("name must be a string.")
        
        super().__init__(node_type='capture', name=name)
        self.capture_type = 'Camera'
        self.laser_power = 0.5
        self.scan_area_size = [100.0, 100.0]
        self.scan_area_ref_factors = [1.0, 1.0]

    def confocal(self, laser_power: float = 0.5,
                 scan_area_size: List[float] = [100.0, 100.0],
                 scan_area_ref_factors: List[float] = [1.0, 1.0]) -> 'Capture':
        """
        Configure the capture node for confocal capture.

        Parameters:
            laser_power (float): The laser power, must be greater or equal to 0.
            scan_area_size (List[float]): The scan area size [width, height], must be greater or equal to 0.
            scan_area_ref_factors (List[float]): The resolution factors for the scan area, must be greater than 0.

        Returns:
            Capture: The instance of the Capture class.

        Raises:
            ValueError: If any parameter value is not valid.
        """
        if not isinstance(laser_power, (float, int)) or laser_power < 0:
            raise ValueError("laser_power must be greater or equal to 0.")
        if not isinstance(scan_area_size, list) or len(scan_area_size) != 2 or not all(isinstance(size, (float, int)) for size in scan_area_size):
            raise TypeError("scan_area_size must be a list of two numbers greater or equal to 0.")
        if any(size < 0 for size in scan_area_size):
            raise ValueError("All elements in scan_area_size must be greater or equal to 0.")
        if not isinstance(scan_area_ref_factors, list) or len(scan_area_ref_factors) != 2 or not all(isinstance(factor, (float, int)) for factor in scan_area_ref_factors):
            raise TypeError("scan_area_ref_factors must be a list of two numbers greater than 0.")
        if any(factor <= 0 for factor in scan_area_ref_factors):
            raise ValueError("All elements in scan_area_ref_factors must be greater than 0.")
        
        self.laser_power = laser_power
        self.scan_area_size = scan_area_size
        self.scan_area_ref_factors = scan_area_ref_factors
        self.capture_type = 'Confocal'
        
        return self

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary representation of the current state of the object.
        """
        node_dict = super().to_dict()
        node_dict['capture_type'] = self.capture_type
        node_dict['laser_power'] = self.laser_power
        node_dict['scan_area_size'] = self.scan_area_size
        node_dict['scan_area_ref_factors'] = self.scan_area_ref_factors
        return node_dict

class StageMove(Node):
    """
    A class to represent a stage move node with a specified stage position.

    Attributes:
        target_position (List[float]): The target position of the stage [x, y, z].
    """
    def __init__(self, 
                 name: str = 'Stage move', 
                 stage_position: List[float] = [0.0, 0.0, 0.0]):
        """
        Initialize the stage move node with the specified parameters.

        Parameters:
            name (str): Name of the stage move node.
            stage_position (List[float]): Target position of the stage [x, y, z].

        Raises:
            ValueError: If stage_position does not contain exactly three elements.
            TypeError: If stage_position elements are not numbers.
        """
        if not isinstance(name, str):
            raise TypeError("name must be a string.")
        if not isinstance(stage_position, list) or len(stage_position) != 3 or not all(isinstance(val, (float, int)) for val in stage_position):
            raise TypeError("stage_position must be a list of three numbers.")
        
        super().__init__(node_type='stage_move',
                         name=name,
                         target_position=stage_position)

class Wait(Node):
    """
    A class to represent a wait node with a specified wait time.

    Attributes:
        wait_time (float): The wait time in seconds.
    """
    def __init__(self, 
                 name: str = 'Wait', 
                 wait_time: float = 1.0):
        """
        Initialize the wait node with the specified parameters.

        Parameters:
            name (str): Name of the wait node.
            wait_time (float): Wait time in seconds, must be greater than 0.

        Raises:
            ValueError: If wait_time is not greater than 0.
            TypeError: If wait_time is not a number.
        """
        if not isinstance(name, str):
            raise TypeError("name must be a string.")
        if not isinstance(wait_time, (float, int)) or wait_time <= 0:
            raise ValueError("wait_time must be a positive number.")
        
        super().__init__(node_type='wait', 
                         name=name,
                         wait_time=wait_time)