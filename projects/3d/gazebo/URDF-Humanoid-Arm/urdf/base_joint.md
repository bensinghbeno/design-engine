# Single-Joint Servo Rig

Launch from the project directory with `bash 6-base-joint.sh`.
Close any existing Gazebo simulation first. The model starts paused for inspection;
unpausing enables passive dynamics, not powered servo position holding.
The old multi-joint slider GUI is not used by this model.

The fixed base carries a servo with one revolute joint about its transverse Y axis.
Two circular hubs share that axis on opposite sides of the servo and rotate
with the steel bracket. Its cheeks meet the hubs' outer faces and support a
flat steel bracket face. The 25.4 x 25.4 mm wooden
arm meets that face end-on, perpendicular to it, and retains the 375 mm upper-arm
length. At zero angle the wood points upward. No elbow, wrist, or gripper is included.

This is a layout approximation of the supplied dual-shaft servo photo, not CAD
verified against the purchased hardware. Servo envelope (48 x 30 x 65 mm), mass
(350 g), centered shaft position, bracket reach (50 mm), thickness (3 mm), and
clearance are provisional. Hub radius (12 mm) and axial depth (4 mm) are also
provisional and adjustable with `hub_radius` and `hub_depth` Xacro arguments.
Bracket holes, fasteners, bearings, wiring, and servo
mounting hardware are not modeled. Confirm dimensions and a suitable reinforced
wood-to-bracket fastening method before fabrication.

The assumed 270-degree travel is represented as +/-135 degrees about neutral.
The 14.7 Nm effort and 1 rad/s speed are simulation placeholders, not validated
continuous operating ratings. Mechanical clearance throughout the travel is not
certified. The world anchor does not model tipping or mounting strength.

Dimensions and simulation limits can be overridden when expanding the Xacro.
The launcher exposes `arm_length`, `gui`, and `paused`, for example:
`bash 6-base-joint.sh gui:=false arm_length:=0.375`.