; Script de Inno Setup para crear un instalador de Windows.
;
; Requiere Inno Setup:  winget install JRSoftware.InnoSetup
; Uso:  compilar este archivo con Inno Setup tras haber ejecutado construir.ps1
;   & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" instalador.iss

#define NombreApp "Adaptador de documentos Word"
#define VersionApp "1.1.0"
#define EjecutableApp "Adaptador Word.exe"

[Setup]
AppName={#NombreApp}
AppVersion={#VersionApp}
AppPublisher=Adaptador de documentos Word
DefaultDirName={autopf}\Adaptador Word
DefaultGroupName=Adaptador Word
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=Instalar Adaptador Word {#VersionApp}
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
Source: "dist\{#EjecutableApp}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#NombreApp}"; Filename: "{app}\{#EjecutableApp}"
Name: "{group}\Desinstalar {#NombreApp}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#NombreApp}"; Filename: "{app}\{#EjecutableApp}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#EjecutableApp}"; Description: "Abrir {#NombreApp}"; Flags: nowait postinstall skipifsilent
