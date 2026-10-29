$ErrorActionPreference = "Stop"

$backendPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $backendPath

python manage.py migrate
if ($LASTEXITCODE -ne 0) {
    throw "Les migrations ont échoué ; aucun compte administrateur n'a été créé."
}

Write-Host "Création d'un administrateur dans la base locale Akasha."
Write-Host "Django demandera l'adresse e-mail, le nom d'utilisateur et un mot de passe masqué."
python manage.py createsuperuser
if ($LASTEXITCODE -ne 0) {
    throw "La création du compte administrateur a échoué."
}
