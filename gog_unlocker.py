#!/usr/bin/env python3
"""
gog_unlocker.py - sblocca / ri-blocca gli achievement GOG via API (stato salvato sui server GOG).

Richiede Windows con GOG Galaxy installato e l'utente loggato: il refresh token
viene letto dal registro (HKCU\\Software\\GOG.com\\Galaxy, valore "refreshToken").
Nessuna dipendenza esterna: solo standard library.

Uso (su Windows l'interprete puo' essere "py" invece di "python"):

    py gog_unlocker.py                                  # elenca i giochi posseduti
    py gog_unlocker.py 1558393671                       # elenca gli achievement del gioco
    py gog_unlocker.py 1558393671 --unlock --all        # sblocca tutti i bloccati
    py gog_unlocker.py 1558393671 --lock --all          # ri-blocca tutti gli sbloccati
    py gog_unlocker.py 1558393671 --unlock 58889697238411342 1234567
    py gog_unlocker.py 1558393671 --unlock 2 5               # per numero della lista
    py gog_unlocker.py 1558393671 -i                        # menu interattivo a numeri
    py gog_unlocker.py 1558393671 --lock 58889697238411342
    opzioni: --dry-run (mostra solo), -y (salta conferma)
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Credenziali del client GOG Galaxy (pubbliche, le stesse usate dal client desktop).
GALAXY_CLIENT_ID = "46899977096215655"
GALAXY_CLIENT_SECRET = "9d85c43b1482497dbbce61f6e4aa173a433796eeae2ca8c5f6129f2dc4de46d9"

AUTH_URL = "https://auth.gog.com/token"
GAMEPLAY_URL = "https://gameplay.gog.com/clients/{client_id}/users/{user_id}/achievements"
GOGDB_PRODUCT = "https://www.gogdb.org/data/products/{pid}/product.json"
GOGDB_BUILD = "https://www.gogdb.org/data/products/{pid}/builds/{bid}.json"
OWNED_GAMES_URL = "https://embed.gog.com/user/data/games"

# Cache accanto allo script; in un eseguibile PyInstaller __file__ sta nella cartella
# temporanea del bundle, quindi si usa il percorso dell'exe.
if getattr(sys, "frozen", False):
    CACHE_PATH = Path(sys.executable).resolve().with_name("gog_cache.json")
else:
    CACHE_PATH = Path(__file__).resolve().with_name("gog_cache.json")


def http(method, url, token=None, body=None, timeout=30):
    headers = {"Accept": "application/json", "User-Agent": "gog-unlocker/1.0"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"raw": raw[:400]}
        return exc.code, payload
    except urllib.error.URLError as exc:
        sys.exit("Errore di rete: {}".format(exc.reason))


def read_refresh_token():
    if os.name != "nt":
        sys.exit("Questo script legge il token da GOG Galaxy per Windows.")
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\GOG.com\Galaxy") as key:
            value, _ = winreg.QueryValueEx(key, "refreshToken")
            return value
    except FileNotFoundError:
        sys.exit("Chiave di registro non trovata: avvia GOG Galaxy e fai login una volta.")
    except OSError as exc:
        sys.exit("Impossibile leggere il refresh token: {}".format(exc))


def authenticate(refresh_token, client_id=GALAXY_CLIENT_ID, client_secret=GALAXY_CLIENT_SECRET):
    query = urllib.parse.urlencode(
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "without_new_session": "1",  # non invalida la sessione di Galaxy
        }
    )
    status, payload = http("GET", AUTH_URL + "?" + query)
    if status != 200 or not payload.get("access_token"):
        return None
    return payload


def load_cache():
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_cache(cache):
    try:
        CACHE_PATH.write_text(json.dumps(cache, indent=1), encoding="utf-8")
    except OSError:
        pass


def game_credentials(product_id, cache):
    """client_id/client_secret del gioco, presi dall'ultima build pubblica su GOGDB."""
    entry = cache.setdefault(str(product_id), {})
    if entry.get("client_id"):
        return entry["client_id"], entry.get("client_secret") or ""
    status, product = http("GET", GOGDB_PRODUCT.format(pid=product_id))
    if status != 200:
        sys.exit("GOGDB non ha dati per il prodotto {} (HTTP {}).".format(product_id, status))
    if product.get("title"):
        entry["title"] = product["title"]
    builds = [
        b for b in (product.get("builds") or [])
        if b.get("listed") and b.get("date_published")
    ]
    if not builds:
        sys.exit("Nessuna build pubblica per {}: credenziali non recuperabili.".format(product_id))
    latest = max(builds, key=lambda b: b["date_published"])
    status, details = http("GET", GOGDB_BUILD.format(pid=product_id, bid=latest["id"]))
    if status != 200 or not details.get("clientId"):
        sys.exit("Client credentials assenti per il prodotto {}.".format(product_id))
    entry["client_id"] = details["clientId"]
    entry["client_secret"] = details.get("clientSecret") or ""
    save_cache(cache)
    return entry["client_id"], entry["client_secret"]


