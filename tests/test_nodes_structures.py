import unittest
from npxpy.nodes.structures import Structure, Text, Lens
from npxpy.preset import Preset
from npxpy.resources import Mesh
from npxpy.nodes.project import Project

# Define the test resource paths
TEST_MESH_PATH = (
    "test_resources/5416ba193f0bacf1e37be08d5c249914/combined_file.stl"
)
PRESETS_DIR = "./test_presets/"  # Path where test TOML presets are stored

# List of test presets
PRESET_FILES = [
    "25x_IP-n162_anchorage_FuSi.toml",
    "25x_IP-n162_speed.toml",
    "25x_IP-Visio.toml",
]


class TestStructureSubclasses(unittest.TestCase):
    def setUp(self):
        # Load the presets from the provided directory
        self.preset_anchorage = Preset.load_single(
            PRESETS_DIR + PRESET_FILES[0]
        )
        self.preset_speed = Preset.load_single(PRESETS_DIR + PRESET_FILES[1])
        self.preset_visio = Preset.load_single(PRESETS_DIR + PRESET_FILES[2])

        # Create dummy Mesh
        self.dummy_mesh = Mesh(TEST_MESH_PATH)

    def test_structure_project_configuration(self):
        # Project for "anchorage FuSi"
        project_anchorage = Project(
            objective="25x", resin="IP-n162", substrate="*"
        )
        structure = Structure(
            preset=self.preset_anchorage, mesh=self.dummy_mesh
        ).auto_load(project_anchorage)

        # Check that the project matches the preset's configuration
        self.assertEqual(project_anchorage.objective, "25x")
        self.assertIn("IP-n162", self.preset_anchorage.valid_resins)
        self.assertEqual(project_anchorage.substrate, "*")

    def test_speed_project_configuration(self):
        # Project for "speed"
        project_speed = Project(
            objective="25x", resin="IP-n162", substrate="*"
        )
        structure = Structure(
            preset=self.preset_speed, mesh=self.dummy_mesh
        ).auto_load(project_speed)

        # Check that the project matches the preset's configuration
        self.assertEqual(project_speed.objective, "25x")
        self.assertIn("IP-n162", self.preset_speed.valid_resins)
        self.assertEqual(project_speed.substrate, "*")

    def test_visio_project_configuration(self):
        # Project for "Visio"
        project_visio = Project(
            objective="25x", resin="IP-Visio", substrate="*"
        )
        structure = Structure(
            preset=self.preset_visio,
            mesh=self.dummy_mesh,
        ).auto_load(project_visio)

        # Check that the project matches the preset's configuration
        self.assertEqual(project_visio.objective, "25x")
        self.assertIn("IP-Visio", self.preset_visio.valid_resins)
        self.assertEqual(project_visio.substrate, "*")

    def test_text_project_configuration(self):
        # Text node configuration with preset "Visio"
        project_visio = Project(
            objective="25x", resin="IP-Visio", substrate="*"
        )
        text = Text(preset=self.preset_visio).auto_load(project_visio)

        # Check that the project matches the preset's configuration
        self.assertEqual(project_visio.objective, "25x")
        self.assertIn("IP-Visio", self.preset_visio.valid_resins)

    def test_lens_project_configuration(self):
        # Lens node configuration with preset "speed"
        project_speed = Project(
            objective="25x", resin="IP-n162", substrate="*"
        )
        lens = Lens(preset=self.preset_speed).auto_load(project_speed)

        # Check that the project matches the preset's configuration
        self.assertEqual(project_speed.objective, "25x")
        self.assertIn("IP-n162", self.preset_speed.valid_resins)

    # Further validation tests can be added to ensure the correctness of the mesh, size, and preset details


if __name__ == "__main__":
    unittest.main()
