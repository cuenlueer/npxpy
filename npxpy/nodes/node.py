# -*- coding: utf-8 -*-
"""
npxpy
Created on Thu Feb 29 11:49:17 2024

@author: Caghan Uenlueer
Neuromorphic Quantumphotonics
Heidelberg University
E-Mail:	caghan.uenlueer@kip.uni-heidelberg.de

This file is part of npxpy (formerly nanoAPI), which is licensed under the GNU
Lesser General Public License v3.0. You can find a copy of this license at
https://www.gnu.org/licenses/lgpl-3.0.html
"""
import uuid
import copy
from typing import Dict, Any, List, Tuple


class Node:
    """
    A class to represent a node object of nanoPrintX with various attributes
    and methods for managing node hierarchy.

    Attributes:
        type (str): Type of the node.
        name (str): Name of the node.
        position (List[float]): Position of the node [x, y, z].
        rotation (List[float]): Rotation of the node [psi, theta, phi].
        children (List[str]): List of children node IDs.
        children_nodes (List[Node]): List of children nodes.
        properties (Any): Properties of the node.
        geometry (Any): Geometry of the node.
        unique_attributes (Dict[str, Any]): Additional dynamic attributes.
    """

    def __init__(
        self,
        node_type: str,
        name: str,
        position: List[float] = [0.0, 0.0, 0.0],
        rotation: List[float] = [0.0, 0.0, 0.0],
    ):
        """
        Initialize a Node instance with the specified parameters.

        Parameters:
            node_type (str): Type of the node.
            name (str): Name of the node.
            properties (Any, optional): Properties of the node. Defaults to None.
            geometry (Any, optional): Geometry of the node. Defaults to None.
            **kwargs (Any): Additional dynamic attributes.
        """

        self.id = str(uuid.uuid4())
        self._type = node_type
        self.name = name
        self.position = position
        self.rotation = rotation
        self.properties = {}
        self.geometry = {}

        self.children: List[str] = []
        self.children_nodes: List[Node] = []
        self.all_descendants: List[Node] = self._generate_all_descendants()

        self.parents_nodes: List[Node] = []
        self.all_ancestors: List[Node] = []

    @property
    def name(self):
        """Return the name of the node."""
        return self._name

    @name.setter
    def name(self, value: str):
        value = str(value)
        """Set the name of the node with validation to ensure it is a non-empty string."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("name must be a non-empty string.")
        self._name = value

    def add_child(self, child_node: "Node"):
        """
        Add a child node to the current node.

        Parameters:
            child_node (Node): The child node to add.
        """
        if not all(
            hasattr(child_node, attr)
            for attr in ["_type", "all_descendants", "all_ancestors"]
        ):
            raise TypeError(
                "Only instances of nodes can be added as children to nodes!"
            )
        elif self._type == "structure":
            raise ValueError(
                "Structure, Text and Lens are terminal nodes! They cannot have children!"
            )
        elif child_node._type == "project":
            raise ValueError(
                "A project node can never be a child to any node!"
            )
        elif child_node._type == "scene":
            if self._has_ancestor_of_type("scene"):
                raise ValueError("Nested scenes are not allowed!")
        elif self in child_node.all_descendants:
            raise ValueError(
                "This node cannot be added since it is a ancestor to the current node!"
            )

        child_node.parents_nodes.append(self)
        self.children_nodes.append(child_node)
        self.all_descendants = (
            self._generate_all_descendants()
        )  # Update descendants list
        child_node.all_ancestors = (
            child_node._generate_all_ancestors()
        )  # Update ancestors list

        for i in (
            self.all_descendants + child_node.all_ancestors
        ):  # Update for the whole batch of nodes their ancestors and descendants
            i.all_descendants = i._generate_all_descendants()
            i.all_ancestors = i._generate_all_ancestors()

        if child_node._type == "structure":
            if (
                not "scene" in [i._type for i in self.all_ancestors]
                and "scene" != self._type
            ):
                print("WARNING: Structures have to be inside Scene nodes!")

        return self

    def _has_ancestor_of_type(self, node_type: str) -> bool:
        """
        Check if the current node has an ancestor of the specified type.

        Parameters:
            node_type (str): The type of the ancestor node to check for.

        Returns:
            bool: True if an ancestor of the specified type exists, False otherwise.
        """
        current_node = self
        while current_node:
            if current_node._type == node_type:
                return True
            current_node = getattr(
                current_node, "parent", None
            )  # Assumes a parent attribute is set for each node
        return False

    def tree(
        self,
        level: int = 0,
        show_type: bool = True,
        show_id: bool = False,
        is_last: bool = True,
        prefix: str = "",
    ):
        """
        Print the tree structure of the node and its descendants.

        Parameters:
            level (int, optional): The current level in the tree. Defaults to 0.
            show_type (bool, optional): Whether to show the node type. Defaults to True.
            show_id (bool, optional): Whether to show the node ID. Defaults to False.
            is_last (bool, optional): Whether the node is the last child. Defaults to True.
            prefix (str, optional): The prefix for the current level. Defaults to ''.
        """
        indent = (
            "" if level == 0 else prefix + ("└" if is_last else "├") + "──"
        )
        output = (
            f"{indent}{self.name} ({self._type})"
            if show_type
            else f"{indent}{self.name}"
        )
        if show_id:
            output += f" (ID: {self.id})"
        print(output)
        new_prefix = prefix + ("    " if is_last else "│   ")
        child_count = len(self.children_nodes)
        for index, child in enumerate(self.children_nodes):
            child.tree(
                level + 1,
                show_type,
                show_id,
                is_last=(index == child_count - 1),
                prefix=new_prefix,
            )

    def deepcopy_node(self, copy_children: bool = True) -> "Node":
        """
        Create a deep copy of the node.

        Parameters:
            copy_children (bool, optional): Whether to copy children nodes. Defaults to True.

        Returns:
            Node: A deep copy of the current node.
        """
        if copy_children:
            copied_node = copy.deepcopy(self)
            self._reset_ids(copied_node)
        else:
            copied_node = copy.copy(self)
            copied_node.id = str(uuid.uuid4())
            copied_node.children_nodes = []
        return copied_node

    def _reset_ids(self, node: "Node"):
        """
        Reset the IDs of the node and its descendants.

        Parameters:
            node (Node): The node to reset IDs for.
        """
        node.id = str(uuid.uuid4())
        for child in node.children_nodes:
            self._reset_ids(child)

    def grab_node(
        self, node_types_with_indices: List[Tuple[str, int]]
    ) -> "Node":
        """
        Grab nodes based on the specified types and indices.

        Parameters:
            node_types_with_indices (List[Tuple[str, int]]): List of tuples containing node type and index.

        Returns:
            Node: The node found based on the specified types and indices.
        """
        current_level_nodes = [self]
        for node_type, index in node_types_with_indices:
            next_level_nodes = []
            for node in current_level_nodes:
                filtered_nodes = [
                    child
                    for child in node.children_nodes
                    if child._type == node_type
                ]
                if len(filtered_nodes) > index:
                    next_level_nodes.append(filtered_nodes[index])
            current_level_nodes = next_level_nodes
        return current_level_nodes[0]

    def _generate_all_descendants(self) -> List["Node"]:
        """
        Generate a list of all descendant nodes.

        Returns:
            List[Node]: List of all descendant nodes.
        """
        descendants = []
        nodes_to_check = [self]
        while nodes_to_check:
            current_node = nodes_to_check.pop()
            descendants.extend(current_node.children_nodes)
            nodes_to_check.extend(current_node.children_nodes)
        return descendants

    def _generate_all_ancestors(self) -> List["Node"]:
        """
        Generate a list of all ancestor nodes.

        Returns:
            List[Node]: List of all descendant nodes.
        """
        ancestors = []
        nodes_to_check = [self]
        while nodes_to_check:
            current_node = nodes_to_check.pop()
            ancestors.extend(current_node.parents_nodes)
            nodes_to_check.extend(current_node.parents_nodes)
        return ancestors

    def grab_all_nodes_bfs(self, node_type: str) -> List["Node"]:
        """
        Grab all nodes of the specified type using breadth-first search.

        Parameters:
            node_type (str): The type of nodes to grab.

        Returns:
            List[Node]: List of nodes of the specified type.
        """
        result = []
        nodes_to_check = [self]
        while nodes_to_check:
            current_node = nodes_to_check.pop(0)  # Dequeue from the front
            if current_node._type == node_type:
                result.append(current_node)
            nodes_to_check.extend(
                current_node.children_nodes
            )  # Enqueue children
        return result

    def append_node(self, node_to_append: "Node"):
        """
        Append a node to the deepest descendant.

        Parameters:
            node_to_append (Node): The node to append.
        """
        grandest_grandchild = self._find_grandest_grandchild(self)
        grandest_grandchild.add_child(node_to_append)

    def _find_grandest_grandchild(self, current_node: "Node") -> "Node":
        """
        Find the deepest descendant node.

        Parameters:
            current_node (Node): The current node to start the search from.

        Returns:
            Node: The deepest descendant node.
        """
        if not current_node.children_nodes:
            return current_node
        else:
            grandest_children = [
                self._find_grandest_grandchild(child)
                for child in current_node.children_nodes
            ]
            return max(grandest_children, key=lambda node: self._depth(node))

    def _depth(self, node: "Node") -> int:
        """
        Calculate the depth of a node.

        Parameters:
            node (Node): The node to calculate the depth for.

        Returns:
            int: The depth of the node.
        """
        depth = 0
        current = node
        while current.children_nodes:
            current = current.children_nodes[0]
            depth += 1
        return depth

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the node and its attributes to a dictionary format.

        Returns:
            Dict[str, Any]: Dictionary representation of the node.
        """
        self.children = [i.id for i in self.children_nodes]
        node_dict = {
            "type": self._type,
            "id": self.id,
            "name": self.name,
            "position": self.position,
            "rotation": self.rotation,
            "children": self.children,
            "properties": self.properties,
            "geometry": self.geometry,
        }

        return node_dict
