# Package module/ into a flashable zip for Magisk / KernelSU / Apatch.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$src  = Join-Path $root "module"
$out  = Join-Path $root "NS-Ringtone-v1.0.zip"

if (Test-Path $out) { Remove-Item $out -Force }

# flashable stub (Magisk / KernelSU compatible)
$meta = Join-Path $src "META-INF\com\google\android"
New-Item -ItemType Directory -Force -Path $meta | Out-Null
$updateBinary = @'
#!/sbin/sh
umask 022
OUTFD=$2
ZIPFILE=$3
mount /data 2>/dev/null
. /data/adb/magisk/util_functions.sh
install_module
exit 0
'@
[IO.File]::WriteAllText((Join-Path $meta "update-binary"), ($updateBinary -replace "`r`n", "`n"))
[IO.File]::WriteAllText((Join-Path $meta "updater-script"), "#MAGISK")

Push-Location $src
try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::CreateFromDirectory(
        $src, $out,
        [IO.Compression.CompressionLevel]::Optimal,
        $false)
}
finally { Pop-Location }

$mb = [math]::Round((Get-Item $out).Length / 1MB, 1)
Write-Output "built: $out ($mb MB)"
