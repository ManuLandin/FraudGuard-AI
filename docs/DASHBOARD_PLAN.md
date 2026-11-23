# Dashboard conectado a la API

1. Persistir resultados por transacción en tabla nueva, sin alterar las tablas existentes. Añadir estado/entrenamiento/análisis ML y resumen agregado por lote.
2. Exponer filtros de nivel y pendientes en la paginación del servidor. Los KPI y gráficas representan el lote seleccionado completo; búsqueda/nivel afectan a la tabla.
3. Construir dashboard en español con diseño existente: sidebar, cuatro KPI, gráficas de montos/frecuencia/distribución, importación CSV y tabla paginada. Acciones de entrenamiento y análisis explícitas y separadas.
4. No incluir datos simulados en el frontend. Los CSV sintéticos se importan por la API y su procedencia académica se declara visiblemente. No generar métricas cuando falten datos.
5. Probar flujo completo con SQLite temporal y modelo temporal, filtros/paginación/resumen, errores de importación y conexiones frontend. Compilar y comprobar en navegador.
