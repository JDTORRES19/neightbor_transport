## Plan de Implementacion - Fase 2 (Concurrencia y operacion)

Fecha: 2026-06-23
Estado: planificado
Duracion sugerida: 5 a 6 dias

### Objetivo
1. Blindar invariantes de cupos y estados bajo concurrencia real.
2. Completar operacion automatica (scheduler) y notificaciones persistentes.

### Alcance funcional
1. Aceptar/rechazar solicitudes con reglas de capacidad.
2. Evitar sobre-reserva en aceptaciones simultaneas.
3. Finalizacion automatica de viajes vencidos.
4. Notificaciones persistentes y consumo en UI.

### Alcance backend
1. Casos de uso:
   - aceptar solicitud
   - rechazar solicitud
   - finalizar viaje (manual y automatico)
2. Locking transaccional en aceptar solicitud.
3. Error estandar de concurrencia: ERR_CONCURRENT_UPDATE (409).
4. Scheduler de finalizacion cada 1 minuto con idempotencia.
5. Registro de ejecuciones del job y metricas operativas.

### Alcance frontend
1. Gestion de solicitudes por viaje para ofertante.
2. Feedback de concurrencia y conflictos en UI.
3. Centro de notificaciones y marcado de leidas.
4. Toasters unificados conectados a eventos persistentes.

### Entregables
1. Flujo completo de aceptacion sin sobre-reserva.
2. Job estable de finalizacion automatica.
3. Notificaciones funcionales en backend y frontend.
4. Suite de pruebas de concurrencia y scheduler.

### Criterios de salida
1. Cero sobre-reserva en pruebas de carrera repetidas.
2. Viajes vencidos se finalizan en ventana esperada.
3. Frontend refleja estados finales y notificaciones sin incoherencias.
4. Logs y metricas permiten diagnosticar conflictos y reintentos.

### Checklist de ejecucion
1. Implementar bloqueo ordenado viaje -> solicitud -> relacionadas.
2. Agregar manejo de errores concurrentes en API y UI.
3. Implementar scheduler con guardas de idempotencia.
4. Integrar notificaciones persistentes en frontend.
5. Ejecutar test suite de concurrencia, jobs y regresion de flujos.

### Riesgos y mitigaciones
1. Riesgo: deadlocks por orden de locks inconsistente.
   - Mitigacion: unica estrategia de lock documentada y testeada.
2. Riesgo: ruido por notificaciones duplicadas.
   - Mitigacion: claves de idempotencia y deduplicacion por evento.
3. Riesgo: job periodico degradando DB.
   - Mitigacion: ventanas acotadas + indices + metricas de duracion.
