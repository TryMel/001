#Requires -RunAsAdministrator
$ErrorActionPreference = "Stop"

$ruleName = "AkashaDevelopmentMobileLAN"
$existingRule = Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue
if ($existingRule) {
    Write-Host "La regle Akasha LAN existe deja."
    return
}

$profiles = @(
    Get-NetConnectionProfile |
        Where-Object { $_.IPv4Connectivity -ne "Disconnected" } |
        Select-Object -ExpandProperty NetworkCategory -Unique
)

if ($profiles.Count -eq 0) {
    throw "Aucun profil reseau actif n'a ete trouve."
}

New-NetFirewallRule `
    -Name $ruleName `
    -DisplayName "Akasha mobile dev (sous-reseau local uniquement)" `
    -Description "Autorise l'API et Expo uniquement depuis le sous-reseau local." `
    -Direction Inbound `
    -Action Allow `
    -Enabled True `
    -Profile $profiles `
    -Protocol TCP `
    -LocalPort 8000,8081 `
    -RemoteAddress LocalSubnet `
    -EdgeTraversalPolicy Block

Write-Host "Regle creee pour les ports TCP 8000 et 8081, limitee au sous-reseau local."
