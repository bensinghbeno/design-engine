#!/usr/bin/env python3
"""Compute axis-aligned bounding boxes for the collision meshes we intend to
replace with primitives, so the proxies are sized from real geometry rather
than guessed."""
import os
import struct
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "unitree_ros", "robots", "g1_description")


def aabb(path):
    with open(path, "rb") as f:
        f.read(80)
        n = struct.unpack("<I", f.read(4))[0]
        lo = [1e9] * 3
        hi = [-1e9] * 3
        for _ in range(n):
            d = f.read(50)
            for k in range(3):
                v = struct.unpack("<fff", d[12 + k * 12:24 + k * 12])
                for a in range(3):
                    lo[a] = min(lo[a], v[a])
                    hi[a] = max(hi[a], v[a])
    return lo, hi, n


TARGETS = [
    "torso_link", "head_link",
    "left_shoulder_yaw_link", "left_elbow_link",
    "left_wrist_roll_link", "left_wrist_pitch_link", "left_wrist_yaw_link",
    "left_rubber_hand",
]

root = ET.parse(os.path.join(SRC, "g1_29dof.urdf")).getroot()
origins = {}
for l in root.findall("link"):
    c = l.find("collision")
    if c is None:
        continue
    o = c.find("origin")
    origins[l.get("name")] = o.get("xyz", "0 0 0") if o is not None else "0 0 0"

for name in TARGETS:
    p = os.path.join(SRC, "meshes", name + ".STL")
    if not os.path.exists(p):
        print(f"  {name:28s} (no mesh)")
        continue
    lo, hi, n = aabb(p)
    size = [hi[i] - lo[i] for i in range(3)]
    ctr = [(hi[i] + lo[i]) / 2 for i in range(3)]
    print(f"  {name:28s} tris={n:6d}")
    print(f"      size  x={size[0]:.4f} y={size[1]:.4f} z={size[2]:.4f}")
    print(f"      centre x={ctr[0]:+.4f} y={ctr[1]:+.4f} z={ctr[2]:+.4f}")
    print(f"      urdf collision origin: {origins.get(name, '?')}")
