# Resultados — Prueba de EstrÃ©s (150 usuarios)

**Herramienta:** Apache JMeter 5.6.3  
**Escenario:** 150 usuarios concurrentes · duración 90 s  
**Periodo:** 2026-11-09T23:09:41.410000+00:00 a 2026-11-09T23:11:11.195000+00:00  
**Endpoints:** login JWT, catálogo completo, filtro Cómputo, estadísticas y reservas del estudiante.

## Resumen general

| Métrica | Valor | Umbral SLA | Estado |
|---|---:|---:|:---:|
| Peticiones totales | 113,600 | — | Informativo |
| Errores HTTP | 0 (0.00 %) | ≤ 5.0 % | Cumple |
| Throughput promedio | 1265.24 req/s | — | Informativo |
| Tiempo promedio | 108.9 ms | — | Informativo |
| Mediana (p50) | 101.0 ms | ≤ 5000 ms | Conforme |
| Percentil 90 (p90) | 132.0 ms | ≤ 5000 ms | Conforme |
| Percentil 95 (p95) | 151.0 ms | ≤ 5000 ms | Cumple |
| Percentil 99 (p99) | 381.0 ms | — | Informativo |
| Tiempo máximo | 1072.0 ms | — | Informativo |
| Desviación estándar | 47.9 ms | — | Informativo |

## Detalle por transacción

| Transacción | Muestras | Promedio | p50 | p90 | p95 | p99 | Throughput | Error % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| GET /api/equipment | 28421 | 108.9 ms | 101.0 ms | 133.0 ms | 152.0 ms | 380.0 ms | 316.55 rps | 0.00 % |
| GET /api/equipment/stats | 28345 | 108.3 ms | 101.0 ms | 131.0 ms | 150.0 ms | 374.0 ms | 315.70 rps | 0.00 % |
| GET /api/equipment?category=Cómputo | 28377 | 108.4 ms | 101.0 ms | 132.0 ms | 150.0 ms | 380.2 ms | 316.06 rps | 0.00 % |
| GET /api/reservations/me | 28307 | 108.1 ms | 101.0 ms | 132.0 ms | 150.0 ms | 369.0 ms | 315.28 rps | 0.00 % |
| POST /api/auth/login | 150 | 461.2 ms | 402.5 ms | 891.7 ms | 963.3 ms | 1033.4 ms | 1.67 rps | 0.00 % |
| **TOTAL GENERAL** | **113600** | **108.9 ms** | **101.0 ms** | **132.0 ms** | **151.0 ms** | **381.0 ms** | **1265.24 rps** | **0.00 %** |

## Veredicto

**APROBADA: tasa de error (0.0 %) dentro del umbral (5.0 %) y percentil 95 (151.0 ms) dentro del umbral (5000 ms).**

## Artefactos generados

- Tabla de resultados CSV: `estres/resultados_tabla.csv`
- Métricas estructuradas JSON: `estres/summary.json`
- Gráficas generadas:
  - `charts/response-time.png` (evolución en el tiempo del promedio y p95)
  - `charts/percentiles.png` (distribución de percentiles p50 a p99)
  - `charts/throughput.png` (peticiones por segundo vs usuarios concurrentes)
  - `charts/errors.png` (evolución de errores HTTP)
