## ADR: Decisiones Clave v1

Registro corto de decisiones arquitectonicas que orientan implementacion y reducen ambiguedad.

Formato:
1. ID
2. Titulo
3. Estado
4. Contexto
5. Decision
6. Consecuencias

### ADR-001: Estados y transiciones como fuente de verdad
1. ID: ADR-001
2. Titulo: Maquina de estados obligatoria para viaje y solicitud.
3. Estado: Aceptada.
4. Contexto: alto riesgo de inconsistencias cuando los estados se cambian desde multiples puntos.
5. Decision:
   - transiciones solo por casos de uso autorizados.
   - estados oficiales: viaje (activo, lleno, cancelado, finalizado), solicitud (pendiente, aceptada, rechazada, cancelada_por_*, finalizada).
6. Consecuencias:
   - mayor control y trazabilidad.
   - requiere pruebas de transicion y auditoria estricta.

### ADR-002: Concurrencia fuerte para aceptacion de solicitudes
1. ID: ADR-002
2. Titulo: Locking transaccional para evitar sobre-reserva.
3. Estado: Aceptada.
4. Contexto: aceptar solicitudes en paralelo puede generar cupos negativos.
5. Decision:
   - transaccion ACID con lock ordenado: viaje -> solicitud -> relacionadas.
   - conflictos concurrentes responden 409 ERR_CONCURRENT_UPDATE.
6. Consecuencias:
   - elimina sobre-reserva.
   - puede aumentar latencia bajo alta contencion.

### ADR-003: Versionamiento de API por carpetas y ruta
1. ID: ADR-003
2. Titulo: Versionado por /api/v{n} y estructura por version.
3. Estado: Aceptada.
4. Contexto: cambios futuros pueden romper compatibilidad.
5. Decision:
   - estructura por carpetas versionadas.
   - cambios breaking en nueva version (v2) manteniendo soporte de v1 por ventana definida.
6. Consecuencias:
   - evolucion controlada.
   - costo de mantener multiples versiones temporalmente.

### ADR-004: Endpoints delgados y logica en casos de uso
1. ID: ADR-004
2. Titulo: Separacion estricta de responsabilidades.
3. Estado: Aceptada.
4. Contexto: mezclar negocio en endpoints degrada mantenibilidad y testabilidad.
5. Decision:
   - endpoints solo parsean/validan/delegan/serializan.
   - logica de negocio en casos de uso y servicios de aplicacion.
   - lecturas complejas en query services.
6. Consecuencias:
   - codigo mas modular y testeable.
   - requiere disciplina de arquitectura.

### ADR-005: Estandar unificado de errores y respuestas
1. ID: ADR-005
2. Titulo: Envelope estandar y catalogo central de errores.
3. Estado: Aceptada.
4. Contexto: respuestas heterogeneas complican frontend y monitoreo.
5. Decision:
   - envelope unico ok/data y ok/error.
   - base domain exception + handler global.
   - request_id obligatorio en errores.
6. Consecuencias:
   - integracion frontend estable.
   - menor ambiguedad en soporte.

### ADR-006: Scheduler de finalizacion automatica
1. ID: ADR-006
2. Titulo: Job periodico cada minuto para cierre de viajes.
3. Estado: Aceptada.
4. Contexto: viajes vencidos deben cerrarse aun sin accion manual del ofertante.
5. Decision:
   - scheduler cada 1 minuto.
   - si salida + 20 min vencida: viaje -> finalizado.
   - pendientes -> cancelada_por_finalizacion; aceptadas -> finalizada.
6. Consecuencias:
   - coherencia temporal del sistema.
   - requiere observabilidad y alertas operativas.

### ADR-007: Privacidad de contacto y comentarios
1. ID: ADR-007
2. Titulo: Minima exposicion de datos sensibles.
3. Estado: Aceptada.
4. Contexto: riesgo de fuga de informacion personal.
5. Decision:
   - WhatsApp visible solo con solicitud aceptada.
   - comentarios visibles solo entre solicitante y ofertante.
6. Consecuencias:
   - menor riesgo de privacidad.
   - validaciones de autorizacion mas estrictas.

### ADR-008: Persistencia de notificaciones + toast
1. ID: ADR-008
2. Titulo: Notificacion dual (persistente y UI toast).
3. Estado: Aceptada.
4. Contexto: eventos pueden perderse si solo se usa feedback efimero.
5. Decision:
   - toda notificacion de negocio se persiste.
   - UI consume y muestra toast desde eventos no leidos.
6. Consecuencias:
   - mejor trazabilidad para usuario.
   - costo adicional de almacenamiento y limpieza.

### ADR-009: Telefono obligatorio y normalizacion internacional
1. ID: ADR-009
2. Titulo: Contactabilidad estandar para WhatsApp.
3. Estado: Aceptada.
4. Contexto: sin telefono valido no hay continuidad del flujo de contacto.
5. Decision:
   - telefono obligatorio en perfil.
   - pais por defecto CO y prefijo +57.
   - almacenamiento normalizado en E.164.
6. Consecuencias:
   - menos errores de enlace.
   - validaciones adicionales en perfil.

### ADR-010: Una oferta activa por ofertante y una aceptada por solicitante
1. ID: ADR-010
2. Titulo: Restricciones operativas de simplicidad MVP.
3. Estado: Aceptada.
4. Contexto: reducir complejidad y conflictos de asignacion de cupos.
5. Decision:
   - ofertante: maximo una oferta activa/llena.
   - solicitante: maximo una solicitud aceptada activa.
6. Consecuencias:
   - menor complejidad operativa.
   - puede limitar flexibilidad en escenarios avanzados.

### ADRs pendientes (para siguiente iteracion)
1. ADR-P01: Estrategia de autenticacion (sesion vs token).
2. ADR-P02: Estrategia de paginacion (offset-limit vs cursor).
3. ADR-P03: Politica de retencion y archivado de auditoria/notificaciones.
4. ADR-P04: Politica de deprecacion y ventana de soporte por version API.

### Regla de mantenimiento de ADR
1. Cualquier cambio breaking en contrato, estados o modelo de datos exige actualizar ADR afectado.
2. Cada ADR debe registrar fecha de decision y responsable al pasar a implementacion.
