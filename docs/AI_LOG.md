# AI Development Log

Registro de las interacciones con IA que **afectaron significativamente** el desarrollo (no hace falta anotar cada prompt).
Cada fila la llena quien hizo la interacción. Las capturas van en el Word de evidencias.

## 1. Registro general

| Fecha | Persona | HU | Actividad | Herramienta IA | Qué se solicitó | Resultado | Decisión humana |
|---|---|---|---|---|---|---|---|
| 27/10 | Kelvin | HU-01 | Arquitectura | Claude Code (Claude Sonnet 5.5) | Analizar el repo (index.html, schemas, crud, tests) antes de modificar código | Detectó que el repo no tiene pago ni cuentas; que el backend ya normaliza el celular a +56… y lo devuelve; y que el flujo es de 3 pasos | Aceptada |
| 27/10 | Kelvin | HU-01 | Código | Claude Code (Claude Sonnet 5.5) | Reserva en un clic con datos guardados en el navegador, y "Olvidar mis datos" | Cambios en `frontend/index.html` (reserva rápida, `localStorage`, función `book()` compartida) | Aceptada; pendiente de revisión por Roy |
| 27/10 | Kelvin | HU-01 | Testing | Claude Code (Claude Sonnet 5.5) | Crear pruebas automatizadas de la historia | 3 pruebas nuevas en `test_booking.py`; suite en 9/9 | Aceptada |
| 27/10 | Kelvin | HU-01 | Testing (pre-chequeo del Developer) | Claude Code + Playwright | Probar en navegador: cliente nuevo, cliente recurrente, olvidar datos y nombre con HTML | Todo correcto (captura en `docs/evidencias/HU-01_reserva-rapida.png`). La validación formal la hace Einer (QA) | Aceptada |
| | | | | | | | |

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
| 3 | 27/10 | Propuesta de la IA (HU-01), pendiente de confirmar por Roy (Reviewer) | Guardar nombre y celular solo en `localStorage`, sin endpoint de búsqueda por celular | Endpoint público que devuelva el nombre dado un celular | Un endpoint así filtraría datos personales a cualquiera que conozca un número |
| 4 | 27/10 | Propuesta de la IA (HU-01), pendiente de confirmar por Roy (Reviewer) | Guardar el celular que **devuelve la API** (normalizado), no el tecleado | Guardar el texto tal como lo escribió el usuario | Evita guardar formatos distintos del mismo número |
| 5 | 27/10 | Propuesta de la IA (HU-01), pendiente de confirmar | No corregir en HU-01 el bug previo de la fecha mínima del calendario (usa fecha UTC: de noche en Panamá bloquea "hoy") | Corregirlo dentro de esta historia | Fuera de alcance; queda como mejora para otra historia (HU-02 toca el calendario) |
