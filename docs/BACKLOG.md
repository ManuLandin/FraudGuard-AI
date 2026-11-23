# Backlog y plan de tres semanas

Solo la fase 1 se ejecuta en esta entrega. Las fases siguientes requieren una nueva instrucción.

| Fase | Semana orientativa | Entregable y criterio de aceptación |
| --- | --- | --- |
| 1. Base ejecutable | 1 | Estructura modular, configuración, `/health`, página React responsive en español y conexión comprobada; pytest, Vitest y build correctos. |
| 2. Ingesta y persistencia | 1 | Contrato CSV documentado, límites y validación, previsualización, lotes y transacciones SQLite con SQLAlchemy, generador sintético reproducible; pruebas de archivos válidos y adversos. |
| 3. Modelo y evaluación | 1–2 | Isolation Forest con pipeline reproducible, separación de entrenamiento/inferencia/evaluación, artefactos joblib, puntuaciones y umbrales documentados, comparación con línea base y métricas condicionadas a etiquetas. |
| 4. Dashboard y entrega | 2–3 | Indicadores, Recharts, búsqueda/filtros/paginación, estados y accesibilidad, integración de punta a punta, revisión de limitaciones y guion académico de tres minutos. |

## API pendiente

- `POST /api/transactions/upload`: validación y registro de lotes.
- `GET /api/transactions`: filtros y paginación.
- `GET /api/transactions/{id}`: detalle.
- `GET /api/dashboard/summary`: agregaciones.
- `POST /api/ml/train`: entrenamiento separado.
- `POST /api/ml/analyze`: inferencia sobre lotes.
- `GET /api/ml/status`: versión y disponibilidad del artefacto.

## Prioridad

Completar primero un recorrido CSV → validación → IA → resultados → dashboard. Mantener fuera del MVP bancos reales, pagos, autenticación compleja y microservicios. No usar información bancaria real. Identificar explícitamente todos los datos sintéticos.

## Estado al 13 de noviembre de 2026

MVP de ingesta, modelo, dashboard e integración implementado. Comparación exploratoria contra línea base, informe de auditoría y guion de demo añadidos. Validación externa, estudios de carga, accesibilidad exhaustiva, historial/migraciones y mejoras del modelo quedan como trabajo posterior documentado en LIMITATIONS.md. El registro inicial de fases se mantiene como planificación histórica.
