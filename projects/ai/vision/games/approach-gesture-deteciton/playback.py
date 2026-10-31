"""Native playback controls for annotated video frames."""

import math
import os
import time
import random
import subprocess
from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor
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
        self.gesture_pixmap = None
        self.intro_image = None
        self.score_entries = None
        self.score_cache = None
        self.current_gesture = None
        self.deadline = 0.0
        self.session_writer = None
        self.session_audio = None
        self.recording_error = None
        self.recording_frames = 0
        self.gameplay_visible = False
        self.recording_timer = QTimer(self)
        self.recording_timer.timeout.connect(self.record_presentation)
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
        self.gesture_image = QLabel()
        self.gesture_image.setMinimumSize(0, 0)
        self.gesture_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gesture_image.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.gesture_image.hide()
        self.image_layout = QHBoxLayout()
        self.image_layout.setSpacing(0)
        self.image_layout.addWidget(self.image, 3)
        self.image_layout.addWidget(self.gesture_image, 1)
        layout.addLayout(self.image_layout, 1)
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
            if self.recording_error is not None:
                raise RuntimeError(f"Session recording failed: {self.recording_error}")
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

    def start_recording(self, writer, audio, width, height, fps):
        self.session_writer = writer
        self.session_audio = audio
        self.recording_size = (width, height)
        self.record_presentation()
        self.recording_timer.start(max(1, round(1000 / fps)))

    def record_presentation(self):
        if self.session_writer is None or self.closed or self.recording_error is not None:
            return
        try:
            import cv2
            import numpy as np
            timestamp = time.monotonic()
            image = self.grab().toImage().convertToFormat(QImage.Format.Format_RGB888)
            pixels = np.frombuffer(image.bits(), dtype=np.uint8).reshape(image.height(), image.bytesPerLine())
            rgb = pixels[:, :image.width() * 3].reshape(image.height(), image.width(), 3)
            width, height = self.recording_size
            scale = min(width / image.width(), height / image.height())
            resized = cv2.resize(rgb, (max(1, round(image.width() * scale)), max(1, round(image.height() * scale))))
            canvas = np.zeros((height, width, 3), dtype=np.uint8)
            top, left = (height - resized.shape[0]) // 2, (width - resized.shape[1]) // 2
            canvas[top:top + resized.shape[0], left:left + resized.shape[1]] = resized
            if self.session_audio.started is None:
                self.session_audio.started = timestamp
            self.session_writer.write(cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR), timestamp)
            if self.gameplay_visible and self.intro_image is None:
                self.session_audio.mark_gameplay_start(timestamp)
            self.recording_frames += 1
        except Exception as error:
            self.recording_error = error
            self.recording_timer.stop()

    def stop_recording(self):
        self.recording_timer.stop()
        self.record_presentation()
        self.session_writer = None

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
        if self.gesture_pixmap is not None:
            self.gesture_image.setPixmap(self.gesture_pixmap.scaled(
                self.gesture_image.size(), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        source = self.intro_image if self.intro_image is not None else self.pixmap
        if self.score_entries is not None:
            source = self.render_scores()
        if source is not None:
            self.image.setPixmap(source.scaled(self.image.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                                   Qt.TransformationMode.SmoothTransformation))

    def failure_grid(self, failed):
        width, height = self.image.width(), self.image.height()
        grid = QPixmap(width, height)
        grid.fill(QColor("#202020"))
        painter = QPainter(grid)
        columns = max(1, math.ceil(math.sqrt(len(failed) * width / max(1, height))))
        columns = min(columns, len(failed))
        rows = math.ceil(len(failed) / columns)
        cell_width, cell_height = width // columns, height // rows
        for index, (track_id, crop) in enumerate(sorted(failed.items())):
            crop_height, crop_width = crop.shape[:2]
            image = QImage(crop.data, crop_width, crop_height, crop.strides[0], QImage.Format.Format_BGR888).copy()
            tile = QPixmap.fromImage(image).scaled(max(1, cell_width - 12), max(1, cell_height - 32),
                                                   Qt.AspectRatioMode.KeepAspectRatio,
                                                   Qt.TransformationMode.SmoothTransformation)
            left = (index % columns) * cell_width
            top = (index // columns) * cell_height
            painter.drawPixmap(left + (cell_width - tile.width()) // 2, top + 24, tile)
            painter.setPen(QColor("white"))
            painter.drawText(left + 8, top + 18, f"ID {track_id}")
        painter.end()
        return grid

    def show_scores(self, entries, save_path=None):
        self.set_gesture(None)
        self.score_entries = entries
        self.score_cache = None
        self.script_status.setText("Scores")
        self.script_status.show()
        self.update_image()
        QApplication.instance().processEvents()

        if save_path is not None:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = save_path.with_suffix(".tmp.png")
            if not self.render_scores().save(str(temporary), "PNG"):
                raise OSError(f"Could not save scores image: {save_path}")
            temporary.replace(save_path)

    def render_scores(self):
        width, height = self.image.width(), self.image.height()
        if self.score_cache is not None and self.score_cache.size() == self.image.size():
            return self.score_cache
        canvas = QPixmap(width, height)
        canvas.fill(QColor("#ffffff"))
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        medals = [("Gold", "#d5a710"), ("Silver", "#99a3a5"), ("Bronze", "#b57439")]
        if any(entry["medal"] == "Unscored" for entry in self.score_entries):
            medals.append(("Unscored", "#677575"))
        band_height = height // len(medals)
        label_width = min(145, width // 4)
        for band, (medal, color) in enumerate(medals):
            top = band * band_height
            painter.setPen(QColor("#bac7c7"))
            painter.setBrush(QColor("#ffffff"))
            painter.drawRoundedRect(6, top + 6, width - 12, band_height - 12, 8, 8)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(color))
            painter.drawEllipse(18, top + 22, 18, 18)
            painter.setPen(QColor("#263238"))
            font = painter.font()
            font.setPixelSize(16)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(44, top + 37, medal)
            entries = [entry for entry in self.score_entries if entry["medal"] == medal]
            if not entries:
                continue
            available = max(1, width - label_width - 18)
            columns = max(1, min(len(entries), available // 110))
            rows = math.ceil(len(entries) / columns)
            cell_width, cell_height = available // columns, (band_height - 20) // rows
            for index, entry in enumerate(entries):
                left = label_width + (index % columns) * cell_width
                cell_top = top + 10 + (index // columns) * cell_height
                photo = entry["photo"]
                if photo is not None:
                    photo_height, photo_width = photo.shape[:2]
                    image = QImage(photo.data, photo_width, photo_height, photo.strides[0], QImage.Format.Format_BGR888).copy()
                    tile = QPixmap.fromImage(image).scaled(max(1, cell_width - 12), max(1, cell_height - 36),
                                                          Qt.AspectRatioMode.KeepAspectRatio,
                                                          Qt.TransformationMode.SmoothTransformation)
                    painter.drawPixmap(left + (cell_width - tile.width()) // 2, cell_top, tile)
                font.setBold(False)
                font.setPixelSize(max(8, min(12, cell_height // 5)))
                painter.setFont(font)
                percent = "Unscored" if entry["percentage"] is None else f"{entry['percentage']:.0f}%"
                painter.drawText(left + 4, cell_top + cell_height - 19, f"ID {entry['track_id']}  {percent}")
                painter.drawText(left + 4, cell_top + cell_height - 5, f"{entry['correct']}/{entry['total']}")
        painter.end()
        self.score_cache = canvas
        return canvas

    def show_failures(self, expected, failed, intro_clip=None, congrats=False):
        import av
        from PySide6.QtCore import QThread
        folder = "congrats" if congrats else "bad"
        clips = [intro_clip] if intro_clip is not None else sorted((Path(__file__).parent / folder).glob("*.mp4"))
        if not clips:
            self.error.setText(f"No videos found in {folder}/*.mp4")
            return
        clip = random.choice(clips)
        previous_pixmap = self.pixmap
        previous_gesture = self.current_gesture
        audio = None
        controls = (self.play, self.previous, self.following, self.timeline, self.apply, self.fps_field)
        enabled = [control.isEnabled() for control in controls]
        visibility = [control.isVisible() for control in controls]
        status_visible = self.script_status.isVisible()
        try:
            for control in controls:
                control.setEnabled(False)
                if intro_clip is not None:
                    control.hide()
            if intro_clip is not None:
                self.intro_image = None
                self.script_status.hide()
                self.gesture_image.hide()
            else:
                self.script_status.setText("Scores" if congrats else f"Gesture review: {expected}")
                self.gesture_image.show()
            self.image_layout.activate()
            if intro_clip is None and not congrats:
                self.pixmap = self.failure_grid(failed)
            with av.open(str(clip)) as video:
                frames = video.decode(video=0)
                first = next(frames)
                origin = float(first.time or 0)
                duration = float(video.duration / av.time_base) if video.duration else 0
                audio_command = ["ffplay", "-nodisp", "-vn", "-autoexit", "-loglevel", "error", str(clip)]
                started = time.monotonic()
                audio = subprocess.Popen(audio_command,
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                def present(decoded):
                    target = float(decoded.time or 0) - origin
                    while not self.closed and time.monotonic() - started < target:
                        QApplication.instance().processEvents()
                        QThread.msleep(5)
                    if self.closed:
                        return
                    rgb = decoded.to_ndarray(format="rgb24").copy()
                    height, width = rgb.shape[:2]
                    image = QImage(rgb.data, width, height, rgb.strides[0], QImage.Format.Format_RGB888).copy()
                    if intro_clip is not None:
                        self.pixmap = QPixmap.fromImage(image)
                    else:
                        self.gesture_pixmap = QPixmap.fromImage(image)
                    self.update_image()
                    QApplication.instance().processEvents()

                present(first)
                for decoded in frames:
                    if self.closed:
                        break
                    present(decoded)
                while not self.closed and time.monotonic() - started < duration:
                    QApplication.instance().processEvents()
                    QThread.msleep(5)
        except Exception as error:
            self.error.setText(f"Failure video: {error}")
        finally:
            if audio is not None:
                ended = time.monotonic()
                if audio.poll() is None:
                    audio.terminate()
                try:
                    audio.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    audio.kill()
                    audio.wait()
                if self.session_audio is not None:
                    self.session_audio.record(audio_command, started, ended)
            if intro_clip is None:
                self.pixmap = previous_pixmap
            self.current_gesture = ""
            self.set_gesture(previous_gesture)
            for control, was_enabled, was_visible in zip(controls, enabled, visibility):
                control.setEnabled(was_enabled)
                control.setVisible(was_visible)
            self.script_status.setVisible(status_visible)
            self.deadline = 0.0
            self.update_image()

    def set_gesture(self, gesture):
        if gesture == self.current_gesture:
            return
        self.current_gesture = gesture
        if gesture is not None:
            self.score_entries = None
            self.score_cache = None
        self.intro_image = None
        self.gesture_pixmap = None
        self.gesture_image.clear()
        if gesture == "Intro Image":
            path = Path(__file__).parent / "intro" / "intro-image.jpeg"
            pixmap = QPixmap(str(path))
            if pixmap.isNull():
                self.error.setText(f"Cannot load intro image: {path}")
            else:
                self.intro_image = pixmap
        if gesture in {"Left Hand Up", "Right Hand Up", "Both Hands Up", "Left Leg Up",
                       "Right Leg Up", "Stand Normal", "Bend Down"}:
            path = Path(__file__).parent / "gesture-images" / (gesture.lower().replace(" ", "-") + ".png")
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self.gesture_pixmap = pixmap
        self.gesture_image.setVisible(self.gesture_pixmap is not None)
        self.image_layout.activate()
        self.update_image()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_image()

    def closeEvent(self, event):
        self.stop_recording()
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
    player.showFullScreen()
    return player