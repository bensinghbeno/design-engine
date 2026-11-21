# Rig 2 Launchers

Run from the `gazebo/humanoid-arm` directory. Rig 1 scripts are unchanged.

| Command | Purpose |
| --- | --- |
| `bash rig2/1-launch-rig.sh` | Launch the Rig 2 Gazebo model, paused by default |
| `bash rig2/2-arm-gui.sh` | Four-joint Rig 2 GUI; start after the model is spawned |
| `bash rig2/3-workspace-viewer.sh` | Workspace viewer, default Rig 2, localhost:8785 |
| `bash rig2/4-motion-visualizer.sh` | Shared phone motion tool; viewer 8786, phone HTTPS 8787 |
| `bash rig2/5-sensor-visualizer.sh` | Shared sensor tool; viewer 8790, phone HTTPS 8791 |
| `bash rig2/6-screen-to-camera.sh --help` | Shared X11 screen-to-camera utility and prerequisites |

Close an existing Gazebo simulation before starting Rig 2. Launch the model and GUI in separate terminals. ROS launch arguments pass through, for example `bash rig2/1-launch-rig.sh gui:=false`. The GUI never chooses another model as a fallback and never sends motor hardware commands. It starts released, reads feedback before accepting changes, and commands only Rig 2's four arm joints. There is no gripper aperture control because the exported Rig 2 model has no movable fingers.

The shoulder pitch slider spans -180 to +180 degrees; the other three sliders use the URDF's -135 to +135 degree limits. Dragging a slider engages kinematic hold; Release stops sending poses; Reset to zero engages hold at the neutral pose. Hold is repeated Gazebo pose setting, not a physical servo controller or collision-safe motion. Released joints can fall under gravity when the simulation is unpaused. Closing the GUI stops its updates, not Gazebo.

Web launchers reuse the existing applications with distinct default ports; they do not fork their source. Motion/sensor visualizers are model-independent and share recordings and certificate storage with the original launchers. They do not animate or command the Rig 2 URDF. Override `PORT`/`STREAM_PORT` for motion, `VIEWER_PORT`/`PHONE_PORT` for sensors, and `PORT` for the workspace viewer as needed. Do not select ports already used by another process. The screen-camera utility captures the desktop, not a rig-specific camera, and needs its own unused loopback device.

The earlier `6-base-joint.sh` is intentionally not duplicated: it launches a separate single-servo model, not Rig 2. RobStride hardware controls remain shared under `actuators/robstride00`; these simulation scripts do not start them.

Offline GUI tests:

```bash
/usr/bin/python3 -m unittest discover -s tests -p test_rig2_gui.py -v
```