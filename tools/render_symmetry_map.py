from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass
class Node:
    node_id: str
    label: str
    parent: Optional[str]
    status: Optional[str] = None
    match: Optional[List[dict]] = None
    status_if_missing: Optional[str] = None


STATUS_STYLE = {
    "found": {"fill": "#2e7d32", "stroke": "#1b5e20", "text": "#ffffff"},
    "explored": {"fill": "#f9a825", "stroke": "#f57f17", "text": "#000000"},
    "unknown": {"fill": "#90a4ae", "stroke": "#546e7a", "text": "#000000"},
}


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def read_nodes(path: str) -> List[Node]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    nodes = []
    for item in data.get("nodes", []):
        nodes.append(
            Node(
                node_id=item["id"],
                label=item["label"],
                parent=item.get("parent"),
                status=item.get("status"),
                match=item.get("match"),
                status_if_missing=item.get("status_if_missing"),
            )
        )
    return nodes


def load_records(path: str) -> List[dict]:
    if not os.path.exists(path):
        return []
    records = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def get_field(record: dict, field: str):
    parts = field.split(".")
    current = record
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def record_matches(record: dict, rule: dict) -> bool:
    value = get_field(record, rule["field"])
    if "equals" in rule:
        return value == rule["equals"]
    if "in" in rule:
        return value in rule["in"]
    if "contains" in rule and isinstance(value, str):
        return rule["contains"] in value
    return False


def evaluate_status(nodes: List[Node], results_dir: str) -> Dict[str, str]:
    file_cache: Dict[str, List[dict]] = {}
    status = {}
    for node in nodes:
        if node.status:
            status[node.node_id] = node.status
            continue
        found = False
        if node.match:
            for rule in node.match:
                for file_path in rule.get("files", []):
                    path = os.path.join(results_dir, os.path.basename(file_path))
                    if path not in file_cache:
                        file_cache[path] = load_records(path)
                    for rec in file_cache[path]:
                        if record_matches(rec, rule):
                            found = True
                            break
                    if found:
                        break
                if found:
                    break
        if found:
            status[node.node_id] = "found"
        else:
            status[node.node_id] = node.status_if_missing or "unknown"
    return status


def build_tree(nodes: List[Node]) -> Tuple[Dict[str, Node], Dict[str, List[str]], List[str]]:
    node_map = {node.node_id: node for node in nodes}
    children: Dict[str, List[str]] = {node.node_id: [] for node in nodes}
    roots = []
    for node in nodes:
        if node.parent is None:
            roots.append(node.node_id)
        else:
            children[node.parent].append(node.node_id)
    return node_map, children, roots


def compute_widths(
    node_id: str,
    children: Dict[str, List[str]],
    node_w: int,
    h_spacing: int,
    widths: Dict[str, int],
) -> int:
    if not children[node_id]:
        widths[node_id] = node_w
        return node_w
    child_widths = [
        compute_widths(child, children, node_w, h_spacing, widths) for child in children[node_id]
    ]
    total = sum(child_widths) + h_spacing * (len(child_widths) - 1)
    widths[node_id] = max(node_w, total)
    return widths[node_id]


def assign_positions(
    node_id: str,
    children: Dict[str, List[str]],
    widths: Dict[str, int],
    node_w: int,
    node_h: int,
    h_spacing: int,
    v_spacing: int,
    x0: int,
    y0: int,
    positions: Dict[str, Tuple[int, int]],
) -> None:
    x_center = x0 + widths[node_id] // 2
    positions[node_id] = (x_center, y0)
    if not children[node_id]:
        return
    cursor = x0
    for child in children[node_id]:
        assign_positions(
            child,
            children,
            widths,
            node_w,
            node_h,
            h_spacing,
            v_spacing,
            cursor,
            y0 + node_h + v_spacing,
            positions,
        )
        cursor += widths[child] + h_spacing


def render_svg(
    nodes: List[Node],
    positions: Dict[str, Tuple[int, int]],
    children: Dict[str, List[str]],
    status: Dict[str, str],
    output_path: str,
) -> None:
    node_w = 220
    node_h = 36
    margin = 40
    legend_h = 80

    max_x = max(x for x, _y in positions.values()) + node_w // 2
    max_y = max(y for _x, y in positions.values()) + node_h
    width = max_x + margin
    height = max_y + margin + legend_h

    lines = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>",
        "<rect width='100%' height='100%' fill='#f5f7fa'/>",
        "<g font-family='Helvetica, Arial, sans-serif' font-size='12'>",
    ]

    # edges
    for parent, kids in children.items():
        px, py = positions[parent]
        for child in kids:
            cx, cy = positions[child]
            lines.append(
                "<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' "
                "stroke='#90a4ae' stroke-width='1.5'/>".format(
                    x1=px,
                    y1=py + node_h,
                    x2=cx,
                    y2=cy,
                )
            )

    # nodes
    for node in nodes:
        x, y = positions[node.node_id]
        s = status.get(node.node_id, "unknown")
        style = STATUS_STYLE.get(s, STATUS_STYLE["unknown"])
        x0 = x - node_w // 2
        y0 = y
        label = escape_xml(node.label)
        lines.append(
            "<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='6' ry='6' "
            "fill='{fill}' stroke='{stroke}' stroke-width='1.5'/>".format(
                x=x0,
                y=y0,
                w=node_w,
                h=node_h,
                fill=style["fill"],
                stroke=style["stroke"],
            )
        )
        lines.append(
            "<text x='{x}' y='{y}' fill='{fill}' text-anchor='middle' dominant-baseline='middle'>"
            "{label}</text>".format(
                x=x,
                y=y0 + node_h / 2,
                fill=style["text"],
                label=label,
            )
        )

    # legend
    legend_x = margin
    legend_y = max_y + margin
    lines.append("<text x='{x}' y='{y}' font-size='14'>Legend</text>".format(x=legend_x, y=legend_y))
    legend_items = [("found", "Found from first principles"), ("explored", "Explored"), ("unknown", "Unknown")]
    offset = 20
    for key, label in legend_items:
        style = STATUS_STYLE[key]
        lines.append(
            "<rect x='{x}' y='{y}' width='16' height='16' rx='3' ry='3' fill='{fill}' stroke='{stroke}'/>".format(
                x=legend_x,
                y=legend_y + offset,
                fill=style["fill"],
                stroke=style["stroke"],
            )
        )
        lines.append(
            "<text x='{x}' y='{y}' font-size='12' dominant-baseline='middle'>{label}</text>".format(
                x=legend_x + 24,
                y=legend_y + offset + 8,
                label=escape_xml(label),
            )
        )
        offset += 22

    lines.append("</g></svg>")
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="docs/symmetry_map.json")
    parser.add_argument("--results", default="results")
    parser.add_argument("--output", default="docs/symmetry_map.svg")
    args = parser.parse_args(argv)

    nodes = read_nodes(args.input)
    status = evaluate_status(nodes, args.results)
    node_map, children, roots = build_tree(nodes)

    node_w = 220
    h_spacing = 40
    widths: Dict[str, int] = {}
    for root in roots:
        compute_widths(root, children, node_w, h_spacing, widths)

    positions: Dict[str, Tuple[int, int]] = {}
    x_cursor = 40
    for root in roots:
        assign_positions(
            root,
            children,
            widths,
            node_w,
            36,
            h_spacing,
            80,
            x_cursor,
            40,
            positions,
        )
        x_cursor += widths[root] + h_spacing

    render_svg(nodes, positions, children, status, args.output)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
