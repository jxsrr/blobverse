#!/usr/bin/env python3
"""Batch-populate category README.md files across the Blobverse DM vault.

Safe by default: creates .bak siblings, --dry-run previews without writing.
Does NOT git-commit — run `git diff` after, then your pre-commit pipeline.

Usage:
    python3 scripts/populate-readmes.py --dry-run
    python3 scripts/populate-readmes.py
    python3 scripts/populate-readmes.py --only oversee/
    python3 scripts/populate-readmes.py --no-backup
    python3 scripts/populate-readmes.py --include-endgame-lore
"""

from __future__ import annotations
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DM = ROOT / "Dungeon Master Notes"

# ---------- link helpers ----------

def L(target: str, label: str | None = None) -> str:
    return f"[[{target}|{label or target.rsplit('/', 1)[-1]}]]"

def sec(title: str, targets: list[str]) -> str:
    """Section with links auto-labelled from the filename."""
    return "## " + title + "\n" + "\n".join(f"- {L(t)}" for t in targets)

def sec_named(title: str, pairs: list[tuple[str, str]]) -> str:
    """Section with explicit labels."""
    return "## " + title + "\n" + "\n".join(f"- {L(t, lbl)}" for t, lbl in pairs)

def sec_desc(title: str, pairs: list[tuple[str, str]]) -> str:
    """Section with auto-label + em-dash description."""
    return "## " + title + "\n" + "\n".join(f"- {L(t)} — {d}" for t, d in pairs)

# ---------- gated endgame lore (off by default) ----------

ENDGAME_LORE = [
    "oversee/lore/The Overseer & The Architect",
    "oversee/lore/The Gap-Touched",
    "oversee/lore/The Cult of the Giant Humanoid",
    "oversee/lore/The Endgame Paths",
    "oversee/lore/The Rapture",
]

# ---------- specs ----------

