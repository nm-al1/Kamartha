$ErrorActionPreference = 'Stop'
$project = Split-Path $PSScriptRoot -Parent
$app = Join-Path $env:LOCALAPPDATA 'Programs\ArtCraft\FigCraft\figcraft.exe'
if (-not (Test-Path $app)) {
    throw "FigCraft tidak ditemukan: $app"
}
if (Get-NetTCPConnection -LocalPort 47800 -State Listen -ErrorAction SilentlyContinue) {
    throw 'Port 47800 sedang digunakan. Periksa FigCraft yang sudah berjalan sebelum membuka instance baru.'
}
Start-Process -FilePath $app -ArgumentList @(
    '--control', '47800',
    '--automation-read-root', ('"{0}"' -f (Join-Path $project 'docs')),
    '--automation-read-root', ('"{0}"' -f (Join-Path $project 'frontend')),
    '--automation-write-root', ('"{0}"' -f (Join-Path $project 'design'))
)
