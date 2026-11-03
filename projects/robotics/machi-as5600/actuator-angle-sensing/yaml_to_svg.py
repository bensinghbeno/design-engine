#!/usr/bin/env python3
"""Render the AS5600 wiring YAML file as a scalable SVG connection diagram.

Mirrors the layout conventions of yaml_to_jpg.py but emits resolution-independent
SVG instead of a raster image, so the diagram stays crisp at any size and can be
embedded in documentation or edited in vector tools.
"""

import argparse
import xml.sax.saxutils as su
from pathlib import Path

import yaml


BACKGROUND = "#fbfaf7"
INK = "#25313b"
MUTED = "#66737b"
OUTLINE = "#c4ccd0"
WARNING_FILL = "#fff0ec"
WARNING_OUTLINE = "#d98573"
WARNING_TEXT = "#8e342b"

FONT_FAMILY = "DejaVu Sans, Liberation Sans, sans-serif"


def escape_attr(value):
    return su.quoteattr(str(value))


def escape_text(value):
    return su.escape(str(value))


def svg_attrs(**kwargs):
    """Build an SVG attribute string; converts Python-style underscores to hyphens."""
    return " ".join(f'{k.replace("_", "-")}={escape_attr(v)}' for k, v in kwargs.items())


def rect(x, y, width, height, **attrs):
    attr_str = svg_attrs(**attrs)
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" {attr_str} />'


def rounded_rect(x, y, width, height, radius, **attrs):
    attr_str = svg_attrs(**attrs)
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
        f'rx="{radius}" ry="{radius}" {attr_str} />'
    )


def line(x1, y1, x2, y2, **attrs):
    attr_str = svg_attrs(**attrs)
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" {attr_str} />'


def polyline(points, **attrs):
    attr_str = svg_attrs(**attrs)
    pts = " ".join(f"{x},{y}" for x, y in points)
    return f'<polyline points="{pts}" {attr_str} />'


def circle(cx, cy, r, **attrs):
    attr_str = svg_attrs(**attrs)
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" {attr_str} />'


def text(x, y, content, **attrs):
    attr_str = svg_attrs(**attrs)
    return f'<text x="{x}" y="{y}" {attr_str}>{escape_text(content)}</text>'


def draw_component(dwg, component, anchors):
    x = component["x"]
    y = component["y"]
    width = component["width"]
    height = component["height"]
    right = x + width
    bottom = y + height

    dwg.append(rounded_rect(x, y, width, height, 12, fill=component["fill"], stroke=OUTLINE, stroke_width=2))
    dwg.append(rounded_rect(x, y, width, 82, 12, fill=component["accent"]))
    dwg.append(rect(x, y + 48, width, 34, fill=component["accent"]))

    dwg.append(text(x + 22, y + 44, component["label"], fill="#ffffff",
                    font_family=FONT_FAMILY, font_size=22, font_weight="bold"))
    dwg.append(text(x + 23, y + 73, component["subtitle"], fill="#e9eef0",
                    font_family=FONT_FAMILY, font_size=13))

    for pin, details in component["pins"].items():
        px = x if details["side"] == "left" else right
        anchors[f"{component['id']}.{pin}"] = (px, y + details["y"])


def draw_connections(dwg, data, anchors):
    colors = {item["kind"]: item["color"] for item in data["legend"]}
    for connection in data["connections"]:
        start = anchors[connection["from"]]
        end = anchors[connection["to"]]
        mid_x = (start[0] + end[0]) / 2
        route = [start, (mid_x, start[1]), (mid_x, end[1]), end]
        dwg.append(polyline(
            route,
            fill="none",
            stroke=colors[connection["kind"]],
            stroke_width=4,
            stroke_linejoin="round",
            stroke_linecap="round",
            marker_end="url(#connection-arrow)",
        ))
def draw_pins(dwg, components):
    for component in components:
        x = component["x"]
        y = component["y"]
        right = x + component["width"]
        for pin, details in component["pins"].items():
            side = details["side"]
            px = x if side == "left" else right
            py = y + details["y"]
            dwg.append(circle(px, py, 6, fill="#ffffff", stroke=INK, stroke_width=2))
            label = details.get("label", pin)
            label_x = px + 18 if side == "left" else px - 18
            text_anchor = "start" if side == "left" else "end"
            dwg.append(text(label_x, py + 5, label, fill=INK,
                            font_family=FONT_FAMILY, font_size=15, font_weight="bold",
                            text_anchor=text_anchor, dominant_baseline="middle"))


def draw_legend(dwg, legend):
    x = 100
    y = 770
    for item in legend:
        dwg.append(line(x, y + 10, x + 38, y + 10, stroke=item["color"], stroke_width=5, stroke_linecap="round"))
        dwg.append(text(x + 50, y + 4, item["label"], fill=INK,
                        font_family=FONT_FAMILY, font_size=15, font_weight="bold",
                        dominant_baseline="middle"))
        text_width = len(item["label"]) * 8.5
        x += 50 + text_width + 70


def render(source, destination):
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    canvas = data["canvas"]
    width = canvas["width"]
    height = canvas["height"]

    dwg = []
    dwg.append('<?xml version="1.0" encoding="UTF-8"?>')
    dwg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label={escape_attr(data["title"])}>'
    )
    dwg.append(
        '<defs>'
        '<marker id="connection-arrow" markerWidth="10" markerHeight="10" '
        'refX="9" refY="3" orient="auto" markerUnits="strokeWidth">'
        '<path d="M0,0 L0,6 L9,3 z" fill="#25313b" />'
        '</marker>'
        '</defs>'
    )

    dwg.append(rect(0, 0, width, height, fill=BACKGROUND))

    dwg.append(text(100, 80, data["title"], fill=INK, font_family=FONT_FAMILY,
                    font_size=38, font_weight="bold"))
    dwg.append(text(102, 120, data["subtitle"], fill=MUTED, font_family=FONT_FAMILY, font_size=18))

    dwg.append(rounded_rect(100, 165, width - 200, 60, 8, fill=WARNING_FILL,
                            stroke=WARNING_OUTLINE, stroke_width=2))
    dwg.append(text(122, 196, data["warning"], fill=WARNING_TEXT,
                    font_family=FONT_FAMILY, font_size=16, font_weight="bold"))

    anchors = {}
    for component in data["components"]:
        draw_component(dwg, component, anchors)
    draw_connections(dwg, data, anchors)
    draw_pins(dwg, data["components"])
    draw_legend(dwg, data["legend"])

    note_y = 830
    for note in data["notes"]:
        dwg.append(text(100, note_y, note, fill=MUTED, font_family=FONT_FAMILY, font_size=14))
        note_y += 28

    dwg.append("</svg>")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(dwg) + "\n", encoding="utf-8")
    print(f"Wrote {destination}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("yaml_file", nargs="?", type=Path,
                        default=Path(__file__).with_name("as5600-arduino-uno.yaml"))
    parser.add_argument("svg_file", nargs="?", type=Path,
                        default=Path(__file__).with_name("as5600-arduino-uno.svg"))
    args = parser.parse_args()
    render(args.yaml_file, args.svg_file)


if __name__ == "__main__":
    main()

