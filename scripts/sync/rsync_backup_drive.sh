#!/bin/bash

# =======================================================
#                  CONFIGURACIÓN INICIAL
# =======================================================

# --- RUTA DE MONTAJE DE GOOGLE DRIVE ---
# Carpeta local donde se montará/verificará el Google Drive.
DRIVE_MOUNT_POINT="/mnt/google-drive-clancien"

# --- NOMBRE DEL REMOTO DE RCLONE ---
# Nombre configurado en 'rclone config'.
RCLONE_REMOTE="clancien_at_gmail_dot_com"

# --- CONFIGURACIÓN DE PROPIETARIO PARA MONTAJE RCLONE ---
# ¡IMPORTANTE! Reemplaza '1000' con el UID y GID de tu usuario principal de Ubuntu
# (el usuario que configuró rclone). Usa los comandos 'id -u tu_usuario' y 'id -g tu_usuario'.
# RCLONE_UID="1000"
# RCLONE_GID="1000"

# --- Carpetas Locales a Sincronizar ---
# ¡IMPORTANTE! Rutas absolutas y terminadas en barra inclinada (/).
SOURCE_DIRS=(
    "/home/clancien/Documentos/"
    "/home/clancien/Imágenes/"   
    "/home/clancien/notes/"
    "/home/clancien/Plantillas/"
)

# --- Variables de Sincronización ---
# Carpeta de destino dentro de tu Google Drive remoto.
REMOTE_DESTINATION="Backup-Local/Phenix"

# Ruta completa del destino de rsync (no necesita ser modificada)
RSYNC_DESTINATION="${DRIVE_MOUNT_POINT}/${REMOTE_DESTINATION}"

# Archivo de registro (log)
LOG_FILE="/var/log/rsync_backup_drive.log"

# Archivo de bloqueo (para evitar ejecuciones concurrentes en cron)
LOCK_FILE="/var/tmp/rsync_backup.lock"

# =======================================================
#                      FUNCIONES
# =======================================================

# Función para registrar mensajes
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Función para liberar el bloqueo y salir
cleanup_and_exit() {
    rm -f "$LOCK_FILE"
    exit $1
}

# =======================================================
#                  LÓGICA PRINCIPAL
# =======================================================

log_message "--- INICIO DE LA COPIA DE SEGURIDAD ---"

# 1. Control de Bloqueo
if [ -f "$LOCK_FILE" ]; then
    log_message "ERROR: Otra instancia del script está en ejecución. Saliendo."
    exit 1
fi
trap 'cleanup_and_exit $?' EXIT
touch "$LOCK_FILE"

# 2. Verificación y Montaje de Google Drive (RCLONE)
log_message "Verificando el punto de montaje: ${DRIVE_MOUNT_POINT}"

if ! mountpoint -q "$DRIVE_MOUNT_POINT"; then
    log_message "El punto de montaje NO está activo. Intentando montar con rclone..."
    
    # Comando de montaje: usa --uid/--gid para evitar el error 'mount not ready' con root
    sudo rclone mount "$RCLONE_REMOTE": "$DRIVE_MOUNT_POINT" --allow-other --daemon

#    rclone mount "$RCLONE_REMOTE": "$DRIVE_MOUNT_POINT" \
#      --allow-other --daemon --timeout 1m \
#      --uid "$RCLONE_UID" --gid "$RCLONE_GID" \
#      --log-file-max-days 7
    
    # Esperamos 5 segundos para que el montaje se establezca
    sleep 5
    
    if ! mountpoint -q "$DRIVE_MOUNT_POINT"; then
        log_message "ERROR: Falló el montaje de Google Drive (rclone mount). Abortando copia de seguridad."
        log_message "Asegúrate de que rclone esté configurado y que UID/GID sean correctos."
        cleanup_and_exit 2
    else
        log_message "ÉXITO: Google Drive montado correctamente con rclone."
    fi
else
    log_message "El punto de montaje ya está activo. Continuando con rsync."
fi


# 3. Creación de la Carpeta de Destino Remota si no existe
if [ ! -d "$RSYNC_DESTINATION" ]; then
    log_message "Creando la carpeta de destino remota: ${RSYNC_DESTINATION}"
    mkdir -p "$RSYNC_DESTINATION"
    if [ $? -ne 0 ]; then
        log_message "ERROR: No se pudo crear la carpeta de destino remota."
        cleanup_and_exit 3
    fi
fi

# 4. Ejecución de rsync para cada carpeta de origen
for SOURCE in "${SOURCE_DIRS[@]}"; do
    if [ ! -d "$SOURCE" ]; then
        log_message "ADVERTENCIA: La carpeta de origen ${SOURCE} NO existe. Saltando."
        continue
    fi

    DIR_NAME=$(basename "$SOURCE")
    CURRENT_DEST="${RSYNC_DESTINATION}/${DIR_NAME}"

    log_message "Sincronizando ${SOURCE} a ${CURRENT_DEST}..."

    # Opciones de rsync: -a (archivo), -v (verboso), -h (humano), --delete (sincroniza borrando en destino)
    rsync -avh --delete \
          --log-file="${LOG_FILE}.rsync_details" \
          "$SOURCE" \
          "$CURRENT_DEST"

    if [ $? -eq 0 ]; then
        log_message "ÉXITO: Sincronización de ${SOURCE} completada."
    else
        log_message "FALLO: Error al sincronizar ${SOURCE}. Código de salida: $?."
    fi

done

log_message "--- FIN DE LA COPIA DE SEGURIDAD ---"
