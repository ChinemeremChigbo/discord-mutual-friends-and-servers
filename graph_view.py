import argparse
import json
import os
from pathlib import Path

import webview

from core import normalize_output_path


def build_graph(server_info: dict) -> dict:
    nodes = {}
    edges = set()

    def add_node(node_id: str, label: str, node_type: str) -> None:
        if node_id not in nodes:
            nodes[node_id] = {
                "id": node_id,
                "label": label,
                "type": node_type,
            }

    for server_name, members in server_info.items():
        server_id = f"server::{server_name}"
        add_node(server_id, server_name, "server")

        for member_name, details in members.items():
            member_id = f"user::{member_name}"
            add_node(member_id, member_name, "user")
            edges.add((member_id, server_id, "membership"))

            for mutual_server in details.get("mutual_servers", []):
                mutual_server_id = f"server::{mutual_server}"
                add_node(mutual_server_id, mutual_server, "server")
                edges.add((member_id, mutual_server_id, "mutual_server"))

            for mutual_friend in details.get("mutual_friends", []):
                mutual_friend_id = f"user::{mutual_friend}"
                add_node(mutual_friend_id, mutual_friend, "user")
                edges.add((member_id, mutual_friend_id, "mutual_friend"))

    node_degree = {node_id: 0 for node_id in nodes}
    for source, target, _edge_type in edges:
        if source in node_degree:
            node_degree[source] += 1
        if target in node_degree:
            node_degree[target] += 1

    node_list = []
    for node_id, payload in nodes.items():
        degree = node_degree.get(node_id, 0)
        node_list.append(
            {
                **payload,
                "size": max(6, min(18, 6 + degree)),
                "degree": degree,
            }
        )

    edge_list = [
        {"source": source, "target": target, "type": edge_type}
        for source, target, edge_type in edges
    ]

    return {
        "nodes": node_list,
        "edges": edge_list,
    }


class GraphApi:
    def __init__(self, output_path: str) -> None:
        self._output_path = output_path

    def get_graph(self):
        server_info_path = Path(self._output_path) / "server_info.json"
        if not server_info_path.exists():
            raise FileNotFoundError(
                "server_info.json not found. Run the scanner first to generate output."
            )
        with server_info_path.open("r") as handle:
            server_info = json.load(handle)
        return build_graph(server_info)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        "--output_path",
        default=None,
        help="Output path that contains server_info.json (default: ./output)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = normalize_output_path(args.output_path)

    html_path = Path(__file__).parent / "graph_ui" / "index.html"
    if not html_path.exists():
        raise FileNotFoundError("graph_ui/index.html not found.")

    api = GraphApi(output_path)
    webview.create_window(
        "Mutual Graph",
        html_path.resolve().as_uri(),
        js_api=api,
        width=1100,
        height=720,
    )
    webview.start()


if __name__ == "__main__":
    main()
