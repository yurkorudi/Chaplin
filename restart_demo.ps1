$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
Set-Location -LiteralPath $taskRoot
$listeners = @(Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue)
foreach ($listener in $listeners) {
    $taskProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
    if ($taskProcess.CommandLine -notmatch 'app\.py' -or -not $taskProcess.CommandLine.Contains($taskRoot)) {
        throw 'Port 5000 belongs to another application. It was not stopped.'
    }
    Stop-Process -Id $listener.OwningProcess
}
Start-Process -FilePath (Join-Path $taskRoot 'venv\Scripts\python.exe') -ArgumentList 'app.py' -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskRoot '.local\flask.stdout.log') -RedirectStandardError (Join-Path $taskRoot '.local\flask.stderr.log')
Write-Output 'Chaplin started at http://127.0.0.1:5000'
