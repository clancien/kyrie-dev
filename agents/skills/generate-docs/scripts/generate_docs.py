#!/usr/bin/env python3
"""Genera un visor HTML autocontenido desde un directorio de documentación."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------- config

DEFAULT_INCLUDE = ('md', 'markdown', 'yaml', 'yml', 'csv', 'txt')
DEFAULT_EXCLUDE_DIRS = {'.git', '.idea', '.vscode', '__pycache__', 'node_modules', 'vendor'}
DEFAULT_LABELS = {
    'all_documents': 'Todos los documentos',
    'featured': 'Documentos principales',
    'search_placeholder': 'Buscar en la documentación…',
    'toc': 'En esta página',
}
ALLOWED_TOP_LEVEL = {
    'branding', 'exclude_dirs', 'featured', 'home', 'include', 'labels', 'lang', 'output', 'title'
}
ALLOWED_BRANDING = {
    'accent_dark', 'accent_light', 'favicon', 'logo', 'name', 'tagline'
}
ALLOWED_LABELS = set(DEFAULT_LABELS)
ALLOWED_FEATURED = {'description', 'label', 'path', 'tag'}
HEX_COLOR = re.compile(r'^#[0-9a-fA-F]{6}$')


class ConfigError(ValueError):
    """Configuración inválida que debe mostrarse sin traceback."""

# --------------------------------------------------------------------------- helpers


def read_text(abs_path: str) -> str:
    with open(abs_path, 'r', encoding='utf-8', errors='replace') as fh:
        return fh.read()


def ext_of(path: str) -> str:
    base = path.rsplit('/', 1)[-1]
    return base.rsplit('.', 1)[-1].lower() if '.' in base else ''


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) > 1 and value[0] == value[-1] and value[0] in '"\'':
        value = value[1:-1]
    return value.strip()


def doc_title(path: str, text: str) -> str:
    """Titulo del documento: frontmatter `title:` > primer H1 > nombre de archivo."""
    base = path.rsplit('/', 1)[-1]
    if ext_of(path) not in ('md', 'markdown'):
        return base
    body = text
    front = re.match(r'^---\n(.*?)\n---[ \t]*(?:\n|$)', body, re.S)
    if front:
        found = re.search(r'^title:\s*(.+?)\s*$', front.group(1), re.M)
        body = body[front.end():]
        if found:
            title = strip_quotes(found.group(1))
            if title:
                return title
    heading = re.search(r'^#[ \t]+(.+?)[ \t]*#*[ \t]*$', body, re.M)
    if heading:
        return re.sub(r'[`*]', '', heading.group(1)).strip() or base
    return base


def normalize_relative_path(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f'`{field}` debe ser una ruta relativa no vacía.')
    candidate = Path(value)
    if candidate.is_absolute() or '..' in candidate.parts:
        raise ConfigError(f'`{field}` debe permanecer dentro del directorio fuente: {value!r}.')
    normalized = candidate.as_posix()
    if not normalized:
        raise ConfigError(f'`{field}` no puede apuntar al directorio raíz.')
    return normalized


def string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ConfigError(f'`{field}` debe ser una lista de textos no vacíos.')
    return [item.strip() for item in value]


def ensure_known_keys(data: dict[str, Any], allowed: set[str], field: str) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ConfigError(f'Claves desconocidas en `{field}`: {", ".join(unknown)}.')


def load_config(source_dir: Path) -> dict[str, Any]:
    config_path = source_dir / '.docs.json'
    if not config_path.exists():
        return {}
    try:
        data = json.loads(config_path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exception:
        raise ConfigError(
            f'{config_path}: JSON inválido en línea {exception.lineno}, columna {exception.colno}: '
            f'{exception.msg}.'
        ) from exception
    except OSError as exception:
        raise ConfigError(f'No se pudo leer {config_path}: {exception}.') from exception
    if not isinstance(data, dict):
        raise ConfigError(f'{config_path}: la raíz debe ser un objeto JSON.')
    ensure_known_keys(data, ALLOWED_TOP_LEVEL, '.docs.json')
    return data


def validate_config(data: dict[str, Any], source_dir: Path) -> dict[str, Any]:
    config = dict(data)
    for field in ('title', 'lang', 'output', 'home'):
        if field in config and (not isinstance(config[field], str) or not config[field].strip()):
            raise ConfigError(f'`{field}` debe ser un texto no vacío.')
    if 'output' in config:
        config['output'] = normalize_relative_path(config['output'], 'output')
    if 'home' in config:
        config['home'] = normalize_relative_path(config['home'], 'home')
    if 'include' in config:
        config['include'] = [item.lower().lstrip('.') for item in string_list(config['include'], 'include')]
        if any(not re.fullmatch(r'[a-z0-9]+', item) for item in config['include']):
            raise ConfigError('Cada extensión de `include` debe contener solo letras y números.')
    if 'exclude_dirs' in config:
        config['exclude_dirs'] = string_list(config['exclude_dirs'], 'exclude_dirs')
        if any('/' in item or '\\' in item or item in ('.', '..') for item in config['exclude_dirs']):
            raise ConfigError('Cada elemento de `exclude_dirs` debe ser un nombre de directorio, no una ruta.')

    featured = config.get('featured', [])
    if not isinstance(featured, list):
        raise ConfigError('`featured` debe ser una lista de objetos.')
    normalized_featured = []
    for index, item in enumerate(featured):
        field = f'featured[{index}]'
        if not isinstance(item, dict):
            raise ConfigError(f'`{field}` debe ser un objeto.')
        ensure_known_keys(item, ALLOWED_FEATURED, field)
        if 'path' not in item:
            raise ConfigError(f'`{field}.path` es obligatorio.')
        normalized = {'path': normalize_relative_path(item['path'], f'{field}.path')}
        for key in ('tag', 'label', 'description'):
            value = item.get(key, '')
            if not isinstance(value, str):
                raise ConfigError(f'`{field}.{key}` debe ser texto.')
            normalized[key] = value.strip()
        normalized_featured.append(normalized)
    config['featured'] = normalized_featured

    branding = config.get('branding', {})
    if not isinstance(branding, dict):
        raise ConfigError('`branding` debe ser un objeto.')
    ensure_known_keys(branding, ALLOWED_BRANDING, 'branding')
    branding = dict(branding)
    for key in ('name', 'tagline'):
        if key in branding and (not isinstance(branding[key], str) or not branding[key].strip()):
            raise ConfigError(f'`branding.{key}` debe ser texto no vacío.')
    for key in ('accent_dark', 'accent_light'):
        if key in branding and (not isinstance(branding[key], str) or not HEX_COLOR.fullmatch(branding[key])):
            raise ConfigError(f'`branding.{key}` debe ser un color hexadecimal como `#22d3ee`.')
    for key in ('logo', 'favicon'):
        if key in branding:
            rel = normalize_relative_path(branding[key], f'branding.{key}')
            asset = source_dir / rel
            if not asset.is_file():
                raise ConfigError(f'`branding.{key}` no existe: {asset}.')
            branding[key] = rel
    config['branding'] = branding

    labels = config.get('labels', {})
    if not isinstance(labels, dict):
        raise ConfigError('`labels` debe ser un objeto.')
    ensure_known_keys(labels, ALLOWED_LABELS, 'labels')
    if any(not isinstance(value, str) or not value.strip() for value in labels.values()):
        raise ConfigError('Todos los valores de `labels` deben ser textos no vacíos.')
    config['labels'] = {key: value.strip() for key, value in labels.items()}
    return config


def parse_include_cli(values: list[str] | None) -> list[str] | None:
    if not values:
        return None
    extensions = [part.strip().lower().lstrip('.') for value in values for part in value.split(',') if part.strip()]
    if not extensions or any(not re.fullmatch(r'[a-z0-9]+', item) for item in extensions):
        raise ConfigError('`--include` requiere extensiones separadas por comas, por ejemplo `md,yaml,txt`.')
    return extensions


def asset_data_uri(source_dir: Path, relative_path: str | None) -> str | None:
    if not relative_path:
        return None
    path = source_dir / relative_path
    mime, _ = mimetypes.guess_type(path.name)
    if not mime or not (mime.startswith('image/') or mime == 'image/x-icon'):
        raise ConfigError(f'El recurso de branding no es una imagen compatible: {path}.')
    try:
        encoded = base64.b64encode(path.read_bytes()).decode('ascii')
    except OSError as exception:
        raise ConfigError(f'No se pudo leer el recurso de branding {path}: {exception}.') from exception
    return f'data:{mime};base64,{encoded}'


# --------------------------------------------------------------------------- collect


def collect_files(doc_dir: Path, include_exts: set[str], skip_dirs: set[str]) -> dict[str, dict[str, str]]:
    """Recopilar documentos de texto, indexados por ruta relativa POSIX."""
    files: dict[str, dict] = {}
    for root, dirs, names in os.walk(doc_dir):
        dirs[:] = sorted(d for d in dirs if d not in skip_dirs and not d.startswith('.'))
        for name in sorted(names):
            if name == '.docs.json':
                continue
            abs_path = Path(root) / name
            rel = abs_path.relative_to(doc_dir).as_posix()
            if ext_of(rel) not in include_exts:
                continue
            content = read_text(str(abs_path))
            if not content.strip():
                continue
            files[rel] = {'t': doc_title(rel, content), 'c': content}
    return dict(sorted(files.items()))


# --------------------------------------------------------------------------- render


def detect_home(files: dict[str, dict[str, str]], configured: str | None) -> str:
    if configured:
        if configured not in files:
            raise ConfigError(f'El documento inicial configurado no fue incluido: {configured}.')
        return configured
    lower_paths = {path.lower(): path for path in files}
    for candidate in ('index.md', 'readme.md'):
        if candidate in lower_paths:
            return lower_paths[candidate]
    return next(iter(files))


def build_primary(
    files: dict[str, dict[str, str]], home: str, configured: list[dict[str, str]]
) -> list[dict[str, str]]:
    primary: list[dict[str, str]] = []
    for item in configured:
        path = item['path']
        if path not in files:
            raise ConfigError(f'El documento destacado no fue incluido: {path}.')
        primary.append({
            'path': path,
            'tag': item['tag'] or Path(path).suffix.lstrip('.').upper()[:3] or 'DOC',
            'label': item['label'] or files[path]['t'],
            'desc': item['description'],
        })
    if not any(item['path'] == home for item in primary):
        primary.insert(0, {
            'path': home,
            'tag': 'INI',
            'label': files[home]['t'],
            'desc': '',
        })
    return primary


def build_payload(files: dict, generated: str, settings: dict[str, Any], primary: list[dict]) -> dict:
    return {'files': files, 'generated': generated, 'primary': primary, 'settings': settings}


def render_html(payload: dict) -> str:
    data = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    # `</` nunca debe aparecer literal dentro del <script type="application/json">.
    data = data.replace('</', r'<\/')
    script = '<script type="application/json" id="payload">%s</script>' % data
    return HTML_HEAD + '\n' + script + '\n' + HTML_TAIL


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Genera un visor HTML autocontenido desde un directorio de documentación.'
    )
    parser.add_argument('source_dir', help='Directorio que contiene la documentación.')
    parser.add_argument('-o', '--output', help='Ruta de salida, relativa al directorio fuente o absoluta.')
    parser.add_argument('--title', help='Título del sitio; prevalece sobre .docs.json.')
    parser.add_argument(
        '--include', action='append', metavar='EXT[,EXT...]',
        help='Extensiones que se incluirán. Puede repetirse y acepta valores separados por comas.'
    )
    parser.add_argument(
        '--exclude-dir', action='append', default=[], metavar='NAME',
        help='Nombre de directorio que se excluirá; puede repetirse.'
    )
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_dir = Path(args.source_dir).expanduser().resolve()
    if not source_dir.is_dir():
        raise ConfigError(f'El directorio fuente no existe o no es un directorio: {source_dir}.')

    config = validate_config(load_config(source_dir), source_dir)
    include = set(parse_include_cli(args.include) or config.get('include', DEFAULT_INCLUDE))
    cli_exclude_dirs = [item.strip() for item in args.exclude_dir]
    exclude_dirs = DEFAULT_EXCLUDE_DIRS | set(config.get('exclude_dirs', [])) | set(cli_exclude_dirs)
    if any('/' in item or '\\' in item or item in ('.', '..', '') for item in cli_exclude_dirs):
        raise ConfigError('Cada `--exclude-dir` debe ser un nombre de directorio, no una ruta.')

    files = collect_files(source_dir, include, exclude_dirs)
    if not files:
        raise ConfigError(f'No se encontraron documentos no vacíos en {source_dir}.')
    home = detect_home(files, config.get('home'))
    primary = build_primary(files, home, config.get('featured', []))

    if args.title is not None and not args.title.strip():
        raise ConfigError('`--title` debe ser un texto no vacío.')
    title = (args.title or config.get('title') or source_dir.name or 'Documentación').strip()
    branding = config.get('branding', {})
    labels = {**DEFAULT_LABELS, **config.get('labels', {})}
    settings = {
        'branding': {
            'accent_dark': branding.get('accent_dark', '#22d3ee'),
            'accent_light': branding.get('accent_light', '#0891b2'),
            'favicon': asset_data_uri(source_dir, branding.get('favicon')),
            'logo': asset_data_uri(source_dir, branding.get('logo')),
            'name': branding.get('name', title),
            'tagline': branding.get('tagline', 'documentación'),
        },
        'home': home,
        'labels': labels,
        'lang': config.get('lang', 'es'),
        'title': title,
    }
    generated = datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %z')
    payload = build_payload(files, generated, settings, primary)
    html = render_html(payload)

    if args.output is not None and not args.output.strip():
        raise ConfigError('`--output` debe ser una ruta no vacía.')
    output_value = args.output or config.get('output', 'index.html')
    output = Path(output_value).expanduser()
    if not output.is_absolute():
        output = source_dir / output
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        output.write_text(html, encoding='utf-8')
    except OSError as exception:
        raise ConfigError(f'No se pudo escribir {output}: {exception}.') from exception

    print(f'Visor generado: {output}')
    print(f'  documentos: {len(files)}')
    print(f'  inicio    : {home}')
    print(f'  tamaño    : {len(html) / 1024:.1f} KB')
    return 0


def main() -> int:
    try:
        return run()
    except ConfigError as exception:
        print(f'Error: {exception}', file=sys.stderr)
        return 2


# --------------------------------------------------------------------------- shell

HTML_HEAD = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Documentación</title>
<style>
:root{
  --bg:#12151a; --bg-alt:#171b22; --bg-soft:#1d222b; --border:#2a313d;
  --fg:#dde3ec; --fg-dim:#95a1b3; --fg-mute:#6b788c;
  --accent:#22d3ee; --accent-soft:rgba(34,211,238,.14); --accent-2:#7dd3fc;
  --warn:#fbbf24; --ok:#34d399; --danger:#f87171;
  --code-bg:#0f1319; --mark:#fde68a; --mark-fg:#1b1b1b;
  /* graficos: par validado (OKLab, CVD protan/deutan) sobre superficie --bg-alt */
  --c-done:#16a34a; --c-review:#0891b2;
  /* etapas pendientes: rampa neutra ordinal, del menos al mas avanzado */
  --c-p1:#4b5563; --c-p2:#6b788c; --c-p3:#95a1b3;
  --sidebar-w:290px; --toc-w:220px;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
  --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
}
html[data-theme="light"]{
  --bg:#f7f8fa; --bg-alt:#ffffff; --bg-soft:#eef1f5; --border:#dde1e8;
  --fg:#1c2430; --fg-dim:#5a6577; --fg-mute:#8a94a4;
  --accent:#0891b2; --accent-soft:rgba(8,145,178,.12); --accent-2:#0e7490;
  --code-bg:#f2f4f7; --mark:#fde68a; --mark-fg:#1b1b1b;
  /* mismo par validado contra superficie clara; neutros re-escalonados hacia oscuro */
  --c-done:#16a34a; --c-review:#0891b2;
  --c-p1:#b3bcc9; --c-p2:#8a94a4; --c-p3:#5a6577;
}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--sans);font-size:15px;line-height:1.65;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}

/* ---------- layout ---------- */
header.top{
  position:fixed;top:0;left:0;right:0;height:52px;z-index:40;display:flex;align-items:center;gap:12px;
  padding:0 14px;background:var(--bg-alt);border-bottom:1px solid var(--border)
}
.brand{display:flex;align-items:center;gap:9px;font-weight:650;letter-spacing:.02em;white-space:nowrap}
.brand .dot{width:9px;height:9px;border-radius:50%;background:var(--accent);box-shadow:0 0 12px var(--accent)}
.brand img{width:24px;height:24px;object-fit:contain;border-radius:4px}
.brand small{color:var(--fg-mute);font-weight:500;letter-spacing:0}
.search-wrap{flex:1;max-width:520px;position:relative;margin-left:8px}
#search{
  width:100%;padding:7px 30px 7px 32px;border-radius:8px;border:1px solid var(--border);
  background:var(--bg-soft);color:var(--fg);font-family:var(--sans);font-size:13.5px;outline:none
}
#search:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.search-wrap .ico{position:absolute;left:10px;top:50%;transform:translateY(-50%);color:var(--fg-mute);font-size:13px;pointer-events:none}
.search-wrap kbd{position:absolute;right:8px;top:50%;transform:translateY(-50%);color:var(--fg-mute);font-size:11px;border:1px solid var(--border);border-radius:4px;padding:1px 5px;font-family:var(--mono)}
.top-actions{display:flex;align-items:center;gap:6px;margin-left:auto}
button.icon{
  background:var(--bg-soft);border:1px solid var(--border);color:var(--fg-dim);border-radius:8px;
  height:32px;min-width:32px;padding:0 9px;cursor:pointer;font-size:13px;font-family:var(--sans)
}
button.icon:hover{color:var(--fg);border-color:var(--accent);background:var(--accent-soft)}
#menu-btn{display:none}

aside.sidebar{
  position:fixed;top:52px;bottom:0;left:0;width:var(--sidebar-w);overflow-y:auto;
  background:var(--bg-alt);border-right:1px solid var(--border);padding:14px 0 40px
}
.side-title{padding:10px 16px 6px;font-size:10.5px;letter-spacing:.13em;text-transform:uppercase;color:var(--fg-mute);font-weight:700}
.nav-item{
  display:block;padding:6px 16px 6px 16px;color:var(--fg-dim);font-size:13.5px;
  border-left:2px solid transparent;cursor:pointer;word-break:break-word
}
.nav-item:hover{background:var(--bg-soft);color:var(--fg);text-decoration:none}
.nav-item.active{background:var(--accent-soft);color:var(--accent);border-left-color:var(--accent);font-weight:600}
.nav-item .sub{display:block;font-size:11.5px;color:var(--fg-mute);line-height:1.35}
.nav-item.active .sub{color:var(--fg-dim)}
.pin{display:flex;gap:9px;align-items:flex-start}
.pin .tag{
  flex:none;margin-top:2px;font-family:var(--mono);font-size:9.5px;letter-spacing:.06em;color:var(--accent);
  border:1px solid var(--border);border-radius:4px;padding:1px 4px;background:var(--bg-soft)
}
details.group{border-top:1px solid var(--border);margin-top:8px}
details.group>summary{
  padding:8px 16px;cursor:pointer;color:var(--fg-dim);font-size:12px;font-weight:650;
  letter-spacing:.04em;list-style:none;display:flex;align-items:center;gap:6px;user-select:none
}
details.group>summary::-webkit-details-marker{display:none}
details.group>summary:before{content:"▸";color:var(--fg-mute);font-size:10px;transition:transform .15s}
details.group[open]>summary:before{transform:rotate(90deg)}
details.group>summary:hover{color:var(--fg);background:var(--bg-soft)}
details.group>summary .count{margin-left:auto;color:var(--fg-mute);font-size:11px;font-family:var(--mono)}
.group .nav-item{padding-left:30px;font-size:12.8px}

main{
  margin:52px 0 0 var(--sidebar-w);padding:26px 34px 90px;
  max-width:none;min-height:calc(100vh - 52px)
}
.with-toc main{margin-right:var(--toc-w)}
aside.toc{
  position:fixed;top:52px;right:0;bottom:0;width:var(--toc-w);overflow-y:auto;
  padding:20px 14px 60px;border-left:1px solid var(--border);background:var(--bg)
}
aside.toc .side-title{padding:0 0 8px}
.toc a{display:block;color:var(--fg-mute);font-size:12.3px;padding:3px 8px;border-left:2px solid transparent;line-height:1.4}
.toc a:hover{color:var(--fg);text-decoration:none}
.toc a.active{color:var(--accent);border-left-color:var(--accent);background:var(--accent-soft)}
.toc a.lvl3{padding-left:20px;font-size:11.8px}
.toc a.lvl4{padding-left:32px;font-size:11.4px;color:var(--fg-mute)}

/* ---------- doc header ---------- */
.doc-head{border-bottom:1px solid var(--border);padding-bottom:14px;margin-bottom:22px}
.crumbs{font-family:var(--mono);font-size:11.5px;color:var(--fg-mute);display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.crumbs .file{color:var(--accent-2)}
.doc-head h1.doc-title{margin:8px 0 0;font-size:26px;line-height:1.25;letter-spacing:-.01em}
.doc-meta{margin-top:6px;font-size:12px;color:var(--fg-mute);display:flex;gap:14px;flex-wrap:wrap}

/* ---------- markdown ---------- */
.md{max-width:900px}
.md h1,.md h2,.md h3,.md h4,.md h5,.md h6{line-height:1.3;margin:1.9em 0 .6em;font-weight:660;letter-spacing:-.005em;scroll-margin-top:70px;position:relative}
.md h1{font-size:25px;border-bottom:1px solid var(--border);padding-bottom:.3em}
.md h2{font-size:20.5px;border-bottom:1px solid var(--border);padding-bottom:.28em;color:var(--fg)}
.md h3{font-size:17px;color:var(--accent-2)}
.md h4{font-size:15px;color:var(--fg-dim);text-transform:none}
.md h5,.md h6{font-size:13.5px;color:var(--fg-dim)}
.md h1:first-child,.md h2:first-child{margin-top:0}
.md .anchor{position:absolute;left:-18px;color:var(--fg-mute);opacity:0;font-weight:400;text-decoration:none}
.md h1:hover .anchor,.md h2:hover .anchor,.md h3:hover .anchor,.md h4:hover .anchor{opacity:.6}
.md p{margin:.75em 0}
.md ul,.md ol{margin:.6em 0;padding-left:1.5em}
.md li{margin:.28em 0}
.md li>ul,.md li>ol{margin:.25em 0}
.md blockquote{
  margin:1em 0;padding:.5em 1em;border-left:3px solid var(--accent);
  background:var(--bg-soft);border-radius:0 6px 6px 0;color:var(--fg-dim)
}
.md blockquote p{margin:.35em 0}
.md hr{border:0;border-top:1px solid var(--border);margin:2em 0}
.md code{
  font-family:var(--mono);font-size:.87em;background:var(--code-bg);border:1px solid var(--border);
  border-radius:5px;padding:.1em .35em;color:var(--accent-2);word-break:break-word
}
.md pre.code{
  position:relative;background:var(--code-bg);border:1px solid var(--border);border-radius:9px;
  padding:13px 15px;overflow-x:auto;margin:1em 0;font-size:12.8px;line-height:1.55
}
.md pre.code code{background:none;border:0;padding:0;color:var(--fg);font-size:inherit;white-space:pre}
.md pre.code[data-lang]:before{
  content:attr(data-lang);position:absolute;top:0;right:0;font-family:var(--mono);font-size:10px;
  letter-spacing:.08em;text-transform:uppercase;color:var(--fg-mute);background:var(--bg-soft);
  border-left:1px solid var(--border);border-bottom:1px solid var(--border);border-radius:0 8px 0 8px;padding:2px 7px
}
.copy-btn{
  position:absolute;top:6px;right:8px;opacity:0;transition:opacity .12s;background:var(--bg-soft);
  border:1px solid var(--border);color:var(--fg-dim);border-radius:6px;font-size:10.5px;padding:2px 7px;cursor:pointer;z-index:2
}
pre.code:hover .copy-btn{opacity:1}
.copy-btn:hover{color:var(--accent);border-color:var(--accent)}
.md table{border-collapse:collapse;margin:1.1em 0;font-size:13.2px;display:block;overflow-x:auto;max-width:100%}
.md th,.md td{border:1px solid var(--border);padding:7px 11px;text-align:left;vertical-align:top}
.md th{background:var(--bg-soft);font-weight:650;color:var(--fg);white-space:nowrap}
.md tbody tr:nth-child(even){background:rgba(127,127,127,.045)}
.md img{max-width:100%;border-radius:8px;border:1px solid var(--border)}
.md del{color:var(--fg-mute)}
.md .task{margin-right:.4em}
.md a[data-missing="1"]{color:var(--warn);border-bottom:1px dotted var(--warn)}
.md mark{background:var(--mark);color:var(--mark-fg);border-radius:3px;padding:0 2px}

/* frontmatter + yaml */
details.frontmatter{border:1px solid var(--border);border-radius:9px;background:var(--bg-alt);margin:0 0 20px}
details.frontmatter>summary{
  cursor:pointer;padding:8px 13px;font-size:12px;color:var(--fg-mute);font-family:var(--mono);
  letter-spacing:.04em;user-select:none
}
details.frontmatter>summary:hover{color:var(--accent)}
details.frontmatter pre.code{margin:0;border:0;border-top:1px solid var(--border);border-radius:0 0 8px 8px}
.y-key{color:var(--accent-2)}
.y-com{color:var(--fg-mute);font-style:italic}
.y-val{color:var(--fg)}
.y-num{color:var(--ok)}
.csv-info{font-size:12px;color:var(--fg-mute);font-family:var(--mono);margin-bottom:8px}

/* ---------- graficos (bloques ```chart) ---------- */
.chart{
  background:var(--bg-alt);border:1px solid var(--border);border-radius:10px;
  padding:15px 17px 13px;margin:1.2em 0;max-width:820px
}
.chart-title{
  font-size:10.5px;letter-spacing:.13em;text-transform:uppercase;color:var(--fg-mute);
  font-weight:700;margin-bottom:12px
}
.chart-hero{display:flex;align-items:baseline;flex-wrap:wrap;gap:4px 12px;margin:0 0 16px}
.chart-hero b{font-size:48px;line-height:1;font-weight:660;letter-spacing:-.025em;color:var(--fg)}
.chart-hero span{font-size:12.5px;color:var(--fg-dim)}
.chart-legend{display:flex;flex-wrap:wrap;gap:6px 16px;margin:0 0 12px;font-size:11.5px;color:var(--fg-dim)}
.chart-legend i{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:6px;vertical-align:middle}
.chart-legend i.fill-track{background:var(--bg-soft);border:1px solid var(--border)}
.crow{display:flex;align-items:center;gap:11px;margin:7px 0}
.crow .clabel{
  flex:0 0 clamp(84px,25%,186px);color:var(--fg-dim);font-size:12.3px;text-align:right;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis
}
.crow .ctrack{
  flex:1;min-width:70px;height:14px;border-radius:4px;background:var(--bg-soft);
  display:flex;overflow:hidden
}
.crow .cbar{flex:1;min-width:70px;height:14px;display:flex}
.crow .cseg{height:100%}
.crow .cseg+.cseg{border-left:2px solid var(--bg-alt)}
.crow .cfill{height:100%;border-radius:0 4px 4px 0}
.crow .cval{flex:0 0 96px;font-family:var(--mono);font-size:11.5px;color:var(--fg-dim);white-space:nowrap}
.crow.total .clabel{color:var(--fg);font-weight:650}
.crow.total .ctrack{height:18px}
.chart-note{margin:12px 0 0;font-size:11.5px;color:var(--fg-mute)}
.fill-done{background:var(--c-done)}
.fill-review{background:var(--c-review)}
.fill-p3{background:var(--c-p3)}
.fill-p2{background:var(--c-p2)}
.fill-p1{background:var(--c-p1)}
@media (max-width:640px){
  .crow{gap:8px}
  .crow .clabel{flex-basis:88px;font-size:11.5px}
  .crow .cval{flex-basis:76px;font-size:10.8px}
  .chart-hero b{font-size:38px}
}

/* ---------- search results ---------- */
.result{display:block;padding:9px 16px;border-bottom:1px solid var(--border);cursor:pointer}
.result:hover{background:var(--bg-soft);text-decoration:none}
.result .rtitle{font-size:13px;color:var(--fg);font-weight:600}
.result .rpath{font-family:var(--mono);font-size:10.5px;color:var(--fg-mute)}
.result .rsnip{font-size:11.8px;color:var(--fg-dim);margin-top:3px;line-height:1.45;max-height:3.4em;overflow:hidden}
.result mark{background:var(--accent-soft);color:var(--accent);border-radius:2px}
.empty{padding:18px 16px;color:var(--fg-mute);font-size:13px}

/* ---------- misc ---------- */
#toast{
  position:fixed;bottom:20px;left:50%;transform:translateX(-50%) translateY(20px);opacity:0;
  background:var(--bg-alt);border:1px solid var(--accent);color:var(--fg);padding:9px 16px;border-radius:9px;
  font-size:13px;z-index:80;transition:opacity .18s,transform .18s;pointer-events:none;box-shadow:0 8px 26px rgba(0,0,0,.35);max-width:80vw
}
#toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
.missing{border:1px dashed var(--warn);border-radius:10px;padding:20px;color:var(--fg-dim)}
.missing code{color:var(--warn)}
.backdrop{display:none;position:fixed;inset:52px 0 0 0;background:rgba(0,0,0,.5);z-index:29}
@media (max-width:1180px){ .with-toc main{margin-right:0} aside.toc{display:none} }
@media (max-width:860px){
  #menu-btn{display:inline-block}
  aside.sidebar{transform:translateX(-100%);transition:transform .2s;z-index:30;width:82vw;max-width:330px}
  body.nav-open aside.sidebar{transform:none}
  body.nav-open .backdrop{display:block}
  main{margin-left:0;padding:20px 16px 80px}
  .search-wrap kbd{display:none}
}
@media print{
  header.top,aside.sidebar,aside.toc,.copy-btn{display:none}
  main{margin:0;padding:0}
  body{background:#fff;color:#000}
}
</style>
</head>
<body>

<header class="top">
  <button class="icon" id="menu-btn" title="Menú">☰</button>
  <div class="brand"><span class="dot" id="brand-mark"></span><span id="brand-name">Documentación</span><small id="brand-tagline">· docs</small></div>
  <div class="search-wrap">
    <span class="ico">⌕</span>
    <input id="search" type="text" placeholder="Buscar en la documentación…" autocomplete="off" spellcheck="false">
    <kbd>/</kbd>
  </div>
  <div class="top-actions">
    <button class="icon" id="raw-btn" title="Ver Markdown original">&lt;/&gt;</button>
    <button class="icon" id="theme-btn" title="Cambiar tema">◐</button>
  </div>
</header>

<div class="backdrop" id="backdrop"></div>
<aside class="sidebar" id="sidebar"></aside>
<main id="main"></main>
<aside class="toc" id="toc"></aside>
<div id="toast"></div>
"""

