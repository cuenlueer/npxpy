import unittest
from unittest.mock import patch, mock_open
import uuid
import os
import hashlib
from npxpy.resources import Resource, Image, Mesh


# Paths to test resources
TEST_IMAGE_PATH = "test_resources/78eab7abd2cd201630ba30ed5a7ef4fc/markers.png"
TEST_MESH_PATH = (
    "test_resources/5416ba193f0bacf1e37be08d5c249914/combined_file.stl"
)


class TestResource(unittest.TestCase):
    def setUp(self):
        self.resource_type = "test_type"
        self.name = "test_name"
        self.path = TEST_IMAGE_PATH
        self.resource = Resource(self.resource_type, self.name, self.path)

    def test_init(self):
        self.assertEqual(self.resource._type, self.resource_type)
        self.assertEqual(self.resource.name, self.name)
        self.assertEqual(self.resource.file_path, self.path)
        self.assertTrue(uuid.UUID(self.resource.id))

    def test_init_empty_name(self):
        with self.assertRaises(ValueError):
            Resource(self.resource_type, "", self.path)

    def test_generate_path(self):
        with open(TEST_IMAGE_PATH, "rb") as f:
            file_content = f.read()
        file_hash = hashlib.md5(file_content).hexdigest()
        expected_path = f"resources/{file_hash}/{os.path.basename(self.path)}"

        with patch("builtins.open", mock_open(read_data=file_content)), patch(
            "os.path.isfile", return_value=True
        ):
            self.assertEqual(
                self.resource.generate_safe_path(self.path), expected_path
            )

    def test_generate_path_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.resource.generate_safe_path("nonexistent_path.txt")

    def test_to_dict(self):
        expected_dict = {
            "type": self.resource_type,
            "id": self.resource.id,
            "name": self.name,
            "path": self.resource.safe_path,
        }
        self.assertEqual(self.resource.to_dict(), expected_dict)


class TestImage(unittest.TestCase):
    def setUp(self):
        self.path = TEST_IMAGE_PATH
        self.image = Image(self.path)

    def test_init(self):
        self.assertEqual(self.image._type, "image_file")
        self.assertEqual(self.image.name, "image")
        self.assertEqual(self.image.file_path, self.path)

    def test_init_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            Image("nonexistent_image.jpg")


class TestMesh(unittest.TestCase):
    def setUp(self):
        self.path = TEST_MESH_PATH
        self.name = "test_mesh"
        self.translation = [0, 0, 0]
        self.auto_center = False
        self.rotation = [0.0, 0.0, 0.0]
        self.scale = [1.0, 1.0, 1.0]
        self.enhance_mesh = True
        self.simplify_mesh = False
        self.target_ratio = 100.0
        self.mesh = Mesh(
            self.path,
            self.name,
            self.translation,
            self.auto_center,
            self.rotation,
            self.scale,
            self.enhance_mesh,
            self.simplify_mesh,
            self.target_ratio,
        )

    @patch("os.path.isfile", return_value=True)
    @patch("stl.mesh.Mesh.from_file")
    def test_init(self, mock_from_file, mock_isfile):
        self.assertEqual(self.mesh._type, "mesh_file")
        self.assertEqual(self.mesh.name, self.name)
        self.assertEqual(self.mesh.file_path, self.path)
        self.assertEqual(self.mesh.translation, self.translation)
        self.assertEqual(self.mesh.auto_center, self.auto_center)
        self.assertEqual(self.mesh.rotation, self.rotation)
        self.assertEqual(self.mesh.scale, self.scale)
        self.assertEqual(self.mesh.enhance_mesh, self.enhance_mesh)
        self.assertEqual(self.mesh.simplify_mesh, self.simplify_mesh)
        self.assertEqual(self.mesh.target_ratio, self.target_ratio)

    def test_init_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            Mesh("nonexistent_mesh.stl")

    @patch("os.path.isfile", return_value=True)
    @patch("stl.mesh.Mesh.from_file")
    def test_get_triangle_count(self, mock_from_file, mock_isfile):
        mock_mesh = mock_from_file.return_value
        mock_mesh.vectors = [1, 2, 3]
        self.assertEqual(self.mesh._get_triangle_count(self.path), 3)

    @patch("os.path.isfile", return_value=True)
    @patch(
        "stl.mesh.Mesh.from_file",
        side_effect=Exception("Error reading STL file"),
    )
    def test_get_triangle_count_exception(self, mock_from_file, mock_isfile):
        with self.assertRaises(Exception):
            self.mesh._get_triangle_count(self.path)

    def test_to_dict(self):
        resource_dict = self.mesh.to_dict()
        self.assertIn("properties", resource_dict)
        self.assertIn("original_triangle_count", resource_dict["properties"])


if __name__ == "__main__":
    unittest.main()
