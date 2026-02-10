# Aplicación V2

## Responsabilidad

Orquestar el flujo de voz: recibir audio del cliente, transcribir (STT), generar respuesta (LLM), sintetizar (TTS) y enviar audio. Usa **solo** los ports del dominio; no contiene implementaciones de proveedores.

## Contenido

| Módulo | Propósito |
|--------|-----------|
| `frames.py` | Tipos de mensajes que circulan por el pipeline: Frame (base), AudioFrame, TextFrame. |
| `processor.py` | Interface Processor: procesa un Frame y devuelve el siguiente (o None). |
| `processors/` | STTProcessor, LLMProcessor, TTSProcessor: implementan Processor usando los ports. |
| `pipeline.py` | Pipeline: cadena lineal de procesadores; run(frame) ejecuta en secuencia. |
| `orchestrator.py` | Orchestrator: carga config, construye pipeline, expone process_audio(audio_bytes) y envía resultado por transport. |

## Flujo mínimo (Fase 2)

1. Orchestrator.start() → carga CallConfig desde ConfigPort.
2. Orchestrator.process_audio(audio_bytes) → construye Pipeline(STT → LLM → TTS), ejecuta con AudioFrame(audio_bytes), obtiene AudioFrame(resultado) y llama transport.send_audio().
3. Sin FSM, sin control channel, sin cola con prioridad; flujo secuencial y síncrono por llamada.

## Qué no incluye

- VAD, barge-in, interrupt (fases posteriores).
- Cola de frames, backpressure (fases posteriores).
- Tool calling, FSM (fases posteriores).
- Cualquier import desde `app/`.

## Referencia

- Build Log: docs/APP_V2_BUILD_LOG.md (Paso 2).
- Plan: docs/PLAN_CORE_V2.md.
