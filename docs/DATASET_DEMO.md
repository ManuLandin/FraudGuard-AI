# Dataset de demostración de 1,000 transacciones

## Alcance y reproducibilidad

Archivo: `datasets/fraudguard_demo_1000.csv`. Contiene exactamente **900 normales y 100 anomalías de referencia**, todas ficticias. Negocio simulado: compra de insumos y pagos de una pequeña papelería/cafetería mexicana. No se usaron datos bancarios, nombres personales, cuentas ni ubicaciones reales. Los montos están en MXN.

Generador Python con pandas y NumPy, `random_state=42`, periodo fijo de 90 días: del 1 de agosto de 2026 al 30 de octubre exclusivo, zona -06:00. Orden cronológico, identificadores únicos permutados para no codificar la clase en ellos, montos positivos redondeados a dos decimales y marcas de tiempo con zona explícita. El entorno reproducible está fijado en requirements.lock.txt. Reproducibilidad byte a byte comprobada con esa semilla y entorno; no se promete identidad entre versiones arbitrarias de bibliotecas.

Desde la raíz:

```powershell
.\.venv\Scripts\python.exe datasets/generate_demo.py
```

Opciones: `--seed 42` y `--output ruta/demo.csv`. Cambiar semilla cambia los datos y puede cambiar tamaños de particiones y métricas; las cifras de este documento corresponden únicamente a 42.

El mismo comando genera CSV principal, particiones `_reference.csv` y `_test.csv`, y manifiesto `.manifest.json` con semilla, periodo, corte, hash SHA-256 y familia de cada registro. Las familias son trazabilidad de la simulación y se usan solo en diagnóstico, nunca como entrada del modelo.

## Esquema e integración

| Columna del CSV | Uso |
| --- | --- |
| transaction_id | ID único sintético, sin prefijo de clase. |
| user_id | Uno de 18 usuarios ficticios con perfil estable; alias de account_id en backend. |
| amount | MXN, convertido a amount_cents entero al importar. |
| timestamp | ISO 8601 -06:00; backend lo normaliza a UTC. |
| transaction_type | compra, transferencia, retiro o pago. |
| merchant_category | Categorías ficticias de abastecimiento/servicios. |
| location | Zona general explícitamente ficticia. |
| is_anomaly | Referencia 0/1, alias de label. No es predicción. |

El backend sigue aceptando el CSV anterior con account_id/label. Si llegan ambos nombres de un alias, deben coincidir; no se permite sustituir silenciosamente etiquetas. Se validan tipo de operación, textos de hasta 100 caracteres, nulos/caracteres de control y el contrato anterior. Los metadatos se conservan en la nueva tabla TransactionContext vinculada 1:1; no se alteran ni eliminan tablas o transacciones existentes. Las respuestas añaden campos opcionales user_id/is_anomaly/tipo/categoría/ubicación. Las puntuaciones siguen viniendo de AnalysisResult.

`is_anomaly` se usa exclusivamente como etiqueta de referencia para evaluación/demostración. No entra a Isolation Forest, no define score ni riesgo y no se usa para escoger filas normales al entrenar. La importación no convierte automáticamente una etiqueta 1 en una alerta del modelo.

## Construcción de comportamientos

Cada usuario tiene un monto central entre 95 y 680 MXN, dos categorías preferidas, zona habitual y horario central propio. Los montos habituales siguen una lognormal (sigma .46), con variación natural; horas comerciales alrededor del perfil, fechas aleatorias con menor actividad en fines de semana, selección probabilística de tipo y zona, y separación razonable entre operaciones normales del mismo usuario.

Se inyectan exactamente veinte observaciones de cada familia:

1. **Monto alto:** multiplicador de 9 a 18 respecto de una operación habitual del usuario.
2. **Horario inusual:** madrugada de 00:00 a 05:59 local con monto habitual.
3. **Ráfaga:** cuatro grupos de cinco operaciones del mismo usuario con intervalos de 15 a 60 segundos, montos y categorías habituales.
4. **Cambio de patrón:** categorías fuera de preferencias, otra zona y retiro/transferencia; el monto puede seguir siendo habitual.
5. **Combinada:** madrugada, cambio de categoría/zona y aumento de monto de 3 a 7 veces.

La etiqueta se fija por la intervención sintética antes de ejecutar el modelo. No se modifica según scores. Hay solapamiento de montos entre clases; las anomalías no son separables todas por una regla de monto. Estos supuestos son plausibles para una demo, no estimaciones empíricas de un negocio real.

## Cargar las 1,000 filas en la plataforma

1. Reiniciar el backend con las dependencias existentes para crear la tabla de metadatos y cargar el parser actualizado. No borrar la base:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

