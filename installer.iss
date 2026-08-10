; Inno Setup Script for Kokoro Voice Studio Pro v2.5
; Lead Developer: Dilshan Chandrarathne

#define MyAppName "Kokoro Voice Studio Pro"
#define MyAppVersion "2.5.0"
#define MyAppPublisher "Dilshan Chandrarathne"
#define MyAppExeName "KokoroVoiceStudio.exe"
#define MyAppAssocName MyAppName + " Project"
#define MyAppAssocExt ".kokoro"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
AppId={{D1154A42-9981-4C3D-B916-K0K0R0STU010}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Kokoro Voice Studio
DefaultGroupName=Kokoro Voice Studio
DisableProgramGroupPage=yes
LicenseFile=
OutputDir=dist_installer
OutputBaseFilename=Kokoro_Voice_Studio_Setup_v2.5
SetupIconFile=icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\KokoroVoiceStudio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
