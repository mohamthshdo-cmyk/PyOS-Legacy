"""PyChrome - embedded web browser for PyOS (tkinterweb engine)."""
import tkinter as tk
from tkinter import simpledialog
from pyos.apps.base import BaseApp

try:
    from tkinterweb import HtmlFrame
    ENGINE_OK = True
except ImportError:
    ENGINE_OK = False


# ---- Sites that render well in tkinterweb (no JavaScript required) ----
WORKING_SITES = [
    ("Wikipedia",         "https://en.wikipedia.org/wiki/Main_Page"),
    ("DuckDuckGo (HTML)", "https://html.duckduckgo.com/html/"),
    ("Python Docs",       "https://docs.python.org/3/"),
    ("PyPI",              "https://pypi.org/"),
    ("GitHub",            "https://github.com/"),
    ("Stack Overflow",    "https://stackoverflow.com/"),
    ("Hacker News",       "https://news.ycombinator.com/"),
    ("Lobsters",          "https://lobste.rs/"),
    ("W3Schools",         "https://www.w3schools.com/"),
    ("MDN Web Docs",      "https://developer.mozilla.org/en-US/"),
    ("Arch Wiki",         "https://wiki.archlinux.org/"),
    ("Linux Kernel Docs", "https://www.kernel.org/doc/html/latest/"),
    ("Reddit (old)",      "https://old.reddit.com/"),
    ("Wikipedia Random",  "https://en.wikipedia.org/wiki/Special:Random"),
    ("Wikibooks",         "https://en.wikibooks.org/"),
    ("Project Gutenberg", "https://www.gutenberg.org/"),
    ("OpenStreetMap",     "https://www.openstreetmap.org/"),
    ("Weather (wttr)",    "https://wttr.in/"),
    ("XKCD",              "https://xkcd.com/"),
    ("BBC News",          "https://www.bbc.com/news"),
    ("NPR",               "https://text.npr.org/"),
    ("CNN Lite",          "https://lite.cnn.com/"),
    ("AP News",           "https://apnews.com/"),
    ("Ars Technica",      "https://arstechnica.com/"),
    ("The Verge",         "https://www.theverge.com/"),
    ("Codeberg",          "https://codeberg.org/"),
    ("GitLab",            "https://gitlab.com/"),
    ("SourceForge",       "https://sourceforge.net/"),
    ("Freshmeat",         "https://freshcode.club/"),
    ("Gnu.org",           "https://www.gnu.org/"),
    ("FSF",               "https://www.fsf.org/"),
    ("Debian",            "https://www.debian.org/"),
    ("Ubuntu",            "https://ubuntu.com/"),
    ("Fedora",            "https://fedoraproject.org/"),
    ("Kali Linux",        "https://www.kali.org/"),
    ("FreeBSD",           "https://www.freebsd.org/"),
    ("OpenBSD",           "https://www.openbsd.org/"),
    ("Raspberry Pi",      "https://www.raspberrypi.com/"),
    ("Arduino",           "https://www.arduino.cc/"),
    ("Wolfram Alpha",     "https://www.wolframalpha.com/"),
    ("Internet Archive",  "https://archive.org/"),
    ("Open Library",      "https://openlibrary.org/"),
    ("Wiktionary",        "https://en.wiktionary.org/"),
    ("Wikinews",          "https://en.wikinews.org/"),
    ("Wikiquote",         "https://en.wikiquote.org/"),
    ("Wikisource",        "https://en.wikisource.org/"),
    ("Wikiversity",       "https://en.wikiversity.org/"),
    ("Wikivoyage",        "https://en.wikivoyage.org/"),
    ("Wikispecies",       "https://species.wikimedia.org/"),
    ("Commons",           "https://commons.wikimedia.org/"),
]

HOME_URL = "about:home"


