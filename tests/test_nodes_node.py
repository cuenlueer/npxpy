import unittest
from npxpy.nodes.node import Node


class TestNode(unittest.TestCase):
    def setUp(self):
        # Set up a basic node structure for testing
        self.parent = Node("project", "Parent")
        self.child1 = Node("scene", "Child 1")
        self.child2 = Node("scene", "Child 2")
        self.grandchild1 = Node("coarse_alignment", "Grandchild 1")
        self.structure_node = Node("structure", "Structure")

    def test_add_child(self):
        # Test adding a child node
        self.parent.add_child(self.child1)
        self.assertIn(self.child1, self.parent.children_nodes)

        # Test the child's parent relationship
        self.assertIn(self.parent, self.child1.parent_node)

        # Adding structure node as a child (this is fine)
        self.parent.add_child(self.structure_node)
        self.assertIn(self.structure_node, self.parent.children_nodes)

        # Error: Structure nodes cannot have children
        with self.assertRaises(ValueError):
            self.structure_node.add_child(self.grandchild1)

        # Error: Projects cannot be children
        new_project_node = Node("project", "New Project")
        with self.assertRaises(ValueError):
            self.child1.add_child(new_project_node)

        # Error: Prevent cyclic relationships
        self.parent.add_child(self.child1)
        with self.assertRaises(ValueError):
            self.child1.add_child(
                self.parent
            )  # This should raise a ValueError

    def test_remove_child(self):
        # Test adding and then removing a child node
        self.parent.add_child(self.child1)
        self.parent.children_nodes.remove(self.child1)
        self.assertNotIn(self.child1, self.parent.children_nodes)

    def test_all_descendants(self):
        # Test gathering all descendants
        self.parent.add_child(self.child1)
        self.child1.add_child(self.grandchild1)

        descendants = self.parent._generate_all_descendants()
        self.assertIn(self.child1, descendants)
        self.assertIn(self.grandchild1, descendants)
        self.assertEqual(len(descendants), 2)

    def test_all_ancestors(self):
        # Test gathering all ancestors
        self.parent.add_child(self.child1)
        self.child1.add_child(self.grandchild1)

        ancestors = self.grandchild1._generate_all_ancestors()
        self.assertIn(self.child1, ancestors)
        self.assertIn(self.parent, ancestors)
        self.assertEqual(len(ancestors), 2)

    def test_tree(self):
        # Test tree structure visualization
        self.parent.add_child(self.child1)
        self.child1.add_child(self.grandchild1)

        # This should print the tree structure
        self.parent.tree()

    def test_deepcopy_node(self):
        # Test deep copying of a node
        self.parent.add_child(self.child1)
        copied_node = self.parent.deepcopy_node()

        # Check that the copied node is not the same object but has the same structure
        self.assertNotEqual(copied_node.id, self.parent.id)
        self.assertEqual(
            len(copied_node.children_nodes), len(self.parent.children_nodes)
        )

        # Check deep copy of children
        for copied_child, original_child in zip(
            copied_node.children_nodes, self.parent.children_nodes
        ):
            self.assertNotEqual(copied_child.id, original_child.id)

    def test_grab_node(self):
        # Test grabbing a node by type and index
        self.parent.add_child(self.child1)
        self.child1.add_child(self.grandchild1)

        grabbed_node = self.parent.grab_node(
            ("scene", 0), ("coarse_alignment", 0)
        )
        self.assertEqual(grabbed_node, self.grandchild1)

    def test_grab_all_nodes_bfs(self):
        # Test breadth-first search for nodes of a specific type
        self.parent.add_child(self.child1)
        self.child1.add_child(self.grandchild1)

        nodes = self.parent.grab_all_nodes_bfs("scene")
        self.assertIn(self.child1, nodes)
        self.assertEqual(len(nodes), 1)

    def test_append_node(self):
        # Test appending a node to the deepest descendant
        self.parent.add_child(self.child1)
        self.child1.add_child(self.grandchild1)

        new_node = Node("coarse_alignment", "New Node")
        self.parent.append_node(new_node)

        # Check if the new node is added as the grandchild's child
        self.assertIn(new_node, self.grandchild1.children_nodes)

    def test_to_dict(self):
        # Test converting node to dictionary format
        self.parent.add_child(self.child1)
        node_dict = self.parent.to_dict()

        # Check that the dictionary contains the correct keys
        self.assertIn("type", node_dict)
        self.assertIn("id", node_dict)
        self.assertIn("name", node_dict)
        self.assertIn("position", node_dict)
        self.assertIn("rotation", node_dict)
        self.assertIn("children", node_dict)

    def test_invalid_name(self):
        # Test invalid name error
        with self.assertRaises(ValueError):
            invalid_node = Node("scene", "")

    def test_invalid_add_child_type(self):
        # Test error when adding a non-node as a child
        with self.assertRaises(TypeError):
            self.parent.add_child("Invalid Child")


if __name__ == "__main__":
    unittest.main()
