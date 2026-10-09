#!/usr/bin/env python3
"""Plano de 60 posts/dia (7h-20h46, a cada 14 min) de 7/10 a 5/11 -> queue/plano.csv. Só lê; não mexe em fila.csv."""
import csv, json, os, collections, glob
from datetime import date, timedelta
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(R)
DIAS, SLOTS, INI, PASSO = 30, 60, 7*60, 14
D0 = date(2026, 10, 7); CORTE = D0.isoformat() + "T00:00:00"
REEL_IDX = [3, 9, 15, 21, 27, 33, 39, 45, 51, 57]
EXCLUIR = {f"ex_l1_{i:02d}" for i in range(1, 9)}
def lcsv(p): return list(csv.DictReader(open(p, encoding="utf-8", newline=""))) if os.path.exists(p) else []
fila = [r for r in lcsv("queue/fila.csv") if r["id"] and not r["id"].startswith(("<", "=", ">"))]
usados = {r["arquivo"] for r in fila if r["status"] == "publicado" or (r["status"] == "pendente" and r["datetime"] < CORTE)}
ordem_fila = {r["arquivo"]: i for i, r in enumerate(fila)}
def pool(rows):
    seen = set(); out = []
    for r in rows:
        if r["id"] in seen: continue
        seen.add(r["id"])
        if r["arquivo"] in usados or r["id"] in EXCLUIR: continue
        if not os.path.exists(os.path.join("media", r["arquivo"])): continue
        out.append(r)
    def chave(r):
        if r["arquivo"] in ordem_fila: return (0, ordem_fila[r["arquivo"]], r["id"])
        return (1, 0, r["id"]) if r.get("origem") not in ("novo3", "novo4") else (2, 0, r["id"])
    out.sort(key=chave); return out
C = "conteudo/"
TW = pool(lcsv(C+"tweets.csv") + lcsv(C+"novos3_tw.csv") + lcsv(C+"novos4_tw.csv") + lcsv(C+"novos4b_tw.csv"))
INF = pool(lcsv(C+"informativos.csv") + lcsv(C+"novos3_info.csv") + lcsv(C+"novos4_info.csv") + lcsv(C+"novos4b_info.csv"))
LAY = json.load(open(C+"layout_map.json"))
for m in json.load(open(C+"novos4_meta.json")): LAY[m["id"]] = m["layout"]
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
# ---- reels
MUS = json.load(open(C+"music_map.json"))
V = "../videos_leo/"
def lj(p): return json.load(open(p)) if os.path.exists(p) else []
planos = {x["id"]: x for f in ("plan.json", "plan2.json", "plan3.json") for x in lj(V+f)}
A = sorted(float(x["srcs"][0][1]) for x in lj(V+"plan.json") if x["id"].startswith("rg"))
bs = sorted(float(x["srcs"][0][1]) for x in lj(V+"plan2.json"))
BW = [s for s in bs if s+8 in bs]
WINS = sorted(A + BW)
def chave_janela(rid):
    if rid.startswith("rb"): return "azul"
    p = planos.get(rid)
    if not p: return rid
    if rid.startswith("ro"): return "off:" + p["srcs"][0][0][-30:]
    t = float(p["srcs"][0][1]); return "w%g" % max(w for w in WINS if w <= t + 1e-6)
rows = lcsv(C+"reels.csv") + lj(C+"reels_novos_rows.json") + lj(C+"reels_novos4_rows.json")
seen = set(); rr = []
for r in rows:
    if r["id"] in seen: continue
    seen.add(r["id"])
    if r["arquivo"] in usados or not os.path.exists(os.path.join("media", r["arquivo"])): continue
    rr.append(r)
azul = sorted([r for r in rr if r["id"].startswith("rb")], key=lambda r: r["id"])
off = [r for r in rr if r["id"].startswith("ro")]
cin = [r for r in rr if r["id"].startswith("rg")]
# cinza: intercala antigos e novos para a mistura ficar variada
cin.sort(key=lambda r: int(r["id"][2:])); import random; random.Random(11).shuffle(cin)
def mus(r): return MUS.get(r["id"])
dias_off = sorted({round(i * DIAS / max(len(off), 1)) for i in range(len(off))})
plano = []; stats = collections.Counter(); recente = {}   # janela -> último dia usado
ti = ii = 0; prox = "T"; falta_pos = []
for d in range(DIAS):
    dia = D0 + timedelta(days=d); hoje = []
    if azul: hoje.append(("azul", azul.pop(0)))
    if d in dias_off and off: hoje.append(("off", off.pop(0)))
    ja = {chave_janela(r["id"]) for _, r in hoje}
    while len(hoje) < len(REEL_IDX) and cin:
        usados_m = collections.Counter(mus(r) for _, r in hoje)
        pick = None
        for esp in (6, 4, 2, 0):
            for k, r in enumerate(cin):
                w = chave_janela(r["id"])
                if w in ja or d - recente.get(w, -99) < esp: continue
                if usados_m[mus(r)] >= 4: continue
                pick = k; break
            if pick is not None: break
        if pick is None: pick = 0
        r = cin.pop(pick); ja.add(chave_janela(r["id"])); hoje.append(("cin", r))
    for _, r in hoje: recente[chave_janela(r["id"])] = d
    rot = d % len(hoje) if hoje else 0
    hoje = hoje[rot:] + hoje[:rot]
    # espalha: não deixa dois do mesmo tipo/música colados
    idx_reel = dict(zip(REEL_IDX[:len(hoje)], hoje))
    for k in range(SLOTS):
        h = INI + k * PASSO; dt = f"{dia.isoformat()}T{h//60:02d}:{h%60:02d}:00"
        if k in idx_reel:
            kind, r = idx_reel[k]; tipo = "reel"; stats["reel_" + kind] += 1
        else:
            tipo = "imagem"
            ordem = ("T", "I") if prox == "T" else ("I", "T")
            r = None
            for q in ordem:
                if q == "T" and ti < len(TW): r = TW[ti]; ti += 1; prox = "I"; stats["tweet"] += 1; break
                if q == "I" and ii < len(INF): r = INF[ii]; ii += 1; prox = "T"; stats["info"] += 1; break
            if r is None:
                if cin: r = cin.pop(0); tipo = "reel"; stats["reel_extra"] += 1
                elif azul: r = azul.pop(0); tipo = "reel"; stats["reel_extra"] += 1
                else: falta_pos.append(dt); continue
        plano.append({"id": "v3_" + r["id"], "datetime": dt, "tipo": tipo, "arquivo": r["arquivo"], "legenda": r["legenda"]})
with open("queue/plano.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["id", "datetime", "tipo", "arquivo", "legenda"]); w.writeheader(); w.writerows(plano)
print("posts:", len(plano), dict(stats), "· vagas sem conteúdo:", len(falta_pos))
print("sobra: tweets", len(TW) - ti, "info", len(INF) - ii, "· reels azul", len(azul), "cinza", len(cin), "escritório", len(off))
