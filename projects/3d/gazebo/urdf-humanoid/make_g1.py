#!/usr/bin/env python3
"""
Generate a Gazebo-ready Unitree G1 URDF.

The stock g1_29dof.urdf from unitree_ros is NOT directly spawnable in Gazebo:
  * it is not a ROS package (no package.xml), and
  * all 61 mesh references are relative paths ("meshes/foo.STL"),
    which gzserver cannot resolve.

This script fixes both by rewriting mesh paths to absolute file:// URIs, and
optionally welds the pelvis to the world so the robot doesn't topple.

Usage:
  python3 make_g1.py --pinned          -> urdf/g1_pinned.urdf
  python3 make_g1.py --free            -> urdf/g1_free.urdf
  python3 make_g1.py --pinned --damping 0.5
"""
import argparse
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(HERE, "unitree_ros", "robots", "g1_description")
OUT_DIR = os.path.join(HERE, "urdf")

ARM_KEYS = ("shoulder", "elbow", "wrist")

# Feet sit 0.7522 m below the pelvis at the zero pose, and the foot contact
# spheres are a further 0.035 m below the ankle_roll link origin.
# See calc_stand_height.py.
STAND_HEIGHT = 0.787


def add_ros_control(root):
    """Add a <transmission> per actuated joint plus the gazebo_ros_control
    plugin, so position controllers can hold the robot in a pose."""
    n = 0
    for joint in root.findall("joint"):
        if joint.get("type") not in ("revolute", "continuous", "prismatic"):
            continue
        name = joint.get("name")
        tr = ET.SubElement(root, "transmission", {"name": f"{name}_trans"})
        ET.SubElement(tr, "type").text = "transmission_interface/SimpleTransmission"
        j = ET.SubElement(tr, "joint", {"name": name})
        ET.SubElement(j, "hardwareInterface").text = \
            "hardware_interface/PositionJointInterface"
        a = ET.SubElement(tr, "actuator", {"name": f"{name}_motor"})
        ET.SubElement(a, "hardwareInterface").text = \
            "hardware_interface/PositionJointInterface"
        ET.SubElement(a, "mechanicalReduction").text = "1"
        n += 1

    gz = ET.SubElement(root, "gazebo")
    plug = ET.SubElement(gz, "plugin", {
        "name": "gazebo_ros_control",
        "filename": "libgazebo_ros_control.so"})
    ET.SubElement(plug, "robotNamespace").text = "/g1"
    ET.SubElement(plug, "robotSimType").text = \
        "gazebo_ros_control/DefaultRobotHWSim"
    ET.SubElement(plug, "legacyModeNS").text = "true"
    return n


def prune_legs(root):
    """Delete both legs entirely (hip/knee/ankle chains).

    The legs hang off the pelvis as two independent branches, so removing
    every link whose ancestry passes through a hip joint - plus the joints
    themselves - leaves the rest of the tree intact.
    """
    parent = {}
    for j in root.findall("joint"):
        parent[j.find("child").get("link")] = j.find("parent").get("link")

    def is_leg(link):
        seen = 0
        while link in parent:
            if any(k in link for k in ("hip", "knee", "ankle")):
                return True
            link = parent[link]
            seen += 1
            if seen > 50:
                break
        return any(k in link for k in ("hip", "knee", "ankle"))

    dead_links = [l for l in root.findall("link") if is_leg(l.get("name"))]
    for l in dead_links:
        root.remove(l)
    dead_names = {l.get("name") for l in dead_links}

    dead_joints = [j for j in root.findall("joint")
                   if j.find("child").get("link") in dead_names
                   or j.find("parent").get("link") in dead_names]
    for j in dead_joints:
        root.remove(j)

    return len(dead_links), len(dead_joints)


