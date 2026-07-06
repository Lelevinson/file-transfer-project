; Inno Setup script for File Transfer
; Build with:  ISCC.exe installer.iss  ->  installer_output\FileTransfer-Setup.exe

[Setup]
AppId=FileTransfer
AppName=File Transfer
AppVersion=1.0
; install to a writable per-user location (users drop files into source/)
DefaultDirName={userdocs}\FileTransfer
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=installer_output
OutputBaseFilename=FileTransfer-Setup
Compression=lzma
SolidCompression=yes

[Files]
; the whole PyInstaller output folder (FileTransfer.exe + _internal + config.json)
Source: "dist\FileTransfer\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Dirs]
; the app's working folders, created so they exist right after install
Name: "{app}\source"
Name: "{app}\target"
Name: "{app}\fail"
Name: "{app}\logs"

[Icons]
Name: "{autoprograms}\File Transfer"; Filename: "{app}\FileTransfer.exe"
Name: "{autodesktop}\File Transfer"; Filename: "{app}\FileTransfer.exe"

[Run]
Filename: "{app}\FileTransfer.exe"; Description: "Launch File Transfer now"; Flags: nowait postinstall skipifsilent
