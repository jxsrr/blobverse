#!/usr/bin/env python3
"""
Restructure Oversee locations into continent -> region -> location hierarchy.

Usage:
    python3 scripts/restructure-locations.py --dry-run
    python3 scripts/restructure-locations.py --apply
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import quote

VAULT_ROOT = Path("/Users/mastff/Documents/Blobverse")
LOCATIONS_DIR = VAULT_ROOT / "Dungeon Master Notes" / "oversee" / "locations"
DM_NOTES_DIR = VAULT_ROOT / "Dungeon Master Notes"
REPORT_PATH = VAULT_ROOT / "restructure-report.md"
BRANCH_NAME = "restructure/locations-atlas"

# Directories to skip when scanning Dungeon Master Notes/ for href rewrites
SKIP_SCAN_DIRS = {".obsidian", "sonstige", "Dungeon Master ONLY", "Notes"}

# Authoritative move table (relative to Dungeon Master Notes/oversee/locations/)
FILE_MAP: dict[str, str] = {
    # ROOT -> continent hub README
    "Harka.md": "harka/README.md",
    "Elis.md": "elis/README.md",
    # ROOT -> parent-location hub README
    "Nesia Town.md": "harka/Nesia Town/README.md",
    "Padre Megalopolis.md": "harka/Padre Megalopolis/README.md",
    "Frosthaven Peak.md": "pirizia/Frosthaven Peak/README.md",
    "Maw Desert.md": "pirizia/Maw Desert/README.md",
    "Juto Port City.md": "rioquan/selatan/Juto Port City/README.md",
    # rioquan/utara leaves
    "Graen City.md": "rioquan/utara/Graen City.md",
    "Thainarv Port City.md": "rioquan/utara/Thainarv Port City.md",
    "Zundabun Borough.md": "rioquan/utara/Zundabun Borough.md",
    "Tarakita University of Heroism.md": "rioquan/utara/Tarakita University of Heroism.md",
    "Canyon of Lament.md": "rioquan/utara/Canyon of Lament.md",
    "Observatorium Danau Kuno.md": "rioquan/utara/Observatorium Danau Kuno.md",
    # rioquan/selatan leaves
    "Juto's Observatorium.md": "rioquan/selatan/Juto Port City/Juto's Observatorium.md",
    # harka leaves
    "Domido Forest.md": "harka/Domido Forest.md",
    "Dima Island.md": "harka/Dima Island.md",
    "Ghuffghuff Town.md": "harka/Ghuffghuff Town.md",
    "Greyland Castle.md": "harka/Greyland Castle.md",
    "Gudameng Town.md": "harka/Gudameng Town.md",
    "Javan Town.md": "harka/Javan Town.md",
    "Jestnut Valley.md": "harka/Jestnut Valley.md",
    "Mount Rayu.md": "harka/Mount Rayu.md",
    "Muangching Bay.md": "harka/Muangching Bay.md",
    "Whisper Place.md": "harka/Whisper Place.md",
    "Wind's Rest.md": "harka/Wind's Rest.md",
    "Yawning Town.md": "harka/Yawning Town.md",
    "The Golden Sheaf.md": "harka/Nesia Town/The Golden Sheaf.md",
    "Lyceum University of Arcane Arts.md": "harka/Padre Megalopolis/Lyceum University of Arcane Arts.md",
    # pirizia leaves
    "Garberro Forest.md": "pirizia/Garberro Forest.md",
    "Ironhold Borough.md": "pirizia/Ironhold Borough.md",
    "Kerajaan Grin.md": "pirizia/Kerajaan Grin.md",
    "The Spire of Whispering Ice.md": "pirizia/Frosthaven Peak/The Spire of Whispering Ice.md",
    "The Temple of Vythrax.md": "pirizia/Frosthaven Peak/The Temple of Vythrax.md",
    "Rune of the Cycle.md": "pirizia/Maw Desert/Rune of the Cycle.md",
    # elis leaves
    "Arbor's Observatorium.md": "elis/Arbor's Observatorium.md",
    "Arujaya Metropolis.md": "elis/Arujaya Metropolis.md",
    "Chenalia Town.md": "elis/Chenalia Town.md",
    "Cloud Prison.md": "elis/Cloud Prison.md",
    "Kuo Lau Kingdom.md": "elis/Kuo Lau Kingdom.md",
    "Miracle Cranny.md": "elis/Miracle Cranny.md",
    "The First Tree.md": "elis/The First Tree.md",
    "The Underground Ark.md": "elis/The Underground Ark.md",
}

# Authoritative URL rewrite table (exact match on href="..." values)
URL_MAP: dict[str, str] = {
    "/oversee/locations/Harka": "/oversee/locations/harka",
    "/oversee/locations/Elis": "/oversee/locations/elis",
    "/oversee/locations/Nesia%20Town": "/oversee/locations/harka/Nesia%20Town",
    "/oversee/locations/Padre%20Megalopolis": "/oversee/locations/harka/Padre%20Megalopolis",
    "/oversee/locations/Frosthaven%20Peak": "/oversee/locations/pirizia/Frosthaven%20Peak",
    "/oversee/locations/Maw%20Desert": "/oversee/locations/pirizia/Maw%20Desert",
    "/oversee/locations/Juto%20Port%20City": "/oversee/locations/rioquan/selatan/Juto%20Port%20City",
    "/oversee/locations/Graen%20City": "/oversee/locations/rioquan/utara/Graen%20City",
    "/oversee/locations/Thainarv%20Port%20City": "/oversee/locations/rioquan/utara/Thainarv%20Port%20City",
    "/oversee/locations/Zundabun%20Borough": "/oversee/locations/rioquan/utara/Zundabun%20Borough",
    "/oversee/locations/Tarakita%20University%20of%20Heroism": "/oversee/locations/rioquan/utara/Tarakita%20University%20of%20Heroism",
    "/oversee/locations/Canyon%20of%20Lament": "/oversee/locations/rioquan/utara/Canyon%20of%20Lament",
    "/oversee/locations/Observatorium%20Danau%20Kuno": "/oversee/locations/rioquan/utara/Observatorium%20Danau%20Kuno",
    "/oversee/locations/Juto%27s%20Observatorium": "/oversee/locations/rioquan/selatan/Juto%20Port%20City/Juto%27s%20Observatorium",
    "/oversee/locations/Domido%20Forest": "/oversee/locations/harka/Domido%20Forest",
    "/oversee/locations/Dima%20Island": "/oversee/locations/harka/Dima%20Island",
    "/oversee/locations/Ghuffghuff%20Town": "/oversee/locations/harka/Ghuffghuff%20Town",
    "/oversee/locations/Greyland%20Castle": "/oversee/locations/harka/Greyland%20Castle",
    "/oversee/locations/Gudameng%20Town": "/oversee/locations/harka/Gudameng%20Town",
    "/oversee/locations/Javan%20Town": "/oversee/locations/harka/Javan%20Town",
    "/oversee/locations/Jestnut%20Valley": "/oversee/locations/harka/Jestnut%20Valley",
    "/oversee/locations/Mount%20Rayu": "/oversee/locations/harka/Mount%20Rayu",
    "/oversee/locations/Muangching%20Bay": "/oversee/locations/harka/Muangching%20Bay",
    "/oversee/locations/Whisper%20Place": "/oversee/locations/harka/Whisper%20Place",
    "/oversee/locations/Wind%27s%20Rest": "/oversee/locations/harka/Wind%27s%20Rest",
    "/oversee/locations/Yawning%20Town": "/oversee/locations/harka/Yawning%20Town",
    "/oversee/locations/The%20Golden%20Sheaf": "/oversee/locations/harka/Nesia%20Town/The%20Golden%20Sheaf",
    "/oversee/locations/Lyceum%20University%20of%20Arcane%20Arts": "/oversee/locations/harka/Padre%20Megalopolis/Lyceum%20University%20of%20Arcane%20Arts",
    "/oversee/locations/Garberro%20Forest": "/oversee/locations/pirizia/Garberro%20Forest",
    "/oversee/locations/Ironhold%20Borough": "/oversee/locations/pirizia/Ironhold%20Borough",
    "/oversee/locations/Kerajaan%20Grin": "/oversee/locations/pirizia/Kerajaan%20Grin",
    "/oversee/locations/The%20Spire%20of%20Whispering%20Ice": "/oversee/locations/pirizia/Frosthaven%20Peak/The%20Spire%20of%20Whispering%20Ice",
    "/oversee/locations/The%20Temple%20of%20Vythrax": "/oversee/locations/pirizia/Frosthaven%20Peak/The%20Temple%20of%20Vythrax",
    "/oversee/locations/Rune%20of%20the%20Cycle": "/oversee/locations/pirizia/Maw%20Desert/Rune%20of%20the%20Cycle",
    "/oversee/locations/Arbor%27s%20Observatorium": "/oversee/locations/elis/Arbor%27s%20Observatorium",
    "/oversee/locations/Arujaya%20Metropolis": "/oversee/locations/elis/Arujaya%20Metropolis",
    "/oversee/locations/Chenalia%20Town": "/oversee/locations/elis/Chenalia%20Town",
    "/oversee/locations/Cloud%20Prison": "/oversee/locations/elis/Cloud%20Prison",
    "/oversee/locations/Kuo%20Lau%20Kingdom": "/oversee/locations/elis/Kuo%20Lau%20Kingdom",
    "/oversee/locations/Miracle%20Cranny": "/oversee/locations/elis/Miracle%20Cranny",
    "/oversee/locations/The%20First%20Tree": "/oversee/locations/elis/The%20First%20Tree",
    "/oversee/locations/The%20Underground%20Ark": "/oversee/locations/elis/The%20Underground%20Ark",
    # Root-orphan aliases -> canonical new paths
    "/Ghuffghuff": "/oversee/locations/harka/Ghuffghuff%20Town",
    "/Hutan%20Domido": "/oversee/locations/harka/Domido%20Forest",
    "/Padre%20City": "/oversee/locations/harka/Padre%20Megalopolis",
    "/Frostheart%20Village": "/oversee/locations/pirizia/Frosthaven%20Peak",
}

# Files that become folder READMEs (preserve all existing content verbatim)
FOLDER_README_SOURCES = {
    "Harka.md",
    "Elis.md",
    "Nesia Town.md",
    "Padre Megalopolis.md",
    "Frosthaven Peak.md",
    "Maw Desert.md",
    "Juto Port City.md",
}

# Files that receive an appended card grid at the bottom
APPEND_GRID_SOURCES = {"Harka.md", "Elis.md"}

ROOT_README_CONTENT = """---
layout: list
title: Locations
showSidebar: false
showToc: false
---

