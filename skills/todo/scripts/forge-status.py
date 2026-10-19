#!/usr/bin/env python3
"""List open todos whose linked GitLab/GitHub issues, MRs and PRs are all closed or merged.

Output: one line per todo: "<todo path>\t<ref> <state>, <ref> <state>…"
"""
import os, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import forge

ROOT = pathlib.Path(os.environ.get("TODO_HOME", pathlib.Path.home() / "todos")).expanduser()

for f in sorted((ROOT / "todos/open").glob("*/todo.md")):
    states = []
    for url, *_ in forge.find(f.read_text()):
        item = forge.lookup(url)
        if item:
            states.append((item[0], item[2]))
    if states and all(s in ("closed", "merged") for _, s in states):
        print(f"{f.relative_to(ROOT)}\t" + ", ".join(f"{r} {s}" for r, s in states))
