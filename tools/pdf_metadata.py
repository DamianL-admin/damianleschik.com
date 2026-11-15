#!/usr/bin/env python3
"""
Setzt Titel, Autor, Thema und Schlagwörter in einer PDF-Datei (z. B. für die Comics).
Suchmaschinen zeigen diese Angaben in Ergebnissen an; KI-Systeme ordnen das PDF so besser zu.

    python3 tools/pdf_metadata.py static/downloads/comic-1.pdf \
        --title "Titel des Comics" --subject "Worum es geht" --keywords "Silicon Sampling, Marktforschung"

Benötigt: pip install pypdf
"""
import argparse
import io
import sys
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:  # pragma: no cover
    sys.exit("Bitte zuerst installieren: pip install pypdf")


def main():
    parser = argparse.ArgumentParser(description="PDF-Metadaten setzen")
    parser.add_argument("pdf", help="Pfad zur PDF-Datei")
    parser.add_argument("--title", required=True)
    parser.add_argument("--subject", default="")
    parser.add_argument("--keywords", default="")
    parser.add_argument("--author", default="Damian Leschik")
    args = parser.parse_args()

    path = Path(args.pdf)
    # Erst komplett in den Speicher lesen, dann dieselbe Datei überschreiben
    # (ohne Umbenennen oder Löschen, das ist in geschützten Ordnern nicht erlaubt).
    reader = PdfReader(io.BytesIO(path.read_bytes()))
    writer = PdfWriter()
    writer.append(reader)
    writer.add_metadata({"/Title": args.title, "/Author": args.author, "/Subject": args.subject,
                         "/Keywords": args.keywords, "/Creator": "damianleschik.com"})
    buffer = io.BytesIO()
    writer.write(buffer)
    path.write_bytes(buffer.getvalue())
    print("Metadaten gesetzt: {} ({} Seiten)".format(path, len(reader.pages)))


if __name__ == "__main__":
    main()
