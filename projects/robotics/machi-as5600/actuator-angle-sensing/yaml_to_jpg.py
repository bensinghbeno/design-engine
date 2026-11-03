#!/usr/bin/env python3
"""Render the AS5600 wiring YAML file as a high-resolution JPG diagram."""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import yaml


SCALE = 3
BACKGROUND = "#fbfaf7"
INK = "#25313b"
MUTED = "#66737b"


def load_font(size, bold=False):
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size * SCALE)
    return ImageFont.load_default()


def scaled_point(x, y):
    return int(x * SCALE), int(y * SCALE)


def draw_component(draw, component, anchors):
    x, y = component["x"], component["y"]
    right = x + component["width"]
    bottom = y + component["height"]
    draw.rounded_rectangle(
        (*scaled_point(x, y), *scaled_point(right, bottom)),
        radius=12 * SCALE,
        fill=component["fill"],
        outline="#c4ccd0",
        width=2 * SCALE,
    )
    draw.rounded_rectangle(
        (*scaled_point(x, y), *scaled_point(right, y + 82)),
        radius=12 * SCALE,
        fill=component["accent"],
    )
    draw.rectangle(
        (*scaled_point(x, y + 48), *scaled_point(right, y + 82)),
        fill=component["accent"],
    )
    draw.text(scaled_point(x + 22, y + 16), component["label"], fill="#ffffff", font=load_font(23, bold=True))
    draw.text(scaled_point(x + 23, y + 51), component["subtitle"], fill="#e9eef0", font=load_font(13))

    for pin, details in component["pins"].items():
        px = x if details["side"] == "left" else right
        anchors[f"{component['id']}.{pin}"] = (px, y + details["y"])


def draw_connections(draw, data, anchors):
    colors = {item["kind"]: item["color"] for item in data["legend"]}
    for connection in data["connections"]:
        start = anchors[connection["from"]]
        end = anchors[connection["to"]]
        mid_x = (start[0] + end[0]) / 2
        route = [start, (mid_x, start[1]), (mid_x, end[1]), end]
        draw.line(
            [scaled_point(*coordinate) for coordinate in route],
            fill=colors[connection["kind"]],
            width=4 * SCALE,
            joint="curve",
        )


def draw_pins(draw, components):
    for component in components:
        x, y = component["x"], component["y"]
        right = x + component["width"]
        for pin, details in component["pins"].items():
            side = details["side"]
            px = x if side == "left" else right
            py = y + details["y"]
            draw.ellipse(
                (*scaled_point(px - 6, py - 6), *scaled_point(px + 6, py + 6)),
                fill="#ffffff",
                outline=INK,
                width=2 * SCALE,
            )
            label = details.get("label", pin)
            label_width = draw.textbbox((0, 0), label, font=load_font(15, bold=True))[2] / SCALE
            label_x = px + 18 if side == "left" else px - label_width - 18
            draw.text(scaled_point(label_x, py - 11), label, fill=INK, font=load_font(15, bold=True))


def draw_legend(draw, legend):
    x = 100
    y = 765
    for item in legend:
        draw.line(
            (*scaled_point(x, y + 10), *scaled_point(x + 38, y + 10)),
            fill=item["color"],
            width=5 * SCALE,
        )
        draw.text(scaled_point(x + 50, y), item["label"], fill=INK, font=load_font(15, bold=True))
        text_width = draw.textbbox((0, 0), item["label"], font=load_font(15, bold=True))[2] / SCALE
        x += 50 + text_width + 70


def render(source, destination):
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    width = data["canvas"]["width"]
    height = data["canvas"]["height"]
    image = Image.new("RGB", (width * SCALE, height * SCALE), BACKGROUND)
    draw = ImageDraw.Draw(image)

    draw.text(scaled_point(100, 52), data["title"], fill=INK, font=load_font(40, bold=True))
    draw.text(scaled_point(102, 112), data["subtitle"], fill=MUTED, font=load_font(19))
    draw.rounded_rectangle(
        (*scaled_point(100, 165), *scaled_point(width - 100, 225)),
        radius=8 * SCALE,
        fill="#fff0ec",
        outline="#d98573",
        width=2 * SCALE,
    )
    draw.text(scaled_point(122, 182), data["warning"], fill="#8e342b", font=load_font(17, bold=True))

    anchors = {}
    for component in data["components"]:
        draw_component(draw, component, anchors)
    draw_connections(draw, data, anchors)
    draw_pins(draw, data["components"])
    draw_legend(draw, data["legend"])

    note_y = 815
    for note in data["notes"]:
        draw.text(scaled_point(100, note_y), note, fill=MUTED, font=load_font(14))
        note_y += 28

    destination.parent.mkdir(parents=True, exist_ok=True)
    image.resize((width, height), Image.Resampling.LANCZOS).save(
        destination,
        format="JPEG",
        quality=96,
        subsampling=0,
        optimize=True,
        dpi=(300, 300),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("yaml_file", nargs="?", type=Path, default=Path(__file__).with_name("as5600-arduino-uno.yaml"))
    parser.add_argument("jpg_file", nargs="?", type=Path, default=Path(__file__).with_name("as5600-arduino-uno.jpg"))
    args = parser.parse_args()
    render(args.yaml_file, args.jpg_file)
    print(f"Wrote {args.jpg_file}")


if __name__ == "__main__":
    main()