def build_specs(include_endgame_lore: bool) -> dict[str, str]:
    specs: dict[str, str] = {}

    # =========================================================
    # OVERSEE
    # =========================================================

    specs["oversee/README.md"] = f"""---
layout: list
title: Oversee
---

The main campaign. From the Yawning Town to the Spire of Whispering Ice and beyond.

> [!teaser] Previously...
> The Five Sticks escaped Arujaya with [[oversee/npcs/Lei Livia Vane|Livia]] as hostage. Syl saw something beyond the veil — the Overseer itself. [[oversee/npcs/Lei Darvin Thorne|Darvin]] is Valerius's twin, and the "crazy old man" carries the true power of Lei Roiga. Somewhere in the deep, Echo Gzirmo waits.

## Start Here
- **Latest recap:** {L("oversee/sessions/Session 07 — Opressed")}

{sec_named("Browse the Wiki", [
    ("oversee/canon/README", "Timeline"),
    ("oversee/locations/README", "Locations"),
    ("oversee/npcs/README", "NPCs"),
    ("oversee/factions/README", "Factions"),
    ("oversee/lore/README", "Lore"),
    ("oversee/items/README", "Items"),
    ("oversee/handouts/README", "Handouts"),
    ("oversee/pcs/README", "PCs"),
    ("oversee/sessions/README", "Sessions"),
])}

{sec_desc("The Party", [
    ("oversee/pcs/Zure Ama", "Fighter, the White Calamity"),
    ("oversee/pcs/Husgus", "Ranger, the Golden-Cracked"),
    ("oversee/pcs/Vya Arleschia", "Ranger, the Fire Heir"),
    ("oversee/pcs/Syl Frost", "Sorcerer, the Ice Anomaly"),
    ("oversee/pcs/Shin Van Hel", "Warlock, the Shell"),
])}

{sec_desc("Recent Discoveries", [
    ("oversee/npcs/Lei Darvin Thorne", "revealed as Valerius's twin, true heir of Topaju"),
    ("oversee/npcs/Lei Livia Vane", "captured, terrified of Valerius"),
    ("oversee/locations/Arujaya Metropolis", "underground city of technology, now behind us"),
    ("oversee/lore/The Gemhearts", "four stones: Emelanica, Safayer, Rubion, Topaju"),
])}
"""

    specs["oversee/canon/README.md"] = f"""---
layout: list
title: Timeline
---
Chronological history of Oversee, from before the world to the Power Surge era.

{sec_named("Eras", [
    ("oversee/canon/OV0 Before Oversee", "OV0 — Before Oversee"),
    ("oversee/canon/OV1 Beginning of Time", "OV1 — Beginning of Time"),
    ("oversee/canon/OV2 Age of Knowledge", "OV2 — Age of Knowledge"),
    ("oversee/canon/OV3 Age of Nurturing", "OV3 — Age of Nurturing"),
    ("oversee/canon/OV4 The First God", "OV4 — The First God"),
    ("oversee/canon/OV5 Initial Six Era", "OV5 — Initial Six Era"),
    ("oversee/canon/OV6 Power Surge", "OV6 — Power Surge"),
])}

Back to {L("oversee/README", "Oversee")}.
"""

    specs["oversee/locations/README.md"] = f"""---
layout: list
title: Locations
---
Cities, ruins, and the strange places in between.

{sec("Cities & Settlements", [
    "oversee/locations/Arujaya Metropolis",
    "oversee/locations/Chenalia Town",
    "oversee/locations/Ghuffghuff Town",
    "oversee/locations/Graen City",
    "oversee/locations/Gudameng Town",
    "oversee/locations/Harka",
    "oversee/locations/Javan Town",
    "oversee/locations/Juto Port City",
    "oversee/locations/Kerajaan Grin",
    "oversee/locations/Kuo Lau Kingdom",
    "oversee/locations/Nesia Town",
    "oversee/locations/Padre Megalopolis",
    "oversee/locations/Thainarv Port City",
    "oversee/locations/Yawning Town",
])}

{sec("Boroughs & Districts", [
    "oversee/locations/Ironhold Borough",
    "oversee/locations/Zundabun Borough",
])}

{sec("Castles, Prisons & Ruins", [
    "oversee/locations/Cloud Prison",
    "oversee/locations/Greyland Castle",
    "oversee/locations/Miracle Cranny",
    "oversee/locations/Rune of the Cycle",
    "oversee/locations/The Underground Ark",
])}

{sec("Observatories & Universities", [
    "oversee/locations/Arbor's Observatorium",
    "oversee/locations/Juto's Observatorium",
    "oversee/locations/Observatorium Danau Kuno",
    "oversee/locations/Lyceum University of Arcane Arts",
    "oversee/locations/Tarakita University of Heroism",
])}

{sec("Wilds & Waters", [
    "oversee/locations/Canyon of Lament",
    "oversee/locations/Dima Island",
    "oversee/locations/Domido Forest",
    "oversee/locations/Frosthaven Peak",
    "oversee/locations/Garberro Forest",
    "oversee/locations/Jestnut Valley",
    "oversee/locations/Maw Desert",
    "oversee/locations/Mount Rayu",
    "oversee/locations/Muangching Bay",
    "oversee/locations/Whisper Place",
    "oversee/locations/Wind's Rest",
])}

{sec("Sacred & Strange", [
    "oversee/locations/Elis",
    "oversee/locations/The First Tree",
    "oversee/locations/The Golden Sheaf",
    "oversee/locations/The Spire of Whispering Ice",
    "oversee/locations/The Temple of Vythrax",
])}

Back to {L("oversee/README", "Oversee")}.
"""

    specs["oversee/npcs/README.md"] = f"""---
layout: list
title: NPCs
---
Everyone the party has met — allies, enemies, and those in between.

{sec("The Lei Bloodline", [
    "oversee/npcs/Hanzel Lei Krow",
    "oversee/npcs/Lei Alejandro",
    "oversee/npcs/Lei Darvin Thorne",
    "oversee/npcs/Lei Firage",
    "oversee/npcs/Lei Firsa",
    "oversee/npcs/Lei Iron Gort",
    "oversee/npcs/Lei Livia Vane",
    "oversee/npcs/Lei Roiga",
    "oversee/npcs/Lei Valerius Thorne",
    "oversee/npcs/Lei Watigi",
    "oversee/npcs/Lei Wendigo",
])}

{sec("House Grin", [
    "oversee/npcs/Accarus Grin",
    "oversee/npcs/Atreus Grin",
    "oversee/npcs/Gavaevodata Grin",
    "oversee/npcs/Geneva Grin",
    "oversee/npcs/Grin Qain",
    "oversee/npcs/Hildag Grin",
])}

{sec("Findias & the Guilds", [
    "oversee/npcs/Adam Findias",
    "oversee/npcs/Besik Findias",
])}

{sec("The Guanik Family", [
    "oversee/npcs/Guanik Dontol",
    "oversee/npcs/Guanik Huan",
    "oversee/npcs/Guanik Nila",
    "oversee/npcs/Guanik Smith",
    "oversee/npcs/Guanik Wiseman",
])}

{sec("The Mektol Household", [
    "oversee/npcs/Cindy Mektol",
    "oversee/npcs/Faska Mektol",
    "oversee/npcs/Herman Mektol",
])}

{sec("The Mamat & Sari Households", [
    "oversee/npcs/Agus",
    "oversee/npcs/Bu Mamat",
    "oversee/npcs/Ibu Sari",
    "oversee/npcs/Memeng",
    "oversee/npcs/Mr. Basir",
    "oversee/npcs/Mr. Basuki",
    "oversee/npcs/Mr. Bejir",
    "oversee/npcs/Mrs. Mamat",
    "oversee/npcs/Sari",
    "oversee/npcs/Siti",
])}

{sec("The Town Worthies", [
    "oversee/npcs/Elder Jarl",
    "oversee/npcs/Father Tulus",
    "oversee/npcs/General Wang",
    "oversee/npcs/Guo Lao",
    "oversee/npcs/Mr. Andreas",
    "oversee/npcs/Mr. Poise",
    "oversee/npcs/Mr. Salim",
    "oversee/npcs/Mrs. Ratna",
    "oversee/npcs/Oldrunn",
    "oversee/npcs/Queen Ghaniba",
])}

{sec("Scholars & Professors", [
    "oversee/npcs/Dr. Vektor",
    "oversee/npcs/Professor Alistair Donta",
    "oversee/npcs/Professor Howdy",
    "oversee/npcs/Professor Rubi",
    "oversee/npcs/Vreina Arleschia",
])}

{sec("Dragons & Ancient Powers", [
    "oversee/npcs/Babibubebo",
    "oversee/npcs/Bud-eg",
    "oversee/npcs/Grilnax",
    "oversee/npcs/Grolnok",
    "oversee/npcs/Helius",
    "oversee/npcs/Malakor",
    "oversee/npcs/Vythrax",
    "oversee/npcs/Zargoth",
    "oversee/npcs/Zargoyle",
])}

{sec("The North & the Frostscale", [
    "oversee/npcs/Gunnar Guirela",
    "oversee/npcs/Olaf Guirela",
    "oversee/npcs/The Hermit of the Misty Mountains",
    "oversee/npcs/Yrsa Frostscale",
])}

{sec("Townsfolk & Travellers", [
    "oversee/npcs/Antrem Klaus",
    "oversee/npcs/Atlan Nouveau",
    "oversee/npcs/Crest",
    "oversee/npcs/Dora",
    "oversee/npcs/Edra",
    "oversee/npcs/Elara",
    "oversee/npcs/Erah",
    "oversee/npcs/Erard Gelnne",
    "oversee/npcs/Fidale",
    "oversee/npcs/Geldfre",
    "oversee/npcs/Gordon",
    "oversee/npcs/Gzirmo Kopling",
    "oversee/npcs/Hora",
    "oversee/npcs/Janja",
    "oversee/npcs/Jarko",
    "oversee/npcs/Joni",
    "oversee/npcs/Junior",
    "oversee/npcs/Kael",
    "oversee/npcs/Kristine",
    "oversee/npcs/Ksatrian",
    "oversee/npcs/Mira Nouveau",
    "oversee/npcs/Pops Tortle",
    "oversee/npcs/Reins",
    "oversee/npcs/Rivan",
    "oversee/npcs/Ruslan",
    "oversee/npcs/Sam Hurls",
    "oversee/npcs/Samual",
    "oversee/npcs/Sasimo",
    "oversee/npcs/Senta",
    "oversee/npcs/Simon Greenbottle",
    "oversee/npcs/Yahanda",
    "oversee/npcs/Yayat Kopling",
])}

Back to {L("oversee/README", "Oversee")}.
"""

    specs["oversee/factions/README.md"] = f"""---
layout: list
title: Factions
---
The powers that shape the world — guilds, orders, bloodlines, and secret societies.

{sec("Guilds & Orders", [
    "oversee/factions/One Voice Commonwealth",
    "oversee/factions/Serikat Bongkar Muat",
    "oversee/factions/The Iron Guard",
    "oversee/factions/The Rose Guard",
    "oversee/factions/The Tinkers of Arujaya",
    "oversee/factions/The Yawning Guild",
])}

{sec("Bloodlines & Houses", [
    "oversee/factions/The Frostscale Clan",
    "oversee/factions/The Grace",
    "oversee/factions/The Guo Family",
    "oversee/factions/Will of Grin",
])}

{sec("Secret & Sacred", [
    "oversee/factions/Holy Triage",
    "oversee/factions/Keeper of Secret",
])}

Back to {L("oversee/README", "Oversee")}.
"""

    lore_sections = [
        sec("Cosmology & Origins", [
            "oversee/lore/Ambitio-Ether",
            "oversee/lore/Inbu",
            "oversee/lore/The Behemoths",
            "oversee/lore/The Echoes",
            "oversee/lore/The Gap",
            "oversee/lore/The Initial Six",
            "oversee/lore/The Three Surviving Dragons",
        ]),
        sec("The Cycle & the Bloodlines", [
            "oversee/lore/Lei Bloodline",
            "oversee/lore/The Bloodlines of Power",
            "oversee/lore/The Cycle Clan",
            "oversee/lore/The Cycle Ritual",
            "oversee/lore/The Triase",
            "oversee/lore/The Twin Tradition",
        ]),
        sec("The Gemhearts & Magic", [
            "oversee/lore/Fate Cards",
            "oversee/lore/The Gemhearts",
            "oversee/lore/The Swan, the Bat, and the Fool",
            "oversee/lore/The Valla",
            "oversee/lore/The Valla's History",
        ]),
        sec("Kingdoms, Law & Time", [
            "oversee/lore/The Calendar & Time",
            "oversee/lore/The Edisi Law",
            "oversee/lore/The Geography of Oversee",
            "oversee/lore/Timeline of Oversee",
        ]),
        sec("Threats & Turning Points", [
            "oversee/lore/The Frozen Legion",
            "oversee/lore/The Grace's Fall",
            "oversee/lore/The Great Disappearance",
            "oversee/lore/The Grin Curse",
            "oversee/lore/The Shell",
            "oversee/lore/The Tinkers' History",
        ]),
    ]
    if include_endgame_lore:
        lore_sections.append(sec("Deeper Currents", ENDGAME_LORE))

    specs["oversee/lore/README.md"] = (
        "---\nlayout: list\ntitle: Lore\n---\n"
        "Deep dives into the world's cosmology, magic, and the forces behind it all.\n\n"
        + "\n\n".join(lore_sections)
        + f"\n\nBack to {L('oversee/README', 'Oversee')}.\n"
    )

    specs["oversee/items/README.md"] = f"""---
layout: list
title: Items
---
Weapons, relics, and the Gemhearts that hold the world together.

{sec("The Gemhearts", [
    "oversee/items/Emelanica",
    "oversee/items/Rubion",
    "oversee/items/Safayer",
    "oversee/items/Topaju",
])}

{sec_named("Named Blades", [
    ("oversee/items/Frostfang — The Ice Fang", "Frostfang — The Ice Fang"),
    ("oversee/items/Kkana — The Stone Greatsword", "Kkana — The Stone Greatsword"),
    ("oversee/items/Rayio — The Wind Blade", "Rayio — The Wind Blade"),
    ("oversee/items/Swaith — The Soul-Thirsting Blade", "Swaith — The Soul-Thirsting Blade"),
    ("oversee/items/Terrde — The Patient Blade", "Terrde — The Patient Blade"),
    ("oversee/items/Zenahhi — The Loyal Blade", "Zenahhi — The Loyal Blade"),
])}

{sec_named("The Swan's Armory", [
    ("oversee/items/Alnean — Swan Song", "Alnean — Swan Song"),
    ("oversee/items/Gustaero — The Swan Bow", "Gustaero — The Swan Bow"),
    ("oversee/items/Niette — The Wing of the Swan", "Niette — The Wing of the Swan"),
])}

{sec("Tools, Maps & Oddities", [
    "oversee/items/Atlan's Compass",
    "oversee/items/Hildag's Map",
    "oversee/items/Worn-Out Bag of Tricks",
])}

{sec("Other Relics", [
    "oversee/items/Go Ingsani",
    "oversee/items/Renal",
])}

Back to {L("oversee/README", "Oversee")}.
"""

    specs["oversee/handouts/README.md"] = f"""---
layout: list
title: Handouts
---
In-world documents the party has collected — letters, maps, and transcripts.

{sec("Letters & Diaries", [
    "oversee/handouts/Atlan's Diary",
    "oversee/handouts/Atreus's Letter",
])}

{sec("Maps", [
    "oversee/handouts/Hildag's Map (Handout)",
])}

{sec("Carvings & Transcriptions", [
    "oversee/handouts/The Carving at Greyland Castle",
    "oversee/handouts/The Shell Video Transcript",
    "oversee/handouts/The Vigenère Cipher",
])}

Back to {L("oversee/README", "Oversee")}.
"""

    specs["oversee/pcs/README.md"] = f"""---
layout: list
title: PCs
---
The Five Sticks — the party themselves.

{sec_desc("The Five Sticks", [
    ("oversee/pcs/Zure Ama", "Fighter, the White Calamity"),
    ("oversee/pcs/Husgus", "Ranger, the Golden-Cracked"),
    ("oversee/pcs/Vya Arleschia", "Ranger, the Fire Heir"),
    ("oversee/pcs/Syl Frost", "Sorcerer, the Ice Anomaly"),
    ("oversee/pcs/Shin Van Hel", "Warlock, the Shell"),
])}

Back to {L("oversee/README", "Oversee")}.
"""

    specs["oversee/sessions/README.md"] = f"""---
layout: list
title: Sessions
---
Session recaps for Oversee, newest first.

{sec_named("Recaps", [
    ("oversee/sessions/Session 07 — Opressed", "Session 07 — Opressed"),
    ("oversee/sessions/Session 06 — Ethical Choices", "Session 06 — Ethical Choices"),
    ("oversee/sessions/Session 05 — Empty Husk", "Session 05 — Empty Husk"),
    ("oversee/sessions/Session 04 — Territorial", "Session 04 — Territorial"),
    ("oversee/sessions/Session 03 — The Bard", "Session 03 — The Bard"),
    ("oversee/sessions/Session 02 — The Wizard", "Session 02 — The Wizard"),
    ("oversee/sessions/Session 01 — The Sorcerer", "Session 01 — The Sorcerer"),
])}

Back to {L("oversee/README", "Oversee")}.
"""

    # =========================================================
    # AEDE
    # =========================================================

    specs["aede/README.md"] = f"""---
layout: list
title: Aede
---

A new campaign. One session so far — more to come.

{sec_named("Browse", [
    ("aede/sessions/README", "Sessions"),
])}

{sec_named("Sessions", [
    ("aede/sessions/Session Special — Love in Time", "Session Special — Love in Time"),
])}
"""

    specs["aede/sessions/README.md"] = f"""---
layout: list
title: Sessions
---
Session recaps for Aede.

{sec_named("Recaps", [
    ("aede/sessions/Session Special — Love in Time", "Session Special — Love in Time"),
])}

Back to {L("aede/README", "Aede")}.
"""

    # =========================================================
    # SONSTIGE
    # =========================================================

    specs["sonstige/README.md"] = f"""---
layout: list
title: Sonstige
---

The academy campaign. School life, lessons, and the strange things that happen between classes.

{sec_named("Browse the Wiki", [
    ("sonstige/canon/README", "Timeline"),
    ("sonstige/locations/README", "Locations"),
    ("sonstige/npcs/README", "NPCs"),
    ("sonstige/factions/README", "Factions"),
    ("sonstige/lore/README", "Lore"),
    ("sonstige/items/README", "Items"),
    ("sonstige/handouts/README", "Handouts"),
    ("sonstige/pcs/README", "PCs"),
    ("sonstige/sessions/README", "Sessions"),
])}
"""

    specs["sonstige/canon/README.md"] = f"""---
layout: list
title: Timeline
---
The three dates that shaped Sonstige — 2001, 2016, 2026 — and the world they left behind.

{sec_named("Eras", [
    ("sonstige/canon/SO0 Sonstige", "SO0 — Sonstige"),
    ("sonstige/canon/SO1 Negara Anderes", "SO1 — Negara Anderes"),
    ("sonstige/canon/SO2 The Battery", "SO2 — The Battery"),
    ("sonstige/canon/SO3 The Three Dates", "SO3 — The Three Dates"),
])}

Back to {L("sonstige/README", "Sonstige")}.
"""

    specs["sonstige/locations/README.md"] = f"""---
layout: list
title: Locations
---
Calamara, the Free Bird Academy, and the quiet corners around them.

{sec("The City", [
    "sonstige/locations/Calamara Metropole",
    "sonstige/locations/Grafstenmouth",
])}

{sec("Schools", [
    "sonstige/locations/Everglade Academy",
    "sonstige/locations/Free Bird Academy Campus",
    "sonstige/locations/Imperial Academy",
])}

{sec("Estates & Wilds", [
    "sonstige/locations/Ashbourne Manor",
    "sonstige/locations/The Azures",
    "sonstige/locations/Wood Elf Forest",
])}

Back to {L("sonstige/README", "Sonstige")}.
"""

    specs["sonstige/npcs/README.md"] = f"""---
layout: list
title: NPCs
---
Teachers, students, and the families behind them.

{sec("Faculty & Staff", [
    "sonstige/npcs/Coach Garrick",
    "sonstige/npcs/Dr. Fenwick",
    "sonstige/npcs/Dr. Ope",
    "sonstige/npcs/Madame Seraphine",
    "sonstige/npcs/Maestro Lorenzo",
    "sonstige/npcs/Mr. Elias",
    "sonstige/npcs/Prof. Imelda",
    "sonstige/npcs/Prof. Quill",
])}

{sec("Families & Nobility", [
    "sonstige/npcs/Cordelia Ashbourne",
    "sonstige/npcs/Edmund Ashbourne",
    "sonstige/npcs/Gargathun Ironhide",
    "sonstige/npcs/Lord Aldric Grafsten",
    "sonstige/npcs/Ramarz Ironhide",
])}

{sec("Students & Others", [
    "sonstige/npcs/Bellweather",
    "sonstige/npcs/Calathea Cortenya",
    "sonstige/npcs/Lilia Etheridge II",
    "sonstige/npcs/Mr. Rababrie Bellweather",
    "sonstige/npcs/Oliver Deen",
])}

Back to {L("sonstige/README", "Sonstige")}.
"""

    specs["sonstige/pcs/README.md"] = f"""---
layout: list
title: PCs
---
The student party of the Free Bird Academy.

{sec("The Student Party", [
    "sonstige/pcs/Brougha Ironhide",
    "sonstige/pcs/Mya Cortenya",
    "sonstige/pcs/Vivienne Ashbourne",
    "sonstige/pcs/Zenroy Dala",
])}

Back to {L("sonstige/README", "Sonstige")}.
"""

    specs["sonstige/factions/README.md"] = f"""---
layout: list
title: Factions
---
Student bodies, family lineages, and the powers behind Calamara's elite.

{sec("Factions", [
    "sonstige/factions/Anderes Government",
    "sonstige/factions/FBA Extracurricular",
    "sonstige/factions/The Free Bird Academy",
])}

Back to {L("sonstige/README", "Sonstige")}.
"""

    specs["sonstige/lore/README.md"] = f"""---
layout: list
title: Lore
---
FBA life, Jounce, The Bell, and the things hiding beneath the school.

{sec("School Life", [
    "sonstige/lore/FBA Class Schedule",
    "sonstige/lore/FBA Wing System",
])}

{sec("Jounce", [
    "sonstige/lore/Jounce",
    "sonstige/lore/Jounceling",
])}

{sec("The Bell & Below", [
    "sonstige/lore/R.A.I.B",
    "sonstige/lore/The Bell",
    "sonstige/lore/The Hidden Garden",
])}

Back to {L("sonstige/README", "Sonstige")}.
"""

    specs["sonstige/items/README.md"] = f"""---
layout: list
title: Items
---
Books, manuscripts, and relics that carry more than they seem.

{sec("Items", [
    "sonstige/items/Lumen Arash",
    "sonstige/items/The Manuscript",
])}

Back to {L("sonstige/README", "Sonstige")}.
"""

    # Curly apostrophe in the actual filename: Oliver Deen’s Last Song
    specs["sonstige/handouts/README.md"] = f"""---
layout: list
title: Handouts
---
In-world documents from the FBA — handbooks, letters, and the songs that warned them.

{sec_named("Handouts", [
    ("sonstige/handouts/FBA Student Handbook", "FBA Student Handbook"),
    ("sonstige/handouts/Pre-Session Zero Guide", "Pre-Session Zero Guide"),
    ("sonstige/handouts/The First Bell Note", "The First Bell Note"),
    ("sonstige/handouts/Oliver Deen’s Last Song", "Oliver Deen’s Last Song"),
])}

Back to {L("sonstige/README", "Sonstige")}.
"""

    specs["sonstige/sessions/README.md"] = f"""---
layout: list
title: Sessions
---

Session notes, recaps, and records from the Sonstige campaign.

No session recaps published yet.

Back to {L("sonstige/README", "Sonstige")}.
"""

    return specs

