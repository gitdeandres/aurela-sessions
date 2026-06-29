# Aurela — Sistema de gestión de sesiones

API REST para la reserva y gestión de sesiones terapéuticas entre pacientes y terapeutas. Prueba técnica para Aurela.

**Stack:** Python 3.12 · Django · Django REST Framework · PostgreSQL · Docker · UV

---

## Índice

1. [Arranque rápido](#arranque-rápido)
2. [Endpoints](#endpoints)
3. [Decisiones de diseño](#decisiones-de-diseño)
4. [Casos límite](#casos-límite)
5. [Tests](#tests)
6. [Mejoras futuras](#mejoras-futuras)

---

## Arranque rápido

**Requisitos:** Docker y Docker Compose.

```bash
git clone https://github.com/gitdeandres/aurela-sessions.git
cd aurela-sessions
cp .env.example .env
docker compose up --build
```

La API queda disponible en `http://localhost:8000/api/`.

Las migraciones se aplican automáticamente al levantar el contenedor.

### Comandos útiles

El contenedor incluye aliases para los comandos más frecuentes:

```bash
docker compose exec web bash

djtest                        # correr todos los tests
djtest app/booking/tests/test_book_session.py -v  # tests específicos
djshell                       # shell interactivo de Django
djmigrate                     # aplicar migraciones
djmakemigrations booking      # crear migraciones
```

### Crear datos de prueba

Al levantar el contenedor en desarrollo, el comando `seed` se ejecuta 
automáticamente y crea terapeutas y pacientes de ejemplo:

```bash
docker compose up
```

Si quieres ejecutarlo manualmente:

```bash
docker compose exec web djmanage seed
```

El comando es idempotente — puedes ejecutarlo múltiples veces sin duplicar datos.

---

## Endpoints

### Reservar sesión
```
POST /api/sessions/
```
```json
{
    "therapist_id": 1,
    "patient_id": 1,
    "start_time": "2026-07-10T10:00:00Z",
    "duration_minutes": 60
}
```

### Cancelar sesión
```
POST /api/sessions/{id}/cancel/
```
```json
{
    "cancelled_by": "patient",
    "cancellation_type": "standard",
    "reason": "Conflicto de agenda"
}
```

Cancelación de emergencia (sin restricción de anticipación):
```json
{
    "cancelled_by": "patient",
    "cancellation_type": "emergency",
    "reason": "mental_health_crisis"
}
```

Motivos de emergencia reconocidos: `mental_health_crisis`, `medical_emergency`, `force_majeure`, `bereavement`.

### Sesiones futuras de un terapeuta
```
GET /api/therapists/{id}/sessions/
```

---

## Decisiones de diseño

### Una sola app: `booking`

Se optó por una única app en lugar de separar en `therapist`, `patient` y `session` porque las tres entidades son inseparables dentro del dominio de reservas — `Session` no existe sin `Therapist` y `Patient`. Separarlas hubiera generado imports cruzados desde el primer día sin ningún beneficio real de modularidad. Si el proyecto creciera con módulos independientes (facturación, mensajería), ahí tendría sentido añadir apps separadas.

### Ciclo de vida de la sesión

Se modelaron cinco estados en lugar de los dos obvios (activa/cancelada) porque reflejan mejor la realidad clínica:

| Estado | Descripción |
|--------|-------------|
| `pending` | Reservada, pendiente de pago |
| `confirmed` | Pago recibido, sesión confirmada |
| `completed` | Sesión realizada |
| `cancelled` | Cancelada por cualquier actor |
| `no_show` | El paciente no se presentó |

Los estados `completed`, `cancelled` y `no_show` son terminales — no admiten más transiciones. La transición `pending → confirmed` está modelada pero no expuesta como endpoint, ya que en producción ocurriría como respuesta al webhook de Stripe al confirmar el pago.

### Política de cancelaciones

Las reglas de cancelación están diseñadas en dos niveles:

**Por estado:** solo `pending` y `confirmed` son cancelables. Los estados terminales no admiten cancelación.

**Por anticipación y actor:** diferenciado según quién cancela:
- Paciente: mínimo 24h de antelación para cancelaciones estándar.
- Terapeuta: mínimo 48h — una cancelación tardía del terapeuta tiene mayor impacto en el paciente, que ya organizó su agenda.
- Sesiones `pending`: sin restricción de anticipación, ya que no hay pago procesado.

**Cancelaciones de emergencia:** se añadió un tipo de cancelación `emergency` que omite los requisitos de anticipación cuando el motivo es reconocido (`mental_health_crisis`, `medical_emergency`, `force_majeure`, `bereavement`). La razón es que un sistema de salud mental que bloquea la cancelación a un paciente en crisis es un riesgo clínico, no solo una mala experiencia de usuario.

El campo `cancelled_by` se persiste en BD porque el historial de cancelaciones por actor es información de negocio valiosa: permite detectar terapeutas con alta tasa de cancelación tardía o pacientes con patrones de no-presentación.

### Detección de conflictos de agenda

La detección usa la condición de solapamiento de intervalos estándar:

```
existing.start_time < new.end_time AND existing.end_time > new.start_time
```

`end_time` se calcula dinámicamente con `ExpressionWrapper` y `F()` en lugar de persistirse como campo en BD, evitando el riesgo de inconsistencia entre `start_time`, `duration_minutes` y `end_time`. El trade-off es que cada consulta de conflicto requiere el cálculo — aceptable para el volumen actual.

### Concurrencia

La reserva usa `select_for_update()` dentro de una transacción atómica para resolver la race condition explícitamente mencionada en el enunciado: dos pacientes intentando reservar el mismo hueco simultáneamente. El lock a nivel de fila garantiza que la segunda transacción espera a que la primera complete antes de verificar disponibilidad.

### Capa de servicios

La lógica de negocio vive en `services.py` en lugar de en las vistas o en los modelos. Los modelos contienen el comportamiento de instancia (`is_cancellable`, `cancel`) y los servicios orquestan las operaciones que involucran múltiples entidades, transacciones y reglas de negocio. Las vistas se limitan a validar entrada y devolver respuesta. Esta separación hace cada capa testeable de forma independiente.

### Gestor de paquetes: UV

Usé [UV de Astral](https://docs.astral.sh/uv/) en lugar de pip. El `uv.lock` garantiza reproducibilidad exacta del entorno — `--frozen` en el Dockerfile asegura que el build usa exactamente las versiones del lockfile sin resolución adicional.

---

## Casos límite

### Cubiertos con tests

| Caso | Test |
|------|------|
| Solapamiento exacto (mismo horario) | `test_book_session_conflict_exact_overlap` |
| Solapamiento parcial (sesión dentro de otra) | `test_book_session_conflict_partial_overlap` |
| Sesiones adyacentes sin solapamiento | `test_book_session_no_conflict_adjacent` |
| Conflicto limitado al terapeuta | `test_book_session_conflict_only_for_same_therapist` |
| Cancelación de sesión ya iniciada | `test_cancel_session_already_started_fails` |
| Cancelación de estado terminal | `test_cancel_completed_session_fails` |
| Doble cancelación | `test_cancel_already_cancelled_session_fails` |
| Emergencia con motivo inválido | `test_cancel_emergency_with_invalid_reason_fails` |
| Sesiones pasadas excluidas de agenda | `test_upcoming_sessions_excludes_past_sessions` |
| Agenda limitada al terapeuta | `test_upcoming_sessions_scoped_to_therapist` |

### Identificados pero no cubiertos con tests

**Concurrencia:** La race condition está resuelta con `select_for_update()` dentro de una transacción atómica. El test verifica que el mecanismo de detección de conflictos funciona correctamente — dos bookings secuenciales sobre el mismo hueco, donde el segundo debe fallar. Simular concurrencia verdadera requeriría requests HTTP paralelos contra un servidor activo.

**Sesión que termina después de medianoche:** si una sesión empieza a las 23:30 y dura 90 minutos, `end_time` cruza a la madrugada del día siguiente. La lógica de intervalos lo maneja correctamente, pero no hay test explícito para este caso.

---

## Tests

```bash
# Todos los tests
docker compose exec web djtest

# Con detalle por test
docker compose exec web djtest -v

# Un archivo específico
docker compose exec web djtest app/booking/tests/test_book_session.py -v
```

**27 tests · 4 archivos · ~1s**

| Archivo | Tests | Qué cubre |
|---------|-------|-----------|
| `test_book_session.py` | 8 | Reserva, conflictos, validación de entrada |
| `test_cancel_session.py` | 10 | Cancelaciones estándar, emergencia, estados terminales |
| `test_upcoming_sessions.py` | 8 | Filtros de estado, temporales, orden y scope |
| `test_concurrency.py` | 1 | Mecanismo de prevención de doble reserva simultánea |

Los tests usan PostgreSQL (misma BD que desarrollo, prefijada con `test_`) para garantizar compatibilidad con las queries que usan `ExpressionWrapper` y `select_for_update()`, que no son soportadas por SQLite.

---

## Mejoras futuras

**Endpoint de confirmación de sesión** (`POST /api/sessions/{id}/confirm/`): la transición `pending → confirmed` está modelada pero no expuesta. En producción ocurriría como respuesta al webhook de Stripe al procesar el pago — el diseño actual lo soporta sin cambios en los modelos.

**Notificaciones asíncronas:** las cancelaciones y confirmaciones deberían notificar al otro actor por email. Implementación natural con Celery + Redis sin cambios en los modelos — el servicio simplemente encolaría la tarea tras el `session.cancel()`.
