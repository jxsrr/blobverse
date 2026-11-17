import html, json
from pathlib import Path
from urllib.parse import quote

DATA_PATH = Path("scripts/oversee_atlas_data.json")
LOC_DIR = Path("Dungeon Master Notes/oversee/locations")
README_PATH = LOC_DIR / "README.md"

def is_published(slug: str) -> bool:
    md = LOC_DIR / f"{slug}.md"
    return md.exists() and "publish: false" not in md.read_text(encoding="utf-8")

def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    pins = []
    for loc in data["locations"]:
        if not is_published(loc["slug"]):
            continue
        href = "/oversee/locations/" + quote(loc["slug"], safe="")
        name = html.escape(loc["name"])
        cat = html.escape(loc["category"])
        reg = html.escape(loc["region"])
        status = html.escape(loc.get("status", "Charted"))
        desc = html.escape(loc["summary"])
        pins.append(
            f'<a class="bv-pin" href="{href}" style="--x:{loc["x"]}%;--y:{loc["y"]}%;" aria-label="{name}">'
            f'<span class="bv-pin-dot" aria-hidden="true"></span>'
            f'<span class="bv-pin-label">{name}</span>'
            f'<span class="bv-pin-card" role="tooltip">'
            f'<span class="bv-pin-meta">{reg} · {cat} · {status}</span>'
            f'<strong class="bv-pin-title">{name}</strong>'
            f'<span class="bv-pin-desc">{desc}</span>'
            f'</span></a>'
        )
    content = (
        "---\n"
        "title: Locations\n"
        "showSidebar: false\n"
        "showToc: false\n"
        "---\n\n"
        "::pf\n"
        '<div class="bv-atlas bv-atlas-full" role="region" aria-label="Interactive Atlas of Oversee">'
        f'<div class="bv-atlas-canvas" style="aspect-ratio:{data["aspectRatio"]};">'
        f'<img src="{data["image"]}" alt="World map of Oversee" loading="eager">'
        + "".join(pins) +
        "</div></div>\n"
        "::/pf\n"
    )
    README_PATH.write_text(content, encoding="utf-8")
    print("Built full-map Locations page with", len(pins), "pins")

if __name__ == "__main__":
    main()
