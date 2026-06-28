## Riesgos Operativos v1

Matriz operativa para el MVP: riesgos, impacto, deteccion, mitigacion y acciones de respuesta.

### Objetivo
1. Definir controles operativos minimos antes de implementacion.
2. Reducir caidas funcionales en flujos criticos (cupos, estados, scheduler, notificaciones).
3. Establecer umbrales iniciales de observabilidad (SLI/SLO) y alertamiento.

### Escala de evaluacion
1. Probabilidad: Baja, Media, Alta.
2. Impacto: Bajo, Medio, Alto, Critico.
3. Prioridad: combinacion de probabilidad e impacto.

### Matriz de riesgos

1. Riesgo: sobre-reserva de cupos por concurrencia.
2. Probabilidad: Media.
3. Impacto: Critico.
4. Deteccion: conflictos concurrentes elevados, cupos negativos, inconsistencias de estado.
5. Mitigacion preventiva: locking transaccional + pruebas de concurrencia + constraints de base de datos.
6. Respuesta: bloquear nuevas aceptaciones temporalmente en viaje afectado, reconciliar estados y auditar.
7. Owner: backend dominio viajes/solicitudes.

1. Riesgo: deadlocks en operaciones criticas.
2. Probabilidad: Media.
3. Impacto: Alto.
4. Deteccion: errores DB de deadlock, latencia alta en endpoints de estado.
5. Mitigacion preventiva: orden estable de locks + reintentos acotados.
6. Respuesta: reintento automatico controlado, log con request_id, analisis de query plan.
7. Owner: backend + datos.

1. Riesgo: scheduler no ejecuta o ejecuta tarde.
2. Probabilidad: Media.
3. Impacto: Alto.
4. Deteccion: jobs sin corrida > 2 intervalos, backlog de viajes vencidos activos.
5. Mitigacion preventiva: healthcheck de scheduler, registro de job_run, alertas de retraso.
6. Respuesta: ejecucion manual de catch-up, revisar error_detail y estado de workers.
7. Owner: plataforma/operaciones.

1. Riesgo: transiciones de estado invalidas por bypass de casos de uso.
2. Probabilidad: Media.
3. Impacto: Alto.
4. Deteccion: auditoria con secuencias imposibles, errores de validacion recurrentes.
5. Mitigacion preventiva: solo casos de uso pueden mutar estado + validacion en backend + pruebas de estados.
6. Respuesta: bloquear endpoint afectado, rollback logico y correccion de flujo.
7. Owner: backend dominio.

1. Riesgo: degradacion de performance en board/listados.
2. Probabilidad: Alta.
3. Impacto: Medio/Alto.
4. Deteccion: p95/p99 altos, queries lentas, timeouts intermitentes.
5. Mitigacion preventiva: query services, paginacion obligatoria, indices orientados a consultas.
6. Respuesta: limitar page_size temporalmente, optimizar queries, revisar planes de ejecucion.
7. Owner: backend + datos.

1. Riesgo: filtracion de datos sensibles (telefono/comentarios).
2. Probabilidad: Baja/Media.
3. Impacto: Critico.
4. Deteccion: revision de payloads, auditoria de accesos no autorizados.
5. Mitigacion preventiva: reglas de visibilidad estrictas, tests de autorizacion, minima exposicion de campos.
6. Respuesta: retirar campo de respuesta, rotar logs sensibles, analisis de incidente.
7. Owner: seguridad + backend.

1. Riesgo: duplicacion de notificaciones por reintentos o idempotencia incompleta.
2. Probabilidad: Media.
3. Impacto: Medio.
4. Deteccion: eventos repetidos por correlation_id.
5. Mitigacion preventiva: llaves de idempotencia y deduplicacion en side effects.
6. Respuesta: limpieza de duplicados y ajuste de dedupe key.
7. Owner: backend comunicaciones.

1. Riesgo: inconsistencias entre auditoria y estado real.
2. Probabilidad: Baja/Media.
3. Impacto: Alto.
4. Deteccion: auditoria sin correlacion o saltos de estado no explicados.
5. Mitigacion preventiva: persistencia de auditoria dentro de la misma transaccion.
6. Respuesta: conciliacion operativa por script y analisis de pipeline transaccional.
7. Owner: backend + datos.

