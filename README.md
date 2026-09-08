# FruitTales Video Pipeline

![PowerShell](https://img.shields.io/badge/PowerShell-5391FE?style=for-the-badge&logo=powershell&logoColor=white)
![FFmpeg](https://img.shields.io/badge/FFmpeg-007808?style=for-the-badge&logo=ffmpeg&logoColor=white)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

Pipeline de post-producción de vídeo para preparar Shorts y vídeos largos a partir de material propio, con licencia o con autorización expresa. Combina scripts de PowerShell y FFmpeg para automatizar tareas repetitivas y dejar cada resultado listo para revisión antes de publicar.

> Una marca de agua no concede derechos de uso. Antes de publicar, verifica la licencia o el permiso de cada fuente y regístralo en `derechos.csv`.

<a id="tabla-de-contenidos"></a>
## 🧭 Tabla de contenidos

- [Descripción](#descripcion)
- [Características](#caracteristicas)
- [Requisitos](#requisitos)
- [Instalación](#instalacion)
- [Uso](#uso)
- [Configuración](#configuracion)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Licencia y derechos de contenido](#licencia-y-derechos-de-contenido)
- [Próximas mejoras](#proximas-mejoras)

<a id="descripcion"></a>
## 🍊 Descripción

FruitTales Video Pipeline se encarga de la post-producción técnica de partes de vídeo ya creadas para las historias de FruitTales. No genera guiones ni contenido narrativo: compila las partes indicadas, las ordena, normaliza su formato, aplica una marca propia y prepara el resultado final para revisión antes de publicar.

El proyecto no requiere dependencias de Python ni API keys: funciona con PowerShell, FFmpeg y `ffprobe`.

<a id="caracteristicas"></a>
## ✨ Características

- 🧩 Compila, ordena y normaliza partes de vídeo existentes para crear Shorts y vídeos largos, aplicando reducción de ruido, ajuste de contraste/color y nitidez configurable.
- 📐 Convierte y adapta vídeos a vertical 9:16 o horizontal 16:9 con fondo desenfocado cuando es necesario.
- 💧 Añade una marca de agua mediante texto configurable o un PNG transparente.
- ✍️ Prepara flujos de publicación con títulos, descripciones, hashtags y prompts de miniatura para usar con IA.
- 🔊 Conserva el audio original y permite aplicar ajustes orientados a reducir riesgos de reclamaciones, siempre respetando los derechos del contenido.

<a id="requisitos"></a>
## 📋 Requisitos

- Windows PowerShell 5.1 o PowerShell 7.
- [FFmpeg](https://ffmpeg.org/) y `ffprobe` instalados y disponibles en `PATH`.
- Vídeos autorizados en formatos compatibles, como MP4 o MOV.

Comprueba que FFmpeg está disponible:

```powershell
ffmpeg -version
ffprobe -version
```

<a id="instalacion"></a>
## ⚙️ Instalación

1. Clona el repositorio.

   ```powershell
   git clone https://github.com/Cachopin789/fruittales-video-pipeline.git
   cd fruittales-video-pipeline
   ```

2. Instala FFmpeg y confirma que `ffmpeg -version` y `ffprobe -version` funcionan desde PowerShell.

3. Opcionalmente, añade un logo PNG transparente en `assets/marca.png`. Si no existe, se utilizará el texto definido en `config.psd1`.

4. Ajusta `config.psd1` para cambiar la marca, posición, resolución, calidad o mejora visual.

<a id="uso"></a>
## 🎬 Uso

### Menú interactivo

`Iniciar.ps1` es el punto de entrada recomendado para crear un Short o unir episodios en un vídeo largo.

```powershell
powershell -ExecutionPolicy Bypass -File .\Iniciar.ps1
```

### Crear un Short

`Procesar-Short.ps1` convierte un vídeo autorizado en un Short vertical de 1080 × 1920, con fondo desenfocado, mejora visual y marca propia.

```powershell
.\scripts\Procesar-Short.ps1 -Entrada .\entrada\clip.mp4
```

Para indicar una salida concreta:

```powershell
.\scripts\Procesar-Short.ps1 `
  -Entrada .\entrada\clip.mp4 `
  -Salida .\salida\mi-short.mp4
```

### Crear un vídeo largo

`Crear-VideoLargo.ps1` normaliza y une al menos dos episodios ordenados por nombre. Puede recortar los últimos segundos de cada parte antes de unirlas.

```powershell
.\scripts\Crear-VideoLargo.ps1 `
  -CarpetaPartes .\partes\mi-historia `
  -Titulo mi-historia `
  -RecorteFinalSegundos 1
```

Para crear una versión horizontal 16:9:

```powershell
.\scripts\Crear-VideoLargo.ps1 `
  -CarpetaPartes .\partes\mi-historia `
  -Titulo mi-historia-16x9 `
  -Formato Horizontal
```

### Crear un lote de vídeos largos

`Crear-Lote-Largos.ps1` agrupa los archivos descargados con el patrón `snaptik_*` en lotes de duración aproximada y genera un vídeo largo por cada lote.

```powershell
.\scripts\Crear-Lote-Largos.ps1 `
  -ObjetivoMinutos 12 `
  -Formato Vertical
```

Para retomar el proceso desde un lote específico:

```powershell
.\scripts\Crear-Lote-Largos.ps1 `
  -ObjetivoMinutos 12 `
  -Formato Horizontal `
  -DesdeNumero 3
```

<a id="configuracion"></a>
## 🔧 Configuración

`config.psd1` controla el aspecto y la codificación de salida. No contiene API keys ni datos personales.

- `MarcaTexto`: texto usado si no existe `assets/marca.png`.
- `OpacidadMarca`, `MargenPx` y `EscalaLogoPx`: tamaño y posición de la marca.
- `CalidadCrf` y `Preset`: equilibrio entre calidad, peso y tiempo de codificación.
- `MejoraActiva`, `ReduccionRuido` y `Nitidez`: ajustes de mejora visual.

<a id="estructura-del-proyecto"></a>
## 📂 Estructura del proyecto

```text
.
├── Iniciar.ps1                      # Menú interactivo principal
├── config.psd1                      # Ajustes de marca, vídeo y calidad
├── derechos.csv                     # Registro de fuentes, licencias y permisos
├── assets/
│   └── marca.png                    # Logo opcional con transparencia
├── entrada/                         # Vídeos autorizados de entrada
├── partes/                          # Episodios temporales para vídeos largos
├── salida/                          # Vídeos, imágenes y logs generados
├── scripts/
│   ├── Procesar-Short.ps1           # Genera Shorts verticales
│   ├── Crear-VideoLargo.ps1         # Normaliza y une episodios
│   └── Crear-Lote-Largos.ps1        # Crea lotes de vídeos largos
└── plantillas/
    └── ficha-publicacion.md         # Plantilla de publicación y metadatos
```

Las carpetas `partes/` y `salida/`, los vídeos, logs, descargas `snaptik_*`, entornos virtuales y `.env` están excluidos mediante `.gitignore`.

<a id="licencia-y-derechos-de-contenido"></a>
## 📜 Licencia y derechos de contenido

El código de este repositorio se distribuye bajo la [licencia MIT](LICENSE).

El código del repositorio y los derechos sobre los vídeos son asuntos distintos:

- Usa únicamente material propio, con licencia o con autorización expresa.
- Registra en `derechos.csv` la fuente, titular de derechos, licencia o permiso y fecha de verificación.
- Una marca de agua no convierte una obra de terceros en propia ni evita reclamaciones de copyright.
- Si la licencia exige atribución, inclúyela al publicar el contenido.

<a id="proximas-mejoras"></a>
## 🚀 Próximas mejoras

- Integrar generación asistida de metadatos de publicación desde una plantilla.
- Añadir validaciones automáticas de duración, formato y resolución de los vídeos de entrada.
- Crear un modo de vista previa para revisar la marca, el recorte y el formato antes de codificar el vídeo final.
