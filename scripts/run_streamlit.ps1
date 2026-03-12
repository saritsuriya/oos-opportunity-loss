[CmdletBinding()]
param(
    [string]$ProjectRoot = (Join-Path $PSScriptRoot ".."),
    [string]$PythonExe = "",
    [string]$BindAddress = "0.0.0.0",
    [int]$Port = 8501,
    [string]$PublicHostName = $env:COMPUTERNAME
)

$ErrorActionPreference = "Stop"
$resolvedProjectRoot = (Resolve-Path $ProjectRoot).Path
$configPath = Join-Path $resolvedProjectRoot ".streamlit\config.toml"
$appEntrypoint = Join-Path $resolvedProjectRoot "streamlit_app\app.py"

if (-not (Test-Path $configPath)) {
    throw "Missing Streamlit config: $configPath"
}

if (-not (Test-Path $appEntrypoint)) {
    throw "Missing Streamlit app entrypoint: $appEntrypoint"
}

if (-not $PythonExe) {
    $venvPython = Join-Path $resolvedProjectRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $PythonExe = $venvPython
    } else {
        $PythonExe = "python"
    }
}

Set-Location $resolvedProjectRoot

$streamlitArgs = @(
    "-m",
    "streamlit",
    "run",
    $appEntrypoint,
    "--server.address",
    $BindAddress,
    "--server.port",
    "$Port",
    "--server.headless",
    "true"
)

if ($PublicHostName) {
    $streamlitArgs += @(
        "--browser.serverAddress",
        $PublicHostName,
        "--browser.serverPort",
        "$Port"
    )
}

Write-Host "Starting Streamlit app from $appEntrypoint"
if ($PublicHostName) {
    Write-Host "Expected internal URL: http://$PublicHostName`:$Port/"
}

& $PythonExe @streamlitArgs
exit $LASTEXITCODE
