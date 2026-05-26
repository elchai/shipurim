# Stop the running realtime transcription session.
# Touches the stop flag file; waits up to 5s for graceful exit; force-kills if needed.

$ErrorActionPreference = 'Stop'

$tempDir  = [System.IO.Path]::GetTempPath().TrimEnd('\','/')
$pidFile  = Join-Path $tempDir 'realtime-transcribe.pid'
$stopFile = Join-Path $tempDir 'realtime-transcribe.stop'

if (-not (Test-Path $pidFile)) {
    Write-Output 'No active transcription found.'
    exit 0
}

$pidValue = (Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
if (-not $pidValue) {
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    Write-Output 'Empty PID file removed.'
    exit 0
}

$proc = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
if (-not $proc) {
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    Write-Output 'Transcription process not running (stale PID file removed).'
    exit 0
}

# Signal graceful stop
New-Item -ItemType File -Path $stopFile -Force | Out-Null

# Wait up to 5 seconds
for ($i = 0; $i -lt 10; $i++) {
    Start-Sleep -Milliseconds 500
    if (-not (Get-Process -Id $pidValue -ErrorAction SilentlyContinue)) { break }
}

# Force kill if still alive
$alive = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
if ($alive) {
    try { Stop-Process -Id $pidValue -Force -ErrorAction Stop } catch {}
}

Remove-Item $pidFile  -Force -ErrorAction SilentlyContinue
Remove-Item $stopFile -Force -ErrorAction SilentlyContinue

Write-Output 'Transcription stopped.'
