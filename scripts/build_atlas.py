"""Compile scripts/oversee_atlas_data.json into Dungeon Master Notes/oversee/locations/README.md."""
import html
import json
import re
from pathlib import Path
from urllib.parse import quote

DATA_PATH = Path("scripts/oversee_atlas_data.json")
LOC_DIR = Path("Dungeon Master Notes/oversee/locations")
README_PATH = LOC_DIR / "README.md"

def slug_to_href(slug: str) -> str:
    return "/oversee/locations/" + quote(slug, safe="")

def is_published(slug: str) -> bool:
    md = LOC_DIR / f"{slug}.md"
    if not md.exists():
        return False
    return "publish: false" not in md.read_text(encoding="utf-8")

def render_atlas(data: dict) -> str:
    valid = [loc for loc in data["locations"] if is_published(loc["slug"])]
    pins = []
    cards = []
    for i, loc in enumerate(valid):
        cat_slug = loc["category"].lower()
        href = slug_to_href(loc["slug"])
        name = html.escape(loc["name"])
        cat = html.escape(loc["category"])
        reg = html.escape(loc["region"])
        status = html.escape(loc.get("status", "Charted"))
        desc = html.escape(loc["summary"])
        pins.append(
            f'<a class="bv-pin" data-cat="{cat_slug}" href="{href}" '
            f'style="--x:{loc["x"]}%;--y:{loc["y"]}%;" '
            f'aria-label="{name} — {cat} in {reg} ({status})">'
            f'<span class="bv-pin-dot" aria-hidden="true"></span>'
            f'<span class="bv-pin-label">{name}</span>'
            f'<span class="bv-pin-card" role="tooltip">'
            f'<span class="bv-pin-meta">{reg} · {cat} · {status}</span>'
            f'<strong class="bv-pin-title">{name}</strong>'
            f'<span class="bv-pin-desc">{desc}</span>'
            f'<span class="bv-pin-cta">Open Lore Entry →</span>'
            f'</span></a>'
        )
    out = [
        '<div class="bv-atlas" role="region" aria-label="Interactive Atlas of Oversee">',
        '  <input class="bv-atlas-state" type="radio" name="bv-cat" id="bv-cat-all" checked>',
        '  <input class="bv-atlas-state" type="radio" name="bv-cat" id="bv-cat-settlement">',
        '  <input class="bv-atlas-state" type="radio" name="bv-cat" id="bv-cat-landmark">',
        '  <input class="bv-atlas-state" type="radio" name="bv-cat" id="bv-cat-region">',
        '  <input class="bv-atlas-state" type="radio" name="bv-cat" id="bv-cat-institution">',
        '  <input class="bv-atlas-state" type="radio" name="bv-cat" id="bv-cat-fortress">',
        '  <input class="bv-atlas-state" type="radio" name="bv-zoom" id="bv-zoom-1" checked>',
        '  <input class="bv-atlas-state" type="radio" name="bv-zoom" id="bv-zoom-2">',
        '  <div class="bv-atlas-bar">',
        '    <div class="bv-atlas-filters" role="group" aria-label="Filter locations by category">',
        '      <label for="bv-cat-all">All</label>',
        '      <label for="bv-cat-settlement">Settlements</label>',
        '      <label for="bv-cat-landmark">Landmarks</label>',
        '      <label for="bv-cat-region">Regions</label>',
        '      <label for="bv-cat-institution">Institutions</label>',
        '      <label for="bv-cat-fortress">Fortresses</label>',
        '    </div>',
        '    <div class="bv-atlas-zoom" role="group" aria-label="Map zoom level">',
        '      <label for="bv-zoom-1">100%</label>',
        '      <label for="bv-zoom-2">175% Pan</label>',
        '    </div>',
        '  </div>',
        '  <div class="bv-atlas-frame">',
        '    <div class="bv-atlas-viewport">',
        f'      <div class="bv-atlas-canvas" style="aspect-ratio:{data["aspectRatio"]};">',
        f'        <img src="{data["image"]}" alt="World map of Oversee showing Pirizia, Rioquan, Harka, and Elis" loading="eager">',
        '        ' + ''.join(pins),
        '      </div>',
        '    </div>',
        '    <div class="bv-atlas-dock" aria-live="polite">',
        '      <span class="bv-atlas-dock-hint">Hover, focus, or tap any marker on the chart to preview its archive record. Click to open full entry.</span>',
        '    </div>',
        '  </div>',
        '</div>'
    ]
    return "\n".join(out)

def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    atlas_html = render_atlas(data)
    readme = README_PATH.read_text(encoding="utf-8")
    block = f"<!-- ATLAS:START -->\n{atlas_html}\n<!-- ATLAS:END -->"
    if "<!-- ATLAS:START -->" in readme:
        readme = re.sub(r"<!-- ATLAS:START -->.*?<!-- ATLAS:END -->", block, readme, flags=re.S)
    else:
        readme = readme.replace('<div class="bv-idx-grid">', f"{block}\n\n<div class=\"bv-idx-grid\">", 1)
    README_PATH.write_text(readme, encoding="utf-8")
    print("Injected interactive atlas into", README_PATH)

if __name__ == "__main__":
    main()
