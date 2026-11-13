"""Build the competition report: report.md -> build/report.html -> PDF (Chromium) and -> DOCX (pandoc).
  .venv/bin/python -I competition/build.py          # after make_figs.py
Outputs go to ~/reports/LogisticSolver_2026/. Prints the PDF's page count (the limit is 20, cover included)."""
import os
import re
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
BUILD, OUTDIR = HERE / "build", Path.home() / "reports/LogisticSolver_2026"
NAME = "ANALOG_LogisticSolver2026_Report"
# shortcut: Playwright and its browser libraries live in this session's scratchpad; move them into the project if the build must outlive it
PW = Path("/tmp/claude-1000/-home-ubuntu/19ed5409-849c-4a99-a86a-fd99a7dd07f6/scratchpad")

BUILD.mkdir(exist_ok=True)
OUTDIR.mkdir(parents=True, exist_ok=True)
md = HERE / "report.md"

subprocess.run(["pandoc", str(md), "-f", "markdown", "-t", "html5", "--mathml", "--template", str(HERE / "template.html"),
                "--default-image-extension=svg", "--resource-path", str(HERE), "-o", str(BUILD / "report.html")], check=True)
html = (BUILD / "report.html").read_text()
html = html.replace('src="figs/', 'src="../figs/')
html = re.sub(r"<h2 id=\"summary\">", '<h2 id="summary">', html)
html = re.sub(r'<tr class="(odd|even)">(\s*<td[^>]*>(?:<strong>)?GNN (?:\+ optimizer|short list))', r'<tr class="\1 ours">\2', html)  # our planner's row, soft tint
html = re.sub(r'(<figcaption[^>]*>)(Figure \d+\.)', r'\1<span class="lab">\2</span>', html)
(BUILD / "report.html").write_text(html)

pdf = OUTDIR / f"{NAME}.pdf"
env = dict(os.environ, LD_LIBRARY_PATH=str(PW / "libs/root/usr/lib/x86_64-linux-gnu"))
subprocess.run(["node", str(PW / "pw/pdf.mjs"), str(BUILD / "report.html"), str(pdf)], check=True, env=env, cwd=PW / "pw")
pages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))

subprocess.run(["pandoc", str(md), "-f", "markdown", "-t", "docx", "--default-image-extension=png", "--resource-path", str(HERE),
                "--reference-doc", str(HERE / "reference.docx"), "-o", str(OUTDIR / f"{NAME}.docx")], check=True)
shutil.copy(pdf, BUILD / pdf.name)
print(f"pdf {pdf} pages {pages}" + ("  OVER THE 20-PAGE LIMIT" if pages > 20 else ""))
print(f"docx {OUTDIR / (NAME + '.docx')}")
