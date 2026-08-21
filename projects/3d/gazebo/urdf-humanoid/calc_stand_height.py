#!/usr/bin/env python3
"""Compute where the G1's feet sit relative to the pelvis at the zero pose,
so we know what height to pin the pelvis at for a feet-on-ground stance."""
import os
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "unitree_ros", "robots", "g1_description", "g1_29dof.urdf")

root = ET.parse(SRC).getroot()

joints = {}
for j in root.findall("joint"):
    o = j.find("origin")
    xyz = [float(v) for v in (o.get("xyz", "0 0 0").split())] if o is not None else [0, 0, 0]
    joints[j.find("child").get("link")] = (j.find("parent").get("link"), xyz, j.get("name"))

def chain_z(link):
    """Sum z offsets from pelvis down to `link` at zero joint angles."""
    z = 0.0
    path = []
    while link in joints:
        parent, xyz, jn = joints[link]
        z += xyz[2]
        path.append((jn, xyz[2]))
        link = parent
    return z, list(reversed(path))

for foot in ("left_ankle_roll_link", "right_ankle_roll_link"):
    z, path = chain_z(foot)
    print(f"{foot}: z = {z:.4f} m below pelvis")
    for jn, dz in path:
        print(f"    {jn:28s} dz={dz:+.4f}")

z, _ = chain_z("left_ankle_roll_link")
print()
print(f"=> pelvis height for feet at ground (zero pose): {-z:.4f} m")
print(f"   plus ~0.03 m sole clearance          : {-z + 0.03:.4f} m")
