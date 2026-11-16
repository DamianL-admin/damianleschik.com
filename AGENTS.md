# Arbeitsanweisung für KI-Agenten – damianleschik.com

Diese Datei steuert jeden KI-Agenten, der an dieser Website arbeitet (geplanter Optimierungs-Agent, Claude, Codex, Copilot). Sie gilt vor allen anderen Annahmen.

## Zweck und Ziele

Persönliche, akademische Website von **Prof. Dr. Damian Leschik**, Professor für Betriebswirtschaftslehre mit Schwerpunkt Marketing an der IU Internationalen Hochschule (Aachen/Köln). Ziele in dieser Reihenfolge:

1. **Korrekt.** Jede Angabe stimmt: Publikationen, Titel, Jahre, Zahlen, Quellen.
2. **Auffindbar.** Für Suchmaschinen (Google, Bing) und KI-Systeme (ChatGPT, Claude, Gemini, Perplexity, Mistral, Grok).
3. **Einfach.** Schlichte Gestaltung, schnell, barrierearm. Cookies und Tracking nur mit Einwilligung (Google Analytics 4, siehe Regel 4).
4. **Aktuell.** Neue Publikationen zeitnah, alle 2–4 Wochen eine Forschungsnotiz.

## Projektaufbau

| Was | Wo |
|---|---|
| Zentrale Angaben (Name, Domain, Profile, Impressum-Daten) | `site.yaml` |
| Kurzprofil DE/EN, Seitentitel, großer Satz oben | `content/profil.de.md`, `content/profil.en.md` |
| „Auf einen Blick“ | `content/fakten.yaml` |
| Forschungsschwerpunkte | `content/forschung.yaml` |
| Publikationen (Quelle für Seite, BibTeX, JSON, JSON-LD, llms.txt) | `content/publikationen.yaml` |
| Forschungsnotizen (veröffentlicht) | `content/notizen/*.md` (Vorlage: `content/notizen/_vorlage.md`) |
| Entwürfe für Notizen (nur lokal, nie ins Repository) | `content/entwuerfe/*.md` |
| Berichte (nur lokal, nie ins Repository) | `berichte/` |
| Comics (Texte) / PDFs | `content/comics.yaml` / `static/downloads/` |
| Impressum, Datenschutz | `content/rechtliches/` |
| Oberflächentexte (Navigation, Buttons) | `templates/strings.yaml` |
| Seitenvorlagen | `templates/*.html` |
| Gestaltung (Farben/Schriften als Variablen in `:root`) | `static/assets/css/site.css` |
| Build | `build.py` → `_site/` (Veröffentlichung), `_vorschau/` (mit Entwürfen) |
| Prüfung SEO/GEO + offene Aufgaben | `tools/audit.py` |
| Veröffentlichung über GitHub Pages (Vorlage, gehört im Repository nach `.github/workflows/deploy.yml`; Workflow-Dateien sind für Remote-Werkzeuge geschützt, daher nur über Git anlegen) | `deploy/github-pages.yml` |
| Berichte des Agenten | `berichte/` |

Erzeugt werden automatisch: alle HTML-Seiten (EN als Hauptsprache unter `/`, DE unter `/de/`; alte Adressen bis 16.11.2026 leitet die 404-Seite um), `sitemap.xml` (mit hreflang), `robots.txt`, `llms.txt`, `llms-full.txt`, `feed.xml`, `publikationen.bib`, `publikationen.json`, strukturierte Daten (JSON-LD: Person, ProfilePage, ScholarlyArticle/Chapter, BlogPosting mit citation, BreadcrumbList).

## Befehle

```bash
pip install -r requirements.txt        # einmalig
python3 build.py                       # Veröffentlichungs-Version nach _site/
python3 build.py --vorschau            # Vorschau inkl. Entwürfe nach _vorschau/ (index.html per Doppelklick)
python3 tools/audit.py --bericht       # Prüfung, Bericht nach berichte/audit-JJJJ-MM-TT.md
python3 tools/pdf_metadata.py DATEI.pdf --title "…" --subject "…" --keywords "…"   # PDF-Metadaten
python3 tools/og_image.py              # Vorschaubild für soziale Medien neu erzeugen (braucht Playwright)
```

Nach jeder Änderung: bauen und prüfen. Ziel: 0 Fehler, Warnungen nur bei Punkten, die Damians Entscheidung brauchen.

**Arbeiten auf Damians Mac (über die Claude-Desktop-App):** Der Projektordner liegt unter `~/Documents/Claude/Projects/Homepage/damianleschik.com`. Löschen ist dort standardmäßig gesperrt. `build.py` überschreibt deshalb Dateien, statt den Ausgabeordner zu leeren; veraltete Dateien in `_site/` sind unkritisch, weil GitHub Actions beim Veröffentlichen immer frisch baut. Git-Befehle brauchen Löschrechte (Lock-Dateien). Ohne Freigabe kein `git commit` im lokalen Ordner, stattdessen im Bericht vermerken.

