# Guía de Despliegue en Coolify (Docker) 🐳

Proyecto **Dockerizado para Coolify**. Código por **git push main**; variables de entorno en Coolify (no compartir entre entornos).

**Traefik en Coolify se encarga de todo el enrutamiento externo.** El `docker-compose.yml` del repositorio **no expone ningún puerto al host** (ni app, ni db, ni redis). La app se conecta a `db` y `redis` por la red interna; el acceso público lo gestiona Traefik. Configuración correcta para Coolify, sin conflictos de puertos.

**Referencia completa de variables**: [docs/VARIABLES_ENTORNO.md](docs/VARIABLES_ENTORNO.md).  
**Operación (health, paro global, logs)**: [docs/OPERACION.md](docs/OPERACION.md).  
**Checklist “listo para Coolify” y Simulador V2**: [docs/LISTO_PARA_COOLIFY.md](docs/LISTO_PARA_COOLIFY.md).

## 1. Configuración del Proyecto en Coolify

*   **Build Pack**: `Docker Compose` (recomendado) o `Dockerfile`.
*   **Docker Compose**: Usar el `docker-compose.yml` del repo; pensado para Coolify (sin `ports` en host; Traefik enruta al contenedor `app`).
*   **Start Command**: No es necesario sobreescribir. El `Dockerfile` ya define:
    ```bash
    CMD ["./scripts/startup.sh"]
    ```
    Este script se encarga de:
    1.  Esperar a la Base de Datos (`wait_for_db`).
    2.  Correr migraciones Alembic.
    3.  **Aplicar Parches Manuales** (Fases 7, 8, 9: Baserow, Webhook, VAD).
    4.  Descargar Modelos AI (Silero VAD).
    5.  Iniciar `uvicorn`.

## 2. Variables de Entorno (Environment Variables)

En Coolify, debes configurar las siguientes variables en la sección **Secrets/Env Vars**:

### Base de Datos
Coolify suele inyectar `DATABASE_URL` o variables `POSTGRES_*`. El sistema soporta ambos métodos, pero **prioriza**:
*   `POSTGRES_SERVER`: (Usualmente el nombre del servicio, ej: `db` o `postgresql`).
*   `POSTGRES_USER`: Usuario de la DB.
*   `POSTGRES_PASSWORD`: Contraseña.
*   `POSTGRES_DB`: `voice_db` (o lo que definas).
*   `POSTGRES_PORT`: `5432`.

### Integraciones (API Keys)
Para flujo V2 (simulador y telefonía): `GROQ_API_KEY`, `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`. Opcionales: `GROQ_MODEL`, `GROQ_EXTRACTION_MODEL`. Telefonía: `TELNYX_API_KEY`, `TELNYX_PUBLIC_KEY` y/o Twilio (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`).

### Seguridad
*   `ADMIN_API_KEY`: Obligatoria; acceso al Dashboard y a `POST /admin/reset-global-stop`.

### Política de llamadas (V2)
*   `GLOBAL_STOP_MAX_ERRORS_IN_WINDOW` (default 3), `GLOBAL_STOP_WINDOW_SECONDS` (default 60), `ADMIN_NOTIFICATION_WEBHOOK_URL` (opcional). Ver [docs/VARIABLES_ENTORNO.md](docs/VARIABLES_ENTORNO.md).

## 3. Persistencia (Volúmenes)

El `Dockerfile` crea un usuario no-root `app` (UID 1000).
Asegúrate de que los volúmenes montados (si usas SQLite o guardas audios) tengan permisos de escritura para UID 1000.
*   Path de App: `/app`

## 4. Solución de Problemas Comunes

**Error: `Bind for 0.0.0.0:XXXX failed: port is already allocated`**
*   En Coolify, Traefik gestiona los puertos; el `docker-compose.yml` del repo **no** publica puertos en el host (app, db, redis). Si ves este error, el compose que usa Coolify no es el del repo o tiene `ports` añadidos: debe usar el compose actualizado sin ninguna sección `ports`.

**Error: `UndefinedColumnError`**
*   Causa: Los scripts de parcheo no corrieron.
*   Solución: Revisar logs de inicio. El script `startup.sh` imprime `🛠️ Applying manual patches...`. Si fallan, verificar credenciales de DB.

**Error: `Connection Refused` a DB**
*   Causa: `POSTGRES_SERVER` incorrecto.
*   Solución: En Coolify, verifica el nombre del recurso de base de datos interconectado.
