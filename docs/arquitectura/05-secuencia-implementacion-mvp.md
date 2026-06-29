## Secuencia de Implementacion MVP v1

Roadmap de implementacion por etapas, orientado a reducir riesgo tecnico y entregar valor incremental sin romper reglas de dominio.

### Objetivo
1. Implementar el MVP en fases cortas con criterios de salida verificables.
2. Priorizar primero consistencia de dominio (estados, cupos, reglas de unicidad) y luego experiencia completa.

### Estado de avance (actualizado 2026-06-29)
1. Fases completadas: Fase 0, Fase 1, Fase 2, Fase 3, Fase 4 y Fase 5.
2. Avance de hardening: refactor de arquitectura aplicado (constantes, utils, services y routers por dominio).
3. Fase 4 completada: locking en aceptacion de solicitudes con manejo de conflicto concurrente (409 + ERR_CONCURRENT_UPDATE).
4. Fase 5 completada: scheduler de finalizacion automatica, cierre de solicitudes por finalizacion, notificaciones persistentes y toasts en frontend.
5. Fase 6 iniciada: endpoint de metricas operativas + panel frontend de observabilidad + prueba E2E integral de flujo clave.
6. Frontend: flujo de solicitudes desde board y actualizaciones optimistas de estado/cupos implementadas.
7. Calidad actual:
   - backend test suite en verde (53 pruebas).
   - frontend build en verde.

### Resumen ejecutivo por fase
1. Fase 0: completada.
   - Envelope estandar, request_id y manejo global de excepciones operativos.
2. Fase 1: completada.
   - Perfil y vehiculos con reglas de validacion y ownership cubiertas.
3. Fase 2: completada.
   - Publicacion/listado/cancelacion/finalizacion de viajes con restriccion de viaje activo unica.
4. Fase 3: completada.
   - Flujo completo de solicitudes y reglas de cupos/estados, incluida cancelacion automatica de pendientes al aceptar.
5. Fase 4: completada.
   - locking en aceptar solicitud implementado.
   - comportamiento de reintento validado (double-accept: 200 en primer intento, 409 ERR_REQUEST_NOT_PENDING en segundo intento).
   - competencia de ultimo cupo entre solicitantes distintos validada sin sobre-reserva.
   - aceptaciones casi simultaneas (dos hilos) validadas: 1 aceptada + 1 conflicto, sin sobre-reserva.
   - escenarios con latencia inducida en transaccion validados (mismo request y requesters competidores) sin sobre-reserva.
6. Fase 5: completada.
   - scheduler de finalizacion automatica e idempotencia basica implementados.
   - cierre automatico/manual de solicitudes por finalizacion de viaje implementado (pendiente -> cancelada_por_finalizacion, aceptada -> finalizada).
   - notificaciones persistentes base implementadas (listar, marcar leida, marcar todas leidas).
   - auditoria de negocio implementada para finalizacion manual y automatica.
   - handoff de toasts en frontend implementado sobre notificaciones no leidas.
7. Fase 6: en progreso.
   - E2E de flujo clave implementado y extendido con escenarios de error/transiciones invalidas.
   - dashboard basico de metricas operativas implementado (backend + frontend).
   - metricas de latencia por endpoint implementadas en `/metrics/overview` con ventana temporal configurable.
   - checklist de release MVP creado en `docs/arquitectura/06-checklist-release-mvp.md`.
   - matriz Go/No-Go y responsables operativos documentados en checklist.
   - cierre formal del checklist realizado con decision GO condicionado.
   - reporte de performance MVP documentado en `docs/arquitectura/07-reporte-performance-mvp.md`.
   - plan de rollback documentado en `docs/arquitectura/08-plan-rollback-mvp.md`.

### Siguiente bloque de ejecucion recomendado
1. Asignar responsables nominales (persona/equipo) por cada rol operativo del checklist.
2. Ejecutar salida MVP controlada con monitoreo reforzado post-release.
3. Re-evaluar decision final GO/NO-GO tras ventana inicial de observacion.

### Supuestos de entrada
1. Contratos funcionales v5 cerrados.
2. Modelo de datos fisico v1 aprobado.
3. API contratos v1 y lineamientos de implementacion vigentes.

### Fase 0: Base de arquitectura y calidad
Duracion sugerida: 2 a 3 dias.

1. Alcance:
   - Estructura de capas y paquetes por contexto.
   - Handler global de excepciones y catalogo de errores.
   - Envelope estandar de respuestas.
   - Base de auditoria y notificaciones.
2. Entregables:
   - esqueleto de modulos por contexto.
   - modulo de errores estandar.
   - pruebas base de contract envelope.
3. Criterio de salida:
   - un endpoint de prueba responde con envelope estandar en exito y error.
   - request_id trazable en logs de error.

