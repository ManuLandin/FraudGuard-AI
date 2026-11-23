# Evaluación reproducible — 13 de noviembre de 2026

## Diseño y datos

Se ejecutó `app.ml.evaluation` sobre los archivos existentes `ml_training_synthetic.csv` y `ml_inference_synthetic.csv`. Todos los datos son sintéticos. `label=1` significa monto atípico por construcción del ejemplo; **no fraude confirmado**. La referencia tiene 240 filas: 180 para ajustar y 60 posteriores para calibrar el percentil. La prueba tiene 30 filas: 20 normales y 10 atípicas.

El último registro de referencia es 2026-08-28; la prueba empieza en 2027-01-01. Las fechas futuras son parte del ejemplo inventado. El evaluador rechaza cualquier solapamiento temporal. La prueba no participa en fit, calibración ni elección de umbrales. Estos ejemplos ya habían sido inspeccionados durante el desarrollo: es una evaluación académica exploratoria reproducible, no un benchmark ciego independiente.

Se mantiene el umbral preexistente score>=99. La línea base marca monto superior al percentil 99 de las 180 filas de ajuste (10937.09 centavos), calculado sin etiquetas de prueba. Ambos métodos se evalúan sobre exactamente las mismas etiquetas.

## Resultados ejecutados

| Método | Precision | Recall | F1 | ROC-AUC | Average precision |
| --- | ---: | ---: | ---: | ---: | ---: |
| Isolation Forest, score>=99 | 1.0000 | 0.1000 | 0.1818 | 0.9150 | 0.8326 |
| Línea base de monto | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

Matrices con filas=real y columnas=predicción; orden [normal, atípico]:

```text
Isolation Forest          Línea base
            Pred 0 Pred 1             Pred 0 Pred 1
Real 0         20      0   Real 0         20      0
Real 1          9      1   Real 1          0     10
```

La precisión 1.0 del bosque procede de **una sola predicción positiva** y no compensa los nueve atípicos omitidos. La línea base gana en este conjunto. Sus etiquetas están definidas por montos extremos, lo que favorece una regla de monto; no demuestra superioridad general de esa regla. El bosque combina otras variables y tiene limitada extrapolación fuera del rango observado. Un buen ranking global no garantiza recall en un umbral conservador. No se ajustó el umbral después de observar estos resultados.

ROC-AUC y AP usan -score_samples para Isolation Forest y monto para la línea base, sin convertirlos a probabilidades. AP resume el ranking precision–recall; no se presenta como área trapezoidal de la curva PR. Se incluyen ambas métricas de ranking y las de decisión, evitando usar accuracy como medida principal.

## Etiquetas y casos no evaluables

Solo se incluyen en métricas las filas con etiqueta disponible; todas las filas se puntúan. Sin etiquetas, las métricas y matriz son null. Con una sola clase se omiten ROC-AUC y AP; sin positivos reales recall y F1 son null. Precision es null cuando no hay predicciones positivas. No se sustituyen métricas indefinidas por resultados favorables. Las etiquetas inválidas se rechazan.

## Reproducir

Desde la raíz:

```powershell
Push-Location backend
..\.venv\Scripts\python.exe -m app.ml.evaluation --reference ../datasets/ml_training_synthetic.csv --test ../datasets/ml_inference_synthetic.csv --output ../docs/evaluation/results.json
Pop-Location
```

[Informe JSON completo](evaluation/results.json): tamaños, fechas, semilla, versiones, matrices, umbral y SHA-256 de ambos archivos. Se entrena un modelo temporal en memoria; no reemplaza el artefacto del dashboard ni modifica SQLite. Las pruebas cubren partición temporal inválida, etiquetas ausentes/invalidas y una sola clase.

## Interpretación y próximos experimentos

Treinta filas y diez positivos no permiten estimar rendimiento real ni estabilidad. No se han calculado intervalos de confianza, pruebas de significación, validación cruzada temporal múltiple ni desempeño por subpoblación. Para una evaluación posterior: diseñar datos sintéticos diversos antes de evaluar, definir costes de falsos positivos/negativos, calibrar umbrales en validación y reservar una prueba nueva que no se inspeccione hasta fijar decisiones. No usar datos bancarios reales en este MVP.

Definiciones contrastadas con [métricas scikit-learn](https://scikit-learn.org/stable/modules/model_evaluation.html) y [average_precision_score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html).

## Evaluación posterior del dataset de 1,000 filas

El experimento anterior se mantiene como registro reproducible de los ejemplos iniciales. Para la nueva simulación con cinco familias de anomalías, partición temporal y errores individuales, ver DATASET_DEMO.md y evaluation/demo_1000/results.json. Las métricas de ambos experimentos no son intercambiables ni pruebas de generalización.
