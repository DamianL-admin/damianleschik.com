---
title: Datenschutzerklärung
description: Datenschutzerklärung der Website von Prof. Dr. Damian Leschik – welche Daten beim Besuch anfallen, wofür sie genutzt werden und welche Rechte Sie haben.
---
{% set ga = site.analytics and site.analytics.ga4_id %}
## 1. Verantwortlicher

{{ site.impressum.name }}, Anschrift siehe [Impressum]({{ imprint_url }}), E-Mail: [{{ site.impressum.email }}](mailto:{{ site.impressum.email }})

## 2. Das Wichtigste in Kürze
{% if ga %}
Diese Website setzt Cookies und ein Analysewerkzeug **nur mit Ihrer Einwilligung** ein: Wenn Sie zustimmen, nutze ich Google Analytics 4 für eine Besucherstatistik (Punkt 5). Ohne Ihre Zustimmung wird Google Analytics nicht geladen. Schriften, Bilder und alle anderen Dateien werden direkt von dieser Website geladen. Weitere Inhalte von Drittanbietern sind nicht eingebunden, also zum Beispiel weder Google Fonts noch Videos oder Social-Media-Plugins.
{% else %}
Diese Website verwendet **keine Cookies**, **kein Tracking** und **keine Analysewerkzeuge**. Schriften, Bilder und alle anderen Dateien werden direkt von dieser Website geladen. Es werden keine Inhalte von Drittanbietern eingebunden, also zum Beispiel weder Google Fonts noch Videos oder Social-Media-Plugins.
{% endif %}
## 3. Hosting und Server-Logdateien

Die Website wird bei {{ site.hosting.provider }} gehostet ({{ site.hosting.address }}). Beim Aufruf der Seiten verarbeitet der Hoster technisch notwendige Daten, insbesondere IP-Adresse, Datum und Uhrzeit des Abrufs, die aufgerufene Seite sowie Browsertyp und Betriebssystem. Diese Daten sind nötig, um die Website sicher und stabil auszuliefern. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO; das berechtigte Interesse liegt im sicheren Betrieb der Website.
{% if site.hosting.outside_eu %}
Der Hoster hat seinen Sitz in den USA. Die Übermittlung personenbezogener Daten in die USA stützt sich auf den Angemessenheitsbeschluss der EU-Kommission zum EU-U.S. Data Privacy Framework (Art. 45 DSGVO) sowie ergänzend auf Standardvertragsklauseln (Art. 46 DSGVO).
{% endif %}
Weitere Informationen: [Datenschutzhinweise des Hosters]({{ site.hosting.privacy_url }})

## 4. Kontakt per E-Mail

Wenn Sie mir eine E-Mail schreiben, verarbeite ich Ihre Angaben, um Ihre Anfrage zu beantworten. Rechtsgrundlage ist Art. 6 Abs. 1 lit. b DSGVO, wenn es um einen Vertrag oder dessen Anbahnung geht, sonst Art. 6 Abs. 1 lit. f DSGVO (Interesse an der Beantwortung von Anfragen). Die Daten werden gelöscht, sobald sie nicht mehr benötigt werden und keine gesetzlichen Aufbewahrungspflichten bestehen.

{% if ga %}
## 5. Besucherstatistik mit Google Analytics 4

Wenn Sie zustimmen, nutze ich Google Analytics 4, einen Dienst der Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irland („Google“). Damit sehe ich zum Beispiel, wie viele Menschen die Website besuchen, welche Seiten sie aufrufen, über welche Wege sie kommen (etwa über eine Suchmaschine oder einen Link) und mit welchem Gerätetyp. Das hilft mir, die Inhalte zu verbessern.

**Welche Daten:** Google Analytics speichert Cookies auf Ihrem Gerät (`_ga` und `_ga_…`), die eine zufällige Kennung enthalten. Verarbeitet werden unter anderem aufgerufene Seiten, Datum und Uhrzeit, Verweisquelle, ungefährer Standort (Land, Region), Browser, Betriebssystem, Bildschirmgröße und Spracheinstellung. Nach Angaben von Google werden IP-Adressen von Nutzern aus der EU nur zur Bestimmung des ungefähren Standorts verwendet und danach verworfen, also nicht gespeichert.

**Einstellungen:** Google Signals und Werbefunktionen sind ausgeschaltet. Die Cookies laufen nach 13 Monaten ab. Die Ereignisdaten werden in Google Analytics nach {{ site.analytics.retention_months }} Monaten gelöscht.

**Rechtsgrundlage:** Ihre Einwilligung nach § 25 Abs. 1 TDDDG (Speichern und Auslesen von Informationen auf Ihrem Gerät) und Art. 6 Abs. 1 lit. a DSGVO (Verarbeitung der Daten).

**Widerruf:** Sie können Ihre Einwilligung jederzeit mit Wirkung für die Zukunft widerrufen, über „Cookie-Einstellungen“ unten auf jeder Seite. Dabei werden die Cookies von Google Analytics gelöscht.

**Speicherung Ihrer Auswahl:** Damit das Banner nicht bei jedem Seitenaufruf erscheint, speichert die Website Ihre Entscheidung im lokalen Speicher Ihres Browsers (localStorage). Das ist dafür unbedingt erforderlich (§ 25 Abs. 2 Nr. 2 TDDDG). Nach zwölf Monaten fragt die Website erneut.

**Auftragsverarbeitung und Übermittlung in die USA:** Google verarbeitet die Daten in meinem Auftrag (Art. 28 DSGVO); dafür gelten die Datenverarbeitungsbedingungen von Google. Daten können an die Google LLC in den USA übermittelt werden. Grundlage ist der Angemessenheitsbeschluss der EU-Kommission zum EU-U.S. Data Privacy Framework (Art. 45 DSGVO), unter dem die Google LLC zertifiziert ist, ergänzend Standardvertragsklauseln (Art. 46 DSGVO).

Weitere Informationen: [Datenschutzerklärung von Google](https://policies.google.com/privacy?hl=de)
{% endif %}
## {{ 6 if ga else 5 }}. Downloads und externe Links

Beim Herunterladen der Comic-PDFs fallen nur die unter Punkt 3 genannten Server-Logdaten an. Links zu anderen Websites, zum Beispiel zu Verlagen oder Profilen, werden erst beim Anklicken aufgerufen. Danach gelten die Datenschutzhinweise des jeweiligen Anbieters.

## {{ 7 if ga else 6 }}. Ihre Rechte

Sie haben das Recht auf Auskunft (Art. 15 DSGVO), Berichtigung (Art. 16 DSGVO), Löschung (Art. 17 DSGVO), Einschränkung der Verarbeitung (Art. 18 DSGVO), Datenübertragbarkeit (Art. 20 DSGVO) und Widerspruch (Art. 21 DSGVO). Außerdem können Sie sich bei einer Datenschutz-Aufsichtsbehörde beschweren, zum Beispiel bei der Landesbeauftragten für Datenschutz und Informationsfreiheit Nordrhein-Westfalen.

Stand: {{ today_month }}
