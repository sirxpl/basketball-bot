"""Deterministic tests for minigame rules."""
import unittest

from basketball.services.shooting import attempt_shot


class TestShooting(unittest.TestCase):
    def test_two_point_boundary(self):
        self.assertEqual(attempt_shot(2, 64).points, 2)
        self.assertEqual(attempt_shot(2, 65).points, 0)

    def test_three_point_boundary(self):
        self.assertEqual(attempt_shot(3, 34).points, 3)
        self.assertEqual(attempt_shot(3, 35).points, 0)

    def test_xp(self):
        self.assertEqual(attempt_shot(2, 0).xp, 5)
        self.assertEqual(attempt_shot(2, 99).xp, 1)

    def test_invalid_inputs(self):
        for shot, roll in [(1, 0), (4, 0), (2, -1), (3, 100)]:
            with self.subTest(shot=shot, roll=roll):
                with self.assertRaises(ValueError):
                    attempt_shot(shot, roll)


if __name__ == "__main__":
    unittest.main()
