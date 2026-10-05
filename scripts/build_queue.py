#!/usr/bin/env python3
"""Monta queue/fila.csv a partir de conteudo/tweets.csv, informativos.csv e reels.csv.

Uso (na pasta automacao-instagram):
  python3 scripts/build_queue.py --inicio 2026-10-05 --dias 30

Por dia: 23 horários entre 7h e ~18h44 (a cada 32 min): 20 estáticos (alternando tweet/informativo, 10+10)
e 3 Reels nos horários 4, 12 e 20 (8h36, 13h52, 17h08) (cinza, azul e escritório). Os de escritório são espalhados pelo mês
conforme a quantidade disponível (se houver menos que 1 por dia, o horário fica vazio nos outros dias).
Reexecutável: reconstrói só as linhas ainda pendentes dos conteúdos; o que já foi publicado (ou com erro) fica.
"""
import argparse, csv, os, sys
from datetime import datetime, timedelta

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CAMPOS = ["id", "datetime", "tipo", "arquivo", "legenda", "status", "post_id", "tentativas", "erro"]
SLOTS_DIA, INTERVALO_MIN, HORA_INI = 23, 32, 7
SLOTS_REEL = {3: "cinza", 11: "azul", 19: "escritorio"}

def ler(nome):
    p = os.path.join(ROOT, "conteudo", nome)
    return list(csv.DictReader(open(p, encoding="utf-8", newline=""))) if os.path.exists(p) else []

def intercalar(a, b):
    """Espalha a lista b (menor) de forma uniforme dentro da lista a."""
    if not b: return list(a)
    n, m = len(a), len(b)
    total = n + m
    pos = {int((k + 0.5) * total / m) for k in range(m)}
    res, ia, ib = [], 0, 0
    for i in range(total):
        if i in pos and ib < m: res.append(b[ib]); ib += 1
        elif ia < n: res.append(a[ia]); ia += 1
        else: res.append(b[ib]); ib += 1
    return res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", required=True, help="primeiro dia (AAAA-MM-DD)")
    ap.add_argument("--dias", type=int, default=30)
    a = ap.parse_args()

    tw = ler("tweets.csv")
    inf = ler("informativos.csv")
    novos = [r for r in inf if r["origem"] != "existente"]
    exist = [r for r in inf if r["origem"] == "existente"]
    inf = intercalar(novos, exist)
    reels = ler("reels.csv")
    por_tipo_reel = {t: [r for r in reels if r["tipo"] == t] for t in ("cinza", "azul", "escritorio")}
    print(f"tweets: {len(tw)} · informativos: {len(inf)} · reels: { {k: len(v) for k, v in por_tipo_reel.items()} }")

    ids_conteudo = {r["id"] for r in tw + inf + reels}
    fila_path = os.path.join(ROOT, "queue", "fila.csv")
    atual = list(csv.DictReader(open(fila_path, encoding="utf-8", newline=""))) if os.path.exists(fila_path) else []
    manter = [r for r in atual if not (r["id"] in ids_conteudo and r["status"] in ("pendente", "aguardando"))]
    ja = {r["id"] for r in manter}
    tw = [r for r in tw if r["id"] not in ja]; inf = [r for r in inf if r["id"] not in ja]
    fila_reel = {t: iter([r for r in v if r["id"] not in ja]) for t, v in por_tipo_reel.items()}
    n_esc = len([r for r in por_tipo_reel["escritorio"] if r["id"] not in ja])
    # dias em que sai Reel de escritório (espalhados)
    dias_esc = {round(i * (a.dias - 1) / max(n_esc - 1, 1)) for i in range(n_esc)} if n_esc > 1 else ({0} if n_esc else set())

    novas, it, ii = [], iter(tw), iter(inf)
    dia0 = datetime.fromisoformat(a.inicio)
    faltou = {"tweet": 0, "info": 0, "cinza": 0, "azul": 0, "escritorio": 0}
    for d in range(a.dias):
        base = dia0 + timedelta(days=d, hours=HORA_INI)
        n_nr = 0
        for s in range(SLOTS_DIA):
            quando = (base + timedelta(minutes=s * INTERVALO_MIN)).strftime("%Y-%m-%dT%H:%M:00")
            if s in SLOTS_REEL:
                t = SLOTS_REEL[s]
                if t == "escritorio" and d not in dias_esc: continue
                r = next(fila_reel[t], None)
                if r is None: faltou[t] += 1; continue
                tipo = "reel"
            else:
                t, src = ("tweet", it) if n_nr % 2 == 0 else ("info", ii); n_nr += 1
                r = next(src, None)
                if r is None: faltou[t] += 1; continue
                tipo = "imagem"
            novas.append({"id": r["id"], "datetime": quando, "tipo": tipo, "arquivo": r["arquivo"],
                          "legenda": r["legenda"], "status": "pendente", "post_id": "", "tentativas": "0", "erro": ""})
    # validações
    faltam_arq = [r["arquivo"] for r in novas if not os.path.exists(os.path.join(ROOT, "media", r["arquivo"]))]
    if faltam_arq:
        print("ERRO: arquivos de mídia não encontrados:", faltam_arq[:5], "... total", len(faltam_arq)); sys.exit(1)
    for r in novas:
        if len(r["legenda"]) > 2200 or r["legenda"].count("#") > 30: sys.exit(f"legenda inválida em {r['id']}")
    ids = [r["id"] for r in manter + novas]
    assert len(ids) == len(set(ids)), "ids duplicados"
    novas.sort(key=lambda r: r["datetime"])
    with open(fila_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS); w.writeheader(); w.writerows(manter + novas)
    por_tipo = {}
    for r in novas: por_tipo[r["tipo"]] = por_tipo.get(r["tipo"], 0) + 1
    print(f"fila: {len(manter)} mantidas + {len(novas)} novas {por_tipo} · de {novas[0]['datetime']} até {novas[-1]['datetime']}")
    if any(faltou.values()): print("sem conteúdo para alguns horários (vazios):", faltou)

if __name__ == "__main__": main()
