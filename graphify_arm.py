#!/usr/bin/env python3
"""Graphify fifth arm: graphify query -> node facts -> Moss Inference (no Moss retrieval)."""
import argparse
import json
import re
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

from benchmark import QUESTIONS, do_request

NODE = re.compile(r"^NODE (.*?) \[src=")


def graph_context(graph_path, question, graph, max_nodes=8):
    start = time.perf_counter()
    cmd = ["graphify", "query", question, "--graph", str(graph_path), "--budget", "750"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(f"graphify query exited {proc.returncode}: {proc.stderr[:300]}")
    labels = []
    for line in proc.stdout.splitlines():
        match = NODE.match(line)
        if match and match.group(1) not in labels:
            labels.append(match.group(1))
    labels = labels[:max_nodes]
    by_label = {node["label"]: node for node in graph["nodes"]}
    selected = {by_label[x]["id"] for x in labels if x in by_label}
    lines = [f"{label}: {by_label[label].get('rationale') or 'No description'}" for label in labels if label in by_label]
    for edge in graph["links"]:
        if edge["source"] in selected and edge["target"] in selected:
            src = next((n["label"] for n in graph["nodes"] if n["id"] == edge["source"]), edge["source"])
            dst = next((n["label"] for n in graph["nodes"] if n["id"] == edge["target"]), edge["target"])
            lines.append(f"{src} --{edge['relation']}--> {dst}")
    return "\n".join(lines), labels, round((time.perf_counter() - start) * 1000, 2)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--credentials", required=True, help="private JSON; do not commit")
    p.add_argument("--graph", required=True, help="private graphify-out/graph.json")
    p.add_argument("--output", required=True)
    args = p.parse_args()
    creds = json.loads(Path(args.credentials).read_text())
    graph_path = Path(args.graph)
    graph = json.loads(graph_path.read_text())
    auth = creds["project_id"] + ":" + creds["project_key"]
    run_id = uuid.uuid4().hex
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with requests.Session() as session, out.open("w") as file:
        for case in QUESTIONS:
            context, labels, graph_ms = graph_context(graph_path, case["question"], graph)
            if not labels:
                raise RuntimeError("Graphify returned no nodes for " + case["id"])
            row = do_request(session, auth, case["question"], "graphify", [], 120, run_id, extra_context=context)
            row.update({"timestamp_utc": datetime.now(timezone.utc).isoformat(), "question_id": case["id"], "question": case["question"], "expected": case["expected"], "graph_query_ms": graph_ms, "graph_node_labels": labels, "graph_context_chars": len(context), "graph_nodes_total": len(graph["nodes"]), "graph_edges_total": len(graph["links"])})
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
            file.flush()
            print(case["id"], row["http_status"], row["response_status"], "input", (row.get("usage") or {}).get("input_tokens"), "first_ms", row["first_token_ms"], "total_ms", row["total_ms"], "graph_ms", graph_ms, flush=True)
    print("Saved", out)


if __name__ == "__main__":
    main()
