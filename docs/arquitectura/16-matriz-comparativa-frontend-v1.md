## Matriz Comparativa Frontend v1

Comparativa de alternativas frontend para consumir el backend decidido en Python + FastAPI.

### Objetivo
1. Elegir stack frontend para MVP con foco en velocidad, mantenibilidad y calidad UX.
2. Alinear el frontend con contratos API versionados y envelope estandar de errores.

### Criterios y ponderacion
| Criterio | Peso |
|---|---:|
| Productividad del equipo y curva de aprendizaje | 20% |
| Ecosistema para estado, formularios y validacion | 20% |
| Integracion con OpenAPI/cliente tipado | 15% |
| Mantenibilidad y arquitectura modular | 15% |
| Rendimiento percibido y DX de build | 10% |
| Testing (unitario, integracion, e2e) | 10% |
| Coste operativo para MVP | 10% |

### Opciones evaluadas

#### Opcion A
1. React + TypeScript + Vite
2. Estado server: TanStack Query
3. Formularios: React Hook Form + Zod

#### Opcion B
1. Vue 3 + TypeScript + Vite
2. Estado server: Vue Query
3. Formularios: VeeValidate + Zod/Yup

#### Opcion C
1. Next.js + TypeScript
2. Estado server: TanStack Query o Server Components segun caso
3. Formularios: React Hook Form + Zod

### Scoring inicial (1 a 5) y resultado ponderado
| Criterio | Peso | Opcion A | Opcion B | Opcion C |
|---|---:|---:|---:|---:|
| Productividad y curva | 20 | 5 | 4 | 4 |
| Ecosistema estado/formularios | 20 | 5 | 4 | 5 |
| Integracion OpenAPI tipada | 15 | 5 | 4 | 5 |
| Mantenibilidad modular | 15 | 4 | 4 | 4 |
| Rendimiento y DX build | 10 | 5 | 5 | 4 |
| Testing | 10 | 5 | 4 | 5 |
| Coste operativo MVP | 10 | 5 | 5 | 3 |
| **Total ponderado (/100)** | 100 | **96** | **84** | **86** |

### Lectura de resultados
1. Opcion A lidera por equilibrio entre productividad, ecosistema y simplicidad operativa.
2. Opcion C es fuerte tecnicamente, pero agrega complejidad operativa no esencial para el MVP.
3. Opcion B es viable, especialmente si el equipo tiene experiencia fuerte en Vue.

### Recomendacion inicial frontend
1. Recomendada: Opcion A (React + TypeScript + Vite).
2. Motivo:
   - maximiza velocidad de entrega para MVP.
   - integra facilmente cliente tipado desde OpenAPI.
   - reduce friccion para testing y mantenimiento.

### Requisitos de integracion con backend FastAPI
1. Contrato unico: consumir endpoints versionados /api/v1.
2. Manejo uniforme de errores: mapear envelope de error a mensajes UI por flujo.
3. request_id visible en errores para soporte.
4. Timeouts, retries y cancelacion de requests en operaciones de board.

### Decision y siguiente paso
1. Estado: pendiente de confirmacion por equipo.
2. Siguiente paso: mini POC de frontend (board + crear solicitud + aceptar/rechazar) contra API mock/OpenAPI.
3. Salida esperada: confirmacion final de stack frontend para iniciar Fase 0.
