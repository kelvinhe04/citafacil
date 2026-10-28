# AI Development Log

Registro de las interacciones con IA que **afectaron significativamente** el desarrollo (no hace falta anotar cada prompt).
Cada fila la llena quien hizo la interacción. Las capturas van en el Word de evidencias.

## 1. Registro general

| Fecha | Persona | HU | Actividad | Herramienta IA | Qué se solicitó | Resultado | Decisión humana |
|---|---|---|---|---|---|---|---|
| 27/10 | | | Arquitectura | | Analizar el repo antes de modificar | | |
| | | | | | | | |
| 28/10 | Roy | HU-05 | Arquitectura | Claude Code (Claude Opus 5.5) | Analizar `crud.list_appointments`, `routers/admin.py` y `admin.html` antes de programar | Propuso ampliar `list_appointments` con un rango `date_from`/`date_to` (sin romper el filtro `date` del panel) y un módulo `export.py` aparte | Aceptada |
| 28/10 | Roy | HU-05 | Código | Claude Code (Claude Opus 5.5) | Endpoint `GET /api/admin/appointments/export` y botón "Exportar CSV" en `admin.html` | CSV con BOM UTF-8, estados en español y neutralización de fórmulas; el botón descarga con `fetch` + `Blob` porque el endpoint exige `X-Admin-Token` | Aceptada; pendiente de revisión por Einer |
| 28/10 | Roy | HU-05 | Testing | Claude Code (Claude Opus 5.5) | Crear pruebas automatizadas de la historia | `test_export_csv.py`: 10 pruebas (auth, cabeceras, BOM, contenido, orden, filtros, rango inclusivo, fórmulas y filtros inválidos); suite en 16/16 | Aceptada |
| 28/10 | Roy | HU-05 | Testing (pre-chequeo del Developer) | Claude Code (Claude Opus 5.5) + Playwright | Descargar el CSV desde el panel, sin filtros y filtrando por estado | Mismo número de filas en la tabla y en el CSV; BOM presente (captura en `docs/evidencias/HU-05_exportar-csv.png`). La validación formal la hace Kelvin (QA) | Aceptada |

Ejemplos de "Decisión humana": *Aceptada*, *Aceptada parcialmente*, *Modificada*, *Corregida*, *Rechazada*.

## 2. Respuestas incorrectas de la IA

| # | Fecha | Persona | HU | Herramienta | Qué se pidió | Qué respondió mal | Cómo se detectó | Corrección |
|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | |

## 3. Cambios que rechazamos de la IA

| # | Fecha | Persona | HU | Cambio propuesto | Por qué se rechazó | Alternativa adoptada |
|---|---|---|---|---|---|---|
| 1 | | | | | | |

## 4. Decisiones tomadas por humanos

| # | Fecha | Quién | Decisión | Opciones evaluadas | Justificación |
|---|---|---|---|---|---|
| 1 | 27/10 | Equipo | Elegir CitaFácil como repositorio base | 4 repos de la lista | Python/FastAPI + SQLite sin framework de front; ya trae pruebas (6) y motor de disponibilidad |
| 2 | 27/10 | Equipo | Adaptar HU-01 a "datos guardados" = nombre y celular (el repo no tiene pago) | Implementar un pago simulado | Evitar inventar un flujo de pago ajeno al repo |
| 12 | 28/10 | Propuesta de la IA (HU-05), pendiente de confirmar por Einer (Reviewer) | Separador coma + BOM UTF-8 | Punto y coma (lo que espera Excel con configuración regional de Chile) o un parámetro `sep` | La coma es el estándar (RFC 4180) y la abren bien Google Sheets, LibreOffice y Excel en configuración de Panamá/EE. UU.; el BOM evita que Excel rompa tildes y eñes |
| 13 | 28/10 | Propuesta de la IA (HU-05), pendiente de confirmar | El botón exporta exactamente lo que muestra la tabla (filtros de fecha y estado); el rango `date_from`/`date_to` queda disponible en la API | Agregar campos "Desde/Hasta" al panel | Mantiene el panel simple y lo que se descarga coincide con lo que se ve |
| 14 | 28/10 | Propuesta de la IA (HU-05), pendiente de confirmar | Prefijar con `'` el nombre, el servicio y las notas que empiecen con `= + - @` | Exportar el texto tal cual | Lo escribe el cliente desde la página pública: sin esto, un nombre como `=HYPERLINK(...)` se ejecutaría como fórmula al abrir el archivo. El celular no se toca porque el backend ya lo normaliza |
| 15 | 28/10 | Propuesta de la IA (HU-05), pendiente de confirmar | La columna `precio` es el precio **actual** del servicio | Guardar el precio en cada cita | La tabla `appointments` no guarda el precio y el repo no tiene migraciones; queda como limitación conocida |
