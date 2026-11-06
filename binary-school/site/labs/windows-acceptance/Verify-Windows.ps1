#Requires -Version 5.1
<# Run in an x86/x64 Native Tools PowerShell session. Builds and runs ONLY
   the original training sources under this project. Does not install tools,
   change policies, download packages, or execute arbitrary uploaded files. #>
param([string]$Architecture = $env:VSCMD_ARG_TGT_ARCH)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Native Windows is required; Linux/Wine is not a native acceptance pass.' }
if ($Architecture -notin @('x86','x64') -or $env:VSCMD_ARG_TGT_ARCH -ne $Architecture) {
    throw 'Open the matching x86 or x64 Native Tools PowerShell session first.'
}
$Compiler = Get-Command cl.exe -ErrorAction Stop
$Project = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$LabRoot = Join-Path $Project 'site\labs'
$Output = Join-Path $Project ('.qa\windows-' + $Architecture)
New-Item -ItemType Directory -Force -Path $Output | Out-Null
$Results = New-Object 'System.Collections.Generic.List[object]'
$Builds = New-Object 'System.Collections.Generic.List[object]'
$Metadata = [ordered]@{
    architecture=$Architecture; os=[Environment]::OSVersion.VersionString
    compiler=$Compiler.Source; compilerFileVersion=(Get-Item $Compiler.Source).VersionInfo.FileVersion
    startedUtc=[DateTime]::UtcNow.ToString('o'); status='running'
    scriptSha256=(Get-FileHash $PSCommandPath -Algorithm SHA256).Hash
    curriculumSha256=(Get-FileHash (Join-Path $Project 'site\curriculum.json') -Algorithm SHA256).Hash
    manualDebuggerAcceptance='pending'; nativeBinaryPatchAcceptance='pending'
}
function Invoke-TrainingProcess([string]$File, [string[]]$Arguments, [int]$Timeout=60) {
    # Windows paths cannot contain a literal quote. Quote each complete argument,
    # including /Fo and /Fe paths, so project folders containing spaces work.
    foreach($Arg in $Arguments) { if($Arg.Contains('"')) { throw 'Unexpected quote in generated argument.' } }
    $Start = New-Object Diagnostics.ProcessStartInfo
    $Start.FileName=$File
    $Start.Arguments=(($Arguments | ForEach-Object { '"' + ([regex]::Replace($_,'(\\+)$','$1$1')) + '"' }) -join ' ')
    $Start.WorkingDirectory=$Project; $Start.UseShellExecute=$false
    $Start.RedirectStandardOutput=$true; $Start.RedirectStandardError=$true
    $Process=New-Object Diagnostics.Process
    $Process.StartInfo=$Start
    if(-not $Process.Start()) { throw "Could not start $File" }
    $OutTask=$Process.StandardOutput.ReadToEndAsync(); $ErrTask=$Process.StandardError.ReadToEndAsync()
    if(-not $Process.WaitForExit($Timeout*1000)) { $Process.Kill(); throw "Timed out: $File" }
    $Result=[pscustomobject]@{exit=$Process.ExitCode;stdout=$OutTask.Result;stderr=$ErrTask.Result}
    $Process.Dispose(); return $Result
}
function Build-Training([string]$Group,[string]$Name,[string[]]$Sources,[string]$Mode) {
    $Stem=Join-Path $Output ($Group+'-'+$Name+'-'+$Mode)
    $CompileArgs=@('/nologo','/TC','/W4',('/Fo'+$Stem+'.obj'))
    if($Mode -eq 'guided') { $CompileArgs+=@('/Od','/Zi',('/Fd'+$Stem+'-compile.pdb')) } else { $CompileArgs+='/O2' }
    # Multi-source casebook builds need individual object paths, so compile in
    # an isolated group/name/mode directory rather than one /Fo filename.
    if($Sources.Count -gt 1) {
        $Objects=$Stem+'-objects'; New-Item -ItemType Directory -Force -Path $Objects | Out-Null
        $CompileArgs=$CompileArgs | Where-Object { -not $_.StartsWith('/Fo') }
        $CompileArgs+=('/Fo'+$Objects+'\')
    }
    $CompileArgs+=('/Fe'+$Stem+'.exe'); $CompileArgs+=$Sources
    $Run=Invoke-TrainingProcess $Compiler.Source $CompileArgs 120
    ($Run.stdout+$Run.stderr) | Set-Content -Encoding UTF8 ($Stem+'-build.log')
    if($Run.exit -ne 0) { throw "Compilation failed: $Stem (see build log)." }
    $Bytes=[IO.File]::ReadAllBytes($Stem+'.exe'); $Pe=[BitConverter]::ToInt32($Bytes,0x3c)
    $Machine=[BitConverter]::ToUInt16($Bytes,$Pe+4)
    $Expected=if($Architecture -eq 'x64') {0x8664} else {0x14c}
    if($Machine -ne $Expected) { throw "Wrong PE machine for $Stem" }
    $Builds.Add([pscustomobject]@{group=$Group;name=$Name;mode=$Mode;compileArguments=$CompileArgs;sources=@($Sources | ForEach-Object { [pscustomobject]@{path=$_;sha256=(Get-FileHash $_ -Algorithm SHA256).Hash} });machine=('0x{0:x4}' -f $Machine);sha256=(Get-FileHash ($Stem+'.exe') -Algorithm SHA256).Hash;path=($Stem+'.exe')})
    return ($Stem+'.exe')
}
function Check-Training([string]$Exe,[string[]]$Arguments,[int]$Exit,[string]$Pattern) {
    $Run=Invoke-TrainingProcess $Exe $Arguments 5
    $Pass=$Run.exit -eq $Exit -and (-not $Pattern -or $Run.stdout -match $Pattern)
    $Results.Add([pscustomobject]@{file=[IO.Path]::GetFileName($Exe);arguments=$Arguments;exit=$Run.exit;expectedExit=$Exit;stdout=$Run.stdout;stderr=$Run.stderr;passed=$Pass})
    if(-not $Pass) { throw "Behavior mismatch: $Exe $Arguments" }
}
try {
    $Curriculum=Get-Content -Raw (Join-Path $Project 'site\curriculum.json') | ConvertFrom-Json
    foreach($Lesson in $Curriculum.lessons | Where-Object {$_.flagDigest}) {
        $Target=[regex]::Match($Lesson.solution,'accepted integer is (-?\d+)').Groups[1].Value
        $Flag=[regex]::Match($Lesson.solution,'BS\{[^}]+\}').Value
        if(-not $Target -or -not $Flag) { throw 'Missing original flag-lab contract.' }
        foreach($Mode in @('guided','optimized')) {
            $Exe=Build-Training 'flag' $Lesson.course @((Join-Path $LabRoot ('flags\'+$Lesson.course+'.c'))) $Mode
            Check-Training $Exe @($Target) 0 ([regex]::Escape($Flag))
            Check-Training $Exe @('0') 1 ''
            Check-Training $Exe @('invalid') 2 ''
        }
    }
    foreach($Name in @('xref','records','trace','windows','protected','reconstruct','final-cedar','final-quartz','final-willow')) {
        foreach($Mode in @('guided','optimized')) {
            $Exe=Build-Training 'practical' $Name @((Join-Path $LabRoot ('readiness\sources\'+$Name+'.c'))) $Mode
            switch($Name) {
                'xref' {Check-Training $Exe @('orbit','2') 0 'BS\{practical_xrefs\}'; Check-Training $Exe @('wrong','2') 1 'result=-1'}
                'records' {Check-Training $Exe @('3') 0 'total=14'; Check-Training $Exe @('2') 1 'total=9'}
                'trace' {Check-Training $Exe @('3','-3','4') 0 'total=25'; Check-Training $Exe @('3','3','4') 1 'total=25'}
                'windows' {Check-Training $Exe @('LAB','4') 0 'quote=28'; Check-Training $Exe @('wrong','4') 1 ''}
                'protected' {Check-Training $Exe @('maple','0') 0 'BS\{practical_decoding\}'; Check-Training $Exe @('maple','1') 3 'ANALYSIS_PATH'}
                'reconstruct' {Check-Training $Exe @('1','5') 0 'price=25'; Check-Training $Exe @('0','4') 1 'price=14'}
                default {
                    $Config=switch($Name) { 'final-cedar' {@(3,4,5,'north')} 'final-quartz' {@(2,6,7,'delta')} 'final-willow' {@(4,3,8,'cabin')} }
                    foreach($N in 0..8) {
                        $Total=1;for($I=0;$I -lt $N;$I++){if($I -lt $Config[0]){$Total+=$Config[1]}else{$Total+=$Config[1]+2}}
                        if($N -gt $Config[0]){$Total-=$Config[2]}
                        Check-Training $Exe @([string]$N,[string]$Config[3],'0') 0 ('charge='+$Total+'\r?\n?$')
                    }
                    Check-Training $Exe @('3',[string]$Config[3],'1') 3 'LOCKED'
                }
            }
            Check-Training $Exe @() 2 ''
        }
    }
    foreach($Name in @('constructs','calls','records','patch_logic','obfuscation','audit','windows_lab')) {
        foreach($Mode in @('guided','optimized')) {
            # Build all original full-kit programs. Their program contracts vary;
            # behavioral case validation is intentionally not inferred from exit0.
            $Unused=Build-Training 'full' $Name @((Join-Path $LabRoot ('full\'+$Name+'.c'))) $Mode
        }
    }
    foreach($Name in @('storage','arithmetic','branches','loops','arguments','switch','records','callbacks')) {
        foreach($Mode in @('guided','optimized')) {
            $Unused=Build-Training 'casebook' $Name @((Join-Path $LabRoot ('casebook\'+$Name+'.c')),(Join-Path $LabRoot 'casebook\driver.c')) $Mode
        }
    }
    foreach($Mode in @('guided','optimized')) {
        $Exe=Build-Training 'windows' 'exception_lab' @((Join-Path $PSScriptRoot 'exception_lab.c')) $Mode
        Check-Training $Exe @() 0 'handled=1'
    }
    $Metadata.status='automated-pass-manual-pending'
} catch {
    $Metadata.status='failed';$Metadata.error=$_.Exception.Message
    throw
} finally {
    $Metadata.finishedUtc=[DateTime]::UtcNow.ToString('o')
    [ordered]@{metadata=$Metadata;builds=@($Builds.ToArray());cases=@($Results.ToArray())} | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 (Join-Path $Output 'acceptance.json')
    Write-Host ('Acceptance evidence: '+(Join-Path $Output 'acceptance.json'))
    Write-Host 'Manual debugger and native binary-patch checks remain pending; follow WINDOWS-ACCEPTANCE.md.'
}
