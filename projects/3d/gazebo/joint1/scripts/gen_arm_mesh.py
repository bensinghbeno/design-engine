#!/usr/bin/env python3
"""Generate arm_with_hole.dae — hanging arm with a REAL cylindrical hole
through its top lug, along the Y axis (the pin axis).

Single watertight solid:
  * The bar is one box from z=TOP down to z=BOTTOM (no stacked pieces).
  * Front/back faces (y = +/-HW) are rectangles WITH a circular hole, built by
    mapping each bore-ring vertex to a matching point on the rectangle
    perimeter and quadding between them (a clean annulus, no gaps).
  * The 4 outer side walls (top, bottom, +X, -X) are simple quads.
  * The bore is a cylindrical tube joining the front ring to the back ring,
    with normals facing INTO the hole.
"""
import math, os

R    = 0.03      # bore radius
HW   = 0.05      # half width/depth of the bar (full 0.10)
TOP  =  0.05     # top of bar (a bit above pin axis z=0)
BOT  = -0.50     # bottom of bar
CZ   = 0.0       # hole centre in z (= pin axis)
N    = 64        # segments around the bore (multiple of 4)

verts, tris = [], []
def V(x, y, z):
    verts.append((x, y, z)); return len(verts) - 1
def Q(a, b, c, d):
    tris.append((a, b, c)); tris.append((a, c, d))

# ---- shared rectangle perimeter (CCW), N samples, reused by walls+annulus ----
# corners CCW: (-HW,BOT)->(HW,BOT)->(HW,TOP)->(-HW,TOP)
_corners=[(-HW,BOT),(HW,BOT),(HW,TOP),(-HW,TOP)]
def perim_xz(t):
    s=t*4.0; k=int(s)%4; f=s-int(s)
    x0,z0=_corners[k]; x1,z1=_corners[(k+1)%4]
    return (x0+(x1-x0)*f, z0+(z1-z0)*f)

# perimeter loops on both faces (identical sampling so walls & annulus match)
front_per=[V(*(lambda xz:(xz[0],-HW,xz[1]))(perim_xz(i/N))) for i in range(N)]
back_per =[V(*(lambda xz:(xz[0], HW,xz[1]))(perim_xz(i/N))) for i in range(N)]

# ---- outer walls: quad strip between front_per and back_per (all 4 sides) ----
for i in range(N):
    j=(i+1)%N
    a,b=front_per[i],front_per[j]
    d,c=back_per[i],back_per[j]
    # outward-facing quad around the perimeter
    Q(a, b, c, d)

# ---- bore rings on both faces ----
front_ring=[V(R*math.cos(2*math.pi*i/N), -HW, CZ+R*math.sin(2*math.pi*i/N)) for i in range(N)]
back_ring =[V(R*math.cos(2*math.pi*i/N),  HW, CZ+R*math.sin(2*math.pi*i/N)) for i in range(N)]

# ---- annulus faces (front outward -Y, back outward +Y) ----
for i in range(N):
    j=(i+1)%N
    # front
    Q(front_per[i], front_per[j], front_ring[j], front_ring[i])
    # back
    Q(back_per[j], back_per[i], back_ring[i], back_ring[j])

# ---- bore tube (normals facing INTO the hole) ----
for i in range(N):
    j=(i+1)%N
    a,b=front_ring[i],front_ring[j]
    d,c=back_ring[i],back_ring[j]
    Q(a, d, c, b)

pos=" ".join(f"{c:.6f}" for xyz in verts for c in xyz)

# per-vertex green gradient by height: light green at top (z=TOP) -> dark at bottom
def grad(z):
    t=(TOP - z)/(TOP - BOT)          # 0 at top, 1 at bottom
    t=max(0.0,min(1.0,t))
    r=0.63*(1-t)+0.04*t
    g=0.88*(1-t)+0.25*t
    b=0.31*(1-t)+0.06*t
    return (r,g,b)
cols=[]
for (x,y,z) in verts:
    cols.extend(grad(z))
col=" ".join(f"{c:.4f}" for c in cols)

idx=" ".join(str(i) for t in tris for i in t)
dae=f'''<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset><up_axis>Z_UP</up_axis></asset>
  <library_effects>
    <effect id="arm-fx"><profile_COMMON><technique sid="t">
      <lambert>
        <diffuse><color>0.25 0.65 0.20 1</color></diffuse>
      </lambert>
    </technique></profile_COMMON></effect>
  </library_effects>
  <library_materials>
    <material id="arm-mat" name="arm-mat"><instance_effect url="#arm-fx"/></material>
  </library_materials>
  <library_geometries>
    <geometry id="arm-geom" name="arm"><mesh>
      <source id="arm-pos">
        <float_array id="arm-pos-array" count="{len(verts)*3}">{pos}</float_array>
        <technique_common>
          <accessor source="#arm-pos-array" count="{len(verts)}" stride="3">
            <param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/>
          </accessor>
        </technique_common>
      </source>
      <source id="arm-col">
        <float_array id="arm-col-array" count="{len(verts)*3}">{col}</float_array>
        <technique_common>
          <accessor source="#arm-col-array" count="{len(verts)}" stride="3">
            <param name="R" type="float"/><param name="G" type="float"/><param name="B" type="float"/>
          </accessor>
        </technique_common>
      </source>
      <vertices id="arm-vtx"><input semantic="POSITION" source="#arm-pos"/></vertices>
      <triangles material="arm-mat" count="{len(tris)}">
        <input semantic="VERTEX" source="#arm-vtx" offset="0"/>
        <input semantic="COLOR" source="#arm-col" offset="0"/>
        <p>{idx}</p>
      </triangles>
    </mesh></geometry>
  </library_geometries>
  <library_visual_scenes><visual_scene id="scene" name="scene">
    <node id="arm-node" name="arm">
      <instance_geometry url="#arm-geom">
        <bind_material><technique_common>
          <instance_material symbol="arm-mat" target="#arm-mat"/>
        </technique_common></bind_material>
      </instance_geometry>
    </node>
  </visual_scene></library_visual_scenes>
  <scene><instance_visual_scene url="#scene"/></scene>
</COLLADA>
'''

out=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","meshes","arm_with_hole.dae"))
os.makedirs(os.path.dirname(out),exist_ok=True)
open(out,"w").write(dae)
print(f"wrote {out}  ({len(verts)} verts, {len(tris)} tris)")
