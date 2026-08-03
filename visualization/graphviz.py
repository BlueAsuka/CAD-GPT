"""Render a design-graph JSON file as a dependency-free SVG."""

import argparse
import json
from collections import defaultdict
from html import escape
from pathlib import Path


BOX_W, BOX_H = 210, 58
COLORS = ("#dbeafe", "#dcfce7", "#fef3c7", "#f3e8ff", "#ffe4e6")


def box_edge(a, b):
    """Point where the line from box centre a toward b meets the box."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    scale = min(BOX_W / 2 / max(abs(dx), 1e-9), BOX_H / 2 / max(abs(dy), 1e-9))
    return a[0] + dx * scale, a[1] + dy * scale


def render(data):
    groups = defaultdict(list)
    for node in data["nodes"]:
        groups[node["type"]].append(node)

    preferred = ["housing_lower", "housing_lid", "bearing", "shaft", "spur_gear"]
    kinds = [kind for kind in preferred if kind in groups]
    kinds += [kind for kind in groups if kind not in kinds]
    width, row_gap, margin = 1200, 150, 70
    height = margin * 2 + row_gap * (len(kinds) - 1) + BOX_H
    positions, colours = {}, {}
    for row, kind in enumerate(kinds):
        nodes = groups[kind]
        y = margin + BOX_H / 2 + row * row_gap
        for col, node in enumerate(nodes, 1):
            positions[node["id"]] = (width * col / (len(nodes) + 1), y)
        colours[kind] = COLORS[row % len(COLORS)]

    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>
  text {{ font-family: system-ui, sans-serif; fill: #172033 }}
  .node-id {{ font-size: 14px; font-weight: 650 }}
  .node-type, .edge-label {{ font-size: 11px; fill: #566174 }}
  .edge {{ stroke: #748094; stroke-width: 1.7; fill: none; marker-end: url(#arrow) }}
</style>
<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#748094"/></marker></defs>
<text x="24" y="30" font-size="18" font-weight="700">{escape(data.get('graph_id', 'Design graph'))}</text>''']

    for edge in data.get("edges", []):
        source, target = positions[edge["source"]], positions[edge["target"]]
        start, end = box_edge(source, target), box_edge(target, source)
        mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
        relation = escape(edge.get("relation", ""))
        tooltip = escape(json.dumps(edge.get("attributes", {}), ensure_ascii=False))
        label_w = max(54, len(relation) * 6.5 + 12)
        parts.append(f'''<g><title>{tooltip}</title><line class="edge" x1="{start[0]:.1f}" y1="{start[1]:.1f}" x2="{end[0]:.1f}" y2="{end[1]:.1f}"/>
<rect x="{mx-label_w/2:.1f}" y="{my-11:.1f}" width="{label_w:.1f}" height="18" rx="5" fill="white" opacity=".92"/>
<text class="edge-label" x="{mx:.1f}" y="{my+2:.1f}" text-anchor="middle">{relation}</text></g>''')

    for node in data["nodes"]:
        x, y = positions[node["id"]]
        tooltip = escape(json.dumps(node.get("parameters", {}), ensure_ascii=False))
        parts.append(f'''<g><title>{tooltip}</title><rect x="{x-BOX_W/2:.1f}" y="{y-BOX_H/2:.1f}" width="{BOX_W}" height="{BOX_H}" rx="10" fill="{colours[node['type']]}" stroke="#6b7280"/>
<text class="node-id" x="{x:.1f}" y="{y-3:.1f}" text-anchor="middle">{escape(node['id'])}</text>
<text class="node-type" x="{x:.1f}" y="{y+16:.1f}" text-anchor="middle">{escape(node['type'])}</text></g>''')

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    default = root / "example" / "graph" / "single_stage_gearbox_graph.json"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_file", nargs="?", type=Path, default=default)
    parser.add_argument("-o", "--output", type=Path, help="output SVG path")
    args = parser.parse_args()

    graph = json.loads(args.json_file.read_text(encoding="utf-8"))
    output = args.output or args.json_file.with_suffix(".svg")
    output.write_text(render(graph), encoding="utf-8")
    print(output.resolve())
