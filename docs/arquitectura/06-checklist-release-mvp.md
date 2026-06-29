## Checklist Release MVP

Checklist operativo para cierre de Fase 6 y salida a MVP controlado.

Fecha de evaluacion formal: 2026-06-29

Decision actual: GO condicionado

Condiciones del GO condicionado:
1. Asignar nombres concretos por rol antes de despliegue productivo.
2. Ejecutar monitoreo reforzado durante ventana inicial post-release.

### 1. Calidad tecnica
1. Backend test suite en verde dentro de contenedor `web`.
2. Frontend build en verde dentro de contenedor `frontend`.
3. Sin errores de tipado/bundle en frontend.
4. Verificacion de endpoints criticos con codigos de error estandar.

### 2. Flujos funcionales
1. Publicar viaje con vehiculo activo y telefono valido.
2. Crear solicitud sobre viaje activo con cupos disponibles.
3. Aceptar solicitud sin sobre-reserva en escenarios concurrentes.
4. Finalizar viaje manual con cierre derivado de solicitudes.
5. Finalizacion automatica por scheduler con idempotencia.

### 3. Observabilidad y operacion
1. Endpoint `/api/v1/metrics/overview` disponible y respondiendo.
2. Panel frontend de observabilidad mostrando:
   - estados de viajes/solicitudes,
   - contador de notificaciones,
   - eventos de auditoria,
   - ultimo run de scheduler,
   - latencia por endpoint.
3. Tabla de ejecuciones de scheduler (`scheduler_job_runs`) con historico.
4. Eventos de auditoria (`audit_events`) para finalizacion manual y automatica.

### 4. Notificaciones y UX
1. Notificaciones persistentes se listan y se pueden marcar como leidas.
2. Toasts en frontend aparecen para notificaciones no leidas.
3. Conteo de no leidas consistente entre backend y frontend.

### 5. Preparacion de salida
1. Roadmap de implementacion actualizado con estado real.
2. Riesgos abiertos identificados y mitigaciones definidas.
3. Plan de rollback documentado para despliegue inicial.
4. Responsables de monitoreo post-release definidos.

### 6. Estado sugerido actual
1. Calidad tecnica: GO.
2. Flujos funcionales: GO.
3. Observabilidad y operacion: GO.
4. Notificaciones y UX: GO.
5. Preparacion de salida: GO condicionado.

### 7. Matriz Go/No-Go
1. `GO`: backend tests 100% verde en contenedor `web`.
2. `GO`: frontend build verde en contenedor `frontend`.
3. `GO`: endpoint `/api/v1/metrics/overview` estable con datos de latencia y scheduler.
4. `GO`: flujos criticos (publicar, solicitar, aceptar, finalizar manual/automatico) validados E2E.
5. `NO-GO`: errores funcionales sin codigo estandar o regresiones de concurrencia.
6. `NO-GO`: fallo sostenido de scheduler o ausencia de auditoria/notificaciones en finalizacion.

### 8. Responsables de salida
1. Backend owner: valida tests, errores estandar y auditoria.
2. Frontend owner: valida build, toasts y panel de observabilidad.
3. QA owner: valida checklist funcional y escenarios de error.
4. Operaciones owner: monitorea scheduler, metricas y rollback.

### 9. Evidencia de cierre
1. Backend suite: `53 passed in 8.13s`.
2. Frontend build: `vite build` exitoso (`100 modules transformed`).
3. Salud runtime: `/health` responde `{"status":"ok","service":"web"}`.
4. Observabilidad: `/api/v1/metrics/overview` retorna contadores, scheduler y `endpoint_latency_ms`.
5. Reporte de performance: `docs/arquitectura/07-reporte-performance-mvp.md`.
6. Plan de rollback: `docs/arquitectura/08-plan-rollback-mvp.md`.
