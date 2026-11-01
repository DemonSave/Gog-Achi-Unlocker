# GOG Achievement Unlocker

A small, dependency-free tool that unlocks or re-locks **GOG achievements** through GOG's own
server-side APIs, plus a dark-themed desktop GUI with achievement descriptions, a built-in guide
and filters.

It ships in two flavours that share the same engine:

| Executable | What it is |
| --- | --- |
| `dist/gog_unlocker.exe` | Console CLI |
| `dist/gog_unlocker_gui.exe` | Tkinter GUI (single window, no console) |

> **Use at your own risk.** Modifying achievement state through unofficial endpoints is not
> sanctioned by GOG and can put your library at risk. GOG's Terms of Service (§11.1(e)/(f) and
> §17.2) prohibit tampering with the service and allow account/library suspension. Only run this
> against your own account, and prefer the dry-run mode first.

## How it works

No local Galaxy database is touched — Galaxy overwrites its own files on every sync, so editing
them is pointless. The tool talks to GOG directly:

1. Reads the **Galaxy refresh token** from the Windows registry
   (`HKCU\Software\GOG.com\Galaxy`, value `refreshToken`).
2. Exchanges it for an access token at `https://auth.gog.com/token`
   (`grant_type=refresh_token`, `without_new_session=1`, Galaxy client credentials).
3. Lists owned products via `https://embed.gog.com/user/data/games`.
4. Resolves each product's **game client id/secret** from the latest public build published on
   [GOGDB](https://www.gogdb.org) — required because the gameplay API is scoped per game client.
5. Reads and writes achievements at
   `https://gameplay.gog.com/clients/{client_id}/users/{user_id}/achievements[/{achievement_id}]`.

Unlocking sends `{"date_unlocked": "YYYY-MM-DDTHH:MM:SS+0000"}` (a couple of seconds in the past);
locking sends `{"date_unlocked": null}`. Success is HTTP 200, 201 or 204.

## Requirements

- Windows (the token is read from the Windows registry).
- GOG Galaxy installed and signed in, so a valid refresh token exists.
- To run the sources: Python 3.9+ (standard library only — no `pip install` needed).
- The prebuilt `.exe` files need nothing at all.

## CLI usage

```
gog_unlocker.exe [-h] [--unlock [ACH_ID ...]] [--lock [ACH_ID ...]]
                 [-i] [--all] [--dry-run] [-y] [game_id]
```

- `game_id` — product ID. Omit it to list your owned games.
- `--unlock [ID ...]` — unlock the given achievements (without IDs it requires `--all`).
- `--lock [ID ...]` — re-lock the given achievements.
- `-i, --interactive` — numbered menu; cannot be combined with `--unlock`/`--lock`.
- `--all` — with `--unlock`/`--lock`: apply to every achievement in the requested state.
- `--dry-run` — print the operations without performing them.
- `-y, --yes` — skip the confirmation prompt.

Examples:

```console
# List your library (product ID + title)
gog_unlocker.exe

# Show a game's achievements with their current state
gog_unlocker.exe 1100902638

# Preview unlocking everything that is still locked
gog_unlocker.exe 1100902638 --unlock --all --dry-run

# Unlock two specific achievements
gog_unlocker.exe 1100902638 --unlock 59537454135153447 59537454139108112

# Re-lock a single achievement
gog_unlocker.exe 1100902638 --lock 59537454130968347

# Choose interactively (ENTER on an empty line exits)
gog_unlocker.exe 1100902638 -i
```

Exit code is `0` on success, `1` on error or when the operation is cancelled.
Messages are currently in Italian only.

## GUI

Launch `gog_unlocker_gui.exe`. The window opens already authenticated and loads your library in the
background, so it never freezes.

- **Library panel** (left) — search box, filter `All games / Only with achievements / Only without
  achievements`, and a badge per game with its achievement count. **Reload library** refreshes the
  product list; **Scan achievements** probes (and caches) the count for every game that has not been
  checked yet.
- **Achievements panel** (right) — columns for number, state, name, description and achievement ID,
  with a detail card showing the full text, rarity and unlock date of the selected row.
- **Actions** — unlock/lock the selected rows, unlock everything still locked, or refresh.
- **Preview (dry-run)** is **checked by default**: nothing is written to the server until you
  untick it. Every run asks for confirmation and logs what it did.
- **Check IDs…** — paste a list of product IDs and see how many achievements each one has, without
  touching your unlocked state.
- **Guide** — the full manual (rules, risks, troubleshooting) is available from the header button.

## Language

The GUI follows the language of the installed Windows: Italian for Italian systems, English
otherwise, falling back to English on anything unexpected.

Resolution order:

1. the `GOG_UNLOCKER_LANG` environment variable (`it` or `en`);
2. the Windows UI language (`GetUserDefaultUILanguage`, primary ID `0x10` → Italian, `0x09` → English);
3. the system locale;
4. English.

Translations, guide text and the language detection live in `gog_unlocker_i18n.py`. Adding a
language means adding one entry to the `TRANSLATIONS` dictionary and one to `GUIDES`; any code
listed in `TRANSLATIONS` becomes a valid `GOG_UNLOCKER_LANG` value automatically.

## Cache

Titles and achievement counts are cached so the tool does not re-query GOGDB on every run:

| Binary | Cache location |
| --- | --- |
| CLI | `gog_cache.json` next to the executable |
| GUI | `%LOCALAPPDATA%\GOGUnlocker\gog_cache.json` |

Deleting the file is safe: it is rebuilt on demand, only more slowly.

## Build from source

```console
python -m pip install pyinstaller

# Console CLI
python -m PyInstaller --onefile --name gog_unlocker --noconfirm --clean gog_unlocker.py

# Windowed GUI
python -m PyInstaller --onefile --windowed --name gog_unlocker_gui --noconfirm --clean gog_unlocker_gui.py
```

Both `--onefile` executables are self-contained; the `.spec` files in the repository reproduce the
same build. Keep `gog_unlocker_i18n.py` next to `gog_unlocker_gui.py` — PyInstaller bundles it
automatically when building from these sources.

## Troubleshooting

CLI messages are in Italian; the English explanation is on the right.

| Symptom | Cause and fix |
| --- | --- |
| `Refresh token rifiutato: apri GOG Galaxy, esci e rientra, poi riprova.` | The token in the registry is stale or missing. Open Galaxy, sign out and in again. |
| `GOGDB non ha dati per il prodotto … (HTTP 404).` | The product has no GOGDB page (movie, DLC, pack, unreleased item) so no achievements can be queried. |
| `Nessuna build pubblica per …: credenziali non recuperabili.` | GOGDB has no listed build for the product yet; try again later. |
| `Impossibile leggere la libreria (HTTP …).` | Token expired mid-run, or a network/proxy problem. Re-run. |
| `Lettura achievement fallita (HTTP …): …` | The gameplay API refused the request: usually a game client whose credentials or token are no longer valid. |
| Library list appears shorter than the owned count | Products without a GOGDB page are skipped on purpose, so only real games are shown. |
| Some titles print with `?` in the console | Console that refuses UTF-8. The tool degrades gracefully instead of crashing; redirecting the output to a file avoids it. |
| Achievement not visible in Galaxy after unlocking | Galaxy caches achievements locally; a sync (or restart of Galaxy) refreshes the display. |
