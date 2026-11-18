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
    gazetteer = []
    badge = (
        '<span class="bv-world-theme" data-world="oversee" aria-hidden="true"></span>'
        '<a class="bv-world-home" href="/oversee" aria-label="Back to Oversee Home">'
        '<img src="/oversee/Logo.png" alt="Oversee">'
        '<span class="bv-world-home-arrow">← Hub</span></a>'
    )

    for loc in sorted(data["locations"], key=lambda item: item["name"]):
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
        x = float(loc["x"])
        y = float(loc["y"])

        edge_classes = ["bv-pin"]
        if y < 26:
            edge_classes.append("is-top")
        if x < 18:
            edge_classes.append("is-left")
        elif x > 82:
            edge_classes.append("is-right")

        pins.append(
            f'<a class="{" ".join(edge_classes)}" data-cat="{cat_raw}" href="{href}" '
            f'style="--x:{x}%;--y:{y}%;left:{x}%;top:{y}%;" aria-label="{name} ({reg} · {cat})">'
            f'<span class="bv-pin-marker" aria-hidden="true">{svg}</span>'
            f'<span class="bv-pin-label">{name}</span>'
            f'<span class="bv-pin-card" role="tooltip">'
            f'<span class="bv-pin-meta">{reg} · {cat} · {status}</span>'
            f'<strong class="bv-pin-title">{name}</strong>'
            f'<span class="bv-pin-desc">{desc}</span>'
            f'<span class="bv-pin-cta">Open Location Archive →</span>'
            f'</span></a>'
        )
        gazetteer.append(
            f'<a class="bv-atlas-gaz-item" href="{href}">'
            f'<span class="bv-atlas-gaz-name">{name}</span>'
            f'<span class="bv-atlas-gaz-sub">{reg} · {cat}</span>'
            f'</a>'
        )

    content = (
        "---\n"
        "title: Locations\n"
        "showSidebar: false\n"
        "showToc: false\n"
        "---\n\n"
        "::pf\n"
        f"{badge}\n\n"
        '<div class="bv-sec-hero"><div class="bv-sec-kicker">OVERSEE · CARTOGRAPHIC ATLAS</div>'
        '<div class="bv-sec-title">Atlas of Oversee</div>'
        '<p class="bv-sec-sub">Filter by classification, zoom to inspect regions, or select any charted marker to open its archival entry.</p></div>\n\n'
        '<div class="bv-atlas-shell" role="region" aria-label="Interactive Atlas of Oversee">'
        '<input class="bv-atlas-radio" type="radio" name="atlas-cat" id="atlas-cat-all" checked>'
        '<input class="bv-atlas-radio" type="radio" name="atlas-cat" id="atlas-cat-settlement">'
        '<input class="bv-atlas-radio" type="radio" name="atlas-cat" id="atlas-cat-landmark">'
        '<input class="bv-atlas-radio" type="radio" name="atlas-cat" id="atlas-cat-region">'
        '<input class="bv-atlas-radio" type="radio" name="atlas-cat" id="atlas-cat-institution">'
        '<input class="bv-atlas-radio" type="radio" name="atlas-cat" id="atlas-cat-fortress">'
        '<input class="bv-atlas-radio" type="radio" name="atlas-zoom" id="atlas-zoom-100" checked>'
        '<input class="bv-atlas-radio" type="radio" name="atlas-zoom" id="atlas-zoom-145">'
        '<input class="bv-atlas-radio" type="radio" name="atlas-zoom" id="atlas-zoom-190">'
        '<div class="bv-atlas-toolbar">'
        '  <div class="bv-atlas-group" role="group" aria-label="Filter locations by category">'
        '    <span class="bv-atlas-group-label">Filter:</span>'
        '    <label class="bv-atlas-pill" for="atlas-cat-all">All (28)</label>'
        '    <label class="bv-atlas-pill" for="atlas-cat-settlement">Settlements</label>'
        '    <label class="bv-atlas-pill" for="atlas-cat-landmark">Landmarks</label>'
        '    <label class="bv-atlas-pill" for="atlas-cat-region">Regions</label>'
        '    <label class="bv-atlas-pill" for="atlas-cat-institution">Institutions</label>'
        '    <label class="bv-atlas-pill" for="atlas-cat-fortress">Fortresses</label>'
        '  </div>'
        '  <div class="bv-atlas-group" role="group" aria-label="Map zoom controls">'
        '    <span class="bv-atlas-group-label">Zoom:</span>'
        '    <label class="bv-atlas-pill" for="atlas-zoom-100">Reset (100%)</label>'
        '    <label class="bv-atlas-pill" for="atlas-zoom-145">145%</label>'
        '    <label class="bv-atlas-pill" for="atlas-zoom-190">190%</label>'
        '  </div>'
        '</div>'
        '<div class="bv-atlas-viewport">'
        '  <div class="bv-atlas-stage">'
        f'    <img src="{data["image"]}" alt="World map of Oversee">'
        + "".join(pins) +
        '  </div>'
        '</div>'
        '<div class="bv-atlas-gazetteer">'
        '  <div class="bv-atlas-gaz-title">Charted Gazetteer Index (Direct Archive Links)</div>'
        '  <div class="bv-atlas-gaz-grid">' + "".join(gazetteer) + '</div>'
        '</div>'
        '</div>\n'
        "::/pf\n"
    )
    README_PATH.write_text(content, encoding="utf-8")
    print("Built interactive Fantasy Atlas with", len(pins), "pins and accessible gazetteer")

if __name__ == "__main__":
    main()
