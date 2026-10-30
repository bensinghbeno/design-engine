import unittest

from detect_gestures import GestureState, classify_pose, parse_roi


class GestureTests(unittest.TestCase):
    def pose(self):
        points = [[100.0, 100.0, 1.0] for _ in range(17)]
        for index, position in {5: (80, 100), 6: (120, 100), 9: (70, 180), 10: (130, 180),
                                11: (80, 200), 12: (120, 200), 13: (80, 270), 14: (120, 270),
                                15: (80, 350), 16: (120, 350)}.items():
            points[index][:2] = position
        return points

    def test_arm_labels_and_missing_wrist(self):
        points = self.pose()
        self.assertEqual(classify_pose(points)[0], set())
        points[9][1] = 50
        self.assertEqual(classify_pose(points)[0], {"Left Hand Up"})
        points[10][1] = 50
        self.assertEqual(classify_pose(points)[0], {"Both Hands Up"})
        points[9][2] = 0
        self.assertEqual(classify_pose(points)[0], {"Right Hand Up"})

    def test_leg_raise(self):
        points = self.pose()
        points[13][1] = 220
        points[15][1] = 260
        self.assertEqual(classify_pose(points)[0], {"Left Leg Up"})

    def test_missing_torso(self):
        points = self.pose()
        points[5][2] = 0
        self.assertEqual(classify_pose(points), (set(), "Unknown"))

    def test_hold_and_release(self):
        state = GestureState()
        self.assertEqual(state.update({"Both Hands Up"}, "Unknown", 0, .4, .15), set())
        self.assertEqual(state.update({"Both Hands Up"}, "Unknown", .5, .4, .15), {"Both Hands Up"})
        self.assertEqual(state.update(set(), "Unknown", .7, .4, .15), set())

    def test_no_turn_from_missing_face(self):
        state = GestureState()
        for timestamp in (0, .5, 1):
            self.assertEqual(state.update(set(), "Unknown", timestamp, .4, .15, True), set())

    def test_polygon(self):
        self.assertEqual(parse_roi("0,0;100,0;100,100"), [(0, 0), (100, 0), (100, 100)])


if __name__ == "__main__":
    unittest.main()