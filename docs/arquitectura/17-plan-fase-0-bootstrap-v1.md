## Plan de Implementacion - Fase 0 (Bootstrap tecnico)

Fecha: 2026-06-23
Estado: listo para ejecucion
Duracion sugerida: 2 a 4 dias

### Objetivo
1. Dejar base tecnica estable para desarrollar dominio sin retrabajo.
2. Alinear backend FastAPI y frontend React con contratos, errores y observabilidad minima.

### Alcance backend
1. Estructura de capas inicial:
   - app/api/v1
   - app/application
   - app/domain
   - app/infrastructure
2. Configuracion central con pydantic-settings.
3. Handler global de excepciones + envelope estandar.
4. request_id en middleware y logs estructurados.
5. Base de SQLAlchemy y sesion por request.

### Alcance frontend
1. Estructura inicial por modulos:
   - src/app
   - src/features
   - src/shared
2. Cliente HTTP base y manejo estandar de errores.
3. Capa de estado server (TanStack Query) inicializada.
4. Layout base responsive y pagina de estado de integracion API.

### Integracion backend/frontend
1. Definir contrato inicial OpenAPI v1.
2. Establecer variable VITE_API_BASE_URL y consumo unificado.
3. Definir codigos de error base que frontend debe mapear.

### Entregables
1. Esqueleto de arquitectura backend y frontend.
2. Endpoint health con envelope estandar.
3. Cliente frontend que consume health de API.
4. Guia de convenciones de carpetas y naming.

### Criterios de salida
1. API responde health con envelope de exito y request_id.
2. Frontend muestra estado de conexion API sin errores de runtime.
3. Logs backend incluyen request_id y codigo de error cuando aplica.
4. Compose levanta db, web y frontend de forma reproducible.

### Checklist de ejecucion
1. Congelar estructura de carpetas y convenciones.
2. Implementar middleware request_id.
3. Implementar handler global + catalogo inicial de errores.
4. Crear cliente HTTP frontend y adaptador de errores.
5. Validar flujo health end-to-end.

### Riesgos y mitigaciones
1. Riesgo: divergencia de envelope entre capas.
   - Mitigacion: tests de contrato desde fase 0.
2. Riesgo: deuda de estructura por rapidez inicial.
   - Mitigacion: bloquear PRs fuera de convenciones de capas.
3. Riesgo: roturas por toolchain frontend.
   - Mitigacion: npm ci y limpieza de cache en arranque.
