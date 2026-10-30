"""Native playback controls for annotated video frames."""

import math
import os
import time

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSlider,
    QStyle, QStyleOptionSlider, QVBoxLayout, QWidget,
)


class SeekSlider(QSlider):
    def __init__(self, orientation):
        super().__init__(orientation)
        option = QStyleOptionSlider()
        self.initStyleOption(option)
        groove = self.style().subControlRect(QStyle.ComplexControl.CC_Slider, option, QStyle.SubControl.SC_SliderGroove, self)
        self.setFixedHeight(self.sizeHint().height() * 5)
        self.setStyleSheet(
            f"QSlider::groove:horizontal {{ height: {groove.height() * 5}px; "
            "background: palette(mid); border-radius: 4px; }"
            "QSlider::sub-page:horizontal { background: palette(highlight); border-radius: 4px; }"
            "QSlider::handle:horizontal { width: 15px; background: palette(button); "
            "border: 1px solid palette(dark); border-radius: 4px; margin: -4px 0; }"
        )

    def set_mouse_position(self, event):
        option = QStyleOptionSlider()
        self.initStyleOption(option)
        groove = self.style().subControlRect(QStyle.ComplexControl.CC_Slider, option, QStyle.SubControl.SC_SliderGroove, self)
        handle = self.style().subControlRect(QStyle.ComplexControl.CC_Slider, option, QStyle.SubControl.SC_SliderHandle, self)
        span = max(1, groove.width() - handle.width())
        position = round(event.position().x() - groove.x() - handle.width() / 2)
        self.setValue(QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), position, span, option.upsideDown))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setSliderDown(True)
            self.set_mouse_position(event)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.isSliderDown():
            self.set_mouse_position(event)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.isSliderDown():
            self.set_mouse_position(event)
            self.setSliderDown(False)
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class PlaybackWindow(QWidget):
    def __init__(self, fps, frame_count, seeking=True, live=False):
        super().__init__()
        self.source_fps = fps
        self.live = live
        self.playback_fps = fps
        self.frame_count = max(1, frame_count)
        self.current_frame = 0
        self.pending_seek = None
        self.paused = False
        self.closed = False
        self.ended = False
        self.pixmap = None
        self.deadline = 0.0
        self.setWindowTitle("Gesture detection")
        self.resize(1100, 750)
        layout = QVBoxLayout(self)
        self.script_status = QLabel()
        self.script_status.setWordWrap(True)
        self.script_status.hide()
        layout.addWidget(self.script_status)
        self.image = QLabel()
        self.image.setMinimumSize(320, 180)
        self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        from PySide6.QtWidgets import QSizePolicy
        self.image.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        layout.addWidget(self.image, 1)
        self.timeline = SeekSlider(Qt.Orientation.Horizontal)
        self.timeline.setRange(0, self.frame_count - 1)
        self.timeline.setEnabled(seeking)
        self.timeline.setVisible(not live)
        self.timeline.sliderReleased.connect(lambda: self.request_seek(self.timeline.value()))
        self.timeline.valueChanged.connect(self.timeline_changed)
        layout.addWidget(self.timeline)
        controls = QHBoxLayout()
        layout.addLayout(controls)
        self.previous = QPushButton("-3 s")
        self.previous.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSeekBackward))
        self.previous.setToolTip("Seek backward three seconds")
        self.previous.setEnabled(seeking)
        self.previous.setVisible(not live)
        self.previous.clicked.connect(lambda: self.request_seek(self.current_frame - round(3 * fps)))
        controls.addWidget(self.previous)
        self.play = QPushButton()
        self.play.clicked.connect(self.toggle)
        controls.addWidget(self.play)
        self.following = QPushButton("+3 s")
        self.following.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSeekForward))
        self.following.setToolTip("Seek forward three seconds")
        self.following.setEnabled(seeking)
        self.following.setVisible(not live)
        self.following.clicked.connect(lambda: self.request_seek(self.current_frame + round(3 * fps)))
        controls.addWidget(self.following)
        controls.addSpacing(12)
        controls.addWidget(QLabel("FPS"))
        self.fps_field = QLineEdit(f"{fps:.3f}".rstrip("0").rstrip("."))
        self.fps_field.setFixedWidth(85)
        self.fps_field.returnPressed.connect(self.apply_fps)
        controls.addWidget(self.fps_field)
        self.apply = QPushButton("Apply")
        self.apply.clicked.connect(self.apply_fps)
        controls.addWidget(self.apply)
        self.error = QLabel()
        controls.addWidget(self.error)
        controls.addStretch()
        self.clock = QLabel()
        controls.addWidget(self.clock)
        if not seeking:
            self.timeline.setToolTip("Seeking is disabled while saving output")
        self.update_play_button()
        for widget in [self, *self.findChildren(QWidget)]:
            widget.installEventFilter(self)

    def eventFilter(self, watched, event):
        if (event.type() == QEvent.Type.KeyPress
                and event.modifiers() == Qt.KeyboardModifier.NoModifier
                and not isinstance(watched, QLineEdit)):
            if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right):
                button = self.previous if event.key() == Qt.Key.Key_Left else self.following
                button.click()
                return True
        return super().eventFilter(watched, event)

    def update_play_button(self):
        icon = QStyle.StandardPixmap.SP_MediaPlay if self.paused else QStyle.StandardPixmap.SP_MediaPause
        self.play.setIcon(self.style().standardIcon(icon))
        self.play.setToolTip("Play" if self.paused else "Pause")

    def toggle(self):
        if self.ended and self.timeline.isEnabled():
            self.request_seek(0)
        self.paused = not self.paused
        self.deadline = 0.0
        self.update_play_button()

    def apply_fps(self):
        try:
            value = float(self.fps_field.text())
            if not math.isfinite(value) or not 0 < value <= 240:
                raise ValueError
        except ValueError:
            self.error.setText("FPS must be > 0 and <= 240")
            return
        self.playback_fps = value
        self.deadline = 0.0
        self.error.clear()

    def timeline_changed(self, value):
        if not self.timeline.isSliderDown():
            self.request_seek(value)

    def request_seek(self, frame):
        self.pending_seek = max(0, min(self.frame_count - 1, frame))
        self.ended = False
        self.deadline = 0.0

    def next_action(self):
        app = QApplication.instance()
        while not self.closed:
            app.processEvents()
            if self.pending_seek is not None:
                target = self.pending_seek
                self.pending_seek = None
                return target
            if not self.paused and not self.timeline.isSliderDown() and time.monotonic() >= self.deadline:
                self.deadline = time.monotonic() + 1 / self.playback_fps
                return -1
            from PySide6.QtCore import QThread
            QThread.msleep(5)
        return None

    def display(self, frame, frame_index):
        height, width = frame.shape[:2]
        image = QImage(frame.data, width, height, frame.strides[0], QImage.Format.Format_BGR888).copy()
        self.pixmap = QPixmap.fromImage(image)
        self.update_image()
        self.current_frame = frame_index
        if not self.timeline.isSliderDown():
            self.timeline.blockSignals(True)
            self.timeline.setValue(frame_index)
            self.timeline.blockSignals(False)
        self.clock.setText("Live" if self.live else f"{frame_index / self.source_fps:.1f} / {self.frame_count / self.source_fps:.1f} s")
        QApplication.instance().processEvents()

    def update_image(self):
        if self.pixmap is not None:
            self.image.setPixmap(self.pixmap.scaled(self.image.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                                   Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_image()

    def closeEvent(self, event):
        self.closed = True
        super().closeEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Q):
            self.close()
        elif event.key() == Qt.Key.Key_Space:
            self.toggle()
        else:
            super().keyPressEvent(event)


def create_player(fps, frame_count, seeking=True, live=False):
    for key in ("QT_QPA_PLATFORM_PLUGIN_PATH", "QT_QPA_FONTDIR"):
        if "cv2" in os.environ.get(key, ""):
            os.environ.pop(key)
    app = QApplication.instance() or QApplication([])
    player = PlaybackWindow(fps, frame_count, seeking, live)
    player.app = app
    player.show()
    return player