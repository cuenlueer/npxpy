import unittest
from unittest.mock import patch
from npxpy.nodes.project import Project
from npxpy.resources import Image, Mesh
from npxpy.preset import Preset

# Define test resource paths
TEST_IMAGE_PATH = "test_resources/78eab7abd2cd201630ba30ed5a7ef4fc/markers.png"
TEST_MESH_PATH = (
    "test_resources/5416ba193f0bacf1e37be08d5c249914/combined_file.stl"
)


class TestProjectClass(unittest.TestCase):
    def setUp(self):
        # Set up dummy data for presets, image, and mesh
        self.preset_1 = Preset(
            name="Test Preset 1",
            valid_objectives=["25x"],
            valid_resins=["IP-n162"],
        )
        self.preset_2 = Preset(
            name="Test Preset 2",
            valid_objectives=["25x"],
            valid_resins=["IP-Visio"],
        )

        self.image = Image(file_path=TEST_IMAGE_PATH)
        self.mesh = Mesh(file_path=TEST_MESH_PATH)

    def test_project_initialization(self):
        # Create a valid project
        with patch("os.getlogin", return_value="test_user"):
            project = Project(objective="25x", resin="IP-n162", substrate="*")

        self.assertEqual(project.objective, "25x")
        self.assertEqual(project.resin, "IP-n162")
        self.assertEqual(project.substrate, "*")
        self.assertEqual(project.project_info["author"], "test_user")
        self.assertTrue("creation_date" in project.project_info)

    def test_invalid_objective(self):
        # Test for invalid objective value
        with self.assertRaises(ValueError):
            Project(objective="100x", resin="IP-n162", substrate="*")

    def test_invalid_resin(self):
        # Test for invalid resin value
        with self.assertRaises(ValueError):
            Project(objective="25x", resin="Unknown Resin", substrate="*")

    def test_invalid_substrate(self):
        # Test for invalid substrate value
        with self.assertRaises(ValueError):
            Project(
                objective="25x", resin="IP-n162", substrate="InvalidSubstrate"
            )

    def test_load_presets(self):
        # Create a valid project and load presets
        project = Project(objective="25x", resin="IP-n162", substrate="*")
        project.load_presets(self.preset_1)
        self.assertIn(self.preset_1, project.presets)

        # Test loading multiple presets
        project.load_presets([self.preset_1, self.preset_2])
        self.assertIn(self.preset_2, project.presets)

    def test_load_invalid_presets(self):
        # Create a valid project and test loading invalid presets
        project = Project(objective="25x", resin="IP-n162", substrate="*")
        with self.assertRaises(TypeError):
            project.load_presets("Invalid Preset")  # Not a Preset instance

    def test_load_image_and_mesh(self):
        # Create a valid project and load image and mesh resources
        project = Project(objective="25x", resin="IP-n162", substrate="*")
        project.load_resources(self.image)
        project.load_resources(self.mesh)

        self.assertIn(self.image, project.resources)
        self.assertIn(self.mesh, project.resources)

    def test_load_invalid_resources(self):
        # Create a valid project and test loading invalid resources
        project = Project(objective="25x", resin="IP-n162", substrate="*")
        with self.assertRaises(TypeError):
            project.load_resources(
                "Invalid Resource"
            )  # Not an Image or Mesh instance

    @patch("os.path.isfile", return_value=True)
    def test_nano_file_creation(self, mock_isfile):
        # Test the .nano file creation
        project = Project(objective="25x", resin="IP-n162", substrate="*")
        project.load_presets(self.preset_1)
        project.load_resources(self.image)

        # Mock resource file path and name for adding to zip
        project.nano(project_name="TestProject", path="./test_path")

        # Check that resource was written to the zip file
        self.assertTrue(mock_isfile.called)


if __name__ == "__main__":
    unittest.main()
