[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string]$CarpetaPartes,
    [Parameter(Mandatory)] [string]$Titulo,
    [string]$Salida,
    [ValidateSet('Vertical', 'Horizontal')] [string]$Formato = 'Vertical',
    [ValidateRange(0, 60)] [double]$RecorteFinalSegundos = 1
)

$ErrorActionPreference = 'Stop'
$raiz = Split-Path $PSScriptRoot -Parent
$config = Import-PowerShellDataFile (Join-Path $raiz 'config.psd1')
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue) -or -not (Get-Command ffprobe -ErrorAction SilentlyContinue)) { throw 'Se requieren ffmpeg y ffprobe en PATH.' }
if (-not (Test-Path -LiteralPath $CarpetaPartes -PathType Container)) { throw "No existe la carpeta: $CarpetaPartes" }

$partes = Get-ChildItem -LiteralPath $CarpetaPartes -File | Where-Object { $_.Extension -match '^\.(mp4|mov|mkv|webm|m4v)$' } | Sort-Object Name
if ($partes.Count -lt 2) { throw 'Incluye al menos dos vídeos compatibles y nómbralos en orden (01.mp4, 02.mp4...).' }

$salidaDir = Join-Path $raiz 'salida'
New-Item -ItemType Directory -Force -Path $salidaDir | Out-Null
$trabajo = Join-Path $env:TEMP ("reutilizacion-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $trabajo | Out-Null

try {
    $normalizados = [System.Collections.Generic.List[string]]::new()
    if ($Formato -eq 'Horizontal') {
        # Vídeo vertical centrado; los laterales se rellenan con la propia imagen desenfocada.
        $w = 1920; $h = 1080
    } else {
        $w = $config.Ancho; $h = $config.Alto
    }
    $m = $config.MargenPx
    if ($config.MejoraActiva) {
        $mejora = "hqdn3d=$($config.ReduccionRuido):$($config.ReduccionRuido):3:3,eq=contrast=1.04:saturation=1.03:brightness=0.01,unsharp=5:5:$($config.Nitidez):5:5:0"
    } else {
        $mejora = 'null'
    }
    $base = "[0:v]split=2[bgsrc][fgsrc];[bgsrc]scale=${w}:${h}:force_original_aspect_ratio=increase,crop=${w}:${h},boxblur=24:2,eq=brightness=-0.10[bg];[fgsrc]$mejora,scale=${w}:${h}:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[composed]"
    $logo = Join-Path $raiz 'assets/marca.png'
    $usarLogo = Test-Path -LiteralPath $logo -PathType Leaf
    if ($usarLogo) {
        $filtro = "$base;[1:v]scale=$($config.EscalaLogoPx):-1[wm];[composed][wm]overlay=W-w-${m}:${m}[v]"
    } else {
        $texto = $config.MarcaTexto.Replace("'", "\'").Replace(':', '\:')
        $fuente = $config.Fuente.Replace(':', '\:')
        $filtro = "$base;[composed]drawtext=fontfile='$fuente':text='$texto':fontcolor=white@$($config.OpacidadMarca):fontsize=$($config.TamanoFuentePx):x=w-text_w-${m}:y=${m}:shadowcolor=black@0.55:shadowx=2:shadowy=2[v]"
    }

    for ($i = 0; $i -lt $partes.Count; $i++) {
        $parte = $partes[$i]
        $duracionTexto = & ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $parte.FullName
        $duracion = [double]::Parse($duracionTexto, [Globalization.CultureInfo]::InvariantCulture)
        $fin = [Math]::Max(0.1, $duracion - $RecorteFinalSegundos)
        if ($fin -lt 0.5) { throw "El recorte deja la parte demasiado corta: $($parte.Name)" }
        $destino = Join-Path $trabajo ('{0:D3}.mp4' -f $i)
        Write-Host "Normalizando $($i + 1)/$($partes.Count): $($parte.Name)" -ForegroundColor Cyan
        if ($usarLogo) {
            & ffmpeg -y -i $parte.FullName -loop 1 -i $logo -t $fin -filter_complex $filtro -map '[v]' -map '0:a?' -c:v libx264 -crf $config.CalidadCrf -preset $config.Preset -pix_fmt yuv420p -r 30 -c:a aac -ar 48000 -ac 2 -b:a 192k -shortest $destino
        } else {
            & ffmpeg -y -i $parte.FullName -t $fin -filter_complex $filtro -map '[v]' -map '0:a?' -c:v libx264 -crf $config.CalidadCrf -preset $config.Preset -pix_fmt yuv420p -r 30 -c:a aac -ar 48000 -ac 2 -b:a 192k $destino
        }
        if ($LASTEXITCODE -ne 0) { throw "FFmpeg no pudo normalizar: $($parte.Name)" }
        $normalizados.Add($destino)
    }

    $lista = Join-Path $trabajo 'concat.txt'
    $lineas = $normalizados | ForEach-Object { "file '$($_.Replace("'", "'\\''"))'" }
    [IO.File]::WriteAllLines($lista, [string[]]$lineas, [Text.UTF8Encoding]::new($false))

    if ([string]::IsNullOrWhiteSpace($Salida)) {
        $final = Join-Path $salidaDir ("$Titulo.mp4")
    } else {
        $final = $Salida
    }
    & ffmpeg -y -f concat -safe 0 -i $lista -c copy $final
    if ($LASTEXITCODE -ne 0) { throw 'FFmpeg no pudo unir las partes normalizadas.' }
    Write-Host "Vídeo largo listo: $final" -ForegroundColor Green
}
finally {
    if (Test-Path -LiteralPath $trabajo) { Remove-Item -LiteralPath $trabajo -Recurse -Force }
}
