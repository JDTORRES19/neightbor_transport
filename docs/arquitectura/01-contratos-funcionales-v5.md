## Arquitectura Funcional v5: Contratos y Reglas

Revision enfocada en contratos funcionales de acciones de negocio, alineada con todas las decisiones acordadas.

**Resumen de revision**
1. Cobertura de contratos: parcial en v4; faltaban 5 acciones operativas para cerrar el ciclo completo.
2. Coherencia de estados: correcta, con ajuste clave ya incluido: solicitudes aceptadas pasan a finalizada cuando el viaje finaliza.
3. Reglas criticas: correctas (sin sobre-reserva, una oferta activa por ofertante, una aceptada activa por solicitante).
4. Gap principal cerrado en v5: matriz completa de 8 contratos con precondiciones, validaciones, transiciones, efectos, notificaciones, auditoria y errores.

**Plantilla oficial de contrato por accion**
1. Accion.
2. Actor autorizado.
3. Precondiciones.
4. Inputs requeridos/opcionales.
5. Validaciones UI.
6. Validaciones backend.
7. Regla transaccional.
8. Cambios de estado.
9. Efectos colaterales.
10. Notificaciones persistentes.
11. Toasts UI.
12. Auditoria.
13. Errores estandar.
14. Resultado esperado.

**Matriz completa de contratos (v5)**
1. Publicar viaje
2. Actor: ofertante autenticado.
3. Precondiciones: perfil completo con telefono obligatorio; tiene al menos 1 vehiculo; no tiene otro viaje activo.
4. Inputs: trayecto, origen, fecha_hora_salida, cupos, vehiculo_id.
5. Validaciones UI: campos obligatorios, fecha futura, cupos > 0, selector de vehiculo habilitado.
6. Validaciones backend: vehiculo pertenece al ofertante, unicidad de viaje activo, timezone America/Bogota.
7. Transaccional: si (crear viaje + auditoria atomico).
8. Estados: null -> activo.
9. Efectos: viaje publicado en board.
10. Notificaciones: opcional (sin evento obligatorio en MVP).
11. Toast: viaje publicado.
12. Auditoria: accion publicar_viaje.
13. Errores: ERR_DRIVER_ACTIVE_TRIP_EXISTS, ERR_DRIVER_VEHICLE_REQUIRED, ERR_PHONE_REQUIRED.
14. Resultado: viaje activo creado.

1. Crear solicitud
2. Actor: solicitante autenticado.
3. Precondiciones: viaje en estado activo; cupos disponibles; solicitante no tiene solicitud aceptada activa.
4. Inputs: viaje_id, punto_recogida, cupos_solicitados, comentarios opcional.
5. Validaciones UI: cupos >= 1; no permitir boton si viaje no activo o lleno.
6. Validaciones backend: viaje activo, cupos disponibles al momento real, no solicitud en propio viaje, regla de una aceptada activa.
7. Transaccional: si (crear solicitud + auditoria + notificacion al ofertante).
8. Estados: null -> pendiente.
9. Efectos: solicitud visible en lista del ofertante.
10. Notificaciones: solicitud_nueva al ofertante.
11. Toast: solicitud enviada.
12. Auditoria: accion crear_solicitud.
13. Errores: ERR_TRIP_NOT_ACTIVE, ERR_TRIP_FULL, ERR_RIDER_HAS_ACTIVE_ACCEPTED, ERR_FORBIDDEN_ACTION, ERR_CONCURRENT_UPDATE.
14. Resultado: solicitud pendiente creada.

1. Aceptar solicitud
2. Actor: ofertante dueno del viaje.
3. Precondiciones: solicitud pendiente; viaje activo; cupos suficientes; solicitante sin aceptada activa.
4. Inputs: solicitud_id.
5. Validaciones UI: solo boton en pendientes del propio viaje.
6. Validaciones backend: todas las precondiciones en tiempo real.
7. Transaccional: obligatoria con lock de viaje y solicitud.
8. Estados: solicitud pendiente -> aceptada; viaje activo -> activo|lleno segun cupos; otras pendientes del solicitante -> cancelada_por_otra_aceptacion.
9. Efectos: recalculo de cupos y estado del viaje.
10. Notificaciones: solicitud_aceptada al solicitante; solicitud_cancelada_por_otra_aceptacion a solicitudes impactadas.
11. Toast: solicitud aceptada.
12. Auditoria: accion aceptar_solicitud + acciones de cancelacion automatica derivadas.
13. Errores: ERR_REQUEST_NOT_PENDING, ERR_TRIP_NOT_ACTIVE, ERR_TRIP_FULL, ERR_RIDER_HAS_ACTIVE_ACCEPTED, ERR_CONCURRENT_UPDATE.
14. Resultado: solicitud aceptada y cupos consistentes.

