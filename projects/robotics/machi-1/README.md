# Machi-1 Robotics

## Layout

| Folder | Contents |
| --- | --- |
| `gazebo/humanoid-arm/` | ROS/Gazebo package, numbered launch scripts, arm GUI, URDF/Xacro models and tests |
| `gazebo/humanoid-arm/workspace-viewer/` | Browser kinematics and workspace viewer |
| `gazebo/humanoid-arm/motion-visualizer/` | Phone motion recording and visualization |
| `gazebo/humanoid-arm/sensor-visualizer/` | Sensor visualization |
| `gazebo/humanoid-arm/sensors/` | Sensor recordings, including local captures |
| `actuators/robstride00/` | Motor CLI, tests, wiring YAML/SVG, datasheets, drilling templates and MotorStudio launcher/tools |
| `blender/base-joint/` | Base-joint Blender model and local backup |
| `servo-arm/` | Existing servo firmware, wiring, CAD and conversion tools; unchanged |

Open `machi-1.code-workspace` in VS Code to access the simulation, actuator, Blender and servo folders together.

## Simulation and Viewers

Rig 2 launchers are available directly in this directory:

| Command | Tool |
| --- | --- |
| `bash 1-rig2-gazebo.sh` | Gazebo, initially paused |
| `bash 2-rig2-arm-gui.sh` | Four-joint GUI; run in another terminal after Gazebo spawns Rig 2 |
| `bash 3-rig2-workspace-viewer.sh` | Workspace viewer on port 8785 |
| `bash 4-rig2-motion-visualizer.sh` | Motion viewer on port 8786 |
| `bash 5-rig2-sensor-visualizer.sh` | Sensor viewer on port 8790 |
| `bash 6-rig2-screen-to-camera.sh --help` | Desktop camera utility |

These forward arguments to the [Rig 2 launchers](gazebo/humanoid-arm/rig2/README.md)
and locate their files independently of the current working directory.

From this directory:

```bash
cd gazebo/humanoid-arm
bash 3-workspace-viewer.sh
```

Other launchers in that directory: `1-launch-rig.sh` (Gazebo rig), `2-arm-gui.sh` (ROS GUI), `4-motion-visualizer.sh`, `5-sensor-visualizer.sh`, `6-base-joint.sh`, and `7-launch-rig2.sh`. Gazebo launchers require the existing ROS Noetic/Gazebo installation. Keep URDF, launch, sensor and viewer folders together: their relative references are intentional.

## RobStride

See [motor setup and CLI documentation](actuators/robstride00/README.md). Its existing commands can still be run from `gazebo/humanoid-arm`, where `robstride00` links to `../../actuators/robstride00` and the existing `.venv` is retained. The Python controller and MotorStudio must not share the serial device concurrently.

From this directory, launch MotorStudio with:

```bash
bash actuators/robstride00/launch-motorstudio.sh
```

MotorStudio downloads, local dependencies and motor logs were moved intact, not reinstalled. These local files are not necessarily tracked in Git.

## Migration Compatibility

The former `projects/3d/gazebo/URDF-Humanoid-Arm` directory is now a relative symbolic link to `projects/robotics/machi-1/gazebo/humanoid-arm`. The simulation directory also links its former Blender filenames to `../../blender/base-joint/`.

These links preserve existing terminals, saved commands and virtual-environment entry points. Python virtual environments contain absolute paths; recreate the environment at its new location before removing the old-path compatibility link. Blender files were moved byte-for-byte, without resaving or repacking any externally referenced assets. Other projects, including planetary gearboxes, were not moved.

## Offline Checks

From `gazebo/humanoid-arm`:

```bash
.venv/bin/python -m unittest discover -s robstride00 -p 'test_control.py' -v
npm --prefix workspace-viewer test
npm --prefix motion-visualizer test
/usr/bin/python3 -m unittest discover -s tests -v
```

Migration validation: all original file checksums matched; 20 motor tests, 54 workspace-viewer tests and 5 motion tests passed. The system-Python arm GUI suite passed 19 of 20 tests; its unchanged elbow-axis assertion expects Y while the URDF specifies Z. The motor-control virtual environment lacks Tkinter, so use system Python for the GUI suite. Interactive Blender/Gazebo sessions and hardware motion were not launched during migration.