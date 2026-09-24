; ASLAN TUNER Installer Template
#define MyAppName "ASLAN TUNER"
#define MyAppVersion "@VERSION@"
#define MyAppExeName "ASLAN-TUNER-v@VERSION@.exe"

[Setup]
AppId={{B4E0D3A2-1C8E-4E4E-9C1D-ASLAN10001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher="ASLAN TUNER"
DefaultDirName={autopf}\ASLAN TUNER
DefaultGroupName=ASLAN TUNER
OutputDir=Output
OutputBaseFilename=ASLAN-TUNER-v{#MyAppVersion}-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=..\assets\aslan_tuner.ico
WizardImageFile=..\assets\setup_left.bmp
WizardSmallImageFile=..\assets\setup_small.bmp

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\ASLAN TUNER"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\ASLAN TUNER"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch ASLAN TUNER"; Flags: nowait postinstall skipifsilent