1. Rechazar solicitud
2. Actor: ofertante dueno del viaje.
3. Precondiciones: solicitud pendiente.
4. Inputs: solicitud_id, motivo opcional.
5. Validaciones UI: boton solo en pendientes.
6. Validaciones backend: solicitud pertenece a viaje del actor y sigue pendiente.
7. Transaccional: si (actualizacion + notificacion + auditoria).
8. Estados: pendiente -> rechazada.
9. Efectos: no cambia cupos.
10. Notificaciones: solicitud_rechazada al solicitante.
11. Toast: solicitud rechazada.
12. Auditoria: accion rechazar_solicitud.
13. Errores: ERR_REQUEST_NOT_PENDING, ERR_FORBIDDEN_ACTION, ERR_CONCURRENT_UPDATE.
14. Resultado: solicitud rechazada.

1. Cancelar solicitud por solicitante
2. Actor: solicitante dueno de la solicitud.
3. Precondiciones: solicitud en pendiente o aceptada.
4. Inputs: solicitud_id.
5. Validaciones UI: boton disponible solo en estados cancelables.
6. Validaciones backend: ownership y estado valido.
7. Transaccional: si (actualizar solicitud + recalcular viaje + notificaciones + auditoria).
8. Estados: pendiente|aceptada -> cancelada_por_solicitante; viaje lleno -> activo si libera cupo.
9. Efectos: liberacion de cupos cuando aplica.
10. Notificaciones: solicitud_cancelada_por_solicitante al ofertante.
11. Toast: solicitud cancelada.
12. Auditoria: accion cancelar_solicitud_por_solicitante.
13. Errores: ERR_FORBIDDEN_ACTION, ERR_INVALID_STATE_TRANSITION, ERR_CONCURRENT_UPDATE.
14. Resultado: solicitud cancelada y viaje recalculado.

1. Cancelar viaje por ofertante
2. Actor: ofertante dueno del viaje.
3. Precondiciones: viaje en activo o lleno.
4. Inputs: viaje_id, motivo opcional.
5. Validaciones UI: boton visible solo en estados cancelables.
6. Validaciones backend: ownership y estado valido.
7. Transaccional: si (cambio de viaje + cancelacion de solicitudes + notificaciones + auditoria).
8. Estados: viaje activo|lleno -> cancelado; solicitudes pendiente|aceptada -> cancelada_por_ofertante.
9. Efectos: viaje sale del board.
10. Notificaciones: viaje_cancelado_por_ofertante a solicitantes impactados.
11. Toast: viaje cancelado.
12. Auditoria: accion cancelar_viaje.
13. Errores: ERR_TRIP_NOT_ACTIVE, ERR_FORBIDDEN_ACTION, ERR_CONCURRENT_UPDATE.
14. Resultado: viaje cancelado y solicitudes relacionadas canceladas.

1. Finalizar viaje manual
2. Actor: ofertante dueno del viaje.
3. Precondiciones: viaje en activo o lleno.
4. Inputs: viaje_id.
5. Validaciones UI: boton finalizar visible solo en activo/lleno.
6. Validaciones backend: ownership y estado valido.
7. Transaccional: si (cambio de viaje + cierre de solicitudes + notificaciones + auditoria).
8. Estados: viaje activo|lleno -> finalizado; solicitudes pendiente -> cancelada_por_finalizacion; solicitudes aceptada -> finalizada.
9. Efectos: viaje fuera de operaciones.
10. Notificaciones: viaje_finalizado a solicitantes relacionados.
11. Toast: viaje finalizado.
12. Auditoria: accion finalizar_viaje_manual.
13. Errores: ERR_TRIP_NOT_ACTIVE, ERR_FORBIDDEN_ACTION, ERR_CONCURRENT_UPDATE.
14. Resultado: viaje finalizado con solicitudes consistentes.

