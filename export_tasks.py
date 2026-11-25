#!/usr/bin/env python3
"""Export Moss task records, timeline traces and text outputs; never export keys/media."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

import requests

BASE = "https://inference.moss.dev/v1"
KEY_PATTERN = re.compile(r"moss_[0-9a-fA-F]{32}")


def clean_string(value, creds):
    value = value.replace(creds["project_key"], "[REDACTED_KEY]").replace(creds["project_id"], "[REDACTED_PROJECT_ID]")
    return KEY_PATTERN.sub("[REDACTED_KEY]", value)


def clean_url(url, creds):
    if not url:
        return None
    parts = urlsplit(url)
    # URLs may carry auth/search parameters; retain the location but not its query/fragment.
    return clean_string(urlunsplit((parts.scheme, parts.netloc, parts.path, "", "")), creds)


def sanitize(value, creds):
    if isinstance(value, dict):
        return {k: (clean_url(v, creds) if k == "url" and isinstance(v, str) else sanitize(v, creds)) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(item, creds) for item in value]
    if isinstance(value, str):
        return clean_string(value, creds)
    return value


def get(session, path, params=None):
    response = session.get(BASE + path, params=params, timeout=45)
    response.raise_for_status()
    return response.json()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--credentials", required=True, help="private JSON containing project_id/project_key")
    p.add_argument("--out", default="logs/tasks", help="sanitized output folder")
    args = p.parse_args()
    creds = json.loads(Path(args.credentials).read_text())
    root = Path(args.out)
    root.mkdir(parents=True, exist_ok=True)
    manifest = []
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {creds['project_id']}:{creds['project_key']}"})
    after = None
    seen = set()
    while True:
        page = get(session, "/tasks", {"limit": 50, **({"after": after} if after else {})})
        items = page.get("data", [])
        for item in items:
            task_id = item["id"]
            if task_id in seen:
                raise RuntimeError("Pagination repeated task " + task_id)
            seen.add(task_id)
            task = get(session, f"/tasks/{task_id}")
            trace = get(session, f"/tasks/{task_id}/trace")
            files = get(session, f"/tasks/{task_id}/files")
            target = root / task_id
            target.mkdir(exist_ok=True)
            # The task endpoint has the complete result, usage, and timestamps.
            (target / "task.json").write_text(json.dumps(sanitize(task, creds), ensure_ascii=False, indent=2) + "\n")
            (target / "trace.json").write_text(json.dumps(sanitize(trace, creds), ensure_ascii=False, indent=2) + "\n")
            (target / "files-manifest.json").write_text(json.dumps(sanitize(files, creds), ensure_ascii=False, indent=2) + "\n")
            downloads = []
            for entry in files.get("data", []):
                path = entry["path"]
                # Only small, agent-created textual outputs. Never dump screenshots or videos by default.
                if not path.startswith("outputs/") or not path.endswith((".md", ".csv", ".txt", ".json")) or entry.get("bytes", 0) > 200_000:
                    continue
                name = Path(path).name
                response = session.get(BASE + f"/tasks/{task_id}/files/{quote(path, safe='/')}", timeout=45)
                response.raise_for_status()
                content = clean_string(response.content.decode("utf-8", errors="replace"), creds)
                dest = target / "outputs" / name
                dest.parent.mkdir(exist_ok=True)
                dest.write_text(content)
                downloads.append(str(dest.relative_to(root)))
            manifest.append({"id": task_id, "title": task.get("title"), "status": task.get("status"), "created_at": task.get("created_at"), "steps": (task.get("usage") or {}).get("steps"), "timeline_events": len(trace.get("timeline") or []), "screenshots_listed": len(trace.get("screenshots") or []), "text_outputs": downloads})
            print(task_id, task.get("status"), "events", len(trace.get("timeline") or []), "text_outputs", len(downloads), flush=True)
        if not page.get("has_more"):
            if page.get("total") is not None and len(seen) != page["total"]:
                raise RuntimeError(f"Fetched {len(seen)} tasks but provider asserts {page['total']}")
            break
        if not items:
            raise RuntimeError("Provider says has_more with empty page")
        after = page.get("last_id") or items[-1]["id"]
    (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("Exported", len(manifest), "tasks to", root)


if __name__ == "__main__":
    main()
