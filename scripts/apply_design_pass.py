import re
from pathlib import Path
from urllib.parse import quote

dm = Path("Dungeon Master Notes")
css_path = dm / "custom.css"
css_txt = css_path.read_text(encoding="utf-8")

extra_css = """
.bv-ep-header, .bv-relic {
  position: relative; padding: 1.4rem 1.6rem; margin: 0.75rem 0 1.75rem;
  border-radius: 10px; border: 1px solid var(--color-l-border);
  background: linear-gradient(135deg, color-mix(in srgb, var(--color-l-accent) 8%, var(--color-l-bg)) 0%, var(--color-l-bg-secondary) 100%);
  overflow: hidden;
}
.bv-ep-header::before { content: ""; position: absolute; top: 0; left: 0; bottom: 0; width: 5px; background: var(--color-l-accent); }
.bv-relic { border-color: color-mix(in srgb, #b8860b 35%, var(--color-l-border)); background: linear-gradient(135deg, color-mix(in srgb, #b8860b 8%, var(--color-l-bg)) 0%, var(--color-l-bg-secondary) 100%); }
.bv-relic::before { content: ""; position: absolute; top: 0; left: 0; bottom: 0; width: 5px; background: #b8860b; }
.bv-ep-kicker, .bv-relic-kicker { font-family: var(--font-family-monospace); font-size: 0.74rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--color-l-accent); margin-bottom: 0.3rem; }
.bv-relic-kicker { color: #9a6700; }
.bv-ep-heading, .bv-relic-title { font-family: var(--font-family-heading); font-size: 2rem; font-weight: 700; line-height: 1.15; margin: 0 0 0.65rem; }
.bv-ep-synopsis { font-size: 0.98rem; color: var(--color-l-text-secondary); margin: 0; line-height: 1.55; }
.bv-ep-nav { display: grid; grid-template-columns: 1fr auto 1fr; gap: 0.75rem; align-items: center; margin: 2.25rem 0 1rem; padding-top: 1.1rem; border-top: 1px solid var(--color-l-border); }
.bv-ep-nav-btn { display: inline-flex; flex-direction: column; padding: 0.6rem 0.9rem; border-radius: 8px; border: 1px solid var(--color-l-border); background: var(--color-l-bg-secondary); text-decoration: none !important; }
.bv-ep-nav-btn:hover { border-color: var(--color-l-accent); }
.bv-ep-nav-next { text-align: right; }
.bv-ep-nav-center { text-align: center; font-size: 0.82rem; font-weight: 600; }
.bv-ep-nav-dir { font-family: var(--font-family-monospace); font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--color-l-text-secondary); }
.bv-ep-nav-name { font-family: var(--font-family-heading); font-size: 1.02rem; font-weight: 600; color: var(--color-l-accent); }
@media (prefers-color-scheme: dark) {
  .bv-ep-header { border-color: var(--color-d-border); background: linear-gradient(135deg, color-mix(in srgb, var(--color-d-accent) 12%, var(--color-d-bg)) 0%, var(--color-d-bg-secondary) 100%); }
  .bv-ep-header::before { background: var(--color-d-accent); }
  .bv-ep-kicker, .bv-ep-nav-name { color: var(--color-d-accent); }
  .bv-ep-synopsis, .bv-ep-nav-dir { color: var(--color-d-text-secondary); }
  .bv-ep-nav { border-top-color: var(--color-d-border); }
  .bv-ep-nav-btn { background: var(--color-d-bg-secondary); border-color: var(--color-d-border); }
  .bv-relic { border-color: color-mix(in srgb, #e3b341 35%, var(--color-d-border)); background: linear-gradient(135deg, color-mix(in srgb, #e3b341 10%, var(--color-d-bg)) 0%, var(--color-d-bg-secondary) 100%); }
  .bv-relic::before { background: #e3b341; }
  .bv-relic-kicker { color: #e3b341; }
}
"""
if ".bv-ep-header" not in css_txt:
    css_path.write_text(css_txt.rstrip() + "\n" + extra_css, encoding="utf-8")

def parse_fm(txt):
    m = re.match(r"^---\n(.*?)\n---\n", txt, re.DOTALL)
    if not m: return {}, "", txt
    meta = dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line and not line.startswith(("-", " ")))
    return {k.strip(): v.strip().strip("\"\x27") for k, v in meta.items()}, txt[:m.end()], txt[m.end():]

def swap_glance(body, html):
    if body.lstrip().startswith("::pf"):
        return re.sub(r"^::pf\s*\n> \[!info\] At a Glance\n(?:>.*\n)+", f"::pf\n{html}\n\n", body.lstrip(), count=1)
    idx = body.find("%% DM SECRETS %%")
    if idx != -1:
        pf = re.sub(r"> \[!info\] At a Glance\n(?:>.*\n)+", f"{html}\n\n", body[:idx], count=1)
        return f"::pf\n{pf.strip()}\n::/pf\n{body[idx:]}"
    return re.sub(r"> \[!info\] At a Glance\n(?:>.*\n)+", f"::pf\n{html}\n::/pf\n\n", body, count=1)

