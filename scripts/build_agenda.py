#!/usr/bin/env python3
"""Agenda de 30 dias (v2): 2 estáticos + 1 Reel por dia -> queue/plano.csv (ids v3_).
Estáticos: primeiro os posts premium (conteudo/premium.csv), depois a lista dos 60.
Regra: nunca dois posts do mesmo estilo de design no mesmo dia."""
import csv, json, os, shutil
from datetime import date, timedelta
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(R)
D0 = date(2026, 10, 9); DIAS = 30
HORAS = {"est1": "11:45", "reel": "18:45", "est2": "20:45"}
EST60 = "info_189 info_409 info_423 info_207 info_420 info_429 info_330 info_549 info_434 info_417 info_551 info_441 info_439 info_080 info_522 info_539 info_083 info_555 info_562 info_092 info_556 info_566 info_448 info_642 info_601 info_503 info_677 info_603 info_547 info_554 info_687 info_612 info_681 info_761 info_637 info_104 info_684 info_638 info_315 info_685 info_712 info_590 info_683 info_150 info_087 info_763 info_042 info_645 info_034 info_363 info_680 info_321 info_617 info_144 info_633 info_324 info_752 info_454 info_598 info_450".split()
ESC = ["ro03", "ro04"] + [f"ro{i:02d}" for i in range(5, 14)]
AZ = [f"rb{i:02d}" for i in range(3, 31)]
CZ = ["rg03", "rg05", "rg07", "rg09", "rg11", "rg13", "rg15", "rg17", "rg19", "rg21", "rg23", "rg25"]
G = "../_guardado_nao_enviado/media/"
def lcsv(p): return list(csv.DictReader(open(p, encoding="utf-8", newline=""))) if os.path.exists(p) else []
leg = {}
for f in ("informativos.csv", "novos3_info.csv", "novos4_info.csv", "novos4b_info.csv", "reels.csv", "premium.csv"):
    for r in lcsv("conteudo/" + f): leg.setdefault(r["id"], r["legenda"])
for f in ("reels_novos_rows.json", "reels_novos4_rows.json"):
    for r in json.load(open("conteudo/" + f, encoding="utf-8")): leg.setdefault(r["id"], r["legenda"])
# estilo de design de cada post
lay = dict(json.load(open("conteudo/layout_map.json", encoding="utf-8")))
for f in ("novos3_meta.json", "novos4_meta.json"):
    for r in json.load(open("conteudo/" + f, encoding="utf-8")): lay.setdefault(r["id"], r["layout"])
prem = lcsv("conteudo/premium.csv")
estilo = {}
for r in prem: estilo[r["id"]] = r["id"] if r["estilo"] == "3d" else "prem_" + r["estilo"]  # cada cena 3D é um design próprio
for i in EST60: estilo[i] = "L_" + lay.get(i, "outro_" + i)
fila = [r["id"] for r in prem] + EST60
# monta os pares de cada dia: estilos diferentes no mesmo dia e, se possível, diferentes do último post do dia anterior
resto = fila[:2 * DIAS]; dias = []; ult = None
while resto and len(dias) < DIAS:
    a = resto.pop(0)
    cand = [x for x in resto[:14] if estilo[x] != estilo[a]]
    b = next((x for x in cand if estilo[x] != ult), cand[0] if cand else None)
    if b is None: raise SystemExit("sem par de estilo diferente para " + a)
    resto.remove(b); dias.append((a, b)); ult = estilo[b]
reels = ESC[:]; a = c = 0
while len(reels) < DIAS:
    if (len(reels) - len(ESC)) % 2 == 0: reels.append(AZ[a]); a += 1
    else: reels.append(CZ[c]); c += 1
plano = []; copiados = 0
def garante(sub, nome):
    global copiados
    dst = f"media/{sub}/{nome}"
    if not os.path.exists(dst):
        shutil.copyfile(G + f"{sub}/{nome}", dst); copiados += 1
    return f"{sub}/{nome}"
for d in range(DIAS):
    dia = (D0 + timedelta(days=d)).isoformat()
    for k, i in (("est1", dias[d][0]), ("est2", dias[d][1])):
        arq = garante("info", i + ".jpg") if not i.startswith("prem_") else f"info/{i}.jpg"
        plano.append({"id": "v3_" + i, "datetime": f"{dia}T{HORAS[k]}:00", "tipo": "imagem", "arquivo": arq, "legenda": leg[i]})
    rid = reels[d]; arq = garante("reels", rid + ".mp4")
    plano.append({"id": "v3_" + rid, "datetime": f"{dia}T{HORAS['reel']}:00", "tipo": "reel", "arquivo": arq, "legenda": leg[rid]})
plano.sort(key=lambda r: r["datetime"])
ids = [r["id"] for r in plano]; assert len(ids) == len(set(ids)), "id repetido"
for r in plano:
    assert "Leonardo Rezende\nEspecialista em dívidas empresariais" in r["legenda"], r["id"]
    assert os.path.exists("media/" + r["arquivo"]), r["arquivo"]
for x, y in dias: assert estilo[x] != estilo[y], (x, y)
with open("queue/plano.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["id", "datetime", "tipo", "arquivo", "legenda"]); w.writeheader(); w.writerows(plano)
print("posts", len(plano), "de", plano[0]["datetime"], "a", plano[-1]["datetime"], "· mídia copiada de volta:", copiados)
for d, (x, y) in enumerate(dias): print((D0 + timedelta(days=d)).strftime("%d/%m"), x, f"[{estilo[x]}]", "+", y, f"[{estilo[y]}]", "| reel", reels[d])
