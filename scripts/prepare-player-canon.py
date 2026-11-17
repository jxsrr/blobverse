#!/usr/bin/env python3
"""
Prepare Dungeon Master Notes/oversee/ for Player Facing Notes (_player/):
1. Keep ::pf ... ::/pf ONLY on entities encountered or mentioned (disebutkan) in Sessions 01-07.
2. Hide (strip ::pf / ::/pf) unvisited locations, unmet/DM-secret NPCs, duplicate aliases,
   and all cosmology / world-creation chronicles (canon/ OV0..OV6 & unrevealed lore/).
3. Strip cosmology/spoiler ::pf blocks inside partially-known ("disebutkan") entities
   so only session-known facts appear on the player website.
4. Scrub links inside ::pf blocks pointing to hidden pages (plain text for known names,
   [REDACTED] for DM-secret entities).
5. Delete non-English parenthetical glosses and standardize remaining Indonesian terms to English.

Usage:
    python3 scripts/prepare-player-canon.py --dry-run
    python3 scripts/prepare-player-canon.py --apply
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import re
from urllib.parse import unquote

VAULT_ROOT = Path("/Users/mastff/Documents/Blobverse")
OVERSEE_DIR = VAULT_ROOT / "Dungeon Master Notes" / "oversee"
SESSIONS_DIR = OVERSEE_DIR / "sessions"
REPORT_PATH = VAULT_ROOT / "player-canon-report.md"

TARGET_SUBDIRS = ("locations", "npcs", "items", "factions", "lore", "canon")

# Files that MUST be completely hidden from _player/ (DM secrets or duplicate aliases)
FORCE_HIDE = {
    "npcs/Kristine.md",        # Dr. Vektor DM secret
    "npcs/Mr. Basuki.md",      # Pak Basir DM secret
    "npcs/Mrs. Mamat.md",      # Duplicate of Bu Mamat.md
    "npcs/Sari.md",            # Duplicate of Ibu Sari.md
}

# Structural index/continent READMEs needed to browse canon sub-pages
ALWAYS_ALLOW_HUBS = {
    "locations/README.md",
    "locations/harka/README.md",
    "locations/rioquan/README.md",
    "locations/rioquan/selatan/README.md",
    "locations/pirizia/README.md",
    "locations/elis/README.md",
    "npcs/README.md",
    "items/README.md",
    "factions/README.md",
    "lore/README.md",
    "sessions/README.md",
}

# Entities mentioned (disebutkan) in sessions via lore/diaries/memories:
# Keep on website, but scrub any DM-secret/cosmology ::pf blocks inside them.
DISEBUTKAN_PARTIAL_ALLOW = {
    "npcs/Atlan Nouveau.md",
    "npcs/Reins.md",
    "npcs/Atreus Grin.md",
    "npcs/Olaf Guirela.md",
    "npcs/Guanik Wiseman.md",
    "npcs/Lei Alejandro.md",
    "npcs/Lei Firsa.md",
    "npcs/Gordon.md",
    "npcs/Zargoth.md",
    "npcs/Guo Lao.md",
    "npcs/Yayat Kopling.md",
    "npcs/Queen Ghaniba.md",
    "npcs/Guanik Dontol.md",
    "npcs/Gunnar Guirela.md",
    "npcs/Helius.md",
    "npcs/Crest.md",
    "npcs/Edra.md",
    "npcs/Vreina Arleschia.md",
    "lore/The Echoes.md",
    "lore/The Initial Six.md",
    "lore/The Triase.md",
    "lore/The Cycle Clan.md",
    "lore/The Great Disappearance.md",
}

# Keywords indicating unrevealed cosmology / DM-only secrets that must NOT leak into ::pf blocks
COSMOLOGY_SPOILER_RE = re.compile(
    r"\b("
    r"edisi\s+law|cycle\s+ritual|override\s+clause|cryo-?pod|seed\s+vault|"
    r"human\s+vessel\s+shell|vessel\s+shell|cipher\s+of\s+guilt|final\s+cipher|"
    r"1040\s*bv|before\s+oversee|age\s+of\s+knowledge|age\s+of\s+nurturing|"
    r"astrogeologist|third\s+observatorium|first\s+observatory|dm\s+secret|"
    r"stasis\s+tube|harvest\s+their\s+souls"
    r")\b",
    flags=re.IGNORECASE,
)

# Non-English cleanup rules (applied across oversee markdown files)
NON_ENGLISH_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    # Remove parenthetical Indonesian translations like (*Pegunungan Kabut*)
    (re.compile(r"\s*\(\*[A-Z][^*()]{2,50}\*\)"), ""),
    # Standardize remaining Indonesian entity/place names to English
    (re.compile(r"\bBahtera Bawah Tanah\b"), "The Underground Ark"),
    (re.compile(r"\bObservatorium Danau Kuno\b"), "Arbor's Observatorium"),
    (re.compile(r"\bUniversitas Tarakita\b"), "Tarakita University of Heroism"),
    (re.compile(r"\bKota Juto\b"), "Juto Port City"),
    (re.compile(r"\bPulau Dima\b"), "Dima Island"),
    (re.compile(r"\bHutan Domido\b"), "Domido Forest"),
    (re.compile(r"\bKerajaan Grin\b"), "Grin Kingdom"),
    (re.compile(r"\bKlan Frostscale\b"), "The Frostscale Clan"),
    (re.compile(r"\bKlan Lei\b"), "The Lei Clan"),
    (re.compile(r"\bGarda Besi\b"), "The Iron Guard"),
    (re.compile(r"\bBaja Hitam\b"), "Black Steel"),
    (re.compile(r"\bPemakaman Jiopa\b"), "Jiopa Cemetery"),
    (re.compile(r"\bBerkas Penelitian Cycle Clan\b"), "Cycle Clan Research File"),
    (re.compile(r"\*warung\*"), "food stall"),
    (re.compile(r"\bwarung\b"), "food stall"),
]


def clean_non_english(text: str) -> tuple[str, int]:
    """Delete parenthetical Indonesian glosses and standardize remaining Indonesian terms."""
    total_subs = 0
    for pattern, repl in NON_ENGLISH_REPLACEMENTS:
        text, n = pattern.subn(repl, text)
        total_subs += n
    return text, total_subs


def collect_session_canon() -> set[str]:
    """Collect all /oversee/... targets linked in Session 01..07."""
    canon_rel: set[str] = set(ALWAYS_ALLOW_HUBS) | DISEBUTKAN_PARTIAL_ALLOW

    for sf in sorted(SESSIONS_DIR.glob("Session 0[1-7]*.md")):
        text = sf.read_text(encoding="utf-8")
        for m in re.finditer(r'href="/oversee/([^"#?]+)"', text):
            sub = unquote(m.group(1)).strip("/")
            f_path = OVERSEE_DIR / f"{sub}.md"
            r_path = OVERSEE_DIR / sub / "README.md"
            if f_path.is_file():
                canon_rel.add(str(f_path.relative_to(OVERSEE_DIR)))
            elif r_path.is_file():
                canon_rel.add(str(r_path.relative_to(OVERSEE_DIR)))

    return canon_rel - FORCE_HIDE


def strip_all_pf_markers(text: str) -> tuple[str, int]:
    """Remove all ::pf and ::/pf markers from a file so it is hidden from _player/."""
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    removed = 0
    for line in lines:
        if line.strip() in ("::pf", "::/pf"):
            removed += 1
            continue
        out.append(line)
    return "".join(out), removed


def sanitize_pf_blocks(
    text: str,
    rel_str: str,
    canon_rel: set[str],
) -> tuple[str, list[str]]:
    """
    Inside ::pf ... ::/pf blocks of canon / disebutkan files:
    1. Drop any ::pf block that leaks cosmology / DM-secret spoilers.
    2. Remove index cards pointing to hidden pages.
    3. Replace inline <a href="...">label</a> pointing to hidden pages:
       - If target is in FORCE_HIDE (Kristine / Mr. Basuki) -> [REDACTED]
       - Otherwise -> plain text `label` (so prose reads naturally without dead links).
    """
    notes: list[str] = []
    is_partial = rel_str in DISEBUTKAN_PARTIAL_ALLOW

    def _is_target_visible(href: str) -> bool:
        if not href.startswith("/oversee/"):
            return False
        sub = unquote(href[len("/oversee/"):]).strip("/")
        if sub.startswith("pcs/") or sub.startswith("sessions/"):
            return True
        if f"{sub}.md" in canon_rel or f"{sub}/README.md" in canon_rel:
            return True
        return False

    def _process_block(m: re.Match[str]) -> str:
        full_block = m.group(0)
        inner = m.group(1)

        # Strip block if it contains cosmology / DM secret spoilers
        if COSMOLOGY_SPOILER_RE.search(inner):
            notes.append("Removed cosmology/spoiler ::pf block")
            return inner.strip("\n") + "\n"

        # For partial ("disebutkan") files, keep only concise dossier/overview blocks
        if is_partial and len(inner.splitlines()) > 18:
            notes.append("Trimmed extended lore ::pf block on 'disebutkan' entity")
            return inner.strip("\n") + "\n"

        # Remove hidden index cards
        def _card_repl(cm: re.Match[str]) -> str:
            href = cm.group(1)
            if _is_target_visible(href):
                return cm.group(0)
            notes.append(f"Removed hidden card -> {href}")
            return ""

        block = re.sub(
            r'\s*<a class="bv-idx-card" href="([^"]+)">.*?</a>',
            _card_repl,
            full_block,
            flags=re.DOTALL,
        )

        # Replace links to hidden pages with [REDACTED] (for secret NPCs) or plain label
        def _link_repl(lm: re.Match[str]) -> str:
            href = lm.group(1)
            label = lm.group(2)
            if _is_target_visible(href):
                return lm.group(0)
            decoded = unquote(href)
            if any(secret in decoded for secret in ("Kristine", "Basuki")):
                notes.append(f"Redacted secret link '{label}' ({href}) -> [REDACTED]")
                return "[REDACTED]"
            notes.append(f"Unlinked hidden page '{label}' ({href}) -> plain text")
            return label

        block = re.sub(
            r'<a\s+href="([^"]+)"[^>]*>(.*?)</a>',
            _link_repl,
            block,
            flags=re.DOTALL,
        )
        return block

    updated = re.sub(r"::pf\s*\n(.*?)\n::/pf", _process_block, text, flags=re.DOTALL)
    return updated, notes


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare Oversee notes for Player Facing Notes.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", default=True, help="Preview without modifying files.")
    mode.add_argument("--apply", action="store_true", help="Write changes to disk.")
    args = parser.parse_args()
    apply_mode = bool(args.apply)

    canon_rel = collect_session_canon()

    kept_full: list[str] = []
    kept_partial: list[str] = []
    hidden_list: list[tuple[str, str]] = []
    sanitized_log: dict[str, list[str]] = {}
    english_fixes_total = 0

    for subdir in TARGET_SUBDIRS:
        base = OVERSEE_DIR / subdir
        if not base.exists():
            continue
        for md_path in sorted(base.rglob("*.md")):
            rel_str = str(md_path.relative_to(OVERSEE_DIR))
            orig_text = md_path.read_text(encoding="utf-8")

            # Step A: Clean non-English terms
            text, eng_cnt = clean_non_english(orig_text)
            english_fixes_total += eng_cnt

            # Step B: Determine visibility
            is_cosmology_dir = subdir == "canon"
            is_visible = (not is_cosmology_dir) and (rel_str in canon_rel)

            if not is_visible:
                reason = (
                    "Cosmology / world chronicle (canon/)"
                    if is_cosmology_dir
                    else ("Forced DM-secret / duplicate hide" if rel_str in FORCE_HIDE else "Not yet mentioned in Sessions 01–07")
                )
                text, stripped = strip_all_pf_markers(text)
                hidden_list.append((rel_str, f"{reason} [stripped {stripped} ::pf tags]"))
            else:
                if rel_str in DISEBUTKAN_PARTIAL_ALLOW:
                    kept_partial.append(rel_str)
                else:
                    kept_full.append(rel_str)
                text, notes = sanitize_pf_blocks(text, rel_str, canon_rel)
                if notes:
                    sanitized_log[rel_str] = notes

            if apply_mode and text != orig_text:
                md_path.write_text(text, encoding="utf-8")

    # Also sanitize Session 01..07 prose & links
    for sf in sorted(SESSIONS_DIR.glob("Session 0[1-7]*.md")):
        rel_str = str(sf.relative_to(OVERSEE_DIR))
        orig_text = sf.read_text(encoding="utf-8")
        text, eng_cnt = clean_non_english(orig_text)
        english_fixes_total += eng_cnt
        text, notes = sanitize_pf_blocks(text, rel_str, canon_rel)
        if notes:
            sanitized_log[rel_str] = notes
        if apply_mode and text != orig_text:
            sf.write_text(text, encoding="utf-8")

    # Write concise report
    report = [
        "# Player-Facing Notes Preparation Report",
        "",
        f"- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **Mode:** {'APPLIED' if apply_mode else 'DRY-RUN'}",
        f"- **Full Canon files (`::pf` active):** {len(kept_full)}",
        f"- **Partial / 'Disebutkan' files (scoped `::pf`):** {len(kept_partial)}",
        f"- **Hidden / Cosmology / BELUM Canon (`::pf` stripped):** {len(hidden_list)}",
        f"- **Non-English replacements made:** {english_fixes_total}",
        "",
        "## Hidden Files (`::pf` Stripped)",
        *[f"- `{r}` — {why}" for r, why in hidden_list],
        "",
        "## Partial / 'Disebutkan' Files (Session-Known Facts Only)",
        *[f"- `{r}`" for r in kept_partial],
        "",
        "## Sanitized `::pf` Blocks & Unlinked Spoilers",
    ]
    for r, notes in sorted(sanitized_log.items()):
        report.append(f"- `{r}`: " + "; ".join(notes))

    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(
        f"[{'APPLIED' if apply_mode else 'DRY-RUN'}] "
        f"Full: {len(kept_full)} | Partial (disebutkan): {len(kept_partial)} | "
        f"Hidden: {len(hidden_list)} | Non-English fixes: {english_fixes_total}"
    )
    print(f"Report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
