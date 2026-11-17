import html, json
from pathlib import Path
from urllib.parse import quote

DATA_PATH = Path("scripts/oversee_atlas_data.json")
LOC_DIR = Path("Dungeon Master Notes/oversee/locations")
README_PATH = LOC_DIR / "README.md"

ICONS = {
    "settlement": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 21h18M5 21V9l4-3 4 3v12M13 21v-8l4-2 2 1v9M8 13h2v3H8z"/></svg>',
    "landmark": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2l2.4 6.6L21 11l-6.6 2.4L12 20l-2.4-6.6L3 11l6.6-2.4z"/></svg>',
    "region": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2.2 5.2-5.2 2.2 2.2-5.2z"/></svg>',
    "institution": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3L2 8l10 5 10-5-10-5zM5 11v6l7 3.5 7-3.5v-6"/></svg>',
    "fortress": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 21V8h3v2h3V8h4v2h3V8h3v13H4zm6 0v-5h4v5"/></svg>',
}

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
        cat_raw = loc["category"].lower()
        svg = ICONS.get(cat_raw, ICONS["landmark"])
        cat = html.escape(loc["category"])
        reg = html.escape(loc["region"])
        status = html.escape(loc.get("status", "Charted"))
        desc = html.escape(loc["summary"])
        pins.append(
            f'<a class="bv-pin" data-cat="{cat_raw}" href="{href}" style="--x:{loc["x"]}%;--y:{loc["y"]}%;" aria-label="{name} ({cat})">'
            f'<span class="bv-pin-marker" aria-hidden="true">{svg}</span>'
            f'<span class="bv-pin-label">{name}</span>'
            f'<span class="bv-pin-card" role="tooltip">'
            f'<span class="bv-pin-meta">{reg} · {cat} · {status}</span>'
            f'<strong class="bv-pin-title">{name}</strong>'
            f'<span class="bv-pin-desc">{desc}</span>'
            f'<span class="bv-pin-cta">Buka Arsip Lokasi →</span>'
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
        '<span class="bv-atlas-corner bv-c-tl" aria-hidden="true"></span>'
        '<span class="bv-atlas-corner bv-c-tr" aria-hidden="true"></span>'
        '<span class="bv-atlas-corner bv-c-bl" aria-hidden="true"></span>'
        '<span class="bv-atlas-corner bv-c-br" aria-hidden="true"></span>'
        f'<div class="bv-atlas-canvas" style="aspect-ratio:{data["aspectRatio"]};">'
        f'<img src="{data["image"]}" alt="World map of Oversee" loading="eager">'
        + "".join(pins) +
        "</div></div>\n"
        "::/pf\n"
    )
    README_PATH.write_text(content, encoding="utf-8")
    print("Built framed icon atlas with", len(pins), "markers")

if __name__ == "__main__":
    main()
