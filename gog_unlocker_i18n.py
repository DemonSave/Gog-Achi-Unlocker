#!/usr/bin/env python3
"""
Localizzazione di GOG Achievement Unlocker.

La lingua viene scelta in automatico dalla lingua dell'interfaccia di Windows
(GetUserDefaultUILanguage), con ripiego sulla locale del sistema e infine
sull'inglese. Per forzarla si puo' impostare la variabile d'ambiente
GOG_UNLOCKER_LANG=it oppure GOG_UNLOCKER_LANG=en.
"""
import os

FALLBACK = "en"

TRANSLATIONS = {
    "it": {
        # finestra
        "window_title": "GOG Achievement Unlocker",
        "subtitle": "Sblocco e ripristino degli achievement tramite le API del client Galaxy",
        "btn_guide": "Guida",
        "btn_check_ids": "Verifica ID...",
        # sezioni
        "sec_library": "LIBRERIA",
        "sec_achievements": "ACHIEVEMENT",
        "filter_all": "Tutti i giochi",
        "filter_with": "Solo con achievement",
        "filter_without": "Solo senza achievement",
        "lib_info": "{total} giochi · {shown} mostrati",
        "lib_info_unknown": " · {unknown} non ancora analizzati",
        "btn_reload": "Ricarica libreria",
        "btn_scan": "Analizza achievement",
        "select_game": "Seleziona un gioco a sinistra.",
        # tabella achievement
        "col_n": "#",
        "col_state": "Stato",
        "col_name": "Nome",
        "col_desc": "Descrizione",
        "col_id": "ID",
        "state_on": "sbloccato",
        "state_off": "bloccato",
        "detail_empty_title": "Nessun achievement selezionato",
        "detail_empty_desc": "Seleziona una riga per leggere la descrizione completa.",
        "detail_no_desc": "Questo achievement non ha una descrizione.",
        "hidden": "nascosto",
        # pulsanti
        "btn_refresh": "Aggiorna",
        "btn_unlock_sel": "Sblocca selezionati",
        "btn_lock_sel": "Blocca selezionati",
        "btn_unlock_all": "Sblocca tutti i bloccati",
        "chk_preview": "Anteprima (dry-run)",
        # stato
        "status_connecting": "Connessione a GOG in corso...",
        "status_connected": "Connesso. Carico la libreria...",
        "status_reading": "Lettura della libreria...",
        "status_lib_loaded": "Libreria caricata: {n} giochi.",
        "status_need_auth": "Accesso non ancora completato.",
        "status_need_library": "Libreria non ancora caricata.",
        "status_select_game": "Seleziona prima un gioco.",
        "status_no_targets": "Nessun achievement da modificare.",
        "status_select_rows": "Seleziona gli achievement e usa i pulsanti a destra.",
        "status_scan_done": "Analisi completata su {total} giochi: {with_ach} con achievement, {without} senza.",
        "status_scan_none": "Tutti i giochi sono gia' stati analizzati.",
        "status_result": "{done}/{total} {verb}.",
        "verb_unlock": "sbloccare",
        "verb_lock": "ri-bloccare",
        "loading_achievements": "Caricamento achievement di {pid}...",
        "game_summary": "Gioco {pid}: {total} achievement, {unlocked} sbloccati, {locked} bloccati.",
        "badge_count": "  ·  {n} ach",
        "badge_none": "  ·  nessun ach",
        "no_title": "(senza titolo)",
        "unknown_title": "(titolo sconosciuto)",
        # errori
        "err_refresh": "Refresh token rifiutato: apri GOG Galaxy, esci e rientra, poi riprova.",
        "err_library": "Libreria non disponibile (HTTP {code}).",
        "err_prefix": "ERRORE: ",
        # log
        "log_scan_start": "Analisi di {n} giochi (una richiesta per gioco)...",
        "log_scan_done": "Analisi terminata: {n} giochi esaminati.",
        "log_preview": "Anteprima: {done}/{total} {verb} (nessuna modifica inviata).",
        "log_applied": "Eseguito: {done}/{total} {verb} (inviato a GOG).",
        "log_item": "{mode} {op} {ach} -> {result}",
        "op_unlock": "unlock",
        "op_lock": "lock",
        "result_ok": "ok",
        "result_fail": "fallito",
        "mode_preview": "anteprima",
        "mode_done": "eseguito",
        # conferma
        "confirm_title": "Conferma",
        "confirm_body": "{verb} {n} achievement del gioco {pid}?\n\n{note}",
        "confirm_verb_unlock": "Sbloccare",
        "confirm_verb_lock": "Ri-bloccare",
        "confirm_preview": "Anteprima: non verra' inviato nulla a GOG.",
        "confirm_real": "Questa operazione modifica lo stato sul server GOG.",
        # dialogo verifica ID
        "ids_title": "Verifica ID",
        "ids_hint": "Incolla gli ID dei giochi (uno per riga o separati da spazio):",
        "ids_btn": "Verifica",
        "ids_close": "Chiudi",
        "ids_no_ids": "Nessun ID numerico trovato nel testo.",
        "ids_need_auth": "Accesso a GOG non ancora completato, riprova tra un istante.",
        "ids_checking": "Verifico {n} ID...",
        "ids_with": "{pid}  ·  {title}  ->  {n} achievement",
        "ids_without": "{pid}  ·  {title}  ->  nessun achievement",
        "ids_error": "{pid}  ->  errore: {err}",
        "ids_done": "-- verifica completata --",
        # guida
        "guide_title": "Guida — GOG Achievement Unlocker",
        "guide_close": "Chiudi",
    },
    "en": {
        "window_title": "GOG Achievement Unlocker",
        "subtitle": "Unlock and restore achievements through the official Galaxy client APIs",
        "btn_guide": "Guide",
        "btn_check_ids": "Check IDs...",
        "sec_library": "LIBRARY",
        "sec_achievements": "ACHIEVEMENTS",
        "filter_all": "All games",
        "filter_with": "Only with achievements",
        "filter_without": "Only without achievements",
        "lib_info": "{total} games · {shown} shown",
        "lib_info_unknown": " · {unknown} not analysed yet",
        "btn_reload": "Reload library",
        "btn_scan": "Analyse achievements",
        "select_game": "Pick a game on the left.",
        "col_n": "#",
        "col_state": "State",
        "col_name": "Name",
        "col_desc": "Description",
        "col_id": "ID",
        "state_on": "unlocked",
        "state_off": "locked",
        "detail_empty_title": "No achievement selected",
        "detail_empty_desc": "Select a row to read the full description.",
        "detail_no_desc": "This achievement has no description.",
        "hidden": "hidden",
        "btn_refresh": "Refresh",
        "btn_unlock_sel": "Unlock selected",
        "btn_lock_sel": "Lock selected",
        "btn_unlock_all": "Unlock all locked",
        "chk_preview": "Preview (dry-run)",
        "status_connecting": "Connecting to GOG...",
        "status_connected": "Connected. Loading the library...",
        "status_reading": "Reading the library...",
        "status_lib_loaded": "Library loaded: {n} games.",
        "status_need_auth": "Sign-in not completed yet.",
        "status_need_library": "Library not loaded yet.",
        "status_select_game": "Select a game first.",
        "status_no_targets": "No achievement to change.",
        "status_select_rows": "Select achievements and use the buttons on the right.",
        "status_scan_done": "Scan complete on {total} games: {with_ach} with achievements, {without} without.",
        "status_scan_none": "Every game has already been analysed.",
        "status_result": "{done}/{total} {verb}.",
        "verb_unlock": "unlocked",
        "verb_lock": "locked again",
        "loading_achievements": "Loading achievements for {pid}...",
        "game_summary": "Game {pid}: {total} achievements, {unlocked} unlocked, {locked} locked.",
        "badge_count": "  ·  {n} ach",
        "badge_none": "  ·  no ach",
        "no_title": "(no title)",
        "unknown_title": "(unknown title)",
        "err_refresh": "Refresh token rejected: open GOG Galaxy, sign out and in again, then retry.",
        "err_library": "Library unavailable (HTTP {code}).",
        "err_prefix": "ERROR: ",
        "log_scan_start": "Analysing {n} games (one request each)...",
        "log_scan_done": "Scan finished: {n} games examined.",
        "log_preview": "Preview: {done}/{total} {verb} (nothing sent).",
        "log_applied": "Done: {done}/{total} {verb} (sent to GOG).",
        "log_item": "{mode} {op} {ach} -> {result}",
        "op_unlock": "unlock",
        "op_lock": "lock",
        "result_ok": "ok",
        "result_fail": "failed",
        "mode_preview": "preview",
        "mode_done": "applied",
        "confirm_title": "Confirm",
        "confirm_body": "{verb} {n} achievements of game {pid}?\n\n{note}",
        "confirm_verb_unlock": "Unlock",
        "confirm_verb_lock": "Lock",
        "confirm_preview": "Preview: nothing will be sent to GOG.",
        "confirm_real": "This operation changes the state on the GOG servers.",
        "ids_title": "Check IDs",
        "ids_hint": "Paste game IDs (one per line or space separated):",
        "ids_btn": "Check",
        "ids_close": "Close",
        "ids_no_ids": "No numeric ID found in the text.",
        "ids_need_auth": "GOG sign-in not completed yet, try again in a moment.",
        "ids_checking": "Checking {n} IDs...",
        "ids_with": "{pid}  ·  {title}  ->  {n} achievements",
        "ids_without": "{pid}  ·  {title}  ->  no achievements",
        "ids_error": "{pid}  ->  error: {err}",
        "ids_done": "-- check complete --",
        "guide_title": "Guide — GOG Achievement Unlocker",
        "guide_close": "Close",
    },
}