def get_achievements(client_id, user_id, token):
    url = GAMEPLAY_URL.format(client_id=client_id, user_id=user_id)
    status, payload = http("GET", url, token)
    if status != 200:
        sys.exit("Lettura achievement fallita (HTTP {}): {}".format(status, payload))
    return payload.get("items") or []


def set_achievement(client_id, user_id, achievement_id, tokens, unlock, dry_run=False):
    url = GAMEPLAY_URL.format(client_id=client_id, user_id=user_id) + "/" + achievement_id
    if unlock:
        # leggermente nel passato, come fanno gli altri manager
        stamp = (datetime.now(timezone.utc) - timedelta(seconds=3)).strftime("%Y-%m-%dT%H:%M:%S%z")
    else:
        stamp = None
    body = {"date_unlocked": stamp}
    if dry_run:
        print("  [dry-run] {} {} -> {}".format("unlock" if unlock else "lock", achievement_id, stamp))
        return True
    last = None
    for token in tokens:
        status, payload = http("POST", url, token, body)
        if status in (200, 201, 204):
            return True
        last = (status, payload)
        if status != 401:  # 401 = token emesso per il client sbagliato, prova il successivo
            break
    print("  x {}: HTTP {} {}".format(achievement_id, last[0], last[1]))
    return False


def list_games(token, cache):
    status, payload = http("GET", OWNED_GAMES_URL, token)
    if status != 200:
        sys.exit("Impossibile leggere la libreria (HTTP {}).".format(status))
    owned = payload.get("owned") or []
    total = len(owned)
    print("Giochi posseduti ({}):".format(total))
    for index, pid in enumerate(owned, 1):
        entry = cache.setdefault(str(pid), {})
        if not entry.get("title"):
            status, product = http("GET", GOGDB_PRODUCT.format(pid=pid))
            if status == 404:
                continue  # film, DLC, voci senza pagina prodotto
            if status == 200:
                entry["title"] = product.get("title") or ""
        print("  {:>10}  {}".format(pid, entry.get("title") or "(titolo non disponibile)"))
        if index % 20 == 0 or index == total:
            # i titoli arrivano da GOGDB, un titolo per richiesta: serve un indicatore
            print("  ... {}/{}".format(index, total), file=sys.stderr, flush=True)
    save_cache(cache)


def resolve_selection(selection, items, game_id):
    """Converte una selezione mista in achievement_id: accetta i numeri della lista o gli ID."""
    by_id = {i.get("achievement_id") for i in items}
    targets, missing = [], []
    for token in selection:
        token = str(token).strip()
        if token.isdigit() and 1 <= int(token) <= len(items):
            targets.append(items[int(token) - 1]["achievement_id"])
        elif token in by_id:
            targets.append(token)
        else:
            missing.append(token)
    if missing:
        sys.exit(
            "Nessun achievement con questi numeri/ID nel gioco {}: {}".format(
                game_id, ", ".join(missing)
            )
        )
    return targets


def ask_interactively(items, game_id):
    """Menu a numeri: chiede quali achievement e se sbloccarli o ri-bloccarli."""
    if not items:
        print("Questo gioco non ha achievement.")
        return None, []
    try:
        raw = input(
            "\nNumeri degli achievement (separati da spazio, 'all', INVIO per uscire): "
        ).strip()
    except EOFError:  # input terminato (Ctrl+Z, pipe): uscita pulita, senza traceback
        print()
        return None, []
    if not raw:
        return None, []
    try:
        mode = input("Sbloccare [u] o ri-bloccare [l]? ").strip().lower()
    except EOFError:
        print()
        return None, []
    unlock = mode != "l"
    if raw.lower() == "all":
        source = [i for i in items if bool(i.get("date_unlocked")) != unlock]
        if not source:
            print("Nessun achievement in quello stato.")
            return None, []
        return unlock, [i["achievement_id"] for i in source]
    return unlock, resolve_selection(raw.replace(",", " ").split(), items, game_id)


