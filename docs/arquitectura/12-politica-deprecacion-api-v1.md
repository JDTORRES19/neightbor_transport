## Politica de Deprecacion API v1

Reglas para evolucionar la API sin romper integraciones activas y con ventana de migracion predecible.

### Objetivo
1. Proteger clientes existentes ante cambios.
2. Permitir evolucion controlada de contratos.
3. Definir proceso formal para cambios breaking y retiro de versiones.

### Definiciones
1. Cambio no-breaking:
   - agregar campos opcionales.
   - agregar endpoints nuevos.
   - ampliar catalogos sin alterar comportamiento previo.
2. Cambio breaking:
   - eliminar/renombrar campos.
   - cambiar semantica de respuesta o codigos de error.
   - modificar reglas que invaliden clientes actuales.

### Regla general de versionado
1. No-breaking: se mantiene en misma version mayor (v1).
2. Breaking: requiere nueva version mayor (v2).
3. No se introducen breaking changes en una version activa.

### Ciclo de deprecacion por version
1. Anuncio de deprecacion:
   - publicar nota de cambio con fecha de anuncio.
   - incluir motivacion, impacto y guia de migracion.
2. Ventana minima de soporte:
   - recomendada: 90 dias desde anuncio para endpoints/version en deprecacion.
3. Estado sunset:
   - marcar endpoint/version como deprecado en documentacion.
   - emitir avisos en headers de respuesta.
4. Retiro:
   - pasado el plazo, endpoint/version puede desactivarse.
   - mantener registro historico de comunicados.

### Headers recomendados durante deprecacion
1. Deprecation: true
2. Sunset: <fecha RFC 1123>
3. Link: <url guia migracion>; rel="deprecation"

### Reglas por tipo de cambio
1. Eliminacion de campo:
   - anunciar deprecacion.
   - mantener campo durante ventana de soporte.
   - remover solo en version mayor nueva o al final del ciclo definido.
2. Cambio de codigo de error:
   - mantener compatibilidad o mapear temporalmente.
   - comunicar equivalencias antiguas vs nuevas.
3. Cambio de endpoint:
   - publicar endpoint reemplazo.
   - coexistencia de ambos durante ventana de soporte.

### Contrato de comunicacion
1. Canal primario: documentacion de arquitectura/API.
2. Canal secundario: release notes internas.
3. Contenido minimo de aviso:
   - que cambia.
   - quien impacta.
   - desde cuando.
   - fecha de retiro.
   - pasos de migracion.

### Politica de soporte de versiones
1. Version activa: recibe mejoras y fixes.
2. Version en deprecacion: solo fixes criticos.
3. Version retirada: sin soporte operativo.

### Criterios para declarar deprecacion
1. Existe reemplazo funcional equivalente.
2. Se dispone de guia de migracion.
3. Se definio ventana de soporte.
4. Se asigno owner del proceso de migracion.

### Checklist de deprecacion (obligatorio)
1. ADR actualizado con decision de cambio.
2. API contratos actualizados en nueva version.
3. Tests de contrato para version nueva y version vigente.
4. Comunicacion emitida con fechas y alcance.
5. Headers de deprecacion activos.
6. Monitoreo de uso del endpoint/version deprecada.

### Ownership del proceso
1. Owner primario: Arquitectura API.
2. Backup owner: Backend.
3. Aprobadores: Arquitectura + Producto.

### Excepciones
1. Incidente de seguridad critico:
   - se permite retiro acelerado.
   - requiere comunicacion inmediata y plan de contingencia.
2. Incidente de integridad de datos:
   - se permite mitigacion urgente.
   - debe documentarse post-mortem y decision ADR.

### Indicadores de seguimiento
1. % trafico en version deprecada.
2. Tiempo medio de migracion por cliente interno.
3. Numero de incidentes derivados de deprecacion.
4. Cumplimiento de ventanas de soporte definidas.
