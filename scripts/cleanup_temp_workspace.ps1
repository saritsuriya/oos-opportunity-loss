[CmdletBinding()]
param(
    [string]$ProjectRoot = (Join-Path $PSScriptRoot ".."),
    [string]$PythonExe = "",
    [double]$MaxAgeHours = 24,
    [string]$WorkspaceBaseDir = "",
    [string]$NowIso = ""
)

$ErrorActionPreference = "Stop"
$resolvedProjectRoot = (Resolve-Path $ProjectRoot).Path
$cleanupScript = Join-Path $resolvedProjectRoot "scripts\cleanup_temp_workspace.py"

if (-not (Test-Path $cleanupScript)) {
    throw "Missing cleanup script: $cleanupScript"
}

if (-not $PythonExe) {
    $venvPython = Join-Path $resolvedProjectRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $PythonExe = $venvPython
    } else {
        $PythonExe = "python"
    }
}

$cleanupArgs = @(
    $cleanupScript,
    "--max-age-hours",
    "$MaxAgeHours"
)

if ($WorkspaceBaseDir) {
    $cleanupArgs += @("--base-dir", $WorkspaceBaseDir)
}

if ($NowIso) {
    $cleanupArgs += @("--now-iso", $NowIso)
}

& $PythonExe @cleanupArgs
exit $LASTEXITCODE
