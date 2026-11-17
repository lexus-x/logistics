"""Build the competition report: report.md -> build/report.html -> PDF (Chromium) and -> DOCX (pandoc).
  .venv/bin/python -I competition/build.py          # after make_figs.py
  .venv/bin/python -I competition/build.py ko       # Korean edition: report_ko.md, figs/ko/ (make_figs.py ko), *_KO.pdf/.docx
Outputs go to ~/reports/LogisticSolver_2026/. Prints the PDF's page count (the limit is 20, cover included)."""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
BUILD, OUTDIR = HERE / "build", Path.home() / "reports/LogisticSolver_2026"
KO = sys.argv[1:] == ["ko"]
NAME = "ANALOG_LogisticSolver2026_Report" + ("_KO" if KO else "")
SRC, HTML = ("report_ko.md", "report_ko.html") if KO else ("report.md", "report.html")
PW = HERE.parent / ".bin"  # pw/ = Playwright PDF script, libs/ = browser libraries

BUILD.mkdir(exist_ok=True)
OUTDIR.mkdir(parents=True, exist_ok=True)
md = HERE / SRC

subprocess.run(["pandoc", str(md), "-f", "markdown", "-t", "html5", "--mathml", "--template", str(HERE / "template.html"),
                "--default-image-extension=svg", "--resource-path", str(HERE), "-o", str(BUILD / HTML)], check=True)
html = (BUILD / HTML).read_text()
html = html.replace('src="figs/', 'src="../figs/')
html = re.sub(r"<h2 id=\"summary\">", '<h2 id="summary">', html)
html = re.sub(r'<tr class="(odd|even)">(\s*<td[^>]*>(?:<strong>)?GNN (?:\+ optimizer|short list|\+ 최적화기|후보 목록))', r'<tr class="\1 ours">\2', html)  # our planner's row, soft tint
html = re.sub(r'(<figcaption[^>]*>)((?:Figure|그림) \d+\.)', r'\1<span class="lab">\2</span>', html)
if KO:
    html = html.replace('url("../figs/cover_bg.png")', 'url("../figs/ko/cover_bg.png")')
(BUILD / HTML).write_text(html)

pdf = OUTDIR / f"{NAME}.pdf"
env = dict(os.environ, LD_LIBRARY_PATH=str(PW / "libs/root/usr/lib/x86_64-linux-gnu"))
subprocess.run(["node", str(PW / "pw/pdf.mjs"), str(BUILD / HTML), str(pdf)], check=True, env=env, cwd=PW / "pw")
pages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))

subprocess.run(["pandoc", str(md), "-f", "markdown", "-t", "docx", "--default-image-extension=png", "--resource-path", str(HERE),
                "--reference-doc", str(HERE / "reference.docx"), "-o", str(OUTDIR / f"{NAME}.docx")], check=True)
shutil.copy(pdf, BUILD / pdf.name)
print(f"pdf {pdf} pages {pages}" + ("  OVER THE 20-PAGE LIMIT" if pages > 20 else ""))
print(f"docx {OUTDIR / (NAME + '.docx')}")
