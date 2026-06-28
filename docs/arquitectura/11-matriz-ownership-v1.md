## Matriz de Ownership v1

Asignacion de responsables por componente para operacion, evolucion y respuesta a incidentes.

### Objetivo
1. Evitar zonas grises de responsabilidad.
2. Asegurar que cada componente tenga owner principal y backup.
3. Facilitar escalamiento en incidentes y decisiones de cambio.

### Roles de referencia
1. Arquitectura.
2. Backend.
3. Frontend.
4. Datos.
5. Operaciones/Plataforma.
6. QA.
7. Producto/PM.

### Matriz por componente

1. Dominio viajes y solicitudes
2. Owner primario: Backend.
3. Backup owner: Arquitectura.
4. Responsabilidades:
   - invariantes de negocio.
   - transiciones de estado.
   - casos de uso criticos.

1. API contratos y versionado
2. Owner primario: Arquitectura API.
3. Backup owner: Backend.
4. Responsabilidades:
   - contratos v1/v2.
   - compatibilidad backward.
   - cambios breaking/non-breaking.

1. Capa de errores y exception handler
2. Owner primario: Backend plataforma.
3. Backup owner: Arquitectura.
4. Responsabilidades:
   - envelope de respuestas.
   - catalogo de errores.
   - estandar de mapeo HTTP.

1. Persistencia y modelo de datos
2. Owner primario: Datos.
3. Backup owner: Backend.
4. Responsabilidades:
   - migraciones.
   - indices y constraints.
   - performance de consultas.

1. Concurrencia y locking
2. Owner primario: Backend.
3. Backup owner: Datos.
4. Responsabilidades:
   - estrategia de locks.
   - pruebas de concurrencia.
   - monitoreo de conflictos.

1. Scheduler de finalizacion
2. Owner primario: Operaciones/Plataforma.
3. Backup owner: Backend.
4. Responsabilidades:
   - ejecucion periodica.
   - observabilidad del job.
   - recuperacion ante fallos.

1. Notificaciones (persistencia + toast)
2. Owner primario: Backend comunicaciones.
3. Backup owner: Frontend.
4. Responsabilidades:
   - generacion de eventos.
   - estado leido/no leido.
   - consumo UX toast.

1. Privacidad y autorizacion
2. Owner primario: Backend seguridad.
3. Backup owner: Arquitectura.
4. Responsabilidades:
   - ownership checks.
   - visibilidad de telefono/comentarios.
   - cumplimiento de minima exposicion.

1. Frontend UX y flujos
2. Owner primario: Frontend.
3. Backup owner: Producto.
4. Responsabilidades:
   - tabs, boards y modales.
   - mensajes de error UX.
   - reglas de bloqueo en UI.

1. Observabilidad y alertas
2. Owner primario: Operaciones/Plataforma.
3. Backup owner: Backend.
4. Responsabilidades:
   - dashboards SLI/SLO.
   - alertas.
   - runbooks/playbooks.

1. Pruebas de contrato y E2E
2. Owner primario: QA.
3. Backup owner: Backend + Frontend.
4. Responsabilidades:
   - suites de regresion.
   - criterios de aceptacion.
   - cobertura de casos limite.

### RACI resumido por tipo de decision
1. Cambio de estado o regla de dominio:
   - R: Backend.
   - A: Arquitectura.
   - C: Producto, QA.
   - I: Operaciones.
2. Cambio breaking de API:
   - R: Arquitectura API.
   - A: Arquitectura.
   - C: Backend, Frontend, Producto.
   - I: QA, Operaciones.
3. Cambio de indice/constraint:
   - R: Datos.
   - A: Datos.
   - C: Backend.
   - I: Arquitectura.
4. Cambio en scheduler:
   - R: Operaciones.
   - A: Operaciones.
   - C: Backend.
   - I: QA.

### SLA internos de respuesta (operativo)
1. Incidente critico de cupos/estado: respuesta inicial <= 30 min.
2. Incidente scheduler detenido: respuesta inicial <= 30 min.
3. Degradacion severa de API: respuesta inicial <= 30 min.
4. Fuga potencial de datos: respuesta inicial <= 15 min.

### Regla de mantenimiento
1. Cada nuevo componente debe nacer con owner primario y backup.
2. Si cambia el equipo, este documento se actualiza en la misma iteracion.
3. Revisar ownership al menos una vez por trimestre.
