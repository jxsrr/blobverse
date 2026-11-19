from pathlib import Path

def sanitize_sensitive_content(text):
    forbidden = [
        "gavaevodata",
        "kerajaan grin",
        "zargoyle",
        "grin qain",
        "erah",
        "zargoth",
        "simon greenbottle",
        "ksatrian",
        "human vessel shell",
        "firsa",
        "architect",
        "topaju",
    ]
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        lower_line = line.lower()
        if any(term in lower_line for term in forbidden) and "<!--" not in line:
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


# --- PATCH UTAMA SANITASI FILE PLAYER ---
for md_file in Path("_player/Dungeon Master Notes").glob("**/*.md"):
    try:
        content = md_file.read_text(encoding="utf-8")
        cleaned = sanitize_sensitive_content(content)
        md_file.write_text(cleaned, encoding="utf-8")
    except Exception:
        pass
# ----------------------------------------
