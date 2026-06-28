## Arquitectura Tecnica v1: Modelo de Datos Fisico

Esta seccion aterriza el dominio funcional a estructura de base de datos en PostgreSQL, lista para convertirse en migraciones Django.

### Convenciones generales
1. Zona horaria de negocio: America/Bogota.
2. Almacenamiento temporal: timestamptz en UTC (conversion a Bogota en capa de aplicacion).
3. Borrado logico en entidades de negocio por estado (no hard delete en viajes/solicitudes).
4. Campos de trazabilidad base: created_at y updated_at cuando aplique.

### Catalogos (enums)
1. trip_direction: to_cali, to_parque_natura.
2. trip_status: activo, lleno, cancelado, finalizado.
3. request_status: pendiente, aceptada, rechazada, cancelada_por_solicitante, cancelada_por_ofertante, cancelada_por_otra_aceptacion, cancelada_por_finalizacion, finalizada.
4. notification_type: solicitud_nueva, solicitud_aceptada, solicitud_rechazada, solicitud_cancelada_por_solicitante, solicitud_cancelada_por_otra_aceptacion, viaje_cancelado_por_ofertante, viaje_finalizado.
5. audit_actor_type: usuario, sistema.

### Tabla profile (extiende auth_user)
1. id (bigint, pk).
2. user_id (fk unique a auth_user.id, not null).
3. display_name (varchar(120), not null).
4. photo_url (varchar(500), null).
5. country_code (char(2), not null, default CO).
6. phone_prefix (varchar(8), not null, default +57).
7. phone_number (varchar(20), not null).
8. phone_e164 (varchar(20), not null, unique).
9. created_at (timestamptz, not null).
10. updated_at (timestamptz, not null).

Reglas:
1. Telefono obligatorio para operar en la app.
2. Normalizacion a E.164 al guardar para WhatsApp.

### Tabla vehicle
1. id (bigint, pk).
2. owner_user_id (fk a auth_user.id, not null).
3. brand (varchar(60), not null).
4. reference (varchar(80), not null).
5. color (varchar(40), not null).
6. plate (varchar(10), not null, unique).
7. is_active (bool, not null, default true).
8. created_at (timestamptz, not null).
9. updated_at (timestamptz, not null).

Reglas:
1. Un usuario puede tener 0..n vehiculos.
2. plate se guarda normalizada (uppercase, sin espacios).

### Tabla trip_offer
1. id (bigint, pk).
2. driver_user_id (fk a auth_user.id, not null).
3. vehicle_id (fk a vehicle.id, not null).
4. direction (trip_direction, not null).
5. origin_label (varchar(160), not null).
6. departure_at (timestamptz, not null).
7. total_seats (smallint, not null).
8. status (trip_status, not null, default activo).
9. published_at (timestamptz, not null).
10. canceled_at (timestamptz, null).
11. finalized_at (timestamptz, null).
12. created_at (timestamptz, not null).
13. updated_at (timestamptz, not null).

Constraints:
1. check total_seats >= 1.
2. check total_seats <= 8 (MVP).
3. unique parcial por driver_user_id cuando status in (activo, lleno).

Reglas:
1. Para publicar viaje, vehicle_id debe pertenecer al mismo driver_user_id.
2. activo implica cupos disponibles > 0; lleno implica cupos disponibles = 0 (derivado por logica de negocio).

### Tabla ride_request
1. id (bigint, pk).
2. offer_id (fk a trip_offer.id, not null).
3. rider_user_id (fk a auth_user.id, not null).
4. pickup_label (varchar(160), not null).
5. seats_requested (smallint, not null, default 1).
6. comments (text, null).
7. status (request_status, not null, default pendiente).
8. response_reason (varchar(255), null).
9. created_at (timestamptz, not null).
10. responded_at (timestamptz, null).
11. updated_at (timestamptz, not null).

Constraints:
1. check seats_requested >= 1.
2. check seats_requested <= 4 (MVP).
3. unique parcial por rider_user_id cuando status = aceptada.
4. unique parcial por (offer_id, rider_user_id) cuando status in (pendiente, aceptada).

Reglas:
1. rider_user_id no puede ser igual a driver_user_id de la oferta.
2. comments visibles solo para rider y driver de esa solicitud.

### Tabla notification
1. id (bigint, pk).
2. user_id (fk a auth_user.id, not null).
3. type (notification_type, not null).
4. title (varchar(120), not null).
5. body (varchar(280), not null).
6. payload (jsonb, not null, default {}).
7. is_read (bool, not null, default false).
8. read_at (timestamptz, null).
9. created_at (timestamptz, not null).

Reglas:
1. Se persiste siempre y ademas alimenta toast en frontend.

### Tabla audit_event
1. id (bigint, pk).
2. entity_type (varchar(40), not null).
3. entity_id (bigint, not null).
4. action (varchar(80), not null).
5. previous_state (varchar(50), null).
6. new_state (varchar(50), null).
7. actor_type (audit_actor_type, not null).
8. actor_user_id (fk a auth_user.id, null).
9. source (varchar(30), not null) con valores esperados: ui, backend, scheduler.
10. metadata (jsonb, not null, default {}).
11. correlation_id (uuid, null).
12. created_at (timestamptz, not null).

### Tabla scheduler_job_run (recomendada)
1. id (bigint, pk).
2. job_name (varchar(80), not null).
3. started_at (timestamptz, not null).
4. finished_at (timestamptz, null).
5. status (varchar(20), not null) con valores: running, success, failed.
6. processed_count (int, not null, default 0).
7. error_detail (text, null).

### Indices recomendados
1. trip_offer(status, direction, departure_at).
2. trip_offer(driver_user_id, status).
3. ride_request(offer_id, status, created_at desc).
4. ride_request(rider_user_id, status, created_at desc).
5. notification(user_id, is_read, created_at desc).
6. audit_event(entity_type, entity_id, created_at desc).

### Reglas de integridad clave (backend + DB)
1. No sobre-reserva: aceptar_solicitud en transaccion con lock de trip_offer y ride_request.
2. Una oferta activa por ofertante: enforced por unique parcial en trip_offer.
3. Una solicitud aceptada activa por solicitante: enforced por unique parcial en ride_request.
4. Al finalizar viaje: pendientes -> cancelada_por_finalizacion y aceptadas -> finalizada.

### Decisiones tecnicas cerradas para migraciones
1. Motor objetivo: PostgreSQL.
2. Enum por dominio para estados y tipos de evento.
3. Uso de indices parciales para reglas de unicidad condicional.
4. Campo phone_e164 obligatorio y unico en profile.

### Pendientes tecnicos minimos (siguiente paso)
1. Definir DTO exactos de API por endpoint (request/response JSON).
2. Definir estrategia de control de concurrencia en servicio de aplicacion (orden de locks).
3. Definir periodicidad operativa y mecanismo del scheduler en infraestructura.
