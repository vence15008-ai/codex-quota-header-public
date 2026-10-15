param(
    [ValidateSet('Start','Stop','Rollback','Status','Doctor','InstallStartup','RemoveStartup','Uninstall')]
    [string]$Action = 'Start',
    [switch]$RestartCodex,
    [ValidateRange(0,30)][int]$LaunchDelaySeconds = 0,
    [ValidateRange(1024,65535)][int]$Port = $(if ($env:CODEX_QUOTA_CDP_PORT) { [int]$env:CODEX_QUOTA_CDP_PORT } else { 9222 })
)
$ErrorActionPreference = 'Stop'
if ($LaunchDelaySeconds) { Start-Sleep -Seconds $LaunchDelaySeconds }
$quotaRoot = $PSScriptRoot
$runtimeDir = Join-Path $quotaRoot 'runtime'
New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null
$launcherLog = Join-Path $runtimeDir 'launcher.log'
trap {
    $detail = $_.Exception.Message
    [IO.File]::AppendAllText($launcherLog, ([DateTime]::UtcNow.ToString('o') + ' ERROR ' + $detail + [Environment]::NewLine))
    Write-Error -Message $detail -ErrorAction Continue
    exit 1
}
if ($Action -eq 'Start') {
    [IO.File]::AppendAllText($launcherLog, ([DateTime]::UtcNow.ToString('o') + ' START requested; never closes an existing Codex window' + [Environment]::NewLine))
    if ($RestartCodex) {
        throw 'Automatic Codex restart is disabled. Quit Codex manually, then run Start without -RestartCodex.'
    }
}
function Find-Runtime([string]$Override, [string]$Name, [string]$Fallback) {
    if ($Override) {
        if (!(Test-Path -LiteralPath $Override -PathType Leaf) -or [IO.Path]::GetExtension($Override) -ne '.exe') {
            throw ('Invalid native executable override for ' + $Name)
        }
        return (Resolve-Path -LiteralPath $Override).Path
    }
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command -and $command.Source -notlike '*\WindowsApps\*') { return $command.Source }
    if ($Fallback -and (Test-Path -LiteralPath $Fallback -PathType Leaf)) { return $Fallback }
    throw ($Name + ' not found. Install Node >=22 / Python >=3.10 or set CODEX_QUOTA_NODE / CODEX_QUOTA_PYTHON.')
}
$bridgeFile = Join-Path $quotaRoot 'cdp_bridge.cjs'
$pidFile = Join-Path $runtimeDir 'bridge.pid'
$startupDir = [Environment]::GetFolderPath('Startup')
$startupFile = Join-Path $startupDir 'Codex Quota Header.lnk'

