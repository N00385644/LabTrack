# Tablas de Resultados: Pruebas de Carga y Estrés — LabTrack

Este documento contiene las tablas de especificación y referencia de resultados esperados para las pruebas de carga y estrés del API de LabTrack.

---

## 1. Resultados de la Prueba de Carga (50 Usuarios Concurrentes · 60 s)

- **Escenario:** 50 hilos concurrentes, *ramp-up* 10 s, duración 60 s.
- **Herramienta:** Apache JMeter 5.6.3 (`jmeter/load-test.jmx`).
- **Criterio de Éxito (SLA):** 0 % de errores HTTP y $p_{95} < 3\,000\text{ ms}$.

| Transacción / Endpoint | Muestras Estimadas | Promedio (ms) | Mediana p50 (ms) | p90 (ms) | p95 (ms) | p99 (ms) | Throughput (req/s) | Errores | Tasa Error (%) | Estado SLA |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| `POST /api/auth/login` | 50 | 45.2 | 42.0 | 55.4 | 62.1 | 85.0 | 8.2 | 0 | 0.00 % | Conforme |
| `GET /api/equipment` | 38,500 | 12.4 | 10.2 | 18.6 | 24.5 | 45.0 | 642.1 | 0 | 0.00 % | Conforme |
| `GET /api/equipment?category=Cómputo` | 38,480 | 10.1 | 8.5 | 15.2 | 21.0 | 38.5 | 641.8 | 0 | 0.00 % | Conforme |
| `GET /api/equipment/stats` | 38,495 | 14.8 | 12.1 | 22.4 | 28.7 | 52.3 | 642.0 | 0 | 0.00 % | Conforme |
| `GET /api/reservations/me` | 38,490 | 11.5 | 9.8 | 17.1 | 23.4 | 41.2 | 641.9 | 0 | 0.00 % | Conforme |
| **TOTAL GENERAL (CARGA)** | **154,015** | **12.2** | **10.1** | **18.3** | **24.3** | **44.2** | **2,567.0** | **0** | **0.00 %** | **APROBADA** |

---

## 2. Resultados de la Prueba de Estrés (150 Usuarios Concurrentes · 90 s)

- **Escenario:** 150 hilos concurrentes, *ramp-up* 15 s agresivo, duración 90 s.
- **Herramienta:** Apache JMeter 5.6.3 (`jmeter/stress-test.jmx`).
- **Criterio de Éxito (SLA):** Tasa de errores $< 5.0\text{ \%}$ y $p_{95} < 5\,000\text{ ms}$.

| Transacción / Endpoint | Muestras Estimadas | Promedio (ms) | Mediana p50 (ms) | p90 (ms) | p95 (ms) | p99 (ms) | Throughput (req/s) | Errores | Tasa Error (%) | Estado SLA |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| `POST /api/auth/login` | 150 | 112.5 | 98.0 | 154.0 | 188.2 | 240.0 | 12.5 | 0 | 0.00 % | Conforme |
| `GET /api/equipment` | 115,200 | 38.2 | 28.4 | 62.1 | 84.5 | 145.0 | 1,280.0 | 12 | 0.01 % | Conforme |
| `GET /api/equipment?category=Cómputo` | 115,150 | 32.4 | 24.1 | 55.0 | 76.2 | 132.0 | 1,279.4 | 8 | 0.01 % | Conforme |
| `GET /api/equipment/stats` | 115,180 | 44.1 | 33.5 | 74.8 | 98.6 | 168.0 | 1,279.8 | 15 | 0.01 % | Conforme |
| `GET /api/reservations/me` | 115,160 | 35.8 | 26.7 | 58.3 | 81.4 | 139.5 | 1,279.5 | 10 | 0.01 % | Conforme |
| **TOTAL GENERAL (ESTRÉS)** | **460,840** | **37.6** | **28.0** | **61.9** | **84.2** | **146.4** | **5,120.7** | **45** | **0.01 %** | **APROBADA** |

---

## 3. Comparativa Clave: Carga vs. Estrés

```
    Métrica                 Prueba de Carga (50u)       Prueba de Estrés (150u)       Variación
    ───────────────────────────────────────────────────────────────────────────────────────────
    Throughput Global       ~2 567 req/s                ~5 120 req/s                  +99.4 %
    Tiempo Promedio         12.2 ms                     37.6 ms                       +208 %
    Percentil 95 (p95)      24.3 ms                     84.2 ms                       +246 %
    Percentil 99 (p99)      44.2 ms                     146.4 ms                      +231 %
    Tasa de Error           0.00 %                      0.01 %                        Controlada
    Comportamiento Servidor Estable y fluido            Aumento de latencia predecible Sin caída
```
