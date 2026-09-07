# FruitTales · preparación de vídeo con FFmpeg

Herramientas de PowerShell para preparar vídeos verticales y montajes largos a partir de material propio, con licencia o con autorización expresa. Añaden una marca propia, normalizan el formato y generan MP4 listos para revisar antes de publicar.

> Una marca de agua no concede derechos de uso. Antes de publicar, verifica la licencia o el permiso de cada fuente y regístralo en `derechos.csv`.

## Requisitos

- Windows PowerShell 5.1 o PowerShell 7.
- [FFmpeg](https://ffmpeg.org/) y `ffprobe` instalados y disponibles en `PATH`.
- Vídeos autorizados en formatos compatibles como MP4 o MOV.

Comprueba la instalación con:

```powershell
ffmpeg -version
ffprobe -version
```

## Instalación

1. Clona el repositorio.
2. Instala FFmpeg y asegúrate de que los comandos anteriores funcionan desde PowerShell.
3. Opcionalmente, añade `assets/marca.png` (PNG con transparencia) para usar un logo; de lo contrario se usará la marca de texto configurada.
4. Ajusta `config.psd1` si quieres modificar el texto de la marca, su posición o la calidad de codificación.

No hay dependencias de Python ni claves API necesarias.

## Estructura

```text
assets/marca.png       Logo opcional para la marca de agua
entrada/               Vídeos autorizados de entrada
partes/                Episodios temporales para montajes largos (no se versiona)
salida/                Vídeos, imágenes y registros generados (no se versiona)
scripts/               Scripts de procesamiento
config.psd1            Ajustes de salida y marca, sin credenciales
derechos.csv           Registro de licencias y permisos
```

## Scripts

### `Iniciar.ps1`

Es el punto de entrada interactivo. Muestra un menú para crear un Short o unir episodios en un vídeo largo. Desde la raíz del proyecto:

```powershell
powershell -ExecutionPolicy Bypass -File .\Iniciar.ps1
```

### `scripts/Procesar-Short.ps1`

Convierte un vídeo autorizado en un Short vertical de 1080 × 1920. Aplica una mejora visual moderada, compone un fondo desenfocado cuando es necesario y añade el logo o texto de marca. El resultado se guarda en `salida/`.

```powershell
.\scripts\Procesar-Short.ps1 -Entrada .\entrada\clip.mp4
```

Para decidir una ubicación concreta:

```powershell
.\scripts\Procesar-Short.ps1 -Entrada .\entrada\clip.mp4 -Salida .\salida\mi-short.mp4
```

### `scripts/Crear-VideoLargo.ps1`

Normaliza y une al menos dos episodios ordenados por nombre dentro de una carpeta. Puede recortar los últimos segundos de cada parte para eliminar rótulos finales. Genera un vídeo vertical por defecto o un vídeo horizontal 16:9 con el contenido vertical centrado sobre un fondo desenfocado.

```powershell
.\scripts\Crear-VideoLargo.ps1 `
  -CarpetaPartes .\partes\mi-historia `
  -Titulo mi-historia `
  -RecorteFinalSegundos 1
```

Versión horizontal:

```powershell
.\scripts\Crear-VideoLargo.ps1 `
  -CarpetaPartes .\partes\mi-historia `
  -Titulo mi-historia-16x9 `
  -Formato Horizontal
```

### `scripts/Crear-Lote-Largos.ps1`

Agrupa automáticamente los archivos descargados con nombre `snaptik_*` que estén en la raíz local en lotes de una duración aproximada y llama a `Crear-VideoLargo.ps1` para crear cada montaje. Esos archivos de descarga y los resultados están excluidos de Git.

```powershell
.\scripts\Crear-Lote-Largos.ps1 -ObjetivoMinutos 12 -Formato Vertical
```

Puedes retomar un lote desde un número concreto:

```powershell
.\scripts\Crear-Lote-Largos.ps1 -ObjetivoMinutos 12 -Formato Horizontal -DesdeNumero 3
```

## Configuración

`config.psd1` controla la resolución, calidad, texto de marca, fuente, márgenes y mejora visual. No contiene API keys ni datos privados. Ajusta estos valores con moderación:

- `MarcaTexto`: texto usado si no existe `assets/marca.png`.
- `OpacidadMarca`, `MargenPx` y `EscalaLogoPx`: aspecto y posición de la marca.
- `CalidadCrf` y `Preset`: equilibrio entre calidad, tamaño y tiempo de codificación.
- `MejoraActiva`, `ReduccionRuido` y `Nitidez`: procesamiento visual previo a la marca.

## Registro de derechos

Completa una fila de `derechos.csv` por cada fuente, indicando origen, titular de derechos, licencia o permiso y fecha de verificación. El archivo no debe contener tokens, cuentas ni datos personales innecesarios.

## Archivos no versionados

El `.gitignore` evita subir vídeos, descargas `snaptik_*`, resultados de `salida/`, partes temporales, logs, imágenes de frame, entornos virtuales y `.env`. Así el repositorio conserva únicamente scripts, configuración sin claves, documentación y activos que decidas incluir deliberadamente.
