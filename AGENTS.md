# AGENTS.md — Guía de trabajo del equipo (Proyecto 1, Tópicos Especiales II)

Este archivo lo leen **las personas y los agentes de IA** (Claude Code, Codex, Cursor, Copilot, etc.).
Si eres un agente: sigue estas reglas antes de tocar código.

- **Curso:** Tópicos Especiales II · Prof. Regis Rivera · Grupo 1GS242
- **Equipo:** Kelvin He · Roy Barrera · Einer Mosquera
- **Entrega y presentación:** miércoles **28/10/2026, 6:00 PM** (MS Teams)
- **Repositorio base:** [gianca675/citafacil](https://github.com/gianca675/citafacil) (licencia MIT; se conserva el `LICENSE` y el crédito al autor original)
- **Qué se evalúa:** el *proceso* (cómo se usó, validó, corrigió y midió la IA), no cuánto código generó.

---

## Contexto del curso (leer si eres un agente)

- `docs/DSaIA-Proyecto1.pdf`: enunciado oficial del profesor (objetivo, historias, restricciones, entrega).
- `docs/1GS242_Proyecto1_Evidencias_IA.docx`: documento de evidencias que el equipo entrega. **Los agentes sí lo editan**
  (ver reglas en la sección 6.1).

---

## 1. El proyecto en 1 minuto

CitaFácil: reservas web para pequeños negocios. Una página pública de reservas y un panel de administración.

| Capa | Tecnología | Dónde |
|---|---|---|
| Backend | Python 3, FastAPI, SQLAlchemy, Pydantic | `backend/app/` |
| Base de datos | SQLite (local) · PostgreSQL (producción) | `DATABASE_URL` |
| Frontend | HTML5 + CSS3 + JavaScript sin framework | `frontend/index.html`, `frontend/admin.html` |
| Pruebas | pytest | `backend/tests/` |

Mapa del backend: `models.py` (tablas `Service`, `Appointment`), `schemas.py` (validación), `crud.py` (BD),
`availability.py` (horarios libres y anti doble-booking), `routers/public.py` y `routers/admin.py` (endpoints),
`auth.py` (token `X-Admin-Token`), `notifications.py`/`reminders.py` (WhatsApp vía Twilio, modo demo sin credenciales).

### Ejecutar en local

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate        # Windows (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env                                  # ajustar ADMIN_TOKEN
python seed.py                                        # datos de ejemplo
python -m uvicorn app.main:app --reload               # API en http://localhost:8000/docs
```

Frontend: abrir `frontend/index.html` en el navegador (usa `http://localhost:8000`). Admin: `frontend/admin.html`.

### Pruebas

```bash
cd backend
python -m pytest -q
```

Línea base antes de empezar: **6 pruebas pasan**. No se mergea nada que la rompa.

---

## 2. Historias de usuario del sprint

| ID | Historia | Dueño (Developer) |
|---|---|---|
| **HU-01** | Como usuario recurrente, quiero reservar directamente usando mis datos guardados, para no tener que rellenar el formulario en cada compra. | Kelvin |
| **HU-02** | Como cliente, quiero ver un calendario dinámico con los días disponibles y ocupados, para elegir mi fecha rápidamente sin intentos fallidos. | Roy |
| **HU-03** | Como administrador del sistema, quiero ver gráficos de previsión de la demanda basados en el histórico, para ajustar los precios y el inventario de forma inteligente. | Einer |
| **HU-04** *(propuesta)* | Como cliente, quiero cancelar o reprogramar mi cita desde un enlace, para no tener que llamar al negocio. | Kelvin |
| **HU-05** *(propuesta)* | Como administrador, quiero exportar las reservas a CSV, para llevar el control en una hoja de cálculo. | Roy |

Notas de adaptación al repo (documentarlas en el issue de cada HU):

- CitaFácil **no tiene formulario de pago**: en HU-01 "datos guardados" = nombre y celular del cliente (p. ej. `localStorage` + reserva en un clic).
- HU-02 reutiliza `availability.py`; falta un endpoint que devuelva disponibilidad **por mes** para pintar el calendario.
- HU-03 necesita agregar el histórico de `appointments` por día/semana/servicio y graficarlo en `admin.html`.
- HU-04 y HU-05 son propuestas: el equipo puede cambiarlas, pero deben quedar como issue **antes** de programarse.

---

## 3. Roles y cuándo rotan

Cada historia tiene **tres roles**, uno por persona. Los roles **rotan en cada historia**, de modo que cada integrante
sea Developer, Reviewer y QA a lo largo del proyecto. Las historias se trabajan en paralelo, así que cada quien
cumple los tres roles a la vez en historias distintas.

| Historia | Developer | Reviewer | QA |
|---|---|---|---|
| HU-01 | Kelvin | Roy | Einer |
| HU-02 | Roy | Einer | Kelvin |
| HU-03 | Einer | Kelvin | Roy |
| HU-04 | Kelvin | Roy | Einer |
| HU-05 | Roy | Einer | Kelvin |

**Momento de la rotación:** al abrir el Pull Request de una historia, el Developer pasa a ser Reviewer o QA de la historia
de otra persona. Con 5 historias y 3 personas la rotación no puede quedar perfectamente pareja (Einer desarrolla una
historia menos); eso se acepta y se menciona en la presentación.

| Rol | Hace | No hace |
|---|---|---|
| **Developer** | Crea el issue y la rama, programa con apoyo de IA, escribe pruebas, abre el PR. | Aprobar su propio PR. |
| **Reviewer** | Lee el diff completo, revisa lo que generó la IA, comenta el PR, aprueba o pide cambios. | Reescribir el código del Developer. |
| **QA** | Ejecuta la funcionalidad a mano, corre `pytest`, prueba casos límite y deja evidencia (captura). | Mergear sin evidencia. |

---

## 4. Flujo de trabajo por historia (Feature Sprint con IA)

1. **Issue**: el Developer crea un issue `HU-0X: <título>` con la historia (Como… quiero… para…) y criterios de aceptación.
2. **Rama**: `feature/hu-0X-descripcion-corta`. Nunca se trabaja directo en `main`.
3. **Analizar antes de pedir**: antes de pedirle código a la IA, leer los archivos afectados y pedirle un análisis/plan primero.
4. **Programar con IA**: pedir cambios pequeños, leer el diff, ejecutar. No pegar código sin entenderlo.
5. **Pruebas**: cada historia lleva pruebas automatizadas nuevas en `backend/tests/` y deben pasar.
6. **Commits identificables**: ver sección 5.
7. **Pull Request** hacia `main` con la plantilla de `.github/pull_request_template.md`, enlazando el issue (`Closes #N`).
8. **Revisión** (Reviewer) y **validación manual** (QA). Solo entonces se hace merge (squash o merge commit, sin borrar el historial de la rama).
9. **AI Log**: el Developer (y quien detecte un error de la IA) lo registra en `docs/AI_LOG.md` el mismo día.

### Reglas para agentes de IA

- Leer este archivo y los archivos afectados antes de editar.
- Cambios mínimos: una historia por vez, sin refactors ni dependencias nuevas que nadie pidió.
- No tocar `.env`, secretos ni la base de datos `*.db`. No ejecutar `git push --force`.
- Toda funcionalidad nueva lleva pruebas; si no puedes ejecutarlas, dilo explícitamente en vez de afirmar que funcionan.
- Mantener el estilo existente (comentarios y mensajes en español, tipado con `from __future__ import annotations`).
- No inventar resultados: si algo falló, reportarlo tal cual.

---

## 5. Convenciones de Git

- **Mensajes de commit** (en español, modo imperativo), con el ID de la historia:
  `HU-02: agrega endpoint de disponibilidad mensual`
- **Autor real**: cada integrante configura su `git config user.name` / `user.email` para que el historial muestre quién hizo qué.
- **Atribución de IA**: si el commit tuvo ayuda sustancial de IA, se deja el trailer
  `Co-Authored-By: <herramienta/modelo> <noreply@...>`. Es **deseable**: es parte de la evidencia de uso de IA que pide el proyecto.
- Un commit = un cambio coherente. Evitar commits gigantes tipo "varios cambios".

---

## 6. Evidencias que debemos poder mostrar (checklist del enunciado)

| # | Evidencia | Dónde queda |
|---|---|---|
| 1 | Repositorio Git | este repo |
| 2 | Issues / historias de usuario | pestaña *Issues* |
| 3 | Commits identificables | historial (`HU-0X: …`) |
| 4 | Uso de ramas | `feature/hu-0X-…` |
| 5 | Pull Request o revisión equivalente | pestaña *Pull requests* |
| 6 | Pruebas automatizadas | `backend/tests/` + captura de `pytest` |
| 7 | Evidencia del uso de IA | `docs/AI_LOG.md` + capturas |
| 8 | Ejemplos de respuestas incorrectas de la IA | `docs/AI_LOG.md` (sección 2) |
| 9 | Cambios que rechazamos de la IA | `docs/AI_LOG.md` (sección 3) |
| 10 | Decisiones tomadas por humanos | `docs/AI_LOG.md` (sección 4) |

Las capturas y el resumen final van en el Word compartido `docs/1GS242_Proyecto1_Evidencias_IA.docx`
(secciones 6 a 9). **Solo se registran las interacciones con IA que afectaron significativamente el desarrollo**, no cada prompt.

### 6.1 Cómo editar el Word (personas y agentes)

El Word está en el repo para que la IA de cada integrante lo tenga a mano. Pero es un archivo binario: **Git no puede
combinar dos ediciones**, así que si dos personas lo cambian a la vez habrá conflicto. Reglas:

1. **Antes de editar:** `git pull` para partir de la última versión. Nunca editar una copia vieja.
2. **Editar solo lo tuyo:** llenar las filas `[Pendiente]` de tus historias (secciones 3 a 9 del Word). No reorganizar ni borrar
   secciones, ni tocar la portada.
3. **Cómo editarlo (agentes):** con python-docx o la skill `docx`, cambiando solo el texto de las celdas y conservando estilos
   y tablas. Después abrir el resultado (o convertirlo a PDF) y verificar que se ve bien antes de hacer commit.
4. **Commit y push inmediatos**, en un commit solo del Word: `Evidencias: HU-0X – <qué se llenó>`.
   Así el siguiente que haga `pull` ya trae tu cambio.
5. **Si hay conflicto** en el `.docx`: no intentar fusionarlo. Quedarse con la versión de `main`
   (`git checkout --theirs docs/1GS242_Proyecto1_Evidencias_IA.docx` o equivalente), volver a aplicar tu cambio encima y hacer commit.
6. **Capturas de pantalla:** guardarlas en `docs/evidencias/` con nombre `HU-0X_descripcion.png` (commit aparte, sin conflicto)
   e insertarlas en el Word en el recuadro `[Insertar captura: …]` que corresponda.
7. **Avisar por el chat del grupo** cuando empiezas y terminas de editar el Word.

> Lo que sí se fusiona bien es `docs/AI_LOG.md` (texto plano). Úsalo como borrador del día a día y pasa el resumen al Word.

---

## 7. Calendario sugerido (entrega 28/10, 6:00 PM)

| Cuándo | Qué |
|---|---|
| Hoy 27/10 | Repo propio creado, issues HU-01..05 y ramas abiertas; cada Developer arranca su historia. |
| 27/10 noche | Primeros PR abiertos; empezar revisión y QA cruzados. |
| 28/10 mañana | Merge de HU-01..03; terminar HU-04/05; completar `docs/AI_LOG.md` y el Word. |
| 28/10 mediodía | Congelar código, preparar la presentación (cualquiera puede ser el presentador, se elige al azar) y ensayar cambios en vivo. |
| 28/10 antes de las 6:00 PM | Subir a Teams el Word + material de la presentación + enlace al repositorio. |
