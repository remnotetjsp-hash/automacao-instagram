#!/usr/bin/env python3
"""Publicador do Instagram (API oficial, grátis). Roda no GitHub Actions a cada 15 min.

Lê queue/fila.csv, publica o que já está na hora (horário de São Paulo) e grava o resultado no CSV.
Variáveis de ambiente:
  IG_USER_ID, IG_TOKEN      credenciais (secrets do GitHub)
  MEDIA_BASE_URL            URL pública base das mídias (ex.: https://raw.githubusercontent.com/USUARIO/REPO/main/media/)
  MAX_POR_EXECUCAO          teto de posts por execução (padrão 3)
  DRY_RUN=1                 só mostra o que faria
  API_BASE                  padrão https://graph.instagram.com/v22.0 (usado nos testes)
"""
import csv, os, sys, time, json, urllib.parse, urllib.request, urllib.error
from datetime import datetime
from zoneinfo import ZoneInfo

SP = ZoneInfo("America/Sao_Paulo")
FILA = os.environ.get("FILA", os.path.join(os.path.dirname(__file__), "..", "queue", "fila.csv"))
API = os.environ.get("API_BASE", "https://graph.instagram.com/v22.0").rstrip("/")
UID = os.environ.get("IG_USER_ID", "")
TOKEN = os.environ.get("IG_TOKEN", "")
BASE = os.environ.get("MEDIA_BASE_URL", "")
MAXRUN = int(os.environ.get("MAX_POR_EXECUCAO", "3"))
DRY = os.environ.get("DRY_RUN") == "1"
MAX_TENT = 3
CAMPOS = ["id", "datetime", "tipo", "arquivo", "legenda", "status", "post_id", "tentativas", "erro"]

def http(method, path, params=None):
    params = dict(params or {}); params["access_token"] = TOKEN
    url = f"{API}/{path}"
    data = None
    if method == "GET": url += "?" + urllib.parse.urlencode(params)
    else: data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"HTTP {e.code}: {body[:400]}")

def cota_restante():
    try:
        r = http("GET", f"{UID}/content_publishing_limit", {"fields": "quota_usage,config"})
        d = r["data"][0]; return d["config"]["quota_total"] - d["quota_usage"]
    except Exception as e:
        print("aviso: não consegui ler a cota:", e); return 100

def publicar(row):
    url = BASE.rstrip("/") + "/" + urllib.parse.quote(row["arquivo"])
    p = {"caption": row["legenda"]}
    if row["tipo"] == "reel": p.update({"media_type": "REELS", "video_url": url, "share_to_feed": "true"})
    else: p["image_url"] = url
    cid = http("POST", f"{UID}/media", p)["id"]
    if row["tipo"] == "reel":
        for _ in range(60):  # até ~10 min
            st = http("GET", cid, {"fields": "status_code"}).get("status_code")
            if st == "FINISHED": break
            if st in ("ERROR", "EXPIRED"): raise RuntimeError(f"processamento {st}")
            time.sleep(10)
        else: raise RuntimeError("timeout no processamento do vídeo")
    return http("POST", f"{UID}/media_publish", {"creation_id": cid})["id"]

def main():
    rows = list(csv.DictReader(open(FILA, encoding="utf-8", newline="")))
    agora = datetime.now(SP)
    pend = [r for r in rows if r["status"] in ("pendente", "erro") and int(r["tentativas"] or 0) < MAX_TENT
            and datetime.fromisoformat(r["datetime"]).replace(tzinfo=SP) <= agora]
    pend.sort(key=lambda r: r["datetime"])
    print(f"{agora:%d/%m %H:%M} · pendentes vencidos: {len(pend)} · máx. por execução: {MAXRUN}")
    if not DRY and pend:
        if not (UID and TOKEN and BASE): sys.exit("faltam IG_USER_ID, IG_TOKEN ou MEDIA_BASE_URL")
        pend = pend[:min(MAXRUN, cota_restante())]
    else: pend = pend[:MAXRUN]
    mudou = False
    for r in pend:
        print(f"→ {r['id']} ({r['tipo']}) {r['arquivo']}")
        if DRY: continue
        try:
            r["post_id"] = publicar(r); r["status"] = "publicado"; r["erro"] = ""
            print("  publicado:", r["post_id"])
        except Exception as e:
            r["tentativas"] = str(int(r["tentativas"] or 0) + 1); r["status"] = "erro"; r["erro"] = str(e)[:300]
            print("  ERRO:", e)
        mudou = True
        with open(FILA, "w", encoding="utf-8", newline="") as f:  # grava a cada post para não perder progresso
            w = csv.DictWriter(f, fieldnames=CAMPOS); w.writeheader(); w.writerows(rows)

if __name__ == "__main__": main()
