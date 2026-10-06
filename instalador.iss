; Instalador de Salud de la batería (Inno Setup 6).
; Lo compila construir_instalador.bat a partir de dist\SaludBateria.

#define Nombre "Salud de la batería"
#define Version "1.0.0"
#define Exe "SaludBateria.exe"

[Setup]
AppId={{7E3B9C1A-4F2D-4B8E-9A61-5C0D2E7F8B34}
AppName={#Nombre}
AppVersion={#Version}
AppVerName={#Nombre} {#Version}
AppPublisher=Joseba
DefaultDirName={autopf}\Salud de la bateria
DefaultGroupName={#Nombre}
DisableProgramGroupPage=yes
; Se instala para todos los usuarios (pide permiso de administrador),
; pero deja elegir instalar solo para el usuario actual.
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=instalador
OutputBaseFilename=SaludBateria-Setup-{#Version}
SetupIconFile=icono.ico
UninstallDisplayIcon={app}\{#Exe}
UninstallDisplayName={#Nombre}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "escritorio"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "dist\SaludBateria\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#Nombre}"; Filename: "{app}\{#Exe}"
Name: "{group}\Desinstalar {#Nombre}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#Nombre}"; Filename: "{app}\{#Exe}"; Tasks: escritorio

[Run]
Filename: "{app}\{#Exe}"; Description: "Abrir {#Nombre} ahora"; Flags: nowait postinstall skipifsilent
