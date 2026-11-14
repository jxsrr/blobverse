"""Sync Dungeon Master Notes -> _player/Dungeon Master Notes, then resolve links.

Use this INSTEAD of the Publish with Flowershow plugin when publishing via Git.
"""
import os
import re
import subprocess
from pathlib import Path

SRC = "Dungeon Master Notes"
MIRROR = "_player/Dungeon Master Notes"

print(f"rsync {SRC}/ -> {MIRROR}/")
subprocess.run(
    ["rsync", "-a", "--delete", f"{SRC}/", f"{MIRROR}/"],
    check=True,
)

mirror_path = Path(MIRROR)
lookup = {}
for root, _dirs, files in os.walk(mirror_path):
    for name in files:
        if not name.endswith(".md"):
            continue
        rel = Path(root).joinpath(name).relative_to(mirror_path)
        lookup.setdefault(rel.stem, []).append(str(rel.with_suffix("")))

ambiguous = {k: v for k, v in lookup.items() if len(v) > 1}
if ambiguous:
    print("Ambiguous basenames (first picked — fix manually if needed):")
    for name, paths in sorted(ambiguous.items()):
        print(f"  {name!r} -> {paths}")
    print()

link_re = re.compile(r'(!?)\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')

def rewrite_link(m):
    embed, target, alias = m.group(1), m.group(2).strip(), m.group(3)
    original = m.group(0)

    if target.startswith("_player/Dungeon Master Notes/"):
        target = target[len("_player/Dungeon Master Notes/"):]

    if "/" in target or target.startswith("http"):
        return f"{embed}[[{target}|{alias}]]" if alias else f"{embed}[[{target}]]"

    candidates = lookup.get(target, [])
    if not candidates:
        return original

    resolved = candidates[0]
    return f"{embed}[[{resolved}|{alias}]]" if alias else f"{embed}[[{resolved}]]"

changed = 0
for root, _dirs, files in os.walk(mirror_path):
    for name in files:
        if not name.endswith(".md"):
            continue
        path = Path(root) / name
        text = path.read_text(encoding="utf-8")
        new_text = link_re.sub(rewrite_link, text)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            changed += 1

print(f"Resolved links in {changed} file(s).")
