# Resultados — Prueba de Carga (50 usuarios)

**Herramienta:** Apache JMeter 5.6.3  
**Escenario:** 50 usuarios concurrentes · duración 60 s  
**Periodo:** 2026-11-09T23:08:25.028000+00:00 a 2026-11-09T23:09:24.563000+00:00  
**Endpoints:** login JWT, catálogo completo, filtro Cómputo, estadísticas y reservas del estudiante.

## Resumen general

| Métrica | Valor | Umbral SLA | Estado |
|---|---:|---:|:---:|
| Peticiones totales | 79,424 | — | Informativo |
| Errores HTTP | 0 (0.00 %) | ≤ 1.0 % | Cumple |
| Throughput promedio | 1334.07 req/s | — | Informativo |
| Tiempo promedio | 34.4 ms | — | Informativo |
| Mediana (p50) | 34.0 ms | ≤ 3000 ms | Conforme |
| Percentil 90 (p90) | 42.0 ms | ≤ 3000 ms | Conforme |
| Percentil 95 (p95) | 48.0 ms | ≤ 3000 ms | Cumple |
| Percentil 99 (p99) | 89.0 ms | — | Informativo |
| Tiempo máximo | 230.0 ms | — | Informativo |
| Desviación estándar | 11.8 ms | — | Informativo |

## Detalle por transacción

| Transacción | Muestras | Promedio | p50 | p90 | p95 | p99 | Throughput | Error % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| GET /api/equipment | 19865 | 34.5 ms | 34.0 ms | 43.0 ms | 49.0 ms | 89.0 ms | 333.67 rps | 0.00 % |
| GET /api/equipment/stats | 19836 | 34.4 ms | 34.0 ms | 42.0 ms | 48.0 ms | 88.0 ms | 333.18 rps | 0.00 % |
| GET /api/equipment?category=Cómputo | 19848 | 34.3 ms | 34.0 ms | 42.0 ms | 48.0 ms | 88.5 ms | 333.38 rps | 0.00 % |
| GET /api/reservations/me | 19825 | 34.3 ms | 33.0 ms | 42.0 ms | 48.0 ms | 88.0 ms | 333.00 rps | 0.00 % |
| POST /api/auth/login | 50 | 113.5 ms | 104.5 ms | 153.2 ms | 160.8 ms | 204.5 ms | 0.84 rps | 0.00 % |
| **TOTAL GENERAL** | **79424** | **34.4 ms** | **34.0 ms** | **42.0 ms** | **48.0 ms** | **89.0 ms** | **1334.07 rps** | **0.00 %** |

## Veredicto

**APROBADA: tasa de error (0.0 %) dentro del umbral (1.0 %) y percentil 95 (48.0 ms) dentro del umbral (3000 ms).**

## Artefactos generados

- Tabla de resultados CSV: `carga/resultados_tabla.csv`
- Métricas estructuradas JSON: `carga/summary.json`
- Gráficas generadas:
  - `charts/response-time.png` (evolución en el tiempo del promedio y p95)
  - `charts/percentiles.png` (distribución de percentiles p50 a p99)
  - `charts/throughput.png` (peticiones por segundo vs usuarios concurrentes)
  - `charts/errors.png` (evolución de errores HTTP)
