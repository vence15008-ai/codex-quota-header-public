$ErrorActionPreference = 'Stop'
$desktopDir = [Environment]::GetFolderPath('Desktop')
$shell = New-Object -ComObject WScript.Shell
foreach ($entry in @(
    @{Name='Codex Quota Header.lnk';Args='-Action Start'},
    @{Name='Stop Codex Quota Header.lnk';Args='-Action Stop'},
    @{Name='Restore Codex Quota Float.lnk';Args='-Action Rollback'}
)) {
    $linkFile = Join-Path $desktopDir $entry.Name
    if (Test-Path -LiteralPath $linkFile) {
        $existing = $shell.CreateShortcut($linkFile)
        $managePath = Join-Path $PSScriptRoot 'manage.ps1'
        if (!$existing.Arguments.Contains($managePath)) { throw ('Unrelated desktop shortcut: ' + $linkFile) }
        $backupDir = Join-Path $PSScriptRoot 'runtime'
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
        Copy-Item -LiteralPath $linkFile -Destination (Join-Path $backupDir ([DateTime]::UtcNow.Ticks.ToString() + '-' + $entry.Name))
    }
    $shortcut = $shell.CreateShortcut($linkFile)
    $shortcut.TargetPath = (Get-Command powershell.exe).Source
    $shortcut.Arguments = '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + (Join-Path $PSScriptRoot 'manage.ps1') + '" ' + $entry.Args
    $shortcut.WorkingDirectory = $PSScriptRoot
    $shortcut.WindowStyle = 7
    $shortcut.Save()
    Write-Output $linkFile
}
