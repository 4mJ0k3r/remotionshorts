# Gracefully stop only classroom_fart runners registered by our launcher.
# Never touches another project, an idle Blender GUI, or a foreign GPU lock.
$ErrorActionPreference = 'Stop'
$registryDir = 'D:\remotionshorts\renders\classroom_fart\logs'
[IO.File]::WriteAllText((Join-Path $registryDir 'stop_preview.request'), 'stop requested by user')
$records = @(Get-ChildItem -LiteralPath $registryDir -Filter 'active_run_*.json' -File)
$requested = 0
foreach ($record in $records) {
    $run = Get-Content -LiteralPath $record.FullName -Raw | ConvertFrom-Json
    if ($run.project -ne 'classroom_fart') { continue }
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $($run.pid)" -ErrorAction SilentlyContinue
    if (-not $process -or $process.CommandLine -notlike '*classroom_fart*run_blender.py*') { continue }
    $stopTarget = [IO.Path]::GetFullPath([string]$run.stop_file)
    if ([IO.Path]::GetDirectoryName($stopTarget) -ne $registryDir) { throw 'Refusing a stop request outside our project log directory.' }
    [IO.File]::WriteAllText($stopTarget, 'stop requested by user')
    $requested++
}
if ($requested -eq 0) { Write-Output 'No active classroom_fart render or queue is registered.' }
else { Write-Output "Requested a safe stop for $requested classroom_fart job(s). The launcher stops its own child PID and releases only its own GPU lock." }