HTML_TAIL = r"""<script>
(function(){
"use strict";

var DATA    = JSON.parse(document.getElementById('payload').textContent);
var FILES   = DATA.files;
var PRIMARY = DATA.primary;
var GEN     = DATA.generated;
var SETTINGS = DATA.settings;
var BRAND = SETTINGS.branding;
var LABELS = SETTINGS.labels;

var elMain = document.getElementById('main');
var elSide = document.getElementById('sidebar');
var elToc  = document.getElementById('toc');
var elSearch = document.getElementById('search');

var currentPath = null, currentAnchor = null, showRaw = false, searchTerm = '';

function applyAccent(){
  var light = document.documentElement.getAttribute('data-theme') === 'light';
  var color = light ? BRAND.accent_light : BRAND.accent_dark;
  document.documentElement.style.setProperty('--accent', color);
  document.documentElement.style.setProperty('--accent-2', color);
  document.documentElement.style.setProperty('--accent-soft', color + '24');
}

function applySettings(){
  document.documentElement.lang = SETTINGS.lang;
  elSearch.placeholder = LABELS.search_placeholder;
  document.getElementById('brand-name').textContent = BRAND.name;
  document.getElementById('brand-tagline').textContent = BRAND.tagline ? '· ' + BRAND.tagline : '';
  if(BRAND.logo){
    var mark = document.getElementById('brand-mark');
    var logo = document.createElement('img');
    logo.src = BRAND.logo; logo.alt = '';
    mark.replaceWith(logo);
  }
  if(BRAND.favicon){
    var icon = document.createElement('link');
    icon.rel = 'icon'; icon.href = BRAND.favicon;
    document.head.appendChild(icon);
  }
  applyAccent();
}

/* ========================= utils ========================= */
function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function slugify(t){
  return String(t).toLowerCase().trim()
    .replace(/<[^>]*>/g,'')
    .replace(/[`*_~]/g,'')
    .replace(/[‘’“”]/g,'')
    .replace(/[^\p{L}\p{N} \-_]/gu,'')
    .replace(/\s+/g,'-');
}
function dirname(p){ var i = p.lastIndexOf('/'); return i < 0 ? '' : p.slice(0, i); }
function basename(p){ var i = p.lastIndexOf('/'); return i < 0 ? p : p.slice(i + 1); }
function ext(p){ var b = basename(p), i = b.lastIndexOf('.'); return i < 0 ? '' : b.slice(i + 1).toLowerCase(); }
function resolvePath(base, rel){
  if(rel.charAt(0) === '/') return rel.replace(/^\/+/, '');
  var parts = (base ? base.split('/') : []).concat(rel.split('/'));
  var out = [];
  for(var i = 0; i < parts.length; i++){
    var s = parts[i];
    if(s === '' || s === '.') continue;
    if(s === '..'){ if(out.length && out[out.length-1] !== '..') out.pop(); else out.push('..'); }
    else out.push(s);
  }
  return out.join('/');
}
function splitHash(href){
  var i = href.indexOf('#');
  return i < 0 ? [href, null] : [href.slice(0, i), decodeURIComponent(href.slice(i + 1))];
}
function toast(msg){
  var t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  clearTimeout(t._t); t._t = setTimeout(function(){ t.classList.remove('show'); }, 2600);
}

/* ========================= markdown ========================= */
function inlineMd(src){
  var codes = [];
  var s = String(src).replace(/(`+)([\s\S]*?)\1/g, function(m, f, c){
    codes.push(c.replace(/^ (.*) $/, '$1'));
    return '\u0001' + (codes.length - 1) + '\u0001';
  });
  s = esc(s);
  s = s.replace(/!\[([^\]]*)\]\(\s*([^)\s]+)(?:\s+&quot;[^&]*&quot;)?\s*\)/g, function(m, alt, src2){
    return '<img alt="' + alt + '" data-src="' + src2 + '">';
  });
  s = s.replace(/\[([^\]]*)\]\(\s*([^)\s]*)(?:\s+&quot;([^&]*)&quot;)?\s*\)/g, function(m, txt, href, title){
    return '<a href="' + href + '"' + (title ? ' title="' + title + '"' : '') + '>' + txt + '</a>';
  });
  s = s.replace(/&lt;(https?:\/\/[^\s&<>]+)&gt;/g, '<a href="$1">$1</a>');
  s = s.replace(/\*\*\*([^*]+)\*\*\*/g, '<strong><em>$1</em></strong>');
  s = s.replace(/\*\*([\s\S]+?)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/(^|[^\w*\\])\*([^*\n]+)\*(?!\*)/g, '$1<em>$2</em>');
  s = s.replace(/(^|[^\w_\\])__([^_\n]+)__(?!\w)/g, '$1<strong>$2</strong>');
  s = s.replace(/(^|[^\w_\\])_([^_\n]+)_(?!\w)/g, '$1<em>$2</em>');
  s = s.replace(/~~([\s\S]+?)~~/g, '<del>$1</del>');
  s = s.replace(/\u0001(\d+)\u0001/g, function(m, i){ return '<code>' + esc(codes[+i]) + '</code>'; });
  return s;
}

function isFence(l){ return /^ {0,3}(`{3,}|~{3,})/.test(l); }
function isHeading(l){ return /^ {0,3}#{1,6}\s/.test(l); }
function isHr(l){ return /^ {0,3}([-*_])[ \t]*(\1[ \t]*){2,}$/.test(l); }
function isQuote(l){ return /^ {0,3}>/.test(l); }
function isListItem(l){ return /^ *([-*+]|\d+[.)])(\s+|$)/.test(l); }
function isTableSep(l){ return !!l && /^ {0,3}\|?[ :\-|]+$/.test(l) && l.indexOf('-') >= 0 && l.indexOf('|') >= 0; }
function isBlockStart(l, next){
  return isFence(l) || isHeading(l) || isHr(l) || isQuote(l) || isListItem(l) ||
         (l.indexOf('|') >= 0 && isTableSep(next));
}

function splitRow(row){
  row = row.trim().replace(/^\|/, '').replace(/\|$/, '');
  var cells = [], cur = '';
  for(var i = 0; i < row.length; i++){
    var ch = row.charAt(i);
    if(ch === '\\' && row.charAt(i + 1) === '|'){ cur += '|'; i++; continue; }
    if(ch === '|'){ cells.push(cur); cur = ''; continue; }
    cur += ch;
  }
  cells.push(cur);
  return cells.map(function(c){ return c.trim(); });
}

function renderTable(lines, ctx){
  var head = splitRow(lines[0]);
  var aligns = splitRow(lines[1]).map(function(c){
    if(/^:-+:$/.test(c)) return 'center';
    if(/^-+:$/.test(c)) return 'right';
    return '';
  });
  var html = '<table><thead><tr>';
  head.forEach(function(c, i){
    html += '<th' + (aligns[i] ? ' style="text-align:' + aligns[i] + '"' : '') + '>' + inlineMd(c) + '</th>';
  });
  html += '</tr></thead><tbody>';
  for(var r = 2; r < lines.length; r++){
    var cells = splitRow(lines[r]);
    html += '<tr>';
    for(var c2 = 0; c2 < head.length; c2++){
      html += '<td' + (aligns[c2] ? ' style="text-align:' + aligns[c2] + '"' : '') + '>' +
              inlineMd(cells[c2] === undefined ? '' : cells[c2]) + '</td>';
    }
    html += '</tr>';
  }
  return html + '</tbody></table>';
}

function collectList(lines, start){
  var i = start;
  while(i < lines.length){
    var l = lines[i];
    if(isListItem(l)){ i++; continue; }
    if(!l.trim()){
      var n = lines[i + 1];
      if(n && (isListItem(n) || /^ {2,}\S/.test(n))){ i++; continue; }
      break;
    }
    if(/^ {2,}\S/.test(l) && !isHeading(l) && !isHr(l)){ i++; continue; }
    break;
  }
  return i;
}

function renderList(ls, ctx){
  var first = ls[0].match(/^( *)([-*+]|\d+[.)])(\s*)/);
  var baseIndent = first[1].length;
  var ordered = /\d/.test(first[2]);
  var items = [], cur = null, curIndent = 0;
  for(var k = 0; k < ls.length; k++){
    var l = ls[k];
    var m = l.match(/^( *)([-*+]|\d+[.)])(\s+|$)(.*)$/);
    if(m && m[1].length <= baseIndent + 1){
      if(cur) items.push(cur);
      cur = [m[4]];
      curIndent = m[1].length + m[2].length + (m[3].length || 1);
      cur.indent = curIndent;
    } else if(cur){
      var lead = (l.match(/^ */) || [''])[0].length;
      cur.push(l.slice(Math.min(cur.indent, lead)));
    }
  }
  if(cur) items.push(cur);
  var body = items.map(function(it){
    var box = '';
    var tm = it[0].match(/^\[([ xX])\]\s+(.*)$/);
    if(tm){
      box = '<input class="task" type="checkbox" disabled' + (tm[1].toLowerCase() === 'x' ? ' checked' : '') + '>';
      it[0] = tm[2];
    }
    var content = mdBlocks(it, ctx);
    var single = content.match(/^<p>([\s\S]*)<\/p>$/);
    if(single && single[1].indexOf('<p>') < 0) content = single[1];
    else content = content.replace(/^<p>([\s\S]*?)<\/p>\n?/, '$1\n');
    return '<li>' + box + content + '</li>';
  }).join('');
  if(ordered){
    var st = first[2].replace(/\D/g, '');
    return '<ol' + (st && st !== '1' ? ' start="' + st + '"' : '') + '>' + body + '</ol>';
  }
  return '<ul>' + body + '</ul>';
}

/* ========================= graficos ========================= */
/* Bloque ```chart: cabeceras `clave: valor` + filas `etiqueta | n | n | n`.
   type: progress -> barra apilada (cerradas | en revision | pendientes)
   type: bars     -> barras horizontales, tono por etapa (done/review/p3/p2/p1) */
var CHART_KEYS = ['type', 'title', 'hero', 'hero_label', 'legend', 'max', 'note'];

function chartData(lines){
  var head = {}, rows = [];
  for(var i = 0; i < lines.length; i++){
    var l = lines[i].trim();
    if(!l) continue;
    var kv = l.match(/^([A-Za-z_]+)\s*:\s*(.*)$/);
    if(kv && CHART_KEYS.indexOf(kv[1].toLowerCase()) >= 0){ head[kv[1].toLowerCase()] = kv[2].trim(); continue; }
    if(l.indexOf('|') >= 0) rows.push(l.split('|').map(function(c){ return c.trim(); }));
  }
  return { head: head, rows: rows };
}

function chartTone(name){ return /^[a-z0-9]+$/.test(name || '') ? name : 'p1'; }

function renderChart(lines){
  var d = chartData(lines), head = d.head, rows = d.rows;
  var html = '<div class="chart">';
  if(head.title) html += '<div class="chart-title">' + esc(head.title) + '</div>';
  if(head.hero){
    html += '<div class="chart-hero"><b>' + esc(head.hero) + '</b>' +
            (head.hero_label ? '<span>' + esc(head.hero_label) + '</span>' : '') + '</div>';
  }
  if((head.type || 'bars').toLowerCase() === 'progress'){
    var names = (head.legend || 'Cerradas|En revisión|Pendientes').split('|');
    html += '<div class="chart-legend">' +
            '<span><i class="fill-done"></i>' + esc(names[0] || '') + '</span>' +
            '<span><i class="fill-review"></i>' + esc(names[1] || '') + '</span>' +
            '<span><i class="fill-track"></i>' + esc(names[2] || '') + '</span></div>';
    rows.forEach(function(r){
      var done = +r[1] || 0, rev = +r[2] || 0, pend = +r[3] || 0, tot = done + rev + pend;
      if(tot <= 0) return;
      var pd = done / tot * 100, pr = rev / tot * 100;
      var tip = r[0] + ' — ' + done + ' ' + (names[0] || '') + ', ' + rev + ' ' + (names[1] || '') +
                ', ' + pend + ' ' + (names[2] || '') + ' · total ' + tot;
      html += '<div class="crow' + (r[4] === 'total' ? ' total' : '') + '" title="' + esc(tip) + '">' +
              '<span class="clabel">' + esc(r[0]) + '</span><span class="ctrack">' +
              (done ? '<span class="cseg fill-done" style="width:' + pd.toFixed(1) + '%"></span>' : '') +
              (rev ? '<span class="cseg fill-review" style="width:' + pr.toFixed(1) + '%"></span>' : '') +
              '</span><span class="cval">' + Math.round((done + rev) / tot * 100) + '% listo · ' +
              (done + rev) + '/' + tot + '</span></div>';
    });
  } else {
    var max = +head.max || 0;
    rows.forEach(function(r){ max = Math.max(max, +r[1] || 0); });
    rows.forEach(function(r){
      var v = +r[1] || 0, w = max ? v / max * 100 : 0;
      html += '<div class="crow" title="' + esc(r[0] + ' — ' + v) + '">' +
              '<span class="clabel">' + esc(r[0]) + '</span>' +
              '<span class="cbar"><span class="cfill fill-' + esc(chartTone(r[2])) +
              '" style="width:' + w.toFixed(1) + '%"></span></span>' +
              '<span class="cval">' + esc(String(v)) + '</span></div>';
    });
  }
  if(head.note) html += '<p class="chart-note">' + inlineMd(head.note) + '</p>';
  return html + '</div>';
}

function mdBlocks(lines, ctx){
  var out = [], i = 0, m;
  while(i < lines.length){
    var line = lines[i];
    if(!line.trim()){ i++; continue; }

    if((m = line.match(/^ {0,3}(`{3,}|~{3,})\s*([^\s`]*)/))){
      var fenceCh = m[1].charAt(0), lang = m[2] || '', buf = [];
      var closer = new RegExp('^ {0,3}' + (fenceCh === '`' ? '`' : '~') + '{3,}\\s*$');
      i++;
      while(i < lines.length && !closer.test(lines[i])){ buf.push(lines[i]); i++; }
      i++;
      if(lang === 'chart'){ out.push(renderChart(buf)); continue; }
      out.push('<pre class="code"' + (lang ? ' data-lang="' + esc(lang) + '"' : '') +
               '><code>' + esc(buf.join('\n')) + '</code></pre>');
      continue;
    }

    if((m = line.match(/^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$/))){
      var lvl = m[1].length, text = m[2];
      var id = ctx.slug(slugify(text));
      ctx.toc.push({ level: lvl, text: text.replace(/[`*_]/g, ''), id: id });
      out.push('<h' + lvl + ' id="' + id + '"><a class="anchor" href="#' + id + '">#</a>' + inlineMd(text) + '</h' + lvl + '>');
      i++; continue;
    }

    if(isHr(line)){ out.push('<hr>'); i++; continue; }

    if(isQuote(line)){
      var qb = [];
      while(i < lines.length && (isQuote(lines[i]) || (lines[i].trim() && !isBlockStart(lines[i], lines[i+1])))){
        qb.push(lines[i].replace(/^ {0,3}> ?/, '')); i++;
      }
      out.push('<blockquote>' + mdBlocks(qb, ctx) + '</blockquote>');
      continue;
    }

    if(line.indexOf('|') >= 0 && isTableSep(lines[i + 1])){
      var tb = [lines[i], lines[i + 1]]; i += 2;
      while(i < lines.length && lines[i].trim() && lines[i].indexOf('|') >= 0){ tb.push(lines[i]); i++; }
      out.push(renderTable(tb, ctx));
      continue;
    }

    if(isListItem(line)){
      var end = collectList(lines, i);
      out.push(renderList(lines.slice(i, end), ctx));
      i = end; continue;
    }

    var pb = [];
    while(i < lines.length && lines[i].trim() && !isBlockStart(lines[i], lines[i + 1])){ pb.push(lines[i]); i++; }
    if(!pb.length){ pb.push(lines[i]); i++; }
    out.push('<p>' + inlineMd(pb.join('\n')).replace(/ {2,}\n/g, '<br>\n') + '</p>');
  }
  return out.join('\n');
}

function newCtx(){
  var used = {};
  return {
    toc: [],
    slug: function(base){
      var s = base || 'seccion';
      if(used[s] === undefined){ used[s] = 0; return s; }
      used[s]++; return s + '-' + used[s];
    }
  };
}

function renderMarkdown(md){
  var ctx = newCtx();
  var body = String(md).replace(/\r\n?/g, '\n').replace(/\t/g, '    ');
  var fm = '';
  var fmm = body.match(/^---\n([\s\S]*?)\n---\n?/);
  if(fmm){
    fm = '<details class="frontmatter"><summary>▸ metadatos del documento</summary>' +
         highlightYaml(fmm[1]) + '</details>';
    body = body.slice(fmm[0].length);
  }
  return { html: fm + '<div class="md">' + mdBlocks(body.split('\n'), ctx) + '</div>', toc: ctx.toc };
}

/* ========================= yaml / csv ========================= */
function highlightYaml(src){
  var lines = esc(String(src).replace(/\r\n?/g, '\n')).split('\n').map(function(l){
    if(/^\s*#/.test(l)) return '<span class="y-com">' + l + '</span>';
    var m = l.match(/^(\s*(?:- )?)([A-Za-z0-9_.\-\/ ]+?)(:)(\s?)(.*)$/);
    if(m){
      var val = m[5], com = '';
      var ci = val.indexOf(' #');
      if(ci >= 0){ com = '<span class="y-com">' + val.slice(ci) + '</span>'; val = val.slice(0, ci); }
      var cls = /^(true|false|null|~|\d[\d.:\-]*)$/.test(val.trim()) ? 'y-num' : 'y-val';
      var vh = val.trim() ? '<span class="' + cls + '">' + val + '</span>' : val;
      return m[1] + '<span class="y-key">' + m[2] + '</span>' + m[3] + m[4] + vh + com;
    }
    return l;
  });
  return '<pre class="code" data-lang="yaml"><code>' + lines.join('\n') + '</code></pre>';
}

function renderYamlDoc(src){
  var ctx = newCtx();
  var out = [], lines = String(src).replace(/\r\n?/g, '\n').split('\n'), chunk = [];
  function flush(){ if(chunk.length){ out.push(highlightYaml(chunk.join('\n'))); chunk = []; } }
  for(var i = 0; i < lines.length; i++){
    var l = lines[i];
    var m = l.match(/^([a-zA-Z0-9_\-]+):\s*$/);
    if(m){
      flush();
      var id = ctx.slug(slugify(m[1]));
      ctx.toc.push({ level: 2, text: m[1], id: id });
      out.push('<h2 id="' + id + '"><a class="anchor" href="#' + id + '">#</a><code>' + esc(m[1]) + ':</code></h2>');
      continue;
    }
    chunk.push(l);
  }
  flush();
  return { html: '<div class="md">' + out.join('\n') + '</div>', toc: ctx.toc };
}

function parseCsv(text){
  var rows = [], row = [], cur = '', q = false;
  text = String(text).replace(/\r\n?/g, '\n');
  for(var i = 0; i < text.length; i++){
    var c = text.charAt(i);
    if(q){
      if(c === '"'){ if(text.charAt(i + 1) === '"'){ cur += '"'; i++; } else q = false; }
      else cur += c;
    } else if(c === '"'){ q = true; }
    else if(c === ','){ row.push(cur); cur = ''; }
    else if(c === '\n'){ row.push(cur); rows.push(row); row = []; cur = ''; }
    else cur += c;
  }
  if(cur !== '' || row.length){ row.push(cur); rows.push(row); }
  return rows.filter(function(r){ return r.length > 1 || (r[0] || '').trim() !== ''; });
}

function renderCsvDoc(src){
  var rows = parseCsv(src);
  if(!rows.length) return { html: '<div class="md"><p>Archivo vacío.</p></div>', toc: [] };
  var head = rows[0];
  var html = '<div class="md"><div class="csv-info">' + (rows.length - 1) + ' filas · ' + head.length + ' columnas</div><table><thead><tr>';
  head.forEach(function(h){ html += '<th>' + esc(h) + '</th>'; });
  html += '</tr></thead><tbody>';
  for(var r = 1; r < rows.length; r++){
    html += '<tr>';
    for(var c = 0; c < head.length; c++) html += '<td>' + esc(rows[r][c] === undefined ? '' : rows[r][c]) + '</td>';
    html += '</tr>';
  }
  return { html: html + '</tbody></table></div>', toc: [] };
}

function renderContent(path, src){
  var e = ext(path);
  if(e === 'md' || e === 'markdown') return renderMarkdown(src);
  if(e === 'yaml' || e === 'yml') return renderYamlDoc(src);
  if(e === 'csv') return renderCsvDoc(src);
  return { html: '<div class="md"><pre class="code"><code>' + esc(src) + '</code></pre></div>', toc: [] };
}

/* ========================= sidebar ========================= */
function buildSidebar(){
  var html = '<div class="side-title">' + esc(LABELS.featured) + '</div>';
  PRIMARY.forEach(function(p){
    html += '<a class="nav-item pin" data-path="' + esc(p.path) + '" href="#' + esc(p.path) + '">' +
            '<span class="tag">' + esc(p.tag) + '</span><span><span>' + esc(p.label) + '</span>' +
            '<span class="sub">' + esc(p.desc) + '</span></span></a>';
  });

  var groups = {}, paths = Object.keys(FILES).filter(function(p){ return !FILES[p].v; }).sort();
  paths.forEach(function(p){
    var d = dirname(p);
    (groups[d] = groups[d] || []).push(p);
  });
  html += '<div class="side-title" style="margin-top:14px">' + esc(LABELS.all_documents) + '</div>';
  Object.keys(groups).sort(function(a, b){
    if(a === '') return -1; if(b === '') return 1; return a.localeCompare(b);
  }).forEach(function(d){
    var open = d === '' ? ' open' : '';
    html += '<details class="group"' + open + '><summary>' + esc(d ? d + '/' : 'Raíz') +
            '<span class="count">' + groups[d].length + '</span></summary>';
    groups[d].forEach(function(p){
      html += '<a class="nav-item" data-path="' + esc(p) + '" href="#' + esc(p) + '" title="' + esc(p) + '">' +
              esc(basename(p)) + '</a>';
    });
    html += '</details>';
  });
  elSide.innerHTML = html;
}

function markActive(){
  var items = elSide.querySelectorAll('.nav-item');
  for(var i = 0; i < items.length; i++){
    var on = items[i].getAttribute('data-path') === currentPath;
    items[i].classList.toggle('active', on);
    if(on){
      var det = items[i].closest('details');
      if(det) det.open = true;
    }
  }
}

/* ========================= search ========================= */
var INDEX = null;
function buildIndex(){
  if(INDEX) return INDEX;
  INDEX = Object.keys(FILES).map(function(p){
    return { path: p, title: FILES[p].t, lower: FILES[p].c.toLowerCase(), raw: FILES[p].c };
  });
  return INDEX;
}
function norm(s){ return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); }

function runSearch(q){
  var term = q.trim();
  if(!term){ searchTerm = ''; buildSidebar(); markActive(); return; }
  searchTerm = term;
  var nt = norm(term);
  var idx = buildIndex();
  var res = [];
  idx.forEach(function(f){
    var hay = norm(f.lower), pos = hay.indexOf(nt);
    var nameHit = norm(f.path).indexOf(nt) >= 0 || norm(f.title).indexOf(nt) >= 0;
    if(pos < 0 && !nameHit) return;
    var count = 0, from = 0, p2;
    while(pos >= 0 && (p2 = hay.indexOf(nt, from)) >= 0){ count++; from = p2 + nt.length; if(count > 400) break; }
    var snip = '';
    if(pos >= 0){
      var s0 = Math.max(0, pos - 55), s1 = Math.min(f.raw.length, pos + nt.length + 85);
      snip = (s0 > 0 ? '…' : '') + esc(f.raw.slice(s0, s1).replace(/\s+/g, ' ')) + (s1 < f.raw.length ? '…' : '');
      var re = new RegExp('(' + term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'ig');
      snip = snip.replace(re, '<mark>$1</mark>');
    }
    res.push({ path: f.path, title: f.title, count: count, snip: snip, nameHit: nameHit });
  });
  res.sort(function(a, b){
    if(a.nameHit !== b.nameHit) return a.nameHit ? -1 : 1;
    return b.count - a.count;
  });
  var html = '<div class="side-title">' + res.length + ' documento(s) con «' + esc(term) + '»</div>';
  if(!res.length) html += '<div class="empty">Sin resultados.</div>';
  res.slice(0, 60).forEach(function(r){
    html += '<a class="result" data-path="' + esc(r.path) + '" href="#' + esc(r.path) + '">' +
            '<div class="rtitle">' + esc(r.title) + (r.count ? ' <span class="rpath">(' + r.count + ')</span>' : '') + '</div>' +
            '<div class="rpath">' + esc(r.path) + '</div>' +
            (r.snip ? '<div class="rsnip">' + r.snip + '</div>' : '') + '</a>';
  });
  elSide.innerHTML = html;
}

function highlightTerm(term){
  if(!term) return;
  var re = new RegExp(term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'ig');
  var walker = document.createTreeWalker(elMain, NodeFilter.SHOW_TEXT, null);
  var nodes = [], n;
  while((n = walker.nextNode())){
    if(n.parentNode && /^(SCRIPT|STYLE|MARK)$/.test(n.parentNode.nodeName)) continue;
    if(re.test(n.nodeValue)) nodes.push(n);
    re.lastIndex = 0;
  }
  nodes.slice(0, 400).forEach(function(node){
    var span = document.createElement('span');
    span.innerHTML = esc(node.nodeValue).replace(re, function(m){ return '<mark>' + m + '</mark>'; });
    node.parentNode.replaceChild(span, node);
  });
  var first = elMain.querySelector('mark');
  if(first && !currentAnchor) first.scrollIntoView({ block: 'center' });
}

/* ========================= render doc ========================= */
function docHead(path){
  var f = FILES[path];
  var parts = path.split('/');
  var crumbs = parts.map(function(s, i){
    return i === parts.length - 1 ? '<span class="file">' + esc(s) + '</span>' : esc(s);
  }).join(' <span style="opacity:.5">/</span> ');
  var bytes = f.c.length, lines = f.c.split('\n').length;
  return '<div class="doc-head"><div class="crumbs">' + esc(BRAND.name) + ' <span style="opacity:.5">/</span> ' + crumbs + '</div>' +
         '<h1 class="doc-title">' + esc(f.t) + '</h1>' +
         '<div class="doc-meta"><span>' + lines + ' líneas</span><span>' + (bytes / 1024).toFixed(1) + ' KB</span>' +
         '<span>tipo: ' + esc(ext(path) || 'txt') + '</span></div></div>';
}

function buildToc(toc){
  var items = toc.filter(function(t){ return t.level >= 2 && t.level <= 4; });
  if(items.length < 2){ elToc.innerHTML = ''; document.body.classList.remove('with-toc'); return; }
  document.body.classList.add('with-toc');
  var html = '<div class="side-title">' + esc(LABELS.toc) + '</div>';
  items.forEach(function(t){
    html += '<a class="lvl' + t.level + '" href="#' + encodeURIComponent(currentPath) .replace(/%2F/g,'/') + '#' + t.id +
            '" data-id="' + esc(t.id) + '">' + esc(t.text) + '</a>';
  });
  elToc.innerHTML = html;
}

function postProcess(){
  // resolve links
  var as = elMain.querySelectorAll('.md a[href]');
  for(var i = 0; i < as.length; i++){
    var a = as[i], href = a.getAttribute('href');
    if(!href) continue;
    if(/^(https?:|mailto:|tel:)/i.test(href)){ a.target = '_blank'; a.rel = 'noopener'; continue; }
    if(href.charAt(0) === '#'){ continue; }
    var sp = splitHash(href);
    var target = resolvePath(dirname(currentPath), sp[0]);
    if(FILES[target]){
      a.setAttribute('href', '#' + target + (sp[1] ? '#' + sp[1] : ''));
      a.setAttribute('data-doc', target);
      a.title = target;
    } else {
      a.setAttribute('data-missing', '1');
      a.title = 'No incluido en el visor: ' + target;
    }
  }
  // images relative to the generated viewer
  var imgs = elMain.querySelectorAll('img[data-src]');
  for(var j = 0; j < imgs.length; j++){
    var src = imgs[j].getAttribute('data-src');
    imgs[j].src = /^(https?:|data:)/i.test(src) ? src : resolvePath(dirname(currentPath), src);
  }
  // copy buttons
  var pres = elMain.querySelectorAll('pre.code');
  for(var k = 0; k < pres.length; k++){
    var b = document.createElement('button');
    b.className = 'copy-btn'; b.type = 'button'; b.textContent = 'copiar';
    pres[k].appendChild(b);
  }
}

function scrollToAnchor(anchor){
  if(!anchor) return false;
  var el = document.getElementById(anchor);
  if(!el){
    var want = norm(anchor);
    var hs = elMain.querySelectorAll('[id]');
    for(var i = 0; i < hs.length; i++){ if(norm(hs[i].id) === want){ el = hs[i]; break; } }
  }
  if(el){ el.scrollIntoView({ block: 'start' }); window.scrollBy(0, -8); return true; }
  return false;
}

function renderDoc(){
  var path = currentPath;
  if(!FILES[path]){
    elMain.innerHTML = '<div class="missing"><h2>Documento no incluido</h2><p>La ruta <code>' + esc(path) +
      '</code> no está embebida en este visor.</p><p>El archivo no coincidía con la configuración de inclusión al generar el visor.</p>' +
      '<p><a href="' + esc(path) + '" target="_blank">Intentar abrir el archivo directamente ↗</a></p></div>';
    elToc.innerHTML = ''; document.body.classList.remove('with-toc');
    return;
  }
  var f = FILES[path];
  var rendered;
  if(showRaw){
    rendered = { html: '<div class="md"><pre class="code" data-lang="' + esc(ext(path)) + '"><code>' + esc(f.c) + '</code></pre></div>', toc: [] };
  } else {
    rendered = renderContent(path, f.c);
  }
  elMain.innerHTML = docHead(path) + rendered.html;
  buildToc(rendered.toc);
  postProcess();
  document.title = f.t + ' · ' + SETTINGS.title;
  markActive();
  if(searchTerm) highlightTerm(searchTerm);
  if(!scrollToAnchor(currentAnchor)) window.scrollTo(0, 0);
  syncToc();
  maybeRefresh(path);
}

function navigate(path, anchor){
  var h = '#' + path + (anchor ? '#' + anchor : '');
  if(location.hash === h){ currentPath = path; currentAnchor = anchor; renderDoc(); }
  else location.hash = h;
}

function parseHash(){
  var h = location.hash.replace(/^#/, '');
  try { h = decodeURIComponent(h); } catch(e){}
  if(!h) return { path: PRIMARY[0].path, anchor: null };
  var i = h.indexOf('#');
  return i < 0 ? { path: h, anchor: null } : { path: h.slice(0, i), anchor: h.slice(i + 1) };
}

function onRoute(){
  var r = parseHash();
  var changedDoc = r.path !== currentPath;
  currentPath = r.path; currentAnchor = r.anchor;
  if(changedDoc || !elMain.firstChild) renderDoc();
  else { scrollToAnchor(currentAnchor); syncToc(); }
  document.body.classList.remove('nav-open');
}

/* live refresh when served over http(s) */
var refreshed = {};
function maybeRefresh(path){
  if(location.protocol === 'file:' || refreshed[path]) return;
  if(FILES[path] && FILES[path].v) return;   /* virtual: no existe en disco */
  refreshed[path] = true;
  fetch(path, { cache: 'no-store' }).then(function(r){
    return r.ok ? r.text() : null;
  }).then(function(t){
    if(t === null || t === undefined) return;
    if(t === FILES[path].c) return;
    FILES[path].c = t;
    INDEX = null;
    if(currentPath === path){ renderDoc(); toast('Contenido recargado desde el archivo en disco'); }
  }).catch(function(){});
}

/* ========================= toc scroll spy ========================= */
function syncToc(){
  var links = elToc.querySelectorAll('a[data-id]');
  if(!links.length) return;
  var best = null, bestTop = -Infinity;
  for(var i = 0; i < links.length; i++){
    var el = document.getElementById(links[i].getAttribute('data-id'));
    if(!el) continue;
    var top = el.getBoundingClientRect().top - 80;
    if(top <= 0 && top > bestTop){ bestTop = top; best = links[i]; }
  }
  if(!best) best = links[0];
  for(var j = 0; j < links.length; j++) links[j].classList.toggle('active', links[j] === best);
}

/* ========================= events ========================= */
document.addEventListener('click', function(e){
  var btn = e.target.closest('.copy-btn');
  if(btn){
    var code = btn.parentNode.querySelector('code');
    var txt = code ? code.innerText : '';
    if(navigator.clipboard) navigator.clipboard.writeText(txt);
    btn.textContent = '¡copiado!';
    setTimeout(function(){ btn.textContent = 'copiar'; }, 1400);
    return;
  }
  var a = e.target.closest('a');
  if(!a) return;
  var href = a.getAttribute('href');
  if(!href) return;
  if(/^(https?:|mailto:|tel:)/i.test(href)) return;
  if(a.hasAttribute('data-missing')){
    e.preventDefault();
    window.open(a.title.replace(/^No incluido en el visor: /, ''), '_blank');
    toast('Ese archivo no está embebido; se intentó abrir directo.');
    return;
  }
  if(href.charAt(0) === '#'){
    var rest = href.slice(1);
    if(rest.indexOf('#') < 0 && !FILES[rest]){
      // pure in-document anchor
      e.preventDefault();
      navigate(currentPath, rest);
    }
    return; // hashchange router handles the rest
  }
  e.preventDefault();
  var sp = splitHash(href);
  var target = resolvePath(dirname(currentPath || ''), sp[0]);
  if(FILES[target]) navigate(target, sp[1]);
  else { window.open(target, '_blank'); toast('Archivo fuera del visor: ' + target); }
});

window.addEventListener('hashchange', onRoute);
window.addEventListener('scroll', function(){
  clearTimeout(window._tocT);
  window._tocT = setTimeout(syncToc, 60);
}, { passive: true });

var searchT;
elSearch.addEventListener('input', function(){
  clearTimeout(searchT);
  var v = elSearch.value;
  searchT = setTimeout(function(){ runSearch(v); }, 160);
});
elSearch.addEventListener('keydown', function(e){
  if(e.key === 'Escape'){ elSearch.value = ''; runSearch(''); elSearch.blur(); }
  if(e.key === 'Enter'){
    var first = elSide.querySelector('.result');
    if(first) navigate(first.getAttribute('data-path'), null);
  }
});
document.addEventListener('keydown', function(e){
  if(e.key === '/' && document.activeElement !== elSearch){ e.preventDefault(); elSearch.focus(); elSearch.select(); }
});

document.getElementById('theme-btn').addEventListener('click', function(){
  var cur = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', cur);
  applyAccent();
  try { localStorage.setItem('generate-docs-theme', cur); } catch(err){}
});
document.getElementById('raw-btn').addEventListener('click', function(){
  showRaw = !showRaw;
  this.style.color = showRaw ? 'var(--accent)' : '';
  renderDoc();
});
document.getElementById('menu-btn').addEventListener('click', function(){
  document.body.classList.toggle('nav-open');
});
document.getElementById('backdrop').addEventListener('click', function(){
  document.body.classList.remove('nav-open');
});

/* ========================= init ========================= */
try {
  var saved = localStorage.getItem('generate-docs-theme');
  if(saved) document.documentElement.setAttribute('data-theme', saved);
  else if(window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches)
    document.documentElement.setAttribute('data-theme', 'light');
} catch(err){}

applySettings();
buildSidebar();
onRoute();
})();
</script>
</body>
</html>
"""


if __name__ == '__main__':
    sys.exit(main())
