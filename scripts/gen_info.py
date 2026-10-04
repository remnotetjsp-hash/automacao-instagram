#!/usr/bin/env python3
"""Gera posts informativos 1080x1350 (escuro + vermelho) do @adv.leonardorezende.
Uso: python3 gen_info.py posts.json saida/   (lista de objetos com campo 'layout')
Layouts: tese | sumula | chat | planilha | antes_depois | pergunta
Marcação: *palavra* vira destaque vermelho.
"""
import sys, os, re, json, html, base64, random

HERE = os.path.dirname(os.path.abspath(__file__))
AV = "data:image/jpeg;base64," + base64.b64encode(open(os.path.join(HERE, "..", "assets", "avatar.jpg"), "rb").read()).decode()
NAME, HANDLE = "Leonardo Rezende", "@adv.leonardorezende"

def esc(t): return html.escape(t)
def em(t): return re.sub(r"\*(.+?)\*", r"<em>\1</em>", esc(t))

CSS = """
@font-face{font-family:'PF';src:url('../assets/fonts/playfair-display-latin-700-normal.woff2');font-weight:700;font-style:normal}
@font-face{font-family:'PF';src:url('../assets/fonts/playfair-display-latin-700-italic.woff2');font-weight:700;font-style:italic}
@font-face{font-family:'PF';src:url('../assets/fonts/playfair-display-latin-500-normal.woff2');font-weight:500;font-style:normal}
@font-face{font-family:'PF';src:url('../assets/fonts/playfair-display-latin-500-italic.woff2');font-weight:500;font-style:italic}
@font-face{font-family:'AN';src:url('../assets/fonts/anton-latin-400-normal.woff2')}
:root{--red:#d7192b;--bg:#09090a}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1350px;overflow:hidden;background:var(--bg)}
body{font-family:'Poppins',sans-serif;color:#fff;position:relative}
.abs{position:absolute}
.foot{position:absolute;left:80px;bottom:78px;display:flex;align-items:center;gap:20px}
.foot.c{left:0;right:0;justify-content:center}
.foot img,.hd img{width:64px;height:64px;border-radius:50%;object-fit:cover}
.foot .n,.hd .n{font-weight:600;font-size:26px;line-height:30px}
.foot .h,.hd .h{font-weight:400;font-size:22px;line-height:28px;color:#8b8b90}
.pill{position:absolute;left:80px;top:76px;background:var(--red);color:#fff;font-weight:600;font-size:20px;letter-spacing:.2em;padding:14px 26px;border-radius:40px}
"""

def foot(c=False):
    return f'<div class="foot{" c" if c else ""}"><img src="{AV}"><div><div class="n">{NAME}</div><div class="h">{HANDLE}</div></div></div>'

def L_tese(d):
    return f"""<style>
body{{background:radial-gradient(900px 700px at 100% 100%,rgba(120,12,22,.75),transparent 70%),#09090a}}
.k{{position:absolute;left:80px;top:114px;font-weight:500;font-size:25px;letter-spacing:.2em;color:var(--red);border-left:7px solid var(--red);padding-left:20px;line-height:38px;text-transform:uppercase}}
.num{{position:absolute;right:50px;top:150px;font-family:'PF';font-style:italic;font-weight:700;font-size:230px;line-height:1;color:#3b0b12}}
.t{{position:absolute;left:80px;top:430px;width:930px;font-family:'PF';font-weight:700;font-size:88px;line-height:1.12;color:#f4f4f4}}
.t em{{color:var(--red);font-style:italic}}
.rule{{position:absolute;left:80px;width:130px;height:7px;background:var(--red)}}
.b{{position:absolute;left:80px;width:860px;font-weight:300;font-size:39px;line-height:58px;color:#d9d9db}}
</style>
{('<div class="k">'+esc(d['kicker'])+'</div>') if d.get('kicker') else ''}<div class="num">{esc(d.get('num',''))}</div>
<div class="t" id="t">{em(d['titulo'])}</div><div class="rule" id="r"></div><div class="b" id="b">{esc(d['corpo'])}</div>{foot()}
<script>
const t=document.getElementById('t'),r=document.getElementById('r'),b=document.getElementById('b');
const tb=t.getBoundingClientRect().bottom; r.style.top=(tb+40)+'px'; b.style.top=(tb+82)+'px';
</script>"""