GUIDES = {
    "it": """GOG Achievement Unlocker
========================

Cosa fa
-------
Sblocca o ri-blocca gli achievement di un gioco direttamente sui server GOG,
usando le stesse API del client Galaxy. Non tocca i database locali di Galaxy:
quelli vengono riconciliati col server, quindi qualsiasi modifica locale
verrebbe sovrascritta al primo sync.

Requisiti
---------
- GOG Galaxy installato e con l'utente gia' loggato: il refresh token viene
  letto dal registro (HKCU\\Software\\GOG.com\\Galaxy, valore refreshToken).
- Connessione a internet (auth.gog.com, gameplay.gog.com, gogdb.org).

Come si usa
-----------
1. La libreria si carica da sola all'avvio; i titoli arrivano da GOGDB man mano.
   Puoi filtrare per titolo o ID nel campo in alto a sinistra.
2. Clicca un gioco: a destra compaiono i suoi achievement, con stato e
   descrizione. Selezionandone uno, il riquadro sotto mostra il testo intero.
3. Seleziona le righe (Ctrl per aggiungerne, Shift per un intervallo) e usa
   "Sblocca selezionati" o "Blocca selezionati". "Sblocca tutti i bloccati" fa
   tutto in un colpo.
4. Ogni invio chiede conferma e scrive una riga nel log in basso.

Anteprima (dry-run)
-------------------
La casella "Anteprima" e' attiva di default: nessun dato viene inviato a GOG,
viene solo mostrato cosa succederebbe. Toglila solo quando vuoi modificare
davvero il tuo profilo.

Filtri per achievement
----------------------
La tendina sopra la libreria filtra i giochi che hanno o non hanno achievement.
Per saperlo bisogna interrogare GOG gioco per gioco, quindi la prima volta
premi "Analizza achievement": i risultati finiscono nella cache e restano
disponibili anche ai riavvii successivi. La scansione completa di una libreria
grande richiede qualche minuto: la barra di avanzamento mostra il progresso.

"Verifica ID..." apre un riquadro in cui incollare una lista di ID (uno per
riga o separati da spazio) e ti dice, per ognuno, quanti achievement ha.

Lingua
------
L'interfaccia segue la lingua di Windows. Si puo' forzare impostando la
variabile d'ambiente GOG_UNLOCKER_LANG=it oppure GOG_UNLOCKER_LANG=en.

Cosa aspettarti dopo uno sblocco
--------------------------------
- La data registrata e' quella dell'invio, non quella in cui hai giocato.
- "Blocca" riporta l'achievement a non sbloccato, ma non cancella i log lato
  server ne' eventuali conteggi gia' avvenuti.
- Il profilo e' pubblico: gli achievement compaiono agli altri utenti.

Avvertenza
----------
L'uso di script che interagiscono con i servizi GOG e' vietato dai Termini
(§11.1(e)/(f)) e puo' comportare la sospensione dell'accesso, anche ai contenuti
della libreria (§17.2). Usa il programma consapevolmente e solo sul tuo account.
""",
    "en": """GOG Achievement Unlocker
========================

What it does
------------
Unlocks or re-locks a game's achievements directly on the GOG servers, using the
same APIs as the Galaxy client. It never touches Galaxy's local databases: those
are reconciled with the server, so any local edit would be overwritten on the
next sync.

Requirements
------------
- GOG Galaxy installed with a signed-in user: the refresh token is read from the
  registry (HKCU\\Software\\GOG.com\\Galaxy, value refreshToken).
- Internet access (auth.gog.com, gameplay.gog.com, gogdb.org).

How to use it
-------------
1. The library loads on start; titles arrive from GOGDB as they are fetched.
   Filter by title or ID with the field on the left.
2. Click a game: its achievements appear on the right with state and
   description. Selecting a row shows the full text in the panel below.
3. Select rows (Ctrl to add, Shift for a range) and use "Unlock selected" or
   "Lock selected". "Unlock all locked" does the whole list at once.
4. Every run asks for confirmation and writes a line in the log at the bottom.

Preview (dry-run)
-----------------
The "Preview" box is on by default: nothing is sent to GOG, only what would
happen is shown. Turn it off only when you really want to change your profile.

Achievement filters
-------------------
The drop-down above the library filters games that have or have no
achievements. GOG has no bulk endpoint for that, so the first time press
"Analyse achievements": results are cached and remain available on later runs.
A full scan of a large library takes a few minutes; the progress bar shows it.

"Check IDs..." opens a box where you can paste a list of IDs (one per line or
space separated) and see how many achievements each one has.

Language
--------
The interface follows the Windows display language. It can be forced with the
environment variable GOG_UNLOCKER_LANG=it or GOG_UNLOCKER_LANG=en.

What to expect after an unlock
------------------------------
- The recorded date is the moment of the request, not when you played.
- "Lock" sets the achievement back to locked, but does not erase server-side
  logs or counts that already happened.
- Profiles are public: unlocked achievements are visible to other users.

Warning
-------
Scripts that interact with GOG services are forbidden by the Terms (§11.1(e)/(f))
and can lead to the access being suspended, including access to your library
(§17.2). Use the program knowingly and only on your own account.
""",
}


