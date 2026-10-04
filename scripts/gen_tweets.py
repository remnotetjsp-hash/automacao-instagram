#!/usr/bin/env python3
"""Gera tweets 1080x1080 no padrão X.com do @adv.leonardorezende.
Uso: python3 gen_tweets.py tweets.txt saida/   (tweets separados por uma linha '---')
"""
import sys, os, html, base64
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
AVATAR = "data:image/jpeg;base64," + base64.b64encode(open(os.path.join(HERE, "..", "assets", "avatar.jpg"), "rb").read()).decode()

TPL = """<!doctype html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1080px;background:#fff;overflow:hidden}
body{font-family:'Liberation Sans',Arial,Helvetica,sans-serif;color:#0f1419;position:relative}
.av{position:absolute;left:110px;top:105px;width:96px;height:96px;border-radius:50%;overflow:hidden}
.av img{width:96px;height:96px;display:block;object-fit:cover}
.name{position:absolute;left:230px;top:111px;font-size:30px;line-height:36px;font-weight:700;color:#0f1419;white-space:nowrap}
.handle{position:absolute;left:230px;top:153px;font-size:30px;line-height:36px;color:#6b7280;white-space:nowrap}
.x{position:absolute;right:110px;top:116px;font-size:45px;line-height:54px;font-weight:700;color:#0f1419}
.body{position:absolute;left:110px;top:269px;width:860px;font-size:42px;line-height:59.5px;white-space:pre-wrap;color:#0f1419}
</style></head><body>
<div class="av"><img src="{{AV}}"></div>
<div class="name">Leonardo Rezende</div><div class="handle">@adv.leonardorezende</div>
<div class="x">X.com</div>
<div class="body" id="b">{{TXT}}</div>
</body></html>"""

def main(src, outdir, prefix="tweet"):
    os.makedirs(outdir, exist_ok=True)
    items = [t.strip("\n") for t in open(src, encoding="utf-8").read().split("\n---\n") if t.strip()]
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width":1080,"height":1080})
        for i, t in enumerate(items, 1):
            pg.set_content(TPL.replace("{{AV}}", AVATAR).replace("{{TXT}}", html.escape(t.strip())))
            pg.wait_for_timeout(50)
            bottom = pg.evaluate("(()=>{const e=document.getElementById('b');return e.getBoundingClientRect().bottom})()")
            if bottom > 1030: print(f"AVISO: tweet {i} estoura a área ({bottom:.0f}px)")
            pg.screenshot(path=os.path.join(outdir, f"{prefix}_{i:03d}.png"))
        b.close()
    print(f"{len(items)} tweets em {outdir}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], *(sys.argv[3:4]))
