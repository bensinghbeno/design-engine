# Single-Joint Servo Rig

Launch from the project directory with `bash 6-base-joint.sh`.
Close any existing Gazebo simulation first. The model starts paused for inspection;
unpausing enables passive dynamics, not powered servo position holding.
The old multi-joint slider GUI is not used by this model.

The fixed base carries a servo with one revolute joint about its transverse Y axis.
Two circular hubs share that axis on opposite sides of the servo and rotate
with the steel bracket. Its cheeks sit 0.05 mm outside the hubs' outer faces and support a
flat steel bracket face. The 25.4 x 25.4 mm wooden
arm meets that face end-on, perpendicular to it, and retains the 375 mm upper-arm
length. At zero angle the wood points upward. No elbow, wrist, or gripper is included.

A second steel U-bracket is fixed to the bottom of the servo housing. Its lower
face is the `fixed_bracket` link origin, ready for a future wooden connector
extending along local -Z. It currently rests on the shortened support pedestal;
no second wooden arm or joint has been added. This bracket does not rotate with
the output hubs. Its outer span is 52 mm and its width is 30 mm, matching the
supplied drawing. The inferred 2 mm plate thickness and simplified cheeks are
provisional. Cheek height is capped below the rotating hubs by
`fixed_bracket_hub_clearance` (1 mm by default), resulting in 34 mm cheeks with
the default shaft position. This flat-edge relief approximates the pictured
cutouts, without modeling screw holes. The upper and lower bracket side plates
have 4.75 mm lateral clearance on each side. The 1 mm hub clearance is a modeling
allowance, not a dimension labeled in the drawing.

This is a layout approximation of the supplied dual-shaft servo photo, not CAD
verified against the purchased hardware. The housing is oriented 30 x 48 x 65 mm
(X/Y/Z), with the shaft along Y, using the supplied dimension drawing. Mass
(350 g), 15 mm shaft setback from the upper housing end, 2 mm rotating plate
thickness, and 15 mm hub radius are provisional. The shaft setback is adjustable
with `shaft_end_setback`; it is estimated from the image, not a labeled measurement.

At zero angle the drawing's envelope dimensions are enforced:

| Dimension | Model |
| --- | --- |
| Upper bracket outer span | 65.5 mm |
| Lower bracket outer span | 52 mm |
| Bracket width | 30 mm |
| Across outer disk faces | 61.4 mm |
| Lower bracket bottom to upper bracket top | 94.5 mm |

`upper_bracket_span`, `disk_span`, and `assembly_height` expose these dimensions.
The upper plate center is derived from the overall height and shaft location
(41.5 mm above the axis by default). Each hub's modeled axial envelope is 6.7 mm,
including the unmodeled shaft standoff, derived from the 48 mm housing depth and
61.4 mm disk span. It is not a claim that the actual disk is 6.7 mm thick.
Bracket holes, fasteners, bearings, wiring, and servo
mounting hardware are not modeled. In particular, the labeled M2.5 patterns and
12/24 mm hole spacings are not represented. Bend chamfers and curved cutouts are
also simplified; this remains a simulation envelope, not fabrication CAD.
Confirm dimensions and a suitable reinforced
wood-to-bracket fastening method before fabrication.

The assumed 270-degree travel is represented as +/-135 degrees about neutral.
The 14.7 Nm effort and 1 rad/s speed are simulation placeholders, not validated
continuous operating ratings. Mechanical clearance throughout the travel is not
certified. The world anchor does not model tipping or mounting strength.

Dimensions and simulation limits can be overridden when expanding the Xacro.
The launcher exposes `arm_length`, `gui`, and `paused`, for example:
`bash 6-base-joint.sh gui:=false arm_length:=0.375`.