::pf
<div class="bv-sec-hero">
  <div class="bv-sec-kicker">OVERSEE · WORLD ATLAS</div>
  <div class="bv-sec-title">Locations</div>
  <p class="bv-sec-sub">Choose a continent to explore.</p>
</div>

<div class="bv-idx-grid">
  <a class="bv-idx-card" href="/oversee/locations/rioquan">
    <span class="bv-idx-tag">CONTINENT</span>
    <span class="bv-idx-name">Rioquan</span>
    <span class="bv-idx-meta">North &amp; South</span>
  </a>
  <a class="bv-idx-card" href="/oversee/locations/harka">
    <span class="bv-idx-tag">CONTINENT</span>
    <span class="bv-idx-name">Harka</span>
    <span class="bv-idx-meta">Commonwealth heartland</span>
  </a>
  <a class="bv-idx-card" href="/oversee/locations/pirizia">
    <span class="bv-idx-tag">CONTINENT</span>
    <span class="bv-idx-name">Pirizia</span>
    <span class="bv-idx-meta">Grin, Frosthaven, Maw</span>
  </a>
  <a class="bv-idx-card" href="/oversee/locations/elis">
    <span class="bv-idx-tag">CONTINENT</span>
    <span class="bv-idx-name">Elis</span>
    <span class="bv-idx-meta">The wild continent</span>
  </a>
