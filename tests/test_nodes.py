import unittest
from npxpy.nodes.aligners import CoarseAligner
from npxpy.nodes.aligners import MarkerAligner
from npxpy.nodes.aligners import InterfaceAligner
from npxpy.nodes.misc import DoseCompensation
from npxpy.nodes.space import Scene
from npxpy.nodes.structures import Structure
from npxpy.nodes.project import Project
from npxpy.resources import Image, Mesh


# Test paths for resources
TEST_IMAGE_PATH = "test_resources/78eab7abd2cd201630ba30ed5a7ef4fc/markers.png"
TEST_MESH_PATH = (
    "test_resources/5416ba193f0bacf1e37be08d5c249914/combined_file.stl"
)


class TestNodeMethods(unittest.TestCase):
    def setUp(self):
        # Set up common resources for testing
        self.test_image = Image(file_path=TEST_IMAGE_PATH, name="Test Image")
        self.test_mesh = Mesh(file_path=TEST_MESH_PATH, name="Test Mesh")

    def test_add_child(self):
        # Test the add_child method across node types
        parent = CoarseAligner(name="Parent Node")
        child = MarkerAligner(name="Child Node", image=self.test_image)

        # Add child to parent
        parent.add_child(child)

        # Verify the child was added
        self.assertIn(child, parent.children_nodes)
        self.assertEqual(child.all_ancestors[0], parent)
        self.assertEqual(len(parent.children_nodes), 1)

        # Error handling: trying to add a non-Node child
        with self.assertRaises(TypeError):
            parent.add_child("Invalid Child")  # This should raise an error

    def test_remove_child(self):
        # Test the remove_child method
        parent = CoarseAligner(name="Parent Node")
        child = MarkerAligner(name="Child Node", image=self.test_image)

        # Add and then remove the child
        parent.add_child(child)
        parent.children_nodes.pop()

        # Verify the child was removed
        self.assertNotIn(child, parent.children_nodes)

    def test_translate(self):
        # Test the translate method (assuming InterfaceAligner should not have it)
        node = Scene(name="Test Scene")

        # Initial position should be [0, 0, 0]
        self.assertEqual(node.position, [0.0, 0.0, 0.0])

        # Translate the node
        node.translate([10.0, 5.0, 3.0])

        # Verify the position after translation
        self.assertEqual(node.position, [10.0, 5.0, 3.0])

    def test_position_at(self):
        # Test setting both position and rotation with position_at()
        node = Scene(name="Test Scene")

        # Set position and rotation
        node.position_at([20.0, 15.0, 5.0], [90.0, 45.0, 180.0])

        # Verify the new position and rotation
        self.assertEqual(node.position, [20.0, 15.0, 5.0])
        self.assertEqual(node.rotation, [90.0, 45.0, 180.0])

    def test_to_dict(self):
        # Test the to_dict method for node serialization
        node = MarkerAligner(name="Test MarkerAligner", image=self.test_image)
        node_dict = node.to_dict()

        # Check that required keys exist in the dictionary
        self.assertIn("name", node_dict)
        self.assertIn("position", node_dict)
        self.assertIn("rotation", node_dict)
        self.assertIn("id", node_dict)
        self.assertIn("children", node_dict)

    def test_all_descendants(self):
        # Test the all_descendants method to gather all child nodes
        root = Project(objective="25x", resin="IP-n162", substrate="FuSi")
        child1 = Scene(name="Child 1")
        grandchild1 = MarkerAligner(name="Grandchild 1", image=self.test_image)

        # Build hierarchy
        root.add_child(child1)
        child1.add_child(grandchild1)

        # Retrieve all descendants of the root node
        descendants = root.all_descendants

        # Verify that all descendants are present
        self.assertIn(child1, descendants)
        self.assertIn(grandchild1, descendants)
        self.assertEqual(len(descendants), 2)

    def test_all_ancestors(self):
        # Test the all_ancestors method to gather all ancestor nodes
        root = Project(objective="25x", resin="IP-n162", substrate="FuSi")
        child1 = Scene(name="Child 1")
        grandchild1 = MarkerAligner(name="Grandchild 1", image=self.test_image)

        # Build hierarchy
        root.add_child(child1)
        child1.add_child(grandchild1)

        # Retrieve all ancestors of grandchild1 node
        ancestors = grandchild1.all_ancestors

        # Verify that all ancestors are present
        self.assertIn(root, ancestors)
        self.assertIn(child1, ancestors)
        self.assertEqual(len(ancestors), 2)


if __name__ == "__main__":
    unittest.main()
