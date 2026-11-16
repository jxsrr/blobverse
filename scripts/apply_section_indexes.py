import re
from pathlib import Path
from urllib.parse import quote

dm = Path("Dungeon Master Notes")
pl = Path("_player/Dungeon Master Notes")
css_path = dm / "custom.css"
css_txt = css_path.read_text(encoding="utf-8")

sec_css = """
/* === Section Directory Headers & Quick-Link Grids === */
.bv-sec-hero {
  position: relative; padding: 1.5rem 1.7rem; margin: 0.75rem 0 1.75rem;
  border-radius: 10px; border: 1px solid var(--color-l-border);
  background: linear-gradient(135deg, color-mix(in srgb, var(--color-l-accent) 9%, var(--color-l-bg)) 0%, var(--color-l-bg-secondary) 100%);
  overflow: hidden;
}
.bv-sec-hero::before { content: ""; position: absolute; top: 0; left: 0; bottom: 0; width: 5px; background: var(--color-l-accent); }
.bv-sec-kicker { font-family: var(--font-family-monospace); font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--color-l-accent); margin-bottom: 0.3rem; }
.bv-sec-title { font-family: var(--font-family-heading); font-size: 2rem; font-weight: 700; line-height: 1.15; margin: 0 0 0.4rem; }
.bv-sec-sub { font-size: 0.96rem; color: var(--color-l-text-secondary); margin: 0; line-height: 1.5; }
.bv-idx-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 0.75rem; margin: 1.25rem 0 2rem; }
.bv-idx-card {
  display: flex; flex-direction: column; justify-content: space-between;
  padding: 0.95rem 1.05rem; border-radius: 8px;
  border: 1px solid var(--color-l-border); background: var(--color-l-bg-secondary);
  text-decoration: none !important; transition: border-color 120ms ease, transform 120ms ease;
}
.bv-idx-card:hover { border-color: var(--color-l-accent); transform: translateY(-1px); }
.bv-idx-tag { font-family: var(--font-family-monospace); font-size: 0.66rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--color-l-text-secondary); margin-bottom: 0.25rem; }
.bv-idx-name { font-family: var(--font-family-heading); font-size: 1.15rem; font-weight: 700; color: var(--color-l-accent); line-height: 1.25; margin-bottom: 0.25rem; }
.bv-idx-meta { font-size: 0.84rem; color: var(--color-l-text-secondary); line-height: 1.35; }
@media (prefers-color-scheme: dark) {
  .bv-sec-hero { border-color: var(--color-d-border); background: linear-gradient(135deg, color-mix(in srgb, var(--color-d-accent) 12%, var(--color-d-bg)) 0%, var(--color-d-bg-secondary) 100%); }
  .bv-sec-hero::before { background: var(--color-d-accent); }
  .bv-sec-kicker, .bv-idx-name { color: var(--color-d-accent); }
  .bv-sec-sub, .bv-idx-tag, .bv-idx-meta { color: var(--color-d-text-secondary); }
  .bv-idx-card { border-color: var(--color-d-border); background: var(--color-d-bg-secondary); }
  .bv-idx-card:hover { border-color: var(--color-d-accent); }
}
"""
if ".bv-sec-hero" not in css_txt:
    css_path.write_text(css_txt.rstrip() + "\n" + sec_css, encoding="utf-8")

sections = {
    "pcs": ("PLAYER CHARACTERS", "The party members you play alongside at the table."),
    "npcs": ("CHARACTER ARCHIVE", "Allies, rivals, patrons, and figures encountered across the campaign."),
    "locations": ("ATLAS & LOCATIONS", "Cities, landmarks, regions, and territories charted so far."),
    "factions": ("FACTIONS & ORDERS", "Guilds, courts, syndicates, and powers shaping the world."),
    "items": ("RELICS & ARTIFACTS", "Weapons, curiosities, and named items uncovered in play."),
    "lore": ("WORLD LORE", "History, metaphysics, magic systems, and documented knowledge."),
    "canon": ("CANON TIMELINE", "Chronological eras and recorded historical ages."),
    "sessions": ("SESSION LOGS", "Episode-by-episode recaps of everything that happened at the table."),
    "handouts": ("PLAYER HANDOUTS", "Letters, maps, notices, and in-world documents found by the party."),
}

def get_meta(p):
    txt = p.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", txt, re.DOTALL)
    meta = {}
    if m:
        for ln in m.group(1).splitlines():
            if ":" in ln and not ln.startswith(("-", " ")):
                k, v = ln.split(":", 1)
                meta[k.strip()] = v.strip().strip("\"\x27")
    return meta, txt

updated = 0
for camp in ("oversee", "sonstige", "aede"):
    for sec, (kicker, desc) in sections.items():
        readme = dm / camp / sec / "README.md"
        if not readme.exists(): continue
        pdir = pl / camp / sec
        entries = []
        if pdir.exists():
            for fp in sorted(pdir.glob("*.md")):
                if fp.name == "README.md": continue
                meta, ptxt = get_meta(fp)
                if "not yet appeared in the session recaps" in ptxt: continue
                tag = meta.get("faction") or meta.get("region") or meta.get("era") or meta.get("class") or sec.upper()
                sub = meta.get("role") or meta.get("summary") or meta.get("description") or ""
                if len(sub) > 85: sub = sub[:82].rstrip() + "..."
                entries.append((fp.stem, tag.split("(")[0].strip(), sub))
        cards = "".join(
            f"<a class=\"bv-idx-card\" href=\"/{camp}/{sec}/{quote(name)}\"><span class=\"bv-idx-tag\">{tag}</span><span class=\"bv-idx-name\">{name}</span><span class=\"bv-idx-meta\">{sub}</span></a>"
            for name, tag, sub in entries
        )
        grid = f"<div class=\"bv-idx-grid\">{cards}</div>" if cards else "<p><em>No entries revealed in play yet.</em></p>"
        title = f"{camp.capitalize()} — {sec.capitalize()}"
        hero = f"<div class=\"bv-sec-hero\"><div class=\"bv-sec-kicker\">{camp.upper()} · {kicker} ({len(entries)} ENTRIES)</div><div class=\"bv-sec-title\">{title}</div><p class=\"bv-sec-sub\">{desc}</p></div>"
        raw = readme.read_text(encoding="utf-8")
        m_fm = re.match(r"^---\n.*?\n---\n", raw, re.DOTALL)
        fm = m_fm.group(0) if m_fm else f"---\ntitle: {title}\n---\n"
        readme.write_text(f"{fm}\n::pf\n{hero}\n\n{grid}\n::/pf\n", encoding="utf-8")
        updated += 1

print(f"SECTION INDEX PAGES UPGRADED: {updated}")
