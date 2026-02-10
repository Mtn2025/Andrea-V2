# Convenciones de documentación del proyecto

**Versión**: 1.0  
**Fecha de vigencia**: 2026-02-09  
**Alcance**: Toda la documentación técnica y de producto del Asistente de Voz (legacy y V2).  
**Objetivo**: Garantizar documentación profesional, estricta y trazable en todo el ciclo de vida del producto.

---

## 1. Principios

1. **Obligatoriedad**: Todo cambio de comportamiento, nueva funcionalidad, decisión de diseño o corrección que afecte al sistema debe quedar registrado en los documentos correspondientes. No se asume que “el código documenta solo”; el código y la documentación se complementan.
2. **Trazabilidad**: Cada decisión o hallazgo debe poder localizarse por documento, sección y, cuando aplique, por fecha o versión. Los documentos vivos (Build Log, planes) no eliminan entradas pasadas; solo añaden o corrigen de forma explícita.
3. **Rigor**: Redacción clara, sin ambigüedades innecesarias. Términos técnicos usados de forma consistente. Referencias cruzadas por nombre de archivo o ruta cuando se cite código.
4. **Profesionalismo**: Estructura predecible (encabezados, tablas, listas), formato uniforme (Markdown estándar), y separación entre “hecho” y “pendiente” o “sugerido”.

---

## 2. Estructura obligatoria de documentos por tipo

### 2.1 Documentos de plan o fase (ej. PLAN_TRABAJO_PRODUCCION.md)

- **Título** y **objetivo** del documento en las primeras líneas.
- **Metodología o criterios** aplicables (ej. “legacy como referencia”, “revisión previa”).
- **Secciones numeradas o con encabezados claros** (Fases, Alcance, Criterios de cierre).
- **Estado y fechas**: al actualizar, indicar fecha de la última modificación relevante al final del documento o en la sección afectada.
- **Referencias**: enlaces o rutas a otros documentos (Build Log, políticas, revisiones legacy) cuando se cite un paso o decisión.

### 2.2 Build Log (APP_V2_BUILD_LOG.md)

- **Por cada paso (Paso N)**:
  - **Decisión N.x**: título breve, cuerpo con qué se decidió, motivo y referencia legacy si aplica.
  - **Archivos creados/modificados**: tabla con ruta y propósito.
  - **Índice o resumen** de archivos V2 tras ese paso (opcional pero recomendado).
- **No eliminar** pasos anteriores. Las correcciones se hacen añadiendo una subsección “Corrección” o actualizando la decisión con una nota “(actualizado: fecha, motivo)”.
- **Próximos pasos**: sección explícita de lo no ejecutado aún, para evitar olvidos.

### 2.3 Revisión legacy (ej. REVISION_LEGACY_FASE_N.md)

- **Objetivo de la revisión**: qué fase o bloque se va a implementar y qué se buscaba en legacy.
- **Ámbito revisado**: lista de archivos o rutas con descripción breve de su rol.
- **Hallazgos**: tabla o lista con (archivo/ruta, hallazgo, relevancia para V2). Incluir números de línea o nombres de símbolos cuando aporten.
- **Conclusiones**: qué se toma como referencia, qué se evita o no se replica, y qué dudas quedan (y cómo se resuelven: investigación, decisión posterior).
- **Fecha de la revisión**.

### 2.4 Políticas y flujos (POLITICAS_Y_FLUJOS.md)

- **Secciones estables**: flujo de datos, política de errores, perfiles, excepciones (ej. fallbacks).
- **Estado en código**: para cada política, indicar qué está implementado y qué falta (con referencia a módulo o capa si aplica).
- Al implementar una política en código, **actualizar** este documento con la referencia al código y la decisión (o enlace al Build Log).

### 2.5 README de paquetes (app_v2/README.md, app_v2/domain/README.md, etc.)

- **Propósito** del paquete en 1–2 frases.
- **Responsabilidades**: qué hace (y qué no hace).
- **Estructura** o índice de módulos/archivos principales.
- **Reglas** (ej. “app_v2 no importa app”).
- **Estado actual**: breve (completado / en curso / pendiente) con enlace al Build Log o al plan cuando aplique.

---

## 3. Convenciones de redacción

- **Tiempo verbal**: presente para descripción de comportamiento y estado actual (“El orquestador carga la configuración”); pasado para hechos ya realizados (“Se implementó en Paso 4”).
- **Código y rutas**: en texto plano o `monoespaciado` (ej. `app_v2/application/orchestrator.py`). Rutas relativas al repositorio salvo que se indique lo contrario.
- **Términos clave**: usar de forma consistente (ej. “orquestador V2”, “core V2”, “legacy”, “Historial”, “paro global”, “política de errores”). Si se introduce un término nuevo, definirlo en el documento donde aparezca por primera vez.
- **Idioma**: español para documentación de producto y planes; se permite inglés en nombres técnicos (código, APIs, variables de entorno).

---

## 4. Control de cambios en documentación

- **Documentos vivos** (Build Log, plan de trabajo, políticas): al añadir una sección o decisión importante, se puede añadir al final del documento una línea tipo “*Actualizado: YYYY-MM-DD, motivo breve*”.
- **Nuevos documentos**: deben crearse con **título**, **fecha** (o versión) y **propósito** en las primeras líneas.
- **Deprecación**: si un documento deja de ser la fuente de verdad, indicar en su inicio: “**Deprecado**: reemplazado por [enlace o ruta]. Fecha: YYYY-MM-DD.”

---

## 5. Ubicación de documentos

| Tipo | Ubicación | Ejemplo |
|------|-----------|---------|
| Planes y fases | `docs/` | `PLAN_TRABAJO_PRODUCCION.md` |
| Build Log V2 | `docs/` | `APP_V2_BUILD_LOG.md` |
| Revisión legacy por fase | `docs/` | `REVISION_LEGACY_FASE_1.md` |
| Políticas y flujos | `docs/` | `POLITICAS_Y_FLUJOS.md` |
| Convenciones (este doc) | `docs/` | `CONVENCIONES_DOCUMENTACION.md` |
| README de paquetes | Raíz del paquete | `app_v2/README.md`, `app_v2/domain/README.md` |
| Producción y despliegue | `docs/` o `docs/production/` | `DEPLOYMENT.md`, `production/PRODUCTION_README.md` |

---

## 6. Checklist antes de dar por cerrada una fase

- [ ] Revisión legacy (si aplica) documentada en `docs/REVISION_LEGACY_FASE_N.md` o equivalente.
- [ ] Decisiones y archivos del paso registrados en `docs/APP_V2_BUILD_LOG.md`.
- [ ] Políticas afectadas (ej. errores) actualizadas en `docs/POLITICAS_Y_FLUJOS.md` con estado en código.
- [ ] README de paquetes tocados actualizados (estado, responsabilidades).
- [ ] Plan de trabajo (`PLAN_TRABAJO_PRODUCCION.md`) con criterios de cierre de la fase verificables y, si se avanza, fecha o nota de avance.

---

*Este documento es la referencia para el estándar de documentación del proyecto. Cualquier excepción debe quedar justificada y anotada en el documento afectado.*
