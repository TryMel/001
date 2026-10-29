$ErrorActionPreference = "Stop"

$backendPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $backendPath

$localAddresses = @(
    Get-NetIPConfiguration |
        Where-Object { $_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq "Up" } |
        ForEach-Object { $_.IPv4Address.IPAddress } |
        Where-Object { $_ -and $_ -ne "127.0.0.1" }
)

if ($localAddresses.Count -eq 0) {
    throw "No active LAN IPv4 address found. Connect the PC to the same network as the mobile."
}

$existingListeners = @(
    Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue
)
if ($existingListeners.Count -gt 0) {
    $listenerDetails = $existingListeners |
        ForEach-Object { "$($_.LocalAddress) (PID $($_.OwningProcess))" } |
        Sort-Object -Unique
    throw "Port 8000 is already occupied by $($listenerDetails -join ', '). Stop that server first, then rerun this script so Django binds to 0.0.0.0 for mobile access."
}

$env:ALLOWED_HOSTS = (@("localhost", "127.0.0.1") + $localAddresses) -join ","
$env:CORS_ALLOWED_ORIGIN_REGEXES = '^https?://(localhost|127\.0\.0\.1)(:\d+)?$'
$mobileAddresses = ($localAddresses | ForEach-Object { "http://${_}:8000" }) -join ", "
$postgresHost = if ($env:POSTGRES_HOST) { $env:POSTGRES_HOST } else { "127.0.0.1" }
$postgresPort = if ($env:POSTGRES_PORT) { [int]$env:POSTGRES_PORT } else { 5432 }

if (-not (Test-NetConnection -ComputerName $postgresHost -Port $postgresPort -InformationLevel Quiet)) {
    throw "PostgreSQL n'est pas joignable sur ${postgresHost}:$postgresPort. Démarrez le service PostgreSQL puis relancez ce script."
}

Write-Host "API locale : http://localhost:8000"
Write-Host "API mobile : $mobileAddresses"
Write-Host "Base de développement : PostgreSQL ($postgresHost`:$postgresPort)"
Write-Host "Le serveur Django sera lié à 0.0.0.0:8000 pour accepter le réseau local."

python manage.py migrate
if ($LASTEXITCODE -ne 0) {
    throw "Les migrations Django ont échoué ; le serveur n'a pas été démarré."
}

python manage.py runserver 0.0.0.0:8000