def setup_output():
    """Console Windows: cp1252/cp850 non sanno scrivere molti titoli GOG ('ō', 'Ł', ...)
    e una print() farebbe morire il programma a metà elenco con UnicodeEncodeError.
    Passa a UTF-8 quando la console lo accetta, altrimenti degrada senza crashare."""
    utf8_console = False
    if sys.platform == "win32":
        try:
            import ctypes

            utf8_console = bool(ctypes.windll.kernel32.SetConsoleOutputCP(65001))
        except Exception:  # noqa: BLE001 - il ripiego gestisce comunque l'output
            utf8_console = False
    for stream in (sys.stdout, sys.stderr):
        if stream is None:  # exe --windowed
            continue
        try:
            if utf8_console or not stream.isatty():
                stream.reconfigure(encoding="utf-8", errors="replace")
            else:
                stream.reconfigure(errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


def main(argv=None):
    setup_output()
    parser = argparse.ArgumentParser(
        description="Sblocca o ri-blocca gli achievement GOG (modifica lo stato sul server GOG)."
    )
    parser.add_argument(
        "game_id", nargs="?", type=int,
        help="product ID del gioco (omesso: elenca i giochi posseduti)",
    )
    parser.add_argument(
        "--unlock", nargs="*", metavar="ACH_ID", default=None,
        help="sblocca gli achievement indicati (senza ID: richiede --all)",
    )
    parser.add_argument(
        "--lock", nargs="*", metavar="ACH_ID", default=None,
        help="ri-blocca gli achievement indicati (senza ID: richiede --all)",
    )
    parser.add_argument(
        "-i", "--interactive", action="store_true",
        help="menu a numeri per scegliere quali achievement sbloccare o ri-bloccare",
    )
    parser.add_argument("--all", action="store_true", help="con --unlock/--lock: applica a tutti")
    parser.add_argument("--dry-run", action="store_true", help="mostra le operazioni senza eseguirle")
    parser.add_argument("-y", "--yes", action="store_true", help="salta la conferma")
    args = parser.parse_args(argv)

    if args.unlock is not None and args.lock is not None:
        sys.exit("Usa --unlock oppure --lock, non entrambi.")
    if args.interactive and (args.unlock is not None or args.lock is not None):
        sys.exit("Usa -i da sola, oppure --unlock/--lock con i numeri o gli ID.")

    refresh_token = read_refresh_token()
    auth = authenticate(refresh_token)
    if not auth:
        sys.exit("Refresh token rifiutato: apri GOG Galaxy, esci e rientra, poi riprova.")
    user_id, galaxy_token = auth["user_id"], auth["access_token"]
    cache = load_cache()

    if not args.game_id:
        list_games(galaxy_token, cache)
        return 0

    client_id, client_secret = game_credentials(args.game_id, cache)
    items = get_achievements(client_id, user_id, galaxy_token)

    unlocked = [i for i in items if i.get("date_unlocked")]
    locked = [i for i in items if not i.get("date_unlocked")]
    print(
        "Achievement del prodotto {}: {} totali, {} sbloccati, {} bloccati.\n".format(
            args.game_id, len(items), len(unlocked), len(locked)
        )
    )
    for index, item in enumerate(items, 1):
        print(
            "  {:>3}) [{}] {:>20}  {}{}".format(
                index,
                "v" if item.get("date_unlocked") else " ",
                item.get("achievement_id"),
                item.get("name") or "",
                "" if item.get("visible", True) else "  (nascosto)",
            )
        )

    if args.unlock is None and args.lock is None and not args.interactive:
        return 0

    if args.interactive:
        unlock, targets = ask_interactively(items, args.game_id)
        if not targets:
            print("Nessuna modifica.")
            return 0
    else:
        unlock = args.unlock is not None
        selection = args.unlock if unlock else args.lock
        if args.all:
            targets = [i["achievement_id"] for i in (locked if unlock else unlocked)]
        elif selection:
            targets = resolve_selection(selection, items, args.game_id)
        else:
            sys.exit("Indica i numeri/ID degli achievement oppure aggiungi --all.")

    if not targets:
        print("\nNessun achievement da modificare.")
        return 0

    verb = "sbloccare" if unlock else "ri-bloccare"
    print("\nSto per {} {} achievement su {}.".format(verb, len(targets), args.game_id))
    if not args.yes and not args.dry_run:
        try:
            answer = input("Continuare? [s/N] ").strip().lower()
        except EOFError:  # nessuna risposta disponibile: equivale a "no"
            print()
            answer = ""
        if answer not in ("s", "si", "si'", "y", "yes"):
            print("Annullato.")
            return 1

    # Il POST vuole un token emesso per il client del gioco; se non arriva, si ripiega su Galaxy.
    tokens = []
    game_auth = authenticate(refresh_token, client_id, client_secret)
    if game_auth and game_auth.get("access_token"):
        tokens.append(game_auth["access_token"])
    if galaxy_token not in tokens:
        tokens.append(galaxy_token)

    done = 0
    for achievement_id in targets:
        if set_achievement(client_id, user_id, achievement_id, tokens, unlock, args.dry_run):
            done += 1
            if not args.dry_run:
                print("  OK {} {}".format("sbloccato" if unlock else "ri-bloccato", achievement_id))

    print("\nFatto: {}/{}.".format(done, len(targets)))
    return 0 if done == len(targets) else 2


if __name__ == "__main__":
    # In modalita' interattiva (anche dall'exe aperto col doppio clic) la finestra
    # resterebbe aperta solo per un istante: si aspetta INVIO prima di uscire.
    interactive = "-i" in sys.argv or "--interactive" in sys.argv
    try:
        code = main()
    except SystemExit as exc:
        if isinstance(exc.code, str):
            print(exc.code, file=sys.stderr)
            code = 1
        else:
            code = exc.code or 0
    if interactive:
        try:
            if sys.stdin.isatty():
                input("\nPremi INVIO per chiudere.")
        except (EOFError, KeyboardInterrupt):
            pass
    raise SystemExit(code)
