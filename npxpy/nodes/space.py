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
from typing import Dict, List
from npxpy.nodes.node import Node


class _GatekeeperSpace(Node):
    """Helper class for input data validation"""

    def __init__(
        self,
        node_type: str,
        name: str,
        position: List[float] = [0.0, 0.0, 0.0],
        rotation: List[float] = [0.0, 0.0, 0.0],
    ):
        super().__init__(node_type, name)
        self.position = position
        self.rotation = rotation

    @property
    def position(self) -> List[float]:
        return self._position

    @position.setter
    def position(self, value):
        try:
            value_list = list(value)
        except TypeError:
            raise ValueError(
                "Position must be an iterable of three numeric values."
            )
        if len(value_list) != 3:
            raise ValueError("Position must have exactly three elements.")
        try:
            self._position = [float(x) for x in value_list]
        except ValueError as e:
            raise ValueError(
                "All elements in position must be numeric."
            ) from e

    @property
    def rotation(self) -> List[float]:
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        try:
            value_list = list(value)
        except TypeError:
            raise ValueError(
                "Rotation must be an iterable of three numeric values."
            )
        if len(value_list) != 3:
            raise ValueError("Rotation must have exactly three elements.")
        try:
            self._rotation = [float(x) for x in value_list]
        except ValueError as e:
            raise ValueError(
                "All elements in rotation must be numeric."
            ) from e

    def position_at(
        self,
        position: List[float] = [0.0, 0.0, 0.0],
        rotation: List[float] = None,
    ):
        """
        Set the position and rotation of the scene/group/array.

        Parameters:
            position (List[float]): The new position [x, y, z].
            rotation (List[float]): The new rotation [psi, theta, phi].

        Returns:
            Acene/Group/Array: The updated object.
        """
        if rotation is not None:
            self.position = position
            self.rotation = rotation
        else:
            self.position = position
        return self

    def translate(
        self,
        translation: List[float] = [
            0.0,
            0.0,
            0.0,
        ],
    ):
        """
        Translate the current position by the specified values.

        Parameters:
            translation (List[float]): The translation values [dx, dy, dz].

        Raises:
            ValueError: If translation does not have exactly 3 elements.

        Returns:
            Acene/Group/Array: The updated object.
        """
        if (
            len(translation) != 3
            or not all(isinstance(t, (int, float)) for t in translation)
            or not isinstance(translation, list)
        ):
            raise ValueError(
                "Translation must be a list of three numeric elements."
            )
        self.position = [p + t for p, t in zip(self.position, translation)]
        return self

    def rotate(
        self,
        rotation: List[float] = [
            0.0,
            0.0,
            0.0,
        ],
    ):
        """
        Rotate the scene/group/array by specified angles.

        Parameters:
            rotation (List[float]): The rotation values [d_psi, d_theta, d_phi].

        Raises:
            ValueError: If rotation does not have exactly 3 elements.

        Returns:
            Acene/Group/Array: The updated object.
        """
        if len(rotation) != 3 or not all(
            isinstance(r, (int, float)) for r in rotation
        ):
            raise ValueError(
                "Rotation must be a list of three numeric elements."
            )
        self.rotation = [
            (r + delta) % 360 for r, delta in zip(self.rotation, rotation)
        ]
        return self