def add_pole(root, pole_height, pole_radius):
    """Add a static pole from the ground up to the pelvis, welded to world."""
    ET.SubElement(root, "link", {"name": "world"})

    pole = ET.SubElement(root, "link", {"name": "pole"})
    for tag in ("visual", "collision"):
        el = ET.SubElement(pole, tag)
        ET.SubElement(el, "origin",
                      {"xyz": f"0 0 {pole_height/2.0}", "rpy": "0 0 0"})
        geom = ET.SubElement(el, "geometry")
        ET.SubElement(geom, "cylinder",
                      {"radius": str(pole_radius), "length": str(pole_height)})
        if tag == "visual":
            mat = ET.SubElement(el, "material", {"name": "pole_grey"})
            ET.SubElement(mat, "color", {"rgba": "0.35 0.35 0.38 1"})
    inr = ET.SubElement(pole, "inertial")
    ET.SubElement(inr, "origin", {"xyz": f"0 0 {pole_height/2.0}", "rpy": "0 0 0"})
    ET.SubElement(inr, "mass", {"value": "50.0"})
    ET.SubElement(inr, "inertia", {"ixx": "5.0", "ixy": "0", "ixz": "0",
                                   "iyy": "5.0", "iyz": "0", "izz": "1.0"})

    # world -> pole (static)
    j1 = ET.SubElement(root, "joint", {"name": "world_to_pole", "type": "fixed"})
    ET.SubElement(j1, "parent", {"link": "world"})
    ET.SubElement(j1, "child", {"link": "pole"})
    ET.SubElement(j1, "origin", {"xyz": "0 0 0", "rpy": "0 0 0"})

    # pole -> pelvis (static): torso sits on top of the pole
    j2 = ET.SubElement(root, "joint", {"name": "pole_to_pelvis", "type": "fixed"})
    ET.SubElement(j2, "parent", {"link": "pole"})
    ET.SubElement(j2, "child", {"link": "pelvis"})
    ET.SubElement(j2, "origin", {"xyz": f"0 0 {pole_height}", "rpy": "0 0 0"})

    gz = ET.SubElement(root, "gazebo", {"reference": "pole"})
    ET.SubElement(gz, "material").text = "Gazebo/Grey"


# Simplified collision proxies, sized from the real mesh bounding boxes
# (see calc_collision_boxes.py). Each entry is:
#     link: (shape, dims, xyz, rpy)
#       box      dims = (sx, sy, sz)
#       cylinder dims = (radius, length)   default axis is z
#       sphere   dims = (radius,)
#
# Why not just self-collide the meshes: the torso STL is 44,658 triangles and
# the hand is 45,748. ODE's trimesh-trimesh path is both very slow and prone
# to tunnelling/jitter, so self-collision against raw meshes is unusable.
# These proxies are deliberately a little smaller than the visual mesh so
# links that merely graze each other do not sit in permanent contact.
HALF_PI = 1.5708

COLLISION_PROXIES = {
    "torso_link":  ("box", (0.135, 0.195, 0.295), (0.0085, 0.0, 0.1452), (0, 0, 0)),
    "head_link":   ("box", (0.125, 0.140, 0.185), (0.0038, 0.0, 0.4277), (0, 0, 0)),
}
for _s, _sign in (("left", 1.0), ("right", -1.0)):
    COLLISION_PROXIES.update({
        # upper arm: slim cylinder down the link's z axis
        f"{_s}_shoulder_yaw_link":
            ("cylinder", (0.030, 0.115), (0.0078, -0.0042 * _sign, -0.0411), (0, 0, 0)),
        # forearm: cylinder laid along the link's x axis
        f"{_s}_elbow_link":
            ("cylinder", (0.030, 0.110), (0.0351, 0.0018 * _sign, -0.0078), (0, HALF_PI, 0)),
        f"{_s}_wrist_roll_link":
            ("sphere", (0.026,), (0.0280, 0.0, 0.0), (0, 0, 0)),
        f"{_s}_wrist_pitch_link":
            ("cylinder", (0.026, 0.085), (0.0230, 0.0, 0.0), (0, HALF_PI, 0)),
        f"{_s}_wrist_yaw_link":
            ("sphere", (0.026,), (0.0118, 0.0031 * _sign, 0.0), (0, 0, 0)),
        # the rubber hands ship with NO collision at all - give them one
        f"{_s}_rubber_hand":
            ("box", (0.115, 0.058, 0.095), (0.0659, -0.0146 * _sign, 0.0102), (0, 0, 0)),
    })

# Links allowed to self-collide. Deliberately excludes shoulder_pitch and
# shoulder_roll: those sit partly inside the torso shell, so enabling them
# puts the solver in permanent contact and the arm jitters instead of hanging.
SELF_COLLIDE_LINKS = ["torso_link", "head_link"]
for _s in ("left", "right"):
    SELF_COLLIDE_LINKS += [
        f"{_s}_shoulder_yaw_link", f"{_s}_elbow_link",
        f"{_s}_wrist_roll_link", f"{_s}_wrist_pitch_link",
        f"{_s}_wrist_yaw_link", f"{_s}_rubber_hand",
    ]


