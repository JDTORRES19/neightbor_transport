## Plan Rollback MVP

Plan operativo para revertir cambios de release MVP de forma segura.

### 1. Disparadores de rollback
1. Errores funcionales criticos en flujos `publicar -> solicitar -> aceptar -> finalizar`.
2. Regresion de concurrencia (sobre-reserva o conflictos no controlados).
3. Fallo sostenido del scheduler o auditoria/notificaciones incompletas.
4. Degradacion severa de latencia en endpoints criticos.

### 2. Estrategia de rollback
1. Congelar trafico de escritura temporalmente (modo mantenimiento parcial o bloqueo UI).
2. Revertir version de backend al release previo estable.
3. Revertir version de frontend al build previo estable.
4. Validar healthchecks y endpoints criticos antes de reabrir trafico.

### 3. Pasos operativos sugeridos
1. Confirmar incidente y abrir canal de guerra (Backend + Frontend + QA + Operaciones).
2. Ejecutar rollback de backend (imagen/tag previo).
3. Ejecutar rollback de frontend (artefacto/tag previo).
4. Verificar:
   - `/health`
   - `/api/v1/trips`
   - `/api/v1/requests/mine`
   - `/api/v1/metrics/overview`
5. Ejecutar smoke tests minimos post-rollback.
6. Comunicar cierre de incidente y estado de servicio.

### 4. Datos y consistencia
1. No ejecutar borrados masivos durante rollback.
2. Mantener `scheduler_job_runs`, `audit_events` y `notifications` para trazabilidad.
3. Si hubo operaciones parcialmente procesadas, registrar compensaciones en auditoria.

### 5. Criterios de salida del rollback
1. Endpoints criticos responden con codigos esperados.
2. Scheduler estable y sin errores recurrentes.
3. Sin nuevos incidentes funcionales durante ventana de observacion.
