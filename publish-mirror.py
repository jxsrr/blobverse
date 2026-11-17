"""Sync Dungeon Master Notes -> _player/Dungeon Master Notes, then resolve links.

Pipeline:
1. rsync source -> mirror (with --delete)
2. Strip DM-only content from every .md in mirror:
   - Cut from %% DM SECRETS %% / %% DM ONLY %% sentinel to EOF
   - Keep only content between ::pf ... ::/pf markers (drop markers)
   - Strip remaining %%...%% comments
3. Build basename + frontmatter alias lookup for wiki-link resolution
4. Rewrite short/alias wiki-links to full paths (and Markdown links when apostrophe is present)
"""
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import quote

SRC = "Dungeon Master Notes"
MIRROR = "_player/Dungeon Master Notes"

DM_SENTINEL_RE = re.compile(
    r'^[ \t]*%%[ \t]*(DM SECRETS|DM ONLY)[ \t]*%%[ \t]*$',
    re.MULTILINE,
)
INLINE_COMMENT_RE = re.compile(r'%%.*?%%', re.DOTALL)

SAFE_PLAYER_FRONTMATTER = {
    "oversee/npcs/Reins.md": """---
type: Oversee NPC
role: Ama's Lost Friend, Atlan's Wife, Mira's Mother
faction: Known through Atlan's Diary
home: Unknown
status: Unknown
first_seen: Session 02 (via Atlan's Diary)
universe: Oversee
---
""",
    "oversee/npcs/Zargoth.md": """---
type: Oversee NPC
role: Ancient Demon Associated with the Gap
faction: Unknown
home: Unknown
status: Associated with the curse affecting HVS
first_seen: Session 06
universe: Oversee
---
""",
    "oversee/npcs/Olaf Guirela.md": """---
type: Oversee NPC
role: Ranger of the Initial Six, Gordon's Teacher
faction: The Initial Six
home: Whisper Place (formerly)
status: Deceased; known through memory
first_seen: Session 02 (mentioned), Session 05 (memory)
universe: Oversee
---
""",
}


def apply_safe_player_frontmatter(rel_path, text):
    safe_fm = SAFE_PLAYER_FRONTMATTER.get(rel_path)
    if not safe_fm:
        return text

    _old_fm, body = split_frontmatter(text)
    return safe_fm + body

FM_RE = re.compile(r'^---\r?\n(.*?)\r?\n---\r?\n', re.DOTALL)


def split_frontmatter(text):
    if not text.startswith('---'):
        return '', text
    m = FM_RE.match(text)
    if not m:
        return '', text
    return m.group(0), text[m.end():]


def parse_aliases(fm_block):
    if not fm_block:
        return []
    m = FM_RE.match(fm_block)
    if not m:
        return []
    fm = m.group(1)
    aliases = []
    in_aliases = False
    for line in fm.splitlines():
        if re.match(r'^aliases\s*:\s*$', line):
            in_aliases = True
            continue
        if in_aliases:
            if re.match(r'^\s*-\s+', line):
                aliases.append(re.sub(r'^\s*-\s+', '', line).strip().strip("\"'"))
            elif re.match(r'^\S', line):
                in_aliases = False
    return aliases


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
    removed = 0
    for root, _dirs, files in os.walk(mirror_path):
        for name in files:
            if not name.endswith(".md"):
                continue
            path = Path(root) / name
            text = path.read_text(encoding="utf-8")
            fm, body = split_frontmatter(text)
            # Exclude files explicitly marked publish: false or oversee lore/entity files with zero ::pf blocks
            rel_str = str(path.relative_to(mirror_path)).replace("\\", "/")
            is_unpublished = bool(re.search(r"^publish\s*:\s*false\s*$", fm, flags=re.M))
            is_gated_oversee_doc = (
                rel_str.startswith(("oversee/canon/", "oversee/sessions/", "oversee/locations/", "oversee/npcs/", "oversee/items/", "oversee/factions/", "oversee/lore/"))
                and "::pf" not in body
            )
            if is_unpublished or is_gated_oversee_doc:
                path.unlink()
                removed += 1
                continue
            new_text = strip_dm_content(text)
            new_text = apply_safe_player_frontmatter(rel_str, new_text)
            if new_text != text:
                path.write_text(new_text, encoding="utf-8")
                stripped += 1
    # Prune empty directories so hidden sections (like canon/ or rioquan/utara/) vanish from sidebar
    for root, dirs, files in os.walk(mirror_path, topdown=False):
        p = Path(root)
        if p != mirror_path and not any(p.iterdir()):
            p.rmdir()
    print(f"Stripped DM content from {stripped} file(s); excluded {removed} non-canon/hidden file(s).")


