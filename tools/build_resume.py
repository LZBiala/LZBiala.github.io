"""Rebuild Lito-Biala-Resume.pdf from its tracked HTML source.

The PDF on this site is a published artifact. Until now its source lived outside
version control, which is the one thing every lab in this portfolio has CI to prevent:
an artifact nobody can regenerate is an artifact nobody can check. The source is
Lito-Biala-Resume.html, tracked beside the PDF, and this script is how the two stay
in step.

Run: python tools/build_resume.py
Needs: Microsoft Edge (headless). Chrome works too if you point EDGE at it.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Lito-Biala-Resume.html"
OUT = ROOT / "Lito-Biala-Resume.pdf"

EDGE_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
]


def find_browser() -> Path:
    for p in EDGE_CANDIDATES:
        if p.exists():
            return p
    raise SystemExit("No Edge or Chrome found. Edit EDGE_CANDIDATES in this script.")


def main() -> int:
    if not SRC.exists():
        raise SystemExit(f"missing source: {SRC}")
    browser = find_browser()
    before = OUT.stat().st_mtime if OUT.exists() else 0

    # --headless=new prints; the older --dump-dom path is dead on this machine
    cmd = [
        str(browser),
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={OUT}",
        SRC.as_uri(),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if not OUT.exists() or OUT.stat().st_mtime == before:
        sys.stderr.write(r.stdout + r.stderr)
        raise SystemExit("PDF was not written")

    kb = OUT.stat().st_size / 1024
    pages = check_pages(OUT, expected=2)
    print(f"rebuilt {OUT.name} from {SRC.name} ({kb:.0f} KB, {pages} pages)")
    return 0


def check_pages(pdf, expected: int) -> int:
    """The two-page budget is a published claim, so it is a gate, not an eyeball.
    Requires pypdf (a build-time dependency of this script only; the site itself needs
    nothing). An adversarial QA on 2026-08-31 found no automated page-count gate at all."""
    from pypdf import PdfReader  # noqa: WPS433 - build-time only
    pages = len(PdfReader(str(pdf)).pages)
    if pages != expected:
        raise SystemExit(f"{pdf.name} is {pages} pages; the budget is {expected}. Cut before shipping.")
    return pages


if __name__ == "__main__":
    raise SystemExit(main())
