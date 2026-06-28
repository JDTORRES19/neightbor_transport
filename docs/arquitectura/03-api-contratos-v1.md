## API Contratos v1

Contrato tecnico inicial de endpoints para soportar los flujos definidos en arquitectura funcional v5.

### Convenciones generales
1. Base URL: /api/v1
2. Formato: application/json
3. Zona horaria en API: ISO 8601 UTC (ejemplo: 2026-06-22T15:30:00Z)
4. Autenticacion: usuario autenticado requerido en endpoints de negocio.
5. Paginacion: page, page_size en listados.

### Envelope de respuesta
1. Exito:
```json
{
  "ok": true,
  "data": {}
}
```
2. Error:
```json
{
  "ok": false,
  "error": {
    "code": "ERR_TRIP_FULL",
    "message": "No hay cupos disponibles.",
    "details": {},
    "request_id": "c5c66cd8-bf54-4ce8-a26d-635c2245fa4f"
  }
}
```

### Codigos HTTP estandar
1. 200: operacion exitosa.
2. 201: recurso creado.
3. 400: payload invalido.
4. 401: no autenticado.
5. 403: sin permisos.
6. 404: recurso no existe.
7. 409: conflicto de negocio/concurrencia.
8. 422: error de validacion de dominio.

### Endpoints de perfil y vehiculos

#### GET /me
1. Uso: obtener perfil del usuario actual.
2. Respuesta data:
```json
{
  "user_id": 12,
  "display_name": "Juan D",
  "photo_url": "https://...",
  "country_code": "CO",
  "phone_prefix": "+57",
  "phone_number": "3001234567",
  "phone_e164": "+573001234567"
}
```

#### PATCH /me
1. Uso: actualizar perfil.
2. Request:
```json
{
  "display_name": "Juan David",
  "photo_url": "https://...",
  "country_code": "CO",
  "phone_prefix": "+57",
  "phone_number": "3001234567"
}
```
3. Errores: ERR_PHONE_REQUIRED, ERR_PHONE_INVALID.

#### GET /vehicles
1. Uso: listar vehiculos del usuario.

#### POST /vehicles
1. Uso: crear vehiculo.
2. Request:
```json
{
  "brand": "Mazda",
  "reference": "3 Touring",
  "color": "Rojo",
  "plate": "ABC123"
}
```

#### PATCH /vehicles/{vehicle_id}
1. Uso: editar vehiculo propio.

#### DELETE /vehicles/{vehicle_id}
1. Uso: desactivar vehiculo propio (soft delete via is_active=false).

### Endpoints de viajes

#### GET /trips
1. Uso: board de viajes disponibles.
2. Query params: direction, page, page_size.
3. Regla: devuelve viajes en estado activo.
4. Respuesta item:
```json
{
  "id": 44,
  "direction": "to_cali",
  "origin_label": "Unidad La Arboleda",
  "departure_at": "2026-06-22T22:30:00Z",
  "published_at": "2026-06-22T20:10:00Z",
  "status": "activo",
  "total_seats": 4,
  "available_seats": 2,
  "driver": {
    "user_id": 31,
    "display_name": "Ana V",
    "photo_url": "https://..."
  },
  "vehicle": {
    "id": 7,
    "brand": "Kia",
    "reference": "Picanto",
    "color": "Blanco",
    "plate": "XYZ987"
  }
}
```

#### GET /trips/mine/active
1. Uso: obtener viaje activo o lleno del ofertante actual.
2. Respuesta: null si no existe.

#### POST /trips
1. Uso: publicar viaje.
2. Request:
```json
{
  "direction": "to_cali",
  "origin_label": "Unidad La Arboleda",
  "departure_at": "2026-06-22T22:30:00Z",
  "total_seats": 4,
  "vehicle_id": 7
}
```
3. Errores: ERR_DRIVER_ACTIVE_TRIP_EXISTS, ERR_DRIVER_VEHICLE_REQUIRED, ERR_PHONE_REQUIRED.
4. Response: 201 con viaje creado.

#### POST /trips/{trip_id}/cancel
1. Uso: cancelar viaje por ofertante.
2. Request opcional:
```json
{
  "reason": "No podre salir hoy"
}
```
3. Errores: ERR_TRIP_NOT_ACTIVE, ERR_FORBIDDEN_ACTION.

#### POST /trips/{trip_id}/finalize
1. Uso: finalizar viaje manualmente.
2. Errores: ERR_TRIP_NOT_ACTIVE, ERR_FORBIDDEN_ACTION.

