# AI Development Log

Registro de las interacciones con IA que **afectaron significativamente** el desarrollo (no hace falta anotar cada prompt).
Cada fila la llena quien hizo la interacción. Las capturas van en el Word de evidencias.

## 1. Registro general

| Fecha | Persona | HU | Actividad | Herramienta IA | Qué se solicitó | Resultado | Decisión humana |
|---|---|---|---|---|---|---|---|
| 28/10 | Kelvin | HU-04 | Arquitectura | Claude Code (Claude Sonnet 5.5) | Analizar el backend antes de programar (modelos, crud, disponibilidad, recordatorios, config) | Detectó 3 restricciones: no hay migraciones (agregar una columna rompería la BD desplegada); `is_slot_free` cuenta la cita propia como ocupada; `reminder_sent` debe reiniciarse al reprogramar | Aceptada |
| 28/10 | Kelvin | HU-04 | Diseño | Claude Code (Claude Sonnet 5.5) | Proponer cómo identificar la cita sin cuentas de usuario | Token firmado (HMAC) sin cambios de esquema, en vez de una columna nueva en la BD | Aceptada; pendiente de revisión por Roy |
| 28/10 | Kelvin | HU-04 | Código | Claude Code (Claude Sonnet 5.5) | Backend: `manage.py`, router `/api/manage/*`, `exclude_id` en disponibilidad, mensajes de WhatsApp. Frontend: `manage.html` y enlace en la reserva confirmada | 4 endpoints nuevos y página de autogestión (cancelar y reprogramar) | Aceptada tras corregir los 2 errores de la sección 2 |
| 28/10 | Kelvin | HU-04 | Testing | Claude Code (Claude Sonnet 5.5) | Crear pruebas automatizadas de la historia | 15 pruebas nuevas en `test_manage.py`; suite en 21/21 | Aceptada |
| 28/10 | Kelvin | HU-04 | Testing (pre-chequeo del Developer) | Claude Code (Claude Sonnet 5.5) + Playwright | Probar en navegador: reservar, abrir el enlace, reprogramar, cancelar y enlace falso | Todo correcto (capturas en `docs/evidencias/HU-04_*.png`). La validación formal la hace Einer (QA) | Aceptada |
| | | | | | | | |

Ejemplos de "Decisión humana": *Aceptada*, *Aceptada parcialmente*, *Modificada*, *Corregida*, *Rechazada*.

## 2. Respuestas incorrectas de la IA

| # | Fecha | Persona | HU | Herramienta | Qué se pidió | Qué respondió mal | Cómo se detectó | Corrección |
|---|---|---|---|---|---|---|---|---|
| 1 | 28/10 | Kelvin | HU-04 | Claude Code (Claude Sonnet 5.5) | Esquema `ManageOut` para la vista de la cita | Declaró `can_change` como campo obligatorio, pero el router lo rellena después de validar el objeto: toda petición a `/api/manage/{token}` fallaba con `ValidationError` | Las pruebas automatizadas: 5 fallaron en la primera ejecución | Se le dio valor por defecto (`can_change: bool = False`); suite en verde |
| 2 | 28/10 | Kelvin | HU-04 | Claude Code (Claude Sonnet 5.5) | Script de parche para `notifications.py` (mensajes de WhatsApp) | Generó los `\n` de los textos como saltos de línea reales dentro de f-strings: código con error de sintaxis | Se verificó la sintaxis con `ast.parse` antes de ejecutar nada | Se reescribieron los 3 mensajes con `\n` escapados; sintaxis correcta |

## 3. Cambios que rechazamos de la IA

| # | Fecha | Persona | HU | Cambio propuesto | Por qué se rechazó | Alternativa adoptada |
|---|---|---|---|---|---|---|
| 1 | | | | | | |

## 4. Decisiones tomadas por humanos

| # | Fecha | Quién | Decisión | Opciones evaluadas | Justificación |
|---|---|---|---|---|---|
| 1 | 27/10 | Equipo | Elegir CitaFácil como repositorio base | 4 repos de la lista | Python/FastAPI + SQLite sin framework de front; ya trae pruebas (6) y motor de disponibilidad |
| 2 | 27/10 | Equipo | Adaptar HU-01 a "datos guardados" = nombre y celular (el repo no tiene pago) | Implementar un pago simulado | Evitar inventar un flujo de pago ajeno al repo |
| 6 | 28/10 | Propuesta de la IA (HU-04), pendiente de confirmar por Roy (Reviewer) | Identificar la cita con un token firmado (HMAC) en vez de agregar una columna a la base de datos | Columna `manage_token` en `appointments` | El proyecto no tiene migraciones: una columna nueva rompería la base ya desplegada |
| 7 | 28/10 | Propuesta de la IA (HU-04), pendiente de confirmar | Solo se puede cancelar o reprogramar hasta 2 horas antes (`MANAGE_MIN_HOURS_BEFORE`) | Sin límite de anticipación | Evita cancelaciones cuando ya no se puede reasignar el horario; es configurable |
| 8 | 28/10 | Propuesta de la IA (HU-04), pendiente de confirmar | Al reprogramar se reinicia `reminder_sent` | Dejarlo como estaba | Si no, el cliente no recibiría recordatorio de la nueva fecha |
