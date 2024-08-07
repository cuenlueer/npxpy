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
from npxpy.resources import Image

class CoarseAligner(Node):
    """
    Class for coarse alignment nodes.

    Attributes:
        alignment_anchors (list): List of alignment anchors.
    """
    def __init__(self, name: str = 'Coarse aligner', residual_threshold: Union[float, int] = 10.0):
        """
        Initialize the coarse aligner with a name and a residual threshold.

        Parameters:
            name (str): The name of the coarse aligner node.
            residual_threshold (Union[float, int]): The residual threshold for alignment. Must be greater than 0.

        Raises:
            ValueError: If residual_threshold is not greater than 0.
        """
        if not isinstance(name, str):
            raise TypeError("name must be a string.")
        if not isinstance(residual_threshold, (float, int)) or residual_threshold <= 0:
            raise ValueError("residual_threshold must be a positive number.")
        
        super().__init__('coarse_alignment', name, residual_threshold=residual_threshold)
        self.alignment_anchors = []

    def add_coarse_anchor(self, label: str, position: List[Union[float, int]]):
        """
        Add a single coarse anchor with a label and position.

        Parameters:
            label (str): The label for the anchor.
            position (List[Union[float, int]]): The position [x, y, z] for the anchor.

        Raises:
            ValueError: If position does not contain exactly three elements.
            TypeError: If any element in position is not a number.
        """
        if not isinstance(label, str):
            raise TypeError("label must be a string.")
        if len(position) != 3:
            raise ValueError("position must be a list of three elements.")
        if not all(isinstance(p, (float, int)) for p in position):
            raise TypeError("All position elements must be numbers.")
        
        self.alignment_anchors.append({
            "label": label,
            "position": position,
        })

    def set_coarse_anchors_at(self, labels: List[str], positions: List[List[Union[float, int]]]):
        """
        Create multiple coarse anchors at specified positions.

        Parameters:
            labels (List[str]): List of labels for the anchors.
            positions (List[List[Union[float, int]]]): List of positions for the anchors, each position is [x, y, z].

        Returns:
            self: The instance of the CoarseAligner class.

        Raises:
            ValueError: If the number of labels does not match the number of positions.
            TypeError: If any label is not a string or any position is not a list of numbers.
        """
        if len(labels) != len(positions):
            raise ValueError("The number of labels must match the number of positions.")
        for label in labels:
            if not isinstance(label, str):
                raise TypeError("All labels must be strings.")
        for position in positions:
            if len(position) != 3:
                raise ValueError("Each position must be a list of three elements.")
            if not all(isinstance(p, (float, int)) for p in position):
                raise TypeError("All position elements must be numbers.")

        for label, position in zip(labels, positions):
            self.add_coarse_anchor(label, position)
        return self

    def to_dict(self) -> Dict:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            dict: Dictionary representation of the current state of the object.
        """
        node_dict = super().to_dict()
        node_dict['alignment_anchors'] = self.alignment_anchors
        return node_dict
    
class InterfaceAligner(Node):
    """
    Interface aligner class.

    Attributes:
        alignment_anchors (list): Stores the measurement locations (or interface anchors) for interface alignment.
        count (list of int): The number of grid points in [x, y] direction.
        size (list of float): The size of the grid in [width, height].
        pattern (str): The pattern used for grid or custom alignment.
    """
    def __init__(self, name: str = 'Interface aligner',
                 signal_type: str = 'auto',
                 detector_type: str = 'auto',
                 measure_tilt: bool = False,
                 area_measurement: bool = False,
                 center_stage: bool = True,
                 action_upon_failure: str = 'abort',
                 laser_power: float = 0.5,
                 scan_area_res_factors: List[float] = [1.0, 1.0],
                 scan_z_sample_distance: float = 0.1,
                 scan_z_sample_count: int = 51):
        """
        Initializes the interface aligner with specified parameters.

        Parameters:
            name (str): Name of the interface aligner.
            signal_type (str): Type of signal, can be 'auto', 'fluorescence', or 'reflection'.
            detector_type (str): Type of detector, can be 'auto', 'confocal', 'camera', or 'camera_legacy'.
            measure_tilt (bool): Whether to measure tilt.
            area_measurement (bool): Whether to measure the area.
            center_stage (bool): Whether to center the stage.
            action_upon_failure (str): Action upon failure, can be 'abort' or 'ignore'.
            laser_power (float): Power of the laser.
            scan_area_res_factors (List[float]): Resolution factors for the scan area.
            scan_z_sample_distance (float): Distance between samples in the z-direction.
            scan_z_sample_count (int): Number of samples in the z-direction.

        Raises:
            ValueError: If scan_z_sample_count is less than 1.
        """
        if not isinstance(name, str):
            raise TypeError("name must be a string.")
        if not isinstance(signal_type, str):
            raise TypeError("signal_type must be a string.")
        if not isinstance(detector_type, str):
            raise TypeError("detector_type must be a string.")
        if not isinstance(measure_tilt, bool):
            raise TypeError("measure_tilt must be a boolean.")
        if not isinstance(area_measurement, bool):
            raise TypeError("area_measurement must be a boolean.")
        if not isinstance(center_stage, bool):
            raise TypeError("center_stage must be a boolean.")
        if not isinstance(action_upon_failure, str):
            raise TypeError("action_upon_failure must be a string.")
        if not isinstance(laser_power, (float, int)) or laser_power <= 0:
            raise ValueError("laser_power must be a positive number.")
        if not isinstance(scan_area_res_factors, list) or not all(isinstance(f, (float, int)) for f in scan_area_res_factors):
            raise TypeError("scan_area_res_factors must be a list of floats or ints.")
        if not isinstance(scan_z_sample_distance, (float, int)):
            raise TypeError("scan_z_sample_distance must be a float or an int.")
        if not isinstance(scan_z_sample_count, int) or scan_z_sample_count < 1:
            raise ValueError("scan_z_sample_count must be an integer greater than 0.")

        if signal_type not in ['auto', 'fluorescence', 'reflection']:
            raise ValueError('signal_type must be "auto", "fluorescence", or "reflection".')
        
        if detector_type not in ['auto', 'confocal', 'camera', 'camera_legacy']:
            raise ValueError('detector_type must be "auto", "confocal", "camera", or "camera_legacy".')

        super().__init__('interface_alignment', name,
                         action_upon_failure=action_upon_failure,
                         measure_tilt=measure_tilt,
                         area_measurement=area_measurement,
                         properties={'signal_type': signal_type,
                                     'detector_type': detector_type},
                         center_stage=center_stage,
                         laser_power=laser_power,
                         scan_area_res_factors=scan_area_res_factors,
                         scan_z_sample_distance=scan_z_sample_distance,
                         scan_z_sample_count=scan_z_sample_count)
        
        self.alignment_anchors = []
        self.count = [5, 5]
        self.size = [200.0, 200.0]
        self.pattern = 'Origin'
        
    def set_grid(self, count: List[int] = [5, 5], size: List[float] = [200.0, 200.0]):
        """
        Sets the grid point count and grid size.

        Parameters:
            count (List[int]): Number of grid points in [x, y] direction.
            size (List[float]): Size of the grid in [width, height].

        Returns:
            self: The instance of the InterfaceAligner class.

        Raises:
            ValueError: If count or size does not contain exactly two elements.
            TypeError: If elements in count or size are not numbers.
        """
        if len(count) != 2 or len(size) != 2:
            raise ValueError("count and size must each be lists of two elements.")
        if not all(isinstance(c, int) for c in count):
            raise TypeError("All count elements must be integers.")
        if not all(isinstance(s, (float, int)) for s in size):
            raise TypeError("All size elements must be numbers.")
        
        if self.pattern != 'Grid':
            self.pattern = 'Grid'
        
        self.count = count
        self.size = size
        return self
        
    def add_interface_anchor(self, label: str, position: List[float], scan_area_size: List[float] = None):
        """
        Adds an interface anchor with a given label, position, and scan area size.
        
        Parameters:
            label (str): The label for the anchor.
            position (List[float]): The position of the anchor [x, y].
            scan_area_size (List[float], optional): The scan area size [width, height]. 
                                                   Defaults to [10.0, 10.0].

        Raises:
            ValueError: If position does not contain exactly two elements.
            TypeError: If label is not a string or elements in position or scan_area_size are not numbers.
        """
        if not isinstance(label, str):
            raise TypeError("label must be a string.")
        if len(position) != 2:
            raise ValueError("position must be a list of two elements.")
        if not all(isinstance(p, (float, int)) for p in position):
            raise TypeError("All position elements must be numbers.")
        
        if self.pattern != 'Custom':
            self.pattern = 'Custom'
        
        if scan_area_size is None:
            scan_area_size = [10.0, 10.0]
        elif len(scan_area_size) != 2 or not all(isinstance(s, (float, int)) for s in scan_area_size):
            raise TypeError("scan_area_size must be a list of two numbers.")
        
        self.alignment_anchors.append({
            "label": label,
            "position": position,
            "scan_area_size": scan_area_size
        })
        
    def set_interface_anchors_at(self, labels: List[str], positions: List[List[float]], scan_area_sizes: List[List[float]] = None):
        """
        Creates multiple measurement locations at specified positions.
        This method only works if pattern = 'Custom'. Otherwise user input will be overridden.

        Parameters:
            labels (List[str]): List of labels for the measurement locations.
            positions (List[List[float]]): List of positions for the measurement locations, each position is [x, y].
            scan_area_sizes (List[List[float]], optional): List of scan area sizes for the measurement locations, 
                                                           each scan area size is [width, height]. Defaults to [10.0, 10.0] 
                                                           for each anchor.

        Returns:
            self: The instance of the InterfaceAligner class.

        Raises:
            ValueError: If the number of labels does not match the number of positions.
            TypeError: If elements in labels, positions, or scan_area_sizes are not of the correct types.
        """
        if len(labels) != len(positions):
            raise ValueError("The number of labels must match the number of positions.")
        
        if scan_area_sizes is None:
            scan_area_sizes = [[10.0, 10.0]] * len(labels)
        
        for label in labels:
            if not isinstance(label, str):
                raise TypeError("All labels must be strings.")
        
        for position in positions:
            if len(position) != 2:
                raise ValueError("Each position must be a list of two elements.")
            if not all(isinstance(p, (float, int)) for p in position):
                raise TypeError("All position elements must be numbers.")
        
        for scan_area_size in scan_area_sizes:
            if len(scan_area_size) != 2 or not all(isinstance(s, (float, int)) for s in scan_area_size):
                raise TypeError("Each scan_area_size must be a list of two numbers.")
        
        for label, position, scan_area_size in zip(labels, positions, scan_area_sizes):
            self.add_interface_anchor(label, position, scan_area_size)
        return self
        
    def to_dict(self) -> Dict:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            dict: Dictionary representation of the current state of the object.
        """
        node_dict = super().to_dict()
        node_dict['alignment_anchors'] = self.alignment_anchors
        node_dict['grid_point_count'] = self.count
        node_dict['grid_size'] = self.size
        node_dict['pattern'] = self.pattern
        return node_dict