## Feste Regeln

1. **Nichts erfinden.** Keine Publikationen, Zitate, Zahlen, DOIs, Auszeichnungen oder Lebenslaufangaben ohne geprüfte Quelle (Verlagsseite, DOI-Auflösung, IU-Profil, ORCID). Unsicheres mit `verified: false` und `check: …` eintragen.
2. **Inhalte in Damians Namen nur als Entwurf.** Forschungsnotizen immer als Entwurf in `content/entwuerfe/` mit `draft: true` anlegen, nie direkt in `content/notizen/`. Das GitHub-Repository ist öffentlich; Entwürfe und Berichte sind per `.gitignore` ausgeschlossen. Profiltexte und Forschungsschwerpunkte nicht umschreiben, sondern Vorschläge im Bericht machen. Damian gibt frei.
3. **Rechtstexte nicht inhaltlich ändern** (`content/rechtliches/`, Impressum-Daten in `site.yaml`). Nur Hinweise im Bericht.
4. **Keine Cookies, kein Tracking, keine externen Skripte, Schriften oder Einbettungen – einzige Ausnahme: Google Analytics 4 nach Einwilligung.** GA4 wird nur über das eigene Banner in `templates/base.html` geladen (Mess-ID in `site.yaml` unter `analytics.ga4_id`; leer = aus). Vor der Einwilligung darf keine Anfrage an Google gehen; Ablehnen muss so einfach sein wie Zustimmen; „Cookie-Einstellungen“ steht auf jeder Seite. `tools/audit.py` prüft das. Keine weiteren Tracking-Dienste, keine neuen Abhängigkeiten ohne klaren Nutzen.
5. **KI-Crawler nie blockieren** (robots.txt wird erzeugt; auch Hoster-/CDN-Einstellungen prüfen, z. B. Cloudflare „Block AI bots“).
6. **Deutsch und Englisch synchron halten.** Änderung in einer Sprache immer auch in der anderen.
7. **Einfache, klare Sprache.** Kurze Sätze, wenig Fachjargon; Fachbegriffe nur, wo im Feld üblich.
8. **Gestaltung nur mit gutem Grund ändern.** Farben und Schriften stehen in `site.css` unter `:root`. Leitbild (Damians Wunsch, angelehnt an yoshuabengio.org, aber eigenständig): ruhiger, warmer Hintergrund; rundes Porträt zentriert über einem weichen Farbverlauf; große Serifen-Überschrift in Petrol; Menü und Abschnittsüberschriften in Versalien; Forschungsnotizen als gerahmte Einträge mit Datum und Autor. Keine fremden Texte, Bilder oder Logos übernehmen.
9. **Nichts löschen ohne Rückfrage.** Keine Zugangsdaten in Dateien oder Commits.
10. **Quellenangaben nicht verkürzen.** Jede besprochene Studie in Notizen mit DOI oder Link unter `studies:`.

## Routine-Lauf (geplanter Task)

1. **Stand holen.** Wenn Git-Repository mit Remote: `git pull`.
2. **Bauen und prüfen.** `python3 build.py && python3 tools/audit.py --bericht`. Ergebnis merken (vorher).
3. **Technik verbessern.** Fehler und Warnungen beheben, die keine Entscheidung von Damian brauchen (Titel- und Beschreibungslängen, Links, JSON-LD, Sitemap, Überschriften). Erneut bauen und prüfen (nachher).
4. **Publikationen aktualisieren.** Websuche nach neuen Veröffentlichungen: „Damian Leschik“, „Leschik, D.“, IU-Profil, Springer, Emerald, Crossref, Google Scholar und ORCID (falls in `site.yaml` eingetragen). Neue Funde mit vollständigen Angaben eintragen; `verified: true` nur, wenn DOI oder Verlagsseite die Angaben bestätigen. Offene `check`-Hinweise klären, wo möglich.
5. **Forschungsradar.** Neue Studien der letzten 4–8 Wochen zu Silicon Sampling und synthetischen Befragten, KI und Konsumentenverhalten, KI in der Marktforschung sowie Konsumentenverhalten allgemein suchen (z. B. Journal of Marketing, Journal of Marketing Research, Marketing Science, Journal of Consumer Research, Journal of Consumer Psychology, IJRM, Psychology & Marketing, NIM Marketing Intelligence Review, Pew Research Center, arXiv/SSRN). 2–3 Kandidaten mit einem Satz Begründung im Bericht nennen. Den stärksten als Entwurf `content/entwuerfe/JJJJ-MM-TT-kurztitel.md` nach `content/notizen/_vorlage.md` anlegen: Zahlen nur aus der Quelle, paraphrasieren statt zitieren, Abschnitt „Meine Einordnung“ als Vorschlag formulieren.
6. **Sichtbarkeit prüfen (GEO).** Websuche nach „Damian Leschik“ und „Damian Leschik Silicon Sampling“: Erscheint die Website? Stimmen Angaben im Netz (IU-Profil, Verlage, ORCID) mit der Website überein? Abweichungen im Bericht nennen.
7. **Bericht schreiben.** `berichte/JJJJ-MM-TT.md` mit: Prüfergebnis vorher/nachher, erledigten Änderungen, Vorschlägen (Publikationen, Notiz-Entwurf), höchstens fünf priorisierten Aufgaben für Damian.
8. **Veröffentlichen.** Nur wenn ein Git-Repository mit Remote existiert:
   - rein technische Korrekturen und den Bericht auf `main` committen und pushen (Commit-Nachricht auf Deutsch);
   - inhaltliche Änderungen (neue Publikationen, Notiz-Entwürfe) auf einem Branch `agent/JJJJ-MM-TT` committen und, falls `gh` verfügbar ist, einen Pull Request öffnen.
   Ohne Repository: Änderungen nur im Ordner lassen und im Bericht nennen.
