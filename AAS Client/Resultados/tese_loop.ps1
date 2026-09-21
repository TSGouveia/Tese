# tese_loop.ps1
# Pede o nome do teste, abre TESE.exe, aguarda encerramento automatico (ou fecha por timeout) — repete N vezes

# ============================================================================
#  CONFIGURAÇÃO
# ============================================================================
$shortcutPath  = "C:\Users\LazyT\Desktop\TESE.exe - Atalho.lnk"
$baseDir       = "C:\Users\LazyT\Desktop\Resultados"
$totalRuns     = 100
$waitSeconds   = 1200

# ============================================================================
#  PEDIR NOME DO TESTE
# ============================================================================
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "             TESE - Loop de Testes          " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$testName = ""
while ([string]::IsNullOrWhiteSpace($testName)) {
    $testName = Read-Host "  Nome do teste (ex: baseline, sem_shader, com_lod)"
    if ([string]::IsNullOrWhiteSpace($testName)) {
        Write-Host "  [ERRO] O nome do teste nao pode estar vazio!" -ForegroundColor Red
    }
}

# Sanitizar o nome (remover caracteres inválidos para nomes de pasta)
$testName = $testName.Trim() -replace '[\\/:*?"<>|]', '_'

# Criar pasta para este teste
$testDir = Join-Path $baseDir $testName
if (-not (Test-Path $testDir)) {
    New-Item -ItemType Directory -Path $testDir | Out-Null
    Write-Host "  [OK] Pasta criada: $testDir" -ForegroundColor Green
} else {
    Write-Host "  [INFO] Pasta ja existe: $testDir" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  Teste:        $testName"
Write-Host "  Runs:         $totalRuns"
Write-Host "  Timeout:      ${waitSeconds}s"
Write-Host "  Pasta:        $testDir"
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
#  LOOP PRINCIPAL
# ============================================================================
for ($i = 1; $i -le $totalRuns; $i++) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    Write-Host "=== Execucao $i / $totalRuns === ($timestamp)"

    # 1. Abrir a app pelo atalho
    Write-Host "  Abrindo TESE.exe..."
    $proc = Start-Process -FilePath $shortcutPath -PassThru

    # 2. Aguardar que o processo termine sozinho (ate ao timeout estipulado)
    Write-Host "  Aguardando encerramento automatico (maximo ${waitSeconds}s)..."
    $elapsed = 0
    $checkInterval = 2

    while ($elapsed -lt $waitSeconds) {
        Start-Sleep -Seconds $checkInterval
        $elapsed += $checkInterval

        $teseRunning = Get-Process -Name "TESE" -ErrorAction SilentlyContinue
        if (-not $teseRunning) {
            Write-Host "  [OK] TESE encerrou sozinho apos ${elapsed}s." -ForegroundColor Green
            break
        }
    }

    # 3. Se ainda estiver aberto apos o timeout, forcar fecho (kill)
    $teseProcesses = Get-Process -Name "TESE" -ErrorAction SilentlyContinue
    if ($teseProcesses) {
        Write-Host "  [AVISO] Tempo limite atingido (${waitSeconds}s). Fechando TESE.exe..." -ForegroundColor Yellow
        foreach ($p in $teseProcesses) {
            $p.CloseMainWindow() | Out-Null
        }
        Start-Sleep -Seconds 1
        $teseProcesses = Get-Process -Name "TESE" -ErrorAction SilentlyContinue
        if ($teseProcesses) {
            try {
                $teseProcesses | Stop-Process -Force -ErrorAction Stop
                Write-Host "  (Forcou encerramento via Stop-Process)"
            } catch {
                Write-Host "  (Stop-Process falhou, a usar taskkill...)"
                taskkill /F /IM "TESE.exe" 2>$null | Out-Null
            }
        }
    }

    # Pequena pausa entre iterações
    Start-Sleep -Seconds 1
    Write-Host "  Concluido!`n"
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Todas as $totalRuns execucoes concluidas!" -ForegroundColor Green
Write-Host "  Teste: $testName" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Para extrair os tempos, executa:" -ForegroundColor Cyan
Write-Host "  python extrair_tempos.py `"$testName`"" -ForegroundColor White
Write-Host ""

# ============================================================================
#  NOTIFICAÇÃO NTFY
# ============================================================================
Write-Host "Enviando notificacao para ntfy (lazysan)..." -ForegroundColor Cyan
try {
    Invoke-RestMethod -Uri "https://ntfy.sh/lazysan" `
        -Method Post `
        -Body "O loop de testes '$testName' ($totalRuns execucoes) terminou com sucesso!" `
        -Headers @{
            Title    = "TESE - Testes Concluidos"
            Priority = "default"
            Tags     = "white_check_mark,hourglass_done"
        } | Out-Null
    Write-Host "  [OK] Notificacao enviada com sucesso!" -ForegroundColor Green
} catch {
    Write-Host "  [AVISO] Nao foi possivel enviar a notificacao ntfy: $_" -ForegroundColor Yellow
}

