#!/usr/bin/env python3
"""Build a Graphify PDF graph via Moss's OpenAI-compatible inference endpoint."""
import argparse
import json
import os
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credentials", required=True, help="private JSON with project_id/project_key")
    parser.add_argument("--book-dir", required=True, help="private folder containing only the book PDF")
    parser.add_argument("--out", required=True, help="private Graphify output folder; do not publish graph.json")
    args = parser.parse_args()
    creds = json.loads(Path(args.credentials).read_text())
    env = os.environ.copy()
    env.update({
        "OPENAI_API_KEY": creds["project_id"] + ":" + creds["project_key"],
        "OPENAI_BASE_URL": "https://inference.moss.dev/v1",
        "OPENAI_MODEL": "moss/fastlane-1",
    })
    command = [
        "graphify", "extract", args.book_dir,
        "--backend", "openai", "--model", "moss/fastlane-1",
        "--token-budget", "6000", "--max-concurrency", "2",
        "--out", args.out,
    ]
    raise SystemExit(subprocess.run(command, env=env, check=False).returncode)


if __name__ == "__main__":
    main()
