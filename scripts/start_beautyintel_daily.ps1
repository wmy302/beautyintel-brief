param(
  [int]$Port = 8001
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

$Python = Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe"
if (-not (Test-Path $Python)) {
  $Python = "py"
}

New-Item -ItemType Directory -Force -Path (Join-Path $ProjectRoot "data") | Out-Null

function Invoke-Python {
  param([string]$Arguments)
  if ($Python -eq "py") {
    & py -3 $Arguments.Split(" ")
  } else {
    & $Python $Arguments.Split(" ")
  }
}

function Start-PythonProcess {
  param(
    [string]$Arguments,
    [string]$OutLog,
    [string]$ErrLog
  )

  if ($Python -eq "py") {
    Start-Process -FilePath "py" -ArgumentList "-3 $Arguments" -WorkingDirectory $ProjectRoot -WindowStyle Hidden -RedirectStandardOutput $OutLog -RedirectStandardError $ErrLog | Out-Null
  } else {
    Start-Process -FilePath $Python -ArgumentList $Arguments -WorkingDirectory $ProjectRoot -WindowStyle Hidden -RedirectStandardOutput $OutLog -RedirectStandardError $ErrLog | Out-Null
  }
}

function Test-LocalApi {
  param([int]$ApiPort)
  try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:$ApiPort/health" -UseBasicParsing -TimeoutSec 3
    return $response.StatusCode -eq 200
  } catch {
    return $false
  }
}

Invoke-Python "-m app.cli init-db"

$PortOwner = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $PortOwner) {
  Start-PythonProcess `
    "-m app.run_api --host 127.0.0.1 --port $Port" `
    (Join-Path $ProjectRoot "data\uvicorn8001.out.log") `
    (Join-Path $ProjectRoot "data\uvicorn8001.err.log")
}

$ready = $false
for ($i = 0; $i -lt 10; $i++) {
  Start-Sleep -Seconds 1
  if (Test-LocalApi -ApiPort $Port) {
    $ready = $true
    break
  }
}

if (-not $ready) {
  Write-Host "本地刷新后台没有启动成功。请查看下面的错误信息：" -ForegroundColor Red
  $errLog = Join-Path $ProjectRoot "data\uvicorn8001.err.log"
  if (Test-Path $errLog) {
    Get-Content $errLog -Tail 40
  }
  Write-Host ""
  Write-Host "也可以手动运行：" -ForegroundColor Yellow
  Write-Host "$Python -m app.run_api --host 127.0.0.1 --port $Port"
  exit 1
}

try {
  $Scheduler = Get-CimInstance Win32_Process -Filter "name = 'python.exe' or name = 'py.exe'" |
    Where-Object { $_.CommandLine -like "*app.cli run-scheduler*" } |
    Select-Object -First 1
} catch {
  $Scheduler = $null
  Write-Host "Cannot inspect scheduler process; starting a fresh background scheduler if needed." -ForegroundColor Yellow
}

if (-not $Scheduler) {
  Start-PythonProcess `
    "-m app.cli run-scheduler" `
    (Join-Path $ProjectRoot "data\scheduler.out.log") `
    (Join-Path $ProjectRoot "data\scheduler.err.log")
}

try {
  Start-Process "http://127.0.0.1:$Port/reports/latest/view" | Out-Null
} catch {
  Write-Host "Browser auto-open was blocked. Please open the URL below manually." -ForegroundColor Yellow
}

Write-Host "BeautyIntel local API: http://127.0.0.1:$Port"
Write-Host "Latest report view: http://127.0.0.1:$Port/reports/latest/view"
Write-Host "Daily scheduler is running in the background. Keep Windows signed in for automatic daily refresh."
