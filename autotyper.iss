; Inno Setup script: wraps dist\AutoTyper.exe (built by PyInstaller) into dist\AutoTyperSetup.exe.
; Built by build_windows.bat; or open this in the Inno Setup IDE and press Compile.
; Needs Inno Setup 6.3+ (for x64compatible).

#define MyAppName "Auto Typer"
#define MyAppVersion "1.0.0"
#define MyAppExeName "AutoTyper.exe"

[Setup]
; AppId identifies the app for upgrades/uninstall: never change it ({{ escapes the brace)
AppId={{811D71F3-AD13-43B1-80E3-C92CE4FEAE0B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
; Per-user install by default (no admin prompt); the first page offers "all users" instead
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=dist
OutputBaseFilename=AutoTyperSetup
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
