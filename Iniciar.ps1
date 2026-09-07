[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$raiz = $PSScriptRoot

Write-Host ''
Write-Host '=== Preparador de vídeos verticales autorizados ===' -ForegroundColor Cyan
Write-Host '1. Crear un Short con marca propia'
Write-Host '2. Unir episodios en vídeo largo vertical'
Write-Host 'Q. Salir'
$opcion = Read-Host 'Elige una opción'

switch ($opcion.ToUpperInvariant()) {
    '1' {
        $archivo = Read-Host 'Ruta del vídeo autorizado'
        & "$raiz\scripts\Procesar-Short.ps1" -Entrada $archivo
    }
    '2' {
        $carpeta = Read-Host 'Carpeta de episodios (nombres 01.mp4, 02.mp4...)'
        $titulo = Read-Host 'Nombre del archivo final (sin extensión)'
        $recorte = Read-Host 'Segundos a recortar al final de CADA episodio (ej. 1; 0 para no recortar)'
        if ([string]::IsNullOrWhiteSpace($titulo)) { $titulo = 'video-largo' }
        if ([string]::IsNullOrWhiteSpace($recorte)) { $recorte = '1' }
        & "$raiz\scripts\Crear-VideoLargo.ps1" -CarpetaPartes $carpeta -Titulo $titulo -RecorteFinalSegundos ([double]$recorte)
    }
    default { Write-Host 'Sin cambios.' }
}
