@echo off
echo.
echo === Apagando o login do GitHub guardado neste computador ===
echo (so o login salvo para o Git; seus repositorios e arquivos nao sao afetados)
echo.
(echo protocol=https& echo host=github.com& echo.) | git credential-manager erase
git credential-manager github logout sinprofran10-a11y
cmdkey /delete:git:https://github.com
cmdkey /delete:LegacyGeneric:target=git:https://github.com
echo.
echo Pronto. Agora de dois cliques em enviar.bat e, quando abrir a janela
echo de login do GitHub, entre com a conta remnotetjsp-hash.
echo.
pause