groups = [
    ("oversee", "/oversee/sessions", [f"Session 0{i} — {t}.md" for i, t in enumerate(["The Sorcerer","The Wizard","The Bard","Territorial","Empty Husk","Ethical Choices","Opressed"], 1)]),
    ("aede", "/aede/sessions", ["Session Special — Love in Time.md"]),
]
for camp, burl, files in groups:
    for i, fn in enumerate(files):
        p = dm / camp / "sessions" / fn
        if not p.exists(): continue
        _, fm, body = parse_fm(p.read_text(encoding="utf-8"))
        m = re.search(r"> \[!abstract\] Previously\.\.\.\n((?:>.*\n)+)", body)
        syn = " ".join(re.sub(r"^>\s*", "", l).strip() for l in m.group(1).strip().splitlines()) if m else ""
        kicker = f"SPECIAL EPISODE · {camp.upper()}" if "Special" in fn else f"EPISODE {i+1:02d} · {camp.upper()}"
        hdr = f"<div class=\"bv-ep-header\"><div class=\"bv-ep-kicker\">{kicker}</div><div class=\"bv-ep-heading\">{fn[:-3]}</div><p class=\"bv-ep-synopsis\">{syn}</p></div>"
        pv = f"<a class=\"bv-ep-nav-btn\" href=\"{burl}/{quote(files[i-1][:-3])}\"><span class=\"bv-ep-nav-dir\">← Previous</span><span class=\"bv-ep-nav-name\">{files[i-1][:-3]}</span></a>" if i > 0 else "<div></div>"
        nx = f"<a class=\"bv-ep-nav-btn bv-ep-nav-next\" href=\"{burl}/{quote(files[i+1][:-3])}\"><span class=\"bv-ep-nav-dir\">Next →</span><span class=\"bv-ep-nav-name\">{files[i+1][:-3]}</span></a>" if i < len(files)-1 else "<div></div>"
        nav = f"\n<div class=\"bv-ep-nav\">{pv}<a class=\"bv-ep-nav-center\" href=\"{burl}\">All Sessions</a>{nx}</div>\n"
        if "bv-ep-header" not in body and m:
            body = body[:m.start()] + hdr + "\n\n" + body[m.end():].lstrip()
        if "bv-ep-nav" not in body:
            body = body.replace("\n::/pf", f"\n{nav}::/pf", 1) if "\n::/pf" in body else body.replace("%% DM SECRETS %%", f"{nav}::/pf\n%% DM SECRETS %%", 1)
        p.write_text(fm + body, encoding="utf-8")

for p in sorted((dm / "oversee" / "npcs").glob("*.md")):
    raw = p.read_text(encoding="utf-8")
    if p.name == "README.md" or "bv-dossier" in raw: continue
    meta, fm, body = parse_fm(raw)
    gm = re.search(r"> \[!info\] At a Glance\n((?:>.*\n)+)", body)
    if not gm or "not yet appeared" in gm.group(1): continue
    st = meta.get("status", "Alive")
    sl = st.lower()
    sc = "bv-status-captive" if any(w in sl for w in ("hostage","captive","imprison")) else ("bv-status-deceased" if any(w in sl for w in ("deceas","dead")) else "bv-status-alive")
    where = next((l.split("**Where:**",1)[1].strip() for l in gm.group(1).splitlines() if "**Where:**" in l), meta.get("home","Unknown"))
    fac = meta.get("faction", "Independent")
    cells = "".join(f"<div class=\"bv-stat-cell\"><div class=\"bv-stat-label\">{k}</div><div class=\"bv-stat-val\">{v}</div></div>" for k,v in [("Affiliation",fac),("Whereabouts",where),("Base",meta.get("home","Unknown")),("First Seen",meta.get("first_seen","Oversee"))])
    card = f"<div class=\"bv-dossier\"><div class=\"bv-dossier-top\"><div class=\"bv-badge-row\"><span class=\"bv-badge\">NPC Dossier</span><span class=\"bv-badge bv-badge-neutral\">{fac.split(chr(40))[0].strip()}</span></div><span class=\"bv-status {sc}\">{st.capitalize()}</span></div><div class=\"bv-dossier-name\">{p.stem}</div><div class=\"bv-dossier-epithet\">{meta.get(chr(114)+chr(111)+chr(108)+chr(101), chr(79)+chr(118)+chr(101)+chr(114)+chr(115)+chr(101)+chr(101)+chr(32)+chr(78)+chr(80)+chr(67))}</div><div class=\"bv-dossier-grid\">{cells}</div></div>"
    p.write_text(fm + swap_glance(body, card), encoding="utf-8")

for p in sorted(list((dm / "oversee" / "items").glob("*.md")) + [dm / "oversee" / "lore" / "The Gemhearts.md"]):
    raw = p.read_text(encoding="utf-8")
    if not p.exists() or p.name == "README.md" or "bv-relic" in raw: continue
    _, fm, body = parse_fm(raw)
    gm = re.search(r"> \[!info\] At a Glance\n((?:>.*\n)+)", body)
    if not gm: continue
    rows = [re.match(r"^>\s*\*\*([^:*]+):\*\*\s*(.+)$", l.strip()).groups() for l in gm.group(1).splitlines() if re.match(r"^>\s*\*\*([^:*]+):\*\*\s*(.+)$", l.strip())]
    if not rows: continue
    cells = "".join(f"<div class=\"bv-stat-cell\"><div class=\"bv-stat-label\">{k}</div><div class=\"bv-stat-val\">{v}</div></div>" for k,v in rows[:4])
    kicker = "CORE LORE · ARCHITECT ARTIFACT" if p.name == "The Gemhearts.md" else "RELIC & ARTIFACT ARCHIVE"
    relic = f"<div class=\"bv-relic\"><div class=\"bv-relic-kicker\">{kicker}</div><div class=\"bv-relic-title\">{p.stem}</div><div class=\"bv-dossier-grid\">{cells}</div></div>"
    p.write_text(fm + swap_glance(body, relic), encoding="utf-8")
print("ALL DONE")