### Endpoints de solicitudes

#### GET /trips/{trip_id}/requests
1. Uso: listar solicitudes de una oferta propia.
2. Regla: solo visible para ofertante del viaje.
3. Incluye bandera can_open_whatsapp_link por solicitud.

#### POST /trips/{trip_id}/requests
1. Uso: crear solicitud como solicitante.
2. Request:
```json
{
  "pickup_label": "Porteria 2",
  "seats_requested": 1,
  "comments": "Voy con una maleta pequena"
}
```
3. Errores: ERR_TRIP_NOT_ACTIVE, ERR_TRIP_FULL, ERR_RIDER_HAS_ACTIVE_ACCEPTED, ERR_FORBIDDEN_ACTION, ERR_CONCURRENT_UPDATE.

#### POST /requests/{request_id}/accept
1. Uso: aceptar solicitud por ofertante.
2. Regla: transaccion con lock para evitar sobre-reserva.
3. Errores: ERR_REQUEST_NOT_PENDING, ERR_TRIP_NOT_ACTIVE, ERR_TRIP_FULL, ERR_RIDER_HAS_ACTIVE_ACCEPTED, ERR_CONCURRENT_UPDATE.

#### POST /requests/{request_id}/reject
1. Uso: rechazar solicitud por ofertante.
2. Request opcional:
```json
{
  "reason": "No alcanzo a recogerte por ruta"
}
```
3. Errores: ERR_REQUEST_NOT_PENDING, ERR_FORBIDDEN_ACTION.

#### POST /requests/{request_id}/cancel
1. Uso: cancelar solicitud por solicitante.
2. Errores: ERR_INVALID_STATE_TRANSITION, ERR_FORBIDDEN_ACTION.

#### GET /requests/mine
1. Uso: listar solicitudes del solicitante actual.
2. Incluye viaje relacionado y bandera can_open_whatsapp_link.

### Endpoints de notificaciones

#### GET /notifications
1. Uso: listar notificaciones del usuario.
2. Query params: is_read, page, page_size.

#### POST /notifications/{notification_id}/read
1. Uso: marcar una notificacion como leida.

#### POST /notifications/read-all
1. Uso: marcar todas como leidas.

### Regla de WhatsApp en contratos API
1. Campo can_open_whatsapp_link = true solo cuando request.status = aceptada.
2. Campo whatsapp_url se entrega solo cuando can_open_whatsapp_link = true.
3. Formato whatsapp_url: https://wa.me/{phone_e164_sin_mas}?text={mensaje_url_encoded}

### Ejemplo de objeto solicitud (respuesta)
```json
{
  "id": 99,
  "status": "aceptada",
  "pickup_label": "Porteria 2",
  "seats_requested": 1,
  "comments": "Voy con una maleta pequena",
  "rider": {
    "user_id": 53,
    "display_name": "Carlos M",
    "photo_url": "https://..."
  },
  "trip": {
    "id": 44,
    "direction": "to_cali",
    "origin_label": "Unidad La Arboleda",
    "departure_at": "2026-06-22T22:30:00Z",
    "status": "activo"
  },
  "can_open_whatsapp_link": true,
  "whatsapp_url": "https://wa.me/573001234567?text=Hola%20..."
}
```

### Idempotencia y concurrencia
1. Endpoints con mayor riesgo de carrera: /requests/{id}/accept, /trips/{id}/cancel, /trips/{id}/finalize.
2. Recomendacion: soportar cabecera Idempotency-Key en operaciones POST de estado.
3. En conflicto concurrente, devolver 409 con ERR_CONCURRENT_UPDATE.

### Mapeo minimo accion -> endpoint
1. Publicar viaje -> POST /trips
2. Crear solicitud -> POST /trips/{trip_id}/requests
3. Aceptar solicitud -> POST /requests/{request_id}/accept
4. Rechazar solicitud -> POST /requests/{request_id}/reject
5. Cancelar solicitud por solicitante -> POST /requests/{request_id}/cancel
6. Cancelar viaje por ofertante -> POST /trips/{trip_id}/cancel
7. Finalizar viaje manual -> POST /trips/{trip_id}/finalize
8. Finalizar viaje automatico -> scheduler interno (sin endpoint publico)

### Pendientes de este documento
1. Definir contrato de autenticacion exacto (cookie session vs JWT).
2. Definir versionado y politica de deprecacion de endpoints.
3. Definir formato final de paginacion (offset/limit vs cursor).
