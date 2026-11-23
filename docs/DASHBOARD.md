# Dashboard conectado

## Ejecutar

Instalar el lock Python y ejecutar `npm ci` desde frontend. Reiniciar el backend para registrar rutas y crear la nueva tabla de resultados; las tablas existentes se conservan. Seguir los dos comandos de ejecución del README. Abrir http://127.0.0.1:5173/.

## Flujo académico

1. Importar `datasets/ml_training_synthetic.csv` desde el formulario. Se guardan las filas completas y se selecciona el lote. Pulsar «Entrenar con este lote» para crear un modelo si no hay uno compatible. Esta acción reemplaza el artefacto local; no evalúa su precisión.
2. Importar `datasets/ml_inference_synthetic.csv` y pulsar «Analizar lote». Es un conjunto posterior, separado de la referencia. También se puede usar el artefacto local ya entrenado mediante CLI.
3. Revisar indicadores, gráficas y tabla. Cambiar nivel de anomalía, buscar identificadores/cuentas y pasar de página.
4. «Todos los lotes» agrega las importaciones existentes. Para entrenar/analizar hay que seleccionar un lote concreto.

**No hay datos simulados en el frontend.** El estado vacío consulta la base real y no fabrica indicadores. Los ejemplos de demostración son CSV sintéticos importados por la misma API y persistidos en SQLite, con aviso visible de uso académico. No se debe importar información bancaria real. No existe un modo que sustituya las respuestas del servidor por fixtures.

## Semántica

- Transacciones analizadas: registros con resultado persistido. Pendientes no se cuentan como normales ni anomalías.
- Anomalías: nivel alto, puntuación >=99. Porcentaje sobre registros analizados; aparece «—» cuando el denominador es cero.
- Monto importado: suma de todos los montos del lote seleccionado, incluidos pendientes, en la moneda única MXN del contrato académico.
- KPI y gráficas representan todo el lote seleccionado. Búsqueda/nivel/paginación solo afectan a la tabla, como indica la pantalla.
- Gráficas Recharts: frecuencia diaria UTC, distribución por rangos de monto y distribución por niveles incluyendo pendientes. Incluyen tooltips y una alternativa textual expandible con los mismos datos.
- Los resultados previos conservan la fecha de su modelo, consultable sobre su puntuación. Al entrenar no se recalculan resultados antiguos. Reanalizar un lote reemplaza sus resultados de forma atómica y conserva las transacciones originales.
- Las puntuaciones son percentiles relativos a referencias específicas, no probabilidades de fraude ni explicaciones causales. Agregar lotes evaluados con distintos modelos sirve para revisión operativa, no comparación de rendimiento.

## API añadida

- `GET /api/transactions/batches`: id, filename, row_count y created_at.
- `GET /api/transactions`: filtro opcional `risk_level=bajo|medio|alto|pendiente`, además de batch_id, search, page y page_size. Devuelve puntuación, nivel y fecha del modelo cuando existe resultado.
- `GET /api/dashboard/summary?batch_id=1`: total, analyzed, pending, anomalies, anomaly_percentage, amount_cents, daily, distribution y amount_distribution. batch_id opcional.
- `GET /api/ml/status`: disponibilidad y metadatos del modelo local configurado.
- `POST /api/ml/train`: JSON `{"batch_id":1}`. Ajuste y calibración temporal mediante el pipeline existente. 404 lote inexistente, 422 datos insuficientes/invalidos, 503 fallo al guardar artefacto.
- `POST /api/ml/analyze`: JSON `{"batch_id":2}`. Carga el modelo existente y persiste inferencia; 404 lote inexistente y 409 si el artefacto no está disponible o no es compatible.

`MODEL_PATH` configura el artefacto local de confianza. Por defecto: backend/artifacts/isolation_forest.joblib. Nunca se acepta un modelo subido por el navegador. Las operaciones ML se serializan dentro del único proceso del MVP; no usar múltiples workers concurrentes sobre el mismo artefacto.

La nueva entidad AnalysisResult tiene una fila por transacción, score, score crudo, nivel, fecha de modelo y fecha del análisis. Se crea por create_all sin alterar entidades existentes. No es un historial de reanálisis: solo se conserva el resultado más reciente por transacción.

## Errores y límites

La interfaz limita CSV a 5 MiB, además de la validación y límites del servidor. No asigna Content-Type manualmente al multipart. Reporta errores del servidor y ofrece reintento si falla la consulta. Cancela consultas obsoletas al cambiar filtros/desmontar y limita las peticiones a 60 segundos. Los controles ML muestran carga y evitan acciones duplicadas. No hay autenticación; servidores enlazados a loopback, sin publicar el sistema.

La carga de gráficas se separa en un fragmento para evitar un paquete inicial grande. La tabla pagina en servidor con 10 filas por página. El resumen agrega en memoria para el MVP local; para grandes volúmenes futuros conviene SQL agregado y límites de rango temporal. Se ejecutó la comparación exploratoria con línea base descrita en EVALUATION.md; validación externa y estudios de carga siguen pendientes.

Referencia de visualización: [Recharts ResponsiveContainer](https://recharts.github.io/en-US/api/ResponsiveContainer/).

Actualización de contrato auditado: los agregados amount_cents de total y daily son cadenas de enteros; el frontend usa BigInt para mantener exactitud monetaria. Ver TECHNICAL.md.
