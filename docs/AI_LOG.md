# AI Development Log

Registro de las interacciones con IA que **afectaron significativamente** el desarrollo (no hace falta anotar cada prompt).
Cada fila la llena quien hizo la interacción. Las capturas van en el Word de evidencias.

## 1. Registro general

| Fecha | Persona | HU | Actividad | Herramienta IA | Qué se solicitó | Resultado | Decisión humana |
|---|---|---|---|---|---|---|---|
| 27/10 | | | Arquitectura | | Analizar el repo antes de modificar | | |
| 28/10 | Einer | HU-03 | Implementación | Claude Code (Sonnet 5.5) | Endpoint de histórico/previsión de demanda, gráficos en `admin.html` y pruebas | `forecast.py`, `GET /api/admin/forecast`, gráficos de barras sin librerías, 7 pruebas nuevas (13 en total pasan) | Pendiente de revisión: probar a mano en el panel |
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