def _geom(parent, shape, dims):
    g = ET.SubElement(parent, "geometry")
    if shape == "box":
        ET.SubElement(g, "box", {"size": f"{dims[0]} {dims[1]} {dims[2]}"})
    elif shape == "cylinder":
        ET.SubElement(g, "cylinder",
                      {"radius": str(dims[0]), "length": str(dims[1])})
    elif shape == "sphere":
        ET.SubElement(g, "sphere", {"radius": str(dims[0])})


def add_self_collision(root):
    """Swap heavy mesh collisions for primitives and turn on self-collision."""
    links = {l.get("name"): l for l in root.findall("link")}

    replaced = 0
    added = 0
    for name, (shape, dims, xyz, rpy) in COLLISION_PROXIES.items():
        link = links.get(name)
        if link is None:
            continue
        existing = link.findall("collision")
        for c in existing:
            link.remove(c)
        col = ET.SubElement(link, "collision", {"name": f"{name}_collision"})
        ET.SubElement(col, "origin", {
            "xyz": f"{xyz[0]} {xyz[1]} {xyz[2]}",
            "rpy": f"{rpy[0]} {rpy[1]} {rpy[2]}"})
        _geom(col, shape, dims)
        if existing:
            replaced += 1
        else:
            added += 1

    # Gazebo needs self_collide per link, plus contact params that keep the
    # solver stable. Without kp/kd the default stiffness makes light arm links
    # bounce off the torso instead of resting against it.
    enabled = 0
    for name in SELF_COLLIDE_LINKS:
        if name not in links:
            continue
        gz = ET.SubElement(root, "gazebo", {"reference": name})
        ET.SubElement(gz, "self_collide").text = "true"
        ET.SubElement(gz, "mu1").text = "0.7"
        ET.SubElement(gz, "mu2").text = "0.7"
        ET.SubElement(gz, "kp").text = "500000.0"
        ET.SubElement(gz, "kd").text = "100.0"
        ET.SubElement(gz, "maxVel").text = "0.1"
        ET.SubElement(gz, "minDepth").text = "0.001"
        enabled += 1

    return replaced, added, enabled


