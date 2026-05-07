param(
  [int]$Port = 8001,
  [string]$Authtoken = "",
  [string]$BasicAuth = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

function Find-Ngrok {
  $cmd = Get-Command ngrok.exe -ErrorAction SilentlyContinue
  if ($cmd -and $cmd.Source -notlike "*\WindowsApps\ngrok.exe") {
    return $cmd.Source
  }

  $local = Get-ChildItem -Path $env:USERPROFILE -Recurse -Filter ngrok.exe -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notlike "*\WindowsApps\ngrok.exe" } |
    Select-Object -First 1

  if ($local) {
    return $local.FullName
  }

  return $null
}

function Test-LocalApi {
  try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/health" -UseBasicParsing -TimeoutSec 3
    return $response.StatusCode -eq 200
  } catch {
    return $false
  }
}

if (-not (Test-LocalApi)) {
  powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\start_beautyintel_daily.ps1") -Port $Port
}

if (-not (Test-LocalApi)) {
  Write-Host "Local BeautyIntel API did not start, so the public tunnel cannot be created." -ForegroundColor Red
  exit 1
}

$Ngrok = Find-Ngrok
if (-not $Ngrok) {
  Write-Host "Could not find a usable ngrok.exe." -ForegroundColor Red
  Write-Host "Install ngrok, then run this script again:"
  Write-Host "1. Open https://ngrok.com/download"
  Write-Host "2. Download the Windows version and unzip ngrok.exe"
  Write-Host "3. Put ngrok.exe in this project folder, or add it to PATH"
  Write-Host ""
  Write-Host "If winget is available, you can also run: winget install ngrok.ngrok"
  exit 1
}

if ($Authtoken) {
  & $Ngrok config add-authtoken $Authtoken | Out-Null
}

$args = @("http", "http://127.0.0.1:$Port")
if ($BasicAuth) {
  $args += "--basic-auth=$BasicAuth"
}

$logOut = Join-Path $ProjectRoot "data\ngrok.out.log"
$logErr = Join-Path $ProjectRoot "data\ngrok.err.log"
Start-Process -FilePath $Ngrok -ArgumentList $args -WorkingDirectory $ProjectRoot -WindowStyle Hidden -RedirectStandardOutput $logOut -RedirectStandardError $logErr | Out-Null

$publicUrl = $null
for ($i = 0; $i -lt 20; $i++) {
  Start-Sleep -Seconds 1
  try {
    $tunnels = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 3
    $publicUrl = ($tunnels.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1).public_url
    if ($publicUrl) {
      break
    }
  } catch {
    continue
  }
}

if (-not $publicUrl) {
  Write-Host "ngrok was started, but no public URL was detected. Check logs:" -ForegroundColor Yellow
  Write-Host $logOut
  Write-Host $logErr
  exit 1
}

Write-Host ""
Write-Host "Public share URL:" -ForegroundColor Green
Write-Host "$publicUrl/reports/latest/view"
Write-Host ""
Write-Host "Send this URL to other people so they can open your latest report."
Write-Host "Your computer, local API, and ngrok must keep running. The URL stops working when ngrok stops."
