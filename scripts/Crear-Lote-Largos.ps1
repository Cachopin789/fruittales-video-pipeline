[CmdletBinding()]
param(
    [ValidateRange(10, 60)] [double]$ObjetivoMinutos = 12,
    [ValidateRange(0, 60)] [double]$RecorteFinalSegundos = 1,
    [ValidateSet('Vertical', 'Horizontal')] [string]$Formato = 'Vertical',
    [ValidateRange(1, 100)] [int]$DesdeNumero = 1
)

$ErrorActionPreference = 'Stop'
$raiz = Split-Path $PSScriptRoot -Parent
if (-not (Get-Command ffprobe -ErrorAction SilentlyContinue)) { throw 'Se requiere ffprobe en PATH.' }

# Los IDs de TikTok aumentan con el tiempo: parte 1 primero, la más reciente después.
$archivos = Get-ChildItem -LiteralPath $raiz -File | Where-Object {
    $_.Name -like 'snaptik_*' -and $_.Extension -match '^\.(mp4|mov|mkv|webm|m4v)$'
} | Sort-Object Name
if ($archivos.Count -lt 2) { throw 'No hay suficientes archivos snaptik en la carpeta principal.' }

$partes = foreach ($archivo in $archivos) {
    $duracionTexto = & ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $archivo.FullName
    [pscustomobject]@{
        Archivo = $archivo
        Segundos = [double]::Parse($duracionTexto, [Globalization.CultureInfo]::InvariantCulture)
    }
}

$duracionTotal = ($partes | Measure-Object -Property Segundos -Sum).Sum
$numeroLargos = [math]::Ceiling($duracionTotal / ($ObjetivoMinutos * 60))
$indice = 0
$restante = $duracionTotal
$grupos = [System.Collections.Generic.List[object]]::new()

for ($numero = 1; $numero -le $numeroLargos; $numero++) {
    $gruposPendientes = $numeroLargos - $numero
    $objetivo = $restante / ($gruposPendientes + 1)
    $grupo = [System.Collections.Generic.List[object]]::new()
    $suma = 0
    while ($indice -lt $partes.Count) {
        $candidato = $partes[$indice]
        $desvioActual = [math]::Abs($suma - $objetivo)
        $desvioConCandidato = [math]::Abs(($suma + $candidato.Segundos) - $objetivo)
        if ($grupo.Count -gt 0 -and $suma -ge 600 -and $desvioConCandidato -gt $desvioActual -and (($partes.Count - $indice) -ge $gruposPendientes)) { break }
        $grupo.Add($candidato)
        $suma += $candidato.Segundos
        $restante -= $candidato.Segundos
        $indice++
    }
    $grupos.Add([pscustomobject]@{ Numero = $numero; Partes = $grupo; Segundos = $suma })
}

foreach ($grupo in $grupos) {
    if ($grupo.Numero -lt $DesdeNumero) { continue }
    $nombre = 'universo-frutal-ai-largo-{0:D2}' -f $grupo.Numero
    if ($Formato -eq 'Horizontal') {
        $tituloSalida = "$nombre-16x9"
    } else {
        $tituloSalida = $nombre
    }
    # El sufijo evita reutilizar la carpeta de enlaces creada por una ejecución anterior detenida.
    $carpetaPartes = Join-Path $raiz ('partes\' + $nombre + '-secuencia')
    if (Test-Path -LiteralPath $carpetaPartes) {
        $partesExistentes = Get-ChildItem -LiteralPath $carpetaPartes -File | Where-Object { $_.Extension -eq '.mp4' }
        if ($partesExistentes.Count -ne $grupo.Partes.Count) { throw "La carpeta existente no coincide con el lote calculado: $carpetaPartes" }
    } else {
        New-Item -ItemType Directory -Path $carpetaPartes | Out-Null
        for ($i = 0; $i -lt $grupo.Partes.Count; $i++) {
            $origen = $grupo.Partes[$i].Archivo.FullName
            $destino = Join-Path $carpetaPartes ('{0:D3}.mp4' -f ($i + 1))
            New-Item -ItemType HardLink -Path $destino -Value $origen | Out-Null
        }
    }

    $minutos = [math]::Round($grupo.Segundos / 60, 2)
    Write-Host "Creando $tituloSalida ($($grupo.Partes.Count) partes, $minutos min)" -ForegroundColor Cyan
    & "$PSScriptRoot\Crear-VideoLargo.ps1" -CarpetaPartes $carpetaPartes -Titulo $tituloSalida -Formato $Formato -RecorteFinalSegundos $RecorteFinalSegundos
}
