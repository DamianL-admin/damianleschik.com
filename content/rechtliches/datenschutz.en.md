---
title: Privacy policy
description: Privacy policy for the website of Prof. Dr. Damian Leschik – which data are processed when you visit, for what purpose, and which rights you have.
---
{% set ga = site.analytics and site.analytics.ga4_id %}
*This is a translation for convenience. The [German version]({{ other_url }}) is legally binding.*

## 1. Controller

{{ site.impressum.name }}, address see [legal notice]({{ imprint_url }}), email: [{{ site.impressum.email }}](mailto:{{ site.impressum.email }})

## 2. In short

{% if ga %}
This website uses cookies and an analytics tool **only with your consent**: if you agree, I use Google Analytics 4 for visitor statistics (section 5). Without your consent, Google Analytics is not loaded. Fonts, images and all other files are served directly by this website. No other third-party content is embedded, for example no Google Fonts, videos or social media plugins.
{% else %}
This website uses **no cookies**, **no tracking** and **no analytics tools**. Fonts, images and all other files are served directly by this website. No third-party content is embedded, for example no Google Fonts, videos or social media plugins.
{% endif %}
## 3. Hosting and server log files

The website is hosted by {{ site.hosting.provider }} ({{ site.hosting.address }}). When pages are requested, the host processes technically necessary data, in particular the IP address, date and time of the request, the requested page, browser type and operating system. This is required to deliver the website securely and reliably. The legal basis is Art. 6(1)(f) GDPR (legitimate interest in secure operation).
{% if site.hosting.outside_eu %}
The host is based in the USA. Transfers of personal data to the USA rely on the European Commission's adequacy decision for the EU-U.S. Data Privacy Framework (Art. 45 GDPR) and, in addition, on standard contractual clauses (Art. 46 GDPR).
{% endif %}
More information: [host's privacy statement]({{ site.hosting.privacy_url }})

## 4. Contact by email

If you send me an email, I process your details to answer your request (Art. 6(1)(b) GDPR where a contract is concerned, otherwise Art. 6(1)(f) GDPR). The data are deleted once they are no longer needed and no statutory retention obligations apply.

{% if ga %}
## 5. Visitor statistics with Google Analytics 4

If you consent, I use Google Analytics 4, a service of Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Ireland ("Google"). It shows me, for example, how many people visit the website, which pages they view, how they arrive (such as via a search engine or a link) and which type of device they use. This helps me improve the content.

**Which data:** Google Analytics stores cookies on your device (`_ga` and `_ga_…`) that contain a random identifier. Processed data include the pages viewed, date and time, referring source, approximate location (country, region), browser, operating system, screen size and language setting. According to Google, IP addresses of users in the EU are only used to derive the approximate location and are then discarded, i.e. not stored.

**Settings:** Google Signals and advertising features are switched off. The cookies expire after 13 months. Event data are deleted in Google Analytics after {{ site.analytics.retention_months }} months.

**Legal basis:** your consent under Section 25(1) TDDDG (storing and reading information on your device) and Art. 6(1)(a) GDPR (processing of the data).

**Withdrawal:** you can withdraw your consent at any time with effect for the future via "Cookie settings" at the bottom of every page. The Google Analytics cookies are then deleted.

**Storing your choice:** so that the banner does not appear on every page, the website stores your decision in your browser's local storage (localStorage). This is strictly necessary for that purpose (Section 25(2) no. 2 TDDDG). After twelve months the website asks again.

**Processing on my behalf and transfers to the USA:** Google processes the data on my behalf (Art. 28 GDPR) under Google's data processing terms. Data may be transferred to Google LLC in the USA. This relies on the European Commission's adequacy decision for the EU-U.S. Data Privacy Framework (Art. 45 GDPR), under which Google LLC is certified, and in addition on standard contractual clauses (Art. 46 GDPR).

More information: [Google privacy policy](https://policies.google.com/privacy?hl=en)
{% endif %}
## {{ 6 if ga else 5 }}. Downloads and external links

Downloading the comic PDFs only generates the server log data described in section 3. Links to other websites, for example publishers or profiles, are only requested when you click them. The privacy policy of the respective provider then applies.

## {{ 7 if ga else 6 }}. Your rights

You have the right of access (Art. 15 GDPR), rectification (Art. 16), erasure (Art. 17), restriction of processing (Art. 18), data portability (Art. 20) and to object (Art. 21 GDPR). You may also lodge a complaint with a data protection supervisory authority, for example the State Commissioner for Data Protection and Freedom of Information of North Rhine-Westphalia.

Last updated: {{ today_month }}