class PyChromeApp(BaseApp):
    NAME = "PyChrome"
    ICON = "C"
    WIDTH = 1100
    HEIGHT = 700

    def build(self, parent):
        self.parent = parent
        self.history = []
        self.hist_idx = -1

        if not ENGINE_OK:
            self._show_missing_engine(parent)
            return

        self._build_toolbar(parent)
        self._build_bookmarks(parent)
        self._build_page(parent)
        self._build_status(parent)

        # Load the start page
        self._go(HOME_URL, push=False)

    # ---------------- missing engine ----------------
    def _show_missing_engine(self, parent):
        f = tk.Frame(parent, bg="#1a1b26")
        f.pack(expand=True, fill="both")
        tk.Label(f, text="C", font=("Segoe UI", 56, "bold"),
                 bg="#1a1b26", fg="#7aa2f7").pack(pady=(80, 8))
        tk.Label(f, text="PyChrome needs tkinterweb",
                 font=("Segoe UI", 16, "bold"),
                 bg="#1a1b26", fg="#c0caf5").pack()
        tk.Label(f, text="Open the PyOS Terminal and run:\n\n"
                         "    pip install tkinterweb\n\n"
                         "Then restart PyOS.",
                 font=("Consolas", 11), justify="center",
                 bg="#1a1b26", fg="#9ece6a").pack(pady=16)

    # ---------------- toolbar ----------------
    def _build_toolbar(self, parent):
        bar = tk.Frame(parent, bg="#1f2335")
        bar.pack(fill="x")

        def btn(glyph, cmd):
            b = tk.Button(bar, text=glyph, bg="#2a2e3f", fg="#c0caf5",
                          bd=0, activebackground="#7aa2f7",
                          activeforeground="#16161e",
                          font=("Segoe UI Symbol", 12), command=cmd)
            b.pack(side="left", padx=2, pady=4, ipadx=6)

        btn("\u2190", self._back)       # back
        btn("\u2192", self._forward)    # forward
        btn("\u21bb", self._reload)     # reload
        btn("\u2302", self._home)       # home

        self.url_var = tk.StringVar(value=HOME_URL)
        entry = tk.Entry(bar, textvariable=self.url_var,
                         bg="#1a1b26", fg="#c0caf5", bd=0,
                         insertbackground="#7aa2f7",
                         font=("Consolas", 10))
        entry.pack(side="left", fill="x", expand=True,
                   padx=6, pady=4, ipady=4)
        entry.bind("<Return>", lambda e: self._go(self.url_var.get()))

        tk.Button(bar, text="Go", bg="#7aa2f7", fg="#16161e",
                  bd=0, activebackground="#bb9af7",
                  activeforeground="#16161e",
                  font=("Segoe UI", 10, "bold"),
                  command=lambda: self._go(self.url_var.get())
                  ).pack(side="left", padx=(0, 4), pady=4, ipadx=12)

    # ---------------- bookmark bar ----------------
    def _build_bookmarks(self, parent):
        bar = tk.Frame(parent, bg="#16161e")
        bar.pack(fill="x")

        favorites = [
            ("Wikipedia",  "https://en.wikipedia.org/wiki/Main_Page"),
            ("DDG",        "https://html.duckduckgo.com/html/"),
            ("HN",         "https://news.ycombinator.com/"),
            ("PyDocs",     "https://docs.python.org/3/"),
            ("GitHub",     "https://github.com/"),
            ("XKCD",       "https://xkcd.com/"),
            ("Archive",    "https://archive.org/"),
            ("Start",      HOME_URL),
        ]
        for label, url in favorites:
            tk.Button(bar, text=label, bg="#16161e", fg="#7aa2f7",
                      bd=0, activebackground="#2a2e3f",
                      activeforeground="#bb9af7",
                      font=("Segoe UI", 9),
                      command=lambda u=url: self._go(u)
                      ).pack(side="left", padx=4, pady=3)

    # ---------------- page area ----------------
    def _build_page(self, parent):
        self.page_holder = tk.Frame(parent, bg="#0c0c0c")
        self.page_holder.pack(fill="both", expand=True)

        self.html = HtmlFrame(self.page_holder, messages_enabled=False)
        self.html.pack(fill="both", expand=True)

        try:
            self.html.add_link_handler(self._on_link)
        except Exception:
            pass

    def _build_status(self, parent):
        self.status = tk.Label(parent, text="", bg="#1f2335", fg="#565f89",
                               anchor="w", font=("Segoe UI", 8))
        self.status.pack(fill="x", side="bottom")

    # ---------------- navigation ----------------
    def _go(self, url, push=True):
        url = self._normalize(url)

        if url == HOME_URL:
            self._show_start_page()
        else:
            try:
                self.html.load_url(url)
            except Exception as e:
                self.status.config(text="Error: " + str(e), fg="#f7768e")
                return

        self.url_var.set(url)
        self.status.config(text="Loaded: " + url, fg="#565f89")

        if push:
            self.history = self.history[:self.hist_idx + 1]
            self.history.append(url)
            self.hist_idx = len(self.history) - 1

    def _normalize(self, url):
        url = (url or "").strip()
        if not url:
            return HOME_URL
        if url == HOME_URL:
            return url
        # search terms (no dot before space) -> DuckDuckGo HTML
        first = url.split(" ")[0]
        if "." not in first and not url.startswith(("http://", "https://")):
            q = url.replace(" ", "+")
            return "https://html.duckduckgo.com/html/?q=" + q
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        return url

    def _on_link(self, arg):
        url = arg if isinstance(arg, str) else (getattr(arg, "url", None) or getattr(arg, "data", None))
        if url:
            self._go(url)

    def _back(self):
        if self.hist_idx > 0:
            self.hist_idx -= 1
            self._go(self.history[self.hist_idx], push=False)

    def _forward(self):
        if self.hist_idx < len(self.history) - 1:
            self.hist_idx += 1
            self._go(self.history[self.hist_idx], push=False)

    def _reload(self):
        if self.hist_idx >= 0:
            self._go(self.history[self.hist_idx], push=False)

    def _home(self):
        self._go(HOME_URL)

    # ---------------- start page ----------------
    def _show_start_page(self):
        """Render a built-in page with clickable working links."""
        rows = []
        for name, url in WORKING_SITES:
            rows.append(
                '<tr>'
                '<td style="padding:6px 10px;">'
                f'<a href="{url}" style="color:#7aa2f7;text-decoration:none;">{name}</a>'
                '</td>'
                f'<td style="padding:6px 10px;color:#565f89;font-size:11px;">{url}</td>'
                '</tr>'
            )
        html = (
            '<html><head><meta charset="utf-8"></head>'
            '<body style="background:#1a1b26;color:#c0caf5;'
            'font-family:Segoe UI,Arial,sans-serif;padding:24px;">'
            '<h1 style="color:#7aa2f7;margin:0 0 4px 0;">PyChrome</h1>'
            '<p style="color:#565f89;margin:0 0 20px 0;">'
            'Start page &mdash; sites that work in tkinterweb (no JavaScript).'
            '</p>'
            '<table style="border-collapse:collapse;">'
            + "".join(rows) +
            '</table>'
            '<p style="color:#565f89;margin-top:24px;font-size:12px;">'
            'Tip: type a search term in the URL bar and press Enter '
            '(uses DuckDuckGo HTML).</p>'
            '</body></html>'
        )
        try:
            self.html.load_html(html)
        except Exception as e:
            self.status.config(text="Could not render start page: " + str(e),
                               fg="#f7768e")
