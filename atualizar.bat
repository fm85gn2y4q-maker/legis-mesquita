@echo off
REM Rotina semanal da legislacao de Mesquita, para o Agendador de Tarefas.
REM
REM Usa o Python do proprio projeto (.venv), nao o do PATH: o do sistema pode
REM mudar de versao sem aviso, e o do projeto tem as dependencias fixadas.
REM
REM Nao publica nada. Deixa o relatorio em dist\diferenca-<data>.md e o acervo
REM novo em dados\staging.sqlite, para alguem olhar.

setlocal
cd /d "%~dp0"
set PYTHONUTF8=1

set REGISTRO=dist\ultima-atualizacao.log
if not exist dist mkdir dist

echo ============================================================ >> "%REGISTRO%"
echo Inicio: %DATE% %TIME% >> "%REGISTRO%"

".venv\Scripts\python.exe" atualizar.py >> "%REGISTRO%" 2>&1
set RESULTADO=%ERRORLEVEL%

echo Fim: %DATE% %TIME%  (codigo %RESULTADO%) >> "%REGISTRO%"

REM 0 = nada exige leitura - 1 = ha o que ler - 2 = falhou
exit /b %RESULTADO%
