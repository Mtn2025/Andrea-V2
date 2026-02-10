# Plan: Core V2 y capas desde cero

**Fecha**: 2026-02-09  
**Objetivo**: Construir un orquestador V2 limpio, capa por capa, usando el código actual solo como **referencia**. Sin reparar ni “conectar” sobre el legacy para evitar contaminación y errores en cascada.

---

## 1. Por qué V2 desde cero

- **Reparar y vincular todo sobre el legacy** implica:
  - Múltiples puntos de fallo por dependencias ocultas.
  - Código obsoleto o redundante que sigue en uso.
  - Contratos (ports) desalineados con el uso real.
- **Construir V2** permite:
  - Incluir **solo lo útil** (flujos, contratos, políticas ya definidas).
  - **Conectar limpiamente** entre capas (dominio → aplicación → adapters).
  - Mantener el legacy funcionando mientras V2 crece (strangler fig).

**Principio**: Legacy = idea y referencia. V2 = implementación nueva, mínima y clara.

---

## 2. Estrategia general

1. **No tocar el core/orchestrator actual** como “base a parchear”. Solo leerlo como documentación.
2. **Crear un árbol nuevo** bajo `app_v2/` (o `core_v2/`, según prefieras) con la misma idea hexagonal pero sin arrastrar deuda.
3. **Avanzar capa por capa**:
   - Capa 1: Dominio (ports, modelos, value objects, 1–2 use cases mínimos).
   - Capa 2: Aplicación (orquestador mínimo, pipeline mínimo, frames).
   - Capa 3: Adaptadores (solo los que necesitemos para un flujo end-to-end: p. ej. Browser).
   - Capa 4: Entrada (un solo endpoint WebSocket o ruta que use V2).
4. **Un flujo completo primero**: p. ej. “Simulador (navegador): audio entrante → STT → LLM → TTS → audio saliente”, sin tools ni campañas. Luego ampliar.

---

## 3. Estructura propuesta para V2

```
app_v2/
├── domain/           # Capa 1: solo tipos y contratos
│   ├── ports/       # STT, LLM, TTS, Config, Transport (solo lo que usemos)
│   ├── models/      # Request/Response, Chunks (mínimo)
│   ├── value_objects/
│   └── use_cases/   # 1–2: p. ej. Transcribe, Synthesize (o un solo “ProcessTurn”)
├── application/     # Capa 2: orquestación
│   ├── orchestrator.py
│   ├── pipeline.py
│   ├── frames.py
│   └── config/      # Cómo se carga config (perfil browser/telnyx/twilio)
├── adapters/        # Capa 3: implementaciones
│   ├── inbounds/    # WebSocket (simulador primero)
│   └── outbounds/  # Azure STT/TTS, Groq LLM, Config (repo), etc.
└── main.py          # o entrada mínima que monta V2
```

- **No** duplicar todo el dominio legacy: solo los ports y modelos que use el primer flujo.
- **Config**: en V2, el contrato del port de configuración debe coincidir con el uso (p. ej. `get_config_for_call(client_type, agent_id?)` que devuelva un DTO, no el ORM).

---

## 4. Orden de construcción sugerido

| Fase | Contenido | Referencia legacy | Entregable |
|------|-----------|-------------------|------------|
| **1** | Dominio V2: ports (STT, LLM, TTS, AudioTransport, Config), modelos mínimos (Request/Response, Chunk), 0–1 value objects (VoiceConfig). | `app/domain/ports/*`, `models/*` | Contratos claros, sin dependencias de app/core ni app/adapters. |
| **2** | Aplicación V2: Frames (solo los necesarios: Audio, Text, Start/End), Pipeline mínimo (cadena lineal), Orquestador mínimo (carga config, crea pipeline, conecta transport ↔ pipeline). | `app/core/frames.py`, `pipeline.py`, `orchestrator_v2.py` | Un flujo “audio in → audio out” en memoria (mocks de STT/LLM/TTS). |
| **3** | Adaptadores V2: implementaciones reales de STT (Azure), LLM (Groq), TTS (Azure), Config (lectura desde BD), Transport (WebSocket). | `app/adapters/*`, `app/core/voice_ports.py` | Mismo flujo con proveedores reales, 1 cliente (browser). |
| **4** | Entrada V2: una ruta/WebSocket que instancie el orquestador V2 y maneje la sesión (simulador). | `app/api/routes_simulator.py` | Llamada desde el simulador usando **solo** V2. |
| **5** | Políticas: cierre al final de llamada → escritura en Historial; en error grave → disculpa, cierre, y (si persiste) paro + notificación. | `docs/POLITICAS_Y_FLUJOS.md` | Lógica en orquestador V2 y/o en un “CallLifecycle” claro. |

A partir de la fase 5, se pueden añadir: perfiles Telnyx/Twilio, tools, campañas, etc., **siempre sobre V2**, sin volver a tocar el core legacy para esas funciones.

---

## 5. Qué tomar del legacy (solo como idea)

- **Dominio**: idea de los ports (STTPort, LLMPort, TTSPort, AudioTransport, ConfigRepositoryPort), nombres de métodos (transcribe, generate_stream, synthesize), y de los DTOs (TTSRequest, LLMRequest, etc.). No copiar excepciones o helpers que no usemos.
- **Pipeline**: idea de “frames que pasan por una cadena de procesadores” y de control channel para interrupt/emergency. No la cola con prioridad ni backpressure en la primera versión si no hace falta.
- **Orquestador**: idea de “cargar config → crear pipeline → conectar transport a pipeline → iniciar/detener”. No la FSM completa al inicio; se puede introducir una FSM mínima cuando tengamos el flujo estable.
- **Config**: idea de “perfil por client_type” y overlays (browser vs telco). En V2 el port debe devolver un DTO; el adapter lee de BD y aplica perfil/overlay antes de devolverlo.

---

## 6. Qué ignorar o dejar para después

- Código muerto (Protocols no usados, parámetros sin uso).
- Port de configuración que devuelve ORM; en V2 solo DTO.
- Fallbacks Google si no los queremos en el primer slice (se pueden añadir después como otro adapter + flag).
- Tool calling, campañas, CRM en tiempo real, webhooks durante la llamada: no en el primer flujo V2.
- Toda la lógica de “reparar” el core actual: no mezclar con V2.

---

## 7. Comentarios y riesgos

- **Riesgo**: dos orquestadores (legacy y V2) durante un tiempo. Se mitiga teniendo **una sola entrada** por flujo (p. ej. simulador usa solo V2; Telnyx/Twilio siguen en legacy hasta que migremos).
- **Ventaja**: pruebas del simulador (browser) pueden correr 100% sobre V2; el resto de la app sigue estable en legacy.
- **Migración**: cuando V2 cubra Telnyx/Twilio y políticas de error, se puede deprecar el orquestador legacy y redirigir todas las rutas a V2.

Si estás de acuerdo con este plan, el siguiente paso sería **definir la carpeta `app_v2/`** y crear la **Fase 1 (dominio V2)** con los ports y modelos mínimos, sin implementaciones, solo contratos y tipos.
