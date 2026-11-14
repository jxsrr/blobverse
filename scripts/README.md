# scripts/

Tooling audit & guard untuk Blobverse wiki.

## check_broken_links.py

Audit wiki links di `Dungeon Master Notes/`. Default skip DM-only blocks; `--include-dm` untuk scope penuh. `--staged` scan hanya staged files (dipakai pre-commit hook). Default warning-only; `--strict` untuk exit 1 pada broken/ambiguous.

## broken_links_whitelist.txt

Target wikilink yang sengaja di-whitelist (future session placeholder). Bukan untuk menyembunyikan broken link yang perlu diperbaiki.

## hooks/pre-commit

Source of truth untuk git pre-commit hook. Install via:

    bash scripts/install-hooks.sh

Behavior (urut):
1. Jalankan `publish-mirror.py` jika ada staged source di `Dungeon Master Notes/`.
2. Broken-link check pada staged source (non-blocking, warning-only).
3. DM-leak guard: exit 1 jika `_player/` mengandung `Dungeon Master ONLY` atau baris yang diawali `%% DM`.
4. Stage `_player/Dungeon Master Notes/`.

## install-hooks.sh

Copy `scripts/hooks/*` ke `.git/hooks/` + chmod +x.
