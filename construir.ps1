# Construye el ejecutable de Windows (dist\Adaptador Word.exe).
#
# Uso:  .\construir.ps1
#
# Requisitos: haber creado el entorno virtual y las dependencias
#   python -m venv .venv
#   .venv\Scripts\pip install -r requirements.txt

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$py = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { throw "No existe .venv. Crea el entorno virtual primero (ver README)." }

& $py -m pip install --quiet pyinstaller pillow

# Icono (si falta)
if (-not (Test-Path ".\recursos\icono.ico")) {
    & $py .\recursos\crear_icono.py
}

# Cierra una instancia previa que pudiera estar bloqueando el .exe
Stop-Process -Name "Adaptador Word" -Force -ErrorAction SilentlyContinue

# Limpieza de builds anteriores
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Remove-Item -Force "Adaptador Word.spec" -ErrorAction SilentlyContinue

# El trabajo intermedio va fuera de OneDrive para no saturar la sincronizacion
$work = Join-Path $env:LOCALAPPDATA "adaptador-word-build"

& $py -m PyInstaller --noconfirm --onefile --windowed `
    --name "Adaptador Word" `
    --icon ".\recursos\icono.ico" `
    --version-file ".\recursos\version_info.txt" `
    --collect-all tkinterdnd2 `
    --workpath $work `
    --distpath ".\dist" `
    app.py

if ($LASTEXITCODE -ne 0) { throw "PyInstaller ha fallado." }

# Suma de comprobación para publicar junto al ejecutable
$exe = ".\dist\Adaptador Word.exe"
$hash = (Get-FileHash $exe -Algorithm SHA256).Hash
"$hash  Adaptador Word.exe" | Out-File -Encoding ascii ".\dist\Adaptador Word.exe.sha256"

Write-Host ""
Write-Host "Listo:" (Resolve-Path $exe)
Write-Host "SHA-256:" $hash
