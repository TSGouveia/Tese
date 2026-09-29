@echo off
chcp 65001 > nul
cls

echo ========================================================
echo      GERIDOR AUTOMATICO DE TESE (NOVATHESIS)
echo ========================================================
echo.

:: --- PASSO 1: VERIFICACOES DE SEGURANCA ---

:: Verifica se estamos numa pasta git
if not exist .git (
    echo [ERRO] Nao encontro a pasta .git!
    echo Este ficheiro tem de estar dentro da pasta da tua tese.
    pause
    exit /b
)

:: Verifica se ha alteracoes por guardar
git diff-index --quiet HEAD --
if %errorlevel% neq 0 (
    echo.
    echo [!] PERIGO: Tens ficheiros abertos ou nao guardados.
    echo [!] Por favor, faz commit no Git antes de correr este script.
    echo.
    echo O script vai fechar para protecao.
    pause
    exit /b
)

:: --- PASSO 2: SETUP DO UPSTREAM (O TEU PEDIDO) ---

echo [1/4] A verificar configuracao do Upstream...

:: Procura se o remote "upstream" ja existe
git remote | findstr "upstream" > nul
if %errorlevel% neq 0 (
    echo     - Upstream nao detetado. A configurar agora...
    git remote add upstream https://github.com/joaomlourenco/novathesis.git
    echo     - Configurado com sucesso para: joaomlourenco/novathesis
) else (
    echo     - O Upstream ja estava configurado. A continuar.
)

:: --- PASSO 3: ATUALIZACAO ---

echo.
echo [2/4] A mudar para a branch 'main'...
git checkout main > nul 2>&1

echo.
echo [3/4] A ir buscar as novidades ao servidor (Fetch)...
git fetch upstream
if %errorlevel% neq 0 (
    echo [ERRO] Nao consegui ligar a internet ou ao GitHub.
    pause
    exit /b
)

echo.
echo [4/4] A fundir as novidades na tua tese (Merge)...
git merge upstream/main

:: --- PASSO 4: GESTAO DE RESULTADO ---

if %errorlevel% neq 0 (
    echo.
    echo ########################################################
    echo [!] CONFLITO DETETADO [!]
    echo ########################################################
    echo O Git nao conseguiu juntar tudo automaticamente.
    echo (Provavelmente mexeste na mesma linha que o autor do template).
    echo.
    echo O QUE FAZER:
    echo 1. Abre o VS Code.
    echo 2. Resolve os ficheiros com exclamacao vermelha.
    echo 3. Faz o commit manual.
    echo.
    pause
    exit /b
)

:: Se chegou aqui, correu tudo bem
echo.
echo ========================================================
echo  SUCESSO! A tua tese esta atualizada e sincronizada.
echo  A enviar copia de seguranca para o teu GitHub (Origin)...
echo ========================================================
git push origin main

echo.
pause