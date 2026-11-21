param(
    [Parameter(Mandatory)][ValidateSet('calibration','review','master','check')][string]$Phase,
    [Parameter(Mandatory)][string]$Blender
)

$ErrorActionPreference = 'Stop'
$repo = (Get-Item -LiteralPath (Join-Path $PSScriptRoot '..\..')).FullName
$project = 'billionaire_handkerchief'
$output = Join-Path $repo "renders\$project"
$lock = Join-Path $repo '.blender_gpu.lock'
$owner = [guid]::NewGuid().ToString('N')
$Blender = (Get-Item -LiteralPath $Blender).FullName
$entry = Join-Path $PSScriptRoot 'master_job.py'
$claimed = $false

try {
    while (!$claimed) {
        if ((Test-Path -LiteralPath $lock) -or (Get-Process blender -ErrorAction SilentlyContinue)) {
            Write-Output 'Waiting for the shared Blender GPU lock or active Blender process.'
            Start-Sleep -Seconds 15
            continue
        }
        try {
            $claim = [IO.File]::Open($lock,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
        } catch [IO.IOException] {
            if (!(Test-Path -LiteralPath $lock)) { throw }
            Start-Sleep -Seconds 15
            continue
        }
        $claimed = $true
        try {
            $bytes = [Text.Encoding]::UTF8.GetBytes((@{ project=$project; pid=$PID; owner=$owner; phase=$Phase } | ConvertTo-Json -Compress))
            $claim.Write($bytes,0,$bytes.Length)
        } finally { $claim.Dispose() }
    }

    if ($Phase -eq 'master') {
        $work = Join-Path $output 'master_work_1080p'
        $status = Join-Path $work 'progress.json'
        $fingerprint = Join-Path $work 'master_sha256.txt'
        if ((Test-Path -LiteralPath $status) -and (Test-Path -LiteralPath $fingerprint)) {
            $record = Get-Content -LiteralPath $status -Raw | ConvertFrom-Json
            $actual = (Get-FileHash -LiteralPath (Join-Path $output 'billionaire_handkerchief.blend')).Hash
            $expected = (Get-Content -LiteralPath $fingerprint -Raw).Trim()
            if ($record.state -eq 'complete' -and $record.cuts_done.Count -eq 43 -and $actual -eq $expected) {
                Write-Output 'All 43 segments already exist for this exact Blender master.'
                return
            }
        }
    }

    $args = if ($Phase -eq 'check') { @('-b','--version') } else { @('-b','--factory-startup','--python-exit-code','7','-P',('"'+$entry+'"'),'--',$Phase) }
    $log = Join-Path $output "headless_$Phase.log"
    $errLog = Join-Path $output "headless_$Phase.stderr.log"
    $proc = Start-Process -FilePath $Blender -ArgumentList $args -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput $log -RedirectStandardError $errLog
    Write-Output "Started isolated Blender PID $($proc.Id) for $Phase."
    $proc.WaitForExit()
    if ($proc.ExitCode -ne 0) { throw "Blender $Phase exited $($proc.ExitCode). See $log and $errLog." }
} finally {
    if ($claimed -and (Test-Path -LiteralPath $lock)) {
        try { $record = Get-Content -LiteralPath $lock -Raw | ConvertFrom-Json } catch { $record = $null }
        if ($record.owner -eq $owner) { Remove-Item -LiteralPath $lock }
    }
}