# ---------- writer ----------

def write_all(specs: dict[str, str], *, dry_run: bool, backup: bool, only: list[str] | None) -> int:
    written = 0
    for rel, content in specs.items():
        if only and not any(rel.startswith(p) for p in only):
            continue
        path = DM / rel
        if not path.parent.is_dir():
            print(f"  SKIP (no dir): {rel}", file=__import__("sys").stderr)
            continue
        action = "DRY" if dry_run else "WROTE"
        print(f"[{action}] {rel}  ({len(content)} bytes)")
        if not dry_run:
            if backup and path.exists():
                bak = path.with_name(path.name + ".bak")
                bak.write_bytes(path.read_bytes())
            path.write_text(content, encoding="utf-8")
        written += 1
    return written


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="preview only")
    ap.add_argument("--no-backup", action="store_true", help="don't write .bak siblings")
    ap.add_argument("--include-endgame-lore", action="store_true",
                    help="add the 5 gated endgame lore pages to oversee/lore/README")
    ap.add_argument("--only", nargs="+", metavar="PREFIX",
                    help="only process READMEs starting with one of these prefixes, e.g. --only oversee/ sonstige/")
    args = ap.parse_args()

    specs = build_specs(args.include_endgame_lore)
    print(f"Prepared {len(specs)} README specs"
          + (" (incl. endgame lore)" if args.include_endgame_lore else ""))
    n = write_all(specs, dry_run=args.dry_run, backup=not args.no_backup, only=args.only)
    print(f"\nDone: {n} file(s) {'would be ' if args.dry_run else ''}written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
