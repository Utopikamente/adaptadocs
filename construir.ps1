# Construye la distribución de Windows:
#   dist\Adaptadocs\                     (carpeta --onedir de PyInstaller)
#   dist\AdaptadocsSetup-X.Y.Z.exe       (instalador de Inno Setup)
#   dist\Adaptadocs-portable-X.Y.Z.zip   (versión portable, sin instalar)
#
# Se usa --onedir (no --onefile) a propósito: los ejecutables «todo en uno» de
# PyInstaller se autoextraen al arrancar y Windows Defender los marca como
# falso positivo (Trojan:Win32/Wacatac.B!ml). La carpeta + instalador no.
#
# Uso:  .\construir.ps1
# Requisitos: entorno virtual con dependencias, e Inno Setup para el instalador
#   (winget install JRSoftware.InnoSetup).

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$py = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { throw "No existe .venv. Crea el entorno virtual primero (ver README)." }

$version = (Select-String -Path ".\instalador.iss" -Pattern '#define VersionApp "([\d.]+)"').Matches[0].Groups[1].Value

& $py -m pip install --quiet pyinstaller pillow

if (-not (Test-Path ".\recursos\icono.ico")) { & $py .\recursos\crear_icono.py }

Stop-Process -Name "Adaptadocs" -Force -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Remove-Item -Force "Adaptadocs.spec" -ErrorAction SilentlyContinue

$work = Join-Path $env:LOCALAPPDATA "adaptadocs-build"

& $py -m PyInstaller --noconfirm --onedir --windowed `
    --name "Adaptadocs" `
    --icon ".\recursos\icono.ico" `
    --version-file ".\recursos\version_info.txt" `
    --add-data "core\registro.json;core" `
    --add-data "core\acis.json;core" `
    --collect-all tkinterdnd2 `
    --collect-all anthropic `
    --collect-all keyring `
    --collect-submodules keyring.backends `
    --workpath $work `
    --distpath ".\dist" `
    app.py

if ($LASTEXITCODE -ne 0) { throw "PyInstaller ha fallado." }

# --- Versión portable (zip) --------------------------------------------------
$zip = ".\dist\Adaptadocs-portable.zip"
Compress-Archive -Path ".\dist\Adaptadocs" -DestinationPath $zip -Force

# --- Instalador (Inno Setup) ----------------------------------------------- #
$iscc = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe")
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($iscc) {
    & $iscc ".\instalador.iss"
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup ha fallado." }
} else {
    Write-Warning "Inno Setup no encontrado: se omite el instalador. Instálalo con 'winget install JRSoftware.InnoSetup'."
}

# --- Sumas de comprobación ----------------------------------------------- #
Get-ChildItem ".\dist" -File -Filter "*.exe" | ForEach-Object {
    $h = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
    "$h  $($_.Name)" | Out-File -Encoding ascii "$($_.FullName).sha256"
}
$hz = (Get-FileHash $zip -Algorithm SHA256).Hash
"$hz  $(Split-Path $zip -Leaf)" | Out-File -Encoding ascii "$zip.sha256"

Write-Host ""
Write-Host "Listo. En .\dist:"
Get-ChildItem ".\dist" -File | Select-Object Name, Length
