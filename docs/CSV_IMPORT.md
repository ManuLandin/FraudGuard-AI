# Importación CSV y persistencia

## Contrato

Solo datos sintéticos. CSV UTF-8 (BOM opcional), separador coma y encabezados exactos sin duplicados. Orden de columnas libre. Se rechazan columnas desconocidas y filas con diferente número de campos. No se confía en el MIME enviado por el navegador. La extensión debe ser `.csv`; el contenido se valida por separado.

| Columna | Obligatoria | Formato |
| --- | --- | --- |
| transaction_id | Sí | Texto no vacío de hasta 100 caracteres, único dentro del archivo. |
| amount | Sí | Monto positivo, punto decimal, hasta dos decimales y 12 dígitos enteros. Sin símbolos, exponentes ni separadores de miles. |
| timestamp | Sí | ISO 8601 con T y zona horaria explícita, por ejemplo `2026-11-12T10:00:00-06:00`. Se normaliza a UTC. |
| account_id | No | Identificador sintético de hasta 100 caracteres. Vacío se convierte a null. |
| label | No | 0, 1 o vacío. Etiqueta externa para evaluación futura; no es una predicción ni confirma fraude. |

Se usa una sola moneda por dataset (convención académica: MXN). No se mezclan monedas ni se realizan conversiones. `amount_cents` conserva el monto como entero de centavos, evitando redondeo binario.

Ejemplo **sintético**: `datasets/example_synthetic.csv`. Los identificadores no deben corresponder a personas ni cuentas reales.

## Límites y consistencia

- Máximo 5 MiB de archivo y 10 000 filas por defecto. Configurables mediante `MAX_UPLOAD_BYTES` (hasta 20 MiB) y `MAX_CSV_ROWS` (hasta 100 000).
- El cuerpo multipart completo se limita antes de analizarlo a tamaño de archivo + 64 KiB de envoltura. Se cuentan bytes reales, incluso sin Content-Length. Después se valida el límite del archivo individual.
- El parser CSV estricto rechaza comillas sin cerrar, codificación incorrecta, campos inconsistentes, caracteres nulos, identificadores duplicados, fechas sin zona y montos inválidos. Los errores no devuelven el contenido de las filas.
- Se valida el archivo completo antes de escribir. Lote y transacciones se insertan en una única transacción SQL con rollback ante errores.
- La previsualización devuelve las primeras cinco transacciones **ya guardadas**, junto con el identificador del lote. No es una previsualización previa a confirmar la importación.
- Se conserva nombre de archivo saneado, fecha de importación UTC y número de filas. No se guarda el archivo original ni se utiliza su nombre como ruta.
- Reimportar un archivo crea otro lote: no hay deduplicación entre lotes. El modelo y los resultados ya están integrados; ver DASHBOARD.md.

## Entidades

`ImportBatch` tiene id, filename, created_at y row_count. `Transaction` tiene id interno, batch_id (clave foránea), transaction_id externo, amount_cents, timestamp, account_id y label. La combinación batch_id/transaction_id es única. SQLite activa claves foráneas en cada conexión e incluye restricciones de monto y etiqueta.

La base predeterminada está en `backend/fraudguard.db`, independiente del directorio desde el que se inicia Uvicorn. `DATABASE_URL` admite SQLite local; si se cambia la ruta, el directorio padre debe existir. Las tablas se crean al iniciar la aplicación y las conexiones se cierran al detenerla. Esta versión no incluye migraciones de esquemas previos ni eliminación de datos. La base queda excluida de Git.

## Endpoints

- `POST /api/transactions/upload`: formulario multipart con campo `file`. Devuelve 201 con batch_id, filename, row_count y preview.
- `GET /api/transactions?page=1&page_size=25&batch_id=1&search=demo`: listado con items, total, page y page_size. page >= 1; page_size entre 1 y 100. batch_id es opcional. Búsqueda literal por transaction_id o account_id, orden estable por id interno.
- `GET /api/transactions/{id}`: detalle por id interno; 404 si no existe.

Errores: 413 por exceso de tamaño; 415 por extensión/nombre inválido; 422 por CSV inválido o parámetros incorrectos; 400 para multipart que el parser no pueda interpretar; 503 ante errores de persistencia. CORS admite POST desde los orígenes locales configurados. La documentación interactiva en `/docs` permite subir el ejemplo y consultar resultados.

Desde la raíz, con el backend reiniciado:

```powershell
curl.exe -F "file=@datasets/example_synthetic.csv" http://127.0.0.1:8000/api/transactions/upload
Invoke-RestMethod http://127.0.0.1:8000/api/transactions
```

## Verificación

Las pruebas usan una SQLite temporal por caso. Comprueban persistencia entre instancias de aplicación, paginación, detalle, filtros, BOM, campos opcionales, carga válida, archivos vacíos/malformados/grandes, límite sin Content-Length, montos no finitos, duplicados, límites de filas, rollback, CORS POST y errores de base de datos.

Referencias: [SQLAlchemy SQLite](https://docs.sqlalchemy.org/en/21/dialects/sqlite.html), [parser de solicitudes Starlette](https://starlette.dev/requests/).

## Contrato auditado

Ids acotados al rango SQLite y paginación máxima 1000000000. Resumen diario y total envía amount_cents como cadena decimal; por transacción conserva entero numérico. Ver TECHNICAL.md y OpenAPI para esquemas completos.

## Esquema de demostración extendido

También se admiten user_id (alias de account_id), is_anomaly (alias de label), transaction_type (compra/transferencia/retiro/pago), merchant_category y location. Alias simultáneos deben coincidir. Metadatos de texto no vacíos, sin controles y de hasta 100 caracteres; se guardan en TransactionContext y se devuelven como campos opcionales. is_anomaly es referencia, no predicción. El contrato anterior sigue siendo válido. Ver DATASET_DEMO.md.