function Get-Bridge {
    if (!(Test-Path -LiteralPath $pidFile)) { return $null }
    $bridgePid = 0
    if (![int]::TryParse((Get-Content -LiteralPath $pidFile -Raw).Trim(), [ref]$bridgePid) -or $bridgePid -le 0) { return $null }
    $candidate = Get-CimInstance Win32_Process -Filter "ProcessId=$bridgePid"
    if ($candidate -and $candidate.Name -eq 'node.exe' -and $candidate.CommandLine.Contains($bridgeFile)) {
        return $candidate
    }
    return $null
}
function Get-CodexMain {
    Get-CimInstance Win32_Process -Filter "Name='ChatGPT.exe'" | Where-Object {
        $_.ExecutablePath -like '*\OpenAI.Codex_*\app\ChatGPT.exe' -and
        $_.CommandLine -notlike '*--type=*'
    }
}
function Get-CodexPath {
    $running = @(Get-CodexMain)
    if ($running.Count) { return $running[0].ExecutablePath }
    $package = Get-AppxPackage -Name 'OpenAI.Codex' | Sort-Object Version -Descending | Select-Object -First 1
    if (!$package) { throw 'Codex desktop package not found' }
    return Join-Path $package.InstallLocation 'app\ChatGPT.exe'
}
function Assert-OwnedShortcut([string]$File) {
    if (Test-Path -LiteralPath $File) {
        $shell = New-Object -ComObject WScript.Shell
        if (!$shell.CreateShortcut($File).Arguments.Contains((Join-Path $quotaRoot 'manage.ps1'))) {
            throw ('Unrelated shortcut left untouched: ' + $File)
        }
    }
}
function Assert-RuntimeVersions {
    foreach ($spec in @(@{Exe=$nodeExe;Name='node';Minimum=[version]'22.0'}, @{Exe=$pythonExe;Name='python';Minimum=[version]'3.10'})) {
        $outFile = Join-Path $runtimeDir ($spec.Name + '-version.txt')
        $errFile = Join-Path $runtimeDir ($spec.Name + '-version-error.txt')
        $probe = Start-Process -FilePath $spec.Exe -ArgumentList '--version' -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $outFile -RedirectStandardError $errFile
        $versionText = (Get-Content -LiteralPath $outFile -Raw) + (Get-Content -LiteralPath $errFile -Raw)
        if ($probe.ExitCode -ne 0 -or $versionText -notmatch '(\d+\.\d+\.\d+)') { throw ('Cannot check ' + $spec.Name + ' version') }
        if ([version]$Matches[1] -lt $spec.Minimum) { throw ($spec.Name + ' requires >= ' + $spec.Minimum) }
    }
}
function Assert-LocalDebugPort {
    $listeners = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    if (!$listeners.Count) { return $false }
    foreach ($listener in $listeners) {
        if ($listener.LocalAddress -notin @('127.0.0.1','::1')) { throw 'Debug port is not loopback-only; refusing to attach' }
        $ownerProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
        if (!$ownerProcess -or $ownerProcess.ExecutablePath -notlike '*\OpenAI.Codex_*\app\ChatGPT.exe') {
            throw 'Debug port belongs to another application; refusing to attach'
        }
    }
    return $true
}

