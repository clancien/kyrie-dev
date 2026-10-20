# Operación

`server.sh up|down|restart|status|logs [local|docker]`, local por defecto. PID y logs propios en `.cache`, control serializado con flock y arranque verificado. Sin modo explícito, down/status actúan sobre ambos modos. No mata procesos por puerto. Docker se construye antes de detener proceso local y conserva bind mounts `.cache` y `data`. No borrar esos directorios para reiniciar.

Docker Linux usa red host y servidor unido a 127.0.0.1; no publica interfaces externas. Escritorio usa DISPLAY y /tmp/.X11-unix; incluye XAUTHORITY y requiere permisos locales de X11 existentes. Sin escritorio renovar mediante run.sh local. Banco de Chile no se modifica.

Ante error conserva particiones anteriores y muestra recurso fallido. Renueve sesión con run.sh. Código/esquema desconocido exige verificar captura bancaria; no cambiarlo a éxito vacío. No compartir cache, SQLite, exportación ni logs. Se verificaron acceso real, sesión HTTP restaurada, ambas cuentas, tarjeta CLP/USD, consulta histórica y repetición. BuildKit falló internamente; el intento legacy falló al exportar capa por falta de espacio en Docker Desktop. La demostración en contenedor permanece pendiente; no se borraron imágenes ni recursos ajenos para resolverlo.
