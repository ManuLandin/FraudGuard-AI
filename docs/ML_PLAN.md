# Plan de la etapa de Machine Learning

Alcance autorizado: preprocesamiento reproducible, Isolation Forest, entrenamiento separado de inferencia, artefacto joblib y pruebas. Mantener las APIs existentes y los datos SQLite sin cambios de esquema.

1. Escribir pruebas con datos normales/atípicos sintéticos, reproducibilidad, independencia de etiquetas, partición temporal, persistencia e entradas inválidas.
2. Implementar transformación determinista: log1p de monto en unidades monetarias y componentes seno/coseno de hora y día UTC. Excluir identificadores y etiquetas. No calcular frecuencia de un lote completo: introduciría dependencia del lote y datos futuros; se reserva hasta definir historial causal por cuenta.
3. Ordenar por fecha; ajustar con el primer 75% y calibrar con el último 25%, sin dividir timestamps iguales. Exigir al menos 40 filas de ajuste y 20 de calibración.
4. Usar -score_samples como señal cruda y percentil empírico con rango medio para empates como puntuación 0–100. Riesgo orientativo bajo <95, medio [95,99), alto >=99; marcar anomalía >=99. Ninguno es probabilidad ni confirmación de fraude.
5. Guardar pipeline, referencia, semilla, metadatos y versiones de bibliotecas en joblib; reemplazo atómico y carga solo de artefactos locales de confianza. Proveer comandos CSV para train/analyze.
6. Ejecutar suite completa, comprobar comandos y actualizar progreso y documentación. Evaluación formal, línea base, endpoints ML, persistencia de resultados y dashboard quedan fuera de esta etapa.
