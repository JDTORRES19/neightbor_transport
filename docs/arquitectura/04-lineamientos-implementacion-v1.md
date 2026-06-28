## Lineamientos de Implementacion v1 (previo a tecnologias)

Este documento define decisiones de arquitectura de implementacion sin acoplarse aun a framework, librerias o infraestructura especifica.

### Objetivo
1. Reducir retrabajo tecnico cerrando reglas de construccion antes de seleccionar stack.
2. Mantener consistencia entre dominio, API, datos, notificaciones y operacion.

### Principios de arquitectura
1. Dominio primero: reglas de negocio viven en casos de uso y servicios de dominio.
2. Persistencia como detalle: repositorios abstraen acceso a base de datos.
3. API delgada: controladores validan entrada/salida y delegan logica.
4. Estados como fuente de verdad: sin transiciones directas fuera de casos de uso.
5. Consistencia fuerte en operaciones criticas de cupos y aceptaciones.
6. Observabilidad por defecto: toda accion relevante genera trazas auditables.

### Arquitectura logica por capas
1. Capa de presentacion:
   - Endpoints HTTP y serializacion.
   - Mapeo de errores de dominio a respuestas API.
2. Capa de aplicacion:
   - Casos de uso (publicar viaje, aceptar solicitud, finalizar viaje, etc.).
   - Orquestacion transaccional y politicas de idempotencia.
3. Capa de dominio:
   - Entidades, invariantes y transiciones de estado.
   - Reglas de cupos, unicidad de viaje activo y solicitud aceptada activa.
4. Capa de infraestructura:
   - Implementaciones de repositorio.
   - Scheduler, notificaciones persistentes y logging.

### Bounded contexts funcionales
1. Identidad y perfil:
   - Usuario, perfil, telefono, pais.
2. Flota:
   - Vehiculos del usuario.
3. Viajes:
   - Oferta, estados y capacidad de cupos.
4. Solicitudes:
   - Solicitud de cupo y ciclo de vida.
5. Comunicacion:
   - Notificaciones persistentes y reglas de WhatsApp.
6. Auditoria:
   - Historial de transiciones y acciones.

### Casos de uso y responsabilidades
1. PublicarViajeUseCase:
   - valida perfil y vehiculo.
   - crea viaje en estado activo.
2. CrearSolicitudUseCase:
   - valida viaje activo y regla de solicitud aceptada activa.
   - crea solicitud pendiente y notifica ofertante.
3. AceptarSolicitudUseCase:
   - aplica lock, valida invariantes y evita sobre-reserva.
   - acepta solicitud, ajusta viaje y cancela pendientes del solicitante.
4. RechazarSolicitudUseCase:
   - cambia estado y notifica solicitante.
5. CancelarSolicitudUseCase:
   - cambia estado y libera cupos si aplica.
6. CancelarViajeUseCase:
   - cancela viaje y solicitudes asociadas.
7. FinalizarViajeUseCase:
   - finaliza viaje y transforma solicitudes pendientes/aceptadas.
8. FinalizarViajesExpiradosJob:
   - proceso periodico con reglas de idempotencia.

### Fronteras transaccionales
1. Operaciones con transaccion obligatoria:
   - aceptar solicitud.
   - cancelar viaje.
   - finalizar viaje (manual y automatico).
2. Regla de lock:
   - bloquear primero viaje, luego solicitud, luego consultas de solicitudes relacionadas.
3. Regla de rollback:
   - ante cualquier incumplimiento de invariante se revierte toda la operacion.
4. Regla de idempotencia:
   - reintentos no deben duplicar cambios ni notificaciones.

### Modelo de consistencia
1. Consistencia fuerte:
   - cupos y estados de viaje/solicitud.
2. Consistencia eventual:
   - proyecciones de board y orden de notificaciones UI.
3. Derivados calculados:
   - available_seats no se persiste como dato maestro; se calcula desde estado de solicitudes aceptadas.

### Estrategia de errores y resiliencia
1. Catalogo de errores como contrato estable.
2. Error de concurrencia unico: ERR_CONCURRENT_UPDATE para carreras.
3. Excepciones tecnicas no filtradas al cliente con detalle interno.
4. request_id obligatorio en respuestas de error.

### Seguridad y privacidad
1. Validacion de ownership en todos los recursos mutables.
2. Minima exposicion de datos personales en listados.
3. Telefono para WhatsApp expuesto solo cuando solicitud aceptada.
4. Comentarios de solicitud visibles solo entre solicitante y ofertante.
5. Auditoria inmutable para acciones criticas.

### Scheduler y tareas operativas
1. Frecuencia objetivo: cada 1 minuto.
2. Scope del job: viajes activo/lleno con salida + 20 min vencida.
3. Idempotencia por viaje: no reprocesar finalizados.
4. Registro de ejecucion: metricas de procesados, errores y duracion.

### Observabilidad minima
1. Logs estructurados por caso de uso:
   - action, actor_id, entity_id, previous_state, new_state, request_id.
2. Metricas base:
   - solicitudes aceptadas/rechazadas.
   - tasa de conflictos concurrentes.
   - tiempos de respuesta por endpoint.
   - ejecuciones exitosas/fallidas del scheduler.
3. Trazabilidad:
   - correlation_id entre API, auditoria y notificaciones.

### Calidad y pruebas
1. Unit tests:
   - invariantes de dominio y transiciones de estado.
2. Integration tests:
   - endpoints + persistencia + mapeo de errores.
3. Concurrency tests:
   - doble aceptacion simultanea sin sobre-reserva.
4. Contract tests API:
   - envelope y codigos de error estandar.
5. Job tests:
   - finalizacion automatica e idempotencia.

### Gobernanza de cambios
1. Toda decision no trivial se registra como ADR corto.
2. Cambios en estados o codigos de error requieren versionado de contrato.
3. Cualquier nueva regla de negocio debe impactar:
   - contratos funcionales.
   - API contratos.
   - modelo de datos.
   - checklist de aceptacion.

### Secuencia recomendada de implementacion (sin stack)
1. Definir estructura de paquetes por capas y casos de uso.
2. Implementar catalogo de errores y handler global.
3. Implementar entidades y repositorios base.
4. Implementar casos de uso criticos (publicar, crear, aceptar, finalizar).
5. Exponer endpoints de esos casos de uso.
6. Implementar notificaciones y auditoria.
7. Implementar scheduler de finalizacion.
8. Completar pruebas de concurrencia y contratos.
