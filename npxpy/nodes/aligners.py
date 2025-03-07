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
from npxpy.resources import Image


class CoarseAligner(Node):
    """
    Class for coarse alignment nodes.

    Attributes:
        residual_threshold (Union[float, int]): The residual threshold for alignment.
        alignment_anchors (List[Dict]): List of alignment anchors with label and position.
    """

    def __init__(
        self,
        name: str = "Coarse aligner",
        residual_threshold: Union[float, int] = 10.0,
    ):
        """
        Initialize the coarse aligner with a name and a residual threshold.

        Parameters:
            name (str): The name of the coarse aligner node.
            residual_threshold (Union[float, int]): The residual threshold for alignment. Must be greater than 0.

        Raises:
            ValueError: If residual_threshold is not greater than 0.
        """
        super().__init__("coarse_alignment", name)

        self._alignment_anchors = []
        self.residual_threshold = (
            residual_threshold  # Using setter for validation
        )

    @property
    def residual_threshold(self):
        """Get the residual threshold."""
        return self._residual_threshold

    @residual_threshold.setter
    def residual_threshold(self, value: Union[float, int]):
        """
        Set the residual threshold for alignment.

        Parameters:
            value (Union[float, int]): Residual threshold, must be greater than 0.

        Raises:
            ValueError: If residual_threshold is not greater than 0.
        """
        if not isinstance(value, (float, int)) or value <= 0:
            raise ValueError("residual_threshold must be a positive number.")
        self._residual_threshold = value

    @property
    def alignment_anchors(self):
        """Get the list of alignment anchors."""
        return self._alignment_anchors

    def add_coarse_anchor(self, position: List[Union[float, int]], label: str):
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

        self._alignment_anchors.append(
            {
                "label": label,
                "position": position,
            }
        )
        return self

    def set_coarse_anchors_at(
        self,
        positions: List[List[Union[float, int]]],
        labels: List[str] = None,
    ):
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
        if labels is None:
            labels = [f"anchor_{i}" for i in range(len(positions))]
        if len(labels) != len(positions):
            raise ValueError(
                "The number of labels must match the number of positions."
            )

        for label in labels:
            if not isinstance(label, str):
                raise TypeError("All labels must be strings.")

        for position in positions:
            if len(position) != 3:
                raise ValueError(
                    "Each position must be a list of three elements."
                )
            if not all(isinstance(p, (float, int)) for p in position):
                raise TypeError("All position elements must be numbers.")

        for label, position in zip(labels, positions):
            self.add_coarse_anchor(position, label)

        return self

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the CoarseAligner object into a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the object.
        """
        node_dict = super().to_dict()  # Get basic attributes from Node
        node_dict.update(
            {
                "alignment_anchors": self.alignment_anchors,
                "residual_threshold": self.residual_threshold,
            }
        )
        return node_dict


class InterfaceAligner(Node):
    """
    A class representing an interface aligner node, responsible for managing
    alignment settings and grid patterns for various operations.

    Attributes:
        alignment_anchors (List[Dict]): Stores the measurement locations (or interface anchors) for interface alignment.
        count (List[int]): The number of grid points in [x, y] direction.
        size (List[float]): The size of the grid in [width, height].
        pattern (str): The pattern used for grid or custom alignment.
    """

    def __init__(
        self,
        name: str = "Interface aligner",
        signal_type: str = "auto",
        detector_type: str = "auto",
        measure_tilt: bool = False,
        area_measurement: bool = False,
        center_stage: bool = True,
        action_upon_failure: str = "abort",
        laser_power: float = 0.5,
        scan_area_res_factors: List[float] = [1.0, 1.0],
        scan_z_sample_distance: float = 0.1,
        scan_z_sample_count: int = 51,
    ):
        """
        Initializes an InterfaceAligner node with specified settings.

        Parameters:
            name (str): Name of the interface aligner. Defaults to "Interface aligner".
            signal_type (str): The type of signal. Can be 'auto', 'fluorescence', or 'reflection'. Defaults to 'auto'.
            detector_type (str): The type of detector. Can be 'auto', 'confocal', 'camera', or 'camera_legacy'. Defaults to 'auto'.
            measure_tilt (bool): Whether to measure tilt. Defaults to False.
            area_measurement (bool): Whether to measure the area. Defaults to False.
            center_stage (bool): Whether to center the stage. Defaults to True.
            action_upon_failure (str): Action upon failure, can be 'abort' or 'ignore'. Defaults to 'abort'.
            laser_power (float): The power of the laser. Must be a positive number. Defaults to 0.5.
            scan_area_res_factors (List[float]): Resolution factors for the scan area. Defaults to [1.0, 1.0].
            scan_z_sample_distance (float): Distance between samples in the z-direction. Defaults to 0.1.
            scan_z_sample_count (int): Number of samples in the z-direction. Must be greater than 0. Defaults to 51.

        Raises:
            ValueError: If any input is not valid (e.g., invalid types or constraints like negative values).
        """
        super().__init__("interface_alignment", name)

        # Use setters for validation
        self.signal_type = signal_type
        self.detector_type = detector_type
        self.measure_tilt = measure_tilt
        self.area_measurement = area_measurement
        self.center_stage = center_stage
        self.action_upon_failure = action_upon_failure
        self.laser_power = laser_power
        self.scan_area_res_factors = scan_area_res_factors
        self.scan_z_sample_distance = scan_z_sample_distance
        self.scan_z_sample_count = scan_z_sample_count

        self.alignment_anchors = []
        self.count = [5, 5]
        self.size = [200.0, 200.0]
        self.pattern = "Origin"

    # Setters with validation for various attributes

    @property
    def signal_type(self):
        return self._signal_type

    @signal_type.setter
    def signal_type(self, value: str):
        valid_types = ["auto", "fluorescence", "reflection"]
        if value not in valid_types:
            raise ValueError(f"signal_type must be one of {valid_types}.")
        self._signal_type = value

    @property
    def detector_type(self):
        return self._detector_type

    @detector_type.setter
    def detector_type(self, value: str):
        valid_detectors = ["auto", "confocal", "camera", "camera_legacy"]
        if value not in valid_detectors:
            raise ValueError(
                f"detector_type must be one of {valid_detectors}."
            )
        self._detector_type = value

    @property
    def measure_tilt(self):
        return self._measure_tilt

    @measure_tilt.setter
    def measure_tilt(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("measure_tilt must be a boolean.")
        self._measure_tilt = value

    @property
    def area_measurement(self):
        return self._area_measurement

    @area_measurement.setter
    def area_measurement(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("area_measurement must be a boolean.")
        self._area_measurement = value

    @property
    def center_stage(self):
        return self._center_stage

    @center_stage.setter
    def center_stage(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("center_stage must be a boolean.")
        self._center_stage = value

    @property
    def action_upon_failure(self):
        return self._action_upon_failure

    @action_upon_failure.setter
    def action_upon_failure(self, value: str):
        valid_actions = ["abort", "ignore"]
        if value not in valid_actions:
            raise ValueError(
                f"action_upon_failure must be one of {valid_actions}."
            )
        self._action_upon_failure = value

    @property
    def laser_power(self):
        return self._laser_power

    @laser_power.setter
    def laser_power(self, value: float):
        if not isinstance(value, (float, int)) or value <= 0:
            raise ValueError("laser_power must be a positive number.")
        self._laser_power = value

    @property
    def scan_area_res_factors(self):
        return self._scan_area_res_factors

    @scan_area_res_factors.setter
    def scan_area_res_factors(self, value: List[float]):
        if len(value) != 2 or not all(
            isinstance(f, (float, int)) for f in value
        ):
            raise TypeError(
                "scan_area_res_factors must be a list of two floats or ints."
            )
        self._scan_area_res_factors = value

    @property
    def scan_z_sample_distance(self):
        return self._scan_z_sample_distance

    @scan_z_sample_distance.setter
    def scan_z_sample_distance(self, value: float):
        if not isinstance(value, (float, int)):
            raise TypeError(
                "scan_z_sample_distance must be a float or an int."
            )
        self._scan_z_sample_distance = value

    @property
    def scan_z_sample_count(self):
        return self._scan_z_sample_count

    @scan_z_sample_count.setter
    def scan_z_sample_count(self, value: int):
        if not isinstance(value, int) or value < 1:
            raise ValueError(
                "scan_z_sample_count must be an integer greater than 0."
            )
        self._scan_z_sample_count = value

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, value: List[int]):
        if len(value) != 2 or not all(isinstance(c, int) for c in value):
            raise ValueError("count must be a list of two integers.")
        self._count = value

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value: List[float]):
        if len(value) != 2 or not all(
            isinstance(s, (float, int)) for s in value
        ):
            raise ValueError("size must be a list of two numbers.")
        self._size = value

    @property
    def pattern(self):
        return self._pattern

    @pattern.setter
    def pattern(self, value: str):
        if value not in ["Grid", "Custom", "Origin"]:
            raise ValueError("pattern must be 'Grid', 'Custom', or 'Origin'.")
        self._pattern = value

    def set_grid(self, count: List[int], size: List[float]):
        """
        Sets the grid point count and grid size for alignment operations.

        Parameters:
            count (List[int]): Number of grid points in [x, y] direction. Must contain exactly two integers.
            size (List[float]): Size of the grid in [width, height]. Must contain exactly two numbers.

        Returns:
            self: The instance of the InterfaceAligner class.

        Raises:
            ValueError: If count or size does not contain exactly two elements.
            TypeError: If elements in count or size are not numbers.
        """
        self.count = count
        self.size = size
        self.pattern = "Grid"
        return self

    def add_interface_anchor(
        self,
        position: List[float],
        label: str,
        scan_area_size: List[float] = None,
    ):
        """
        Adds a custom interface anchor with a label, position, and optional scan area size.

        Parameters:
            label (str): The label for the anchor. Must be a string.
            position (List[float]): The position of the anchor [x, y]. Must contain exactly two numbers.
            scan_area_size (List[float], optional): The scan area size [width, height]. Defaults to [10.0, 10.0].

        Raises:
            ValueError: If position does not contain exactly two elements.
            TypeError: If label is not a string or elements in position or scan_area_size are not numbers.
        """
        if not isinstance(position, list) or len(position) != 2:
            try:
                position = list(position)
                position = position[:2]
                assert len(position) == 2
            except:
                raise ValueError("position must be a list of two elements.")
        if not all(isinstance(p, (float, int)) for p in position):
            try:
                position = [float(p) for p in position]
            except:
                raise TypeError("All position elements must be numbers.")
        if scan_area_size is None:
            scan_area_size = [10.0, 10.0]

        self.pattern = "Custom"
        self.alignment_anchors.append(
            {
                "label": label,
                "position": position,
                "scan_area_size": scan_area_size,
            }
        )
        return self

    def set_interface_anchors_at(
        self,
        positions: List[List[float]],
        labels: List[str] = None,
        scan_area_sizes: List[List[float]] = None,
    ):
        """
        Creates multiple custom interface anchors at specified positions.

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
        if scan_area_sizes is None:
            scan_area_sizes = [[10.0, 10.0]] * len(positions)
        if labels is None:
            labels = [f"anchor_{i}" for i in range(len(positions))]
        for label, position, scan_area_size in zip(
            labels, positions, scan_area_sizes
        ):
            self.add_interface_anchor(position, label, scan_area_size)

        return self

    def to_dict(self) -> Dict:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            dict: Dictionary representation of the current state of the object, including
                  alignment anchors, grid settings, and signal properties.
        """
        node_dict = super().to_dict()
        if self.signal_type == "auto" or self.detector_type == "camera_legacy":
            node_dict["interface_finder_type"] = self.signal_type
        else:
            node_dict["interface_finder_type"] = (
                f"{self.signal_type}_{self.detector_type}"
            )
        node_dict["properties"] = {
            "signal_type": self.signal_type,
            "detector_type": self.detector_type,
        }
        node_dict["alignment_anchors"] = self.alignment_anchors
        node_dict["grid_point_count"] = self.count
        node_dict["grid_size"] = self.size
        node_dict["pattern"] = self.pattern
        node_dict["measure_tilt"] = self.measure_tilt
        node_dict["area_measurement"] = self.area_measurement
        node_dict["center_stage"] = self.center_stage
        node_dict["action_upon_failure"] = self.action_upon_failure
        node_dict["laser_power"] = self.laser_power
        node_dict["scan_area_res_factors"] = self.scan_area_res_factors
        node_dict["scan_z_sample_distance"] = self.scan_z_sample_distance
        node_dict["scan_z_sample_count"] = self.scan_z_sample_count
        return node_dict


class FiberAligner(Node):
    def __init__(
        self,
        name: str = "Fiber aligner",
        fiber_radius: Union[float, int] = 63.5,
        center_stage: bool = True,
        action_upon_failure: str = "abort",
        illumination_name: str = "process_led_1",
        core_signal_lower_threshold: Union[float, int] = 0.05,
        core_signal_range: List[Union[float, int]] = [0.1, 0.9],
        detection_margin: Union[float, int] = 6.35,
    ):
        """
        Initialize the fiber aligner with specified parameters.

        Parameters:
            name (str): Name of the fiber aligner.
            fiber_radius (Union[float, int]): Radius of the fiber.
            center_stage (bool): Whether to center the stage.
            action_upon_failure (str): Action upon failure ('abort' or 'ignore').
            illumination_name (str): Name of the illumination source.
            core_signal_lower_threshold (Union[float, int]): Lower threshold for
                the core signal.
            core_signal_range (List[Union[float, int]]): Range for the core
                signal [min, max].
            detection_margin (Union[float, int]): Detection margin.
        """
        super().__init__(
            node_type="fiber_core_alignment",
            name=name,
        )

        # Use setters to handle attributes
        self.fiber_radius = fiber_radius
        self.center_stage = center_stage
        self.action_upon_failure = action_upon_failure
        self.illumination_name = illumination_name
        self.core_signal_lower_threshold = core_signal_lower_threshold
        self.core_signal_range = core_signal_range
        self.detection_margin = detection_margin

        # Default values using setters for consistency
        self.detect_light_direction = False
        self.z_scan_range = [10, 100]
        self.z_scan_range_sample_count = 1
        self.z_scan_range_scan_count = 1

    # Proper setters with validation
    @property
    def fiber_radius(self) -> Union[float, int]:
        return self._fiber_radius

    @fiber_radius.setter
    def fiber_radius(self, value: Union[float, int]):
        if not isinstance(value, (float, int)) or value <= 0:
            raise ValueError("fiber_radius must be a positive number.")
        self._fiber_radius = value

    @property
    def center_stage(self) -> bool:
        return self._center_stage

    @center_stage.setter
    def center_stage(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("center_stage must be a boolean.")
        self._center_stage = value

    @property
    def action_upon_failure(self) -> str:
        return self._action_upon_failure

    @action_upon_failure.setter
    def action_upon_failure(self, value: str):
        if value not in ["abort", "ignore"]:
            raise ValueError(
                "action_upon_failure must be 'abort' or 'ignore'."
            )
        self._action_upon_failure = value

    @property
    def illumination_name(self) -> str:
        return self._illumination_name

    @illumination_name.setter
    def illumination_name(self, value: str):
        if not isinstance(value, str):
            raise TypeError("illumination_name must be a string.")
        self._illumination_name = value

    @property
    def core_signal_lower_threshold(self) -> Union[float, int]:
        return self._core_signal_lower_threshold

    @core_signal_lower_threshold.setter
    def core_signal_lower_threshold(self, value: Union[float, int]):
        if not isinstance(value, (float, int)):
            raise TypeError(
                "core_signal_lower_threshold must be a float or an int."
            )
        self._core_signal_lower_threshold = value

    @property
    def core_signal_range(self) -> List[Union[float, int]]:
        return self._core_signal_range

    @core_signal_range.setter
    def core_signal_range(self, value: List[Union[float, int]]):
        if not isinstance(value, list) or len(value) != 2:
            raise ValueError(
                "core_signal_range must be a list of two elements."
            )
        if not all(isinstance(val, (float, int)) for val in value):
            raise TypeError(
                "All elements in core_signal_range must be numbers."
            )
        self._core_signal_range = value

    @property
    def detection_margin(self) -> Union[float, int]:
        return self._detection_margin

    @detection_margin.setter
    def detection_margin(self, value: Union[float, int]):
        if not isinstance(value, (float, int)) or value <= 0:
            raise ValueError("detection_margin must be a positive number.")
        self._detection_margin = value

    @property
    def z_scan_range(self) -> List[Union[float, int]]:
        return self._z_scan_range

    @z_scan_range.setter
    def z_scan_range(self, value: List[Union[float, int]]):
        if (
            not isinstance(value, list)
            or len(value) != 2
            or value[1] <= value[0]
        ):
            raise ValueError(
                "z_scan_range must be a list of two elements where the "
                "second element is greater than the first."
            )
        self._z_scan_range = value

    @property
    def z_scan_range_sample_count(self) -> int:
        return self._z_scan_range_sample_count

    @z_scan_range_sample_count.setter
    def z_scan_range_sample_count(self, value: int):
        if not isinstance(value, int) or value <= 0:
            raise ValueError(
                "z_scan_range_sample_count must be a positive integer."
            )
        self._z_scan_range_sample_count = value

    @property
    def z_scan_range_scan_count(self) -> int:
        return self._z_scan_range_scan_count

    @z_scan_range_scan_count.setter
    def z_scan_range_scan_count(self, value: int):
        if not isinstance(value, int) or value <= 0:
            raise ValueError(
                "z_scan_range_scan_count must be a positive integer."
            )
        self._z_scan_range_scan_count = value

    def measure_tilt(
        self,
        z_scan_range: List[Union[float, int]] = [10, 100],
        z_scan_range_sample_count: int = 3,
        z_scan_range_scan_count: int = 1,
    ):
        """
        Measures tilt by setting scan range parameters.

        Parameters:
            z_scan_range (List[Union[float, int]]): Range for the z-scan.
            z_scan_range_sample_count (int): Number of samples in the z-scan.
            z_scan_range_scan_count (int): Number of scans in the z-scan.

        Returns:
            self: The instance of the FiberAligner class.

        """
        self.z_scan_range = z_scan_range
        self.z_scan_range_sample_count = z_scan_range_sample_count
        self.z_scan_range_scan_count = z_scan_range_scan_count
        self.detect_light_direction = True

        return self

    def to_dict(self) -> Dict:
        """
        Converts the current state of the object into a dictionary.

        Returns:
            dict: Dictionary representation of the current state of the object.
        """
        node_dict = super().to_dict()
        # Add custom attributes not covered by super().__init__()
        node_dict.update(
            {
                "fiber_radius": self.fiber_radius,
                "center_stage": self.center_stage,
                "action_upon_failure": self.action_upon_failure,
                "illumination_name": self.illumination_name,
                "core_signal_lower_threshold": self.core_signal_lower_threshold,
                "core_signal_range": self.core_signal_range,
                "core_position_offset_tolerance": self.detection_margin,
                "detect_light_direction": self.detect_light_direction,
                "z_scan_range": self.z_scan_range,
                "z_scan_range_sample_count": self.z_scan_range_sample_count,
                "z_scan_range_scan_count": self.z_scan_range_scan_count,
            }
        )
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

    def __init__(
        self,
        image: Image,
        name: str = "Marker aligner",
        marker_size: List[float] = [5.0, 5.0],
        center_stage: bool = True,
        action_upon_failure: str = "abort",
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
        z_scan_sample_mode: str = "correlation",
        measure_z: bool = False,
    ):
        """
        Initializes the MarkerAligner with the provided parameters.
        """
        super().__init__(node_type="marker_alignment", name=name)

        # Set attributes via setters
        self.image = image
        self.marker_size = marker_size
        self.center_stage = center_stage
        self.action_upon_failure = action_upon_failure
        self.laser_power = laser_power
        self.scan_area_size = scan_area_size
        self.scan_area_res_factors = scan_area_res_factors
        self.detection_margin = detection_margin
        self.correlation_threshold = correlation_threshold
        self.residual_threshold = residual_threshold
        self.max_outliers = max_outliers
        self.orthonormalize = orthonormalize
        self.z_scan_sample_count = z_scan_sample_count
        self.z_scan_sample_distance = z_scan_sample_distance
        self.z_scan_sample_mode = z_scan_sample_mode
        self.measure_z = measure_z

        self.alignment_anchors = []

    # Property setters with validation
    @property
    def image(self) -> Image:
        return self._image

    @image.setter
    def image(self, value: Image):
        if not isinstance(value, Image):
            raise TypeError("image must be an instance of Image class.")
        self._image = value

    @property
    def marker_size(self) -> List[float]:
        return self._marker_size

    @marker_size.setter
    def marker_size(self, value: List[float]):
        if (
            not isinstance(value, list)
            or len(value) != 2
            or not all(isinstance(val, (float, int)) for val in value)
        ):
            raise TypeError(
                "marker_size must be a list of two positive numbers."
            )
        if value[0] <= 0 or value[1] <= 0:
            raise ValueError("marker_size must be greater than 0.")
        self._marker_size = value

    @property
    def center_stage(self) -> bool:
        return self._center_stage

    @center_stage.setter
    def center_stage(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("center_stage must be a boolean.")
        self._center_stage = value

    @property
    def action_upon_failure(self) -> str:
        return self._action_upon_failure

    @action_upon_failure.setter
    def action_upon_failure(self, value: str):
        if value not in ["abort", "ignore"]:
            raise ValueError(
                "action_upon_failure must be 'abort' or 'ignore'."
            )
        self._action_upon_failure = value

    @property
    def laser_power(self) -> float:
        return self._laser_power

    @laser_power.setter
    def laser_power(self, value: float):
        if not isinstance(value, (float, int)) or value < 0:
            raise ValueError("laser_power must be a non-negative number.")
        self._laser_power = value

    @property
    def scan_area_size(self) -> List[float]:
        return self._scan_area_size

    @scan_area_size.setter
    def scan_area_size(self, value: List[float]):
        if (
            not isinstance(value, list)
            or len(value) != 2
            or not all(isinstance(val, (float, int)) for val in value)
        ):
            raise TypeError("scan_area_size must be a list of two numbers.")
        self._scan_area_size = value

    @property
    def scan_area_res_factors(self) -> List[float]:
        return self._scan_area_res_factors

    @scan_area_res_factors.setter
    def scan_area_res_factors(self, value: List[float]):
        if (
            not isinstance(value, list)
            or len(value) != 2
            or not all(isinstance(val, (float, int)) for val in value)
        ):
            raise TypeError(
                "scan_area_res_factors must be a list of two numbers."
            )
        self._scan_area_res_factors = value

    @property
    def detection_margin(self) -> float:
        return self._detection_margin

    @detection_margin.setter
    def detection_margin(self, value: float):
        if not isinstance(value, (float, int)) or value < 0:
            raise ValueError("detection_margin must be a non-negative number.")
        self._detection_margin = value

    @property
    def correlation_threshold(self) -> float:
        return self._correlation_threshold

    @correlation_threshold.setter
    def correlation_threshold(self, value: float):
        if not isinstance(value, (float, int)) or not (0 <= value <= 100):
            raise ValueError(
                "correlation_threshold must be between 0 and 100."
            )
        self._correlation_threshold = value

    @property
    def residual_threshold(self) -> float:
        return self._residual_threshold

    @residual_threshold.setter
    def residual_threshold(self, value: float):
        if not isinstance(value, (float, int)) or value < 0:
            raise ValueError(
                "residual_threshold must be a non-negative number."
            )
        self._residual_threshold = value

    @property
    def max_outliers(self) -> int:
        return self._max_outliers

    @max_outliers.setter
    def max_outliers(self, value: int):
        if not isinstance(value, int) or value < 0:
            raise ValueError("max_outliers must be a non-negative integer.")
        self._max_outliers = value

    @property
    def orthonormalize(self) -> bool:
        return self._orthonormalize

    @orthonormalize.setter
    def orthonormalize(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("orthonormalize must be a boolean.")
        self._orthonormalize = value

    @property
    def z_scan_sample_count(self) -> int:
        return self._z_scan_sample_count

    @z_scan_sample_count.setter
    def z_scan_sample_count(self, value: int):
        if not isinstance(value, int) or value < 1:
            raise ValueError("z_scan_sample_count must be at least 1.")
        self._z_scan_sample_count = value

    @property
    def z_scan_sample_distance(self) -> float:
        return self._z_scan_sample_distance

    @z_scan_sample_distance.setter
    def z_scan_sample_distance(self, value: float):
        if not isinstance(value, (float, int)) or value <= 0:
            raise ValueError(
                "z_scan_sample_distance must be a positive number."
            )
        self._z_scan_sample_distance = value

    @property
    def z_scan_sample_mode(self) -> str:
        return self._z_scan_sample_mode

    @z_scan_sample_mode.setter
    def z_scan_sample_mode(self, value: str):
        if value not in ["correlation", "intensity"]:
            raise ValueError(
                'z_scan_sample_mode must be either "correlation" or "intensity".'
            )
        self._z_scan_sample_mode = value

    @property
    def measure_z(self) -> bool:
        return self._measure_z

    @measure_z.setter
    def measure_z(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("measure_z must be a boolean.")
        self._measure_z = value

    def add_marker(
        self, position: List[float], orientation: float, label: str
    ):
        """
        Adds a marker to the alignment anchors.
        """
        if not isinstance(label, str):
            raise TypeError("label must be a string.")
        if not isinstance(orientation, (float, int)):
            try:
                float(orientation)
            except:
                raise TypeError("orientation must be a float or an int.")
        if (
            not isinstance(position, list)
            or len(position) != 3
            or not all(isinstance(val, (float, int)) for val in position)
        ):
            raise TypeError("position must be a list of three numbers.")

        self.alignment_anchors.append(
            {"label": label, "position": position, "rotation": orientation}
        )
        return self

    def set_markers_at(
        self,
        positions: List[List[float]],
        orientations: List[float] = None,
        labels: List[str] = None,
    ):
        """
        Creates multiple markers at specified positions with given orientations.
        """
        if labels is None:
            labels = [f"marker_{i}" for i in range(len(positions))]
        if orientations is None:
            orientations = [0 for i in range(len(positions))]
        if len(labels) != len(positions) or len(labels) != len(orientations):
            raise ValueError(
                "The number of labels, positions, and orientations must match."
            )

        for label in labels:
            if not isinstance(label, str):
                raise TypeError("All labels must be strings.")

        for position in positions:
            if (
                not isinstance(position, list)
                or len(position) != 3
                or not all(isinstance(val, (float, int)) for val in position)
            ):
                raise TypeError(
                    "All positions must be lists of three numbers."
                )

        for label, orientation, position in zip(
            labels, orientations, positions
        ):
            self.add_marker(position, orientation, label)
        return self

    def to_dict(self) -> Dict:
        """
        Converts the current state of the object into a dictionary representation.
        """
        node_dict = super().to_dict()
        node_dict.update(
            {
                "marker": {"image": self.image.id, "size": self.marker_size},
                "center_stage": self.center_stage,
                "action_upon_failure": self.action_upon_failure,
                "laser_power": self.laser_power,
                "scan_area_size": self.scan_area_size,
                "scan_area_res_factors": self.scan_area_res_factors,
                "detection_margin": self.detection_margin,
                "correlation_threshold": self.correlation_threshold,
                "residual_threshold": self.residual_threshold,
                "max_outliers": self.max_outliers,
                "orthonormalize": self.orthonormalize,
                "z_scan_sample_count": self.z_scan_sample_count,
                "z_scan_sample_distance": self.z_scan_sample_distance,
                "z_scan_optimization_mode": self.z_scan_sample_mode,
                "measure_z": self.measure_z,
                "alignment_anchors": self.alignment_anchors,
            }
        )
        return node_dict


class EdgeAligner(Node):
    """
    A class to represent an edge aligner with various attributes and methods for managing edge alignment.

    Attributes:
        alignment_anchors (List[Dict[str, Any]]): List of alignment anchors.
    """

    def __init__(
        self,
        name: str = "Edge aligner",
        edge_location: List[float] = [0.0, 0.0],
        edge_orientation: float = 0.0,
        center_stage: bool = True,
        action_upon_failure: str = "abort",
        laser_power: Union[float, int] = 0.5,
        scan_area_res_factors: List[float] = [1.0, 1.0],
        scan_z_sample_distance: Union[float, int] = 0.1,
        scan_z_sample_count: int = 51,
        outlier_threshold: float = 10.0,
    ):
        """
        Initialize the edge aligner with the specified parameters.
        """
        super().__init__(node_type="edge_alignment", name=name)

        # Set attributes using setters
        self.edge_location = edge_location
        self.edge_orientation = edge_orientation
        self.center_stage = center_stage
        self.action_upon_failure = action_upon_failure
        self.laser_power = laser_power
        self.scan_area_res_factors = scan_area_res_factors
        self.scan_z_sample_distance = scan_z_sample_distance
        self.scan_z_sample_count = scan_z_sample_count
        self.outlier_threshold = outlier_threshold

        self.alignment_anchors = []

    # Property setters with validation
    @property
    def edge_location(self) -> List[float]:
        return self._edge_location

    @edge_location.setter
    def edge_location(self, value: List[float]):
        if (
            not isinstance(value, list)
            or len(value) != 2
            or not all(isinstance(val, (float, int)) for val in value)
        ):
            raise TypeError("edge_location must be a list of two numbers.")
        self._edge_location = value

    @property
    def edge_orientation(self) -> float:
        return self._edge_orientation

    @edge_orientation.setter
    def edge_orientation(self, value: float):
        if not isinstance(value, (float, int)):
            raise TypeError("edge_orientation must be a float or an int.")
        self._edge_orientation = value

    @property
    def center_stage(self) -> bool:
        return self._center_stage

    @center_stage.setter
    def center_stage(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("center_stage must be a boolean.")
        self._center_stage = value

    @property
    def action_upon_failure(self) -> str:
        return self._action_upon_failure

    @action_upon_failure.setter
    def action_upon_failure(self, value: str):
        if value not in ["abort", "ignore"]:
            raise ValueError(
                "action_upon_failure must be 'abort' or 'ignore'."
            )
        self._action_upon_failure = value

    @property
    def laser_power(self) -> Union[float, int]:
        return self._laser_power

    @laser_power.setter
    def laser_power(self, value: Union[float, int]):
        if not isinstance(value, (float, int)) or value < 0:
            raise ValueError("laser_power must be a non-negative number.")
        self._laser_power = value

    @property
    def scan_area_res_factors(self) -> List[float]:
        return self._scan_area_res_factors

    @scan_area_res_factors.setter
    def scan_area_res_factors(self, value: List[float]):
        if (
            not isinstance(value, list)
            or len(value) != 2
            or not all(isinstance(val, (float, int)) for val in value)
        ):
            raise TypeError(
                "scan_area_res_factors must be a list of two numbers greater than zero."
            )
        if not all(factor > 0 for factor in value):
            raise ValueError(
                "All elements in scan_area_res_factors must be greater than 0."
            )
        self._scan_area_res_factors = value

    @property
    def scan_z_sample_distance(self) -> Union[float, int]:
        return self._scan_z_sample_distance

    @scan_z_sample_distance.setter
    def scan_z_sample_distance(self, value: Union[float, int]):
        if not isinstance(value, (float, int)) or value <= 0:
            raise ValueError(
                "scan_z_sample_distance must be a positive number."
            )
        self._scan_z_sample_distance = value

    @property
    def scan_z_sample_count(self) -> int:
        return self._scan_z_sample_count

    @scan_z_sample_count.setter
    def scan_z_sample_count(self, value: int):
        if not isinstance(value, int) or value < 1:
            raise ValueError(
                "scan_z_sample_count must be an integer greater than zero."
            )
        self._scan_z_sample_count = value

    @property
    def outlier_threshold(self) -> float:
        return self._outlier_threshold

    @outlier_threshold.setter
    def outlier_threshold(self, value: float):
        if not isinstance(value, (float, int)) or not (0 <= value <= 100):
            raise ValueError(
                "outlier_threshold must be a number between 0 and 100."
            )
        self._outlier_threshold = value

    def add_measurement(
        self,
        offset: Union[float, int],
        scan_area_size: List[Union[float, int]],
        label: str,
    ):
        """
        Add a measurement with a label, offset, and scan area size.
        """
        if not isinstance(label, str):
            raise TypeError("label must be a string.")
        if not isinstance(offset, (float, int)):
            raise TypeError("offset must be a float or an int.")
        if (
            not isinstance(scan_area_size, list)
            or len(scan_area_size) != 2
            or not all(isinstance(val, (float, int)) for val in scan_area_size)
        ):
            raise TypeError("scan_area_size must be a list of two numbers.")
        if scan_area_size[0] <= 0:
            raise ValueError(
                "The width (X) in scan_area_size must be greater than 0."
            )
        if scan_area_size[1] < 0:
            raise ValueError(
                "The height (Y) in scan_area_size must be greater than or equal to 0."
            )

        self.alignment_anchors.append(
            {
                "label": label,
                "offset": offset,
                "scan_area_size": scan_area_size,
            }
        )
        return self

    def set_measurements_at(
        self,
        offsets: List[Union[float, int]],
        scan_area_sizes: List[List[Union[float, int]]] = None,
        labels: List[str] = None,
    ):
        """
        Set multiple measurements at specified positions.
        """
        if scan_area_sizes is None:
            scan_area_sizes = [[50.0, 10.0]] * len(offsets)
        if labels is None:
            labels = [f"marker_{i}" for i in range(len(offsets))]
        if len(labels) != len(scan_area_sizes) or len(labels) != len(offsets):
            raise ValueError(
                "The number of labels, offsets, and scan_area_sizes must match."
            )

        for label in labels:
            if not isinstance(label, str):
                raise TypeError("All labels must be strings.")

        for offset in offsets:
            if not isinstance(offset, (float, int)):
                raise TypeError("All offsets must be float or int.")

        for scan_area_size in scan_area_sizes:
            if (
                not isinstance(scan_area_size, list)
                or len(scan_area_size) != 2
                or not all(
                    isinstance(val, (float, int)) for val in scan_area_size
                )
            ):
                raise TypeError(
                    "All scan_area_sizes must be lists of two numbers."
                )
            if scan_area_size[0] <= 0:
                raise ValueError(
                    "The width (X) in scan_area_size must be greater than 0."
                )
            if scan_area_size[1] < 0:
                raise ValueError(
                    "The height (Y) in scan_area_size must be greater than or equal to 0."
                )

        for label, offset, scan_area_size in zip(
            labels, offsets, scan_area_sizes
        ):
            self.add_measurement(offset, scan_area_size, label)
        return self

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the current state of the object into a dictionary representation.
        """
        node_dict = super().to_dict()
        node_dict.update(
            {
                "xy_position_local_cos": self.edge_location,
                "z_rotation_local_cos": self.edge_orientation,
                "center_stage": self.center_stage,
                "action_upon_failure": self.action_upon_failure,
                "laser_power": self.laser_power,
                "scan_area_res_factors": self.scan_area_res_factors,
                "scan_z_sample_distance": self.scan_z_sample_distance,
                "scan_z_sample_count": self.scan_z_sample_count,
                "outlier_threshold": self.outlier_threshold,
                "alignment_anchors": self.alignment_anchors,
            }
        )
        return node_dict