1. Finalizar viaje automatico
2. Actor: sistema (scheduler).
3. Precondiciones: viaje en activo|lleno y salida + 20 min vencida.
4. Inputs: none directos; lote de viajes elegibles.
5. Validaciones UI: no aplica.
6. Validaciones backend: timezone America/Bogota; idempotencia por estado.
7. Transaccional: por viaje (unidad atomica individual).
8. Estados: igual a finalizar manual.
9. Efectos: igual a finalizar manual.
10. Notificaciones: viaje_finalizado.
11. Toast: al leer eventos nuevos.
12. Auditoria: accion finalizar_viaje_automatico con actor sistema.
13. Errores: no expuestos al usuario; registrar fallo tecnico en observabilidad.
14. Resultado: cierre automatico consistente.

**Catalogo estandar de errores (v5)**
1. ERR_TRIP_NOT_ACTIVE.
2. ERR_TRIP_FULL.
3. ERR_REQUEST_NOT_PENDING.
4. ERR_RIDER_HAS_ACTIVE_ACCEPTED.
5. ERR_DRIVER_ACTIVE_TRIP_EXISTS.
6. ERR_DRIVER_VEHICLE_REQUIRED.
7. ERR_FORBIDDEN_ACTION.
8. ERR_CONCURRENT_UPDATE.
9. ERR_PHONE_REQUIRED.
10. ERR_PHONE_INVALID.
11. ERR_INVALID_STATE_TRANSITION.
12. ERR_OWNERSHIP_MISMATCH.

**Reglas de visibilidad de WhatsApp (confirmadas)**
1. Solicitud pendiente o rechazada: sin enlace para ambas partes.
2. Solicitud aceptada: enlace visible para ofertante y solicitante.
3. Solicitud finalizada o cancelada: enlace no visible por defecto en MVP.

**Verificacion funcional de contratos**
1. Probar cada accion en caso feliz.
2. Probar cada accion con actor no autorizado.
3. Probar conflictos de concurrencia en aceptar solicitud.
4. Probar transiciones prohibidas en todos los estados.
5. Probar regla una oferta activa por ofertante.
6. Probar regla una aceptada activa por solicitante.
7. Probar scheduler cada minuto y conversion aceptada -> finalizada.

**Checklist de aceptacion por contrato (listo para revision de negocio/QA)**
1. Publicar viaje: caso feliz, sin vehiculo, duplicidad de viaje activo, auditoria.
2. Crear solicitud: caso feliz, viaje lleno/no activo, bloque por aceptada activa, notificacion, privacidad.
3. Aceptar solicitud: caso feliz, cancelacion de otras pendientes, solicitud no pendiente, concurrencia, notificaciones, auditoria.
4. Rechazar solicitud: caso feliz, actor no autorizado, solicitud ya procesada, notificacion, auditoria.
5. Cancelar solicitud por solicitante: caso feliz, liberacion de cupo, actor no autorizado, notificacion, auditoria.
6. Cancelar viaje por ofertante: caso feliz, cascada de cancelaciones, actor no autorizado, viaje no cancelable, notificaciones, auditoria.
7. Finalizar viaje manual: caso feliz, pendientes a cancelada_por_finalizacion, aceptadas a finalizada, viaje no finalizable, notificaciones, auditoria.
8. Finalizar viaje automatico: caso feliz, idempotencia, timezone, auditoria con actor sistema.

**Checklist transversal de consistencia**
1. Nunca cupos negativos.
2. Nunca mas de una solicitud aceptada activa por solicitante.
3. Nunca mas de un viaje activo por ofertante.
4. Enlace WhatsApp visible para ambas partes solo con solicitud aceptada.
5. Telefono obligatorio en perfil; pais por defecto Colombia (+57).
6. Todo error funcional responde con codigo estandar del catalogo.
7. Toda transicion de estado genera registro de auditoria.
8. Todo evento de negocio definido genera notificacion persistente y disparador de toast.