if ($Action -eq 'Status') {
    [pscustomobject]@{ HelperRunning=[bool](Get-Bridge); DebugPortReady=(Assert-LocalDebugPort); StartupInstalled=(Test-Path -LiteralPath $startupFile) } | Format-List
    if (Test-Path -LiteralPath (Join-Path $runtimeDir 'bridge.log')) { Get-Content -LiteralPath (Join-Path $runtimeDir 'bridge.log') -Tail 6 }
    exit
}
if ($Action -notin @('InstallStartup','RemoveStartup')) {
    $nodeExe = Find-Runtime $env:CODEX_QUOTA_NODE 'node.exe' ''
}
if ($Action -in @('Start','Rollback','Doctor')) {
    $bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    $pythonExe = Find-Runtime $env:CODEX_QUOTA_PYTHON 'python.exe' $bundledPython
    $pythonWindowless = Join-Path (Split-Path $pythonExe) 'pythonw.exe'
}
if ($Action -eq 'Doctor') {
    Assert-RuntimeVersions
    $probe = Start-Process -FilePath $pythonExe -ArgumentList ('"' + (Join-Path $quotaRoot 'account_reader.py') + '" --check') -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput (Join-Path $runtimeDir 'doctor.txt') -RedirectStandardError (Join-Path $runtimeDir 'doctor-error.txt')
    if ($probe.ExitCode) { throw 'Native Codex CLI check failed; see runtime/doctor-error.txt or set CODEX_QUOTA_CODEX' }
    Get-Content -LiteralPath (Join-Path $runtimeDir 'doctor.txt')
    [pscustomobject]@{ CodexDesktop=(Get-CodexPath); Python=$pythonExe; Node=$nodeExe; DebugPortReady=(Assert-LocalDebugPort); HelperRunning=[bool](Get-Bridge) }
    Write-Output 'Doctor does not start or close Codex, request quota, or modify startup.'
    exit
}
if ($Action -eq 'InstallStartup') {
    if (!(Assert-LocalDebugPort) -or !(Get-Bridge) -or
        !((Get-Content -LiteralPath (Join-Path $runtimeDir 'bridge.log') -Tail 1 -ErrorAction SilentlyContinue) -like 'Quota header mounted*')) {
        throw 'Confirm the native header is mounted before replacing startup'
    }
    Assert-OwnedShortcut $startupFile
    # Preserve the original shortcut outside Startup so only one mode starts.
    $oldShortcut = Join-Path $startupDir 'Codex Quota Widget.lnk'
    $backupShortcut = Join-Path $runtimeDir 'Codex Quota Widget.lnk'
    if (Test-Path -LiteralPath $oldShortcut) {
        if (Test-Path -LiteralPath $backupShortcut) { throw 'Existing shortcut backup found; inspect before replacing' }
        $shell = New-Object -ComObject WScript.Shell
        $legacy = $shell.CreateShortcut($oldShortcut)
        if (!$legacy.Arguments.Contains($quotaRoot) -and !$legacy.TargetPath.StartsWith($quotaRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
            throw 'A legacy startup shortcut from another directory exists; disable it manually before installing this startup.'
        }
        Move-Item -LiteralPath $oldShortcut -Destination $backupShortcut
    }
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($startupFile)
    $shortcut.TargetPath = (Get-Command powershell.exe).Source
    $shortcut.Arguments = '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + (Join-Path $quotaRoot 'manage.ps1') + '" -Action Start -Port ' + $Port
    $shortcut.WorkingDirectory = $quotaRoot
    $shortcut.WindowStyle = 7
    $shortcut.Save()
    Write-Output 'Embedded header startup installed; original shortcut backed up in runtime'
    exit
}
if ($Action -in @('Rollback','RemoveStartup','Uninstall')) {
    Assert-OwnedShortcut $startupFile
    if (Test-Path -LiteralPath $startupFile) {
        # Move, rather than delete, for a recoverable rollback.
        Move-Item -LiteralPath $startupFile -Destination (Join-Path $runtimeDir ('header-shortcut-' + [DateTime]::Now.ToString('yyyyMMdd-HHmmss') + '.lnk'))
    }
    $backupShortcut = Join-Path $runtimeDir 'Codex Quota Widget.lnk'
    $oldShortcut = Join-Path $startupDir 'Codex Quota Widget.lnk'
    if ((Test-Path -LiteralPath $backupShortcut) -and !(Test-Path -LiteralPath $oldShortcut)) {
        Move-Item -LiteralPath $backupShortcut -Destination $oldShortcut
    }
    if ($Action -eq 'RemoveStartup') { exit }
}
if ($Action -in @('Stop','Rollback','Uninstall')) {
    $bridge = Get-Bridge
    if ($bridge) {
        [IO.File]::WriteAllText((Join-Path $runtimeDir 'stop'), 'stop')
        # Give the helper and quota child a chance to stop normally first.
        Wait-Process -Id $bridge.ProcessId -Timeout 10 -ErrorAction SilentlyContinue
        $remainingBridge = Get-Bridge
        if ($remainingBridge) {
            # Exact verified helper tree only; never kill all Python/Node/Codex.
            Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\taskkill.exe') -ArgumentList @('/PID', $remainingBridge.ProcessId, '/T', '/F') -WindowStyle Hidden -Wait
        }
    }
    # Stop reinjection BEFORE removing the DOM (otherwise the helper can race us).
    $env:CODEX_QUOTA_CDP_PORT = "$Port"
    if (Assert-LocalDebugPort) {
        $cleanup = Start-Process -FilePath $nodeExe -ArgumentList ('"' + $bridgeFile + '" --remove') -WorkingDirectory $quotaRoot -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput (Join-Path $runtimeDir 'cleanup.log') -RedirectStandardError (Join-Path $runtimeDir 'cleanup-error.log')
        if ($cleanup.ExitCode) { throw 'Helper stopped, but DOM cleanup failed; manually relaunch Codex normally.' }
    }
    if ($Action -eq 'Uninstall') {
        $shell = New-Object -ComObject WScript.Shell
        foreach ($name in @('Codex Quota Header.lnk','Restore Codex Quota Float.lnk','Stop Codex Quota Header.lnk')) {
            $file = Join-Path ([Environment]::GetFolderPath('Desktop')) $name
            if ((Test-Path -LiteralPath $file) -and $shell.CreateShortcut($file).Arguments.Contains((Join-Path $quotaRoot 'manage.ps1'))) {
                Move-Item -LiteralPath $file -Destination (Join-Path $runtimeDir ([DateTime]::UtcNow.Ticks.ToString() + '-' + $name))
            }
        }
        Write-Output 'Own shortcuts archived in runtime; helper stopped. Source and local data retained. Relaunch Codex normally to close its debug port.'
        exit
    }
    if ($Action -eq 'Stop') {
        Write-Output 'Header helper stopped and component removed; startup setting unchanged. Relaunch Codex normally to close its debug port.'
        exit
    }
    if (!(Test-Path -LiteralPath $pythonWindowless)) { throw 'Legacy floating widget requires pythonw.exe and Tk; embedded mode does not.' }
    $floating = @(Get-CimInstance Win32_Process | Where-Object {
        $_.Name -like 'python*' -and $_.CommandLine -and $_.CommandLine.Contains((Join-Path $quotaRoot 'codex_quota_widget.py'))
    })
    if (!$floating.Count) {
        Start-Process -FilePath $pythonWindowless -ArgumentList ('"' + (Join-Path $quotaRoot 'codex_quota_widget.py') + '"') -WorkingDirectory $quotaRoot -WindowStyle Hidden
    }
    Write-Output 'Original floating widget restored. Quit Codex and relaunch normally to close its debug port.'
    exit
}

$codexExe = Get-CodexPath
Assert-RuntimeVersions
if (!(Assert-LocalDebugPort)) {
    if (@(Get-CodexMain).Count) {
        throw 'Codex is running without a debug port; it was left untouched. Quit Codex fully, including its tray process, then run Start again.'
    }
    # Codex is the interactive app, not a background helper. Show it normally.
    Start-Process -FilePath $codexExe -ArgumentList @('--remote-debugging-address=127.0.0.1', "--remote-debugging-port=$Port") -WindowStyle Normal
    $deadline = [DateTime]::UtcNow.AddSeconds(25)
    while (!(Assert-LocalDebugPort) -and [DateTime]::UtcNow -lt $deadline) { Start-Sleep -Milliseconds 500 }
    if (!(Assert-LocalDebugPort)) { throw 'Codex did not expose the loopback debug port; old floating widget remains available' }
}
if (Get-Bridge) { Write-Output 'Header helper already running'; exit }
if (Test-Path -LiteralPath (Join-Path $runtimeDir 'stop')) {
    Move-Item -LiteralPath (Join-Path $runtimeDir 'stop') -Destination (Join-Path $runtimeDir ('stop-' + [DateTime]::Now.Ticks))
}
$env:CODEX_QUOTA_PYTHON = $pythonExe
$env:CODEX_QUOTA_CDP_PORT = "$Port"
$child = Start-Process -FilePath $nodeExe -ArgumentList ('"' + $bridgeFile + '"') -WorkingDirectory $quotaRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeDir 'bridge.log') -RedirectStandardError (Join-Path $runtimeDir 'bridge-error.log')
[IO.File]::WriteAllText($pidFile, [string]$child.Id)
$mountDeadline = [DateTime]::UtcNow.AddSeconds(25)
$mounted = $false
do {
    $mounted = [bool](Select-String -LiteralPath (Join-Path $runtimeDir 'bridge.log') -Pattern '^Quota header mounted' -Quiet -ErrorAction SilentlyContinue)
    if (!$mounted) { Start-Sleep -Milliseconds 500 }
} while (!$mounted -and [DateTime]::UtcNow -lt $mountDeadline)
if ($mounted) {
    # Hide the previous external UI only after real renderer mount succeeds.
    $copiedFloatingFile = Join-Path $quotaRoot 'codex_quota_widget.py'
    Get-CimInstance Win32_Process | Where-Object {
        $_.Name -like 'python*' -and $_.CommandLine -and
        $_.CommandLine.Contains($copiedFloatingFile)
    } | ForEach-Object {
        Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\taskkill.exe') -ArgumentList @('/PID', $_.ProcessId, '/T', '/F') -WindowStyle Hidden -Wait
    }
    Write-Output 'Native header mounted; previous floating window stopped.'
    Write-Output 'Startup is opt-in: run manage.ps1 -Action InstallStartup after verification.'
} else {
    throw 'Header not mounted within 25 seconds; helper may still be waiting. Original floating widget left running. See runtime/bridge.log, then Stop before retrying.'
}
