# Asistente Andrea V2 – Copia de trabajo

Esta carpeta es una **copia limpia** del proyecto para desarrollo.

**Incluido:** app, tests, alembic, scripts, docs, configuración (Docker, Python, Vite), documentación principal y scripts de simulación.

**Excluido (ruido):** carpetas `back_audit_*`, `backup`, `audit`; scripts de depuración/auditoría sueltos; reportes y logs generados; archivos de warnings y parches puntuales.

Para empezar: copiar `.env.example` a `.env`, configurar variables y ejecutar con `run_local.ps1` o `uvicorn app.main:app --reload`.
