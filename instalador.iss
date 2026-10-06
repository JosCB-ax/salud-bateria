; Instalador de Salud de la batería (Inno Setup 6).
; Lo compila construir_instalador.bat a partir de dist\SaludBateria.

#define Nombre "Salud de la batería"
#define Version "1.7.0"
#define Exe "SaludBateria.exe"

[Setup]
AppId={{7E3B9C1A-4F2D-4B8E-9A61-5C0D2E7F8B34}
AppName={#Nombre}
AppVersion={#Version}
AppVerName={#Nombre} {#Version}
AppPublisher=JosCB
AppCopyright=© 2026 JosCB. Todos los derechos reservados.
LicenseFile=LICENCIA.txt
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
; El inicio automático se guarda en el registro del usuario que instala.
UsedUserAreasWarning=no
CloseApplications=force

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "escritorio"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"
Name: "arranque"; Description: "Iniciar con Windows y avisar al cargar (icono junto al reloj)"; GroupDescription: "Avisos de carga:"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "SaludBateria"; ValueData: """{app}\{#Exe}"" --bandeja"; Tasks: arranque; Flags: uninsdeletevalue

[Files]
Source: "dist\SaludBateria\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "LICENCIA.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#Nombre}"; Filename: "{app}\{#Exe}"
Name: "{group}\Desinstalar {#Nombre}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#Nombre}"; Filename: "{app}\{#Exe}"; Tasks: escritorio

[Run]
Filename: "{app}\{#Exe}"; Description: "Abrir {#Nombre} ahora"; Flags: nowait postinstall skipifsilent
Filename: "{app}\{#Exe}"; Parameters: "--bandeja"; Tasks: arranque; Flags: nowait runasoriginaluser

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/IM {#Exe} /F"; Flags: runhidden; RunOnceId: "CerrarBandeja"
