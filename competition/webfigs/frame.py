"""Frame the prototype screenshots as a browser window: figs/slides/app_top.png (slide 13) and figs/proto_app.png (report).
  .venv/bin/python -I competition/webfigs/frame.py   (after render.mjs)"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).parent
FIGS = HERE.parent / "figs"


def frame(img, bar=64, pad=60, r=24):
    w, h = img.size
    win = Image.new("RGBA", (w, h + bar), (0, 0, 0, 0)); d = ImageDraw.Draw(win)
    d.rounded_rectangle((0, 0, w - 1, h + bar - 1), r, fill="#e9ecf2")
    for i, c in enumerate(["#ec6a5e", "#f4bf4f", "#61c554"]): d.ellipse((28 + i * 40, bar / 2 - 11, 50 + i * 40, bar / 2 + 11), fill=c)
    d.rounded_rectangle((180, 14, min(w - 40, 1100), bar - 14), 14, fill="#ffffff")
    d.text((204, bar / 2 - 12), "delivery-plan  |  Version 1 results", fill="#6b7385", font_size=26)
    win.paste(img, (0, bar))
    mask = Image.new("L", win.size, 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h + bar - 1), r, fill=255)
    win.putalpha(mask)
    out = Image.new("RGBA", (w + 2 * pad, h + bar + 2 * pad), (255, 255, 255, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 10, pad + w, pad + 10 + h + bar), r, fill=(16, 26, 51, 70))
    out = Image.alpha_composite(out, sh.filter(ImageFilter.GaussianBlur(22)))
    out.alpha_composite(win, (pad, pad))
    bg = Image.new("RGB", out.size, "white"); bg.paste(out, mask=out.split()[3]); return bg


head, per = Image.open(HERE / "raw_header.png").convert("RGB"), Image.open(HERE / "raw_perjob.png").convert("RGB")
frame(head).save(FIGS / "slides/app_top.png", optimize=True)
gap = 40                                              # the report figure: the page's header and, below it, its per-job card
page = Image.new("RGB", (head.width, head.height + gap + per.height + gap), "#f4f6fb")
page.paste(head, (0, 0)); page.paste(per, ((head.width - per.width) // 2, head.height + gap))
frame(page).save(FIGS / "proto_app.png", optimize=True)
print("framed", head.size, per.size)
