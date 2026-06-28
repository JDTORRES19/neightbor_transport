## Concurrencia y Locking v1

Estrategia de control de concurrencia para evitar sobre-reserva de cupos y garantizar consistencia de estados bajo operaciones simultaneas.

### Objetivo
1. Evitar sobre-reserva de cupos en aceptaciones concurrentes.
2. Evitar transiciones inconsistentes por acciones simultaneas (aceptar vs cancelar/finalizar).
3. Definir patrones de lock, reintento e idempotencia.

### Operaciones criticas con concurrencia
1. Aceptar solicitud.
2. Cancelar viaje.
3. Finalizar viaje manual.
4. Finalizar viaje automatico (scheduler).
5. Cancelar solicitud aceptada (libera cupo).

### Invariantes protegidos
1. available_seats nunca negativo.
2. Una oferta activa o llena por ofertante.
3. Una solicitud aceptada activa por solicitante.
4. Transiciones de estado solo por casos de uso autorizados.

### Politica de transacciones
1. Toda operacion critica se ejecuta en transaccion ACID.
2. Las validaciones de invariante se hacen dentro de la misma transaccion.
3. No separar validacion y escritura en transacciones distintas.

### Orden de locking (regla anti-deadlock)
1. Bloquear primero trip_offer por id.
2. Luego bloquear ride_request objetivo por id (si aplica).
3. Luego bloquear solicitudes relacionadas del rider (cuando se requiere cancelar pendientes por otra aceptacion).
4. Mantener orden estable en todas las rutas de negocio.

### Aceptar solicitud (protocolo detallado)
1. Iniciar transaccion.
2. Lock trip_offer FOR UPDATE.
3. Lock ride_request objetivo FOR UPDATE.
4. Validar estado de viaje en activo.
5. Validar estado de solicitud en pendiente.
6. Recalcular cupos disponibles en tiempo real desde solicitudes aceptadas.
7. Validar cupos disponibles >= seats_requested.
8. Validar que rider no tenga otra solicitud aceptada activa.
9. Cambiar solicitud a aceptada.
10. Cancelar otras solicitudes pendientes del mismo rider (cancelada_por_otra_aceptacion).
11. Recalcular estado del viaje (activo o lleno).
12. Persistir auditoria y notificaciones derivadas.
13. Commit.
14. Si cualquier validacion falla: rollback + error de dominio.

### Colisiones entre acciones concurrentes
1. aceptar_solicitud vs cancelar_viaje:
   - gana quien obtenga lock primero.
   - segunda operacion revalida estado y falla con ERR_TRIP_NOT_ACTIVE o ERR_INVALID_STATE_TRANSITION.
2. aceptar_solicitud vs finalizar_viaje:
   - mismo criterio de lock.
   - segunda operacion revalida y responde conflicto.
3. aceptar_solicitud A vs aceptar_solicitud B sobre mismo viaje:
   - serializadas por lock del viaje.
   - una puede aceptar; la otra puede fallar con ERR_TRIP_FULL o ERR_CONCURRENT_UPDATE segun estado resultante.

### Estrategia de idempotencia
1. Operaciones de cambio de estado aceptan Idempotency-Key.
2. Si llega el mismo request_idempotency repetido:
   - devolver resultado previo sin repetir side effects.
3. Side effects idempotentes:
   - notificaciones no duplicadas.
   - auditoria con correlation_id para deteccion de duplicados.

### Politica de reintentos
1. Reintentos automaticos solo para errores tecnicos transitorios de BD (deadlock serialization failure).
2. Maximo recomendado: 2 reintentos con backoff corto.
3. Errores de dominio (ERR_TRIP_FULL, ERR_REQUEST_NOT_PENDING, etc.) no se reintentan.

### Niveles de aislamiento (lineamiento)
1. Uso base: READ COMMITTED con locks explicitos FOR UPDATE en rutas criticas.
2. Escalar a SERIALIZABLE solo si la combinacion de reglas lo exige y el costo es aceptable.

### Scheduler y locking
1. Job de finalizacion toma lock por viaje antes de transicionar estados.
2. Procesamiento por lote, pero commit por viaje (unidad atomica).
3. Si viaje ya fue finalizado/cancelado durante ejecucion, saltar (idempotencia).

### Manejo de errores concurrentes
1. Mapear conflictos de carrera a HTTP 409 con ERR_CONCURRENT_UPDATE.
2. Mensaje UX recomendado: "La informacion cambio mientras realizabas la accion. Actualiza e intenta de nuevo."
3. Incluir request_id para trazabilidad.

### Observabilidad especifica de concurrencia
1. Medir tasa de conflictos concurrentes por endpoint.
2. Medir tiempo de espera de lock en operaciones criticas.
3. Medir reintentos de transaccion por tipo de error.
4. Correlacionar auditoria con request_id/correlation_id.

### Pruebas de concurrencia (minimas obligatorias)
1. Dos aceptaciones simultaneas que exceden cupos:
   - resultado esperado: una acepta, otra falla; nunca cupos negativos.
2. Aceptar solicitud mientras viaje se cancela:
   - resultado esperado: una operacion gana; estado final consistente.
3. Aceptar solicitud mientras viaje finaliza:
   - resultado esperado: no queda solicitud aceptada en viaje finalizado fuera de reglas.
4. Doble submit con misma Idempotency-Key:
   - resultado esperado: un solo efecto persistente.

### Checklist de salida de este componente
1. No sobre-reserva validada por pruebas automatizadas.
2. No deadlocks recurrentes en carga moderada.
3. Conflictos concurrentes reportados con codigo estandar.
4. Side effects idempotentes y trazables.
5. Scheduler coexistiendo sin corromper estados.
