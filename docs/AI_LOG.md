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
| 27/10 | Kelvin | HU-01 | Arquitectura | Claude Code (Claude Sonnet 5.5) | Analizar el repo (index.html, schemas, crud, tests) antes de modificar código | Detectó que el repo no tiene pago ni cuentas; que el backend ya normaliza el celular a +56… y lo devuelve; y que el flujo es de 3 pasos | Aceptada |
| 27/10 | Kelvin | HU-01 | Código | Claude Code (Claude Sonnet 5.5) | Reserva en un clic con datos guardados en el navegador, y "Olvidar mis datos" | Cambios en `frontend/index.html` (reserva rápida, `localStorage`, función `book()` compartida) | Aceptada; pendiente de revisión por Roy |
| 27/10 | Kelvin | HU-01 | Testing | Claude Code (Claude Sonnet 5.5) | Crear pruebas automatizadas de la historia | 3 pruebas nuevas en `test_booking.py`; suite en 9/9 | Aceptada |
| 27/10 | Kelvin | HU-01 | Testing (pre-chequeo del Developer) | Claude Code + Playwright | Probar en navegador: cliente nuevo, cliente recurrente, olvidar datos y nombre con HTML | Todo correcto (captura en `docs/evidencias/HU-01_reserva-rapida.png`). La validación formal la hace Einer (QA) | Aceptada |
| 28/10 | Einer | HU-03 | Implementación | Claude Code (Sonnet 5.5) | Endpoint de histórico/previsión de demanda, gráficos en `admin.html` y pruebas | `forecast.py`, `GET /api/admin/forecast`, gráficos de barras sin librerías, 7 pruebas nuevas (13 en total pasan) | Pendiente de revisión: probar a mano en el panel |
| | | | | | | | |
| 28/10 | Roy | HU-05 | Arquitectura | Claude Code (Claude Opus 5.5) | Analizar `crud.list_appointments`, `routers/admin.py` y `admin.html` antes de programar | Propuso ampliar `list_appointments` con un rango `date_from`/`date_to` (sin romper el filtro `date` del panel) y un módulo `export.py` aparte | Aceptada |
| 28/10 | Roy | HU-05 | Código | Claude Code (Claude Opus 5.5) | Endpoint `GET /api/admin/appointments/export` y botón "Exportar CSV" en `admin.html` | CSV con BOM UTF-8, estados en español y neutralización de fórmulas; el botón descarga con `fetch` + `Blob` porque el endpoint exige `X-Admin-Token` | Aceptada; pendiente de revisión por Einer |
| 28/10 | Roy | HU-05 | Testing | Claude Code (Claude Opus 5.5) | Crear pruebas automatizadas de la historia | `test_export_csv.py`: 10 pruebas (auth, cabeceras, BOM, contenido, orden, filtros, rango inclusivo, fórmulas y filtros inválidos); suite en 16/16 | Aceptada |
| 28/10 | Roy | HU-05 | Testing (pre-chequeo del Developer) | Claude Code (Claude Opus 5.5) + Playwright | Descargar el CSV desde el panel, sin filtros y filtrando por estado | Mismo número de filas en la tabla y en el CSV; BOM presente (captura en `docs/evidencias/HU-05_exportar-csv.png`). La validación formal la hace Kelvin (QA) | Aceptada |

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
| 3 | 27/10 | Propuesta de la IA (HU-01), pendiente de confirmar por Roy (Reviewer) | Guardar nombre y celular solo en `localStorage`, sin endpoint de búsqueda por celular | Endpoint público que devuelva el nombre dado un celular | Un endpoint así filtraría datos personales a cualquiera que conozca un número |
| 4 | 27/10 | Propuesta de la IA (HU-01), pendiente de confirmar por Roy (Reviewer) | Guardar el celular que **devuelve la API** (normalizado), no el tecleado | Guardar el texto tal como lo escribió el usuario | Evita guardar formatos distintos del mismo número |
| 5 | 27/10 | Propuesta de la IA (HU-01), pendiente de confirmar | No corregir en HU-01 el bug previo de la fecha mínima del calendario (usa fecha UTC: de noche en Panamá bloquea "hoy") | Corregirlo dentro de esta historia | Fuera de alcance; queda como mejora para otra historia (HU-02 toca el calendario) |
| 12 | 28/10 | Propuesta de la IA (HU-05), pendiente de confirmar por Einer (Reviewer) | Separador coma + BOM UTF-8 | Punto y coma (lo que espera Excel con configuración regional de Chile) o un parámetro `sep` | La coma es el estándar (RFC 4180) y la abren bien Google Sheets, LibreOffice y Excel en configuración de Panamá/EE. UU.; el BOM evita que Excel rompa tildes y eñes |
| 13 | 28/10 | Propuesta de la IA (HU-05), pendiente de confirmar | El botón exporta exactamente lo que muestra la tabla (filtros de fecha y estado); el rango `date_from`/`date_to` queda disponible en la API | Agregar campos "Desde/Hasta" al panel | Mantiene el panel simple y lo que se descarga coincide con lo que se ve |
| 14 | 28/10 | Propuesta de la IA (HU-05), pendiente de confirmar | Prefijar con `'` el nombre, el servicio y las notas que empiecen con `= + - @` | Exportar el texto tal cual | Lo escribe el cliente desde la página pública: sin esto, un nombre como `=HYPERLINK(...)` se ejecutaría como fórmula al abrir el archivo. El celular no se toca porque el backend ya lo normaliza |
| 15 | 28/10 | Propuesta de la IA (HU-05), pendiente de confirmar | La columna `precio` es el precio **actual** del servicio | Guardar el precio en cada cita | La tabla `appointments` no guarda el precio y el repo no tiene migraciones; queda como limitación conocida |
