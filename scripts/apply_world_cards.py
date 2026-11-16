import re
from pathlib import Path

dm = Path("Dungeon Master Notes")
css_path = dm / "custom.css"
css_txt = css_path.read_text(encoding="utf-8")

world_css = """
/* === World Showcase Cards (Factions, Locations, Canon) === */
.bv-world {
  position: relative; padding: 1.4rem 1.6rem; margin: 0.75rem 0 1.75rem;
  border-radius: 10px; border: 1px solid var(--color-l-border);
  background: linear-gradient(135deg, color-mix(in srgb, var(--bv-card-accent, var(--color-l-accent)) 8%, var(--color-l-bg)) 0%, var(--color-l-bg-secondary) 100%);
  overflow: hidden;
}
.bv-world::before { content: ""; position: absolute; top: 0; left: 0; bottom: 0; width: 5px; background: var(--bv-card-accent, var(--color-l-accent)); }
.bv-world-faction { --bv-card-accent: #7c3aed; }
.bv-world-location { --bv-card-accent: #0f766e; }
.bv-world-canon { --bv-card-accent: #b45309; }
.bv-world-kicker { font-family: var(--font-family-monospace); font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--bv-card-accent, var(--color-l-accent)); margin-bottom: 0.3rem; }
.bv-world-title { font-family: var(--font-family-heading); font-size: 1.95rem; font-weight: 700; line-height: 1.15; margin: 0 0 0.35rem; }
.bv-world-sub { font-style: italic; font-size: 0.96rem; color: var(--color-l-text-secondary); margin: 0 0 0.85rem; }
@media (prefers-color-scheme: dark) {
  .bv-world { border-color: var(--color-d-border); background: linear-gradient(135deg, color-mix(in srgb, var(--bv-card-accent, var(--color-d-accent)) 12%, var(--color-d-bg)) 0%, var(--color-d-bg-secondary) 100%); }
  .bv-world-faction { --bv-card-accent: #c4b5fd; }
  .bv-world-location { --bv-card-accent: #5eead4; }
  .bv-world-canon { --bv-card-accent: #fbbf24; }
  .bv-world-sub { color: var(--color-d-text-secondary); }
}
"""
if ".bv-world" not in css_txt:
    css_path.write_text(css_txt.rstrip() + "\n" + world_css, encoding="utf-8")

def parse_fm(txt):
    m = re.match(r"^---\n(.*?)\n---\n", txt, re.DOTALL)
    if not m: return {}, "", txt
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(("-", " ")):
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip("\"\x27")
    return meta, txt[:m.end()], txt[m.end():]

def swap_glance(body, html):
    if body.lstrip().startswith("::pf"):
        return re.sub(r"^::pf\s*\n> \[!info\] At a Glance\n(?:>.*\n)+", f"::pf\n{html}\n\n", body.lstrip(), count=1)
    idx = body.find("%% DM SECRETS %%")
    if idx != -1:
        pf = re.sub(r"> \[!info\] At a Glance\n(?:>.*\n)+", f"{html}\n\n", body[:idx], count=1)
        return f"::pf\n{pf.strip()}\n::/pf\n{body[idx:]}"
    return re.sub(r"> \[!info\] At a Glance\n(?:>.*\n)+", f"::pf\n{html}\n::/pf\n\n", body, count=1)

cats = [
    ("factions", "bv-world-faction", "FACTION DOSSIER"),
    ("locations", "bv-world-location", "LOCATION ARCHIVE"),
    ("canon", "bv-world-canon", "CANON TIMELINE"),
]

counts = {"factions": 0, "locations": 0, "canon": 0}
for camp in ("oversee", "sonstige"):
    for folder, cls, label in cats:
        d = dm / camp / folder
        if not d.exists(): continue
        for p in sorted(d.glob("*.md")):
            if p.name == "README.md": continue
            raw = p.read_text(encoding="utf-8")
            if "bv-world" in raw: continue
            meta, fm, body = parse_fm(raw)
            gm = re.search(r"> \[!info\] At a Glance\n((?:>.*\n)+)", body)
            if not gm: continue
            block = gm.group(1)
            if "not yet appeared" in block: continue
            rows = [re.match(r"^>\s*\*\*([^:*]+):\*\*\s*(.+)$", l.strip()).groups() for l in block.splitlines() if re.match(r"^>\s*\*\*([^:*]+):\*\*\s*(.+)$", l.strip())]
            if not rows:
                for k in ("region", "continent", "era", "alignment", "leader", "status"):
                    if meta.get(k): rows.append((k.capitalize(), meta[k]))
            cells = "".join(f"<div class=\"bv-stat-cell\"><div class=\"bv-stat-label\">{k}</div><div class=\"bv-stat-val\">{v}</div></div>" for k, v in rows[:4])
            grid = f"<div class=\"bv-dossier-grid\">{cells}</div>" if cells else ""
            sub = meta.get("summary") or meta.get("description") or ""
            sub_h = f"<div class=\"bv-world-sub\">{sub}</div>" if sub else ""
            card = f"<div class=\"bv-world {cls}\"><div class=\"bv-world-kicker\">{camp.upper()} · {label}</div><div class=\"bv-world-title\">{p.stem}</div>{sub_h}{grid}</div>"
            p.write_text(fm + swap_glance(body, card), encoding="utf-8")
            counts[folder] += 1

print("WORLD CARDS APPLIED:", counts)
