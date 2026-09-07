[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string]$Entrada,
    [string]$Salida
)

$ErrorActionPreference = 'Stop'
$raiz = Split-Path $PSScriptRoot -Parent
$config = Import-PowerShellDataFile (Join-Path $raiz 'config.psd1')

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { throw 'No se encontró ffmpeg en PATH.' }
if (-not (Test-Path -LiteralPath $Entrada -PathType Leaf)) { throw "No existe el archivo: $Entrada" }

$carpetaSalida = Join-Path $raiz 'salida'
New-Item -ItemType Directory -Force -Path $carpetaSalida | Out-Null
if ([string]::IsNullOrWhiteSpace($Salida)) {
    $nombre = [IO.Path]::GetFileNameWithoutExtension($Entrada)
    $Salida = Join-Path $carpetaSalida ("$nombre-short.mp4")
}

$logo = Join-Path $raiz 'assets/marca.png'
$w = $config.Ancho; $h = $config.Alto; $m = $config.MargenPx
if ($config.MejoraActiva) {
    $mejora = "hqdn3d=$($config.ReduccionRuido):$($config.ReduccionRuido):3:3,eq=contrast=1.04:saturation=1.03:brightness=0.01,unsharp=5:5:$($config.Nitidez):5:5:0"
} else {
    $mejora = 'null'
}
$base = "[0:v]split=2[bgsrc][fgsrc];[bgsrc]scale=${w}:${h}:force_original_aspect_ratio=increase,crop=${w}:${h},boxblur=24:2,eq=brightness=-0.10[bg];[fgsrc]$mejora,scale=${w}:${h}:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[composed]"

if (Test-Path -LiteralPath $logo -PathType Leaf) {
    $filtro = "$base;[1:v]scale=$($config.EscalaLogoPx):-1[wm];[composed][wm]overlay=W-w-${m}:${m}[v]"
    $args = @('-y','-i',$Entrada,'-loop','1','-i',$logo,'-filter_complex',$filtro,'-map','[v]','-map','0:a?','-c:v','libx264','-crf',$config.CalidadCrf,'-preset',$config.Preset,'-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',$Salida)
} else {
    $texto = $config.MarcaTexto.Replace("'", "\'").Replace(':', '\:')
    $fuente = $config.Fuente.Replace(':', '\:')
    $filtro = "$base;[composed]drawtext=fontfile='$fuente':text='$texto':fontcolor=white@$($config.OpacidadMarca):fontsize=$($config.TamanoFuentePx):x=w-text_w-${m}:y=${m}:shadowcolor=black@0.55:shadowx=2:shadowy=2[v]"
    $args = @('-y','-i',$Entrada,'-filter_complex',$filtro,'-map','[v]','-map','0:a?','-c:v','libx264','-crf',$config.CalidadCrf,'-preset',$config.Preset,'-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',$Salida)
}

Write-Host "Procesando: $([IO.Path]::GetFileName($Entrada))" -ForegroundColor Cyan
& ffmpeg @args
if ($LASTEXITCODE -ne 0) { throw "FFmpeg terminó con código $LASTEXITCODE" }
Write-Host "Listo: $Salida" -ForegroundColor Green
