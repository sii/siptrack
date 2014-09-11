[Setup]
AppName=Siptrack
AppVerName=Siptrack 2.0.0
DefaultDirName={pf}\Siptrack
DefaultGroupname=Siptrack
UninstallDisplayIcon={app}\siptrack.exe
Compression=lzma
SolidCompression=yes
OutputDir=..\win-installer
ChangesEnvironment=yes

[Tasks]
Name: modifypath; Description: Add application directory to your system path; Flags: unchecked

[Files]
Source: "..\dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Siptrack GTKConnect"; Filename: "{app}\siptrack-no-console.exe"; Parameters: "gtkconnect"
Name: "{group}\Edit Siptrack config"; Filename: "{app}\siptrack-no-console.exe"; Parameters: "edit-config"

[Code]
function ModPathDir(): TArrayOfString;
var
    Dir: TArrayOfString;
begin
    setArrayLength(Dir, 1)
    Dir[0] := ExpandConstant('{app}');
    Result := Dir;
end;
#include "modpath.iss"
