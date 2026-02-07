# Requisitos: Blog + Podcast para Error de Conexion

## Estado actual

- **Dominio**: `errordeconexion.com` (CNAME apuntando a GitHub Pages)
- **Contenido actual**: una sola pagina HTML con el logo del podcast y enlaces a Apple Podcasts, Spotify y RSS
- **Feed RSS**: alojado en Amazon S3 (`errordeconexion.s3.amazonaws.com/feed.xml`), compatible con Apple Podcasts, Spotify, etc.
- **Episodios**: 39 episodios (Ep001-Ep039), desde noviembre 2013 hasta septiembre 2020
- **Audio**: alojado en archive.org
- **Logo**: alojado en Amazon S3
- **Imagen de cabecera**: `EDC_header.jpeg` en el repositorio

## Objetivo

Convertir el sitio en un blog estatico alojado en GitHub Pages que:

1. Tenga una entrada por cada episodio del podcast extraida del feed XML existente
2. Genere un feed RSS compatible con podcasts (Apple Podcasts, Spotify, etc.)
3. El feed generado se pueda copiar a Amazon S3 para sustituir al actual sin romper nada

## Tecnologia

- **Jekyll** (generador de sitios estaticos nativo de GitHub Pages, no requiere CI/CD externo)
- Sin dependencias de JavaScript en el cliente
- HTML/CSS puro para el frontend

## Estructura del blog

### Pagina principal (`/`)

- Cabecera con la imagen `EDC_header.jpeg` a ancho completo
- Titulo "Error de Conexion" y subtitulo "Un podcast trasnochado sobre estar vivo en el siglo XXI"
- Lista de episodios ordenados del mas reciente al mas antiguo
- Cada episodio en la lista muestra:
  - Titulo (enlace a la pagina del episodio)
  - Fecha de publicacion
  - Descripcion breve (subtitle del feed)
- Botones/enlaces a Apple Podcasts, Spotify y feed RSS (como ahora)

### Pagina de episodio (`/epXXX-slug/`)

- Titulo del episodio
- Fecha de publicacion
- Numero de temporada y episodio
- Duracion
- Reproductor de audio HTML5 nativo (`<audio>`) con la URL del MP3/M4A
- Descripcion completa (contenido del campo `description` del feed, limpiado de HTML innecesario)
- Enlace para descargar el archivo de audio

### Feed RSS (`/feed.xml`)

El feed generado por Jekyll debe ser **100% compatible con podcasts**. Esto significa:

- Namespace `itunes` (`http://www.itunes.com/dtds/podcast-1.0.dtd`)
- Namespace `atom` con enlace `self`
- Namespace `podcast` (podcastindex) si estaba en el original
- Cabecera del canal con:
  - `<title>`, `<link>`, `<description>`, `<language>`
  - `<itunes:summary>`, `<itunes:author>`, `<itunes:image>`, `<itunes:explicit>`
  - `<itunes:owner>` con `<itunes:name>` y `<itunes:email>`
  - `<itunes:category>` (Society & Culture > Personal Journals)
  - `<itunes:type>` (episodic)
  - `<itunes:subtitle>`
  - `<image>` (RSS estandar)
  - `<copyright>`, `<managingEditor>`
- Cada item con:
  - `<title>`, `<link>`, `<pubDate>`, `<guid>`
  - `<description>` (contenido HTML)
  - `<enclosure>` con `url`, `length` y `type` del archivo de audio
  - `<itunes:subtitle>`, `<itunes:summary>`, `<itunes:author>`
  - `<itunes:image>`
  - `<itunes:season>`, `<itunes:episode>`, `<itunes:title>`
  - `<itunes:duration>`

**Importante**: el `<atom:link href>` del feed debe apuntar a la URL de S3 (`https://errordeconexion.s3.amazonaws.com/feed.xml`), no a la de GitHub Pages, ya que ese es el feed que consumen los agregadores de podcasts. Esto se configura como variable en `_config.yml` para poder cambiarlo facilmente.

## Generacion de posts desde el feed XML

Se creara un script (Python) que:

1. Parsee el archivo `feed.xml`
2. Extraiga todos los `<item>` con sus metadatos
3. Genere un archivo Markdown por cada episodio en `_posts/` con el formato:
   ```
   _posts/YYYY-MM-DD-slug.md
   ```
4. Cada archivo tendra front matter YAML con todos los campos necesarios:
   ```yaml
   ---
   layout: post
   title: "Ep039: Decepcionante, se han cargado el podcast"
   date: 2020-09-18 18:13:48 +0000
   guid: "http://errordeconexion.com/?p=368"
   audio_url: "https://archive.org/download/errordeconexion/EDC_EP039.mp3"
   audio_length: "57398597"
   audio_type: "audio/mpeg"
   itunes_subtitle: "De las propiedades de la horchata..."
   itunes_summary: "De las propiedades de la horchata..."
   itunes_season: 4
   itunes_episode: 39
   itunes_title: "Decepcionante, se han cargado el podcast"
   itunes_duration: "1:17:00"
   ---
   Contenido de la descripcion aqui.
   ```

## Diseno

- Minimalista, limpio, fondo claro
- Tipografia del sistema (como la actual)
- Responsive (movil y escritorio)
- Colores: fondo `#f4f4f4`, texto `#222`, acentos en negro `#000`
- La cabecera ocupa el ancho completo con `EDC_header.jpeg`
- Sin frameworks CSS externos

## Restricciones

- El feed XML original no se modifica: se usa solo como fuente para generar los posts
- Los archivos de audio siguen en archive.org, no se mueven
- El logo sigue en Amazon S3, no se mueve
- El CNAME se mantiene
- El sitio debe funcionar con GitHub Pages sin necesidad de GitHub Actions (Jekyll nativo)
- El feed generado debe poder copiarse a S3 tal cual y funcionar como feed de podcast

## Archivos a crear

```
errordeconexion/
  _config.yml              # Configuracion de Jekyll
  _layouts/
    default.html           # Layout base
    post.html              # Layout para episodios
  _includes/
    header.html            # Cabecera con imagen
    footer.html            # Pie de pagina
    player.html            # Reproductor de audio
  _posts/
    2013-11-24-ep001.md    # Un archivo por episodio (39 total)
    ...
    2020-09-18-ep039.md
  assets/
    css/
      style.css            # Estilos del sitio
  feed.xml                 # Template Liquid para generar el feed RSS de podcast
  index.html               # Pagina principal (listado de episodios)
  scripts/
    parse_feed.py           # Script para generar los _posts desde feed.xml
  EDC_header.jpeg           # Ya existe
  CNAME                     # Ya existe
  .gitignore                # Ignorar _site, .jekyll-cache, etc.
```

## Orden de implementacion

1. Crear el script `parse_feed.py` y generar los 39 posts en `_posts/`
2. Configurar Jekyll (`_config.yml`)
3. Crear layouts y includes
4. Crear la pagina principal (`index.html`)
5. Crear el template del feed RSS (`feed.xml`)
6. Crear los estilos CSS
7. Probar localmente con `jekyll serve`
8. Verificar que el feed generado es valido y compatible con podcasts