def L_sumula(d):
    rings = "".join(f'<div class="abs" style="left:{540-r}px;top:{450-r}px;width:{2*r}px;height:{2*r}px;border-radius:50%;border:2px solid rgba(215,25,43,{a})"></div>' for r,a in [(150,.55),(235,.3),(330,.2),(440,.13),(560,.08),(700,.05)])
    return f"""<style>
body{{background:radial-gradient(520px 520px at 540px 450px,rgba(110,10,20,.55),transparent 70%),#09090a}}
.k{{position:absolute;left:0;right:0;top:196px;text-align:center;font-weight:500;font-size:22px;letter-spacing:.26em;color:var(--red);text-transform:uppercase}}
.num{{position:absolute;left:0;right:0;top:280px;text-align:center;font-family:'AN';font-size:320px;line-height:1;color:var(--red);text-shadow:0 0 40px rgba(215,25,43,.35)}}
.rf{{position:absolute;left:0;right:0;top:812px;text-align:center;font-weight:500;font-size:22px;letter-spacing:.24em;color:var(--red);text-transform:uppercase}}
.b{{position:absolute;left:140px;width:800px;top:862px;text-align:center;font-weight:300;font-size:35px;line-height:54px;color:#e4e4e6}}
</style>{rings}
<div class="num">{esc(d['numero'])}</div>{('<div class="rf">'+esc(d['ref'])+'</div>') if d.get('ref') else ''}<div class="b">{esc(d['corpo'])}</div>{foot(True)}"""

def L_chat(d):
    msgs = "".join(f'<div class="m {"q" if m[0]=="q" else "a"}">{esc(m[1])}</div>' for m in d["msgs"])
    return f"""<style>
.hd{{position:absolute;left:0;right:0;top:0;height:170px;background:#101012;border-bottom:1px solid #1d1d20;display:flex;align-items:center;gap:22px;padding:0 60px}}
.hd img{{width:76px;height:76px}} .hd .n{{font-size:32px;line-height:38px}} .hd .h{{font-size:24px}}
.list{{position:absolute;left:60px;right:60px;top:215px;display:flex;flex-direction:column;gap:30px}}
.m{{font-size:32px;line-height:46px;padding:28px 36px;border-radius:34px;max-width:790px;font-weight:400}}
.q{{background:#2a2a2e;color:#f1f1f2;align-self:flex-start;border-bottom-left-radius:10px}}
.a{{background:var(--red);color:#fff;align-self:flex-end;border-bottom-right-radius:10px}}
.in{{position:absolute;left:60px;right:60px;bottom:78px;height:90px;border-radius:45px;background:#1a1a1d;display:flex;align-items:center;justify-content:space-between;padding:0 24px 0 36px;color:#6d6d73;font-size:28px}}
.in i{{width:50px;height:50px;border-radius:50%;background:var(--red);display:block}}
</style>
<div class="hd"><img src="{AV}"><div><div class="n">{NAME}</div><div class="h">{HANDLE}</div></div></div>
<div class="list">{msgs}</div><div class="in">Mensagem<i></i></div>"""

def L_planilha(d, seed=1):
    rnd = random.Random(seed)
    cols = "ABCDE"; cw = (1080-70)//5
    head = "".join(f'<div class="abs hc" style="left:{70+i*cw}px;width:{cw}px">{c}</div>' for i,c in enumerate(cols))
    cells = ""
    red_col = d.get("coluna", 2)
    for r in range(6):
        y = 70 + r*104
        cells += f'<div class="abs rn" style="top:{y}px;height:104px">{r+1}</div><div class="abs rl" style="top:{y}px"></div>'
        for c in range(5):
            x = 70 + c*cw
            if r == 3 and c == red_col:
                cells += f'<div class="abs rc" style="left:{x}px;top:{y}px;width:{cw}px;height:104px">{esc(d["simbolo"])}</div>'
            elif rnd.random() < .72:
                w = rnd.randint(50, cw-90)
                cells += f'<div class="abs bar" style="left:{x+20}px;top:{y+47}px;width:{w}px"></div>'
    vl = "".join(f'<div class="abs vl" style="left:{70+i*cw}px"></div>' for i in range(6))
    return f"""<style>
.hc{{top:14px;height:56px;text-align:center;line-height:56px;font-size:20px;color:#55555a;background:#0f0f11}}
.rn{{left:0;width:70px;text-align:center;line-height:104px;font-size:20px;color:#55555a}}
.rl{{left:0;right:0;height:1px;background:#1c1c1f}} .vl{{top:70px;height:660px;width:1px;background:#1c1c1f}}
.bar{{height:12px;border-radius:6px;background:#3a3a3e}}
.rc{{background:var(--red);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:44px}}
.fade{{position:absolute;left:0;right:0;top:420px;height:330px;background:linear-gradient(transparent,#09090a)}}
.t{{position:absolute;left:80px;top:760px;width:920px;font-weight:700;font-size:62px;line-height:80px}}
.t em{{font-style:normal;color:var(--red)}}
.b{{position:absolute;left:80px;width:860px;font-weight:300;font-size:30px;line-height:46px;color:#bdbdc1}}
</style>{vl}{head}{cells}<div class="fade"></div>
<div class="t" id="t">{em(d['titulo'])}</div><div class="b" id="b">{esc(d['corpo'])}</div>{foot()}
<script>const t=document.getElementById('t'),b=document.getElementById('b');b.style.top=(t.getBoundingClientRect().bottom+28)+'px';</script>"""

