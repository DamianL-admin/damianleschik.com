#!/usr/bin/env python3
"""
Erzeugt die Vorschaubilder für soziale Medien (1200 × 630 px):
static/assets/img/og-image.png (Deutsch) und og-image-en.png (Englisch).
Liegt ein Porträt unter static/assets/img/portrait.jpg, wird es verwendet.

    python3 tools/og_image.py

Benötigt Playwright mit Chromium:  pip install playwright && playwright install chromium
(Alternativ: --chrome /pfad/zu/chrome für eine vorhandene Chrome-Installation.)
"""
import argparse
import asyncio
import base64
import html
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402
from build import read_md  # noqa: E402

try:
    from playwright.async_api import async_playwright
except ImportError:  # pragma: no cover
    sys.exit("Bitte zuerst installieren: pip install playwright && playwright install chromium")

FONTS = (ROOT / "static/assets/fonts").as_uri() + "/"
IMG = ROOT / "static/assets/img"


def page_html(lang: str, site: dict) -> str:
    meta, _ = read_md(ROOT / "content/profil.{}.md".format(lang))
    claim = "<br>".join(html.escape(line) for line in meta.get("claim", "").split("\n"))
    role = "{}, {}".format(site["job_title"][lang], site["affiliation"]["name"] if lang == "de" else site["affiliation"]["name_en"])
    portrait = IMG / "portrait.jpg"
    if portrait.exists():
        data = base64.b64encode(portrait.read_bytes()).decode()
        circle = '<img class="circle" src="data:image/jpeg;base64,{}" alt="">'.format(data)
    else:
        circle = '<div class="circle">DL</div>'
    host = site["url"].split("://", 1)[-1].rstrip("/")
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:IS;src:url('{f}instrument-serif-latin-400-normal.woff2')}}
@font-face{{font-family:ISans;src:url('{f}instrument-sans-latin-wght-normal.woff2');font-weight:400 700}}
html,body{{margin:0;width:1200px;height:630px;background:#ECEBE6;overflow:hidden}}
.wrap{{position:relative;width:1200px;height:630px;display:grid;grid-template-columns:440px 1fr;align-items:center}}
.glow{{position:absolute;inset:0;background:
 radial-gradient(30% 42% at 12% 82%,rgba(201,228,166,.9),transparent 72%),
 radial-gradient(26% 40% at 34% 22%,rgba(143,205,226,.75),transparent 72%),
 radial-gradient(30% 46% at 24% 55%,rgba(151,214,205,.7),transparent 74%),
 radial-gradient(24% 34% at 90% 96%,rgba(240,216,182,.8),transparent 72%)}}
.vis{{position:relative;display:grid;place-items:center;margin-left:70px}}
.circle{{width:300px;height:300px;border-radius:50%;object-fit:cover;background:radial-gradient(circle at 34% 28%,#2E7C84,#0E4C59 58%,#0A3640);display:grid;place-items:center;color:#EEF4F1;font:100px IS;box-shadow:0 0 0 8px rgba(255,255,255,.35),0 30px 70px -30px rgba(10,54,64,.6)}}
.txt{{position:relative;z-index:2;padding-right:70px}}
.name{{font:600 22px ISans;letter-spacing:.16em;text-transform:uppercase;color:#141918;margin:0 0 18px}}
.claim{{font:66px/1.02 IS;color:#0E4C59;margin:0 0 26px;letter-spacing:-.01em}}
.role{{font:400 24px/1.4 ISans;color:#4C5553;margin:0}}
.url{{position:absolute;right:70px;bottom:42px;font:600 18px ISans;letter-spacing:.14em;text-transform:uppercase;color:#0E4C59}}
</style></head><body><div class="wrap"><div class="glow"></div><div class="vis">{circle}</div>
<div class="txt"><p class="name">{hon} {name}</p><p class="claim">{claim}</p><p class="role">{role}</p></div>
<div class="url">{host}</div></div></body></html>""".format(
        f=FONTS, circle=circle, hon=site["honorific"], name=site["name"],
        claim=claim, role=role, host=host)


async def render(chrome):
    site = yaml.safe_load((ROOT / "site.yaml").read_text(encoding="utf-8"))
    async with async_playwright() as p:
        launch = {"args": ["--allow-file-access-from-files"]}
        if chrome:
            launch["executable_path"] = chrome
        browser = await p.chromium.launch(**launch)
        page = await browser.new_page(viewport={"width": 1200, "height": 630})
        workdir = Path(tempfile.mkdtemp(prefix="og_"))  # außerhalb des Projekts
        for lang, name in (("de", "og-image.png"), ("en", "og-image-en.png")):
            tmp = workdir / "og_{}.html".format(lang)
            tmp.write_text(page_html(lang, site), encoding="utf-8")
            await page.goto(tmp.as_uri())
            await page.wait_for_timeout(500)
            await page.screenshot(path=str(IMG / name))
            print("Gespeichert: static/assets/img/" + name)
        await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vorschaubilder erzeugen")
    parser.add_argument("--chrome", help="Pfad zu einer vorhandenen Chrome/Chromium-Installation")
    asyncio.run(render(parser.parse_args().chrome))
