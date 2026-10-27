#!/usr/bin/env python3
"""Publicador do Instagram (API oficial, grátis). Roda no GitHub Actions a cada 15 min.

Lê queue/fila.csv, publica o que já está na hora (horário de São Paulo) e grava o resultado no CSV.
Variáveis de ambiente:
  IG_USER_ID, IG_TOKEN      credenciais (secrets do GitHub)
  MEDIA_BASE_URL            URL pública base das mídias (ex.: https://raw.githubusercontent.com/USUARIO/REPO/main/media/)
  MAX_POR_EXECUCAO          teto de posts por execução (padrão 6)
Tipos: imagem | reel | carrossel (arquivo = caminhos separados por "|", de 2 a 10 imagens)
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
MAXRUN = int(os.environ.get("MAX_POR_EXECUCAO", "6"))
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

def esperar(cid, video=False):
    """Espera o Instagram terminar de processar o container (imagem: segundos; vídeo: até ~10 min)."""
    for _ in range(60):
        time.sleep(10 if video else 5)
        st = http("GET", cid, {"fields": "status_code"}).get("status_code")
        if st == "FINISHED": return
        if st in ("ERROR", "EXPIRED"): raise RuntimeError(f"processamento {st}")
    raise RuntimeError("timeout no processamento da mídia")

def url_midia(arq):
    return BASE.rstrip("/") + "/" + urllib.parse.quote(arq.strip())

def publicar(row):
    if row["tipo"] == "carrossel":
        # carrossel: um container por imagem (is_carousel_item) e depois o container CAROUSEL com a legenda
        arqs = [a for a in row["arquivo"].split("|") if a.strip()]
        if not 2 <= len(arqs) <= 10: raise RuntimeError(f"carrossel precisa de 2 a 10 imagens (tem {len(arqs)})")
        filhos = []
        for a in arqs:
            cid = http("POST", f"{UID}/media", {"image_url": url_midia(a), "is_carousel_item": "true"})["id"]
            esperar(cid); filhos.append(cid)
        pid = http("POST", f"{UID}/media", {"media_type": "CAROUSEL", "children": ",".join(filhos), "caption": row["legenda"]})["id"]
        esperar(pid)
        return http("POST", f"{UID}/media_publish", {"creation_id": pid})["id"]
    url = url_midia(row["arquivo"])
    p = {"caption": row["legenda"]}
    if row["tipo"] == "reel": p.update({"media_type": "REELS", "video_url": url, "share_to_feed": "true"})
    else: p["image_url"] = url
    cid = http("POST", f"{UID}/media", p)["id"]
    esperar(cid, video=row["tipo"] == "reel")
    return http("POST", f"{UID}/media_publish", {"creation_id": cid})["id"]

def ler_csv(path):
    if not os.path.exists(path): return []
    return list(csv.DictReader(open(path, encoding="utf-8", newline="")))

def preparar(rows):
    """Limpa marcas de conflito do git, aplica substituições (queue/substituicoes.csv) e extras (queue/extras.csv).
    Devolve True se mudou alguma coisa."""
    mudou = False
    ok = [r for r in rows if not (r.get("id") or "").startswith(("<<<<<<<", "=======", ">>>>>>>")) and (r.get("id") or "").strip()]
    if len(ok) != len(rows): rows[:] = ok; mudou = True
    qdir = os.path.dirname(FILA)
    # plano novo (queue/plano.csv): substitui TODA a fila pendente antiga (ids que não começam com "v3_").
    # Os ids do plano começam com "v3_"; depois de aplicado, nada mais muda (idempotente).
    subs = ler_csv(os.path.join(qdir, "substituicoes.csv"))
    trocados = {x["id_antigo"] for x in subs}
    plano = [x for x in ler_csv(os.path.join(qdir, "plano.csv")) if x["id"] not in trocados]
    if plano:
        manter = [r for r in rows if not (r["status"] in ("pendente", "erro") and not r["id"].startswith("v3_"))]
        if len(manter) != len(rows):
            print("plano: removidos", len(rows) - len(manter), "posts antigos pendentes"); rows[:] = manter; mudou = True
        ids0 = {r["id"] for r in rows}
        novos = [x for x in plano if x["id"] not in ids0]
        for x in novos:
            rows.append({"id": x["id"], "datetime": x["datetime"], "tipo": x["tipo"], "arquivo": x["arquivo"], "legenda": x["legenda"],
                         "status": "pendente", "post_id": "", "tentativas": "0", "erro": ""})
        if novos:
            print("plano: adicionados", len(novos)); rows.sort(key=lambda r: r["datetime"]); mudou = True
    for s in subs:
        for r in rows:
            if r["id"] == s["id_antigo"] and r["status"] in ("pendente", "erro"):
                r.update({"id": s["id"], "arquivo": s["arquivo"], "legenda": s["legenda"], "status": "pendente", "tentativas": "0", "erro": ""})
                if (s.get("tipo") or "").strip(): r["tipo"] = s["tipo"].strip()
                if (s.get("datetime") or "").strip(): r["datetime"] = s["datetime"].strip()
                print("substituído:", s["id_antigo"], "→", s["id"]); mudou = True
    if mudou: rows.sort(key=lambda r: r["datetime"])
    ids = {r["id"] for r in rows}
    for e in ler_csv(os.path.join(qdir, "extras.csv")):
        if e["id"] not in ids:
            rows.append({"id": e["id"], "datetime": e["datetime"], "tipo": e["tipo"], "arquivo": e["arquivo"], "legenda": e["legenda"],
                         "status": "pendente", "post_id": "", "tentativas": "0", "erro": ""})
            print("extra adicionado:", e["id"], e["datetime"]); mudou = True
    return mudou

def salvar(rows):
    with open(FILA, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS); w.writeheader(); w.writerows(rows)

def main():
    rows = ler_csv(FILA)
    # MODO PAUSA: se existir queue/PAUSA, nada é publicado e tudo que estava pendente vira "cancelado".
    # Para voltar a postar: apague queue/PAUSA, coloque os novos posts em queue/plano.csv (veja RETOMAR.md).
    if os.path.exists(os.path.join(os.path.dirname(FILA), "PAUSA")):
        n = 0
        for r in rows:
            if r["status"] in ("pendente", "erro"): r["status"] = "cancelado"; n += 1
        if n:
            print("PAUSA: cancelados", n, "posts pendentes")
            if not DRY: salvar(rows)
        print("PAUSA ativa: nada será publicado."); return
    if preparar(rows) and not DRY: salvar(rows)
    agora = datetime.now(SP)
    # posts pendentes atrasados há mais de 12 h (ex.: depois de uma pausa) não saem de uma vez: viram "expirado"
    exp = 0
    for r in rows:
        if r["status"] == "pendente" and (agora - datetime.fromisoformat(r["datetime"]).replace(tzinfo=SP)).total_seconds() > 12 * 3600:
            r["status"] = "expirado"; exp += 1
    if exp:
        print("expirados (atrasados > 12h):", exp)
        if not DRY: salvar(rows)
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
        salvar(rows)  # grava a cada post para não perder progresso

if __name__ == "__main__": main()