# ---- Main pipeline ----

print(f"rsync {SRC}/ -> {MIRROR}/")
subprocess.run(
    ["rsync", "-a", "--delete", f"{SRC}/", f"{MIRROR}/"],
    check=True,
)

strip_mirror()

mirror_path = Path(MIRROR)
path_set = set()
lookup = {}
alias_lookup = {}

for root, _dirs, files in sorted(os.walk(mirror_path)):
    for name in sorted(files):
        if not name.endswith(".md"):
            continue
        full_path = Path(root) / name
        rel = full_path.relative_to(mirror_path)
        rel_str = str(rel.with_suffix("")).replace("\\", "/")
        path_set.add(rel_str)
        lookup.setdefault(rel.stem, []).append(rel_str)

        fm, _ = split_frontmatter(full_path.read_text(encoding="utf-8"))
        for alias in parse_aliases(fm):
            if alias and alias not in alias_lookup:
                alias_lookup[alias] = rel_str

ambiguous = {k: v for k, v in lookup.items() if len(v) > 1}
if ambiguous:
    print("Ambiguous basenames (first picked — fix manually if needed):")
    for name, paths in sorted(ambiguous.items()):
        print(f"  {name!r} -> {paths}")
    print()

link_re = re.compile(r'(!?)\[\[([^\]|#]+)(#[^\]|]+)?(?:\|([^\]]+))?\]\]')


def format_output(embed, resolved_path, anchor, label, fallback_label):
    anchor = anchor or ""
    display = label or fallback_label
    # Flowershow truncates wikilinks containing ASCII apostrophes into '&'
    if not embed and "'" in resolved_path:
        encoded_path = "/".join(quote(seg, safe="") for seg in resolved_path.split("/"))
        encoded_anchor = "#" + quote(anchor[1:], safe="") if anchor else ""
        return f"[{display}](/{encoded_path}{encoded_anchor})"
    target_full = f"{resolved_path}{anchor}"
    return f"{embed}[[{target_full}|{label}]]" if label else f"{embed}[[{target_full}]]"


def rewrite_link(m):
    embed, raw_target, anchor, alias = m.group(1), m.group(2).strip(), m.group(3), m.group(4)
    original = m.group(0)

    target = raw_target
    for prefix in ("_player/Dungeon Master Notes/", "Dungeon Master Notes/"):
        if target.startswith(prefix):
            target = target[len(prefix):]

    if target.startswith("http"):
        return original

    # 1. Exact path match
    if target in path_set:
        fallback = Path(target).name
        return format_output(embed, target, anchor, alias, fallback)

    # 2. If it already contains '/' (e.g. relative asset or path), preserve or encode apostrophe
    if "/" in target:
        fallback = Path(target).name
        return format_output(embed, target, anchor, alias, fallback)

    # 3. Basename match
    candidates = lookup.get(target, [])
    if candidates:
        return format_output(embed, candidates[0], anchor, alias, target)

    # 4. Frontmatter alias match
    if target in alias_lookup:
        return format_output(embed, alias_lookup[target], anchor, alias, target)

    # 5. Unresolved non-embed link (e.g., future/unwritten session) -> plain text
    if not embed:
        return alias.strip() if alias else target

    return original


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
