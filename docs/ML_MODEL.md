# Modelo de anomalías

## Uso

Instalar el lock actualizado desde la raíz. Solo datos sintéticos; los ejemplos incluidos son inventados, no información bancaria real.

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.lock.txt
Push-Location backend
..\.venv\Scripts\python.exe -m app.ml train --csv ../datasets/ml_training_synthetic.csv --model artifacts/isolation_forest.joblib
..\.venv\Scripts\python.exe -m app.ml analyze --csv ../datasets/ml_inference_synthetic.csv --model artifacts/isolation_forest.joblib --output artifacts/demo_results.json
Pop-Location
```

`train` valida CSV, ajusta y guarda; `analyze` valida otro CSV, carga y puntúa sin ajustar. Se reutilizan contrato y límites de importación. No se modifica SQLite ni se guardan estos resultados en sus tablas. El JSON conserva transaction_id, fecha del modelo, puntuaciones y aviso de interpretación. Los endpoints ML y la integración visual se implementarán después.

Los archivos de ejemplo contienen 240 observaciones de referencia y 30 de inferencia posterior (20 montos normales y 10 extremos); sus etiquetas describen la construcción sintética, no fraudes. Su sencillez no representa un escenario financiero real. El ejemplo anterior de dos filas sigue sirviendo para importación, pero es insuficiente para entrenar.

## Pipeline y partición

API Python: `train(DataFrame, seed=42) -> AnomalyModel`, `infer(model, DataFrame) -> DataFrame`, `save_model(model, Path)` y `load_model(Path)`. La entrada usa amount_cents entero positivo y timestamp con zona horaria; campos adicionales como label y account_id quedan excluidos.

Se normalizan fechas a UTC y se ordenan establemente por timestamp. El primer 75% ajusta; el tramo final calibra. Los timestamps iguales al punto de corte van juntos a calibración. Se requieren al menos 80 filas totales, 40 de ajuste y 20 de calibración; si las fechas impiden separarlos se rechaza el entrenamiento.

El transformador scikit-learn produce cinco variables: log1p(amount_cents / 100), seno/coseno de hora (incluye minutos y segundos) y seno/coseno de día de semana UTC. No requiere escalador: el bosque divide por variable y rango, y la transformación es fija, sin estadísticas calculadas del lote de inferencia. Se rechazan faltantes, montos no finitos/no enteros y fechas sin zona.

IsolationForest usa 200 árboles, max_samples=min(256, filas de ajuste), random_state=42, n_jobs=1 y contamination=auto. No se usa predict() ni su umbral automático para la decisión final; el umbral procede de la puntuación calibrada descrita abajo. Las etiquetas nunca participan en ajuste, selección de variables ni calibración.

La frecuencia queda pendiente de una definición causal basada en historial por cuenta. Contar operaciones de un lote completo consultaría registros futuros y cambiaría resultados al agrupar solicitudes. Esta versión evita ese cálculo. El score de una fila es independiente de las demás filas del lote.

## Puntuación e interpretación

Se define `r(x) = -pipeline.score_samples(x)`: valores mayores indican mayor anomalía. La referencia R contiene únicamente los valores r de las filas de calibración, ordenados. La puntuación es:

`score(x) = 100 * (cantidad(R < r(x)) + 0.5 * cantidad(R == r(x))) / len(R)`

Es un percentil empírico de rango medio, limitado a [0,100]. Un empate con una referencia completamente constante da 50, no 100. Un valor superior al máximo da 100. No se recalibran rangos ni se hace min-max sobre el lote de inferencia.

- Bajo: score <95.
- Medio: 95 <= score <99.
- Alto: score >=99. También define is_anomaly=true.

Los niveles son orientativos, no validación clínica, bancaria ni decisión automática. **La puntuación no es una probabilidad de fraude. Las anomalías no son fraudes confirmados.** No se atribuyen causas ni explicaciones a variables concretas.

## Artefacto reproducible

joblib conserva el Pipeline, referencia de calibración, número de filas, límites temporales, semilla, fecha de creación y versiones de Python/scikit-learn/NumPy/pandas/joblib. La carga rechaza esquema, versiones y referencia incompatibles. La escritura usa un temporal en el mismo directorio y reemplazo atómico: un lector no observa medio archivo. Usar el lock de entrenamiento para volver a cargarlo. La reproducibilidad se refiere a resultados con los mismos datos/orden, semilla y entorno, no al hash binario o fecha de creación del archivo.

Solo se cargan artefactos locales de confianza: joblib puede ejecutar código durante la deserialización. La comprobación de esquema posterior no vuelve seguro un archivo malicioso. No hay endpoint de subida de modelos. CSV y artefactos se mantienen separados; los comandos rechazan rutas coincidentes de entrada/modelo/salida.

## Límites y evaluación pendiente

La calibración no es un conjunto de evaluación independiente. Una evaluación defendible necesita otro tramo temporal sin reutilizarlo para entrenar, calibrar o seleccionar umbrales, comparación con línea base y métricas con etiquetas válidas. Las pruebas de comportamiento no constituyen métricas; la evaluación separada ejecutada después se documenta en EVALUATION.md.

El percentil es discreto y depende del tamaño y calidad de la referencia; al menos 20 filas es un mínimo técnico, no una calibración robusta. Contaminación de referencia, deriva temporal, moneda mezclada o población distinta pueden producir errores. UTC pierde contexto horario local. Isolation Forest no extrapola la magnitud fuera del rango observado y no garantiza marcar todos los montos extremos; se comprobó esta limitación al ejecutar las pruebas. Se requiere revisión humana, nunca bloqueo automático.

Referencias: [IsolationForest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html) y [prevención de fuga de información](https://scikit-learn.org/stable/common_pitfalls).

## Integración posterior disponible

Además de CLI, ya están disponibles endpoints train/analyze/status y dashboard React. Los resultados se guardan en AnalysisResult; el modelo y la fórmula no cambian. Ver docs/DASHBOARD.md. La comparación exploratoria con la línea base y sus matrices están documentadas en EVALUATION.md; validación externa sigue pendiente.
