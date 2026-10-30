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


class PlaybackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playback import create_player
        cls.player = create_player(30, 301)

    @classmethod
    def tearDownClass(cls):
        cls.player.close()

    def test_click_and_drag_seek(self):
        from PySide6.QtCore import QPoint, Qt
        from PySide6.QtTest import QTest

        player = self.player
        player.app.processEvents()
        slider = player.timeline
        for fraction, expected in ((0.75, 225), (0.25, 75), (0, 0), (1, 300)):
            position = QPoint(round((slider.width() - 1) * fraction), slider.height() // 2)
            QTest.mouseClick(slider, Qt.MouseButton.LeftButton, pos=position)
            self.assertLessEqual(abs(player.pending_seek - expected), 3)
        QTest.mousePress(slider, Qt.MouseButton.LeftButton, pos=QPoint(10, slider.height() // 2))
        QTest.mouseRelease(slider, Qt.MouseButton.LeftButton, pos=QPoint(slider.width() // 2, slider.height() // 2))
        self.assertLessEqual(abs(player.pending_seek - 150), 2)
        self.assertFalse(slider.isSliderDown())
        player.pending_seek = None

    def test_arrow_seeking(self):
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest

        player = self.player
        player.current_frame = 150
        for widget in (player, player.timeline, player.play):
            QTest.keyClick(widget, Qt.Key.Key_Left)
            self.assertEqual(player.pending_seek, 60)
            QTest.keyClick(widget, Qt.Key.Key_Right)
            self.assertEqual(player.pending_seek, 240)
        player.pending_seek = None
        player.fps_field.setText("30")
        player.fps_field.setCursorPosition(2)
        QTest.keyClick(player.fps_field, Qt.Key.Key_Left)
        self.assertEqual(player.fps_field.cursorPosition(), 1)
        self.assertIsNone(player.pending_seek)

    def test_controls(self):
        player = self.player
        player.play.click()
        self.assertTrue(player.paused)
        player.fps_field.setText("12")
        player.apply.click()
        self.assertEqual(player.playback_fps, 12)
        for value in ("nan", "0", "-1", "abc", "241"):
            player.fps_field.setText(value)
            player.apply.click()
            self.assertEqual(player.playback_fps, 12)
            self.assertTrue(player.error.text())
        player.current_frame = 150
        player.previous.click()
        self.assertEqual(player.next_action(), 60)
        player.following.click()
        self.assertEqual(player.next_action(), 240)
        player.timeline.setValue(299)
        self.assertEqual(player.next_action(), 299)
        self.assertTrue(player.paused)
        player.request_seek(-90)
        self.assertEqual(player.next_action(), 0)
        player.request_seek(999)
        self.assertEqual(player.next_action(), 300)
        player.ended = True
        player.play.click()
        self.assertFalse(player.paused)
        self.assertEqual(player.next_action(), 0)


if __name__ == "__main__":
    unittest.main()