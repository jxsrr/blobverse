"""Sync Dungeon Master Notes -> _player/Dungeon Master Notes, then resolve links.

Pipeline:
1. rsync source -> mirror (with --delete)
2. Strip DM-only content from every .md in mirror:
   - Cut from %% DM SECRETS %% / %% DM ONLY %% sentinel to EOF
   - Keep only content between ::pf ... ::/pf markers (drop markers)
   - Strip remaining %%...%% comments
3. Build basename lookup for wiki-link resolution
4. Rewrite short wiki-links to full paths
"""
import os
import re
import subprocess
from pathlib import Path

SRC = "Dungeon Master Notes"
MIRROR = "_player/Dungeon Master Notes"

DM_SENTINEL_RE = re.compile(
    r'^[ \t]*%%[ \t]*(DM SECRETS|DM ONLY)[ \t]*%%[ \t]*$',
    re.MULTILINE,
)
INLINE_COMMENT_RE = re.compile(r'%%.*?%%', re.DOTALL)


def split_frontmatter(text):
    if not text.startswith('---'):
        return '', text
    m = re.match(r'^---\r?\n(.*?)\r?\n---\r?\n', text, re.DOTALL)
    if not m:
        return '', text
    return m.group(0), text[m.end():]


def strip_dm_content(text):
    fm, body = split_frontmatter(text)

    # Cut from DM sentinel to EOF
    m = DM_SENTINEL_RE.search(body)
    if m:
        body = body[:m.start()]

    # Extract ::pf ... ::/pf content, drop markers
    if '::pf' in body:
        parts = []
        idx = 0
        while True:
            start = body.find('::pf', idx)
            if start == -1:
                break
            content_start = start + 4
            end = body.find('::/pf', content_start)
            if end == -1:
                parts.append(body[content_start:])
                break
            parts.append(body[content_start:end])
            idx = end + 5
        body = '\n'.join(p.strip() for p in parts if p.strip())

    # Strip any remaining %%...%% comments
    body = INLINE_COMMENT_RE.sub('', body)

    body = re.sub(r'\n{3,}', '\n\n', body).strip()

    if not body:
        return fm
    return fm + body + '\n'


def strip_mirror():
    mirror_path = Path(MIRROR)
    stripped = 0
    for root, _dirs, files in os.walk(mirror_path):
        for name in files:
            if not name.endswith(".md"):
                continue
            path = Path(root) / name
            text = path.read_text(encoding="utf-8")
            new_text = strip_dm_content(text)
            if new_text != text:
                path.write_text(new_text, encoding="utf-8")
                stripped += 1
    print(f"Stripped DM content from {stripped} file(s).")


# ---- Main pipeline ----

print(f"rsync {SRC}/ -> {MIRROR}/")
subprocess.run(
    ["rsync", "-a", "--delete", f"{SRC}/", f"{MIRROR}/"],
    check=True,
)

strip_mirror()

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
