#!/usr/bin/env python3
"""
Interfaccia grafica (Tkinter) per gog_unlocker.

Usa lo stesso backend di gog_unlocker.py (registro di Galaxy -> auth.gog.com ->
gameplay.gog.com), ma con tema scuro, guida integrata, descrizione di ogni
achievement, filtri sui giochi che hanno/non hanno achievement e interfaccia
tradotta secondo la lingua di Windows (italiano/inglese).
Tutte le chiamate di rete girano in un thread separato: la finestra non si blocca.
"""
import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import gog_unlocker as backend
import gog_unlocker_i18n as i18n
from gog_unlocker_i18n import t as T

FILTER_ALL = "all"
FILTER_WITH = "with"
FILTER_WITHOUT = "without"
FILTER_CODES = (FILTER_ALL, FILTER_WITH, FILTER_WITHOUT)
FILTER_KEYS = ("filter_all", "filter_with", "filter_without")

COLORS = {
    "bg": "#13151a",
    "surface": "#1b1e26",
    "surface2": "#242936",
    "border": "#2f3543",
    "text": "#e8eaf0",
    "muted": "#98a1b3",
    "accent": "#8b6cf0",
    "accent_dark": "#6d4fd8",
    "success": "#4ade80",
    "select": "#352c58",
}


def cache_path():
    """Cache in %LOCALAPPDATA%: una cartella scrivibile anche se l'exe sta altrove."""
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    folder = os.path.join(base, "GOGUnlocker")
    try:
        os.makedirs(folder, exist_ok=True)
        return Path(folder) / "gog_cache.json"
    except OSError:
        return Path(__file__).resolve().with_name("gog_cache.json")


# Il backend legge/scrive questa costante: la puntiamo a un percorso per-utente.
backend.CACHE_PATH = cache_path()


