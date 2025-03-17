import unittest
from npxpy.resources import Image
from npxpy.nodes.aligners import CoarseAligner
from npxpy.nodes.aligners import InterfaceAligner
from npxpy.nodes.aligners import FiberAligner
from npxpy.nodes.aligners import MarkerAligner
from npxpy.nodes.aligners import EdgeAligner

# Define test resource paths
TEST_IMAGE_PATH = "test_resources/78eab7abd2cd201630ba30ed5a7ef4fc/markers.png"


class TestAligners(unittest.TestCase):
    def setUp(self):
        self.image = Image(file_path=TEST_IMAGE_PATH)

    def test_coarse_aligner_initialization(self):
        coarse_aligner = CoarseAligner(residual_threshold=5.0)
        self.assertEqual(coarse_aligner.residual_threshold, 5.0)
        with self.assertRaises(ValueError):
            CoarseAligner(residual_threshold=-1)  # Invalid threshold

        # Test adding coarse anchors
        coarse_aligner.add_coarse_anchor([0, 0, 0], "Anchor 1")
        self.assertEqual(len(coarse_aligner.alignment_anchors), 1)

    def test_interface_aligner_initialization(self):
        interface_aligner = InterfaceAligner(
            signal_type="reflection", detector_type="camera"
        )
        self.assertEqual(interface_aligner.signal_type, "reflection")
        self.assertEqual(interface_aligner.detector_type, "camera")

        # Test grid setting
        interface_aligner.set_grid([5, 5], [100.0, 100.0])
        self.assertEqual(interface_aligner.count, [5, 5])
        self.assertEqual(interface_aligner.size, [100.0, 100.0])

    def test_fiber_aligner_initialization(self):
        fiber_aligner = FiberAligner(
            fiber_radius=63.5, core_signal_lower_threshold=0.05
        )
        self.assertEqual(fiber_aligner.fiber_radius, 63.5)
        self.assertEqual(fiber_aligner.core_signal_lower_threshold, 0.05)

        with self.assertRaises(ValueError):
            FiberAligner(fiber_radius=-5)  # Invalid fiber radius

    def test_marker_aligner_initialization(self):
        marker_aligner = MarkerAligner(
            image=self.image, marker_size=[10.0, 10.0]
        )
        self.assertEqual(marker_aligner.marker_size, [10.0, 10.0])
        self.assertEqual(
            marker_aligner.image.safe_path,
            "resources/" + TEST_IMAGE_PATH.split("/")[1] + "/markers.png",
        )

        # Test marker addition
        marker_aligner.add_marker([0, 0, 0], 90.0, "Marker 1")
        self.assertEqual(len(marker_aligner.alignment_anchors), 1)

    def test_edge_aligner_initialization(self):
        edge_aligner = EdgeAligner(
            edge_location=[0.0, 0.0], edge_orientation=45.0
        )
        self.assertEqual(edge_aligner.edge_location, [0.0, 0.0])
        self.assertEqual(edge_aligner.edge_orientation, 45.0)

        # Test measurement addition
        edge_aligner.add_measurement(
            0.1,
            [50.0, 50.0],
            "Edge 1",
        )
        self.assertEqual(len(edge_aligner.alignment_anchors), 1)

    def test_to_dict_methods(self):
        # Ensure the to_dict method generates proper output
        coarse_aligner = CoarseAligner(residual_threshold=10.0)
        self.assertIn("residual_threshold", coarse_aligner.to_dict())

        interface_aligner = InterfaceAligner()
        self.assertIn(
            "detector_type", interface_aligner.to_dict()["properties"]
        )

        fiber_aligner = FiberAligner()
        self.assertIn("fiber_radius", fiber_aligner.to_dict())

        marker_aligner = MarkerAligner(image=self.image)
        self.assertIn("marker", marker_aligner.to_dict())

        edge_aligner = EdgeAligner()
        self.assertNotIn("edge_location", edge_aligner.to_dict())
        self.assertEqual(
            edge_aligner.edge_location,
            edge_aligner.to_dict()["xy_position_local_cos"],
        )


if __name__ == "__main__":
    unittest.main()
