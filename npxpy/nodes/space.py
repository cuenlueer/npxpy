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
from typing import Dict, List
from npxpy.nodes.node import Node

class Scene(Node):
    """
    scene nodes.

    Attributes:
        position (List[float]): Position of the scene [x, y, z].
        rotation (List[float]): Rotation of the scene [psi, theta, phi].
    """
    def __init__(self, name: str = 'Scene', position: List[float] = [0, 0, 0], rotation: List[float] = [0.0, 0.0, 0.0], writing_direction_upward: bool = True):
        """
        Initialize the scene with a name and writing direction.

        Parameters:
            name (str): The name of the scene node.
            position (List[float]): Initial position of the scene [x, y, z].
            rotation (List[float]): Initial rotation of the scene [psi, theta, phi].
            writing_direction_upward (bool): Writing direction of the scene.
        """
        super().__init__('scene', name, position=position, rotation=rotation, writing_direction_upward=writing_direction_upward)
        
    def position_at(self, position: List[float] = [0, 0, 0], rotation: List[float] = [0.0, 0.0, 0.0]):
        """
        Set the current position and rotation of the scene.

        Parameters:
            position (List[float]): List of position values [x, y, z].
            rotation (List[float]): List of rotation angles [psi, theta, phi].

        Returns:
            self: The instance of the Scene class.

        Raises:
            ValueError: If position or rotation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(position) != 3:
            raise ValueError("position must be a list of three elements.")
        if not all(isinstance(p, (int, float)) for p in position):
            raise ValueError("All position elements must be numbers.")
        
        if len(rotation) != 3:
            raise ValueError("rotation must be a list of three elements.")
        if not all(isinstance(r, (int, float)) for r in rotation):
            raise ValueError("All rotation elements must be numbers.")
        
        self.position = position
        self.rotation = rotation
        return self
    
    def translate(self, translation: List[float]):
        """
        Translate the current position by the specified translation.

        Parameters:
            translation (List[float]): List of translation values [dx, dy, dz].

        Raises:
            ValueError: If translation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(translation) != 3:
            raise ValueError("translation must be a list of three elements.")
        if not all(isinstance(t, (int, float)) for t in translation):
            raise ValueError("All translation elements must be numbers.")
        
        self.position = [pos + trans for pos, trans in zip(self.position, translation)]

    def rotate(self, rotation: List[float]):
        """
        Rotate the scene by the specified rotation angles.

        Parameters:
            rotation (List[float]): List of rotation angles to apply [d_psi, d_theta, d_phi].

        Raises:
            ValueError: If rotation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(rotation) != 3:
            raise ValueError("rotation must be a list of three elements.")
        if not all(isinstance(r, (int, float)) for r in rotation):
            raise ValueError("All rotation elements must be numbers.")
        
        self.rotation = [(angle + rot) % 360 for angle, rot in zip(self.rotation, rotation)]
        
    def to_dict(self) -> Dict:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            dict: Dictionary representation of the current state of the object.
        """
        node_dict = super().to_dict()
        return node_dict


class Group(Node):
    """
    Class: group nodes.

    Attributes:
        position (List[float]): Position of the group [x, y, z].
        rotation (List[float]): Rotation of the group [psi, theta, phi].
    """
    def __init__(self, name: str = 'Group', position: List[float] = [0, 0, 0], rotation: List[float] = [0.0, 0.0, 0.0]):
        """
        Initialize the group with a name.

        Parameters:
            name (str): The name of the group node.
        """
        super().__init__('group', name, position=position, rotation=rotation)

        
    def position_at(self, position: List[float] = [0, 0, 0], rotation: List[float] = [0.0, 0.0, 0.0]):
        """
        Set the current position and rotation of the group.

        Parameters:
            position (List[float]): List of position values [x, y, z].
            rotation (List[float]): List of rotation angles [psi, theta, phi].

        Returns:
            self: The instance of the Group class.

        Raises:
            ValueError: If position or rotation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(position) != 3:
            raise ValueError("position must be a list of three elements.")
        if not all(isinstance(p, (int, float)) for p in position):
            raise ValueError("All position elements must be numbers.")
        
        if len(rotation) != 3:
            raise ValueError("rotation must be a list of three elements.")
        if not all(isinstance(r, (int, float)) for r in rotation):
            raise ValueError("All rotation elements must be numbers.")
        
        self.position = position
        self.rotation = rotation
        return self
    
    def translate(self, translation: List[float]):
        """
        Translate the current position by the specified translation.

        Parameters:
            translation (List[float]): List of translation values [dx, dy, dz].

        Raises:
            ValueError: If translation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(translation) != 3:
            raise ValueError("translation must be a list of three elements.")
        if not all(isinstance(t, (int, float)) for t in translation):
            raise ValueError("All translation elements must be numbers.")
        
        self.position = [pos + trans for pos, trans in zip(self.position, translation)]

    def rotate(self, rotation: List[float]):
        """
        Rotate the group by the specified rotation angles.

        Parameters:
            rotation (List[float]): List of rotation angles to apply [d_psi, d_theta, d_phi].

        Raises:
            ValueError: If rotation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(rotation) != 3:
            raise ValueError("rotation must be a list of three elements.")
        if not all(isinstance(r, (int, float)) for r in rotation):
            raise ValueError("All rotation elements must be numbers.")
        
        self.rotation = [(angle + rot) % 360 for angle, rot in zip(self.rotation, rotation)]
        
    def to_dict(self) -> Dict:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            dict: Dictionary representation of the current state of the object.
        """
        node_dict = super().to_dict()
        return node_dict