class FiberAligner(Node):
    def __init__(self, name: str = 'Fiber aligner',
                 fiber_radius: Union[float, int] = 63.5,
                 center_stage: bool = True,
                 action_upon_failure: str = 'abort',
                 illumination_name: str = "process_led_1",
                 core_signal_lower_threshold: Union[float, int] = 0.05,
                 core_signal_range: List[Union[float, int]] = [0.1, 0.9],
                 detection_margin: Union[float, int] = 6.35):
        """
        Initialize the fiber aligner with specified parameters.

        Parameters:
            name (str): Name of the fiber aligner.
            fiber_radius (Union[float, int]): Radius of the fiber in micrometers. Must be greater than 0.
            center_stage (bool): Whether to center the stage.
            action_upon_failure (str): Action upon failure, can be 'abort' or 'ignore'.
            illumination_name (str): Name of the illumination source.
            core_signal_lower_threshold (Union[float, int]): Lower threshold for the core signal.
            core_signal_range (List[Union[float, int]]): Range for the core signal [min, max].
            detection_margin (Union[float, int]): Detection margin in micrometers. Must be greater than 0.

        Raises:
            ValueError: If fiber_radius or detection_margin is not greater than 0.
            ValueError: If core_signal_range does not contain exactly two elements.
        """
        if not isinstance(name, str):
            raise TypeError("name must be a string.")
        if not isinstance(fiber_radius, (float, int)) or fiber_radius <= 0:
            raise ValueError("fiber_radius must be a positive number.")
        if not isinstance(center_stage, bool):
            raise TypeError("center_stage must be a boolean.")
        if action_upon_failure not in ['abort', 'ignore']:
            raise ValueError("action_upon_failure must be 'abort' or 'ignore'.")
        if not isinstance(illumination_name, str):
            raise TypeError("illumination_name must be a string.")
        if not isinstance(core_signal_lower_threshold, (float, int)):
            raise TypeError("core_signal_lower_threshold must be a float or an int.")
        if not isinstance(core_signal_range, list) or len(core_signal_range) != 2:
            raise ValueError("core_signal_range must be a list of two elements.")
        if not all(isinstance(val, (float, int)) for val in core_signal_range):
            raise TypeError("All elements in core_signal_range must be numbers.")
        if not isinstance(detection_margin, (float, int)) or detection_margin <= 0:
            raise ValueError("detection_margin must be a positive number.")
        
        super().__init__(node_type='fiber_core_alignment', name=name,
                         fiber_radius=fiber_radius,
                         center_stage=center_stage,
                         action_upon_failure=action_upon_failure,
                         illumination_name=illumination_name,
                         core_signal_lower_threshold=core_signal_lower_threshold,
                         core_signal_range=core_signal_range,
                         core_position_offset_tolerance=detection_margin)
        
        self.detect_light_direction = False
        self.z_scan_range = [10, 100]
        self.z_scan_range_sample_count = 1
        self.z_scan_range_scan_count = 1

    def measure_tilt(self, z_scan_range: List[Union[float, int]] = [10, 100],
                     z_scan_range_sample_count: int = 3,
                     z_scan_range_scan_count: int = 1):
        """
        Measures tilt by setting scan range parameters.

        Parameters:
            z_scan_range (List[Union[float, int]]): Range for the z-scan [min, max]. The second entry must be greater than the first.
            z_scan_range_sample_count (int): Number of samples in the z-scan range. Must be greater than 0.
            z_scan_range_scan_count (int): Number of scans in the z-scan range. Must be greater than 0.

        Returns:
            self: The instance of the FiberAligner class.

        Raises:
            ValueError: If z_scan_range does not contain exactly two elements or if the second element is not greater than the first.
            ValueError: If z_scan_range_sample_count or z_scan_range_scan_count is not greater than 0.
        """
        if len(z_scan_range) != 2 or z_scan_range[1] <= z_scan_range[0] or z_scan_range[1] <= 0:
            raise ValueError("z_scan_range must be a list of two elements where the second element is greater than the first and greater than 0.")
        if not isinstance(z_scan_range_sample_count, int) or z_scan_range_sample_count <= 0:
            raise ValueError("z_scan_range_sample_count must be a positive integer.")
        if not isinstance(z_scan_range_scan_count, int) or z_scan_range_scan_count <= 0:
            raise ValueError("z_scan_range_scan_count must be a positive integer.")
        
        self.detect_light_direction = True
        self.z_scan_range = z_scan_range
        self.z_scan_range_sample_count = z_scan_range_sample_count
        self.z_scan_range_scan_count = z_scan_range_scan_count
        
        return self

    def to_dict(self) -> Dict:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            dict: Dictionary representation of the current state of the object.
        """
        node_dict = super().to_dict()
        node_dict['detect_light_direction'] = self.detect_light_direction
        node_dict['z_scan_range'] = self.z_scan_range
        node_dict['z_scan_range_sample_count'] = self.z_scan_range_sample_count
        node_dict['z_scan_range_scan_count'] = self.z_scan_range_scan_count
        return node_dict


class MarkerAligner(Node):
    """
    Marker aligner class.

    Attributes:
        image (Resources): Image object that the marker gets assigned.
        name (str): Name of the marker aligner.
        marker_size (List[float]): Size of markers in micrometers. Marker size must be greater than 0.
        center_stage (bool): Centers stage if true.
        action_upon_failure (str): 'abort' or 'ignore' at failure (not yet implemented!).
        laser_power (float): Laser power in mW.
        scan_area_size (List[float]): Scan area size in micrometers.
        scan_area_res_factors (List[float]): Resolution factors in scanned area.
        detection_margin (float): Additional margin around marker imaging field in micrometers.
        correlation_threshold (float): Correlation threshold below which abort is triggered in percent.
        residual_threshold (float): Residual threshold of marker image.
        max_outliers (int): Maximum amount of markers that are allowed to be outliers.
        orthonormalize (bool): Whether to orthonormalize or not.
        z_scan_sample_count (int): Number of z samples to be taken.
        z_scan_sample_distance (float): Sampling distance in micrometers for z samples to be apart from each other.
        z_scan_sample_mode (str): "correlation" or "intensity" for scan_z_sample_mode.
        measure_z (bool): Whether to measure z or not.
    """

    def __init__(self, image: Image, 
                 name: str = 'Marker aligner',
                 marker_size: List[float] = [0.0, 0.0],
                 center_stage: bool = True,
                 action_upon_failure: str = 'abort',
                 laser_power: float = 0.5,
                 scan_area_size: List[float] = [10.0, 10.0],
                 scan_area_res_factors: List[float] = [2.0, 2.0],
                 detection_margin: float = 5.0,
                 correlation_threshold: float = 60.0,
                 residual_threshold: float = 0.5,
                 max_outliers: int = 0,
                 orthonormalize: bool = True,
                 z_scan_sample_count: int = 1,
                 z_scan_sample_distance: float = 0.5,
                 z_scan_sample_mode: str = 'correlation',
                 measure_z: bool = False):
        """
        Initializes the MarkerAligner with the provided parameters.

        Parameters:
            image (Image): Image object that the marker gets assigned.
            name (str): Name of the marker aligner.
            marker_size (List[float]): Size of markers in micrometers. Marker size must be greater than 0.
            center_stage (bool): Centers stage if true.
            action_upon_failure (str): 'abort' or 'ignore' at failure (not yet implemented!).
            laser_power (float): Laser power in mW.
            scan_area_size (List[float]): Scan area size in micrometers.
            scan_area_res_factors (List[float]): Resolution factors in scanned area.
            detection_margin (float): Additional margin around marker imaging field in micrometers.
            correlation_threshold (float): Correlation threshold below which abort is triggered in percent.
            residual_threshold (float): Residual threshold of marker image.
            max_outliers (int): Maximum amount of markers that are allowed to be outliers.
            orthonormalize (bool): Whether to orthonormalize or not.
            z_scan_sample_count (int): Number of z samples to be taken.
            z_scan_sample_distance (float): Sampling distance in micrometers for z samples to be apart from each other.
            z_scan_sample_mode (str): "correlation" or "intensity" for scan_z_sample_mode.
            measure_z (bool): Whether to measure z or not.

        Raises:
            ValueError: If marker_size is not greater than 0, if z_scan_sample_count is less than 1,
                        or if z_scan_sample_mode is not "correlation" or "intensity".
        """
        if not isinstance(image, Image):
            raise TypeError("image must be an instance of Image class.")
        if not isinstance(name, str):
            raise TypeError("name must be a string.")
        if not isinstance(marker_size, list) or len(marker_size) != 2 or not all(isinstance(val, (float, int)) for val in marker_size):
            raise TypeError("marker_size must be a list of two positive numbers.")
        if marker_size[0] <= 0 or marker_size[1] <= 0:
            raise ValueError("marker_size must be greater than 0.")
        if not isinstance(center_stage, bool):
            raise TypeError("center_stage must be a boolean.")
        if action_upon_failure not in ['abort', 'ignore']:
            raise ValueError("action_upon_failure must be 'abort' or 'ignore'.")
        if not isinstance(laser_power, (float, int)) or laser_power < 0:
            raise ValueError("laser_power must be a non-negative number.")
        if not isinstance(scan_area_size, list) or len(scan_area_size) != 2 or not all(isinstance(val, (float, int)) for val in scan_area_size):
            raise TypeError("scan_area_size must be a list of two positive numbers.")
        if not isinstance(scan_area_res_factors, list) or len(scan_area_res_factors) != 2 or not all(isinstance(val, (float, int)) for val in scan_area_res_factors):
            raise TypeError("scan_area_res_factors must be a list of two positive numbers.")
        if not isinstance(detection_margin, (float, int)) or detection_margin < 0:
            raise ValueError("detection_margin must be a non-negative number.")
        if not isinstance(correlation_threshold, (float, int)) or not (0 <= correlation_threshold <= 100):
            raise ValueError("correlation_threshold must be between 0 and 100.")
        if not isinstance(residual_threshold, (float, int)) or residual_threshold < 0:
            raise ValueError("residual_threshold must be a non-negative number.")
        if not isinstance(max_outliers, int) or max_outliers < 0:
            raise ValueError("max_outliers must be a non-negative integer.")
        if not isinstance(orthonormalize, bool):
            raise TypeError("orthonormalize must be a boolean.")
        if not isinstance(z_scan_sample_count, int) or z_scan_sample_count < 1:
            raise ValueError("z_scan_sample_count must be at least 1.")
        if not isinstance(z_scan_sample_distance, (float, int)) or z_scan_sample_distance <= 0:
            raise ValueError("z_scan_sample_distance must be a positive number.")
        if z_scan_sample_mode not in ['correlation', 'intensity']:
            raise ValueError('z_scan_sample_mode must be either "correlation" or "intensity".')
        if not isinstance(measure_z, bool):
            raise TypeError("measure_z must be a boolean.")

        super().__init__('marker_alignment', name,
                         action_upon_failure=action_upon_failure,
                         marker={'image': image.id,
                                 'size': marker_size},
                         center_stage=center_stage,
                         laser_power=laser_power,
                         scan_area_size=scan_area_size,
                         scan_area_res_factors=scan_area_res_factors,
                         detection_margin=detection_margin,
                         correlation_threshold=correlation_threshold,
                         residual_threshold=residual_threshold,
                         max_outliers=max_outliers,
                         orthonormalize=orthonormalize,
                         z_scan_sample_distance=z_scan_sample_distance,
                         z_scan_sample_count=z_scan_sample_count,
                         z_scan_optimization_mode=z_scan_sample_mode,
                         measure_z=measure_z)
        
        self.alignment_anchors = []

    def add_marker(self, label: str, orientation: float, position: List[float]):
        """
        Adds a marker to the alignment anchors.

        Parameters:
            label (str): The label of the marker.
            orientation (float): The orientation of the marker in degrees.
            position (List[float]): The position of the marker in micrometers.

        Raises:
            ValueError: If position does not contain exactly two elements.
            TypeError: If label is not a string, orientation is not a number, or elements in position are not numbers.
        """
        if not isinstance(label, str):
            raise TypeError("label must be a string.")
        if not isinstance(orientation, (float, int)):
            raise TypeError("orientation must be a float or an int.")
        if not isinstance(position, list) or len(position) != 2 or not all(isinstance(val, (float, int)) for val in position):
            raise TypeError("position must be a list of two numbers.")
        
        self.alignment_anchors.append({
            "label": label,
            "position": position,
            "rotation": orientation
        })
        
    def set_markers_at(self, labels: List[str], orientations: List[float], positions: List[List[float]]):
        """
        Creates multiple markers at specified positions with given orientations.

        Parameters:
            labels (List[str]): List of labels for the markers.
            orientations (List[float]): List of orientations for the markers in degrees.
            positions (List[List[float]]): List of positions for the markers in micrometers.

        Returns:
            MarkerAligner: The current instance with added markers.

        Raises:
            ValueError: If the lengths of labels, orientations, and positions do not match.
            TypeError: If elements in labels, orientations, or positions are not of the correct types.
        """
        if len(labels) != len(positions) or len(labels) != len(orientations):
            raise ValueError("The number of labels, positions, and orientations must match.")
        
        for label in labels:
            if not isinstance(label, str):
                raise TypeError("All labels must be strings.")
        
        for orientation in orientations:
            if not isinstance(orientation, (float, int)):
                raise TypeError("All orientations must be float or int.")
        
        for position in positions:
            if not isinstance(position, list) or len(position) != 2 or not all(isinstance(val, (float, int)) for val in position):
                raise TypeError("All positions must be lists of two numbers.")
        
        for label, orientation, position in zip(labels, orientations, positions):
            self.add_marker(label, orientation, position)
        return self
    
    def to_dict(self) -> Dict:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            dict: Dictionary representation of the current state of the object.
        """
        node_dict = super().to_dict()
        node_dict['alignment_anchors'] = self.alignment_anchors
        return node_dict

