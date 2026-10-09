# Démonstration locale : aucun compte ni mot de passe prédéfini.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "La commande a échoué : $Executable $($Arguments -join ' ')" }
}

$runtimePython = $null
$launcher = Get-Command py -ErrorAction SilentlyContinue
if ($launcher) {
    $detected = & $launcher.Source -3 -c "import sys; print(sys.executable)" 2>$null
    if ($LASTEXITCODE -eq 0) { $runtimePython = [string]$detected }
}
if (-not $runtimePython) {
    $candidate = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $candidate) { $runtimePython = $candidate }
}
if (-not $runtimePython) {
    throw 'Installez Python 3.12 ou 3.13 depuis python.org puis relancez ce script.'
}

$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    Invoke-Checked $runtimePython @('-m', 'venv', '--without-pip', '.venv')
}
# Le Python fourni par Codex contient pip et peut installer dans l’environnement isolé.
& $runtimePython -m pip --version *> $null
if ($LASTEXITCODE -eq 0) {
    Invoke-Checked $runtimePython @('-m', 'pip', '--python', $venvPython, 'install', 'pip', '-e', '.')
} else {
    Invoke-Checked $venvPython @('-m', 'ensurepip', '--upgrade')
    Invoke-Checked $venvPython @('-m', 'pip', 'install', '-e', '.')
}
Invoke-Checked $venvPython @('manage.py', 'migrate')
Write-Host 'Si vous avez déjà créé un compte, appuyez sur Entrée pour le conserver.'
$createAccount = Read-Host 'Créer un superutilisateur ? (o pour oui)'
if ($createAccount -eq 'o') { Invoke-Checked $venvPython @('manage.py', 'createsuperuser') }
Write-Host 'Ouvrez http://127.0.0.1:8000/project/ et connectez-vous avec votre compte.'
Write-Host 'Pour arrêter le serveur : Ctrl+C.'
Invoke-Checked $venvPython @('manage.py', 'runserver')
