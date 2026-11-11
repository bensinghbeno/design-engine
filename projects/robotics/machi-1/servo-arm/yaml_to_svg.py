"""Render the explicit block-diagram schema used by wiring-blocks.yaml.

Install: python -m pip install -r requirements.txt
Usage: python yaml_to_svg.py wiring-blocks.yaml [-o output.svg]
Coordinates are canvas pixels; routes must be orthogonal and disjoint.
"""

import argparse
import itertools
from pathlib import Path
import xml.etree.ElementTree as ET

import yaml


COLORS = {
    "blue": "#087c96", "yellow": "#a97900", "black": "#111111",
    "white": "#ffffff", "red": "#c52e3e",
}


def segment_bounds(start, end):
    return (min(start[0], end[0]), min(start[1], end[1]),
            max(start[0], end[0]), max(start[1], end[1]))


def intersects(first, second):
    return (max(first[0], second[0]) <= min(first[2], second[2])
            and max(first[1], second[1]) <= min(first[3], second[3]))


def validate(document):
    if document.get("schema_version") != 1:
        raise ValueError("Expected block diagram schema_version: 1")
    components = document["components"]
    width = document["canvas"]["width"]
    height = document["canvas"]["height"]
    pins = {}
    rectangles = []
    for name, component in components.items():
        left, top, block_width, block_height = component["bounds"]
        right, bottom = left + block_width, top + block_height
        if not (0 <= left < right <= width and 0 <= top < bottom <= height):
            raise ValueError(f"Invalid bounds for {name}")
        rectangle = (left, top, right, bottom)
        if any(intersects(rectangle, previous) for previous in rectangles):
            raise ValueError(f"Block {name} overlaps another block")
        rectangles.append(rectangle)
        for pin_name, pin in component["pins"].items():
            horizontal, vertical = pin["position"]
            boundary = {
                "left": horizontal == left and top < vertical < bottom,
                "right": horizontal == right and top < vertical < bottom,
                "top": vertical == top and left < horizontal < right,
                "bottom": vertical == bottom and left < horizontal < right,
            }
            if not pin["label"] or not boundary.get(pin["side"], False):
                raise ValueError(f"Invalid boundary pin {name}.{pin_name}")
            if pin["position"] in pins.values():
                raise ValueError(f"Overlapping pin {name}.{pin_name}")
            pins[f"{name}.{pin_name}"] = pin["position"]

    segments = []
    for wire_index, wire in enumerate(document["connections"]):
        route = wire["route"]
        if wire["color"] not in COLORS:
            raise ValueError(f"Unknown wire color: {wire['color']}")
        if (len(route) < 2 or route[0] != pins[wire["from"]]
                or route[-1] != pins[wire["to"]]):
            raise ValueError(f"Wire {wire_index} must terminate at its named pins")
        for point in route:
            if not (0 <= point[0] <= width and 0 <= point[1] <= height):
                raise ValueError(f"Wire {wire_index} leaves the canvas")
        for segment_index, (start, end) in enumerate(zip(route, route[1:])):
            if start == end or (start[0] != end[0] and start[1] != end[1]):
                raise ValueError(f"Wire {wire_index} must have nonzero orthogonal segments")
            bounds = segment_bounds(start, end)
            for left, top, right, bottom in rectangles:
                if start[1] == end[1]:
                    crosses = (top < start[1] < bottom
                               and bounds[0] < right and bounds[2] > left)
                    follows_edge = start[1] in (top, bottom) and max(bounds[0], left) < min(bounds[2], right)
                else:
                    crosses = (left < start[0] < right
                               and bounds[1] < bottom and bounds[3] > top)
                    follows_edge = start[0] in (left, right) and max(bounds[1], top) < min(bounds[3], bottom)
                if crosses or follows_edge:
                    raise ValueError(f"Wire {wire_index} crosses or follows a box edge")
            segments.append((wire_index, segment_index, bounds))
    for first, second in itertools.combinations(segments, 2):
        if not intersects(first[2], second[2]):
            continue
        if first[0] == second[0] and abs(first[1] - second[1]) == 1:
            overlap_width = min(first[2][2], second[2][2]) - max(first[2][0], second[2][0])
            overlap_height = min(first[2][3], second[2][3]) - max(first[2][1], second[2][1])
            if overlap_width == 0 and overlap_height == 0:
                continue
        raise ValueError(f"Wires {first[0]} and {second[0]} cross or overlap")