class EdgeAligner(Node):
    """
    A class to represent an edge aligner with various attributes and methods for managing edge alignment.

    Attributes:
        alignment_anchors (List[Dict[str, Any]]): List of alignment anchors.
    """
    def __init__(self, 
                 node_type: str = 'edge_alignment',
                 name: str = 'Edge aligner',
                 edge_location: List[float] = [0.0, 0.0],
                 edge_orientation: float = 0.0,
                 center_stage: bool = True,
                 action_upon_failure: str = 'abort',
                 laser_power: Union[float, int] = 0.5,
                 scan_area_res_factors: List[float] = [1.0, 1.0],
                 scan_z_sample_distance: Union[float, int] = 0.1,
                 scan_z_sample_count: int = 51,
                 outlier_threshold: float = 10.0):
        """
        Initialize the edge aligner with the specified parameters.

        Parameters:
            node_type (str): Type of the node.
            name (str): Name of the edge aligner.
            edge_location (List[float]): Location of the edge [x, y] in micrometers.
            edge_orientation (float): Orientation of the edge in degrees.
            center_stage (bool): Whether to center the stage.
            action_upon_failure (str): Action upon failure, can be 'abort' or 'ignore'.
            laser_power (Union[float, int]): Power of the laser, must be >= 0.
            scan_area_res_factors (List[float]): Resolution factors for the scan area, must be greater than zero.
            scan_z_sample_distance (Union[float, int]): Distance between samples in the z-direction.
            scan_z_sample_count (int): Number of samples in the z-direction, must be greater than zero.
            outlier_threshold (float): Outlier threshold in percent (0 <= 100).

        Raises:
            ValueError: If any parameter is out of expected range.
        """
        if not isinstance(name, str):
            raise TypeError("name must be a string.")
        if not isinstance(edge_location, list) or len(edge_location) != 2 or not all(isinstance(val, (float, int)) for val in edge_location):
            raise TypeError("edge_location must be a list of two numbers.")
        if not isinstance(edge_orientation, (float, int)):
            raise TypeError("edge_orientation must be a float or an int.")
        if not isinstance(center_stage, bool):
            raise TypeError("center_stage must be a boolean.")
        if action_upon_failure not in ['abort', 'ignore']:
            raise ValueError("action_upon_failure must be 'abort' or 'ignore'.")
        if not isinstance(laser_power, (float, int)) or laser_power < 0:
            raise ValueError("laser_power must be a non-negative number.")
        if not isinstance(scan_area_res_factors, list) or len(scan_area_res_factors) != 2 or not all(isinstance(factor, (float, int)) for factor in scan_area_res_factors):
            raise TypeError("scan_area_res_factors must be a list of two numbers greater than zero.")
        if not all(factor > 0 for factor in scan_area_res_factors):
            raise ValueError("All elements in scan_area_res_factors must be greater than 0.")
        if not isinstance(scan_z_sample_distance, (float, int)) or scan_z_sample_distance <= 0:
            raise ValueError("scan_z_sample_distance must be a positive number.")
        if not isinstance(scan_z_sample_count, int) or scan_z_sample_count < 1:
            raise ValueError("scan_z_sample_count must be an integer greater than zero.")
        if not isinstance(outlier_threshold, (float, int)) or not (0 <= outlier_threshold <= 100):
            raise ValueError("outlier_threshold must be a number between 0 and 100.")
        
        super().__init__(node_type=node_type,
                         name=name,
                         properties={'xy_position_local_cos': edge_location,
                                     'z_rotation_local_cos': edge_orientation,
                                     'center_stage': center_stage,
                                     'action_upon_failure': action_upon_failure,
                                     'laser_power': laser_power,
                                     'scan_area_res_factors': scan_area_res_factors,
                                     'scan_z_sample_distance': scan_z_sample_distance,
                                     'scan_z_sample_count': scan_z_sample_count,
                                     'outlier_threshold': outlier_threshold})
        
        self.alignment_anchors = []

    def add_measurement(self, label: str, offset: Union[float, int], scan_area_size: List[Union[float, int]]):
        """
        Add a measurement with a label, offset, and scan area size.

        Parameters:
            label (str): The label for the measurement.
            offset (Union[float, int]): The offset for the measurement.
            scan_area_size (List[Union[float, int]]): The scan area size [width, height].

        Raises:
            ValueError: If scan_area_size does not contain exactly two elements or if width <= 0 or height < 0.
            TypeError: If label is not a string or elements in scan_area_size are not numbers.
        """
        if not isinstance(label, str):
            raise TypeError("label must be a string.")
        if not isinstance(offset, (float, int)):
            raise TypeError("offset must be a float or an int.")
        if not isinstance(scan_area_size, list) or len(scan_area_size) != 2 or not all(isinstance(val, (float, int)) for val in scan_area_size):
            raise TypeError("scan_area_size must be a list of two numbers.")
        if scan_area_size[0] <= 0:
            raise ValueError("The width (X) in scan_area_size must be greater than 0.")
        if scan_area_size[1] < 0:
            raise ValueError("The height (Y) in scan_area_size must be greater than or equal to 0.")
        
        self.alignment_anchors.append({
            "label": label,
            "offset": offset,
            "scan_area_size": scan_area_size
        })
    
    def set_measurements_at(self, labels: List[str], offsets: List[Union[float, int]], scan_area_sizes: List[List[Union[float, int]]]):
        """
        Set multiple measurements at specified positions.

        Parameters:
            labels (List[str]): List of labels for the measurements.
            offsets (List[Union[float, int]]): List of offsets for the measurements.
            scan_area_sizes (List[List[Union[float, int]]]): List of scan area sizes for the measurements.

        Returns:
            EdgeAligner: The instance of the EdgeAligner class.

        Raises:
            ValueError: If the lengths of labels, offsets, and scan_area_sizes do not match.
            TypeError: If elements in labels, offsets, or scan_area_sizes are not of the correct types.
        """
        if len(labels) != len(scan_area_sizes) or len(labels) != len(offsets):
            raise ValueError("The number of labels, offsets, and scan_area_sizes must match.")
        
        for label in labels:
            if not isinstance(label, str):
                raise TypeError("All labels must be strings.")
        
        for offset in offsets:
            if not isinstance(offset, (float, int)):
                raise TypeError("All offsets must be float or int.")
        
        for scan_area_size in scan_area_sizes:
            if not isinstance(scan_area_size, list) or len(scan_area_size) != 2 or not all(isinstance(val, (float, int)) for val in scan_area_size):
                raise TypeError("All scan_area_sizes must be lists of two numbers.")
            if scan_area_size[0] <= 0:
                raise ValueError("The width (X) in scan_area_size must be greater than 0.")
            if scan_area_size[1] < 0:
                raise ValueError("The height (Y) in scan_area_size must be greater than or equal to 0.")
        
        for label, offset, scan_area_size in zip(labels, offsets, scan_area_sizes):
            self.add_measurement(label, offset, scan_area_size)
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary representation of the current state of the object.
        """
        node_dict = super().to_dict()
        node_dict['alignment_anchors'] = self.alignment_anchors
        return node_dict