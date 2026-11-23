# Auditoría funcional y técnica — 13 de noviembre de 2026

## Alcance ejecutado

Revisión de código frontend/backend, parser CSV y límites, SQLite, pipeline/artefactos, contratos API y documentación. Se ejecutaron suites, build, evaluación y recorrido de red real. No equivale a pentest, certificación de accesibilidad o auditoría financiera de producción.

## Hallazgos corregidos

| Hallazgo | Reproducción observada | Corrección y verificación |
| --- | --- | --- |
| P2: enteros demasiado grandes | page=10**30 produjo OverflowError enlazando parámetros SQLite. | Límites en page, ids de rutas/consultas y BatchInput; 6 casos de regresión pasan con 422. |
| P2: centavo perdido en totales | 99 montos válidos sumaban 9899999999999901 centavos; JS mostraba .00 en vez de .01. Pruebas frontend y backend fallaron antes del cambio. | Agregados como string y formateo BigInt/Intl; regresiones backend/frontend pasan. |
| P3: contratos incompletos en OpenAPI | Resumen y rutas ML no declaraban modelos de respuesta. | Modelos Pydantic de resumen, buckets, estado, entrenamiento, análisis y lotes; recorrido HTTP comprobó sus esquemas. |
| P3: documentación obsoleta | README citaba controles de HomePage y documentos declaraban pendiente funcionalidad existente. | README y referencias técnicas actualizadas; historia incremental conservada en PROGRESS.md. |

No se encontraron otros defectos bloqueantes en la revisión acotada de CSV/atomicidad/persistencia. Esto no garantiza ausencia de errores no observados.

## Evidencia ejecutada

| Comprobación | Resultado de esta auditoría |
| --- | --- |
| Backend inicial, antes de cambios | 54 passed en 67.23 s. |
| Frontend inicial | 12 passed y build correcto. |
| Backend final: pytest completo | **64 passed en 25.10 s**, sin advertencias. |
| Frontend final: Vitest completo | **13 passed en 10.37 s**. |
| Build final: TypeScript + Vite | Salida 0; paquete principal ~243 kB y gráficas ~397 kB, sin advertencia de fragmentos grandes. |
| pip check | No broken requirements found. |
| Evaluación CLI | Salida 0; informe con métricas, matrices, versiones y hashes en evaluation/results.json. |
| scripts/audit_http.py | Salida 0; seis grupos de comprobaciones HTTP reales aprobados. |
| Navegador con servidores reiniciados | Dashboard y gráficos con 30 filas persistidas, filtro alto devuelve synthetic-24 con score 100; al quitar filtro reaparecen registros. |

El script HTTP crea Uvicorn sobre loopback y puerto efímero con base y modelo temporales. Comprueba CSV vacío/malformado/grande sin persistencia, carga válida, train/analyze, CORS, resumen, paginación/filtros/detalle y parámetros fuera de rango. Detiene y vuelve a iniciar el proceso, verificando igualdad del resumen y disponibilidad del artefacto. La base y el modelo del usuario no se modifican con ese script. [Evidencia JSON](audit/http_checks.json).

La visualización se revisó contra la base local previamente existente; no se repitió la importación desde el navegador en esta auditoría (sí se ejecutó por HTTP real). La adaptación responsive completa fue comprobada en la etapa anterior, no se presenta como una nueva certificación. [Captura de esta revisión](audit/dashboard.jpg).

## Evaluación del modelo

Ver EVALUATION.md: el bosque obtiene precision 1.0, recall 0.10 y F1 0.1818, con matriz [[20,0],[9,1]]. La regla de monto obtiene precision/recall/F1 1.0, matriz [[20,0],[0,10]]. El umbral del bosque se mantuvo en 99; no se ocultó el rendimiento inferior ni se optimizó con el test. Las etiquetas describen construcción sintética, nunca fraude confirmado. El evaluador tiene pruebas para ausencia de etiquetas, una sola clase y solapamiento temporal.

## Límites de la auditoría

No se ejecutó instalación desde cero en otro equipo, prueba de estrés/concurrencia multiproceso, pentest, escaneo independiente completo de vulnerabilidades, lectura con lector de pantalla ni medición cronometrada de exposición oral. No se evalúan datos bancarios reales. Persisten los límites de LIMITATIONS.md. La entrega es un MVP académico funcional con evaluación exploratoria, no un detector validado para producción.