### SLI/SLO iniciales (MVP)

1. Endpoint disponibilidad API (SLI): porcentaje de respuestas 2xx/4xx sobre total.
2. SLO sugerido: >= 99.5% diario.

1. Latencia endpoint critico aceptar solicitud (SLI): p95 de /requests/{id}/accept.
2. SLO sugerido: p95 <= 500 ms en carga normal.

1. Integridad de cupos (SLI): numero de viajes con available_seats < 0.
2. SLO sugerido: 0 absoluto.

1. Concurrencia controlada (SLI): ratio de ERR_CONCURRENT_UPDATE sobre total de aceptaciones.
2. SLO sugerido: <= 3% (umbral de alerta si supera 5% sostenido).

1. Scheduler puntualidad (SLI): diferencia entre hora esperada y hora real de ejecucion.
2. SLO sugerido: 95% de corridas dentro de +60s del intervalo.

1. Scheduler efectividad (SLI): viajes vencidos finalizados en <= 2 minutos.
2. SLO sugerido: >= 99%.

1. Notificaciones consistentes (SLI): eventos obligatorios con notificacion persistida.
2. SLO sugerido: >= 99.9%.

### Alertas operativas minimas

1. ALERT_CONCURRENCY_SPIKE
2. Condicion: ERR_CONCURRENT_UPDATE > 5% por 10 minutos.
3. Severidad: Media.
4. Accion: revisar lock contention y tiempos de transaccion.

1. ALERT_SCHEDULER_STALE
2. Condicion: sin ejecucion exitosa del scheduler en 2 intervalos.
3. Severidad: Alta.
4. Accion: ejecutar job manual y revisar estado de worker.

1. ALERT_NEGATIVE_SEATS
2. Condicion: available_seats < 0 en cualquier viaje.
3. Severidad: Critica.
4. Accion: congelar aceptaciones y ejecutar reconciliacion inmediata.

1. ALERT_API_LATENCY_CRITICAL
2. Condicion: p95 > 1000 ms en endpoints criticos por 10 minutos.
3. Severidad: Alta.
4. Accion: activar modo degradado (page_size reducido) y perf triage.

1. ALERT_NOTIFICATION_GAP
2. Condicion: diferencia entre eventos de dominio y notificaciones > 0.5% por 15 minutos.
3. Severidad: Media.
4. Accion: re-procesar eventos faltantes y revisar pipeline de side effects.

### Playbooks minimos de respuesta

1. Playbook concurrencia (aceptaciones)
2. Validar salud DB y locks activos.
3. Correlacionar request_id y correlation_id en logs/auditoria.
4. Confirmar integridad de cupos por viaje afectado.
5. Ejecutar reconciliacion por script si hay desalineacion.

1. Playbook scheduler
2. Verificar ultimo job_run y error_detail.
3. Ejecutar corrida manual de finalizacion.
4. Confirmar transiciones pendientes/aceptadas esperadas.
5. Rehabilitar ciclo normal y monitorear 30 minutos.

1. Playbook fuga de datos
2. Identificar endpoint/campo expuesto.
3. Aplicar hotfix de ocultamiento.
4. Invalidar caches/payloads persistidos si aplica.
5. Registrar incidente y acciones correctivas.

### Criterios de readiness operativa (antes de release)
1. Dashboards basicos de latencia, errores, scheduler y concurrencia disponibles.
2. Alertas criticas configuradas y probadas.
3. Playbooks validados con simulacion de incidente.
4. Reconciliacion de cupos documentada y testeada.
5. Auditoria y notificaciones correlacionables por request_id/correlation_id.

### Backlog de madurez post-MVP
1. Definir SLO por endpoint y presupuesto de errores semanal.
2. Automatizar reconciliacion proactiva de cupos.
3. Incorporar alertas de saturacion de pool de conexiones.
4. Endurecer politicas de privacidad y data retention.
5. Ejercicios periodicos de game day para scheduler y concurrencia.