9. **Kurz berichten.** Höchstens zehn Zeilen: was verbessert wurde, was Damian entscheiden muss.

## Häufige Aufgaben

**Neue Publikation eintragen.** Block in `content/publikationen.yaml` kopieren und oben einfügen. Pflichtfelder: `id`, `type`, `year`, `authors`, `title` plus typabhängige Felder (`journal`/`volume`/`issue`/`pages` oder `container`/`editors`/`publisher`). DOI ohne `https://doi.org/`. Kurze Zusammenfassung DE und EN in eigenen Worten.

**Forschungsnotiz veröffentlichen (nur nach Damians Freigabe).** Datei von `content/entwuerfe/` nach `content/notizen/` verschieben, `draft: false` setzen, bauen, prüfen. Die Notiz erscheint automatisch auf Startseite, Übersicht, in Sitemap, RSS und llms.txt.

**Comic einbinden.** PDF nach `static/downloads/` (Dateiname wie in `comics.yaml`). PDF lesen, Titel und 2–4 Sätze Beschreibung (DE/EN) mit der Kernaussage schreiben, `based_on` auf die Publikations-id setzen. Metadaten setzen: `python3 tools/pdf_metadata.py static/downloads/comic-1.pdf --title "…" --subject "…" --keywords "…"`. Optional Titelbild aus Seite 1 erzeugen (`pdftoppm -jpeg -r 80 -f 1 -l 1 …`) und unter `cover` eintragen.

**Besucherstatistik (GA4).** Mess-ID nur in `site.yaml` (`analytics.ga4_id`) ändern; Banner, Skript, Fußzeile und Datenschutzerklärung passen sich an. In GA4 eingestellt: Google Signals aus, Datenaufbewahrung wie `analytics.retention_months`. Banner-Texte stehen in `templates/strings.yaml` (`consent_*`). Rechtstexte zu GA4 nicht inhaltlich ändern (Regel 3).

**Porträt einfügen.** Quadratisches Foto als `static/assets/img/portrait.jpg` (mind. 800 × 800 px, unter 250 KB). Danach `python3 tools/og_image.py` und bauen.

**Domain ändern (.com/.org).** Nur `url` in `site.yaml` anpassen und bauen.

## Leitlinien für Auffindbarkeit (SEO und GEO)

- Jede Seite: eigener Titel (bis ca. 60 Zeichen), Beschreibung (120–160 Zeichen), genau eine H1, Canonical, hreflang DE/EN.
- Kernaussagen als klare Sätze mit Namen formulieren („Damian Leschik ist …“), damit KI-Systeme sie korrekt zitieren können.
- Strukturierte Daten aktuell halten; `sameAs` in `Person` mit ORCID, Google Scholar, LinkedIn und IU-Profil füllen (über `site.yaml`).
- Konsistenz: Name, Titel und Hochschule überall gleich (Website, IU-Profil, ORCID, Google Scholar, LinkedIn).
- Externe Verweise stärken die Sichtbarkeit: Website-Link im IU-Profil, bei ORCID, Google Scholar und LinkedIn eintragen lassen.
- Sitemap in Google Search Console und Bing Webmaster Tools einreichen (Bing speist u. a. ChatGPT-Suche und Copilot).
- Ehrliche Einordnung: `llms.txt` ist ein Vorschlag, kein Standard; der Nutzen ist unklar, der Aufwand gering. Kein Agent kann garantieren, dass KI-Systeme die Seite zitieren. Am wirksamsten sind korrekte, konsistente und aktuelle Inhalte sowie Verweise von seriösen Seiten.
