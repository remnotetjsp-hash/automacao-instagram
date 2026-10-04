@echo off
setlocal
cd /d "%~dp0"
echo.
echo === Enviando midias e fila para o GitHub ===
echo.

where git >nul 2>nul
if errorlevel 1 (
  echo O Git nao esta instalado neste computador.
  echo Baixe e instale em: https://git-scm.com/download/win
  echo Depois de instalar, de dois cliques neste arquivo de novo.
  pause
  exit /b 1
)

if not exist ".git" (
  echo Primeira vez: ligando esta pasta ao repositorio...
  git init -b main
  git remote add origin https://github.com/remnotetjsp-hash/automacao-instagram.git
  git fetch origin
  if errorlevel 1 goto erro
  git reset --hard origin/main
  if errorlevel 1 goto erro
  git branch --set-upstream-to=origin/main main
)

git config user.name "Guedes e Cruz"
git config user.email "remnotetjsp-hash@users.noreply.github.com"

echo Buscando o que o publicador ja atualizou no GitHub...
git pull --rebase --autostash origin main
if errorlevel 1 goto erro

git add -A
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "novas midias e fila"
  if errorlevel 1 goto erro
) else (
  echo Nada novo para enviar.
)

echo Enviando...
git push origin main
if errorlevel 1 goto erro

echo.
echo === Pronto! Tudo enviado. ===
pause
exit /b 0

:erro
echo.
echo Algo deu errado. Tire um print desta janela e me envie.
pause
exit /b 1