class Array(Node):
    """
    Class: array nodes.

    Attributes:
        position (List[float]): Position of the array [x, y, z].
        rotation (List[float]): Rotation of the array [psi, theta, phi].
        count (List[int]): Number of grid points in [x, y] direction.
        spacing (List[float]): Spacing of the grid in [width, height].
        order (str): Order of the array ('Lexical' or 'Meander').
        shape (str): Shape of the array ('Rectangular' or 'Round').
    """
    def __init__(self, name: str = 'Array', position: List[float] = [0, 0, 0], rotation: List[float] = [0.0, 0.0, 0.0],
                 count: List[int] = [5, 5], spacing: List[float] = [100.0, 100.0],
                 order: str = "Lexical", shape: str = 'Rectangular'):
        """
        Initialize the array with a name, position, rotation, count, spacing, order, and shape.

        Parameters:
            name (str): The name of the array node.
            position (List[float]): Initial position of the array [x, y, z].
            rotation (List[float]): Initial rotation of the array [psi, theta, phi].
            count (List[int]): Number of grid points in [x, y] direction. Must be integers and greater than zero.
            spacing (List[float]): Spacing of the grid in [width, height]. Can be integers or floats.
            order (str): Order of the array. Can only be 'Lexical' or 'Meander'.
            shape (str): Shape of the array. Can only be 'Rectangular' or 'Round'.

        Raises:
            ValueError: If count elements are not integers or not greater than zero.
                        If spacing elements are not numbers.
                        If order is not 'Lexical' or 'Meander'.
                        If shape is not 'Rectangular' or 'Round'.
        """
        if not all(isinstance(c, int) and c > 0 for c in count):
            raise ValueError("All count elements must be integers greater than zero.")
        if not all(isinstance(s, (int, float)) for s in spacing):
            raise ValueError("All spacing elements must be numbers.")
        if order not in ['Lexical', 'Meander']:
            raise ValueError("order must be either 'Lexical' or 'Meander'.")
        if shape not in ['Rectangular', 'Round']:
            raise ValueError("shape must be either 'Rectangular' or 'Round'.")

        super().__init__('array', name=name, position=position, rotation=rotation,
                         order=order, shape=shape, count=count, spacing=spacing)
        
    def set_grid(self, count: List[int] = [5, 5], spacing: List[float] = [200.0, 200.0]):
        """
        Sets the grid point count and spacing.

        Parameters:
            count (List[int]): Number of grid points in [x, y] direction.
            spacing (List[float]): Spacing of the grid in [width, height].

        Returns:
            self: The instance of the Array class.

        Raises:
            ValueError: If count or spacing does not contain exactly two elements.
                        If count elements are not integers or not greater than zero.
                        If spacing elements are not numbers.
        """
        if len(count) != 2 or len(spacing) != 2:
            raise ValueError("count and spacing must each be lists of two elements.")
        if not all(isinstance(c, int) and c > 0 for c in count):
            raise ValueError("All count elements must be integers greater than zero.")
        if not all(isinstance(s, (int, float)) for s in spacing):
            raise ValueError("All spacing elements must be numbers.")
        
        self.count = count
        self.spacing = spacing
        return self
        
    def position_at(self, position: List[float] = [0, 0, 0], rotation: List[float] = [0.0, 0.0, 0.0]):
        """
        Set the current position and rotation of the array.

        Parameters:
            position (List[float]): List of position values [x, y, z].
            rotation (List[float]): List of rotation angles [psi, theta, phi].

        Returns:
            self: The instance of the Array class.

        Raises:
            ValueError: If position or rotation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(position) != 3:
            raise ValueError("position must be a list of three elements.")
        if not all(isinstance(p, (int, float)) for p in position):
            raise ValueError("All position elements must be numbers.")
        
        if len(rotation) != 3:
            raise ValueError("rotation must be a list of three elements.")
        if not all(isinstance(r, (int, float)) for r in rotation):
            raise ValueError("All rotation elements must be numbers.")
        
        self.position = position
        self.rotation = rotation
        return self
    
    def translate(self, translation: List[float]):
        """
        Translate the current position by the specified translation.

        Parameters:
            translation (List[float]): List of translation values [dx, dy, dz].

        Raises:
            ValueError: If translation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(translation) != 3:
            raise ValueError("translation must be a list of three elements.")
        if not all(isinstance(t, (int, float)) for t in translation):
            raise ValueError("All translation elements must be numbers.")
        
        self.position = [pos + trans for pos, trans in zip(self.position, translation)]

    def rotate(self, rotation: List[float]):
        """
        Rotate the array by the specified rotation angles.

        Parameters:
            rotation (List[float]): List of rotation angles to apply [d_psi, d_theta, d_phi].

        Raises:
            ValueError: If rotation does not contain exactly three elements,
                        or if any element is not a number.
        """
        if len(rotation) != 3:
            raise ValueError("rotation must be a list of three elements.")
        if not all(isinstance(r, (int, float)) for r in rotation):
            raise ValueError("All rotation elements must be numbers.")
        
        self.rotation = [(angle + rot) % 360 for angle, rot in zip(self.rotation, rotation)]
    
    def to_dict(self) -> Dict:
        """
        Converts the current state of the object into a dictionary representation.

        Returns:
            dict: Dictionary representation of the current state of the object.
        """
        node_dict = super().to_dict()
        return node_dict