def L_antes_depois(d):
    return f"""<style>
body{{background:#09090a}}
.red{{position:absolute;left:540px;right:0;top:0;bottom:0;background:linear-gradient(180deg,#e0202f 0%,#a5121e 55%,#6a0c14 100%)}}
.tt{{position:absolute;left:80px;right:60px;top:300px;font-family:'PF';font-weight:500;font-size:62px;line-height:1.15;white-space:nowrap}}
.line{{position:absolute;left:539px;top:620px;width:2px;height:580px;background:#fff}}
.hdl{{position:absolute;left:497px;top:565px;width:86px;height:86px;border-radius:50%;background:#fff;color:#09090a;display:flex;align-items:center;justify-content:center}}
.lab{{position:absolute;top:790px;font-family:'AN';font-size:104px;line-height:1;letter-spacing:.01em}}
.tx{{position:absolute;top:930px;width:400px;font-size:30px;line-height:46px;font-weight:400}}
.tx.l{{left:80px;color:#c9c9cc}} .tx.r{{left:575px;color:#fff}}
</style><div class="red"></div>
<div class="tt">{esc(d['titulo'])}</div><div class="line"></div><div class="hdl"><svg width="46" height="30" viewBox="0 0 46 30"><path d="M14 4 L3 15 L14 26 Z M32 4 L43 15 L32 26 Z" fill="#09090a"/></svg></div>
<div class="lab" style="left:80px;color:#f4f4f4">{esc(d['antes'])}</div><div class="lab" style="left:575px;color:#0b0b0c">{esc(d['depois'])}</div>
<div class="tx l">{esc(d['antes_txt'])}</div><div class="tx r">{esc(d['depois_txt'])}</div>{foot()}"""

def L_pergunta(d):
    return f"""<style>
body{{background:linear-gradient(180deg,#e0202f 0%,#a5121e 50%,#4a0910 100%)}}
.pill{{background:#09090a}}
.q{{position:absolute;left:80px;right:80px;top:330px;background:#f5f5f5;border-radius:40px;padding:56px 60px 62px;color:#0c0c0d}}
.q .k{{font-size:20px;letter-spacing:.2em;color:var(--red);font-weight:600;margin-bottom:22px}}
.q .t{{font-size:54px;line-height:68px;font-weight:700}}
.a{{position:absolute;left:80px;right:80px;background:#0c0c0d;border-radius:40px;padding:48px 56px 56px}}
.a .hd2{{display:flex;align-items:center;gap:20px;margin-bottom:34px}} .a img{{width:64px;height:64px;border-radius:50%;object-fit:cover}}
.a .n{{font-weight:600;font-size:28px;line-height:32px}} .a .h{{font-size:21px;color:#8b8b90;line-height:26px}}
.a .tx{{font-size:40px;line-height:58px;font-weight:400}}
</style>
<div class="q" id="q"><div class="k">PERGUNTA ANÔNIMA</div><div class="t">{esc(d['pergunta'])}</div></div>
<div class="a" id="a"><div class="hd2"><img src="{AV}"><div><div class="n">{NAME}</div><div class="h">respondeu · {HANDLE}</div></div></div><div class="tx">{esc(d['resposta'])}</div></div>
<script>const q=document.getElementById('q'),a=document.getElementById('a');a.style.top=(q.getBoundingClientRect().bottom+34)+'px';</script>"""

LAYOUTS = dict(tese=L_tese, sumula=L_sumula, chat=L_chat, planilha=L_planilha, antes_depois=L_antes_depois, pergunta=L_pergunta)

def build(d, i):
    fn = LAYOUTS[d["layout"]]
    body = fn(d, i) if d["layout"] == "planilha" else fn(d)
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{body}</body></html>'

def main(src, outdir, prefix="info"):
    from playwright.sync_api import sync_playwright
    os.makedirs(outdir, exist_ok=True)
    items = json.load(open(src, encoding="utf-8"))
    tmp = os.path.join(HERE, "_tmp.html")
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width":1080,"height":1350})
        for i, d in enumerate(items, 1):
            open(tmp, "w", encoding="utf-8").write(build(d, i))
            pg.goto("file://" + tmp); pg.wait_for_timeout(250)
            pg.evaluate("document.fonts.ready")
            ov = pg.evaluate("Math.max(...[...document.querySelectorAll('.b,.tx,.a,.list')].map(e=>e.getBoundingClientRect().bottom))")
            if ov > 1190: print(f"AVISO: post {i} ({d['layout']}) pode colidir com o rodapé ({ov:.0f}px)")
            pg.screenshot(path=os.path.join(outdir, f"{prefix}_{i:03d}_{d['layout']}.png"))
        b.close()
    os.remove(tmp); print(len(items), "posts em", outdir)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], *(sys.argv[3:4]))
