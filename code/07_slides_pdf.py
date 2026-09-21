#!/usr/bin/env python3
"""07_slides_pdf.py — render the slide files to a standalone PDF (slides/Retailer_Churn_slides.pdf).

The Slides deck in Claude is the version to present from. This PDF is the portable copy for the
repository: figures are embedded from paper/figures/, so it opens anywhere.
Usage: python code/07_slides_pdf.py [--final]   (run 06_slides.py with the same flag first)
"""
import base64, json, pathlib, sys
from playwright.sync_api import sync_playwright

FINAL = "--final" in sys.argv
ROOT = pathlib.Path(__file__).resolve().parents[1]
deck = json.loads((ROOT / "slides/project/deck.json").read_text())
assets = json.loads((ROOT / "slides/assets.json").read_text())
figfile = {"fig1": "fig1_exit_definitions.png", "fig2": "fig2_store_type.png", "fig3": "fig3_poverty_gradient.png",
           "fig4": "fig4_store_mix.png", "fig5": "fig5_tennessee_region.png"}
css = """
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400..700&family=IBM+Plex+Sans:wght@400;600&display=swap');
* { box-sizing: border-box; margin: 0; }
@page { size: 1920px 1080px; margin: 0; }
body { margin: 0; }
section { width: 1920px; height: 1080px; position: relative; overflow: hidden; page-break-after: always; }
section aside { display: none; }
ul { padding-left: 1.1em; } li { margin-bottom: 0.35em; }
table { border-collapse: collapse; width: 100%; }
th, td { padding: 0.35em 0.6em; border-bottom: 1px solid #DCE1E7; }
th { border-bottom: 2px solid #9AA5B4; font-weight: 600; }
"""
html = ""
for sid in deck["order"]:
    s = (ROOT / f"slides/project/slides/{sid}.html").read_text()
    for k, url in assets.items():
        b64 = base64.b64encode((ROOT / "paper/figures" / figfile[k]).read_bytes()).decode()
        s = s.replace(f'src="{url}"', f'src="data:image/png;base64,{b64}"')
    html += s
page = f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{html}</body></html>"
out_html = ROOT / "slides/_render.html"
out_html.write_text(page)
out = ROOT / "slides" / ("Retailer_Churn_Food_Access_slides.pdf" if FINAL else "Retailer_Churn_Food_Access_slides_DRAFT.pdf")
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    pg.goto(out_html.as_uri()); pg.wait_for_timeout(1500)
    # overflow report: any element whose bottom passes y=1000 (footer zone) other than footers
    rep = pg.evaluate("""() => [...document.querySelectorAll('section')].map((s,i) => {
        const top = s.getBoundingClientRect().top; let worst = 0;
        s.querySelectorAll('h1,h2,h3,p,li,td,img,div').forEach(e => { if (getComputedStyle(e).position==='absolute') return;
            const r = e.getBoundingClientRect(); worst = Math.max(worst, r.bottom - top); });
        return [i+1, s.id, Math.round(worst)]; })""")
    pg.pdf(path=str(out), width="1920px", height="1080px", print_background=True)
    b.close()
out_html.unlink()
print("wrote", out.name)
for r in rep:
    print(r, "OVERFLOW" if r[2] > 935 else "")