def detect_language():
    """Lingua dell'interfaccia di Windows, poi la locale, poi l'inglese."""
    override = os.environ.get("GOG_UNLOCKER_LANG", "").strip()
    if override:
        code = override.replace("-", "_").split(".")[0].split("_")[0].lower()[:2]
        if code in TRANSLATIONS:
            return code

    if os.name == "nt":
        try:
            import ctypes

            langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            primary = langid & 0xFF
            if primary == 0x10:
                return "it"
            if primary == 0x09:
                return "en"
        except Exception:  # noqa: BLE001 - euristica, non deve mai far fallire l'avvio
            pass

    try:
        import locale

        code = (locale.getlocale()[0] or "")[:2].lower()
        if code in TRANSLATIONS:
            return code
    except Exception:  # noqa: BLE001
        pass

    return FALLBACK


_current = detect_language()


def current_language():
    return _current


def set_language(code):
    """Forza la lingua (usato dai test); ignorato se non supportata."""
    global _current
    if code in TRANSLATIONS:
        _current = code
    return _current


def t(key, **kwargs):
    """Traduzione della chiave nella lingua corrente, con ripiego sull'inglese."""
    text = TRANSLATIONS.get(_current, TRANSLATIONS[FALLBACK]).get(key)
    if text is None:
        text = TRANSLATIONS[FALLBACK].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


def guide():
    return GUIDES.get(_current, GUIDES[FALLBACK])
