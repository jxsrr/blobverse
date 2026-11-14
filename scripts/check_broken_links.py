#!/usr/bin/env python3
"""
check_broken_links.py - audit wiki links di Dungeon Master Notes/.

Semantik publish-mirror.py (dikonfirmasi):
  ::pf ... ::/pf           = player-facing block. Marker di-strip, KONTEN
                             tetap dipublikasikan. Link di dalam HARUS dicek.
  %% DM SECRETS %% ... %%  = DM-only block. Seluruh block (marker + konten)
                             di-strip. Link di dalam TIDAK sampai Flowershow.
  ```...```                = fenced code block. Tidak dirender sebagai link.

Default   : scan ::pf + konten default, skip %% DM SECRETS %% + code fences.
--include-dm : scan semua, termasuk DM-only block.
--strict  : exit 1 jika ada broken/ambiguous (default warning-only, exit 0).
--quiet   : ringkasan count saja.

Resolve order per wikilink: exact path -> basename -> alias frontmatter.
"""
import sys
import re
import argparse
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "Dungeon Master Notes"
WHITELIST = ROOT / "scripts" / "broken_links_whitelist.txt"

WIKILINK_RE = re.compile(r"\[\[([^\]\|#]+)(?:#[^\|\]]+)?(?:\|([^\]]+))?\]\]")
FM_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def parse_aliases(text):
    m = FM_RE.search(text)
    if not m:
        return []
    fm = m.group(1)
    aliases = []
    in_aliases = False
    for line in fm.split("\n"):
        if re.match(r"^aliases\s*:\s*$", line):
            in_aliases = True
            continue
        if in_aliases:
            if re.match(r"^\s*-\s+", line):
                aliases.append(re.sub(r"^\s*-\s+", "", line).strip().strip("\"'"))
            elif re.match(r"^\S", line):
                in_aliases = False
    return aliases


def build_indexes():
    path_index = set()
    basename_index = defaultdict(list)
    alias_index = {}
    for f in SOURCE.rglob("*.md"):
        rel = f.relative_to(SOURCE).with_suffix("")
        rel_str = str(rel).replace("\\", "/")
        path_index.add(rel_str)
        basename_index[f.stem].append(rel_str)
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for alias in parse_aliases(text):
            if alias not in alias_index:
                alias_index[alias] = rel_str
    return path_index, dict(basename_index), alias_index


def iter_visible_lines(text, include_dm):
    """Yield (lineno, line) yang relevan untuk audit link."""
    lines = text.split("\n")
    if include_dm:
        for lineno, line in enumerate(lines, 1):
            yield lineno, line
        return

    in_code = False
    in_dm = False
    for lineno, line in enumerate(lines, 1):
        s = line.strip()

        if not in_code:
            if s == "%% DM SECRETS %%":
                in_dm = True
                continue
            if in_dm and s == "%%":
                in_dm = False
                continue

        if in_dm:
            continue

        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue

        yield lineno, line


def get_staged_source_files():
    """Set of absolute paths for staged .md under SOURCE (A/C/M/R only)."""
    import subprocess
    try:
        out = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR",
             "--", "Dungeon Master Notes/"],
            cwd=str(ROOT), text=True, stderr=subprocess.DEVNULL,
        )
    except Exception:
        return set()
    staged = set()
    for line in out.split("\n"):
        line = line.strip()
        if not line:
            continue
        staged.add((ROOT / line).resolve())
    return staged


def collect_links(include_dm, staged_files=None):
    links = []
    for f in SOURCE.rglob("*.md"):
        if staged_files is not None and f.resolve() not in staged_files:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        rel = str(f.relative_to(ROOT))
        for lineno, line in iter_visible_lines(text, include_dm):
            for m in WIKILINK_RE.finditer(line):
                target = m.group(1).strip()
                links.append((rel, lineno, target))
    return links


def resolve(target, path_index, basename_index, alias_index):
    # Normalisasi: link kadang pakai prefix vault "Dungeon Master Notes/"
    if target.startswith("Dungeon Master Notes/"):
        target = target[len("Dungeon Master Notes/"):]
    if target in path_index:
        return ("ok", target)
    if target in basename_index:
        hits = basename_index[target]
        if len(hits) == 1:
            return ("ok", hits[0])
        return ("ambiguous", hits)
    if target in alias_index:
        return ("ok", alias_index[target])
    return ("broken", None)


def load_whitelist():
    if not WHITELIST.exists():
        return set()
    out = set()
    for line in WHITELIST.read_text().split("\n"):
        s = line.strip()
        if s and not s.startswith("#"):
            out.add(s)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--include-dm", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--staged", action="store_true")
    args = ap.parse_args()

    staged_files = None
    if args.staged:
        staged_files = get_staged_source_files()
        if not staged_files:
            print("=== check_broken_links.py [STAGED] ===")
            print("No staged source files in Dungeon Master Notes/. SKIP.")
            return 0

    path_index, basename_index, alias_index = build_indexes()
    links = collect_links(include_dm=args.include_dm, staged_files=staged_files)
    whitelist = load_whitelist()

    broken = []
    ambiguous = []
    for src, lineno, target in links:
        status, info = resolve(target, path_index, basename_index, alias_index)
        if status == "ok":
            continue
        if status == "ambiguous":
            ambiguous.append((src, lineno, target, info))
            continue
        if target in whitelist:
            continue
        broken.append((src, lineno, target))

    if args.staged:
        scope = "STAGED" + ("+DM" if args.include_dm else "")
    else:
        scope = "INCLUDE-DM" if args.include_dm else "SKIP-DM (player-facing only)"
    n_files = len(list(SOURCE.rglob("*.md")))
    print(f"=== check_broken_links.py [{scope}] ===")
    print(f"Files scanned   : {n_files}")
    print(f"Links collected : {len(links)}")
    print(f"Whitelist       : {len(whitelist)} entry")

    if args.quiet:
        print(f"broken          : {len(broken)}")
        print(f"ambiguous       : {len(ambiguous)}")
    else:
        if ambiguous:
            print(f"\n!! AMBIGUOUS ({len(ambiguous)}):")
            for src, lineno, target, hits in ambiguous[:20]:
                print(f"   {src}:{lineno}  [[{target}]]  -> {len(hits)} kandidat")
            if len(ambiguous) > 20:
                print(f"   ... dan {len(ambiguous) - 20} lagi")
        if broken:
            print(f"\n!! BROKEN ({len(broken)}) - target tidak ditemukan:")
            for src, lineno, target in broken[:60]:
                print(f"   {src}:{lineno}  [[{target}]]")
            if len(broken) > 60:
                print(f"   ... dan {len(broken) - 60} lagi")
            print(f"\n   Whitelist: {WHITELIST.relative_to(ROOT)}")
        else:
            print("\nOK: tidak ada broken link.")

    if not broken and not ambiguous:
        print("PASS.")
        return 0
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
