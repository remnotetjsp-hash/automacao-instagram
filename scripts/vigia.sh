#!/bin/bash
# Vigia do publicador: roda o robô a cada 4 minutos durante ~5h40 e, no fim, dispara a próxima execução.
# O cron do GitHub sozinho atrasa ou pula horários; workflow_dispatch feito com o GITHUB_TOKEN cria uma
# execução nova, então a vigia se encadeia sozinha, sem depender de navegador ou computador ligado.
git config user.name "publicador"
git config user.email "publicador@users.noreply.github.com"
FIM=$(( $(date +%s) + ${DURACAO_MIN:-340} * 60 ))
salvar() {
  git add queue/fila.csv
  git add queue/metricas.csv queue/metricas_conta.csv 2>/dev/null || true
  if ! git diff --cached --quiet; then
    git commit -q -m "status da fila"
    for i in 1 2 3; do git pull --rebase --autostash -q origin main && git push -q origin HEAD:main && break; sleep 5; done
  fi
}
while [ "$(date +%s)" -lt "$FIM" ]; do
  git pull --rebase --autostash -q origin main || true
  python3 scripts/publish.py || echo "robô falhou nesta volta"
  python3 scripts/metricas.py || true
  salvar
  sleep 240
done
curl -s -o /dev/null -w "próxima execução: HTTP %{http_code}\n" -X POST \
  -H "Authorization: Bearer $GH_TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/workflows/publish.yml/dispatches" -d '{"ref":"main"}'
