param(
    [string]$HostName = "",
    [string]$HostAlias = "dt4n-aws",
    [string]$User = "ubuntu",
    [string]$SourceKey = "",
    [string]$TargetKeyName = "dt4n-aws.pem"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($SourceKey)) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $SourceKey = Join-Path (Split-Path -Parent $ScriptDir) "dt4n-aws.pem"
}

$SshDir = Join-Path $env:USERPROFILE ".ssh"
$TargetKey = Join-Path $SshDir $TargetKeyName
$ConfigPath = Join-Path $SshDir "config"

New-Item -ItemType Directory -Force $SshDir | Out-Null

if (!(Test-Path $SourceKey)) {
    throw "Khong thay private key: $SourceKey"
}

if (Test-Path $TargetKey) {
    icacls $TargetKey /grant:r "$($env:USERNAME):(F)" | Out-Null
}

Copy-Item -Force $SourceKey $TargetKey

icacls $TargetKey /inheritance:r | Out-Null
icacls $TargetKey /grant:r "$($env:USERNAME):(R)" | Out-Null

if ([string]::IsNullOrWhiteSpace($HostName)) {
    $HostName = "REPLACE_WITH_EC2_PUBLIC_IP"
}

$IdentityFile = $TargetKey.Replace("\", "/")
$QuotedIdentityFile = '"' + $IdentityFile + '"'
$Entry = @"
Host $HostAlias
    HostName $HostName
    User $User
    IdentityFile $QuotedIdentityFile
    IdentitiesOnly yes
    ServerAliveInterval 60
    ServerAliveCountMax 5
    StrictHostKeyChecking accept-new

"@

$Existing = ""
if (Test-Path $ConfigPath) {
    $Existing = Get-Content -Raw $ConfigPath
}

$Pattern = "(?ms)^Host\s+$([regex]::Escape($HostAlias))\s*$.*?(?=^Host\s+|\z)"
if ($Existing -match $Pattern) {
    $NewConfig = [regex]::Replace($Existing, $Pattern, $Entry.TrimEnd() + "`r`n`r`n")
} else {
    if ($Existing.Length -gt 0 -and !$Existing.EndsWith("`n")) {
        $Existing += "`r`n"
    }
    $NewConfig = $Existing + $Entry
}

Set-Content -Path $ConfigPath -Value $NewConfig -Encoding ascii

Write-Host "Windows SSH key: $TargetKey"
Write-Host "Windows SSH config: $ConfigPath"
Write-Host "VS Code Remote-SSH host: $HostAlias"
Write-Host "HostName: $HostName"

if ($HostName -eq "REPLACE_WITH_EC2_PUBLIC_IP") {
    Write-Host "Sau khi terraform apply co IP, chay lai script nay voi -HostName EC2_PUBLIC_IP."
} else {
    Write-Host "Test SSH bang: ssh $HostAlias"
}