def apply_theme(root):
    """Tema scuro coerente su tutti i widget ttk."""
    root.configure(bg=COLORS["bg"])
    style = ttk.Style(root)
    try:
        style.theme_use("clam")  # l'unico tema che rispetta i colori personalizzati
    except tk.TclError:
        pass

    root.option_add("*TCombobox*Listbox.background", COLORS["surface"])
    root.option_add("*TCombobox*Listbox.foreground", COLORS["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", COLORS["accent"])
    root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")

    style.configure(
        ".",
        background=COLORS["bg"],
        foreground=COLORS["text"],
        fieldbackground=COLORS["surface"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["border"],
        darkcolor=COLORS["border"],
        troughcolor=COLORS["surface2"],
        focuscolor=COLORS["accent"],
    )
    style.configure("TFrame", background=COLORS["bg"])
    style.configure("Card.TFrame", background=COLORS["surface"])
    style.configure("Header.TFrame", background=COLORS["surface"])
    style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"])
    style.configure("Muted.TLabel", background=COLORS["bg"], foreground=COLORS["muted"])
    style.configure(
        "Title.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["accent"],
        font=("Segoe UI Semibold", 14),
    )
    style.configure(
        "Subtitle.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["muted"],
        font=("Segoe UI", 9),
    )
    style.configure(
        "Section.TLabel",
        background=COLORS["bg"],
        foreground=COLORS["accent"],
        font=("Segoe UI Semibold", 10),
    )
    style.configure("TButton", background=COLORS["surface2"], foreground=COLORS["text"],
                    borderwidth=0, padding=(10, 6), focusthickness=0)
    style.map(
        "TButton",
        background=[("pressed", COLORS["accent_dark"]), ("active", COLORS["accent"])],
        foreground=[("active", "#ffffff")],
    )
    style.configure("Accent.TButton", background=COLORS["accent"], foreground="#ffffff",
                    borderwidth=0, padding=(12, 6))
    style.map(
        "Accent.TButton",
        background=[("pressed", COLORS["accent_dark"]), ("active", COLORS["accent_dark"])],
    )
    style.configure("TEntry", fieldbackground=COLORS["surface"], foreground=COLORS["text"],
                    insertcolor=COLORS["text"], bordercolor=COLORS["border"], padding=6)
    style.map("TEntry", bordercolor=[("focus", COLORS["accent"])])
    style.configure("TCombobox", fieldbackground=COLORS["surface"],
                    background=COLORS["surface2"], foreground=COLORS["text"],
                    arrowcolor=COLORS["text"], bordercolor=COLORS["border"], padding=5)
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", COLORS["surface"])],
        foreground=[("readonly", COLORS["text"])],
        bordercolor=[("focus", COLORS["accent"])],
    )
    style.configure("TCheckbutton", background=COLORS["bg"], foreground=COLORS["text"],
                    focuscolor=COLORS["accent"])
    style.map(
        "TCheckbutton",
        background=[("active", COLORS["bg"])],
        indicatorcolor=[("selected", COLORS["accent"]), ("!selected", COLORS["surface2"])],
    )
    style.configure("Treeview", background=COLORS["surface"],
                    fieldbackground=COLORS["surface"], foreground=COLORS["text"],
                    borderwidth=0, rowheight=25)
    style.map(
        "Treeview",
        background=[("selected", COLORS["select"])],
        foreground=[("selected", "#ffffff")],
    )
    style.configure("Treeview.Heading", background=COLORS["surface2"],
                    foreground=COLORS["muted"], borderwidth=0, padding=(6, 7),
                    font=("Segoe UI Semibold", 9))
    style.map("Treeview.Heading", background=[("active", COLORS["accent_dark"])],
              foreground=[("active", "#ffffff")])
    style.configure("Horizontal.TProgressbar", background=COLORS["accent"],
                    troughcolor=COLORS["surface2"], borderwidth=0, thickness=8)
    style.configure("TPanedwindow", background=COLORS["bg"])
    style.configure("Vertical.TScrollbar", background=COLORS["surface2"],
                    troughcolor=COLORS["bg"], bordercolor=COLORS["bg"],
                    arrowcolor=COLORS["muted"])
    return style


class LogWriter:
    """In un exe --windowed sys.stdout e' None: i print del backend finiscono nel log."""

    def __init__(self, app):
        self.app = app

    def write(self, text):
        text = text.rstrip()
        if text:
            self.app.post("log", text)

    def flush(self):
        pass


class GuideWindow(tk.Toplevel):
    """Guida d'uso, apribile dal pulsante nell'intestazione."""

    def __init__(self, app):
        super().__init__(app.root)
        self.title(T("guide_title"))
        self.configure(bg=COLORS["bg"])
        self.geometry("740x660")
        self.transient(app.root)

        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=12, pady=12)
        text = tk.Text(
            body,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            padx=14,
            pady=12,
            font=("Consolas", 9),
        )
        scroll = ttk.Scrollbar(body, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        text.insert("1.0", i18n.guide())
        text.configure(state="disabled")

        ttk.Button(self, text=T("guide_close"), command=self.destroy).pack(pady=(0, 12))


class IdCheckDialog(tk.Toplevel):
    """Verifica rapida: incolli una lista di ID e vedi quanti achievement hanno."""

    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title(T("ids_title"))
        self.configure(bg=COLORS["bg"])
        self.geometry("580x480")
        self.transient(app.root)
        self.queue = queue.Queue()

        ttk.Label(self, text=T("ids_hint")).pack(anchor="w", padx=12, pady=(12, 4))
        self.input = tk.Text(self, height=6, bg=COLORS["surface"], fg=COLORS["text"],
                             insertbackground=COLORS["text"], relief="flat", padx=10, pady=8)
        self.input.pack(fill="x", padx=12)

        row = ttk.Frame(self)
        row.pack(fill="x", padx=12, pady=8)
        ttk.Button(row, text=T("ids_btn"), style="Accent.TButton", command=self.start).pack(side="left")
        ttk.Button(row, text=T("ids_close"), command=self.destroy).pack(side="right")

        self.out = tk.Text(self, bg=COLORS["surface"], fg=COLORS["text"], relief="flat",
                           wrap="word", padx=10, pady=8, state="disabled")
        self.out.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.after(100, self._drain)

    def _write(self, line):
        self.out.configure(state="normal")
        self.out.insert("end", line + "\n")
        self.out.see("end")
        self.out.configure(state="disabled")

    def start(self):
        ids = []
        raw = self.input.get("1.0", "end").replace(",", " ").split()
        for token in raw:
            if token.isdigit() and int(token) not in ids:
                ids.append(int(token))
        if not ids:
            self._write(T("ids_no_ids"))
            return
        if not self.app.auth:
            self._write(T("ids_need_auth"))
            return
        self._write(T("ids_checking", n=len(ids)))

        def worker():
            for pid in ids:
                try:
                    count = self.app.count_for(pid)
                    title = (
                        self.app.titles.get(pid)
                        or self.app.cache.get(str(pid), {}).get("title")
                        or T("unknown_title")
                    )
                    key = "ids_with" if count else "ids_without"
                    self.queue.put(T(key, pid=pid, title=title, n=count))
                except SystemExit as exc:
                    self.queue.put(T("ids_error", pid=pid, err=exc.code))
                except Exception as exc:  # noqa: BLE001 - mostrato all'utente
                    self.queue.put(T("ids_error", pid=pid, err=exc))
            self.queue.put(None)

        threading.Thread(target=worker, daemon=True).start()

    def _drain(self):
        try:
            while True:
                line = self.queue.get_nowait()
                if line is None:
                    self.app.cache_save()
                    self._write(T("ids_done"))
                else:
                    self._write(line)
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(100, self._drain)


class App:
    def __init__(self, root):
        self.root = root
        self.style = apply_theme(root)
        self.queue = queue.Queue()
        self.refresh_token = None
        self.auth = None
        self.cache = backend.load_cache()
        self.games = []       # product ID nell'ordine della libreria
        self.titles = {}      # product ID -> titolo
        self.counts = {}      # product ID -> numero di achievement (dalla cache)
        self.items = []       # achievement del gioco aperto
        self.current_pid = None
        self.preview_var = tk.BooleanVar(value=True)  # dry-run attivo di default

        for key, entry in self.cache.items():
            if isinstance(entry, dict) and "achievements_count" in entry:
                try:
                    self.counts[int(key)] = int(entry["achievements_count"])
                except (TypeError, ValueError):
                    pass

        for stream in ("stdout", "stderr"):
            if getattr(sys, stream, None) is None:
                setattr(sys, stream, LogWriter(self))

        self._build_ui()
        self.root.after(80, self._drain)
        self._spawn(self._login_worker)

    # ---------------------------------------------------------------- interfaccia
    def _build_ui(self):
        self.root.title(T("window_title"))
        self.root.geometry("1180x720")
        self.root.minsize(940, 560)
        self.root.columnconfigure(0, weight=1)

        header = ttk.Frame(self.root, style="Header.TFrame", padding=(16, 12))
        header.grid(row=0, column=0, sticky="ew")
        titles = ttk.Frame(header, style="Header.TFrame")
        titles.pack(side="left")
        tk.Label(titles, text=T("window_title"), bg=COLORS["surface"], fg=COLORS["accent"],
                 font=("Segoe UI Semibold", 14), anchor="w").pack(anchor="w")
        ttk.Label(titles, text=T("subtitle"), style="Subtitle.TLabel").pack(anchor="w")
        ttk.Button(header, text=T("btn_check_ids"),
                   command=lambda: IdCheckDialog(self)).pack(side="right", padx=(8, 0))
        ttk.Button(header, text=T("btn_guide"),
                   command=lambda: GuideWindow(self)).pack(side="right")

        bar = ttk.Frame(self.root, padding=(16, 8, 16, 4))
        bar.grid(row=1, column=0, sticky="new")
        self.status = tk.StringVar(value=T("status_connecting"))
        ttk.Label(bar, textvariable=self.status, style="Muted.TLabel").pack(side="left")

        body = ttk.Panedwindow(self.root, orient="horizontal")
        body.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 8))
        self.root.rowconfigure(2, weight=1)

        # ---- colonna sinistra: libreria
        left = ttk.Frame(body)
        ttk.Label(left, text=T("sec_library"), style="Section.TLabel").pack(anchor="w")
        self.library_info = tk.StringVar(value="")
        ttk.Label(left, textvariable=self.library_info, style="Muted.TLabel").pack(anchor="w")

        self.filter_var = tk.StringVar()
        search = ttk.Entry(left, textvariable=self.filter_var)
        search.pack(fill="x", pady=(6, 4))
        search.bind("<KeyRelease>", lambda _event: self._refresh_games())

        self.ach_combo = ttk.Combobox(
            left,
            values=[T(key) for key in FILTER_KEYS],
            state="readonly",
        )
        self.ach_combo.current(0)
        self.ach_combo.pack(fill="x", pady=(0, 6))
        self.ach_combo.bind("<<ComboboxSelected>>", lambda _event: self._refresh_games())

        games_box = ttk.Frame(left)
        games_box.pack(fill="both", expand=True)
        self.game_tree = ttk.Treeview(
            games_box, columns=("gioco",), show="headings", selectmode="browse"
        )
        self.game_tree.heading("gioco", text="ID · " + T("col_name"))
        self.game_tree.column("gioco", width=340, anchor="w")
        games_scroll = ttk.Scrollbar(games_box, orient="vertical", command=self.game_tree.yview)
        self.game_tree.configure(yscrollcommand=games_scroll.set)
        self.game_tree.pack(side="left", fill="both", expand=True)
        games_scroll.pack(side="right", fill="y")
        self.game_tree.bind("<<TreeviewSelect>>", self._on_game_select)

        left_buttons = ttk.Frame(left)
        left_buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(left_buttons, text=T("btn_reload"), command=self.load_library).pack(
            side="left"
        )
        ttk.Button(left_buttons, text=T("btn_scan"),
                   command=self.scan_achievements).pack(side="left", padx=(6, 0))
        body.add(left, weight=1)

        # ---- colonna destra: achievement
        right = ttk.Frame(body)
        ttk.Label(right, text=T("sec_achievements"), style="Section.TLabel").pack(anchor="w")
        self.game_label = tk.StringVar(value=T("select_game"))
        ttk.Label(right, textvariable=self.game_label, style="Muted.TLabel").pack(anchor="w")

        ach_box = ttk.Frame(right)
        ach_box.pack(fill="both", expand=True, pady=(6, 6))
        self.ach_tree = ttk.Treeview(
            ach_box,
            columns=("n", "stato", "nome", "descrizione", "id"),
            show="headings",
            selectmode="extended",
        )
        for column, title, width, anchor, stretch in (
            ("n", T("col_n"), 44, "center", False),
            ("stato", T("col_state"), 96, "w", False),
            ("nome", T("col_name"), 230, "w", False),
            ("descrizione", T("col_desc"), 340, "w", True),
            ("id", T("col_id"), 170, "w", False),
        ):
            self.ach_tree.heading(column, text=title)
            self.ach_tree.column(column, width=width, anchor=anchor, stretch=stretch)
        ach_scroll = ttk.Scrollbar(ach_box, orient="vertical", command=self.ach_tree.yview)
        self.ach_tree.configure(yscrollcommand=ach_scroll.set)
        self.ach_tree.pack(side="left", fill="both", expand=True)
        ach_scroll.pack(side="right", fill="y")
        self.ach_tree.tag_configure("unlocked", foreground=COLORS["success"])
        self.ach_tree.bind("<<TreeviewSelect>>", self._on_ach_select)

        detail = ttk.Frame(right, style="Card.TFrame", padding=10)
        detail.pack(fill="x", pady=(0, 8))
        self.detail_title = tk.Label(
            detail, text=T("detail_empty_title"), bg=COLORS["surface"],
            fg=COLORS["text"], font=("Segoe UI Semibold", 11), anchor="w", justify="left",
        )
        self.detail_title.pack(anchor="w")
        self.detail_meta = tk.Label(
            detail, text="", bg=COLORS["surface"], fg=COLORS["muted"],
            font=("Segoe UI", 9), anchor="w", justify="left",
        )
        self.detail_meta.pack(anchor="w", pady=(2, 4))
        self.detail_desc = tk.Label(
            detail, text=T("detail_empty_desc"), bg=COLORS["surface"], fg=COLORS["text"],
            font=("Segoe UI", 9), anchor="w", justify="left", wraplength=620,
        )
        self.detail_desc.pack(anchor="w")
        detail.bind(
            "<Configure>",
            lambda event: self.detail_desc.configure(wraplength=max(320, event.width - 30)),
        )

        actions = ttk.Frame(right)
        actions.pack(fill="x")
        ttk.Button(actions, text=T("btn_refresh"),
                   command=self.reload_achievements).pack(side="left")
        ttk.Button(actions, text=T("btn_unlock_sel"), style="Accent.TButton",
                   command=self.unlock_selected).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text=T("btn_lock_sel"),
                   command=self.lock_selected).pack(side="left", padx=6)
        ttk.Button(actions, text=T("btn_unlock_all"),
                   command=self.unlock_all).pack(side="left")
        self.preview_check = ttk.Checkbutton(
            actions, text=T("chk_preview"), variable=self.preview_var
        )
        self.preview_check.pack(side="right")
        body.add(right, weight=2)

        footer = ttk.Frame(self.root, padding=(16, 0, 16, 12))
        footer.grid(row=3, column=0, sticky="ew")
        self.progress = ttk.Progressbar(footer, mode="determinate", maximum=100)
        self.progress.pack(fill="x")
        self.log = tk.Text(footer, height=6, wrap="word", state="disabled",
                           bg=COLORS["surface"], fg=COLORS["muted"], relief="flat",
                           padx=10, pady=6, font=("Consolas", 9))
        self.log.pack(fill="both", expand=True, pady=(6, 0))

    # ------------------------------------------------------------------ threading
    def post(self, kind, data=None):
        """Dal thread di lavoro verso la UI: solo la coda e' thread-safe."""
        self.queue.put((kind, data))

    def _spawn(self, worker):
        def run():
            try:
                worker()
            except SystemExit as exc:
                self.post("error", str(exc.code) if exc.code else T("status_need_auth"))
            except Exception as exc:  # noqa: BLE001 - l'errore va mostrato, non ingoiato
                self.post("error", "{}: {}".format(type(exc).__name__, exc))

        threading.Thread(target=run, daemon=True).start()

    def _drain(self):
        try:
            while True:
                kind, data = self.queue.get_nowait()
                self._handle(kind, data)
        except queue.Empty:
            pass
        self.root.after(80, self._drain)

    def _handle(self, kind, data):
        if kind == "status":
            self.status.set(data)
        elif kind == "log":
            self._write_log(data)
        elif kind == "error":
            self.status.set(data)
            self._write_log(T("err_prefix") + str(data))
        elif kind == "auth_ok":
            self.status.set(T("status_connected"))
            self.load_library()
        elif kind == "progress":
            self.progress.configure(value=data)
        elif kind == "library_ids":
            self.games = list(data)
            self._refresh_games()
        elif kind == "game_title":
            pid, title = data
            self.titles[pid] = title
            self._update_game_row(pid)
        elif kind == "counts_updated":
            if self._filter_mode() != FILTER_ALL:
                self._refresh_games()
        elif kind == "scan_done":
            total = data
            self._refresh_games()
            with_ach = sum(1 for pid in self.games if self.counts.get(pid))
            self.status.set(
                T(
                    "status_scan_done",
                    total=total or len(self.games),
                    with_ach=with_ach,
                    without=len(self.games) - with_ach,
                )
            )
            self._write_log(T("log_scan_done", n=total))
        elif kind == "achievements":
            pid, items = data
            if pid == self.current_pid:
                self._show_achievements(items)
        elif kind == "action_done":
            unlock, done, total, preview = data
            key = "log_preview" if preview else "log_applied"
            self._write_log(
                T(key, done=done, total=total,
                  verb=T("verb_unlock") if unlock else T("verb_lock"))
            )
            self.status.set(
                T("status_result", done=done, total=total,
                  verb=T("verb_unlock") if unlock else T("verb_lock"))
            )
            if not preview:
                self.reload_achievements()

    def _write_log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def cache_save(self):
        backend.save_cache(self.cache)

    # -------------------------------------------------------------------- libreria
    def _filter_mode(self):
        index = self.ach_combo.current()
        return FILTER_CODES[index] if 0 <= index < len(FILTER_CODES) else FILTER_ALL

    def _label(self, pid):
        title = self.titles.get(pid)
        if title is None:
            return "{}  ·  ...".format(pid)
        count = self.counts.get(pid)
        if count is None:
            badge = ""
        else:
            badge = T("badge_count", n=count) if count else T("badge_none")
        return "{}  ·  {}{}".format(pid, title or T("no_title"), badge)

    def _matches_filter(self, pid):
        needle = self.filter_var.get().strip().lower()
        if needle and needle not in self._label(pid).lower():
            return False
        mode = self._filter_mode()
        if mode == FILTER_ALL:
            return True
        count = self.counts.get(pid)
        if count is None:
            return False  # non ancora analizzato
        return count > 0 if mode == FILTER_WITH else count == 0

    def _refresh_games(self):
        self.game_tree.delete(*self.game_tree.get_children())
        shown = 0
        unknown = 0
        for pid in self.games:
            if self.counts.get(pid) is None:
                unknown += 1
            if self._matches_filter(pid):
                self.game_tree.insert("", "end", iid=str(pid), values=(self._label(pid),))
                shown += 1
        info = T("lib_info", total=len(self.games), shown=shown)
        if self._filter_mode() != FILTER_ALL and unknown:
            info += T("lib_info_unknown", unknown=unknown)
        self.library_info.set(info)

    def _update_game_row(self, pid):
        iid = str(pid)
        if self.game_tree.exists(iid):
            self.game_tree.item(iid, values=(self._label(pid),))
        elif self._matches_filter(pid):
            self.game_tree.insert("", "end", iid=iid, values=(self._label(pid),))
        if self.counts.get(pid) is not None and self._filter_mode() != FILTER_ALL:
            self._refresh_games()

    def load_library(self):
        if not self.auth:
            self.status.set(T("status_need_auth"))
            return
        self.progress.configure(value=0)
        self._spawn(self._library_worker)

    def _login_worker(self):
        self.refresh_token = backend.read_refresh_token()
        auth = backend.authenticate(self.refresh_token)
        if not auth:
            raise SystemExit(T("err_refresh"))
        self.auth = auth
        self.post("auth_ok", None)

    def _library_worker(self):
        self.post("status", T("status_reading"))
        status, payload = backend.http("GET", backend.OWNED_GAMES_URL, self.auth["access_token"])
        if status != 200:
            raise SystemExit(T("err_library", code=status))
        owned = payload.get("owned") or []
        self.post("library_ids", owned)
        total = len(owned) or 1
        for index, pid in enumerate(owned, 1):
            entry = self.cache.setdefault(str(pid), {})
            if not entry.get("title"):
                state, product = backend.http("GET", backend.GOGDB_PRODUCT.format(pid=pid))
                entry["title"] = (product.get("title") or "") if state == 200 else ""
            if entry.get("title"):
                self.post("game_title", (pid, entry["title"]))
            if index % 25 == 0 or index == len(owned):
                self.post("progress", int(index * 100 / total))
                self.cache_save()
        self.cache_save()
        self.post("status", T("status_lib_loaded", n=len(owned)))

    # --------------------------------------------------- conteggio achievement
    def count_for(self, pid):
        """Numero di achievement del gioco (0 se non ne supporta). Usa e aggiorna la cache."""
        key = str(pid)
        entry = self.cache.setdefault(key, {})
        if "achievements_count" in entry:
            count = int(entry["achievements_count"])
            self.counts[pid] = count
            return count
        try:
            client_id, _secret = backend.game_credentials(pid, self.cache)
        except SystemExit:
            entry["achievements_count"] = 0
            self.counts[pid] = 0
            return 0
        status, payload = backend.http(
            "GET",
            backend.GAMEPLAY_URL.format(client_id=client_id, user_id=self.auth["user_id"]),
            self.auth["access_token"],
        )
        count = len(payload.get("items") or []) if status == 200 else 0
        entry["achievements_count"] = count
        self.counts[pid] = count
        return count

    def scan_achievements(self):
        if not self.auth:
            self.status.set(T("status_need_auth"))
            return
        if not self.games:
            self.status.set(T("status_need_library"))
            return
        self.progress.configure(value=0)
        self._spawn(self._scan_worker)

    def _scan_worker(self):
        pending = [pid for pid in self.games if self.counts.get(pid) is None]
        if not pending:
            self.post("status", T("status_scan_none"))
            return
        self.post("log", T("log_scan_start", n=len(pending)))
        total = len(pending)
        for index, pid in enumerate(pending, 1):
            self.count_for(pid)
            if index % 10 == 0 or index == total:
                self.post("progress", int(index * 100 / total))
                self.post("counts_updated", None)
                self.cache_save()
        self.post("scan_done", total)

    # ---------------------------------------------------------------- achievement
    def _on_game_select(self, _event=None):
        selection = self.game_tree.selection()
        if selection:
            pid = int(selection[0])
            if pid != self.current_pid:
                self.current_pid = pid
                self.reload_achievements()

    def _on_ach_select(self, _event=None):
        selection = self.ach_tree.selection()
        if not selection or not selection[0].isdigit():
            return
        index = int(selection[0])
        if not 1 <= index <= len(self.items):
            return
        item = self.items[index - 1]
        self.detail_title.configure(text=(item.get("name") or ""))
        meta = ["{} {}".format(T("col_id"), item.get("achievement_id"))]
        meta.append(T("state_on") if item.get("date_unlocked") else T("state_off"))
        if not item.get("visible", True):
            meta.append(T("hidden"))
        rarity = item.get("rarity_level_description") or item.get("rarity")
        if rarity:
            meta.append(str(rarity))
        if item.get("date_unlocked"):
            meta.append(str(item["date_unlocked"]))
        self.detail_meta.configure(text="  ·  ".join(meta))
        self.detail_desc.configure(
            text=item.get("description") or T("detail_no_desc")
        )

    def reload_achievements(self):
        if self.current_pid is None or not self.auth:
            return
        self.game_label.set(T("loading_achievements", pid=self.current_pid))
        self._spawn(lambda: self._achievements_worker(self.current_pid))

    def _achievements_worker(self, pid):
        client_id, _secret = backend.game_credentials(pid, self.cache)
        items = backend.get_achievements(client_id, self.auth["user_id"], self.auth["access_token"])
        self.post("achievements", (pid, items))

    def _show_achievements(self, items):
        self.items = items
        self.ach_tree.delete(*self.ach_tree.get_children())
        unlocked = sum(1 for item in items if item.get("date_unlocked"))
        for index, item in enumerate(items, 1):
            done = bool(item.get("date_unlocked"))
            self.ach_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    index,
                    T("state_on") if done else T("state_off"),
                    item.get("name") or "",
                    (item.get("description") or "").replace("\n", " "),
                    item.get("achievement_id"),
                ),
                tags=("unlocked",) if done else (),
            )
        self.game_label.set(
            T(
                "game_summary",
                pid=self.current_pid,
                total=len(items),
                unlocked=unlocked,
                locked=len(items) - unlocked,
            )
        )
        self.status.set(T("status_select_rows"))
        self.detail_title.configure(text=T("detail_empty_title"))
        self.detail_meta.configure(text="")
        self.detail_desc.configure(text=T("detail_empty_desc"))

    def _selected_targets(self):
        targets = []
        for iid in self.ach_tree.selection():
            if iid.isdigit() and 1 <= int(iid) <= len(self.items):
                targets.append(self.items[int(iid) - 1]["achievement_id"])
        return targets

    def unlock_selected(self):
        self._confirm_and_apply(unlock=True, targets=self._selected_targets())

    def lock_selected(self):
        self._confirm_and_apply(unlock=False, targets=self._selected_targets())

    def unlock_all(self):
        targets = [i["achievement_id"] for i in self.items if not i.get("date_unlocked")]
        self._confirm_and_apply(unlock=True, targets=targets)

    def _confirm_and_apply(self, unlock, targets):
        if not self.auth or self.current_pid is None:
            self.status.set(T("status_select_game"))
            return
        if not targets:
            self.status.set(T("status_no_targets"))
            return
        preview = self.preview_var.get()
        note = T("confirm_preview") if preview else T("confirm_real")
        verb = T("confirm_verb_unlock") if unlock else T("confirm_verb_lock")
        if not messagebox.askyesno(
            T("confirm_title"),
            T("confirm_body", verb=verb, n=len(targets), pid=self.current_pid, note=note),
        ):
            return
        self._spawn(lambda: self._apply_worker(unlock, targets, preview))

    def _apply_worker(self, unlock, targets, preview):
        client_id, client_secret = backend.game_credentials(self.current_pid, self.cache)
        tokens = []
        game_auth = backend.authenticate(self.refresh_token, client_id, client_secret)
        if game_auth and game_auth.get("access_token"):
            tokens.append(game_auth["access_token"])
        if self.auth["access_token"] not in tokens:
            tokens.append(self.auth["access_token"])

        done = 0
        total = len(targets)
        for index, achievement_id in enumerate(targets, 1):
            ok = backend.set_achievement(
                client_id, self.auth["user_id"], achievement_id, tokens, unlock, preview
            )
            done += 1 if ok else 0
            self.post(
                "log",
                T(
                    "log_item",
                    mode=T("mode_preview") if preview else T("mode_done"),
                    op=T("op_unlock") if unlock else T("op_lock"),
                    ach=achievement_id,
                    result=T("result_ok") if ok else T("result_fail"),
                ),
            )
            self.post("progress", int(index * 100 / total))
        self.post("action_done", (unlock, done, total, preview))


def main():
    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", 1.25)
    except tk.TclError:
        pass
    App(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
