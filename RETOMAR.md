# Como voltar a postar automaticamente

Estado atual (8/10/2026): agenda de 30 dias montada (9/10 a 7/11): 2 estáticos + 1 Reel por dia, às 11h45, 18h45 (Reel) e 20h45. Gerada por `scripts/build_agenda.py`. Para pausar de novo: crie o arquivo `queue/PAUSA` ou desligue o workflow no GitHub.
Quando o robô rodar com `queue/PAUSA`, ele não publica nada e marca como "cancelado" tudo que estava pendente.

## Para retomar
1. Escolha os posts. Cada post precisa de: id, datetime (AAAA-MM-DDTHH:MM:00, horário de Brasília), tipo (imagem ou reel), arquivo (caminho dentro de `media/`) e legenda.
   Peça ao Claude: "monte o plano de X posts por dia a partir de DD/MM". Ele grava em `queue/plano.csv` (ids começando com `v3_`).
2. Apague o arquivo `queue/PAUSA`.
3. Rode o `enviar.bat` (envia plano, mídia e scripts para o GitHub).
4. No GitHub: Actions > publicar-instagram > menu (⋯) > **Enable workflow**.
   O robô roda a cada 15 minutos e publica o que estiver na hora. Posts atrasados há mais de 12 h viram "expirado" (não saem todos de uma vez).

## Lembretes
- Nunca edite `queue/fila.csv` no PC; só o robô mexe nele.
- Limite do Instagram: 100 publicações por 24 h. O robô respeita e publica no máximo 6 por execução.
- O token do Instagram (secret `IG_TOKEN`) vence por volta do início de dezembro de 2026. Renove na Meta antes de retomar e atualize o secret no GitHub (Settings > Secrets and variables > Actions).
- Conteúdo pronto e não usado: pasta `_guardado_nao_enviado` ao lado do repositório (192 reels, informativos e tweets novos) e as listas em `conteudo/`.

## Agenda v2 (09/10/2026)
- 30 dias, 2 estáticos + 1 reel/dia (11:45 / 18:45 reel / 20:45). Os 30 posts premium (conteudo/premium.csv, media/info/prem_*.jpg) vêm PRIMEIRO (dias 1–15); depois a lista dos 60 (dias 16–30).
- Regra: nunca dois posts do mesmo estilo de design no mesmo dia (verificada em scripts/build_agenda.py).
- Reels: 11 takes do escritório primeiro (ro03–ro13), depois terno azul e cinza alternados.
- Para refazer: python3 scripts/build_agenda.py (gera queue/plano.csv).
