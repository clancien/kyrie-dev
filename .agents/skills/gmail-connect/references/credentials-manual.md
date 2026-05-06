# Manual para Obtener Credenciales Gmail API

## 1) Crear proyecto en Google Cloud

1. Ir a https://console.cloud.google.com/
2. Crear proyecto nuevo (o usar uno existente).

## 2) Habilitar Gmail API

1. Menú `APIs & Services` > `Library`.
2. Buscar `Gmail API`.
3. Click `Enable`.

## 3) Configurar OAuth Consent Screen

1. Ir a `APIs & Services` > `OAuth consent screen`.
2. Elegir `External` (o `Internal` si aplica a Workspace corporativo).
3. Completar:
   - App name
   - User support email
   - Developer contact email
4. En `Scopes`, agregar:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.compose`
5. Guardar.

## 4) Crear OAuth Client ID

1. Ir a `APIs & Services` > `Credentials`.
2. `Create Credentials` > `OAuth client ID`.
3. Tipo recomendado: `Desktop app`.
4. Guardar y copiar:
   - `Client ID`
   - `Client Secret`

## 5) Configurar `.env`

Agregar en `.env`:

```env
GMAIL_CLIENT_ID=xxxxxxxx.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=xxxxxxxx
GMAIL_REDIRECT_URI=http://localhost:8080
GMAIL_USER=me
```

## 6) Obtener `GMAIL_REFRESH_TOKEN`

1. Generar URL de autorización:

```bash
python3 .agents/skills/gmail-connect/assets/gmail_oauth_helper.py --project-root "$PWD" auth-url
```

2. Abrir la URL en navegador y autorizar acceso.
3. Copiar el `code` de la URL de callback (`?code=...`).
4. Intercambiar `code` por tokens:

```bash
python3 .agents/skills/gmail-connect/assets/gmail_oauth_helper.py --project-root "$PWD" exchange-code --code "<CODE>"
```

5. Copiar el valor mostrado y agregar:

```env
GMAIL_REFRESH_TOKEN=xxxxxxxx
```

## 7) Probar lectura y borrador

```bash
python3 .agents/skills/gmail-connect/assets/gmail_client.py --project-root "$PWD" read --max-results 5
python3 .agents/skills/gmail-connect/assets/gmail_client.py --project-root "$PWD" draft --to "tu_correo@dominio.com" --subject "Prueba" --body "Hola"
```
