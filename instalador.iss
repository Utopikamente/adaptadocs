; Script de Inno Setup para crear un instalador de Windows.
;
; Requiere Inno Setup:  winget install JRSoftware.InnoSetup
; Uso:  compilar este archivo con Inno Setup tras haber ejecutado construir.ps1
;   & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" instalador.iss

#define NombreApp "Adaptadocs"
#define VersionApp "1.9.0"
#define EjecutableApp "Adaptadocs.exe"

[Setup]
AppName={#NombreApp}
AppVersion={#VersionApp}
AppPublisher=Máximo Escribano Diéguez
DefaultDirName={autopf}\Adaptadocs
DefaultGroupName=Adaptadocs
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=AdaptadocsSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Instala para el usuario actual: no pide permisos de administrador
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=recursos\icono.ico
UninstallDisplayIcon={app}\{#EjecutableApp}

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
; Carpeta completa del build --onedir de PyInstaller (Adaptadocs.exe + _internal\)
Source: "dist\Adaptadocs\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#NombreApp}"; Filename: "{app}\{#EjecutableApp}"
Name: "{group}\Desinstalar {#NombreApp}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#NombreApp}"; Filename: "{app}\{#EjecutableApp}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#EjecutableApp}"; Description: "Abrir {#NombreApp}"; Flags: nowait postinstall skipifsilent
