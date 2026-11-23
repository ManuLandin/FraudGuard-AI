# Demostración académica de tres minutos

## Preparación fuera del tiempo de exposición

Iniciar backend y frontend siguiendo README. Comprobar /health, abrir dashboard y localizar los CSV de datasets. Tener un modelo compatible preparado (por CLI o con el lote de referencia) para no depender del tiempo de entrenamiento. Seleccionar el lote recién importado: los lotes de pruebas anteriores pueden seguir en SQLite. No borrar datos para preparar la demo. Abrir EVALUATION.md junto al dashboard. Ensayar el guion; **no se ha cronometrado una presentación oral**.

## 0:00–0:25 · Problema y alcance

Mostrar título y aviso académico. Decir: «FraudGuard AI explora transacciones sintéticas y señala operaciones atípicas para revisión. No confirma fraudes ni ejecuta decisiones financieras. Se ejecuta localmente, sin bancos ni servicios de pago».

## 0:25–0:55 · Ingesta y persistencia

Importar ml_inference_synthetic.csv desde el formulario. Mostrar confirmación y 30 registros. Decir: «La API valida encabezados, montos, zona horaria, tamaño y estructura CSV. Si una fila falla, no guarda parte del lote. Los montos se conservan en centavos y el lote persiste en SQLite».

Si falla un archivo, leer el error y mostrar que no apareció un lote nuevo. No prometer formato Excel ni previsualización previa al guardado.

## 0:55–1:25 · Modelo

Mostrar el panel del modelo y pulsar Analizar lote. Decir: «Se carga un pipeline ya entrenado: logaritmo del monto y variables cíclicas de hora/día alimentan Isolation Forest. El ajuste usa un tramo temporal; otro tramo posterior calibra la referencia. Analizar no vuelve a entrenar. Los resultados guardan la fecha del modelo».

Señalar que Entrenar con este lote requiere un CSV de referencia de al menos 80 filas; no entrenar con las 30 filas de prueba.

## 1:25–2:05 · Dashboard

Mostrar KPI, las tres gráficas y sus tooltips. Filtrar nivel Alto en la tabla, buscar synthetic-24 y cambiar páginas tras quitar el filtro. Decir: «El score es un percentil respecto de la referencia. Alto es >=99; medio >=95. No es una probabilidad. Los indicadores describen el lote completo y los filtros inferiores afectan solo a la tabla. Los pendientes no se consideran normales».

Con el modelo predeterminado y archivos originales se observó 1/30 en nivel alto. Si se ha reentrenado el modelo, describir lo observado en pantalla y no repetir cifras como si fueran invariantes.

## 2:05–2:45 · Evaluación honesta

Abrir EVALUATION.md. Decir: «En 30 ejemplos sintéticos posteriores, de los cuales diez fueron construidos como atípicos, el bosque tuvo precision 1.0, recall 0.10 y F1 0.182. La precisión proviene de una sola alerta. Omitió nueve casos. Una línea base de monto obtuvo mejor resultado; el ejemplo está construido precisamente con montos extremos. No ajusté el umbral con esas etiquetas ni extrapolo estas cifras a banca real».

Mostrar matrices para explicar falsos negativos. Aclarar que la referencia de calibración no fue el conjunto de prueba y que estos ejemplos ya habían sido inspeccionados durante desarrollo.

## 2:45–3:00 · Defensa técnica y límites

Decir: «La entrega incluye pruebas automatizadas de frontend/backend y un recorrido HTTP real con reinicio y persistencia. La prioridad siguiente sería datos sintéticos más diversos y evaluación temporal adicional. Es un MVP académico local: no es un sistema bancario de producción».

## Preguntas previsibles

- ¿Por qué SQLite? Un proceso local y plazo académico; simplicidad sin microservicios.
- ¿Por qué Isolation Forest? Método no supervisado para explorar observaciones raras; no necesita etiquetas para entrenar. La comparación demuestra que más complejidad no garantiza mejorar una línea base.
- ¿Por qué pierde casos extremos? Los árboles no extrapolan magnitud fuera de rango y el score mezcla variables; el umbral 99 es conservador. Cambiarlo necesitaría validación separada, no elegirlo sobre la prueba.
- ¿Qué protege contra fuga? Partición temporal, transformador fijo dentro del pipeline, calibración separada y etiquetas excluidas. El evaluador rechaza pruebas anteriores o solapadas.
