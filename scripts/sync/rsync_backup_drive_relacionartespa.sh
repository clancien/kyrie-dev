#!/bin/bash

# =======================================================
#                  CONFIGURACION INICIAL
# =======================================================

# --- RUTA DE MONTAJE DE GOOGLE DRIVE ---
# Carpeta local donde se montara/verificara el Google Drive.
DRIVE_MOUNT_POINT="/mnt/google-drive-relacionartespa"

# --- NOMBRE DEL REMOTO DE RCLONE ---
# Nombre configurado en 'rclone config'.
RCLONE_REMOTE="relacionartespa_at_gmail_dot_com"

# --- CONFIGURACION DE PROPIETARIO PARA MONTAJE RCLONE ---
# IMPORTANTE: Reemplaza '1000' con el UID y GID de tu usuario principal de Ubuntu
# (el usuario que configuro rclone). Usa los comandos 'id -u tu_usuario' y 'id -g tu_usuario'.
# RCLONE_UID="1000"
# RCLONE_GID="1000"

# --- Carpetas Locales a Sincronizar ---
# IMPORTANTE: Rutas absolutas y terminadas en barra inclinada (/).
SOURCE_DIRS=()

# --- Variables de Sincronizacion ---
# Carpeta de destino dentro de tu Google Drive remoto.
REMOTE_DESTINATION="Backup/Cyrille"

# Ruta completa del destino de rsync (no necesita ser modificada)
RSYNC_DESTINATION="${DRIVE_MOUNT_POINT}/${REMOTE_DESTINATION}"

# Archivo de registro (log)
LOG_FILE="/var/log/rsync_backup_drive_relacionartespa.log"

# Archivo de bloqueo (para evitar ejecuciones concurrentes en cron)
LOCK_FILE="/var/tmp/rsync_backup_relacionartespa.lock"

# =======================================================
#                      FUNCIONES
# =======================================================

# Funcion para registrar mensajes
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Funcion para liberar el bloqueo y salir
cleanup_and_exit() {
    rm -f "$LOCK_FILE"
    exit $1
}

# =======================================================
#                  LOGICA PRINCIPAL
# =======================================================

log_message "--- INICIO DE LA COPIA DE SEGURIDAD ---"

# 1. Control de Bloqueo
if [ -f "$LOCK_FILE" ]; then
    log_message "ERROR: Otra instancia del script esta en ejecucion. Saliendo."
    exit 1
fi
trap 'cleanup_and_exit $?' EXIT
touch "$LOCK_FILE"

# 2. Verificacion y Montaje de Google Drive (RCLONE)
log_message "Verificando el punto de montaje: ${DRIVE_MOUNT_POINT}"

if ! mountpoint -q "$DRIVE_MOUNT_POINT"; then
    log_message "El punto de montaje NO esta activo. Intentando montar con rclone..."

    # Comando de montaje: usa --uid/--gid para evitar el error 'mount not ready' con root
    sudo rclone mount "$RCLONE_REMOTE": "$DRIVE_MOUNT_POINT" --allow-other --daemon

#    rclone mount "$RCLONE_REMOTE": "$DRIVE_MOUNT_POINT" \
#      --allow-other --daemon --timeout 1m \
#      --uid "$RCLONE_UID" --gid "$RCLONE_GID" \
#      --log-file-max-days 7

    # Esperamos 5 segundos para que el montaje se establezca
    sleep 5

    if ! mountpoint -q "$DRIVE_MOUNT_POINT"; then
        log_message "ERROR: Fallo el montaje de Google Drive (rclone mount). Abortando copia de seguridad."
        log_message "Asegurate de que rclone este configurado y que UID/GID sean correctos."
        cleanup_and_exit 2
    else
        log_message "EXITO: Google Drive montado correctamente con rclone."
    fi
else
    log_message "El punto de montaje ya esta activo. Continuando con rsync."
fi


# 3. Creacion de la Carpeta de Destino Remota si no existe
if [ ! -d "$RSYNC_DESTINATION" ]; then
    log_message "Creando la carpeta de destino remota: ${RSYNC_DESTINATION}"
    mkdir -p "$RSYNC_DESTINATION"
    if [ $? -ne 0 ]; then
        log_message "ERROR: No se pudo crear la carpeta de destino remota."
        cleanup_and_exit 3
    fi
fi

# 4. Ejecucion de rsync para cada carpeta de origen
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
        log_message "EXITO: Sincronizacion de ${SOURCE} completada."
    else
        log_message "FALLO: Error al sincronizar ${SOURCE}. Codigo de salida: $?."
    fi

done

log_message "--- FIN DE LA COPIA DE SEGURIDAD ---"
