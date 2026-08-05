---
name: generate-docs
description: Generar un visor HTML autocontenido, navegable y con búsqueda desde un directorio de documentación Markdown, YAML, CSV o texto. Usar cuando Codex deba publicar, regenerar o previsualizar documentación local como un único index.html, con configuración persistente opcional en .docs.json para portada, archivos destacados, filtros y branding.
---

# Generate Docs

## Objetivo

Generar un sitio de documentación estático de un solo archivo con `scripts/generate_docs.py`. Mantener los documentos fuente intactos y escribir únicamente el HTML solicitado.

## Flujo

1. Identificar el directorio que contiene la documentación.
2. Leer `.docs.json` si existe para entender la salida, portada, filtros y branding esperados.
3. Ejecutar el generador desde el directorio del skill o usando su ruta absoluta:

```bash
python3 scripts/generate_docs.py /ruta/a/documentos
```

4. Pasar opciones de CLI solamente para cambios puntuales. La precedencia es: defaults, `.docs.json`, CLI.
5. Confirmar la ruta, cantidad de documentos y portada reportadas por el comando.

## CLI

```bash
python3 scripts/generate_docs.py SOURCE_DIR \
  --output index.html \
  --title "Documentación" \
  --include md,yaml,csv,txt \
  --exclude-dir build
```

- Repetir `--include` o separar extensiones con comas.
- Repetir `--exclude-dir` para añadir nombres de directorio.
- Resolver una salida relativa respecto de `SOURCE_DIR`; aceptar una salida absoluta desde CLI.
- Usar `SOURCE_DIR/index.html` cuando no se configure otra salida.

## Configuración persistente

Usar `SOURCE_DIR/.docs.json` cuando la configuración deba conservarse entre ejecuciones:

```json
{
  "title": "Documentación del proyecto",
  "lang": "es",
  "output": "index.html",
  "home": "README.md",
  "include": ["md", "yaml", "yml", "csv", "txt"],
  "exclude_dirs": ["build", "tmp"],
  "featured": [
    {
      "path": "README.md",
      "tag": "INI",
      "label": "Introducción",
      "description": "Punto de entrada del proyecto"
    }
  ],
  "branding": {
    "name": "Mi Proyecto",
    "tagline": "Documentación técnica",
    "logo": "assets/logo.svg",
    "favicon": "assets/favicon.png",
    "accent_dark": "#22d3ee",
    "accent_light": "#0891b2"
  },
  "labels": {
    "search_placeholder": "Buscar en la documentación…",
    "featured": "Documentos principales",
    "all_documents": "Todos los documentos",
    "toc": "En esta página"
  }
}
```

Tratar todas las rutas del archivo como relativas a `SOURCE_DIR`. Corregir configuraciones rechazadas por el generador; no ignorar errores ni claves desconocidas. No agregar `.docs.json` al contenido publicado.

## Comportamiento

- Incluir por defecto archivos `md`, `markdown`, `yaml`, `yml`, `csv` y `txt` no vacíos.
- Excluir siempre directorios ocultos, `.git`, `.idea`, `.vscode`, `__pycache__`, `node_modules` y `vendor`.
- Elegir la portada configurada; de lo contrario usar `index.md`, `README.md` o el primer documento ordenado.
- Incrustar logo, favicon, documentos, estilos y runtime en el HTML.
- Conservar las imágenes enlazadas desde Markdown como rutas relativas al HTML generado.
- Admitir bloques cercados `chart` para gráficos de barras y progreso.

## Recurso incluido

- `scripts/generate_docs.py`: generador Python sin dependencias de terceros.
