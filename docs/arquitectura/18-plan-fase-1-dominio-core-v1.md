## Plan de Implementacion - Fase 1 (Dominio core)

Fecha: 2026-06-23
Estado: planificado
Duracion sugerida: 5 a 7 dias

### Objetivo
1. Implementar nucleo funcional del MVP: perfil, vehiculos, viajes y solicitudes.
2. Entregar primer flujo completo ofertante/solicitante con UI funcional.

### Alcance funcional
1. Perfil y telefono obligatorio normalizado (E.164).
2. Vehiculos del ofertante (alta, listado, desactivacion).
3. Publicar viaje y listar board con filtros basicos.
4. Crear solicitud y gestion inicial (pendiente, cancelada por usuario).

### Alcance backend
1. Endpoints v1 para:
   - /me
   - /vehicles
   - /trips
   - /requests
2. Casos de uso base:
   - publicar viaje
   - crear solicitud
   - cancelar solicitud
3. Reglas de dominio activas:
   - viaje activo unico por ofertante
   - validaciones de ownership
4. Pruebas unitarias e integracion de casos criticos.

### Alcance frontend
1. Flujos UI:
   - perfil
   - vehiculos
   - board de viajes
   - crear solicitud
2. Estado server con TanStack Query por feature.
3. Formularios con React Hook Form + Zod.
4. Manejo visual de errores de negocio por codigo.

### Entregables
1. Vertical slice completo crear viaje -> crear solicitud.
2. Board navegable con datos reales de API.
3. Validaciones de dominio reflejadas en UI.
4. Baseline de pruebas automatizadas backend y frontend.

### Criterios de salida
1. No se publica viaje sin telefono valido y vehiculo activo.
2. Board responde con paginacion y filtros definidos.
3. Error handling consistente en backend y frontend.
4. Flujos principales pasan en pruebas de integracion.

### Checklist de ejecucion
1. Implementar modelos y repositorios por contexto.
2. Implementar casos de uso y endpoints del dominio base.
3. Construir pantallas y formularios del flujo principal.
4. Integrar cliente API tipado con manejo de errores.
5. Ejecutar smoke end-to-end del flujo principal.

### Riesgos y mitigaciones
1. Riesgo: N+1 y rendimiento pobre en board.
   - Mitigacion: query services e indices desde el inicio.
2. Riesgo: acoplamiento UI a payloads internos.
   - Mitigacion: normalizadores y mapeadores en cliente API.
3. Riesgo: deuda de pruebas por velocidad de entrega.
   - Mitigacion: DoD exige pruebas minimas por endpoint/feature.
