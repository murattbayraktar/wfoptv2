<#
.SYNOPSIS
    WFOpt gelistirme sunucularini yonetir.
.EXAMPLE
    .\dev.ps1           # varsayilan: start
    .\dev.ps1 start
    .\dev.ps1 stop
    .\dev.ps1 restart
    .\dev.ps1 status
#>
param(
    [Parameter(Position = 0)]
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string]$Action = 'start'
)

$Root     = $PSScriptRoot
$ApiDir   = Join-Path $Root 'bank_forecast'
$FrontDir = Join-Path $Root 'bank_forecast\frontend'
$Uvicorn  = Join-Path $ApiDir 'venv\Scripts\uvicorn.exe'
$PidFile  = Join-Path $Root '.dev-pids'

function Get-SavedPids {
    if (-not (Test-Path $PidFile)) { return @() }
    return (Get-Content $PidFile -Raw).Trim().Split(',') |
           Where-Object { $_ -match '^\d+$' }
}

function Start-WfServices {
    $saved = Get-SavedPids
    $running = $saved | Where-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue }
    if ($running.Count -gt 0) {
        Write-Host ""
        Write-Host "  Servisler zaten calisıyor (PID: $($running -join ', '))." -ForegroundColor Yellow
        Write-Host "  Yeniden baslatmak icin:  .\dev.ps1 restart" -ForegroundColor DarkGray
        Write-Host ""
        return
    }
    if (Test-Path $PidFile) { Remove-Item $PidFile -Force }

    if (-not (Test-Path $Uvicorn)) {
        Write-Host ""
        Write-Host "  [HATA] Uvicorn bulunamadi: $Uvicorn" -ForegroundColor Red
        Write-Host "  venv olusturup pip install -r requirements.txt calistirin." -ForegroundColor DarkGray
        Write-Host ""
        return
    }

    $apiArgs = @(
        '-NoExit', '-Command',
        "`$Host.UI.RawUI.WindowTitle = 'WFOpt API :8000'; " +
        "Set-Location '$ApiDir'; " +
        "& '$Uvicorn' api.main:app --reload --port 8000"
    )
    $apiProc = Start-Process powershell -ArgumentList $apiArgs -PassThru

    $feArgs = @(
        '-NoExit', '-Command',
        "`$Host.UI.RawUI.WindowTitle = 'WFOpt Frontend :5173'; " +
        "Set-Location '$FrontDir'; " +
        "npm run dev"
    )
    $feProc = Start-Process powershell -ArgumentList $feArgs -PassThru

    "$($apiProc.Id),$($feProc.Id)" | Out-File $PidFile -Encoding utf8 -NoNewline

    Write-Host ""
    Write-Host "  Servisler baslatildi" -ForegroundColor Green
    Write-Host "  API       -> http://localhost:8000  (PID $($apiProc.Id))" -ForegroundColor Cyan
    Write-Host "  Frontend  -> http://localhost:5173  (PID $($feProc.Id))" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Durdurmak icin:  .\dev.ps1 stop" -ForegroundColor DarkGray
    Write-Host ""
}

function Stop-WfServices {
    $pids = Get-SavedPids
    if ($pids.Count -eq 0) {
        Write-Host ""
        Write-Host "  Calisir durumda kayitli servis yok." -ForegroundColor Yellow
        Write-Host ""
        return
    }
    Write-Host ""
    foreach ($p in $pids) {
        $proc = Get-Process -Id $p -ErrorAction SilentlyContinue
        if ($proc) {
            & taskkill /PID $p /T /F 2>$null | Out-Null
            Write-Host "  Durduruldu  PID $p  ($($proc.ProcessName))" -ForegroundColor Red
        } else {
            Write-Host "  Zaten durmustu  PID $p" -ForegroundColor DarkGray
        }
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    Write-Host "  Tum servisler durduruldu." -ForegroundColor Green
    Write-Host ""
}

function Get-WfStatus {
    $pids = Get-SavedPids
    Write-Host ""
    if ($pids.Count -eq 0) {
        Write-Host "  Kayitli servis yok." -ForegroundColor Yellow
        Write-Host ""
        return
    }
    foreach ($p in $pids) {
        $proc = Get-Process -Id $p -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "  CALISIYOR   PID $p   $($proc.ProcessName)" -ForegroundColor Green
        } else {
            Write-Host "  DURMUS      PID $p   (surec bulunamadi)" -ForegroundColor Red
        }
    }
    Write-Host ""
}

switch ($Action) {
    'start'   { Start-WfServices }
    'stop'    { Stop-WfServices }
    'restart' { Stop-WfServices; Start-Sleep -Milliseconds 800; Start-WfServices }
    'status'  { Get-WfStatus }
}
