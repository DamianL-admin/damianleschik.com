# damianleschik.com – deine Homepage

Eine schlichte, schnelle Website mit Kurzprofil, Forschungsschwerpunkten, allen Publikationen, Forschungsnotizen und zwei Comics zum Download. Sie ist auf Deutsch und Englisch, setzt Cookies und Besucherstatistik (Google Analytics 4) nur mit Einwilligung ein und ist für Suchmaschinen und KI-Systeme (ChatGPT, Claude, Gemini, Perplexity, Mistral, Grok) gut lesbar.

## Inhalte ändern

Alle Inhalte sind einfache Textdateien. Nach einer Änderung einmal bauen (siehe unten).

| Was du ändern willst | Datei |
|---|---|
| Kurzprofil, großer Satz oben, Seitentitel | `content/profil.de.md` und `content/profil.en.md` |
| „Auf einen Blick“ | `content/fakten.yaml` |
| Forschungsschwerpunkte | `content/forschung.yaml` |
| Publikationen | `content/publikationen.yaml` (Anleitung steht oben in der Datei) |
| Neue Forschungsnotiz | `content/notizen/_vorlage.md` nach `content/entwuerfe/` kopieren, umbenennen, ausfüllen |
| Comics | PDFs nach `static/downloads/`, Texte in `content/comics.yaml` |
| Porträtfoto | als `static/assets/img/portrait.jpg` ablegen (quadratisch, mind. 800 px) |
| Domain, E-Mail, Profil-Links (ORCID, Scholar, LinkedIn), Impressum-Daten | `site.yaml` |

Entwürfe liegen in `content/entwuerfe/`. Dieser Ordner bleibt auf deinem Mac und kommt nicht ins öffentliche GitHub-Repository; in der Vorschau sind Entwürfe trotzdem zu sehen. Eine Notiz geht erst online, wenn sie nach `content/notizen/` verschoben ist und `draft: false` in ihr steht.

## Bauen und Vorschau ansehen

Im Terminal in diesem Ordner:

```bash
pip install -r requirements.txt   # nur beim ersten Mal
python3 build.py --vorschau       # Vorschau inklusive Entwürfen
```

Dann `_vorschau/index.html` per Doppelklick im Browser öffnen. Die Version zum Veröffentlichen entsteht mit `python3 build.py` im Ordner `_site/`.

Prüfen, ob alles für Google und KI-Systeme passt:

```bash
python3 tools/audit.py
```

## Vor der Veröffentlichung (Checkliste)

1. **Impressum vervollständigen:** Anschrift in `site.yaml` unter `impressum` eintragen (Pflicht nach § 5 DDG). Die Texte in `content/rechtliches/` sind sorgfältige Vorlagen, aber keine Rechtsberatung. Bitte einmal prüfen lassen.
2. **Porträtfoto** ablegen.
3. **Publikationen bestätigen:** Einträge mit `verified: false` in `content/publikationen.yaml` prüfen (der Prüfbericht listet sie auf).
4. **Forschungsnotiz freigeben:** Entwurf in `content/entwuerfe/` lesen, die Einordnung anpassen, nach `content/notizen/` verschieben und `draft: false` setzen.
5. **ORCID, Google Scholar, LinkedIn** in `site.yaml` eintragen. Diese Profile helfen KI-Systemen sehr, dich eindeutig zuzuordnen.
6. **E-Mail-Adresse** prüfen (aktuell die IU-Adresse; nach der Domain-Registrierung ist z. B. kontakt@damianleschik.com möglich).

## Veröffentlichen mit GitHub Pages (empfohlen, kostenlos)

1. **Domain registrieren:** damianleschik.com bei einem Anbieter deiner Wahl. Optional zusätzlich .org als Weiterleitung auf .com.
2. **GitHub-Konto** anlegen und ein öffentliches Repository `damianleschik.com` erstellen.
3. **Diesen Ordner hochladen.** Einfacher: GitHub in Claude verbinden (Einstellungen → Connectors). Dann übernimmt Claude das Hochladen und spätere Änderungen.
4. Beim Einrichten des Repositorys die Vorlage `deploy/github-pages.yml` nach `.github/workflows/deploy.yml` kopieren. Sie baut und veröffentlicht die Seite automatisch. Ist GitHub in Claude verbunden, erledigt Claude das. (Workflow-Dateien sind aus Sicherheitsgründen geschützt und werden deshalb nicht automatisch in diesen Ordner geschrieben.)
5. In GitHub unter **Settings → Pages**: Source auf **GitHub Actions** stellen, Custom domain `damianleschik.com` eintragen, **Enforce HTTPS** aktivieren.
6. **DNS beim Domain-Anbieter** einstellen:
   - A-Records für `@`: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - AAAA-Records für `@`: `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`
   - CNAME für `www`: `DEIN-GITHUB-NAME.github.io`
7. Nach einigen Minuten bis Stunden ist die Seite unter https://damianleschik.com erreichbar.
8. **Bei Google Search Console und Bing Webmaster Tools anmelden** und die Sitemap `https://damianleschik.com/sitemap.xml` einreichen. Bing ist wichtig, weil u. a. die ChatGPT-Suche und Copilot darauf zugreifen.
9. **Link zur Website eintragen** im IU-Profil, bei ORCID, Google Scholar und LinkedIn.

Bei jeder Änderung auf GitHub baut und veröffentlicht GitHub die Seite automatisch neu. Der Ablauf bricht ab, solange das Impressum Platzhalter enthält. So geht nichts versehentlich unvollständig online.

**Achtung bei Cloudflare:** Wenn du deine Domain über Cloudflare verwaltest, blockiert Cloudflare KI-Crawler bei neuen Domains standardmäßig. Für dein Ziel muss das unter „AI Crawl Control“ bzw. „Block AI bots“ ausgeschaltet sein.

## Der Optimierungs-Agent

Ein geplanter Claude-Task prüft die Website regelmäßig. Er baut und prüft die Seite, behebt technische Mängel, sucht nach neuen Publikationen und aktuellen Studien und legt Entwürfe für Forschungsnotizen an. Danach schreibt er einen kurzen Bericht nach `berichte/`. Inhalte in deinem Namen bleiben Entwürfe, bis du sie freigibst. Die Arbeitsanweisung steht in `AGENTS.md`.

## Technik in Kürze

Statische Website, gebaut mit Python (`build.py`, Jinja2, Markdown). Keine Datenbank, kein CMS, keine externen Dienste. Schriften: Instrument Serif und Instrument Sans (SIL Open Font License), lokal eingebunden. Erzeugt werden außerdem `sitemap.xml`, `robots.txt` (KI-Crawler ausdrücklich erlaubt), `llms.txt`, `llms-full.txt`, `feed.xml` sowie `publikationen.bib` und `publikationen.json`.
