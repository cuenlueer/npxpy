import unittest
from npxpy.nodes.misc import DoseCompensation
from npxpy.nodes.misc import Capture
from npxpy.nodes.misc import StageMove
from npxpy.nodes.misc import Wait


class TestNewNodeSubclasses(unittest.TestCase):
    # Test DoseCompensation class
    def test_dose_compensation_initialization(self):
        dose_comp = DoseCompensation()
        self.assertEqual(dose_comp.name, "Dose compensation 1")
        self.assertEqual(dose_comp.edge_location, [0.0, 0.0, 0.0])
        self.assertEqual(dose_comp.edge_orientation, 0.0)
        self.assertEqual(dose_comp.domain_size, [200.0, 100.0, 100.0])
        self.assertEqual(dose_comp.gain_limit, 2.0)

    def test_dose_compensation_edge_location_setter(self):
        dose_comp = DoseCompensation()
        dose_comp.edge_location = [10.0, 20.0, 30.0]
        self.assertEqual(dose_comp.edge_location, [10.0, 20.0, 30.0])

        with self.assertRaises(TypeError):
            dose_comp.edge_location = [10.0, 20.0]  # Length mismatch
        with self.assertRaises(TypeError):
            dose_comp.edge_location = ["x", 20.0, 30.0]  # Invalid type

    def test_dose_compensation_domain_size_setter(self):
        dose_comp = DoseCompensation()
        dose_comp.domain_size = [150.0, 200.0, 300.0]
        self.assertEqual(dose_comp.domain_size, [150.0, 200.0, 300.0])

        with self.assertRaises(ValueError):
            dose_comp.domain_size = [150.0, -200.0, 300.0]  # Negative value
        with self.assertRaises(TypeError):
            dose_comp.domain_size = [150.0]  # Length mismatch

    def test_dose_compensation_gain_limit_setter(self):
        dose_comp = DoseCompensation()
        dose_comp.gain_limit = 3.0
        self.assertEqual(dose_comp.gain_limit, 3.0)

        with self.assertRaises(ValueError):
            dose_comp.gain_limit = 0.5  # Below 1.0

    # Test Capture class
    def test_capture_initialization(self):
        capture = Capture()
        self.assertEqual(capture.name, "Capture")
        self.assertEqual(capture.capture_type, "Camera")
        self.assertEqual(capture.laser_power, 0.5)
        self.assertEqual(capture.scan_area_size, [100.0, 100.0])
        self.assertEqual(capture.scan_area_res_factors, [1.0, 1.0])

    def test_capture_laser_power_setter(self):
        capture = Capture()
        capture.laser_power = 1.5
        self.assertEqual(capture.laser_power, 1.5)

        with self.assertRaises(ValueError):
            capture.laser_power = -1.0  # Negative value not allowed

    def test_capture_scan_area_size_setter(self):
        capture = Capture()
        capture.scan_area_size = [200.0, 150.0]
        self.assertEqual(capture.scan_area_size, [200.0, 150.0])

        with self.assertRaises(TypeError):
            capture.scan_area_size = [200.0]  # Length mismatch
        with self.assertRaises(ValueError):
            capture.scan_area_size = [200.0, -150.0]  # Negative size

    def test_capture_confocal_method(self):
        capture = Capture()
        capture.confocal(
            laser_power=2.0,
            scan_area_size=[250.0, 250.0],
            scan_area_res_factors=[2.0, 2.0],
        )
        self.assertEqual(capture.laser_power, 2.0)
        self.assertEqual(capture.scan_area_size, [250.0, 250.0])
        self.assertEqual(capture.scan_area_res_factors, [2.0, 2.0])
        self.assertEqual(capture.capture_type, "Confocal")

    # Test StageMove class
    def test_stage_move_initialization(self):
        stage_move = StageMove()
        self.assertEqual(stage_move.name, "Stage move")
        self.assertEqual(stage_move.stage_position, [0.0, 0.0, 0.0])

    def test_stage_move_position_setter(self):
        stage_move = StageMove()
        stage_move.stage_position = [10.0, 20.0, 30.0]
        self.assertEqual(stage_move.stage_position, [10.0, 20.0, 30.0])

        with self.assertRaises(TypeError):
            stage_move.stage_position = [10.0, 20.0]  # Length mismatch
        with self.assertRaises(TypeError):
            stage_move.stage_position = ["x", 20.0, 30.0]  # Invalid type

    # Test Wait class
    def test_wait_initialization(self):
        wait = Wait()
        self.assertEqual(wait.name, "Wait")
        self.assertEqual(wait.wait_time, 1.0)

    def test_wait_time_setter(self):
        wait = Wait()
        wait.wait_time = 2.5
        self.assertEqual(wait.wait_time, 2.5)

        with self.assertRaises(ValueError):
            wait.wait_time = 0  # Zero or negative time not allowed
        with self.assertRaises(ValueError):
            wait.wait_time = -5.0  # Negative time not allowed


if __name__ == "__main__":
    unittest.main()
