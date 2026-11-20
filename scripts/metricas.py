#!/usr/bin/env python3
"""Coleta as métricas do Instagram (API oficial, só leitura) uma vez por dia.

Grava:
  queue/metricas.csv        uma linha por post dos últimos 30 dias (até 120 posts) (sobrescrito a cada coleta)
  queue/metricas_conta.csv  uma linha por dia com seguidores e total de posts (acumula)
Roda no mesmo workflow do publicador; se já coletou hoje (horário de São Paulo), sai sem fazer nada.
Variáveis: IG_USER_ID, IG_TOKEN, API_BASE (testes), FORCAR=1 (coleta mesmo se já coletou hoje).
"""
import csv, os, sys, json, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

SP = ZoneInfo("America/Sao_Paulo")
QDIR = os.environ.get("QDIR", os.path.join(os.path.dirname(__file__), "..", "queue"))
API = os.environ.get("API_BASE", "https://graph.instagram.com/v22.0").rstrip("/")
UID = os.environ.get("IG_USER_ID", "")
TOKEN = os.environ.get("IG_TOKEN", "")
DIAS = 30
MAX_POSTS = 120
HORA_MIN = 20  # coleta à noite, quando o dia de posts já fechou

# métricas por tipo de mídia (nomes da API do Instagram; as que não existirem para o tipo são puladas)
MET_REEL = ["views", "reach", "likes", "comments", "saved", "shares", "total_interactions", "ig_reels_avg_watch_time", "ig_reels_video_view_total_time"]
MET_FEED = ["views", "reach", "likes", "comments", "saved", "shares", "total_interactions"]
COLS = ["post_id", "data", "hora", "tipo", "permalink", "legenda_inicio"] + list(dict.fromkeys(MET_REEL + MET_FEED)) + ["erro"]


def http(path, params=None):
    params = dict(params or {}); params["access_token"] = TOKEN
    url = f"{API}/{path}?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")


def insights(mid, metricas):
    """Pede todas de uma vez; se a API recusar alguma, tenta uma a uma."""
    def ler(resp):
        out = {}
        for m in resp.get("data", []):
            v = m.get("values", [{}])
            out[m["name"]] = (v[0].get("value") if v else None) if "values" in m else m.get("total_value", {}).get("value")
        return out
    try:
        return ler(http(f"{mid}/insights", {"metric": ",".join(metricas)})), ""
    except RuntimeError:
        out, falhas = {}, []
        for m in metricas:
            try: out.update(ler(http(f"{mid}/insights", {"metric": m})))
            except RuntimeError: falhas.append(m)
        return out, ("sem: " + ",".join(falhas)) if falhas else ""


def ja_coletou_hoje(hoje):
    p = os.path.join(QDIR, "metricas_conta.csv")
    if not os.path.exists(p): return False
    with open(p, encoding="utf-8") as f:
        return any(r.get("data") == hoje for r in csv.DictReader(f))


def main():
    agora = datetime.now(SP); hoje = agora.strftime("%Y-%m-%d")
    if not (UID and TOKEN): print("métricas: faltam IG_USER_ID/IG_TOKEN"); return
    if os.environ.get("FORCAR") != "1":
        if agora.hour < HORA_MIN: print(f"métricas: só depois das {HORA_MIN}h"); return
        if ja_coletou_hoje(hoje): print("métricas: já coletadas hoje"); return
    conta = http(UID, {"fields": "followers_count,follows_count,media_count"})
    limite = agora - timedelta(days=DIAS)
    linhas, url_next, params = [], f"{UID}/media", {"fields": "id,caption,media_type,media_product_type,timestamp,permalink", "limit": 50}
    while url_next:
        resp = http(url_next, params)
        parar = False
        for m in resp.get("data", []):
            ts = datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S%z").astimezone(SP)
            if ts < limite or len(linhas) >= MAX_POSTS: parar = True; break
            tipo = "reel" if m.get("media_product_type") == "REELS" else ("carrossel" if m.get("media_type") == "CAROUSEL_ALBUM" else "imagem")
            vals, erro = insights(m["id"], MET_REEL if tipo == "reel" else MET_FEED)
            leg = (m.get("caption") or "").replace("\n", " ")[:80]
            linhas.append({"post_id": m["id"], "data": ts.strftime("%Y-%m-%d"), "hora": ts.strftime("%H:%M"), "tipo": tipo,
                           "permalink": m.get("permalink", ""), "legenda_inicio": leg, "erro": erro, **{k: vals.get(k, "") for k in COLS if k in vals}})
        nxt = resp.get("paging", {}).get("cursors", {}).get("after") if resp.get("paging", {}).get("next") else None
        if parar or not nxt: break
        params = dict(params, after=nxt)
    with open(os.path.join(QDIR, "metricas.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore"); w.writeheader(); w.writerows(linhas)
    p = os.path.join(QDIR, "metricas_conta.csv"); novo = not os.path.exists(p)
    with open(p, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if novo: w.writerow(["data", "hora", "seguidores", "seguindo", "posts"])
        w.writerow([hoje, agora.strftime("%H:%M"), conta.get("followers_count", ""), conta.get("follows_count", ""), conta.get("media_count", "")])
    print(f"métricas: {len(linhas)} posts, {conta.get('followers_count')} seguidores")


if __name__ == "__main__":
    try: main()
    except Exception as e: print("métricas: erro", e)  # nunca derruba o publicador
