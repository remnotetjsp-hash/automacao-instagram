#!/usr/bin/env python3
"""Monta o plano de 40 posts/dia (7h-21h) de 6/10 a 4/11 -> queue/plano.csv.
Roda no PC dentro de automacao-instagram/. Só lê; não mexe em queue/fila.csv."""
import csv, json, os, random, collections, sys
from datetime import date, timedelta
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if os.path.basename(os.path.dirname(os.path.abspath(__file__)))=="scripts" else os.getcwd()
os.chdir(R)
DIAS, SLOTS, INI, PASSO = 30, 40, 7*60, 21
D0 = date(2026, 10, 6)
REEL_IDX = [4, 14, 24, 34]
EXCLUIR_INFO = {f"ex_l1_{i:02d}" for i in range(1, 9)}   # já postados pelo cliente
def lcsv(p): return list(csv.DictReader(open(p, encoding="utf-8", newline=""))) if os.path.exists(p) else []

fila = [r for r in lcsv("queue/fila.csv") if r["id"] and not r["id"].startswith(("<", "=", ">"))]
pub_ids = {r["id"] for r in fila if r["status"] == "publicado"}
pub_arq = {r["arquivo"] for r in fila if r["status"] == "publicado"}
ordem_fila = {r["arquivo"]: i for i, r in enumerate(fila)}

def pool(rows, prefixo):
    out = []
    for r in rows:
        if r["arquivo"] in pub_arq or r["id"] in pub_ids or r["id"] in EXCLUIR_INFO: continue
        if not os.path.exists(os.path.join("media", r["arquivo"])): continue
        out.append(r)
    # os que já estavam na fila vêm primeiro (na ordem em que estavam), depois os livres, depois os novos
    def chave(r):
        if r["arquivo"] in ordem_fila: return (0, ordem_fila[r["arquivo"]])
        return (1 if r.get("origem") != "novo3" else 2, r["id"])
    out.sort(key=chave); return out

tw_rows = lcsv("conteudo/tweets.csv"); ids_tw = {r["id"] for r in tw_rows}
tw_rows += [r for r in lcsv("conteudo/novos3_tw.csv") if r["id"] not in ids_tw]
inf_rows = lcsv("conteudo/informativos.csv"); ids_in = {r["id"] for r in inf_rows}
inf_rows += [r for r in lcsv("conteudo/novos3_info.csv") if r["id"] not in ids_in]
TW, INF = pool(tw_rows, "tw"), pool(inf_rows, "info")
LAY = json.load(open("conteudo/layout_map.json"))

# ordena informativos evitando layout repetido em sequência
def ordenar_info(p):
    p = p[:]; out = []; ult = None
    while p:
        for j, r in enumerate(p[:14]):
            l = LAY.get(r["id"], "ex")
            if l == "ex" or l != ult: break
        else: j = 0
        r = p.pop(j); out.append(r); ult = LAY.get(r["id"], "ex")
    return out
INF = ordenar_info(INF)

# reels
MUS = json.load(open("conteudo/music_map.json"))
reels = lcsv("conteudo/reels.csv") + [r for r in json.load(open("conteudo/reels_novos_rows.json"))]
seen = set(); rr = []
for r in reels:
    if r["id"] in seen: continue
    seen.add(r["id"]); rr.append(r)
reels = [r for r in rr if r["arquivo"] not in pub_arq and r["id"] not in pub_ids and os.path.exists(os.path.join("media", r["arquivo"]))]
azul = sorted([r for r in reels if r["id"].startswith("rb")], key=lambda r: r["id"])
off = sorted([r for r in reels if r["id"].startswith("ro")], key=lambda r: r["id"])
cin = [r for r in reels if r["id"].startswith("rg")]
cin_old = sorted([r for r in cin if int(r["id"][2:]) <= 30], key=lambda r: r["id"])
cin_new = [r for r in cin if int(r["id"][2:]) > 30]
cin_new.sort(key=lambda r: (((int(r["id"][2:]) - 31) % 2), (int(r["id"][2:]) - 31) // 2))   # metades do mesmo trecho ficam longe
cin_pool = []
a, b = cin_new[:], cin_old[:]
while a or b:
    for _ in range(2):
        if a: cin_pool.append(a.pop(0))
    if b: cin_pool.append(b.pop(0))

dias_off = [1 + 8 * j for j in range(len(off))]
def mus(r): return MUS.get(r["id"])
plano = []; stats = collections.Counter(); conflitos = 0
ti = ii = 0; proximo_tipo = "T"
for d in range(DIAS):
    dia = D0 + timedelta(days=d)
    # quais reels hoje
    hoje = []
    if azul: hoje.append(("azul", azul.pop(0)))
    if d in dias_off and off: hoje.append(("off", off.pop(0)))
    while len(hoje) < 4 and cin_pool:
        usados = {mus(r) for _, r in hoje}
        j = next((k for k, r in enumerate(cin_pool[:8]) if mus(r) not in usados), 0)
        hoje.append(("cin", cin_pool.pop(j)))
    while len(hoje) < 4 and azul: hoje.append(("azul", azul.pop(0)))
    if len({mus(r) for _, r in hoje}) < min(3, len(hoje)): conflitos += 1
    # posição: gira para variar onde cai o azul
    rot = d % len(hoje) if hoje else 0
    hoje = hoje[rot:] + hoje[:rot]
    idx_reel = dict(zip(REEL_IDX[:len(hoje)], hoje))
    for k in range(SLOTS):
        h = INI + k * PASSO; dt = f"{dia.isoformat()}T{h//60:02d}:{h%60:02d}:00"
        if k in idx_reel:
            kind, r = idx_reel[k]
            plano.append({"id": "v2_" + r["id"], "datetime": dt, "tipo": "reel", "arquivo": r["arquivo"], "legenda": r["legenda"]}); stats["reel_" + kind] += 1
        else:
            if proximo_tipo == "T":
                r = TW[ti]; ti += 1; proximo_tipo = "I"; stats["tweet"] += 1
            else:
                r = INF[ii]; ii += 1; proximo_tipo = "T"; stats["info"] += 1
            plano.append({"id": "v2_" + r["id"], "datetime": dt, "tipo": "imagem", "arquivo": r["arquivo"], "legenda": r["legenda"]})
with open("queue/plano.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["id", "datetime", "tipo", "arquivo", "legenda"]); w.writeheader(); w.writerows(plano)
print("posts:", len(plano), dict(stats), "· dias com música repetida:", conflitos)
print("tweets usados", ti, "de", len(TW), "· info usados", ii, "de", len(INF), "· reels sobrando: azul", len(azul), "cinza", len(cin_pool), "escritório", len(off))
