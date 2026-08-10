; Inno Setup Script for Kokoro Voice Studio Pro v2.5
; Lead Developer: Dilshan Chandrarathne

#define MyAppName "Kokoro Voice Studio Pro"
#define MyAppVersion "2.5.0"
#define MyAppPublisher "Dilshan Chandrarathne"
#define MyAppExeName "KokoroVoiceStudio.exe"

[Setup]
AppId={{D1154A42-9981-4C3D-B916-K0K0R0STU010}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Kokoro Voice Studio
DefaultGroupName=Kokoro Voice Studio
DisableProgramGroupPage=yes
OutputDir=dist_installer
OutputBaseFilename=Kokoro_Voice_Studio_Setup_v2.5
SetupIconFile=icon.ico
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\KokoroVoiceStudio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