class Scene(_GatekeeperSpace):
    """
    Class representing a scene node.

    Attributes:
        position (List[float]): Position of the scene [x, y, z].
        rotation (List[float]): Rotation of the scene [psi, theta, phi].
        writing_direction_upward (bool): Writing direction of the scene.
    """

    def __init__(
        self,
        name: str = "Scene",
        position: List[float] = [0, 0, 0],
        rotation: List[float] = [0.0, 0.0, 0.0],
        writing_direction_upward: bool = True,
    ):
        """
        Initialize a Scene node.
        """
        super().__init__("scene", name)
        self.position = position
        self.rotation = rotation
        self._writing_direction_upward = None
        self.writing_direction_upward = (
            writing_direction_upward  # Using setter
        )

    # Getter and setter for writing direction
    @property
    def writing_direction_upward(self):
        return self._writing_direction_upward

    @writing_direction_upward.setter
    def writing_direction_upward(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError("writing_direction_upward must be a boolean.")
        self._writing_direction_upward = value

    def to_dict(self) -> Dict:
        """
        Convert the Scene object into a dictionary.
        """
        node_dict = super().to_dict()
        node_dict["position"] = self.position
        node_dict["rotation"] = self.rotation
        node_dict["writing_direction_upward"] = self.writing_direction_upward
        return node_dict


class Group(_GatekeeperSpace):
    """
    Class representing a group node.

    Attributes:
        position (List[float]): Position of the group [x, y, z].
        rotation (List[float]): Rotation of the group [psi, theta, phi].
    """

    def __init__(
        self,
        name: str = "Group",
        position: List[float] = [0, 0, 0],
        rotation: List[float] = [0.0, 0.0, 0.0],
    ):
        """
        Initialize a Group node.
        """
        super().__init__("group", name)
        self.position = position
        self.rotation = rotation

    def to_dict(self) -> Dict:
        """
        Convert the Group object into a dictionary.
        """
        node_dict = super().to_dict()
        node_dict["position"] = self.position
        node_dict["rotation"] = self.rotation
        return node_dict


class Array(_GatekeeperSpace):
    """
    Class representing an array node with additional attributes.

    Attributes:
        position (List[float]): Position of the array [x, y, z].
        rotation (List[float]): Rotation of the array [psi, theta, phi].
        count (List[int]): Number of grid points in [x, y] direction.
        spacing (List[float]): Spacing of the grid in [width, height].
        order (str): Order of the array ('Lexical' or 'Meander').
        shape (str): Shape of the array ('Rectangular' or 'Round').
    """

    def __init__(
        self,
        name: str = "Array",
        position: List[float] = [0, 0, 0],
        rotation: List[float] = [0.0, 0.0, 0.0],
        count: List[int] = [5, 5],
        spacing: List[float] = [100.0, 100.0],
        order: str = "Lexical",
        shape: str = "Rectangular",
    ):
        """
        Initialize an Array node.
        """
        super().__init__("array", name)
        self.position = position
        self.rotation = rotation
        self.count = count
        self.spacing = spacing
        self.order = order
        self.shape = shape

    # Setters for other attributes
    @property
    def count(self):
        return self._count

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, value: List[int]):
        if len(value) != 2 or not all(
            isinstance(c, int) and c > 0 for c in value
        ):
            raise ValueError(
                "Count must be a list of exactly two integers greater than zero."
            )
        self._count = value

    @property
    def spacing(self):
        return self._spacing

    @spacing.setter
    def spacing(self, value: List[float]):
        if len(value) != 2 or not all(
            isinstance(s, (int, float)) for s in value
        ):
            raise ValueError(
                "Spacing must be a list of exactly two numeric values."
            )
        self._spacing = value

    @property
    def order(self):
        return self._order

    @order.setter
    def order(self, value: str):
        if value not in ["Lexical", "Meander"]:
            raise ValueError("order must be either 'Lexical' or 'Meander'.")
        self._order = value

    @property
    def shape(self):
        return self._shape

    @shape.setter
    def shape(self, value: str):
        if value not in ["Rectangular", "Round"]:
            raise ValueError("shape must be either 'Rectangular' or 'Round'.")
        self._shape = value

    def set_grid(
        self, count: List[int] = count, spacing: List[float] = spacing
    ):
        """
        Set the count and spacing of the array grid.

        Parameters:
            count (List[int]): The new grid point count.
            spacing (List[float]): The new grid spacing.

        Returns:
            Array: The updated Array object.
        """
        self.count = count
        self.spacing = spacing
        return self

    def to_dict(self) -> Dict:
        """
        Convert the Array object into a dictionary.
        """
        node_dict = super().to_dict()
        node_dict["position"] = self.position
        node_dict["rotation"] = self.rotation
        node_dict["count"] = self.count
        node_dict["spacing"] = self.spacing
        node_dict["order"] = self.order
        node_dict["shape"] = self.shape
        return node_dict