2. Iniciar React desde frontend con `npm run dev` y abrir http://127.0.0.1:5173/.
3. En **Importa tus transacciones**, seleccionar `datasets/fraudguard_demo_1000.csv` y pulsar **Importar CSV**. El lote debe informar 1,000 registros; inicialmente están pendientes de análisis. La tabla se pagina y muestra el usuario mediante account_id adaptado. Los metadatos también pueden consultarse en detalle API.
4. Seleccionar el lote para explorarlo. Analizar las 1,000 filas sirve para demostración, pero si el modelo se entrenó con parte de ellas, esos resultados completos no constituyen evaluación independiente.

Alternativa HTTP, con backend actualizado iniciado:

```powershell
curl.exe -F "file=@datasets/fraudguard_demo_1000.csv" http://127.0.0.1:8000/api/transactions/upload
```

Reimportar crea otro lote. Los IDs son únicos dentro del archivo, no se deduplican entre lotes; no importar principal y particiones esperando que el total global siga siendo 1,000.

## Partición y evaluación sin fuga

El corte se fija al día 63 (3 de octubre de 2026, 00:00 -06:00), sin consultar etiquetas. Para semilla 42:

- Referencia: 709 filas, 73 anomalías de referencia. El modelo ajusta con las primeras 531 y calibra con las 178 posteriores.
- Prueba: 291 filas posteriores, 264 normales y 27 anomalías.
- Ningún ID/timestamp cruza la partición. Las proporciones no se fuerzan por partición.

No se filtra la referencia para dejar solo normales: es entrenamiento no supervisado con posible contaminación. No se ajustan variables ni umbrales usando etiquetas de prueba. Para reproducir:

```powershell
.\.venv\Scripts\python.exe datasets/evaluate_demo.py
```

El evaluador comprueba el hash del CSV, deriva el corte del manifiesto, reutiliza el pipeline actual y guarda métricas, predicciones y errores en `docs/evaluation/demo_1000/`. No modifica la base ni reemplaza el modelo de la plataforma. Los resultados distinguen `reference_is_anomaly` de `predicted_is_anomaly`; no sobrescriben la etiqueta fuente.

Para demostrar entrenamiento e inferencia separados en la UI, importar `_reference.csv`, entrenar ese lote y después importar y analizar `_test.csv`. También puede entrenarse el modelo local con el comando CLI existente y `_reference.csv`. No entrenar con el CSV completo y presentar las métricas de las mismas filas como prueba independiente.

## Resultados ejecutados sobre la prueba

| Método | Precision | Recall | F1 | ROC-AUC | Average precision |
| --- | ---: | ---: | ---: | ---: | ---: |
| Isolation Forest, umbral 99 | 1.0000 | 0.2222 | 0.3636 | 0.8130 | 0.5701 |
| Línea base de monto | 1.0000 | 0.1111 | 0.2000 | 0.7663 | 0.4822 |

Matriz Isolation Forest: filas=real, columnas=predicción; orden [normal, anomalía]:

```text
             Pred normal  Pred anomalía
Real normal       264          0
Real anomalía      21          6
```

Falsos positivos: **0** (CSV de errores vacío con encabezados). Falsos negativos: **21**, identificados individualmente en false_negatives.csv y results.json. La línea base tiene 24 falsos negativos y 0 falsos positivos. No se presentan como fraudes ni como rendimiento garantizado.

Por familia en prueba: cambios de patrón 0/5 detectados, combinadas 4/7, horario inusual 2/3, monto alto 0/7 y ráfagas 0/5. El modelo actual solo observa monto/hora/día UTC, no categorías, ubicación, usuario ni frecuencia causal. Su referencia contiene anomalías y su umbral es conservador. Estas limitaciones explican por qué no debe esperarse detección completa; no se añadieron variables ni cambiaron etiquetas para favorecer métricas.

## Pruebas y límites

Las pruebas comprueban cantidades, esquema, IDs, montos, fechas, familias sutiles/ráfagas, reproducibilidad en memoria y por comandos/bytes, correspondencia del archivo generado, corte temporal, importación real en FastAPI/SQLite temporal, metadatos, etiquetas inválidas/conflictivas, exclusión de etiquetas del transformador y recorrido referencia→train→test→analyze→dashboard.

Dataset diseñado por reglas, sin parámetros estimados de datos reales, con 18 usuarios y 90 días. El 10% es una elección didáctica, no prevalencia bancaria. Hay relaciones de categorías simplificadas y frecuencia limitada. Una sola semilla/prueba no valida generalización; los resultados se inspeccionaron al desarrollar esta demo. La precisión 1.0 se basa en solo seis alertas y no compensa los falsos negativos. No hay detección causal, validación externa ni decisión automática sobre personas.
