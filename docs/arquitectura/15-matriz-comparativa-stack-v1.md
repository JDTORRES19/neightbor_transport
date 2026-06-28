## Matriz Comparativa de Stack v1

Comparativa inicial de alternativas tecnologicas usando los criterios y ponderaciones definidos en 14-criterios-seleccion-stack-v1.md.

### Criterios y ponderacion
| Criterio | Peso |
|---|---:|
| Capacidad transaccional y locking | 20% |
| Productividad y curva de aprendizaje | 15% |
| Ecosistema API, validacion y testing | 15% |
| Observabilidad y operacion | 15% |
| Mantenibilidad y modularidad | 10% |
| Desempeno en consultas criticas | 10% |
| Versionado API y gobernanza | 5% |
| Coste operativo e infraestructura | 10% |

### Opciones evaluadas

#### Opcion A
1. Backend/API: Python + Django + DRF
2. Datos: PostgreSQL
3. Scheduler/background: Celery + Redis (o alternativa equivalente)
4. Frontend: web separada o Django templates para MVP

#### Opcion B
1. Backend/API: Python + FastAPI + SQLAlchemy
2. Datos: PostgreSQL
3. Scheduler/background: Celery + Redis (o APScheduler para etapa inicial)
4. Frontend: web separada

#### Opcion C
1. Backend/API: Node.js + NestJS + ORM relacional
2. Datos: PostgreSQL
3. Scheduler/background: cola de trabajos en ecosistema Node
4. Frontend: web separada

### Scoring (1 a 5) y resultado ponderado
| Criterio | Peso | Opcion A | Opcion B | Opcion C |
|---|---:|---:|---:|---:|
| Capacidad transaccional y locking | 20 | 5 | 5 | 4 |
| Productividad y curva de aprendizaje | 15 | 5 | 4 | 3 |
| Ecosistema API/testing | 15 | 5 | 4 | 4 |
| Observabilidad y operacion | 15 | 4 | 4 | 4 |
| Mantenibilidad/modularidad | 10 | 4 | 4 | 4 |
| Desempeno consultas criticas | 10 | 4 | 4 | 4 |
| Versionado API/gobernanza | 5 | 4 | 4 | 4 |
| Coste operativo | 10 | 4 | 4 | 3 |
| **Total ponderado (/100)** | 100 | **90** | **84** | **76** |

### Lectura de resultados
1. Opcion A obtiene la mejor puntuacion total.
2. Opcion B queda cercana y es muy viable, con mayor esfuerzo inicial de estructura.
3. Opcion C es viable, pero con mayor costo de adopcion para este contexto y menor inercia en el proyecto actual.

### Recomendacion v1
1. Recomendada: Opcion A.
2. Razon principal:
   - mejor ajuste con el estado actual del repositorio.
   - alta productividad para MVP con reglas de dominio y concurrencia.
   - menor friccion operativa para avanzar rapido en Fase 0/Fase 1.

### Riesgos por opcion

#### Opcion A
1. Riesgo: acoplar demasiada logica al framework.
2. Mitigacion: mantener arquitectura por capas, use cases y repositorios.

#### Opcion B
1. Riesgo: mayor complejidad de decisiones de librerias desde el inicio.
2. Mitigacion: plantilla base de arquitectura y convenciones estrictas.

#### Opcion C
1. Riesgo: curva de aprendizaje y mayor costo de estandarizacion en este contexto.
2. Mitigacion: solo considerar si el equipo domina este stack y hay drivers claros.

### Decision propuesta
1. Decision propuesta: GO con Opcion A para inicio MVP.
2. Validacion previa recomendada:
   - mini POC de concurrencia para aceptar solicitud en carrera.
   - baseline de latencia en endpoints criticos.

### Plan de verificacion rapida (POC 2-3 dias)
1. Implementar vertical slice minimo:
   - crear viaje
   - crear solicitud
   - aceptar solicitud con lock
2. Probar doble aceptacion simultanea y confirmar cero sobre-reserva.
3. Medir p95 de endpoints criticos y registrar baseline.

### Criterio de confirmacion final de stack
1. Si el POC confirma invariantes y rendimiento base: confirmar stack recomendado.
2. Si falla concurrencia o complejidad operativa: re-evaluar entre opcion A y B con ajustes.