</div>
::/pf
"""

RIOQUAN_README_CONTENT = """---
layout: list
title: Rioquan
showSidebar: false
showToc: false
---

::pf
<div class="bv-sec-hero">
  <div class="bv-sec-kicker">OVERSEE · RIOQUAN</div>
  <div class="bv-sec-title">Rioquan</div>
  <p class="bv-sec-sub">Choose a region to explore.</p>
</div>

<div class="bv-idx-grid">
  <a class="bv-idx-card" href="/oversee/locations/rioquan/utara">
    <span class="bv-idx-tag">REGION</span>
    <span class="bv-idx-name">Utara</span>
    <span class="bv-idx-meta">Northern Rioquan</span>
  </a>
  <a class="bv-idx-card" href="/oversee/locations/rioquan/selatan">
    <span class="bv-idx-tag">REGION</span>
    <span class="bv-idx-name">Selatan</span>
    <span class="bv-idx-meta">Southern Rioquan</span>
  </a>
</div>
::/pf
"""


class Ansi:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    DIM = "\033[2m"


def encode_url_segment(segment: str) -> str:
    """Encode path segment matching URL_MAP conventions (spaces -> %20, apostrophe -> %27)."""
    return quote(segment, safe="")


def build_card_grid(url_prefix: str, item_names: list[str]) -> str:
    """Build a sorted bv-idx-grid block for direct children of a hub folder."""
    cards: list[str] = ['<div class="bv-idx-grid">']
    for name in sorted(item_names, key=lambda s: s.lower()):
        encoded = encode_url_segment(name)
        cards.append(f'  <a class="bv-idx-card" href="{url_prefix}/{encoded}">')
        cards.append('    <span class="bv-idx-tag">LOCATION</span>')
        cards.append(f'    <span class="bv-idx-name">{name}</span>')
        cards.append('    <span class="bv-idx-meta"></span>')
        cards.append("  </a>")
    cards.append("</div>")
    return "\n".join(cards)


def build_leaf_hub_readme(title: str, kicker_label: str, url_prefix: str, item_names: list[str]) -> str:
    """Generate a new hub README with ::pf wrapper and card grid."""
    grid = build_card_grid(url_prefix, item_names)
    return (
        f"---\n"
        f"layout: list\n"
        f"title: {title}\n"
        f"showSidebar: false\n"
        f"showToc: false\n"
        f"---\n\n"
        f"::pf\n"
        f'<div class="bv-sec-hero">\n'
        f'  <div class="bv-sec-kicker">OVERSEE · {kicker_label.upper()}</div>\n'
        f'  <div class="bv-sec-title">{title}</div>\n'
        f"</div>\n\n"
        f"{grid}\n"
        f"::/pf\n"
    )


def get_new_hub_files() -> dict[str, str]:
    """Compute the 4 new hub README files and their generated contents."""
    utara_items = [
        Path(dst).stem
        for dst in FILE_MAP.values()
        if dst.startswith("rioquan/utara/") and not dst.endswith("/README.md")
    ]
    selatan_items = [
        "Juto Port City",
    ]
    pirizia_items = [
        "Garberro Forest",
        "Ironhold Borough",
        "Kerajaan Grin",
        "Frosthaven Peak",
        "Maw Desert",
    ]

    return {
        "rioquan/README.md": RIOQUAN_README_CONTENT,
        "rioquan/utara/README.md": build_leaf_hub_readme(
            title="Utara",
            kicker_label="UTARA",
            url_prefix="/oversee/locations/rioquan/utara",
            item_names=utara_items,
        ),
        "rioquan/selatan/README.md": build_leaf_hub_readme(
            title="Selatan",
            kicker_label="SELATAN",
            url_prefix="/oversee/locations/rioquan/selatan",
            item_names=selatan_items,
        ),
        "pirizia/README.md": build_leaf_hub_readme(
            title="Pirizia",
            kicker_label="PIRIZIA",
            url_prefix="/oversee/locations/pirizia",
            item_names=pirizia_items,
        ),
    }


def get_continent_appended_grid(src_name: str) -> str:
    """Build the appended card grid for Harka.md or Elis.md."""
    if src_name == "Harka.md":
        items = [
            "Domido Forest",
            "Dima Island",
            "Ghuffghuff Town",
            "Greyland Castle",
            "Gudameng Town",
            "Javan Town",
            "Jestnut Valley",
            "Mount Rayu",
            "Muangching Bay",
            "Whisper Place",
            "Wind's Rest",
            "Yawning Town",
            "Nesia Town",
            "Padre Megalopolis",
        ]
        return build_card_grid("/oversee/locations/harka", items)
    if src_name == "Elis.md":
        items = [
            "Arbor's Observatorium",
            "Arujaya Metropolis",
            "Chenalia Town",
            "Cloud Prison",
            "Kuo Lau Kingdom",
            "Miracle Cranny",
            "The First Tree",
            "The Underground Ark",
        ]
        return build_card_grid("/oversee/locations/elis", items)
    raise ValueError(f"Unexpected continent grid source: {src_name}")


def derive_metadata_for_target(src_filename: str, dst_rel_path: str) -> dict[str, str]:
    """Return required frontmatter keys for a moved file."""
    parts = Path(dst_rel_path).parts
    continent = parts[0]  # rioquan | harka | pirizia | elis
    title = Path(src_filename).stem
    meta: dict[str, str] = {
        "type": "Location",
        "universe": "Oversee",
        "continent": continent,
    }
    if continent == "rioquan":
        region_folder = parts[1]  # utara | selatan
        meta["region"] = region_folder.capitalize()
    meta["title"] = title
    return meta


def format_yaml_value(val: str) -> str:
    """Format a scalar YAML string safely if needed."""
    if any(ch in val for ch in (":", "#", "'", '"', "[", "]", "{", "}")):
        escaped = val.replace('"', '\\"')
        return f'"{escaped}"'
    return val


def update_frontmatter(
    content: str,
    src_filename: str,
    dst_rel_path: str,
) -> tuple[str, list[str]]:
    """
    Ensure required frontmatter keys exist without overwriting existing values,
    and normalize `type: Oversee location` / `type: Oversee Location` -> `type: Location`.
    """
    notes: list[str] = []

    if src_filename in FOLDER_README_SOURCES:
        return content, notes

    required = derive_metadata_for_target(src_filename, dst_rel_path)

    fm_match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", content, flags=re.DOTALL)
    if fm_match:
        fm_raw = fm_match.group(1)
        body = fm_match.group(2)
        fm_lines = fm_raw.splitlines()

        existing_keys: set[str] = set()
        new_fm_lines: list[str] = []

        for line in fm_lines:
            key_match = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
            if key_match:
                key = key_match.group(1)
                val = key_match.group(2).strip()
                existing_keys.add(key)

                if key == "type" and val.strip("\"'").lower() == "oversee location":
                    new_fm_lines.append("type: Location")
                    notes.append(f"{src_filename}: normalized `type: {val}` -> `type: Location`")
                    continue

            new_fm_lines.append(line)

        added_keys: list[str] = []
        for req_key, req_val in required.items():
            if req_key not in existing_keys:
                new_fm_lines.append(f"{req_key}: {format_yaml_value(req_val)}")
                added_keys.append(f"{req_key}={req_val}")

        if added_keys:
            notes.append(f"{src_filename}: added frontmatter ({', '.join(added_keys)})")

        rebuilt = "---\n" + "\n".join(new_fm_lines) + "\n---\n" + body
        return rebuilt, notes

    new_fm_lines = [f"{k}: {format_yaml_value(v)}" for k, v in required.items()]
    notes.append(f"{src_filename}: created frontmatter block ({', '.join(required.keys())})")
    rebuilt = "---\n" + "\n".join(new_fm_lines) + "\n---\n\n" + content
    return rebuilt, notes


def rewrite_hrefs_single_pass(text: str) -> tuple[str, dict[str, int]]:
    """
    Replace exact `href="<old_url>"` with `href="<new_url>"` in a single pass
    so chained rewrites cannot occur.
    """
    counts: dict[str, int] = {}
    lookup = {f'href="{old}"': (old, new) for old, new in URL_MAP.items()}
    pattern = re.compile("|".join(re.escape(k) for k in lookup))

    def _repl(match: re.Match[str]) -> str:
        matched_str = match.group(0)
        old_url, new_url = lookup[matched_str]
        label = f"{old_url} -> {new_url}"
        counts[label] = counts.get(label, 0) + 1
        return f'href="{new_url}"'

    updated = pattern.sub(_repl, text)
    return updated, counts


def iter_dm_markdown_files() -> list[Path]:
    """Yield all .md files in Dungeon Master Notes/, skipping excluded folders and backups."""
    md_files: list[Path] = []
    for path in sorted(DM_NOTES_DIR.rglob("*.md")):
        rel = path.relative_to(DM_NOTES_DIR)
        if any(part in SKIP_SCAN_DIRS or part.startswith("locations.bak-") for part in rel.parts):
            continue
        md_files.append(path)
    return md_files


def run_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=VAULT_ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def verify_git_safety(apply_mode: bool) -> None:
    """Enforce branch creation and clean working tree checks."""
    if not VAULT_ROOT.exists():
        sys.exit(f"{Ansi.RED}ERROR: Vault root not found: {VAULT_ROOT}{Ansi.RESET}")

    status_res = run_git(["status", "--short"])
    ignored_prefixes = (
        " M .obsidian/",
        "?? .obsidian/",
        "?? dryrun.log",
        "?? scripts/restructure-locations.py",
    )
    dirty_lines = [
        line
        for line in status_res.stdout.splitlines()
        if line.strip() and not line.startswith(ignored_prefixes)
    ]
    if dirty_lines:
        print(f"{Ansi.RED}ERROR: Working tree is not clean (excluding .obsidian/):{Ansi.RESET}")
        for line in dirty_lines:
            print(f"  {line}")
        sys.exit(1)

    branch_check = run_git(["rev-parse", "--verify", BRANCH_NAME], check=False)
    current_branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()

    if apply_mode:
        if branch_check.returncode == 0:
            sys.exit(
                f"{Ansi.RED}ERROR: Branch '{BRANCH_NAME}' already exists. "
                f"Aborting per safety protocol.{Ansi.RESET}"
            )
        run_git(["checkout", "-b", BRANCH_NAME])
        print(f"{Ansi.GREEN}Created and checked out branch: {BRANCH_NAME}{Ansi.RESET}")
    else:
        if branch_check.returncode == 0 and current_branch != BRANCH_NAME:
            print(
                f"{Ansi.YELLOW}WARNING (dry-run): Branch '{BRANCH_NAME}' already exists "
                f"(will abort on --apply unless removed).{Ansi.RESET}"
            )


def validate_paths() -> None:
    """Ensure all 42 source files exist and no target path already exists."""
    missing_sources: list[str] = []
    existing_targets: list[str] = []

    for src_rel, dst_rel in FILE_MAP.items():
        src_path = LOCATIONS_DIR / src_rel
        dst_path = LOCATIONS_DIR / dst_rel
        if not src_path.is_file():
            missing_sources.append(src_rel)
        if dst_path.exists():
            existing_targets.append(dst_rel)

    for hub_rel in get_new_hub_files():
        hub_path = LOCATIONS_DIR / hub_rel
        if hub_path.exists():
            existing_targets.append(hub_rel)

    if missing_sources:
        print(f"{Ansi.RED}ERROR: Missing source files in {LOCATIONS_DIR}:{Ansi.RESET}")
        for item in missing_sources:
            print(f"  - {item}")
        sys.exit(1)

    if existing_targets:
        print(f"{Ansi.RED}ERROR: Target path(s) already exist (refusing to overwrite):{Ansi.RESET}")
        for item in existing_targets:
            print(f"  - {item}")
        sys.exit(1)


def generate_report_markdown(
    moves: list[tuple[str, str]],
    new_files: dict[str, str],
    rewrites_by_file: dict[str, dict[str, int]],
    unresolved_location_hrefs: dict[str, list[str]],
    root_orphans_untouched: dict[str, list[str]],
    frontmatter_notes: list[str],
) -> str:
    lines: list[str] = [
        "# Oversee Locations Restructure Report",
        "",
        f"- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **Files moved:** {len(moves)}",
        f"- **New hub READMEs:** {len(new_files)}",
        f"- **Files with rewritten hrefs:** {len(rewrites_by_file)}",
        "",
        "## 1. Moves",
        "",
        "| Old Path | New Path |",
        "| --- | --- |",
    ]
    for old_p, new_p in moves:
        lines.append(f"| `oversee/locations/{old_p}` | `oversee/locations/{new_p}` |")

    lines.extend(["", "## 2. New Files", ""])
    lines.append(
        f"- `oversee/locations/README.md` (rewritten root chooser, {len(ROOT_README_CONTENT.splitlines())} lines)"
    )
    for rel_path, content in new_files.items():
        lines.append(f"- `oversee/locations/{rel_path}` ({len(content.splitlines())} lines)")

    lines.extend(["", "## 3. Rewrites by File", ""])
    if not rewrites_by_file:
        lines.append("_No href replacements needed._")
    else:
        for file_rel, repl_map in sorted(rewrites_by_file.items()):
            total_count = sum(repl_map.values())
            lines.append(f"### `{file_rel}` ({total_count} replacement{'s' if total_count != 1 else ''})")
            for repl_desc, cnt in sorted(repl_map.items()):
                lines.append(f"- `{repl_desc}` ({cnt}x)")
            lines.append("")

    lines.extend(["", "## 4. Unresolved Links (`/oversee/locations/...`)", ""])
    if not unresolved_location_hrefs:
        lines.append("_None — all `/oversee/locations/...` hrefs resolved cleanly._")
    else:
        for file_rel, hrefs in sorted(unresolved_location_hrefs.items()):
            for h in sorted(set(hrefs)):
                lines.append(f"- `{file_rel}`: `{h}`")

    lines.extend(["", "## 5. Root Orphans Untouched", ""])
    if not root_orphans_untouched:
        lines.append("_None found._")
    else:
        for file_rel, hrefs in sorted(root_orphans_untouched.items()):
            for h in sorted(set(hrefs)):
                lines.append(f"- `{file_rel}`: `{h}`")

    lines.extend(["", "## 6. Frontmatter Normalizations", ""])
    if not frontmatter_notes:
        lines.append("_No frontmatter changes required._")
    else:
        for note in frontmatter_notes:
            lines.append(f"- {note}")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Restructure Oversee locations into continent -> region -> location hierarchy."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Simulate restructure and print colored report without modifying files (default).",
    )
    group.add_argument(
        "--apply",
        action="store_true",
        help="Execute git moves, create hub READMEs, rewrite links, and write restructure-report.md.",
    )
    args = parser.parse_args()
    apply_mode = bool(args.apply)

    mode_banner = "APPLY MODE" if apply_mode else "DRY-RUN MODE (no files will be modified)"
    print(f"\n{Ansi.BOLD}{Ansi.CYAN}=== Oversee Locations Restructure [{mode_banner}] ==={Ansi.RESET}\n")

    verify_git_safety(apply_mode=apply_mode)
    validate_paths()

    new_hub_files = get_new_hub_files()

    if apply_mode:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir = LOCATIONS_DIR.parent / f"locations.bak-{timestamp}"
        shutil.copytree(LOCATIONS_DIR, backup_dir)
        print(f"{Ansi.GREEN}Created rollback backup:{Ansi.RESET} {backup_dir.relative_to(VAULT_ROOT)}")

    moves_list: list[tuple[str, str]] = list(FILE_MAP.items())
    frontmatter_notes: list[str] = []
    prepared_moved_contents: dict[str, str] = {}

    for src_rel, dst_rel in moves_list:
        src_path = LOCATIONS_DIR / src_rel
        raw_text = src_path.read_text(encoding="utf-8")

        updated_text, fm_notes = update_frontmatter(raw_text, src_rel, dst_rel)
        frontmatter_notes.extend(fm_notes)

        if src_rel in APPEND_GRID_SOURCES:
            grid_block = get_continent_appended_grid(src_rel)
            updated_text = updated_text.rstrip("\n") + "\n\n" + grid_block + "\n"
            frontmatter_notes.append(f"{src_rel} -> {dst_rel}: appended continent location card grid")

        prepared_moved_contents[dst_rel] = updated_text

    if apply_mode:
        for dst_rel in FILE_MAP.values():
            (LOCATIONS_DIR / dst_rel).parent.mkdir(parents=True, exist_ok=True)
        for hub_rel in new_hub_files:
            (LOCATIONS_DIR / hub_rel).parent.mkdir(parents=True, exist_ok=True)

        for src_rel, dst_rel in moves_list:
            src_repo_rel = str((LOCATIONS_DIR / src_rel).relative_to(VAULT_ROOT))
            dst_repo_rel = str((LOCATIONS_DIR / dst_rel).relative_to(VAULT_ROOT))
            run_git(["mv", src_repo_rel, dst_repo_rel])

        for dst_rel, final_text in prepared_moved_contents.items():
            (LOCATIONS_DIR / dst_rel).write_text(final_text, encoding="utf-8")

        (LOCATIONS_DIR / "README.md").write_text(ROOT_README_CONTENT, encoding="utf-8")

        for hub_rel, hub_content in new_hub_files.items():
            (LOCATIONS_DIR / hub_rel).write_text(hub_content, encoding="utf-8")

    valid_new_location_urls = {
        "/oversee/locations/README",
        "/oversee/locations/rioquan",
        "/oversee/locations/rioquan/utara",
        "/oversee/locations/rioquan/selatan",
        "/oversee/locations/harka",
        "/oversee/locations/pirizia",
        "/oversee/locations/elis",
        *URL_MAP.values(),
    }

    rewrites_by_file: dict[str, dict[str, int]] = {}
    unresolved_location_hrefs: dict[str, list[str]] = {}
    root_orphans_untouched: dict[str, list[str]] = {}

    virtual_contents: dict[Path, str] = {}
    if not apply_mode:
        for dst_rel, text in prepared_moved_contents.items():
            virtual_contents[LOCATIONS_DIR / dst_rel] = text
        virtual_contents[LOCATIONS_DIR / "README.md"] = ROOT_README_CONTENT
        for hub_rel, text in new_hub_files.items():
            virtual_contents[LOCATIONS_DIR / hub_rel] = text

        moved_src_paths = {LOCATIONS_DIR / src_rel for src_rel in FILE_MAP}
        scan_files = [
            p for p in iter_dm_markdown_files() if p not in moved_src_paths and p not in virtual_contents
        ] + sorted(virtual_contents.keys())
    else:
        scan_files = iter_dm_markdown_files()

    for md_path in scan_files:
        rel_str = str(md_path.relative_to(VAULT_ROOT))
        original_text = (
            virtual_contents[md_path] if md_path in virtual_contents else md_path.read_text(encoding="utf-8")
        )
        rewritten_text, repl_counts = rewrite_hrefs_single_pass(original_text)

        if repl_counts:
            rewrites_by_file[rel_str] = repl_counts
            if apply_mode:
                md_path.write_text(rewritten_text, encoding="utf-8")

        for match in re.finditer(r'href="([^"]+)"', rewritten_text):
            href_val = match.group(1)
            if href_val.startswith("/oversee/locations/") and href_val not in valid_new_location_urls:
                unresolved_location_hrefs.setdefault(rel_str, []).append(href_val)
            elif re.match(r"^/[^/]+$", href_val) and href_val not in URL_MAP:
                root_orphans_untouched.setdefault(rel_str, []).append(href_val)

    print(f"{Ansi.BOLD}{Ansi.BLUE}1. File Moves ({len(moves_list)}):{Ansi.RESET}")
    for src_rel, dst_rel in moves_list:
        print(f"  {Ansi.DIM}{src_rel}{Ansi.RESET} -> {Ansi.GREEN}{dst_rel}{Ansi.RESET}")

    print(f"\n{Ansi.BOLD}{Ansi.BLUE}2. Hub READMEs:{Ansi.RESET}")
    print(f"  {Ansi.YELLOW}REWRITE{Ansi.RESET} oversee/locations/README.md ({len(ROOT_README_CONTENT.splitlines())} lines)")
    for hub_rel, content in new_hub_files.items():
        print(f"  {Ansi.GREEN}NEW    {Ansi.RESET} oversee/locations/{hub_rel} ({len(content.splitlines())} lines)")

    total_replacements = sum(sum(m.values()) for m in rewrites_by_file.values())
    print(
        f"\n{Ansi.BOLD}{Ansi.BLUE}3. Href Rewrites ({total_replacements} across {len(rewrites_by_file)} files):{Ansi.RESET}"
    )
    for file_rel, repl_map in sorted(rewrites_by_file.items()):
        cnt = sum(repl_map.values())
        print(f"  {Ansi.CYAN}{file_rel}{Ansi.RESET} ({cnt})")
        for desc, c in sorted(repl_map.items()):
            print(f"    - {desc} ({c}x)")

    print(f"\n{Ansi.BOLD}{Ansi.BLUE}4. Frontmatter & Grid Updates ({len(frontmatter_notes)}):{Ansi.RESET}")
    for note in frontmatter_notes:
        print(f"  - {note}")

    if unresolved_location_hrefs:
        print(f"\n{Ansi.BOLD}{Ansi.YELLOW}5. Unresolved /oversee/locations/... Links:{Ansi.RESET}")
        for file_rel, hrefs in sorted(unresolved_location_hrefs.items()):
            for h in sorted(set(hrefs)):
                print(f"  - {file_rel}: {h}")

    if root_orphans_untouched:
        print(f"\n{Ansi.BOLD}{Ansi.YELLOW}6. Root Orphans Untouched:{Ansi.RESET}")
        for file_rel, hrefs in sorted(root_orphans_untouched.items()):
            for h in sorted(set(hrefs)):
                print(f"  - {file_rel}: {h}")

    report_md = generate_report_markdown(
        moves=moves_list,
        new_files=new_hub_files,
        rewrites_by_file=rewrites_by_file,
        unresolved_location_hrefs=unresolved_location_hrefs,
        root_orphans_untouched=root_orphans_untouched,
        frontmatter_notes=frontmatter_notes,
    )

    if apply_mode:
        REPORT_PATH.write_text(report_md, encoding="utf-8")
        print(f"\n{Ansi.BOLD}{Ansi.GREEN}Applied successfully! Report written to:{Ansi.RESET} {REPORT_PATH}")
    else:
        print(f"\n{Ansi.BOLD}{Ansi.YELLOW}Dry run complete. Run with --apply to execute changes.{Ansi.RESET}")


if __name__ == "__main__":
    main()
