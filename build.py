#!/usr/bin/env python3
"""
Baut die Website damianleschik.com aus den Inhalten im Ordner content/.

    python3 build.py              ->  _site/      zum Veröffentlichen
    python3 build.py --vorschau   ->  _vorschau/  mit Entwürfen; index.html per Doppelklick öffnen

Weitere Optionen:
    --base-url URL   andere Adresse als in site.yaml (z. B. für Tests)
    --out ORDNER     anderer Ausgabeordner
    --entwuerfe      Entwürfe auch in die Veröffentlichungs-Version aufnehmen

Benötigt Python 3.9+ und die Pakete aus requirements.txt (jinja2, markdown, pyyaml).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import posixpath
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse
from xml.sax.saxutils import escape as xml_escape

try:
    import markdown
    import yaml
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    from markupsafe import Markup, escape
except ImportError as exc:  # pragma: no cover
    sys.exit("Fehlendes Python-Paket ({}). Bitte ausführen: pip install -r requirements.txt".format(exc.name))

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
LANGS = ("de", "en")

# Englisch ist die Hauptsprache (unter /), Deutsch liegt unter /de/.
DEFAULT_LANG = "en"
ROUTES = {
    "home": {"en": "/", "de": "/de/"},
    "publications": {"en": "/publications/", "de": "/de/publikationen/"},
    "notes": {"en": "/notes/", "de": "/de/notizen/"},
    "comics": {"en": "/comics/", "de": "/de/comics/"},
    "imprint": {"en": "/legal-notice/", "de": "/de/impressum/"},
    "privacy": {"en": "/privacy/", "de": "/de/datenschutz/"},
}
# Alte Adressen (bis 16.11.2026: Deutsch unter /, Englisch unter /en/). Die 404-Seite leitet sie um.
OLD_PATHS = {"/en/": "/", "/publikationen/": "/de/publikationen/", "/notizen/": "/de/notizen/",
             "/impressum/": "/de/impressum/", "/datenschutz/": "/de/datenschutz/"}
MONTHS = {
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
           "September", "Oktober", "November", "Dezember"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"],
}
TYPE_LD = {"article": "ScholarlyArticle", "chapter": "Chapter", "proceedings": "ScholarlyArticle",
           "report": "Report", "thesis": "Thesis", "talk": "Event"}
TYPE_BIB = {"article": "article", "chapter": "incollection", "proceedings": "inproceedings",
            "report": "techreport", "thesis": "phdthesis", "talk": "misc"}
TYPE_CSL = {"article": "article-journal", "chapter": "chapter", "proceedings": "paper-conference",
            "report": "report", "thesis": "thesis", "talk": "speech"}
FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.S)


# ----------------------------------------------------------------- Hilfsfunktionen

def read_yaml(path: Path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def read_md(path: Path):
    text = path.read_text(encoding="utf-8")
    match = FM_RE.match(text)
    if match:
        return (yaml.safe_load(match.group(1)) or {}), match.group(2)
    return {}, text


_MD = markdown.Markdown(extensions=["extra", "sane_lists", "toc"], output_format="html")


def md_html(text: str) -> Markup:
    _MD.reset()
    return Markup(_MD.convert(text))


def loc(value, lang):
    """Gibt die Sprachfassung zurück, wenn value ein {de:…, en:…}-Eintrag ist."""
    if isinstance(value, dict) and any(k in value for k in LANGS):
        return value.get(lang) or value.get("de") or value.get("en") or ""
    return value if value is not None else ""


def to_date(value):
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if value:
        text = str(value)
        if re.fullmatch(r"\d{4}-\d{2}", text):
            text += "-01"
        return dt.date.fromisoformat(text)
    return None


def fmt_date(d: dt.date, lang: str) -> str:
    if lang == "de":
        return "{}. {} {}".format(d.day, MONTHS["de"][d.month - 1], d.year)
    return "{} {} {}".format(d.day, MONTHS["en"][d.month - 1], d.year)


def fmt_month(d: dt.date, lang: str) -> str:
    return "{} {}".format(MONTHS[lang][d.month - 1], d.year)


def split_name(name: str):
    if "," in name:
        family, given = [p.strip() for p in name.split(",", 1)]
    else:
        parts = name.split()
        family, given = parts[-1], " ".join(parts[:-1])
    return family, given


def initials(given: str) -> str:
    out = []
    for part in given.replace(".", ". ").split():
        if part.endswith(".") and len(part) <= 3:
            out.append(part)
        elif "-" in part:
            out.append("-".join(p[0] + "." for p in part.split("-") if p))
        else:
            out.append(part[0] + ".")
    return " ".join(out)


def apa_name(name: str) -> str:
    family, given = split_name(name)
    return "{}, {}".format(family, initials(given)) if given else family


def short_name(name: str) -> str:
    family, given = split_name(name)
    return "{} {}".format(initials(given), family).strip()


def full_name(name: str) -> str:
    family, given = split_name(name)
    return "{} {}".format(given, family).strip()


def join_apa(names) -> str:
    items = [apa_name(n) for n in names]
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + ", & " + items[-1]


def human_size(num: int, lang: str) -> str:
    mb = num / (1024 * 1024)
    text = "{:.1f} MB".format(mb) if mb >= 0.1 else "{} KB".format(max(1, round(num / 1024)))
    return text.replace(".", ",") if lang == "de" else text


def json_ld(data) -> Markup:
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return Markup(text.replace("</", "<\\/"))


def bib_escape(text) -> str:
    text = str(text)
    for a, b in (("\\", "\\textbackslash{}"), ("&", "\\&"), ("%", "\\%"), ("$", "\\$"), ("#", "\\#"), ("_", "\\_")):
        text = text.replace(a, b)
    return text.replace("–", "--")


# ----------------------------------------------------------------- Builder

class Builder:
    def __init__(self, args):
        self.site = read_yaml(ROOT / "site.yaml")
        self.base = (args.base_url or self.site["url"]).rstrip("/")
        # Unterpfad der Adresse, z. B. "/damianleschik.com" bei name.github.io/damianleschik.com.
        # Bei einer eigenen Domain leer.
        self.base_path = urlparse(self.base).path.rstrip("/")
        self.preview = bool(args.vorschau)
        self.include_drafts = self.preview or bool(args.entwuerfe)
        default_out = "_vorschau" if self.preview else "_site"
        self.out = Path(args.out).resolve() if args.out else ROOT / default_out
        self.today = dt.date.today()
        self.build_id = dt.datetime.now().strftime("%Y%m%d%H%M")
        self.warnings = []
        self.sitemap = []
        self.strings = read_yaml(TEMPLATES / "strings.yaml")
        self.env = Environment(loader=FileSystemLoader(str(TEMPLATES)),
                               autoescape=select_autoescape(["html", "xml"]),
                               trim_blocks=True, lstrip_blocks=True)
        self.family = self.site["family_name"]
        self.person_id = self.base + "/#person"
        self.website_id = self.base + "/#website"
        self.portrait = "/assets/img/portrait.jpg" if (STATIC / "assets/img/portrait.jpg").exists() else None

    # ------------------------------------------------------------- Laden

    def warn(self, msg: str):
        self.warnings.append(msg)

    def load(self):
        self.profile = {lang: read_md(CONTENT / "profil.{}.md".format(lang)) for lang in LANGS}
        self.facts = read_yaml(CONTENT / "fakten.yaml")
        self.research = read_yaml(CONTENT / "forschung.yaml")
        self.pubs = self.load_publications()
        self.notes = self.load_notes()
        self.comics = self.load_comics()
        self.check_placeholders()

    def load_publications(self):
        pubs = []
        for raw in read_yaml(CONTENT / "publikationen.yaml"):
            p = dict(raw)
            p["year"] = int(p["year"])
            p["authors"] = p.get("authors", [])
            p["date"] = to_date(p.get("date")) if p.get("date") else None
            p["doi_url"] = "https://doi.org/{}".format(p["doi"]) if p.get("doi") else ""
            p["link"] = p["doi_url"] or p.get("url", "")
            if not p.get("verified"):
                self.warn("Publikation noch nicht bestätigt: {} ({})".format(p["id"], p.get("check", "bitte prüfen")))
            pubs.append(p)
        pubs.sort(key=lambda item: -item["year"])
        return pubs

    def load_notes(self):
        """Notizen aus content/notizen/ (veröffentlicht, sofern nicht draft: true) und
        content/entwuerfe/ (immer Entwurf; der Ordner bleibt lokal und kommt nicht ins Repository)."""
        notes = []
        paths = sorted((CONTENT / "notizen").glob("*.md"))
        drafts_dir = CONTENT / "entwuerfe"
        draft_paths = set(sorted(drafts_dir.glob("*.md"))) if drafts_dir.exists() else set()
        for path in paths + sorted(draft_paths):
            if path.name.startswith("_"):
                continue
            meta, body = read_md(path)
            draft = path in draft_paths or bool(meta.get("draft", False))
            if draft and not self.include_drafts:
                self.warn("Entwurf (nicht veröffentlicht): content/{}/{}".format(path.parent.name, path.name))
                continue
            lang = meta.get("lang", "de")
            slug = meta.get("slug") or re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)
            date = to_date(meta.get("date")) or self.today
            updated = to_date(meta.get("updated")) or date
            base = ROUTES["notes"][lang]
            words = len(re.findall(r"\w+", body))
            notes.append({
                "file": path.name, "slug": slug, "lang": lang, "draft": draft,
                "title": meta.get("title", slug), "summary": meta.get("summary", ""),
                "description": meta.get("description") or meta.get("summary", ""),
                "tags": meta.get("tags", []) or [], "studies": meta.get("studies", []) or [],
                "date": date, "updated": updated, "url": "{}{}/".format(base, slug),
                "body_md": body, "html": md_html(body), "words": words,
                "minutes": max(1, round(words / 200)),
            })
        notes.sort(key=lambda n: n["date"], reverse=True)
        return notes

    def load_comics(self):
        comics = []
        for raw in read_yaml(CONTENT / "comics.yaml"):
            c = dict(raw)
            pdf = STATIC / "downloads" / c["file"]
            c["available"] = pdf.exists()
            c["bytes"] = pdf.stat().st_size if c["available"] else 0
            c["url"] = "/downloads/{}".format(c["file"])
            cover = (c.get("cover") or "").strip()
            c["cover"] = cover if cover and (STATIC / cover.lstrip("/")).exists() else ""
            c["based_on_pub"] = next((p for p in self.pubs if p["id"] == c.get("based_on")), None)
            if not c["available"]:
                self.warn("Comic-PDF fehlt noch: static/downloads/{}".format(c["file"]))
            comics.append(c)
        return comics

    def check_placeholders(self):
        imp = self.site.get("impressum", {})
        if any("[" in str(v) for v in imp.values()):
            self.warn("Impressum unvollständig: Platzhalter in site.yaml → impressum ausfüllen (Pflicht vor Veröffentlichung)")
        if not self.portrait:
            self.warn("Kein Porträtfoto: static/assets/img/portrait.jpg ablegen (quadratisch, mind. 800 px)")
        for key in ("orcid", "google_scholar"):
            if not self.site.get("profiles", {}).get(key, {}).get("url"):
                self.warn("Profil-Link fehlt: {} (wichtig für Auffindbarkeit)".format(key))

    # ------------------------------------------------------------- URLs

    def abs_url(self, path: str) -> str:
        return self.base + path

    def make_rel(self, current: str):
        preview = self.preview
        base_path = self.base_path

        def rel(target: str) -> str:
            if not target.startswith("/") or target.startswith("//"):
                return target
            if not preview:
                return base_path + target
            fragment = ""
            if "#" in target:
                target, fragment = target.split("#", 1)
                fragment = "#" + fragment
            if target.endswith("/"):
                target += "index.html"
            start = current if current.endswith("/") else posixpath.dirname(current) + "/"
            return posixpath.relpath(target, start) + fragment
        return rel

    def out_path(self, url: str) -> Path:
        if url.endswith("/"):
            return self.out / url.lstrip("/") / "index.html"
        return self.out / url.lstrip("/")

    # ------------------------------------------------------------- Strukturierte Daten

    def person_ref(self):
        return {"@type": "Person", "@id": self.person_id, "name": self.site["name"]}

    def person_ld(self, lang: str):
        s = self.site
        profile_meta, profile_body = self.profile[lang]
        first_para = re.sub(r"[*_]", "", profile_body.strip().split("\n\n")[0])
        same_as = [v["url"] for v in s.get("profiles", {}).values() if v.get("url")]
        person = {
            "@type": "Person", "@id": self.person_id, "name": s["name"],
            "honorificPrefix": s.get("honorific"), "givenName": s["given_name"], "familyName": s["family_name"],
            "jobTitle": loc(s["job_title"], lang), "description": first_para,
            "url": self.abs_url(ROUTES["home"][lang]),
            "email": "mailto:" + s["email"] if s.get("email") else None,
            "worksFor": {"@type": "CollegeOrUniversity",
                         "name": s["affiliation"]["name"] if lang == "de" else s["affiliation"]["name_en"],
                         "url": s["affiliation"]["url"]},
            "workLocation": {"@type": "Place", "address": {"@type": "PostalAddress",
                             "addressLocality": s["location"]["city"], "addressCountry": s["location"]["country"]}},
            "alumniOf": [{"@type": "CollegeOrUniversity", "name": a["name"], "url": a.get("url")} for a in s.get("alumni", [])],
            "hasCredential": [{"@type": "EducationalOccupationalCredential", "credentialCategory": "degree",
                               "name": loc(c, lang)} for c in s.get("credentials", [])],
            "award": s.get("awards", []),
            "memberOf": [{"@type": "Organization", "name": loc(m, lang)} for m in s.get("member_of", [])],
            "knowsAbout": loc(s.get("topics", {}), lang),
            "knowsLanguage": ["de", "en"],
            "sameAs": same_as,
        }
        if self.portrait:
            person["image"] = self.abs_url(self.portrait)
        return {k: v for k, v in person.items() if v}

    def website_ld(self):
        return {"@type": "WebSite", "@id": self.website_id, "url": self.abs_url("/"),
                "name": self.site["name"], "inLanguage": list(LANGS), "publisher": {"@id": self.person_id}}

    def breadcrumb_ld(self, lang: str, items):
        t = self.strings[lang]
        trail = [(t["breadcrumb_home"], ROUTES["home"][lang])] + items
        return {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": self.abs_url(url)}
            for i, (name, url) in enumerate(trail)]}

    def pub_ld(self, p, lang: str):
        authors = [self.person_ref() if split_name(a)[0] == self.family else {"@type": "Person", "name": full_name(a)}
                   for a in p["authors"]]
        item = {"@type": TYPE_LD[p["type"]], "@id": self.abs_url(ROUTES["publications"][DEFAULT_LANG]) + "#" + p["id"],
                "name": p["title"], "inLanguage": p.get("language")}
        if p["type"] == "talk":
            item.update({"startDate": (p["date"].isoformat()[:7] if p.get("date") else str(p["year"])),
                         "performer": authors[0] if len(authors) == 1 else authors,
                         "location": {"@type": "Place", "name": loc(p.get("place"), lang) or loc(p.get("event"), lang)},
                         "superEvent": {"@type": "Event", "name": loc(p.get("event"), lang)},
                         "url": p.get("url")})
            return {k: v for k, v in item.items() if v}
        item.update({"author": authors, "datePublished": str(p["year"]), "url": p["link"] or None,
                     "abstract": loc(p.get("summary"), lang) or None, "pagination": p.get("pages")})
        if p.get("doi"):
            item["sameAs"] = p["doi_url"]
            item["identifier"] = {"@type": "PropertyValue", "propertyID": "DOI", "value": p["doi"]}
        if p["type"] == "article":
            item["isPartOf"] = {"@type": "PublicationIssue", "issueNumber": str(p.get("issue", "")),
                                "isPartOf": {"@type": "PublicationVolume", "volumeNumber": str(p.get("volume", "")),
                                             "isPartOf": {"@type": "Periodical", "name": p.get("journal")}}}
        elif p["type"] in ("chapter", "proceedings"):
            item["isPartOf"] = {"@type": "Book", "name": p.get("container"),
                                "editor": [{"@type": "Person", "name": full_name(e)} for e in p.get("editors", [])],
                                "publisher": {"@type": "Organization", "name": p.get("publisher")}}
        elif p["type"] == "report":
            item["publisher"] = {"@type": "Organization", "name": p.get("institution")}
        elif p["type"] == "thesis":
            item["inSupportOf"] = p.get("degree")
            item["sourceOrganization"] = {"@type": "CollegeOrUniversity", "name": p.get("institution")}
            item["award"] = p.get("award")
        return {k: v for k, v in item.items() if v}

    def note_ld(self, n):
        citations = []
        for st in n["studies"]:
            link = "https://doi.org/{}".format(st["doi"]) if st.get("doi") else st.get("url")
            citations.append({"@type": "CreativeWork", "name": st.get("title"), "author": st.get("authors"),
                              "datePublished": str(st.get("year", "")), "url": link})
        post = {"@type": "BlogPosting", "@id": self.abs_url(n["url"]) + "#post", "headline": n["title"],
                "description": n["description"], "datePublished": n["date"].isoformat(),
                "dateModified": n["updated"].isoformat(), "inLanguage": n["lang"],
                "author": self.person_ref(), "publisher": self.person_ref(),
                "mainEntityOfPage": self.abs_url(n["url"]), "url": self.abs_url(n["url"]),
                "keywords": ", ".join(n["tags"]), "wordCount": n["words"],
                "image": self.abs_url("/assets/img/og-image.png"),
                "isPartOf": {"@type": "Blog", "@id": self.abs_url(ROUTES["notes"][DEFAULT_LANG]) + "#blog"},
                "citation": citations}
        return {k: v for k, v in post.items() if v}

    # ------------------------------------------------------------- Formatierung

    def venue_html(self, p, lang: str) -> Markup:
        t = self.strings[lang]
        e = lambda value: str(escape(value))  # noqa: E731
        typ, parts = p["type"], []
        if typ == "article":
            text = "<em>{}</em>".format(e(p.get("journal", "")))
            if p.get("volume"):
                text += ", <em>{}</em>".format(e(p["volume"]))
                if p.get("issue"):
                    text += "({})".format(e(p["issue"]))
            if p.get("pages"):
                text += ", {}".format(e(p["pages"]))
            parts.append(text + ".")
        elif typ in ("chapter", "proceedings"):
            names = [short_name(n) for n in p.get("editors", [])]
            if len(names) > 3:
                editors = "{} {}".format(names[0], t["et_al"])
            elif len(names) > 1:
                editors = ", ".join(names[:-1]) + " & " + names[-1]
            else:
                editors = "".join(names)
            text = "{} {} ({}), ".format(t["in"], e(editors), t["eds"]) if editors else t["in"] + " "
            text += "<em>{}</em>".format(e(p.get("container", "")))
            if p.get("pages"):
                text += " ({} {})".format(t["pp"], e(p["pages"]))
            text += "."
            if p.get("publisher"):
                text += " {}.".format(e(p["publisher"]))
            parts.append(text)
        elif typ == "report":
            parts.append("{}.".format(e(p.get("institution", ""))))
        elif typ == "thesis":
            parts.append("{}, {}, {}.".format(e(p.get("degree", "")), e(p.get("institution", "")),
                                              e(loc(p.get("place"), lang))))
            if p.get("award"):
                template = "Ausgezeichnet mit dem {}." if lang == "de" else "Awarded the {}."
                parts.append(template.format(e(p["award"])))
        elif typ == "talk":
            event, place = loc(p.get("event"), lang), loc(p.get("place"), lang)
            parts.append("{}{}.".format(e(event), ", " + e(place) if place else ""))
        note = loc(p.get("note"), lang)
        if note:
            parts.append(e(note))
        return Markup(" ".join(parts))

    def authors_html(self, names) -> Markup:
        items = []
        for name in names:
            label = escape(apa_name(name))
            if split_name(name)[0] == self.family:
                label = Markup("<strong>{}</strong>").format(label)
            items.append(Markup(label))
        if len(items) <= 1:
            return Markup("").join(items)
        return Markup(", ").join(items[:-1]) + Markup(", &amp; ") + items[-1]

    def pub_view(self, p, lang: str):
        view = dict(p)
        view["authors_html"] = self.authors_html(p["authors"])
        view["venue_html"] = self.venue_html(p, lang)
        view["summary_text"] = loc(p.get("summary"), lang)
        view["type_label"] = self.strings[lang]["type_labels"][p["type"]]
        return view

    def note_view(self, n, lang: str):
        view = dict(n)
        view["date_text"] = fmt_date(n["date"], lang)
        view["lang_label"] = self.strings[lang]["note_lang_" + n["lang"]]
        return view

    def comic_view(self, c, lang: str):
        view = dict(c)
        view["title_text"] = loc(c.get("title"), lang)
        view["description_text"] = loc(c.get("description"), lang)
        view["size_text"] = human_size(c["bytes"], lang) if c["available"] else ""
        if c["based_on_pub"]:
            view["based_on_text"] = "{} ({})".format(c["based_on_pub"]["title"], c["based_on_pub"]["year"])
            view["based_on_link"] = c["based_on_pub"]["link"]
        return view

    # ------------------------------------------------------------- Rendern

    def base_context(self, lang: str, url: str, key: str):
        t = self.strings[lang]
        other = "en" if lang == "de" else "de"
        alternates = []
        if key in ROUTES:
            alternates = [{"lang": l, "url": self.abs_url(ROUTES[key][l])} for l in LANGS]
            alternates.append({"lang": "x-default", "url": self.abs_url(ROUTES[key][DEFAULT_LANG])})
        profiles = [{"label": (v.get("label_en") if lang == "en" and v.get("label_en") else v["label"]), "url": v["url"]}
                    for v in self.site.get("profiles", {}).values() if v.get("url")]
        return {
            "site": self.site, "lang": lang, "t": t, "routes": {k: v[lang] for k, v in ROUTES.items()},
            "other_lang": other, "other_url": ROUTES.get(key, ROUTES["home"])[other],
            "alternates": alternates, "canonical": self.abs_url(url), "rel": self.make_rel(url),
            "abs_url": self.abs_url, "build_id": self.build_id, "year": self.today.year,
            "preview": self.preview, "active": key, "profiles": profiles, "portrait": self.portrait,
            "job_title": loc(self.site["job_title"], lang),
            "affiliation_name": self.site["affiliation"]["name"] if lang == "de" else self.site["affiliation"]["name_en"],
            "campus": loc(self.site["affiliation"]["campus"], lang),
        }

    def render(self, template: str, url: str, context: dict, sitemap_key: str = None, lastmod=None,
               alternates=None, index: bool = True):
        html = self.env.get_template(template).render(**context)
        target = self.out_path(url)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        if index:
            self.sitemap.append({"loc": self.abs_url(url), "lastmod": (lastmod or self.today).isoformat(),
                                 "alternates": alternates or []})

    def page_alternates(self, key: str):
        alts = [{"lang": l, "url": self.abs_url(ROUTES[key][l])} for l in LANGS]
        alts.append({"lang": "x-default", "url": self.abs_url(ROUTES[key][DEFAULT_LANG])})
        return alts

    def build_home(self, lang: str):
        url = ROUTES["home"][lang]
        meta, body = self.profile[lang]
        ctx = self.base_context(lang, url, "home")
        published_notes = [self.note_view(n, lang) for n in self.notes][:3]
        papers = [self.pub_view(p, lang) for p in self.pubs if p["type"] != "talk"][:3]
        graph = [self.website_ld(),
                 {"@type": "ProfilePage", "@id": self.abs_url(url) + "#profilepage", "url": self.abs_url(url),
                  "name": meta.get("title"), "inLanguage": lang, "isPartOf": {"@id": self.website_id},
                  "mainEntity": {"@id": self.person_id}, "dateModified": self.today.isoformat()},
                 self.person_ld(lang)]
        ctx.update({
            "page_title": meta.get("title"), "description": meta.get("description"), "og_type": "profile",
            "claim": meta.get("claim", ""), "profile_html": md_html(body),
            "facts": [{"label": loc(f["label"], lang), "value": loc(f["value"], lang)} for f in self.facts],
            "research": [dict(r[lang], id=r["id"]) for r in self.research],
            "notes": published_notes, "papers": papers,
            "comics": [self.comic_view(c, lang) for c in self.comics],
            "jsonld": json_ld({"@context": "https://schema.org", "@graph": graph}),
        })
        self.render("home.html", url, ctx, alternates=self.page_alternates("home"))

    def build_publications(self, lang: str):
        url = ROUTES["publications"][lang]
        t = self.strings[lang]
        ctx = self.base_context(lang, url, "publications")
        groups = []
        for year in sorted({p["year"] for p in self.pubs}, reverse=True):
            groups.append({"year": year, "items": [self.pub_view(p, lang) for p in self.pubs if p["year"] == year]})
        items = [{"@type": "ListItem", "position": i + 1, "item": self.pub_ld(p, lang)} for i, p in enumerate(self.pubs)]
        graph = [{"@type": "CollectionPage", "@id": self.abs_url(url) + "#page", "url": self.abs_url(url),
                  "name": t["pubs_page_title"], "description": t["pubs_page_description"], "inLanguage": lang,
                  "isPartOf": {"@id": self.website_id}, "about": {"@id": self.person_id},
                  "mainEntity": {"@type": "ItemList", "numberOfItems": len(items), "itemListElement": items}},
                 self.breadcrumb_ld(lang, [(t["pubs_heading"], url)])]
        ctx.update({"page_title": t["pubs_page_title"], "description": t["pubs_page_description"],
                    "og_type": "website", "groups": groups, "count": len(self.pubs),
                    "intro": t["pubs_intro"].format(n=len(self.pubs)),
                    "jsonld": json_ld({"@context": "https://schema.org", "@graph": graph})})
        self.render("publications.html", url, ctx, alternates=self.page_alternates("publications"))

    def build_notes_index(self, lang: str):
        url = ROUTES["notes"][lang]
        t = self.strings[lang]
        ctx = self.base_context(lang, url, "notes")
        views = [self.note_view(n, lang) for n in self.notes]
        blog = {"@type": "Blog", "@id": self.abs_url(ROUTES["notes"][DEFAULT_LANG]) + "#blog", "url": self.abs_url(url),
                "name": t["notes_page_title"], "description": t["notes_page_description"], "inLanguage": lang,
                "author": self.person_ref(), "isPartOf": {"@id": self.website_id},
                "blogPost": [{"@type": "BlogPosting", "headline": n["title"], "url": self.abs_url(n["url"]),
                              "datePublished": n["date"].isoformat(), "inLanguage": n["lang"]} for n in self.notes]}
        graph = [blog, self.breadcrumb_ld(lang, [(t["notes_heading"], url)])]
        ctx.update({"page_title": t["notes_page_title"], "description": t["notes_page_description"],
                    "og_type": "website", "notes": views,
                    "jsonld": json_ld({"@context": "https://schema.org", "@graph": graph})})
        lastmod = self.notes[0]["updated"] if self.notes else None
        self.render("notes.html", url, ctx, lastmod=lastmod, alternates=self.page_alternates("notes"))

    def build_note(self, n):
        lang = n["lang"]
        t = self.strings[lang]
        ctx = self.base_context(lang, n["url"], "note")
        ctx["alternates"] = []
        ctx["other_url"] = ROUTES["notes"]["en" if lang == "de" else "de"]
        citation = "{} ({}). {}. {}: {}".format(
            apa_name(self.site["family_name"] + ", " + self.site["given_name"]), n["date"].year, n["title"],
            "Forschungsnotiz" if lang == "de" else "Research note", self.abs_url(n["url"]))
        graph = [self.note_ld(n), self.breadcrumb_ld(lang, [(t["notes_heading"], ROUTES["notes"][lang]), (n["title"], n["url"])])]
        ctx.update({"page_title": "{} – {}".format(n["title"], self.site["name"]), "description": n["description"],
                    "og_type": "article", "note": self.note_view(n, lang), "citation": citation,
                    "updated_text": fmt_date(n["updated"], lang),
                    "jsonld": json_ld({"@context": "https://schema.org", "@graph": graph})})
        self.render("note.html", n["url"], ctx, lastmod=n["updated"], index=not n["draft"])

    def build_comics(self, lang: str):
        url = ROUTES["comics"][lang]
        t = self.strings[lang]
        ctx = self.base_context(lang, url, "comics")
        parts = []
        for c in self.comics:
            work = {"@type": "CreativeWork", "name": loc(c["title"], lang), "description": loc(c["description"], lang),
                    "genre": "Wissenschaftscomic" if lang == "de" else "Science comic", "author": self.person_ref(),
                    "inLanguage": lang}
            if c["available"]:
                work["associatedMedia"] = {"@type": "MediaObject", "contentUrl": self.abs_url(c["url"]),
                                           "encodingFormat": "application/pdf"}
            if c["based_on_pub"]:
                work["isBasedOn"] = {"@id": self.abs_url(ROUTES["publications"][DEFAULT_LANG]) + "#" + c["based_on_pub"]["id"]}
            parts.append(work)
        graph = [{"@type": "CollectionPage", "url": self.abs_url(url), "name": t["comics_page_title"],
                  "description": t["comics_page_description"], "inLanguage": lang, "hasPart": parts,
                  "isPartOf": {"@id": self.website_id}},
                 self.breadcrumb_ld(lang, [(t["comics_heading"], url)])]
        ctx.update({"page_title": t["comics_page_title"], "description": t["comics_page_description"],
                    "og_type": "website", "comics": [self.comic_view(c, lang) for c in self.comics],
                    "jsonld": json_ld({"@context": "https://schema.org", "@graph": graph})})
        self.render("comics.html", url, ctx, alternates=self.page_alternates("comics"))

    def build_legal(self, lang: str, key: str, filename: str):
        url = ROUTES[key][lang]
        meta, body = read_md(CONTENT / "rechtliches" / "{}.{}.md".format(filename, lang))
        ctx = self.base_context(lang, url, key)
        other = "en" if lang == "de" else "de"
        body_rendered = self.env.from_string(body).render(
            site=self.site, imprint_url=ctx["rel"](ROUTES["imprint"][lang]),
            other_url=ctx["rel"](ROUTES[key][other]), today_month=fmt_month(self.today, lang))
        graph = [{"@type": "WebPage", "url": self.abs_url(url), "name": meta.get("title"), "inLanguage": lang,
                  "isPartOf": {"@id": self.website_id}},
                 self.breadcrumb_ld(lang, [(meta.get("title"), url)])]
        ctx.update({"page_title": "{} – {}".format(meta.get("title"), self.site["name"]),
                    "description": meta.get("description"), "og_type": "website", "heading": meta.get("title"),
                    "body_html": md_html(body_rendered),
                    "jsonld": json_ld({"@context": "https://schema.org", "@graph": graph})})
        self.render("page.html", url, ctx, alternates=self.page_alternates(key))

    def build_404(self):
        ctx = self.base_context(DEFAULT_LANG, "/404.html", "notfound")
        t = self.strings[DEFAULT_LANG]
        ctx["old_paths"] = OLD_PATHS
        ctx.update({"page_title": "{} – {}".format(t["not_found_title"], self.site["name"]),
                    "description": t["not_found_text"], "og_type": "website", "noindex": True,
                    "jsonld": json_ld({"@context": "https://schema.org", "@type": "WebPage", "name": t["not_found_title"]})})
        self.render("404.html", "/404.html", ctx, index=False)

    # ------------------------------------------------------------- Zusatzdateien

    def write(self, rel_path: str, text: str):
        target = self.out / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def write_sitemap(self):
        lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
        for entry in self.sitemap:
            lines.append("  <url>")
            lines.append("    <loc>{}</loc>".format(xml_escape(entry["loc"])))
            lines.append("    <lastmod>{}</lastmod>".format(entry["lastmod"]))
            for alt in entry["alternates"]:
                lines.append('    <xhtml:link rel="alternate" hreflang="{}" href="{}"/>'.format(alt["lang"], xml_escape(alt["url"])))
            lines.append("  </url>")
        lines.append("</urlset>")
        self.write("sitemap.xml", "\n".join(lines) + "\n")

    def write_robots(self):
        bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User",
                "Google-Extended", "PerplexityBot", "Perplexity-User", "Applebot-Extended", "MistralAI-User",
                "meta-externalagent", "Amazonbot", "DuckAssistBot", "CCBot"]
        text = ["# Diese Website darf von Suchmaschinen und KI-Systemen gelesen werden.",
                "# This website may be read by search engines and AI systems.", "",
                "User-agent: *", "Allow: /", "",
                "# KI-Crawler ausdrücklich erlaubt / AI crawlers explicitly allowed"]
        text += ["User-agent: {}".format(b) for b in bots]
        text += ["Allow: /", "", "Sitemap: {}".format(self.abs_url("/sitemap.xml")), ""]
        self.write("robots.txt", "\n".join(text))

    def write_feed(self):
        items = []
        for n in self.notes:
            if n["draft"]:
                continue
            pub_date = dt.datetime.combine(n["date"], dt.time(9, 0)).strftime("%a, %d %b %Y %H:%M:%S +0000")
            items.append(
                "  <item>\n    <title>{t}</title>\n    <link>{l}</link>\n    <guid>{l}</guid>\n"
                "    <pubDate>{d}</pubDate>\n    <description>{s}</description>\n  </item>".format(
                    t=xml_escape(n["title"]), l=xml_escape(self.abs_url(n["url"])), d=pub_date, s=xml_escape(n["summary"])))
        feed = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
                '<channel>\n  <title>Forschungsnotizen – Damian Leschik</title>\n  <link>{home}</link>\n'
                '  <atom:link href="{feed}" rel="self" type="application/rss+xml"/>\n'
                '  <description>{desc}</description>\n  <language>de</language>\n{items}\n</channel>\n</rss>\n').format(
                    home=xml_escape(self.abs_url(ROUTES["notes"]["de"])), feed=xml_escape(self.abs_url("/feed.xml")),
                    desc=xml_escape(self.strings["de"]["notes_page_description"]), items="\n".join(items))
        self.write("feed.xml", feed)

    def citation_text(self, p, lang: str) -> str:
        text = re.sub(r"<[^>]+>", "", str(self.venue_html(p, lang)))
        text = text.replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", '"')
        line = "{} ({}). {}. {}".format(join_apa(p["authors"]), p["year"], p["title"], text)
        return line + (" " + p["link"] if p["link"] else "")

    def write_llms(self):
        s = self.site
        en_meta, en_body = self.profile["en"]
        de_meta, de_body = self.profile["de"]
        strip_md = lambda text: re.sub(r"\*\*(.+?)\*\*", r"\1", text).strip()  # noqa: E731
        pub_lines = ["- " + self.citation_text(p, "en") for p in self.pubs]
        note_lines = ["- [{}]({}) ({}, {}): {}".format(n["title"], self.abs_url(n["url"]), n["date"].isoformat(),
                                                       n["lang"], n["summary"]) for n in self.notes if not n["draft"]]
        facts = ["- {}: {}".format(loc(f["label"], "en"), loc(f["value"], "en")) for f in self.facts]
        profiles = ["- {}: {}".format(v.get("label_en", v["label"]), v["url"])
                    for v in s.get("profiles", {}).values() if v.get("url")]
        research = ["- {}: {}".format(r["en"]["title"], r["en"]["text"]) for r in self.research]
        comics = ["- {}: {}".format(loc(c["title"], "en"), loc(c["description"], "en")) for c in self.comics if c["available"]]
        def lower_first(text):
            return text[0].lower() + text[1:] if len(text) > 1 and text[1].islower() else text
        summary_en = ("{} {} is {} at {} ({}). Research topics: {}.").format(
            s["honorific"], s["name"], loc(s["job_title"], "en"), s["affiliation"]["name_en"],
            loc(s["affiliation"]["campus"], "en"),
            "; ".join(lower_first(r["en"]["title"]) for r in self.research))
        summary_de = "{} {} Er ist {} an der {} ({}).".format(
            s["name"], de_meta.get("claim", ""), loc(s["job_title"], "de"),
            s["affiliation"].get("name_dative", s["affiliation"]["name"]), loc(s["affiliation"]["campus"], "de"))
        head = [
            "# {}".format(s["name"]), "",
            "> " + summary_en, "",
            "Deutsch: " + summary_de, "",
            "## Key facts", ""] + facts + ["- Contact: {}".format(s.get("email", ""))] + profiles + [
            "", "## Pages", "",
            "- [Home, English]({}): profile, research interests, latest research notes".format(self.abs_url(ROUTES["home"]["en"])),
            "- [Startseite, Deutsch]({}): Kurzprofil, Forschungsschwerpunkte".format(self.abs_url(ROUTES["home"]["de"])),
            "- [Publications]({}): complete list with DOIs".format(self.abs_url(ROUTES["publications"]["en"])),
            "- [Research notes]({}): recent studies presented and discussed".format(self.abs_url(ROUTES["notes"]["en"])),
            "- [Research as comics]({}): free PDF downloads".format(self.abs_url(ROUTES["comics"]["en"])),
            "", "## Research interests", ""] + research + [
            "", "## Publications", ""] + pub_lines + [
            "", "## Research notes", ""] + (note_lines or ["- (none published yet)"])
        if comics:
            head += ["", "## Comics", ""] + comics
        head += ["", "## Optional", "",
                 "- [Full text for language models]({})".format(self.abs_url("/llms-full.txt")),
                 "- [Publications as BibTeX]({})".format(self.abs_url("/publikationen.bib")),
                 "- [Publications as JSON (CSL)]({})".format(self.abs_url("/publikationen.json")), ""]
        self.write("llms.txt", "\n".join(head))

        full = ["# {} – full text".format(s["name"]), "",
                "Source: {} (generated {})".format(self.abs_url("/"), self.today.isoformat()), "",
                "## Profile (English)", "", strip_md(en_body), "",
                "## Kurzprofil (Deutsch)", "", strip_md(de_body), "",
                "## At a glance", ""] + facts + ["", "## Research interests", ""] + research
        full += ["", "## Publications (with summaries)", ""]
        for p in self.pubs:
            full.append("- " + self.citation_text(p, "en"))
            summary = loc(p.get("summary"), "en")
            if summary:
                full.append("  Summary: " + summary)
        for n in self.notes:
            if n["draft"]:
                continue
            full += ["", "## Research note: {}".format(n["title"]), "",
                     "URL: {} | Date: {} | Language: {}".format(self.abs_url(n["url"]), n["date"].isoformat(), n["lang"]), "",
                     n["body_md"].strip()]
            if n["studies"]:
                full += ["", "Studies discussed:"] + ["- {} ({}). {}. {}. {}".format(
                    st.get("authors", ""), st.get("year", ""), st.get("title", ""), st.get("venue", ""),
                    "https://doi.org/" + st["doi"] if st.get("doi") else st.get("url", "")) for st in n["studies"]]
        if comics:
            full += ["", "## Comics", ""] + comics
        self.write("llms-full.txt", "\n".join(full) + "\n")

    def write_exports(self):
        entries = []
        for p in self.pubs:
            fields = [("author", " and ".join(p["authors"])), ("title", "{" + p["title"] + "}"), ("year", p["year"])]
            if p["type"] == "article":
                fields += [("journal", p.get("journal")), ("volume", p.get("volume")), ("number", p.get("issue")), ("pages", p.get("pages"))]
            elif p["type"] in ("chapter", "proceedings"):
                fields += [("booktitle", p.get("container")), ("editor", " and ".join(p.get("editors", []))),
                           ("publisher", p.get("publisher")), ("pages", p.get("pages"))]
            elif p["type"] in ("report",):
                fields += [("institution", p.get("institution"))]
            elif p["type"] == "thesis":
                fields += [("school", p.get("institution")), ("type", p.get("degree"))]
            elif p["type"] == "talk":
                fields += [("howpublished", "{} {}".format("Talk,", loc(p.get("event"), "en")))]
            fields += [("doi", p.get("doi")), ("url", p.get("url") if not p.get("doi") else None)]
            lines = []
            for key, value in fields:
                if not value:
                    continue
                if key == "title":  # doppelte Klammern erhalten die Groß-/Kleinschreibung
                    lines.append("  title = {{{{{}}}}}".format(bib_escape(p["title"])))
                elif key == "doi":
                    lines.append("  doi = {{{}}}".format(value))
                else:
                    lines.append("  {} = {{{}}}".format(key, bib_escape(value)))
            entries.append("@{}{{{},\n{}\n}}".format(TYPE_BIB[p["type"]], p["id"], ",\n".join(lines)))
        self.write("publikationen.bib", "% Publikationen von Damian Leschik – {}\n\n".format(self.abs_url("/")) + "\n\n".join(entries) + "\n")

        csl = []
        for p in self.pubs:
            item = {"id": p["id"], "type": TYPE_CSL[p["type"]], "title": p["title"],
                    "author": [{"family": split_name(a)[0], "given": split_name(a)[1]} for a in p["authors"]],
                    "issued": {"date-parts": [[p["year"]]]}, "language": p.get("language")}
            if p["type"] == "article":
                item.update({"container-title": p.get("journal"), "volume": str(p.get("volume", "")), "issue": str(p.get("issue", "")),
                             "page": p.get("pages")})
            elif p["type"] in ("chapter", "proceedings"):
                item.update({"container-title": p.get("container"), "publisher": p.get("publisher"), "page": p.get("pages"),
                             "editor": [{"family": split_name(e)[0], "given": split_name(e)[1]} for e in p.get("editors", [])]})
            elif p["type"] in ("report", "thesis"):
                item.update({"publisher": p.get("institution"), "genre": p.get("degree")})
            elif p["type"] == "talk":
                item.update({"event-title": loc(p.get("event"), "en"), "event-place": loc(p.get("place"), "en")})
            item.update({"DOI": p.get("doi"), "URL": p["link"] or None, "abstract": loc(p.get("summary"), "en") or None})
            csl.append({k: v for k, v in item.items() if v})
        self.write("publikationen.json", json.dumps(csl, ensure_ascii=False, indent=2) + "\n")

    def copy_static(self):
        for src in STATIC.rglob("*"):
            if src.is_dir() or src.name.startswith((".", "_")) or src.suffix.lower() == ".md":
                continue
            dst = self.out / src.relative_to(STATIC)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    def write_misc(self):
        host = re.sub(r"^https?://", "", self.base).split("/")[0]
        if not self.preview and not host.endswith("github.io"):
            self.write("CNAME", host + "\n")
        self.write(".nojekyll", "")

    # ------------------------------------------------------------- Ablauf

    def prepare_out(self):
        """Ausgabeordner leeren. Ist Löschen nicht erlaubt (z. B. in geschützten Ordnern),
        werden die Dateien einfach überschrieben; veraltete Dateien bleiben dann liegen."""
        if self.out.exists():
            try:
                shutil.rmtree(self.out)
            except OSError:
                self.warn("Ausgabeordner {} konnte nicht geleert werden (Löschen nicht erlaubt). "
                          "Dateien werden überschrieben; veraltete Dateien bleiben liegen.".format(self.out.name))
        self.out.mkdir(parents=True, exist_ok=True)

    def run(self):
        self.prepare_out()
        self.load()
        self.copy_static()
        for lang in LANGS:
            self.build_home(lang)
            self.build_publications(lang)
            self.build_notes_index(lang)
            self.build_comics(lang)
            self.build_legal(lang, "imprint", "impressum")
            self.build_legal(lang, "privacy", "datenschutz")
        for note in self.notes:
            self.build_note(note)
        self.build_404()
        self.write_sitemap()
        self.write_robots()
        self.write_feed()
        self.write_llms()
        self.write_exports()
        self.write_misc()
        pages = sum(1 for _ in self.out.rglob("*.html"))
        print("Fertig: {} Seiten in {}".format(pages, self.out.relative_to(ROOT) if self.out.is_relative_to(ROOT) else self.out))
        if self.warnings:
            print("\nHinweise ({}):".format(len(self.warnings)))
            for msg in self.warnings:
                print("  - " + msg)
        if self.preview:
            print("\nVorschau öffnen: {}".format(self.out / "index.html"))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Baut die Website damianleschik.com")
    parser.add_argument("--vorschau", action="store_true", help="Vorschau mit Entwürfen nach _vorschau/ (per Doppelklick lesbar)")
    parser.add_argument("--entwuerfe", action="store_true", help="Entwürfe auch in die Veröffentlichungs-Version aufnehmen")
    parser.add_argument("--base-url", help="Adresse der Website (Standard: url aus site.yaml)")
    parser.add_argument("--out", help="Ausgabeordner")
    Builder(parser.parse_args(argv)).run()


if __name__ == "__main__":
    main()
