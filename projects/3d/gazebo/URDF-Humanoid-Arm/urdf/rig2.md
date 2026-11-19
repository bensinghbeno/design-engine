# Rig 2

Rig 2 is a neutral-pose snapshot of the edited Blender assembly in
`../base-joint.blend`, including the user's lowered stand, RobStride 00 shoulder
pitch actuator, right-angle shoulder mounting adapter, and Wrist2Gripper.
It is independent of Rig 1 and the earlier single-servo Xacro.

Run `bash 3-workspace-viewer.sh`, select Rig 2, and load it. The viewer defaults
to Rig 2 and generates a 20,000-point position workspace. The tracked link,
`wrist_to_gripper_tip`, is the center of the outer local +X face of Wrist2Gripper.
It has zero tracked offset. Select another link/offset to explore another point.
The RobStride pitch joint is modeled as continuous (the viewer samples one full
turn); the remaining three servos have +/-135-degree limits. Neutral joint axes
are Y, X, Z, X, with the upper arm down and forearm along +X, matching Rig 1.
Joint checkboxes can lock individual joints; regenerate the cloud after changing
ranges or locks. The adapter is conceptual; fasteners and mounting holes are omitted.

Reach points ignore self-collision, the stand, the ground, torque, gravity,
hardware clearance, and structural deformation. Points below ground can appear.
This is sampled positional reach, not proof of safe motion or arbitrary tool
orientation. No gripper or finger motion is modeled.

For Gazebo, close any existing simulation and run `bash 7-launch-rig2.sh`.
The model starts paused and has no servo-holding controller. Inertias and effort
limits are approximations, suitable for layout inspection rather than dynamics
validation. The old Rig 1 GUI is not used.

URDF geometry preserves connected box components and cylindrical hubs from the
Blender meshes, baking scale into geometry and rigid transforms into joints.
Text labels are omitted. `rig2.reference.json` records neutral Blender link
positions, dimensions, axes, and endpoint for regression checks. Blender edits
do not automatically update this exported snapshot.