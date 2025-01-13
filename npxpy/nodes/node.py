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
import os
from typing import Dict, Any, List, Tuple, Optional, Union


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

    def add_child(self, *child_nodes: "Node"):
        """
        Add child node(s) to the current node.

        Parameters:
            child_node (Node): The child node(s) to add.
        """
        for child_node in child_nodes:
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
            # Update descendants list of parent

            self.all_descendants += [child_node] + child_node.all_descendants

            for child in [child_node] + child_node.all_descendants:
                child.all_ancestors = (
                    child._generate_all_ancestors()
                )  # Update ancestors list (_generate_all_ancestors() inexpensive and easy!)

            for (
                ancestor
            ) in (
                self.all_ancestors
            ):  # Update descendants for the parent's ancestors
                ancestor.all_descendants += [
                    child_node
                ] + child_node.all_descendants

            """
            # Deprecated?
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
            """
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
            copied_node.all_ancestors = []
            for descendant_node in copied_node.all_descendants:
                index_of_copied_node = descendant_node.all_ancestors.index(
                    copied_node
                )
                descendant_node.all_ancestors = descendant_node.all_ancestors[
                    : index_of_copied_node + 1
                ]
        else:
            copied_node = copy.copy(self)
            copied_node.id = str(uuid.uuid4())
            copied_node.children_nodes = []
            copied_node.all_descendants = []
            copied_node.all_ancestors = []
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

    def grab_node(self, *node_types_with_indices: Tuple[str, int]) -> "Node":
        """
        Grab nodes based on the specified types and indices.

        Parameters:
            node_types_with_indices (Tuple[str, int]):
            Tuples of arbitrary amount containing node type and index.

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

    def _lazy_import_wrapper(self):
        from . import _viewport_helpers

        return _viewport_helpers._lazy_import()

    def viewport(
        self,
        title: Optional[str] = None,
        disable_visibility: Optional[Union[str, List[str]]] = None,
        block_render: Optional[Union[str, List[str]]] = [],
        include_ancestor_transforms: Optional[bool] = True,
    ):
        """
        Opens a PyVista viewport visualizing the attached objects in this node.
        Notes: - Does not visualize multiplications caused by Arrays yet.
               - Lenses might not be displayed correctly/accurately.
                 However, the printed result will not be affected by this.

        Parameters
        ----------
        title : str, optional
            Title to display in the PyVista window. Default is name of calling node.
        disable_visibility : str or list of str, optional
            One or more group names whose visibility should be disabled.
            E.g., "scene" or ["scene", "coarse_alignment"].
        block_render : str or list of str, optional
            One or more group names whose initial rendering should be disabled
            when calling the method.
            E.g., "scene" or ["scene", "coarse_alignment"].

        Returns
        -------
        _GroupedPlotter
            The customized plotter instance after drawing all meshes.

        Examples
        --------
        >>> # Basic usage without disabling any groups
        >>> node.viewport()

        >>> # Disable visibility for scenes and coarse alignments
        >>> node.viewport(disable_visibility=["scene", "coarse_alignment"])
        """
        _GroupedPlotter, _apply_transforms, _meshbuilder = (
            self._lazy_import_wrapper()
        )

        if disable_visibility is None:
            disable_visibility = []
        if title is None:
            title = self.name
        # Create the plotter
        plotter = _GroupedPlotter(
            title=f"npxpy - Project Viewport ({title})",
            update_app_icon=False,
        )

        # Grid, axes, background
        plotter.show_grid(
            grid="back",
            location="outer",
            color="gray",
            xtitle="x",
            ytitle="y",
            ztitle="z",
            show_zlabels=True,
            padding=0.1,
            font_size=8,
        )
        plotter.show_axes()
        plotter.view_isometric()
        plotter.set_background("white")

        # Add logo widget
        HERE = os.path.dirname(__file__)
        TWO_LEVELS_UP = os.path.abspath(os.path.join(HERE, "..", ".."))
        plotter.add_logo_widget(
            logo=os.path.join(TWO_LEVELS_UP, "docs/images/logo.png"),
            opacity=0.75,
            size=(0.15, 0.15),
            position=(0.84, 0.86),
        )

        # init the meshbuilder
        meshbuilder = _meshbuilder()

        for node in [self] + self.all_descendants:
            all_rotations = [
                getattr(ancestor, "rotation", [0, 0, 0])
                for ancestor in node.all_ancestors
            ]
            all_rotations.reverse()

            all_positions = [
                getattr(ancestor, "position", [0, 0, 0])
                for ancestor in node.all_ancestors
            ]
            all_positions.reverse()

            # If False, only go as far as node calling viewport()
            if not include_ancestor_transforms:
                if node != self:
                    dummy = node.all_ancestors.copy()
                    dummy.reverse()
                    start = dummy.index(self)
                    all_positions = all_positions[start:]
                    all_rotations = all_rotations[start:]
                else:
                    all_positions = [[0, 0, 0]]
                    all_rotations = [[0, 0, 0]]

            if node._type == "scene" and node._type not in block_render:
                scene = node
                # Create the circle representing the scene
                if len(scene.all_ancestors) != 0 and hasattr(
                    scene.all_ancestors[-1], "objective"
                ):
                    ronin_node = False
                    objective = scene.all_ancestors[-1].objective
                else:
                    print(
                        (
                            f"{self.name} not attached to any project node.\n"
                            "Objective is thus assumed to be x63."
                        )
                    )
                    ronin_node = True
                    objective = ""  # dummy. wont do anything in this case

                scene_mesh, scene_mesh_dict = _meshbuilder.scene_mesh(
                    objective, ronin_node
                )
                # apply first all_ancestors' rots

                _apply_transforms(
                    scene_mesh,
                    all_positions=all_positions + [scene.position],
                    all_rotations=all_rotations + [scene.rotation],
                )

                # Add to plotter as 'scene' group
                plotter.add_mesh(scene_mesh, **scene_mesh_dict)
            # Structure
            if (
                node._type == "structure"
                and node._mesh
                and node._type not in block_render
            ):
                structure = node
                loaded_mesh = _meshbuilder.load_mesh(structure.mesh.file_path)
                # apply initial mesh transformation
                _apply_transforms(
                    mesh=loaded_mesh,
                    all_positions=[structure.mesh.translation],
                    all_rotations=[structure.mesh.rotation],
                )

                # apply all_ancestors' rots and afterwards structure rotation
                _apply_transforms(
                    mesh=loaded_mesh,
                    all_rotations=all_rotations + [structure.rotation],
                    all_positions=all_positions + [structure.position],
                )

                # Add to plotter
                plotter.add_mesh(
                    loaded_mesh, color=structure.color, group=structure._type
                )

            # Text (structure)
            if (
                node._type == "structure"
                and hasattr(node, "font_size")
                and node._type + "_text" not in block_render
            ):
                text_node = node
                text_mesh, text_mesh_dict = _meshbuilder.txt_mesh(text_node)
                # apply all_ancestors' rots and afterwards structure rotation
                _apply_transforms(
                    mesh=text_mesh,
                    all_rotations=all_rotations + [text_node.rotation],
                    all_positions=all_positions + [text_node.position],
                )

                plotter.add_mesh(text_mesh, **text_mesh_dict)

            # Lens (structure)
            elif (
                node._type == "structure"
                and not node._mesh
                and node._type + "_lens" not in block_render
            ):
                lens = node
                geometry = lens.to_dict()["geometry"]
                del (
                    geometry["type"],
                    geometry["nr_radial_segments"],
                    geometry["nr_phi_segments"],
                )
                lens_mesh = meshbuilder.lens_mesh(**geometry)

                _apply_transforms(
                    mesh=lens_mesh,
                    all_rotations=all_rotations + [lens.rotation],
                    all_positions=all_positions + [lens.position],
                )

                plotter.add_mesh(
                    lens_mesh, color=lens.color, group=lens._type + "_lens"
                )

            # Coarse aligners
            if (
                node._type == "coarse_alignment"
                and node._type not in block_render
            ):
                coarse_aligner = node
                coarse_anchor_mesh, coarse_anchor_mesh_dict = (
                    _meshbuilder.ca_mesh(coarse_aligner)
                )
                # for coarse_anchor_mesh in coarse_anchor_meshes:
                # apply all_ancestors' rots and afterwards mesh rotation
                _apply_transforms(
                    mesh=coarse_anchor_mesh,
                    all_rotations=all_rotations,
                    all_positions=all_positions,
                )

                plotter.add_mesh(coarse_anchor_mesh, **coarse_anchor_mesh_dict)
            # interface aligners
            if (
                node._type == "interface_alignment"
                and node._type not in block_render
            ):
                interface_aligner = node

                ia_mesh, ia_mesh_dict = meshbuilder.ia_mesh(
                    interface_aligner_node=interface_aligner
                )

                _apply_transforms(
                    mesh=ia_mesh,
                    all_rotations=all_rotations,
                    all_positions=all_positions,
                )

                plotter.add_mesh(ia_mesh, **ia_mesh_dict)
            # fiber aligners
            if (
                node._type == "fiber_core_alignment"
                and node._type not in block_render
            ):
                fiber_aligner = node
                fa_mesh, fa_mesh_dict = meshbuilder.fa_mesh(fiber_aligner)

                _apply_transforms(
                    mesh=fa_mesh,
                    all_rotations=all_rotations,
                    all_positions=all_positions,
                )

                plotter.add_mesh(fa_mesh, **fa_mesh_dict)
            # Marker aligners
            if (
                node._type == "marker_alignment"
                and node._type not in block_render
            ):
                marker_aligner = node
                ma_meshes, ma_label_meshes, ma_mesh_dict, ma_label_dict = (
                    _meshbuilder.ma_mesh(marker_aligner)
                )

                for ma_mesh, ma_label_mesh in zip(ma_meshes, ma_label_meshes):

                    # apply all_ancestors' rots
                    _apply_transforms(
                        mesh=ma_mesh,
                        all_rotations=all_rotations,
                        all_positions=all_positions,
                    )
                    # apply all_ancestors' rots
                    _apply_transforms(
                        mesh=ma_label_mesh,
                        all_rotations=all_rotations,
                        all_positions=all_positions,
                    )

                    plotter.add_mesh(ma_mesh, **ma_mesh_dict)
                    plotter.add_mesh(ma_label_mesh, **ma_label_dict)

            #  Edge aligners
            if (
                node._type == "edge_alignment"
                and node._type not in block_render
            ):
                edge_aligner = node
                edge_aligner_meshes, edge_aligner_meshes_dicts = (
                    _meshbuilder.ea_mesh(edge_aligner)
                )

                for mesh, mesh_dict in zip(
                    edge_aligner_meshes, edge_aligner_meshes_dicts
                ):

                    _apply_transforms(
                        mesh,
                        all_positions=[edge_aligner.edge_location + [0]],
                        all_rotations=[
                            [0, 0, edge_aligner.edge_orientation]
                        ],  # (in-plane rotation only)
                    )

                    # apply all_ancestors' rots
                    _apply_transforms(
                        mesh,
                        all_rotations=all_rotations,
                        all_positions=all_positions,
                    )

                    plotter.add_mesh(mesh, **mesh_dict)

            # Dose compensation
            if (
                node._type == "dose_compensation"
                and node._type not in block_render
            ):
                dose_compensation = node

                for mesh, kwargs in _meshbuilder.dc_meshes(
                    dose_compensation.domain_size
                ):
                    _apply_transforms(
                        mesh=mesh,
                        all_rotations=all_rotations
                        + [[0, 0, dose_compensation.edge_orientation]],
                        all_positions=all_positions
                        + [dose_compensation.edge_location],
                    )

                    plotter.add_mesh(mesh, **kwargs)

            # Capture
            if node._type == "capture" and node._type not in block_render:
                capture = node

                capt_mesh, capt_mesh_dict = _meshbuilder.capture_mesh(capture)

                _apply_transforms(
                    mesh=capt_mesh,
                    all_rotations=all_rotations,
                    all_positions=all_positions,
                )

                plotter.add_mesh(capt_mesh, **capt_mesh_dict)

        # Disable visibility for certain groups if requested
        self._visibility_in_plotter_disabled = disable_visibility
        for grp in self._visibility_in_plotter_disabled:
            plotter.disable_visibility(grp)

        plotter._add_custom_axes()
        # Show the viewport
        plotter.show()

        return plotter

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
            # "geometry": self.geometry,
        }

        return node_dict
