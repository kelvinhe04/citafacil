# AI Development Log

Registro de las interacciones con IA que **afectaron significativamente** el desarrollo (no hace falta anotar cada prompt).
Cada fila la llena quien hizo la interacción. Las capturas van en el Word de evidencias.

## 1. Registro general

| Fecha | Persona | HU | Actividad | Herramienta IA | Qué se solicitó | Resultado | Decisión humana |
|---|---|---|---|---|---|---|---|
| 27/10 | | | Arquitectura | | Analizar el repo antes de modificar | | |
| | | | | | | | |
| 28/10 | Roy | HU-02 | Arquitectura | Claude Code (Claude Opus 5.5) | Analizar `availability.py`, `routers/public.py`, `index.html` y las ramas abiertas (HU-01, HU-03, HU-04, fix) antes de programar | Propuso reutilizar `generate_slots` día por día; detectó que HU-04 cambia la firma de `generate_slots` y el import de `public.py` (riesgo de conflicto) | Aceptada |
| 28/10 | Roy | HU-02 | Código | Claude Code (Claude Opus 5.5) | Endpoint `GET /api/availability/month?service_id=&month=YYYY-MM` con el estado de cada día | `month_availability()` en `availability.py`, esquema `DayAvailabilityOut`, validación del mes con regex (422) y 404 para servicio inactivo | Aceptada; pendiente de revisión por Einer |
| 28/10 | Roy | HU-02 | Código | Claude Code (Claude Opus 5.5) | Reemplazar el `<input type="date">` por un calendario mensual | Calendario lunes-domingo con días disponibles (verde), ocupados (rojo, tachado) y cerrados/pasados (gris); solo los disponibles son clicables | Aceptada tras corregir los errores 3 y 4 de la sección 2 |
| 28/10 | Roy | HU-02 | Testing | Claude Code (Claude Opus 5.5) | Crear pruebas automatizadas de la historia | `test_calendar.py`: 14 pruebas (incluye mes bisiesto, día lleno, cita cancelada que no bloquea y formatos de mes inválidos); suite en 20/20 | Aceptada |
| 28/10 | Roy | HU-02 | Testing (pre-chequeo del Developer) | Claude Code (Claude Opus 5.5) + Playwright | Probar en navegador: estados del mes, clic en día lleno, navegación de meses, cambio de servicio y vista móvil | Todo correcto (capturas en `docs/evidencias/HU-02_*.png`). La validación formal la hace Kelvin (QA) | Aceptada |

Ejemplos de "Decisión humana": *Aceptada*, *Aceptada parcialmente*, *Modificada*, *Corregida*, *Rechazada*.

## 2. Respuestas incorrectas de la IA

| # | Fecha | Persona | HU | Herramienta | Qué se pidió | Qué respondió mal | Cómo se detectó | Corrección |
|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | |
| 3 | 28/10 | Roy | HU-02 | Claude Code (Claude Opus 5.5) | Título del calendario ("octubre de 2026") con mayúscula inicial | Usó CSS `text-transform: capitalize`, que pone en mayúscula cada palabra: "Octubre **De** 2026" | Revisando la captura de Playwright | Se capitaliza solo la primera letra desde JavaScript |
| 4 | 28/10 | Roy | HU-02 | Claude Code (Claude Opus 5.5) | Celdas cuadradas para los días | Limitó la altura (`max-height`) pero no el ancho: las celdas quedaban pegadas a la izquierda de su columna, desalineadas con los encabezados Lu…Do | Revisando la captura de Playwright | `max-width` + `justify-self: center` con `aspect-ratio: 1/1` |

## 3. Cambios que rechazamos de la IA

| # | Fecha | Persona | HU | Cambio propuesto | Por qué se rechazó | Alternativa adoptada |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| 2 | 28/10 | Roy | HU-02 | Agregar `from typing import Optional` en `availability.py` y `month_availability` al import existente de `public.py` | Un merge de prueba con la rama de HU-04 dio conflicto: HU-04 agrega esas mismas líneas | `date \| None` (válido con `from __future__ import annotations`) y el import nuevo en su propia línea; el merge de prueba con HU-01, HU-03, HU-04 y el fix queda limpio |

## 4. Decisiones tomadas por humanos

| # | Fecha | Quién | Decisión | Opciones evaluadas | Justificación |
|---|---|---|---|---|---|
| 1 | 27/10 | Equipo | Elegir CitaFácil como repositorio base | 4 repos de la lista | Python/FastAPI + SQLite sin framework de front; ya trae pruebas (6) y motor de disponibilidad |
| 2 | 27/10 | Equipo | Adaptar HU-01 a "datos guardados" = nombre y celular (el repo no tiene pago) | Implementar un pago simulado | Evitar inventar un flujo de pago ajeno al repo |
| 9 | 28/10 | Propuesta de la IA (HU-02), pendiente de confirmar por Einer (Reviewer) | Cuatro estados por día: `past`, `closed`, `full`, `available`. "Hoy" sin horas restantes se muestra como ocupado | Solo disponible/no disponible; o un estado extra "pocos horarios" | Cumple el criterio (disponibles, ocupados y cerrados distinguibles) sin sobrecargar la vista; el número de horarios libres va en el tooltip |
| 10 | 28/10 | Propuesta de la IA (HU-02), pendiente de confirmar | El calendario usa la fecha local del navegador y el backend decide qué días son pasados con la zona horaria del negocio | Mantener el `min` del input calculado con `toISOString()` (UTC) | Corrige el bug que HU-01 dejó anotado (decisión 5): de noche en Panamá la fecha UTC ya es "mañana" y bloqueaba "hoy" |
| 11 | 28/10 | Propuesta de la IA (HU-02), pendiente de confirmar | No corregir en HU-02 el desborde horizontal de la página en móvil (418 px en 375 px) | Corregirlo aquí | Ya existía en `main` (lo causa el degradado `.hero::before` de 460 px), no lo introduce el calendario |
