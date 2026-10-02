# Reliable local launcher for Social. Prevents stale Django runserver processes on port 8080.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$port = 8080

$listeners = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
foreach ($listener in $listeners) {
    $pidOnPort = $listener.OwningProcess
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$pidOnPort" -ErrorAction SilentlyContinue
    $cmd = if ($proc) { [string]$proc.CommandLine } else { "" }
    $name = if ($proc) { [string]$proc.Name } else { "unknown" }

    if ($cmd -match "manage\.py\s+runserver") {
        Write-Host "Stopping stale Django runserver on port $port (PID $pidOnPort)..." -ForegroundColor Yellow
        Stop-Process -Id $pidOnPort -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
    }
    else {
        Write-Host "Port $port is already used by PID $pidOnPort ($name)." -ForegroundColor Red
        if ($cmd) { Write-Host "Command: $cmd" }
        Write-Host "Not killing it because it is not a Django runserver." -ForegroundColor Red
        exit 1
    }
}

$env:DJANGO_ALLOWED_HOSTS = "127.0.0.1,localhost,192.168.100.28"
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Virtual environment python not found: $python" }

Write-Host "Starting Social on http://127.0.0.1:$port/" -ForegroundColor Green
Write-Host "Using --noreload so VS Code/Django does not leave a second autoreloader process." -ForegroundColor DarkGray
& $python manage.py runserver "0.0.0.0:$port" --noreload
