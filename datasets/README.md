# Datos de demostración

Esta carpeta queda reservada para un dataset **sintético** y su generador reproducible en la fase 2. La fase 1 no contiene ni analiza transacciones.

No colocar información bancaria real. Los archivos generados se guardarán en `datasets/generated/`, excluida de Git. Se documentarán esquema CSV, semilla, distribución, etiquetas artificiales y limitaciones cuando se implemente el generador.

## Ejemplo de importación

`example_synthetic.csv` contiene dos filas inventadas para probar el contrato CSV. Su label es ilustrativo y no describe fraude confirmado. No constituye un dataset de entrenamiento o evaluación. El generador reproducible sigue pendiente.

## Ejemplos de Machine Learning

`ml_training_synthetic.csv` tiene 240 filas inventadas de montos normales y `ml_inference_synthetic.csv` 30 filas posteriores, incluyendo montos extremos. Ambos son exclusivamente sintéticos y sus etiquetas describen cómo se construyeron los ejemplos; no prueban fraude ni constituyen una evaluación financiera. Ver docs/ML_MODEL.md para comandos y límites.

## Demo de 1,000 operaciones

Dataset principal: fraudguard_demo_1000.csv (900 normales/100 anomalías). Regenerar desde la raíz con `.\.venv\Scripts\python.exe datasets/generate_demo.py`. Incluye particiones cronológicas reference/test y manifiesto con semilla/hash/familias. Evaluar con datasets/evaluate_demo.py. Todos los datos son ficticios; ver docs/DATASET_DEMO.md para contratos, carga y limitaciones.
