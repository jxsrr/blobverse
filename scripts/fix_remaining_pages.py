import re
from pathlib import Path

dm = Path("Dungeon Master Notes")

def parse_fm(txt):
    m = re.match(r"^---\n(.*?)\n---\n", txt, re.DOTALL)
    if not m: return {}, "", txt
    meta = {}
    for ln in m.group(1).splitlines():
        if ":" in ln and not ln.startswith(("-", " ")):
            k, v = ln.split(":", 1)
            meta[k.strip()] = v.strip().strip("\"\x27")
    return meta, txt[:m.end()], txt[m.end():]

def balance_pf(body):
    dm_idx = body.find("%% DM SECRETS %%")
    pf_part = body[:dm_idx] if dm_idx != -1 else body
    dm_part = body[dm_idx:] if dm_idx != -1 else ""
    opens = len(re.findall(r"^::pf\b", pf_part, re.M))
    closes = len(re.findall(r"^::/pf\b", pf_part, re.M))
    if opens > closes:
        pf_part = pf_part.rstrip() + "\n" + ("::/pf\n" * (opens - closes))
    elif closes > opens:
        pf_part = ("::pf\n" * (closes - opens)) + pf_part.lstrip()
    return pf_part + dm_part

cat_map = {
    "lore": ("bv-world bv-world-canon", "WORLD LORE ARCHIVE"),
    "handouts": ("bv-relic", "IN-WORLD HANDOUT"),
    "items": ("bv-relic", "RELIC & ARTIFACT ARCHIVE"),
    "factions": ("bv-world bv-world-faction", "FACTION DOSSIER"),
    "locations": ("bv-world bv-world-location", "LOCATION ARCHIVE"),
    "canon": ("bv-world bv-world-canon", "CANON ARCHIVE"),
    "npcs": ("bv-dossier", "NPC DOSSIER"),
    "pcs": ("bv-dossier", "PLAYER CHARACTER"),
}

bal_n, card_n = 0, 0
for p in sorted(dm.rglob("*.md")):
    if p.name == "README.md": continue
    raw = p.read_text(encoding="utf-8")
    meta, fm, body = parse_fm(raw)
    new_body = balance_pf(body)
    if new_body != body:
        bal_n += 1
    parts = p.relative_to(dm).parts
    camp = parts[0].upper() if len(parts) > 1 else "BLOBVERSE"
    sec = parts[1] if len(parts) > 2 else "lore"
    if "not yet appeared in the session recaps" not in new_body and "bv-" not in new_body:
        cls, label = cat_map.get(sec, ("bv-world bv-world-canon", "CAMPAIGN ARCHIVE"))
        sub = meta.get("summary") or meta.get("description") or meta.get("role") or ""
        sub_h = f"<div class=\"bv-world-sub\">{sub}</div>" if sub else ""
        rows = [(k.capitalize(), meta[k]) for k in ("region", "faction", "era", "type", "status", "author") if meta.get(k)]
        cells = "".join(f"<div class=\"bv-stat-cell\"><div class=\"bv-stat-label\">{k}</div><div class=\"bv-stat-val\">{v}</div></div>" for k, v in rows[:4])
        grid = f"<div class=\"bv-dossier-grid\">{cells}</div>" if cells else ""
        card = f"<div class=\"{cls}\"><div class=\"bv-world-kicker\">{camp} · {label}</div><div class=\"bv-world-title\">{p.stem}</div>{sub_h}{grid}</div>\n\n"
        gm = re.search(r"> \[!info\] At a Glance\n((?:>.*\n)+)", new_body)
        if gm:
            new_body = new_body[:gm.start()] + card + new_body[gm.end():].lstrip()
        elif new_body.lstrip().startswith("::pf"):
            new_body = new_body.lstrip().replace("::pf\n", "::pf\n" + card, 1)
        elif "%% DM SECRETS %%" in new_body:
            idx = new_body.find("%% DM SECRETS %%")
            new_body = "::pf\n" + card + new_body[:idx].strip() + "\n::/pf\n" + new_body[idx:]
        else:
            new_body = "::pf\n" + card + new_body.strip() + "\n::/pf\n"
        card_n += 1
    if fm + new_body != raw:
        p.write_text(fm + new_body, encoding="utf-8")

print(f"BALANCED ::pf FILES: {bal_n} | NEW CARDS APPLIED: {card_n}")
