# -*- coding: utf-8 -*-
"""
Created on Wed Aug  7 12:52:28 2024

@author: CU
"""
import unittest
from unittest.mock import patch, mock_open
from npxpy.preset import Preset


class TestPreset(unittest.TestCase):

    def setUp(self):
        self.preset = Preset()

    def test_default_initialization(self):
        self.assertEqual(self.preset.name, "25x_IP-n162_default")
        self.assertEqual(self.preset.valid_objectives, ["25x"])
        self.assertEqual(self.preset.valid_resins, ["IP-n162"])
        self.assertEqual(self.preset.valid_substrates, ["*"])
        self.assertEqual(self.preset.writing_speed, 250000.0)
        self.assertEqual(self.preset.writing_power, 50.0)
        self.assertEqual(self.preset.slicing_spacing, 0.8)
        self.assertEqual(self.preset.hatching_spacing, 0.3)
        self.assertEqual(self.preset.hatching_angle, 0.0)
        self.assertEqual(self.preset.hatching_angle_increment, 0.0)
        self.assertEqual(self.preset.hatching_offset, 0.0)
        self.assertEqual(self.preset.hatching_offset_increment, 0.0)
        self.assertTrue(self.preset.hatching_back_n_forth)
        self.assertEqual(self.preset.mesh_z_offset, 0.0)
        self.assertFalse(self.preset.grayscale_multilayer_enabled)
        self.assertEqual(self.preset.grayscale_layer_profile_nr_layers, 6)
        self.assertEqual(self.preset.grayscale_writing_power_minimum, 0.0)
        self.assertEqual(self.preset.grayscale_exponent, 1.0)

    def test_validate_values(self):
        with self.assertRaises(ValueError):
            Preset(valid_objectives=["invalid_objective"])

        with self.assertRaises(ValueError):
            Preset(valid_resins=["invalid_resin"])

        with self.assertRaises(ValueError):
            Preset(valid_substrates=["invalid_substrate"])

    def test_set_grayscale_multilayer(self):
        self.preset.set_grayscale_multilayer(10, 1.0, 2.0)
        self.assertTrue(self.preset.grayscale_multilayer_enabled)
        self.assertEqual(self.preset.grayscale_layer_profile_nr_layers, 10)
        self.assertEqual(self.preset.grayscale_writing_power_minimum, 1.0)
        self.assertEqual(self.preset.grayscale_exponent, 2.0)

        with self.assertRaises(ValueError):
            self.preset.set_grayscale_multilayer(-1, 1.0, 2.0)

        with self.assertRaises(ValueError):
            self.preset.set_grayscale_multilayer(10, -1.0, 2.0)

        with self.assertRaises(ValueError):
            self.preset.set_grayscale_multilayer(10, 1.0, -2.0)

    def test_duplicate(self):
        duplicate_preset = self.preset.duplicate()
        self.assertNotEqual(self.preset.id, duplicate_preset.id)
        self.assertEqual(self.preset.name, duplicate_preset.name)
        self.assertEqual(
            self.preset.writing_speed, duplicate_preset.writing_speed
        )

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='name = "25x_IP-Visio"',
    )
    @patch("os.path.isfile", return_value=True)
    def test_load_single(self, mock_isfile, mock_open_file):
        test_toml_data = {
            "name": "25x_IP-Visio",
            "valid_objectives": ["25x"],
            "valid_resins": ["IP-n162"],
            "valid_substrates": ["*"],
            "writing_speed": 250000.0,
            "writing_power": 50.0,
            "slicing_spacing": 0.8,
            "hatching_spacing": 0.3,
            "hatching_angle": 0.0,
            "hatching_angle_increment": 0.0,
            "hatching_offset": 0.0,
            "hatching_offset_increment": 0.0,
            "hatching_back_n_forth": True,
            "mesh_z_offset": 0.0,
            "grayscale_multilayer_enabled": False,
            "grayscale_layer_profile_nr_layers": 6,
            "grayscale_writing_power_minimum": 0.0,
            "grayscale_exponent": 1.0,
        }
        with patch("pytomlpp.load", return_value=test_toml_data):
            preset = Preset.load_single(
                "presets/25x_IP-Visio.toml", fresh_id=True
            )
            self.assertEqual(preset.name, "25x_IP-Visio")

    @patch("os.path.isdir", return_value=True)
    @patch(
        "os.listdir",
        return_value=[
            "25x_IP-n162_anchorage_FuSi.toml",
            "25x_IP-n162_speed.toml",
            "25x_IP-Visio.toml",
        ],
    )
    @patch.object(
        Preset,
        "load_single",
        side_effect=["test", "25x_IP-n162_speed", "25x_IP-Visio"],
    )
    def test_load_multiple(self, mock_load_single, mock_listdir, mock_isdir):
        presets = Preset.load_multiple("presets", print_names=True)
        self.assertEqual(len(presets), 3)
        self.assertEqual(presets[0], "test")
        self.assertEqual(presets[1], "25x_IP-n162_speed")
        self.assertEqual(presets[2], "25x_IP-Visio")

    @patch("builtins.open", new_callable=mock_open)
    def test_export(self, mock_open_file):
        file_path = "preset_export.toml"
        self.preset.export(file_path)
        mock_open_file.assert_called_once_with(file_path, "w")
        handle = mock_open_file()
        handle.write.assert_called_once()


if __name__ == "__main__":
    unittest.main()
