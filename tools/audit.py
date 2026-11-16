#!/usr/bin/env python3
"""
Prüft die gebaute Website auf Suchmaschinen- und KI-Auffindbarkeit (SEO/GEO)
und listet offene Aufgaben auf.

    python3 tools/audit.py               # prüft _site/ (vorher: python3 build.py)
    python3 tools/audit.py --bericht     # speichert zusätzlich berichte/audit-JJJJ-MM-TT.md
    python3 tools/audit.py --streng      # Exit-Code 1 bei Fehlern (für GitHub Actions)

Stufen: FEHLER (muss behoben werden), WARNUNG (sollte behoben werden), HINWEIS (Empfehlung).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("Bitte zuerst ausführen: pip install -r requirements.txt")

AI_BOTS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User",
           "Google-Extended", "PerplexityBot", "Applebot-Extended"]
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = None
        self.title = ""
        self.meta = {}
        self.links = []          # (rel, href, hreflang)
        self.anchors = []        # href
        self.ids = set()
        self.imgs = []           # (src, alt or None)
        self.headings = []       # (level, text)
        self.jsonld = []
        self._in = None
        self._buf = []
        self._text = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title":
            self._in, self._buf = "title", []
        elif tag == "meta":
            key = a.get("name") or a.get("property")
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link":
            self.links.append((a.get("rel", ""), a.get("href", ""), a.get("hreflang")))
        elif tag == "a" and a.get("href"):
            self.anchors.append(a["href"])
        elif tag == "img":
            self.imgs.append((a.get("src", ""), a.get("alt")))
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._in, self._buf = tag, []
        elif tag == "script" and a.get("type") == "application/ld+json":
            self._in, self._buf = "jsonld", []
        elif tag in ("script", "style", "svg"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "svg") and self._in != "jsonld" and self._skip:
            self._skip -= 1
        if self._in == tag or (self._in == "jsonld" and tag == "script"):
            text = "".join(self._buf).strip()
            if self._in == "title":
                self.title = text
            elif self._in == "jsonld":
                self.jsonld.append(text)
            else:
                self.headings.append((int(tag[1]), re.sub(r"\s+", " ", text)))
            self._in = None

    def handle_data(self, data):
        if self._in:
            self._buf.append(data)
        if not self._skip and self._in != "jsonld":
            self._text.append(data)

    @property
    def words(self):
        return len(re.findall(r"\w+", " ".join(self._text)))


class Audit:
    def __init__(self, site_dir: Path, base_url: str | None = None):
        self.site_dir = site_dir
        self.items = []  # (level, area, message)
        self.config = yaml.safe_load((ROOT / "site.yaml").read_text(encoding="utf-8"))
        self.base = (base_url or self.config["url"]).rstrip("/")
        self.base_path = urlparse(self.base).path.rstrip("/")  # z. B. "/damianleschik.com" auf github.io
        self.pages = {}

    def add(self, level, area, msg):
        self.items.append((level, area, msg))

    # ----------------------------------------------------------- Seiten
    def url_of(self, path: Path) -> str:
        rel = path.relative_to(self.site_dir).as_posix()
        if rel.endswith("index.html"):
            rel = rel[: -len("index.html")]
        return "/" + rel

    def resolve(self, href: str, page_url: str):
        if href.startswith(("mailto:", "tel:", "#", "javascript:")):
            return None
        parsed = urlparse(href)
        if parsed.scheme in ("http", "https") or href.startswith("/"):
            if parsed.scheme and not href.startswith(self.base):
                return None  # externer Link
            path = parsed.path
            if self.base_path:
                if path == self.base_path or path.startswith(self.base_path + "/"):
                    path = path[len(self.base_path):] or "/"
                else:
                    return self.site_dir / "__ohne-basispfad__"  # Link ohne Unterpfad führt ins Leere
        else:
            base_dir = page_url if page_url.endswith("/") else page_url.rsplit("/", 1)[0] + "/"
            path = parsed.path if parsed.path.startswith("/") else base_dir + parsed.path
        parts = []
        for seg in path.split("/"):
            if seg == "..":
                if parts:
                    parts.pop()
            elif seg not in ("", "."):
                parts.append(seg)
        clean = "/" + "/".join(parts) + ("/" if path.endswith("/") else "")
        target = self.site_dir / clean.lstrip("/")
        if clean.endswith("/"):
            target = target / "index.html"
        return target

    def check_pages(self):
        for path in sorted(self.site_dir.rglob("*.html")):
            url = self.url_of(path)
            parser = PageParser()
            parser.feed(path.read_text(encoding="utf-8"))
            self.pages[url] = parser
            if path.name == "404.html":
                continue
            area = url
            if not parser.lang:
                self.add("FEHLER", area, "Sprachangabe <html lang> fehlt")
            n = len(parser.title)
            if not parser.title:
                self.add("FEHLER", area, "Seitentitel fehlt")
            elif not 25 <= n <= 65:
                self.add("WARNUNG", area, "Seitentitel hat {} Zeichen (ideal 25–65): {}".format(n, parser.title))
            desc = parser.meta.get("description", "")
            if not desc:
                self.add("FEHLER", area, "Meta-Beschreibung fehlt")
            elif not 70 <= len(desc) <= 165:
                self.add("WARNUNG", area, "Meta-Beschreibung hat {} Zeichen (ideal 70–165)".format(len(desc)))
            if "noindex" in parser.meta.get("robots", ""):
                self.add("FEHLER", area, "Seite ist auf noindex gesetzt (Vorschau-Build statt _site geprüft?)")
            canon = [h for r, h, _ in parser.links if r == "canonical"]
            if not canon or not canon[0].startswith("https://"):
                self.add("FEHLER", area, "Canonical-Link fehlt oder ist nicht absolut (https)")
            for key in ("og:title", "og:description", "og:image"):
                if not parser.meta.get(key):
                    self.add("WARNUNG", area, "Open-Graph-Angabe fehlt: " + key)
            h1 = [h for h in parser.headings if h[0] == 1]
            if len(h1) != 1:
                self.add("FEHLER", area, "Genau eine H1 erwartet, gefunden: {}".format(len(h1)))
            last = 0
            for level, text in parser.headings:
                if last and level > last + 1:
                    self.add("WARNUNG", area, "Überschriften-Sprung von H{} auf H{} bei „{}“".format(last, level, text[:50]))
                last = level
            for src, alt in parser.imgs:
                if alt is None:
                    self.add("FEHLER", area, "Bild ohne alt-Attribut: " + src)
            if not parser.jsonld:
                self.add("FEHLER", area, "Keine strukturierten Daten (JSON-LD)")
            for block in parser.jsonld:
                try:
                    data = json.loads(block)
                    if "@context" not in data:
                        self.add("FEHLER", area, "JSON-LD ohne @context")
                except json.JSONDecodeError as exc:
                    self.add("FEHLER", area, "JSON-LD fehlerhaft: {}".format(exc))
            for href in parser.anchors + [h for r, h, _ in parser.links if r in ("stylesheet", "icon")]:
                target = self.resolve(href.split("?")[0], url)
                if target is not None and not target.exists():
                    self.add("FEHLER", area, "Interner Link führt ins Leere: " + href)
                frag = href.split("#", 1)[1] if "#" in href and href.startswith("#") else None
                if frag and frag not in parser.ids:
                    self.add("WARNUNG", area, "Sprungmarke fehlt: #" + frag)
            if parser.words < 120 and "/impressum" not in url and "/legal-notice" not in url:
                self.add("HINWEIS", area, "Wenig Text ({} Wörter); KI-Systeme und Suchmaschinen brauchen Substanz".format(parser.words))
            size = path.stat().st_size
            if size > 150_000:
                self.add("WARNUNG", area, "HTML-Datei ist groß ({} KB)".format(size // 1024))

    def check_hreflang(self):
        for url, parser in self.pages.items():
            alts = {lang: href for rel, href, lang in parser.links if rel == "alternate" and lang}
            for lang, href in alts.items():
                if lang == "x-default":
                    continue
                target_url = href.replace(self.base, "") or "/"
                other = self.pages.get(target_url)
                if other is None:
                    self.add("FEHLER", url, "hreflang {} zeigt auf fehlende Seite {}".format(lang, href))
                    continue
                back = {l: h for r, h, l in other.links if r == "alternate" and l}
                if self.base + url not in back.values():
                    self.add("WARNUNG", url, "hreflang nicht wechselseitig mit {}".format(href))

    # ----------------------------------------------------------- Dateien für Maschinen
    def check_machine_files(self):
        robots = self.site_dir / "robots.txt"
        if not robots.exists():
            self.add("FEHLER", "robots.txt", "fehlt")
        else:
            text = robots.read_text(encoding="utf-8")
            if "Sitemap:" not in text:
                self.add("FEHLER", "robots.txt", "Sitemap-Zeile fehlt")
            if re.search(r"^Disallow:\s*/\s*$", text, re.M):
                self.add("FEHLER", "robots.txt", "„Disallow: /“ blockiert Crawler")
            missing = [b for b in AI_BOTS if b not in text]
            if missing:
                self.add("HINWEIS", "robots.txt", "KI-Crawler nicht ausdrücklich genannt: " + ", ".join(missing))
        sitemap = self.site_dir / "sitemap.xml"
        if not sitemap.exists():
            self.add("FEHLER", "sitemap.xml", "fehlt")
        else:
            try:
                tree = ET.parse(sitemap)
                ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                locs = {e.text for e in tree.getroot().findall("s:url/s:loc", ns)}
                for url, parser in self.pages.items():
                    if url.endswith("404.html") or "noindex" in parser.meta.get("robots", ""):
                        continue
                    if self.base + url not in locs:
                        self.add("WARNUNG", "sitemap.xml", "Seite fehlt in der Sitemap: " + url)
            except ET.ParseError as exc:
                self.add("FEHLER", "sitemap.xml", "nicht lesbar: {}".format(exc))
        llms = self.site_dir / "llms.txt"
        if not llms.exists():
            self.add("WARNUNG", "llms.txt", "fehlt")
        else:
            text = llms.read_text(encoding="utf-8")
            for url, parser in self.pages.items():
                if "/notizen/" in url and url.count("/") > 2 and "noindex" not in parser.meta.get("robots", ""):
                    if self.base + url not in text:
                        self.add("WARNUNG", "llms.txt", "Forschungsnotiz fehlt: " + url)
        for name in ("llms-full.txt", "feed.xml", "publikationen.bib", "publikationen.json"):
            if not (self.site_dir / name).exists():
                self.add("WARNUNG", name, "fehlt")

    # ----------------------------------------------------------- Inhalte und offene Aufgaben
    def check_content(self):
        imp = self.config.get("impressum", {})
        if any("[" in str(v) for v in imp.values()):
            self.add("FEHLER", "site.yaml", "Impressum enthält Platzhalter. Vor der Veröffentlichung Pflicht (§ 5 DDG)")
        # Google Analytics: nur mit gültiger Mess-ID und nie ohne Einwilligung
        ga4 = str((self.config.get("analytics") or {}).get("ga4_id") or "")
        if ga4 and not re.fullmatch(r"G-[A-Z0-9]{4,}", ga4):
            self.add("FEHLER", "site.yaml", "GA4-Mess-ID hat ein ungültiges Format (erwartet z. B. G-ABC123XYZ)")
        for page in sorted(self.site_dir.rglob("*.html")):
            html = page.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"<script[^>]+src=[\"'][^\"']*(googletagmanager\.com|google-analytics\.com)", html, re.I):
                self.add("FEHLER", str(page.relative_to(self.site_dir)),
                         "Google-Skript wird direkt eingebunden, also ohne Einwilligung. Nur über das Banner laden")
            if ga4 and "data-consent-open" not in html:
                self.add("FEHLER", str(page.relative_to(self.site_dir)), "Link „Cookie-Einstellungen“ fehlt")
        profiles = self.config.get("profiles", {})
        for key in ("orcid", "google_scholar", "linkedin"):
            if not profiles.get(key, {}).get("url"):
                self.add("HINWEIS", "site.yaml", "Profil-Link fehlt: {} (stärkt die eindeutige Zuordnung durch KI-Systeme)".format(key))
        if not (ROOT / "static/assets/img/portrait.jpg").exists():
            self.add("HINWEIS", "static", "Kein Porträtfoto (static/assets/img/portrait.jpg)")
        pubs = yaml.safe_load((ROOT / "content/publikationen.yaml").read_text(encoding="utf-8")) or []
        ids = set()
        for p in pubs:
            if p["id"] in ids:
                self.add("FEHLER", "publikationen.yaml", "Doppelte id: " + p["id"])
            ids.add(p["id"])
            if p.get("doi") and not DOI_RE.match(str(p["doi"])):
                self.add("FEHLER", "publikationen.yaml", "DOI-Format ungültig bei {}: {}".format(p["id"], p["doi"]))
            if not p.get("verified"):
                self.add("WARNUNG", "publikationen.yaml", "Nicht bestätigt: {} – {}".format(p["id"], p.get("check", "bitte prüfen")))
            if p.get("check") and p.get("verified"):
                self.add("HINWEIS", "publikationen.yaml", "Offener Prüfhinweis bei {}: {}".format(p["id"], p["check"]))
        comics = yaml.safe_load((ROOT / "content/comics.yaml").read_text(encoding="utf-8")) or []
        for c in comics:
            if not (ROOT / "static/downloads" / c["file"]).exists():
                self.add("WARNUNG", "comics.yaml", "PDF fehlt: static/downloads/{}".format(c["file"]))
            elif "folgt" in str(c.get("title", "")):
                self.add("WARNUNG", "comics.yaml", "Titel/Beschreibung für {} noch Platzhalter".format(c["id"]))
            if c.get("based_on") and c["based_on"] not in ids:
                self.add("FEHLER", "comics.yaml", "based_on verweist auf unbekannte Publikation: " + c["based_on"])
        newest, drafts = None, []
        from build import read_md, to_date  # noqa: E402
        for path in sorted((ROOT / "content/entwuerfe").glob("*.md")) if (ROOT / "content/entwuerfe").exists() else []:
            if not path.name.startswith("_"):
                drafts.append(path.name)
        for path in (ROOT / "content/notizen").glob("*.md"):
            if path.name.startswith("_"):
                continue
            meta, body = read_md(path)
            if meta.get("draft"):
                drafts.append(path.name)
                self.add("WARNUNG", "notizen/" + path.name, "Entwurf liegt in content/notizen/ und wäre im öffentlichen Repository sichtbar. Nach content/entwuerfe/ verschieben")
                continue
            date = to_date(meta.get("date"))
            newest = max(newest, date) if newest and date else (date or newest)
            if not meta.get("studies"):
                self.add("WARNUNG", "notizen/" + path.name, "Keine besprochenen Studien angegeben (Quellen mit DOI/Link)")
            if len(str(meta.get("summary", ""))) < 60:
                self.add("WARNUNG", "notizen/" + path.name, "Zusammenfassung (summary) fehlt oder ist sehr kurz")
            for st in meta.get("studies") or []:
                if st.get("doi") and not DOI_RE.match(str(st["doi"])):
                    self.add("FEHLER", "notizen/" + path.name, "DOI-Format ungültig: " + str(st["doi"]))
        for name in drafts:
            self.add("HINWEIS", "entwuerfe/" + name, "Entwurf wartet auf Freigabe")
        if newest is None:
            self.add("HINWEIS", "notizen", "Noch keine veröffentlichte Forschungsnotiz. Regelmäßige Notizen stärken Aktualität und Sichtbarkeit")
        else:
            age = (dt.date.today() - newest).days
            if age > 35:
                self.add("HINWEIS", "notizen", "Letzte Forschungsnotiz ist {} Tage alt. Eine neue Notiz wäre gut".format(age))

    # ----------------------------------------------------------- Bericht
    def report(self) -> str:
        order = {"FEHLER": 0, "WARNUNG": 1, "HINWEIS": 2}
        items = sorted(self.items, key=lambda i: (order[i[0]], i[1]))
        counts = {lvl: sum(1 for i in items if i[0] == lvl) for lvl in order}
        score = max(0, 100 - 10 * counts["FEHLER"] - 3 * counts["WARNUNG"] - 1 * counts["HINWEIS"])
        lines = ["# Website-Prüfung {}".format(dt.date.today().isoformat()), "",
                 "Geprüft: `{}` ({} Seiten)  ".format(self.site_dir.relative_to(ROOT) if self.site_dir.is_relative_to(ROOT) else self.site_dir, len(self.pages)),
                 "Ergebnis: **{} Fehler, {} Warnungen, {} Hinweise** (Punktzahl {}/100)".format(
                     counts["FEHLER"], counts["WARNUNG"], counts["HINWEIS"], score), ""]
        for lvl in order:
            group = [i for i in items if i[0] == lvl]
            if not group:
                continue
            lines += ["## {} ({})".format({"FEHLER": "Fehler", "WARNUNG": "Warnungen", "HINWEIS": "Hinweise"}[lvl], len(group)), ""]
            lines += ["- **{}**: {}".format(area, msg) for _, area, msg in group]
            lines.append("")
        if not items:
            lines.append("Keine Auffälligkeiten.")
        return "\n".join(lines)

    def run(self):
        if not self.site_dir.exists():
            sys.exit("Ordner {} fehlt. Bitte zuerst bauen: python3 build.py".format(self.site_dir))
        self.check_pages()
        self.check_hreflang()
        self.check_machine_files()
        self.check_content()
        return self.report()


def main():
    parser = argparse.ArgumentParser(description="SEO/GEO-Prüfung der Website")
    parser.add_argument("--site", default=str(ROOT / "_site"), help="Ordner der gebauten Website (Standard: _site)")
    parser.add_argument("--bericht", action="store_true", help="Bericht unter berichte/ speichern")
    parser.add_argument("--streng", action="store_true", help="Exit-Code 1 bei Fehlern")
    parser.add_argument("--base-url", help="Adresse, mit der gebaut wurde (Standard: url aus site.yaml)")
    args = parser.parse_args()
    audit = Audit(Path(args.site).resolve(), args.base_url)
    text = audit.run()
    print(text)
    if args.bericht:
        out = ROOT / "berichte" / "audit-{}.md".format(dt.date.today().isoformat())
        out.parent.mkdir(exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print("\nBericht gespeichert: {}".format(out.relative_to(ROOT)))
    if args.streng and any(i[0] == "FEHLER" for i in audit.items):
        sys.exit(1)


if __name__ == "__main__":
    main()
