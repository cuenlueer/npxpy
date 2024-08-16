import unittest
from npxpy.nodes.space import Scene
from npxpy.nodes.space import Group
from npxpy.nodes.space import Array


class TestNodeSubclasses(unittest.TestCase):
    # Test Scene class
    def test_scene_initialization(self):
        scene = Scene(name="TestScene")
        self.assertEqual(scene.name, "TestScene")
        self.assertEqual(scene.position, [0, 0, 0])
        self.assertEqual(scene.rotation, [0.0, 0.0, 0.0])
        self.assertTrue(scene.writing_direction_upward)

    def test_scene_position_rotation_setters(self):
        scene = Scene()
        # Valid position and rotation
        scene.position = [10.0, 20.0, 30.0]
        scene.rotation = [45.0, 90.0, 180.0]
        self.assertEqual(scene.position, [10.0, 20.0, 30.0])
        self.assertEqual(scene.rotation, [45.0, 90.0, 180.0])

        # Invalid position (not a list of 3)
        with self.assertRaises(ValueError):
            scene.position = [10.0, 20.0]  # Length mismatch
        with self.assertRaises(ValueError):
            scene.position = "invalid"  # Wrong type

        # Invalid rotation (not a list of 3)
        with self.assertRaises(ValueError):
            scene.rotation = [45.0]  # Length mismatch

    def test_scene_translate_rotate(self):
        scene = Scene()
        scene.translate([5.0, 10.0, 15.0])
        self.assertEqual(scene.position, [5.0, 10.0, 15.0])

        scene.rotate([90.0, 45.0, 30.0])
        self.assertEqual(scene.rotation, [90.0, 45.0, 30.0])

        # Invalid translation/rotation
        with self.assertRaises(ValueError):
            scene.translate([1.0, 2.0])  # Length mismatch
        with self.assertRaises(ValueError):
            scene.rotate("invalid")  # Wrong type

    # Test Group class
    def test_group_initialization(self):
        group = Group(name="TestGroup")
        self.assertEqual(group.name, "TestGroup")
        self.assertEqual(group.position, [0, 0, 0])
        self.assertEqual(group.rotation, [0.0, 0.0, 0.0])

    def test_group_translate_rotate(self):
        group = Group()
        group.translate([5.0, 5.0, 5.0])
        self.assertEqual(group.position, [5.0, 5.0, 5.0])

        group.rotate([30.0, 60.0, 90.0])
        self.assertEqual(group.rotation, [30.0, 60.0, 90.0])

    # Test Array class
    def test_array_initialization(self):
        array = Array(name="TestArray")
        self.assertEqual(array.name, "TestArray")
        self.assertEqual(array.position, [0, 0, 0])
        self.assertEqual(array.rotation, [0.0, 0.0, 0.0])
        self.assertEqual(array.count, [5, 5])
        self.assertEqual(array.spacing, [100.0, 100.0])
        self.assertEqual(array.order, "Lexical")
        self.assertEqual(array.shape, "Rectangular")

    def test_array_grid_settings(self):
        array = Array()
        array.set_grid([10, 10], [50.0, 50.0])
        self.assertEqual(array.count, [10, 10])
        self.assertEqual(array.spacing, [50.0, 50.0])

        # Invalid count and spacing
        with self.assertRaises(ValueError):
            array.set_grid([10, -5], [50.0, 50.0])  # Negative count
        with self.assertRaises(ValueError):
            array.set_grid([5, 5], [50.0])  # Length mismatch

    def test_array_translate_rotate(self):
        array = Array()
        array.translate([3.0, 3.0, 3.0])
        self.assertEqual(array.position, [3.0, 3.0, 3.0])

        array.rotate([45.0, 90.0, 135.0])
        self.assertEqual(array.rotation, [45.0, 90.0, 135.0])

    def test_array_invalid_settings(self):
        array = Array()
        with self.assertRaises(ValueError):
            array.order = "InvalidOrder"
        with self.assertRaises(ValueError):
            array.shape = "InvalidShape"

    def test_array_position_rotation_setters(self):
        array = Array()
        array.position = [1.0, 2.0, 3.0]
        self.assertEqual(array.position, [1.0, 2.0, 3.0])

        array.rotation = [45.0, 90.0, 180.0]
        self.assertEqual(array.rotation, [45.0, 90.0, 180.0])

        # Invalid position/rotation
        with self.assertRaises(ValueError):
            array.position = [1.0, 2.0]  # Length mismatch
        with self.assertRaises(ValueError):
            array.rotation = [45.0, 90.0]  # Length mismatch


if __name__ == "__main__":
    unittest.main()
