## Criterios de Seleccion de Stack v1

Marco de decision para seleccionar tecnologias alineadas al dominio y restricciones del MVP.

### Objetivo
1. Elegir stack con criterios objetivos, no por preferencia personal.
2. Priorizar consistencia de dominio, velocidad de entrega y mantenibilidad.
3. Reducir riesgo tecnico en concurrencia, observabilidad y operacion.

### Principios de decision
1. Fit con arquitectura ya aprobada.
2. Productividad del equipo actual.
3. Simplicidad operativa para MVP.
4. Escalabilidad razonable sin sobre-ingenieria.
5. Coste total de propiedad controlado.

### Criterios y ponderacion sugerida
1. Capacidad transaccional y locking: 20%
2. Productividad y curva de aprendizaje del equipo: 15%
3. Ecosistema para API, validacion y testing: 15%
4. Observabilidad y operacion (scheduler, logs, metrics): 15%
5. Mantenibilidad y modularidad arquitectonica: 10%
6. Desempeno en consultas criticas: 10%
7. Soporte de versionado API y gobernanza: 5%
8. Coste operativo e infraestructura: 10%

### Requisitos no negociables (must-have)
1. Soporte solido de transacciones ACID sobre PostgreSQL.
2. Control explicito de locking para evitar sobre-reserva.
3. Manejo estandarizado de excepciones y respuestas API.
4. Scheduler confiable cada 1 minuto con idempotencia.
5. Testing de concurrencia factible dentro del stack.
6. Integracion sencilla con contenedores y pipeline CI/CD.

### Criterios por capa

1. Backend/API
2. Debe soportar:
   - arquitectura por capas.
   - inyeccion de dependencias o separacion clara de servicios.
   - validacion robusta de request/response.
   - middleware/handler global de errores.

1. Persistencia
2. Debe soportar:
   - indices parciales y constraints condicionales.
   - consultas eficientes para board y notificaciones.
   - migraciones reproducibles.

1. Scheduler
2. Debe soportar:
   - ejecucion periodica confiable.
   - registro de corridas y reintentos.
   - estrategia de recovery.

1. Frontend
2. Debe soportar:
   - manejo de estados por tabs y board.
   - consumo de envelope estandar de errores.
   - toasts basados en notificaciones persistentes.

### Matriz de evaluacion comparativa (plantilla)
1. Opcion A:
   - score total:
   - fortalezas:
   - riesgos:
2. Opcion B:
   - score total:
   - fortalezas:
   - riesgos:
3. Opcion C:
   - score total:
   - fortalezas:
   - riesgos:

### Riesgos de seleccion y mitigacion
1. Riesgo: stack demasiado complejo para MVP.
   - Mitigacion: preferir opcion con menor carga operativa inicial.
2. Riesgo: falta de experiencia del equipo.
   - Mitigacion: ponderar curva de aprendizaje en scoring.
3. Riesgo: tooling insuficiente para concurrencia/testing.
   - Mitigacion: validar pruebas de carrera en POC corta.

### Proceso recomendado de decision
1. Armar shortlist de 2-3 opciones viables.
2. Puntuar con matriz ponderada.
3. Ejecutar POC tecnica corta para el caso mas critico:
   - aceptar solicitud concurrente.
4. Revisar costo operativo base y plan CI/CD.
5. Tomar decision con acta corta de arquitectura.

### Entregables de esta fase
1. Matriz de scoring completada.
2. Resultado de POC concurrente.
3. Decision de stack aprobada.
4. Blueprint tecnico final para iniciar implementacion.