def build(src_name, pinned, height, damping, friction, out_name,
          controlled=False, lock_waist=False,
          torso_only=False, pole_height=1.0, pole_radius=0.05,
          self_collide=False):
    src = os.path.join(SRC_DIR, src_name)
    if not os.path.isfile(src):
        sys.exit(f"ERROR: source URDF not found: {src}")

    tree = ET.parse(src)
    root = tree.getroot()

    # --- 1. rewrite every relative mesh path to an absolute file:// URI ---
    fixed = 0
    for mesh in root.iter("mesh"):
        fn = mesh.get("filename", "")
        if fn.startswith(("package://", "file://", "model://", "/")):
            continue
        mesh.set("filename", "file://" + os.path.join(SRC_DIR, fn))
        fixed += 1

    # --- 2. joint damping/friction so the limbs behave instead of flailing ---
    touched = 0
    for joint in root.findall("joint"):
        if joint.get("type") not in ("revolute", "continuous", "prismatic"):
            continue
        dyn = joint.find("dynamics")
        if dyn is None:
            dyn = ET.SubElement(joint, "dynamics")
        dyn.set("damping", str(damping))
        dyn.set("friction", str(friction))
        touched += 1

    # --- 2b. optionally weld the waist rigid ---
    # The waist joints are the least useful for arm experiments and the most
    # prone to PID limit-cycling: a single yaw axis carries 16.6 kg of torso
    # plus arms. Making them fixed removes the problem outright.
    locked = 0
    if lock_waist:
        for joint in root.findall("joint"):
            if joint.get("name", "").startswith("waist_") and \
                    joint.get("type") == "revolute":
                joint.set("type", "fixed")
                for tag in ("limit", "dynamics", "axis"):
                    el = joint.find(tag)
                    if el is not None:
                        joint.remove(el)
                locked += 1

    # --- 2c. torso-only: drop the legs, mount the torso on a static pole ---
    n_dead_links = n_dead_joints = 0
    if torso_only:
        n_dead_links, n_dead_joints = prune_legs(root)
        add_pole(root, pole_height, pole_radius)

    # --- 2d. self-collision: primitive proxies + per-link self_collide ---
    sc_repl = sc_add = sc_on = 0
    if self_collide:
        sc_repl, sc_add, sc_on = add_self_collision(root)

    # --- 3. optionally weld the pelvis to the world ---
    if pinned and not torso_only:
        names = {l.get("name") for l in root.findall("link")}
        if "world" not in names:
            ET.SubElement(root, "link", {"name": "world"})
        wj = ET.SubElement(root, "joint",
                           {"name": "world_to_pelvis", "type": "fixed"})
        ET.SubElement(wj, "parent", {"link": "world"})
        ET.SubElement(wj, "child", {"link": "pelvis"})
        ET.SubElement(wj, "origin",
                      {"xyz": f"0 0 {height}", "rpy": "0 0 0"})

    # --- 4. gazebo state plugin so /gazebo/get_* services see link states ---
    gz = ET.SubElement(root, "gazebo")
    plug = ET.SubElement(gz, "plugin", {
        "name": "gazebo_ros_state",
        "filename": "libgazebo_ros_state.so"})
    ET.SubElement(plug, "robotNamespace").text = "/"
    ET.SubElement(plug, "updateRate").text = "50.0"

    # --- 5. optional ros_control transmissions for pose holding ---
    n_trans = add_ros_control(root) if controlled else 0

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, out_name)
    tree.write(out, encoding="utf-8", xml_declaration=True)

    arms = [j.get("name") for j in root.findall("joint")
            if any(k in j.get("name") for k in ARM_KEYS)]
    print(f"  wrote {out}")
    print(f"    mesh paths rewritten : {fixed}")
    print(f"    joints damped        : {touched} (damping={damping} friction={friction})")
    print(f"    pelvis pinned        : {pinned}" + (f" at z={height}" if pinned else ""))
    print(f"    arm joints available : {len(arms)}")
    if torso_only:
        print(f"    legs removed         : {n_dead_links} links, {n_dead_joints} joints")
        print(f"    static pole          : h={pole_height} m r={pole_radius} m")
    if self_collide:
        print(f"    collision proxies    : {sc_repl} replaced, {sc_add} added")
        print(f"    self_collide links   : {sc_on}")
    if lock_waist:
        print(f"    waist joints locked  : {locked} (now fixed)")
    if controlled:
        print(f"    transmissions added  : {n_trans} (PositionJointInterface)")
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--src", default="g1_29dof.urdf")
    p.add_argument("--pinned", action="store_true")
    p.add_argument("--free", action="store_true")
    p.add_argument("--stand", action="store_true",
                   help="controlled build: transmissions + ros_control, "
                        "pinned at standing height so the feet touch ground")
    p.add_argument("--height", type=float, default=1.0)
    p.add_argument("--damping", type=float, default=0.2)
    p.add_argument("--friction", type=float, default=0.1)
    p.add_argument("--lock-waist", dest="lock_waist", action="store_true",
                   help="weld the 3 waist joints rigid; stops the torso yaw "
                        "oscillation, recommended for arm experiments")
    p.add_argument("--torso", action="store_true",
                   help="remove both legs and mount the upper body on a "
                        "static pole; arms hang free under gravity")
    p.add_argument("--pole-height", dest="pole_height", type=float, default=1.0)
    p.add_argument("--pole-radius", dest="pole_radius", type=float, default=0.05)
    p.add_argument("--no-self-collide", dest="self_collide",
                   action="store_false", default=True,
                   help="disable arm/torso self-collision (arms pass through "
                        "the body, which is the stock URDF behaviour)")
    a = p.parse_args()

    if a.torso:
        print("[torso on pole: legs removed, passive arms]")
        build(a.src, False, 0, a.damping, a.friction, "g1_torso.urdf",
              controlled=False, lock_waist=True, torso_only=True,
              pole_height=a.pole_height, pole_radius=a.pole_radius,
              self_collide=a.self_collide)
        return

    if not (a.pinned or a.free or a.stand):
        a.pinned = a.free = a.stand = True  # build all three by default

    if a.pinned:
        print("[pinned]")
        build(a.src, True, a.height, a.damping, a.friction, "g1_pinned.urdf")
    if a.free:
        print("[free]")
        build(a.src, False, a.height, a.damping, a.friction, "g1_free.urdf")
    if a.stand:
        print("[stand: ros_control, feet on ground]")
        build(a.src, True, STAND_HEIGHT, a.damping, a.friction,
              "g1_stand.urdf", controlled=True, lock_waist=a.lock_waist)


if __name__ == "__main__":
    main()
