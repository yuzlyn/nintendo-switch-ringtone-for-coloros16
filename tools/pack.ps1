# Package module/ into a flashable zip for Magisk / KernelSU / Apatch.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$src  = Join-Path $root "module"

# version comes from module.prop so the zip name can never drift
$ver = (Select-String -Path (Join-Path $src "module.prop") -Pattern '^version=(.+)$').Matches[0].Groups[1].Value
$out = Join-Path $root "NS-Ringtone-$ver.zip"

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

# Entries are written by hand so every path uses "/": Windows PowerShell's
# ZipFile.CreateFromDirectory emits "\", which Android unzip turns into file
# names containing a literal backslash instead of directories.
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$fs = [IO.File]::Open($out, [IO.FileMode]::Create)
$zip = [IO.Compression.ZipArchive]::new($fs, [IO.Compression.ZipArchiveMode]::Create)
try {
    $base = (Resolve-Path $src).Path
    foreach ($f in Get-ChildItem -Recurse -File $base) {
        $rel = $f.FullName.Substring($base.Length + 1).Replace('\', '/')
        [void][IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $zip, $f.FullName, $rel, [IO.Compression.CompressionLevel]::Optimal)
    }
}
finally {
    $zip.Dispose()
    $fs.Dispose()
}

$mb = [math]::Round((Get-Item $out).Length / 1MB, 1)
Write-Output "built: $out ($mb MB)"
