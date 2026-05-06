# kyrie-dev

Repositorio personal de utilidades, skills y documentacion de trabajo para desarrollo asistido.

## Contenido

- `.agents/skills/`: skills locales para Codex y flujos operativos.
- `skills/`: skills y configuraciones adicionales del workspace.
- `_bmad/`: configuracion local de BMad.
- `doc/`: notas tecnicas, referencias y documentacion de apoyo.
- `scripts/`: scripts de automatizacion y herramientas auxiliares.
- `data/`: datos locales de trabajo. Revisar antes de versionar contenido nuevo.

## Uso Local

Clonar el repositorio:

```bash
git clone git@github-clancien:clancien/kyrie-dev.git
cd kyrie-dev
```

Verificar el estado:

```bash
git status
```

Ejecutar scripts segun corresponda desde sus carpetas respectivas. Algunos scripts pueden requerir dependencias o archivos `.env` locales.

## Secretos y Archivos Locales

No se deben versionar credenciales, tokens, archivos `.env`, secretos OAuth ni codigos de autorizacion.

Archivos sensibles ignorados:

```text
.env
scripts/sync/drive-client_secret.json
scripts/sync/drive.cod.txt
```

Para configurar Google Drive Sync, usar la plantilla:

```text
scripts/sync/drive-client_secret.example.json
```

Copiarla localmente como `scripts/sync/drive-client_secret.json` y completar los valores reales fuera de Git.

## Flujo Git

Este repo usa `main` como rama principal:

```bash
git add .
git commit -m "descripcion del cambio"
git push
```

El remote esperado usa el alias SSH local `github-clancien`:

```text
git@github-clancien:clancien/kyrie-dev.git
```