def render(document):
    validate(document)
    width = document["canvas"]["width"]
    height = document["canvas"]["height"]
    root = ET.Element("svg", {
        "xmlns": "http://www.w3.org/2000/svg", "width": str(width),
        "height": str(height), "viewBox": f"0 0 {width} {height}",
        "role": "img", "aria-labelledby": "title description",
    })

    def element(tag, **attributes):
        return ET.SubElement(root, tag, {
            key.replace("_", "-"): str(value) for key, value in attributes.items()
        })

    def text(content, position, size=15, anchor="start", weight="normal"):
        node = element("text", x=position[0], y=position[1], font_size=size,
                       text_anchor=anchor, font_weight=weight,
                       font_family="sans-serif", fill="#18252b")
        node.text = content

    element("title", id="title").text = document["title"]
    element("desc", id="description").text = document["subtitle"]
    element("rect", width=width, height=height, fill="#f2f6f7")
    text(document["title"], [40, 45], 26, weight="bold")
    text(document["subtitle"], [40, 78])
    for component in document["components"].values():
        left, top, block_width, block_height = component["bounds"]
        element("rect", x=left, y=top, width=block_width, height=block_height,
                rx=4, fill="white", stroke="#53656e", stroke_width=2)
        offset = component.get("header_offset", 32)
        text(component["label"], [left + 20, top + offset], 19, weight="bold")
        text(component["detail"], [left + 20, top + offset + 28], 14)
    for wire in document["connections"]:
        points = " ".join(f"{point[0]},{point[1]}" for point in wire["route"])
        if wire["color"] == "white":
            element("polyline", points=points, fill="none", stroke="#53656e", stroke_width=7)
        element("polyline", points=points, fill="none", stroke=COLORS[wire["color"]],
                stroke_width=3, stroke_linejoin="round")
        text(wire["label"], wire["label_position"], 14, wire.get("label_anchor", "middle"))
    for component in document["components"].values():
        for pin in component["pins"].values():
            horizontal, vertical = pin["position"]
            element("circle", cx=horizontal, cy=vertical, r=5,
                    fill="white", stroke="#18252b", stroke_width=2)
            offset_horizontal, offset_vertical, anchor = {
                "left": (14, 5, "start"), "right": (-14, 5, "end"),
                "top": (0, 27, "middle"), "bottom": (0, -18, "middle"),
            }[pin["side"]]
            text(pin["label"], [horizontal + offset_horizontal, vertical + offset_vertical], 14, anchor)
    for index, note in enumerate(document.get("notes", [])):
        text(note, [40, height - 66 + index * 24], 14)
    ET.indent(root)
    return ET.ElementTree(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Block-diagram YAML (not the legacy wiring.yaml)")
    parser.add_argument("-o", "--output", type=Path)
    arguments = parser.parse_args()
    output = arguments.output or arguments.input.with_suffix(".svg")
    if output.resolve() == arguments.input.resolve():
        parser.error("Output must differ from input")
    try:
        document = yaml.safe_load(arguments.input.read_text(encoding="utf-8"))
        tree = render(document)
        tree.write(output, encoding="utf-8", xml_declaration=True)
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as error:
        parser.exit(1, f"Cannot render diagram: {error}\n")
    print(f"Created {output}: {len(document['connections'])} validated wire routes")


if __name__ == "__main__":
    main()