### Fase 1: Identidad, perfil y vehiculos
Duracion sugerida: 3 a 4 dias.

1. Alcance:
   - perfil con telefono obligatorio y pais por defecto CO (+57).
   - CRUD de vehiculos (con desactivacion logica).
   - validaciones de ownership y formato de telefono.
2. Entregables:
   - endpoints /me y /vehicles.
   - normalizacion phone_e164.
3. Criterio de salida:
   - no se puede publicar viaje sin telefono valido ni vehiculo activo.
   - pruebas de autorizacion y ownership en vehiculos pasan.

### Fase 2: Viajes (publicar, listar, cancelar, finalizar)
Duracion sugerida: 4 a 5 dias.

1. Alcance:
   - publicar viaje.
   - board de viajes por trayecto con paginacion.
   - viaje activo/lleno/cancelado/finalizado.
   - cancelar y finalizar manual.
2. Entregables:
   - endpoints /trips, /trips/mine/active, /trips/{id}/cancel, /trips/{id}/finalize.
   - restricciones de unicidad de viaje activo por ofertante.
3. Criterio de salida:
   - no existe mas de un viaje activo o lleno por ofertante.
   - cambios de estado auditados correctamente.

### Fase 3: Solicitudes y flujo de cupos
Duracion sugerida: 5 a 6 dias.

1. Alcance:
   - crear solicitud.
   - aceptar/rechazar/cancelar solicitud.
   - cancelacion automatica de otras pendientes del solicitante al aceptar una.
   - visibilidad de WhatsApp solo en aceptadas.
2. Entregables:
   - endpoints /trips/{id}/requests, /requests/{id}/accept, /requests/{id}/reject, /requests/{id}/cancel, /requests/mine.
   - reglas de cupos y estados integradas.
3. Criterio de salida:
   - solicitante no puede tener mas de una aceptada activa.
   - viaje pasa a lleno cuando cupos llegan a 0 y vuelve a activo al liberar cupo.

### Fase 4: Concurrencia y locking (hardening)
Duracion sugerida: 3 a 4 dias.

1. Alcance:
   - transaccion con locking en aceptar solicitud.
   - manejo de conflictos concurrentes (409 + ERR_CONCURRENT_UPDATE).
   - pruebas de carrera sobre cupos.
2. Entregables:
   - implementacion de estrategia de locking definida.
   - suite de pruebas de concurrencia.
3. Criterio de salida:
   - cero sobre-reserva en escenarios de aceptacion simultanea.

### Fase 5: Scheduler, notificaciones y cierre operativo
Duracion sugerida: 3 a 4 dias.

1. Alcance:
   - job cada minuto para finalizar viajes vencidos.
   - transiciones derivadas: pendientes -> cancelada_por_finalizacion, aceptadas -> finalizada.
   - notificaciones persistentes + consumo de toast.
2. Entregables:
   - job de finalizacion automatica + tabla de ejecuciones.
   - endpoints de notificaciones y marcado de lectura.
3. Criterio de salida:
   - viaje vencido se finaliza automaticamente con idempotencia.
   - eventos de notificacion se generan por cada accion definida.

### Fase 6: End-to-end, observabilidad y release MVP
Duracion sugerida: 2 a 3 dias.

1. Alcance:
   - pruebas E2E de flujo completo ofertante/solicitante.
   - dashboard basico de metricas operativas.
   - hardening de logs y auditoria.
2. Entregables:
   - checklist de aceptacion completo en verde.
   - reporte de performance en endpoints criticos.
3. Criterio de salida:
   - flujos clave completos y estables.
   - criterios funcionales y tecnicos del MVP cumplidos.

### Dependencias y orden recomendado
1. Fase 0 antes de cualquier endpoint de negocio.
2. Fase 1 antes de publicar viajes.
3. Fase 2 antes de solicitudes.
4. Fase 4 puede arrancar en paralelo parcial con Fase 3, pero debe cerrarse antes de release.
5. Fase 5 depende de estados y transiciones ya estables.

### Riesgos clave y mitigacion
1. Riesgo: sobre-reserva por carrera de aceptaciones.
   - Mitigacion: locking + pruebas de concurrencia desde Fase 4.
2. Riesgo: regresiones por cambios de estado.
   - Mitigacion: pruebas de transicion por estado y auditoria obligatoria.
3. Riesgo: endpoints pesados en board.
   - Mitigacion: query services + indices + paginacion obligatoria.
4. Riesgo: deuda de versionado API.
   - Mitigacion: mantener contratos v1 congelados y cambios breaking en v2.

### Definition of Done (DoD) transversal
1. Cumple contrato API y codigos de error estandar.
2. Incluye pruebas unitarias/integracion del caso.
3. Incluye auditoria y notificacion si la accion lo exige.
4. No introduce N+1 en listados.
5. Documentacion de arquitectura y contrato actualizada.
