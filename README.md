# FraudGuard AI

Plataforma académica de ESCOM-IPN para explorar **anomalías en transacciones**, no fraudes confirmados. Se ejecuta localmente y no requiere servicios de pago.

**Entrega actual: dashboard conectado a la API real.** Incluye CSV, SQLite, entrenamiento e inferencia de Isolation Forest, persistencia de resultados, KPI, gráficas Recharts, búsqueda, paginación y filtros por nivel. Interfaz en español y responsive. Los ejemplos sintéticos se importan por la API real; el frontend no fabrica datos. Consulta [uso del dashboard](docs/DASHBOARD.md) y [modelo y limitaciones](docs/ML_MODEL.md). Se ejecutó una evaluación académica exploratoria contra línea base: ver [resultados y límites](docs/EVALUATION.md).

## Requisitos

- Windows y PowerShell.
- Python 3.12 (verificado con 3.12.10).
- Node.js 22.12 o superior (verificado con 24.14.1) y npm (11.11.0).
- Acceso a Internet para instalar las dependencias por primera vez. La aplicación instalada usa recursos locales, incluida la tipografía.

Todos los comandos siguientes parten de la raíz del proyecto, salvo donde se indique otra carpeta. No hace falta activar el entorno virtual ni cambiar la política de ejecución de PowerShell. Si PowerShell bloquea `npm`, usar `npm.cmd` en su lugar.

## Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.lock.txt
Push-Location .\frontend
npm ci
Pop-Location
```

`requirements.lock.txt` registra todas las versiones de Python verificadas, incluidas las herramientas de prueba. `requirements.txt` declara las dependencias directas de ejecución; `requirements-dev.txt` añade las de pruebas. Para actualizar versiones deliberadamente, instalar `requirements-dev.txt`, ejecutar las comprobaciones y regenerar el lock. El cliente `httpx2` es el recomendado por la versión instalada de Starlette para `TestClient`.

La configuración predeterminada funciona sin archivos `.env`. Para personalizarla, copiar los ejemplos **si aún no existen los archivos locales**:

```powershell
if (-not (Test-Path .\backend\.env)) {
    Copy-Item .\backend\.env.example .\backend\.env
}
if (-not (Test-Path .\frontend\.env)) {
    Copy-Item .\frontend\.env.example .\frontend\.env
}
```

## Ejecución local

En una primera terminal, desde la raíz:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

En una segunda terminal, desde la raíz:

```powershell
Set-Location .\frontend
npm run dev
```

- Interfaz: [http://localhost:5173](http://localhost:5173).
- Salud de la API: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health).
- Documentación interactiva: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

Detener cada servidor con `Ctrl+C`. Vite usa un puerto fijo: si 5173 está ocupado, informa el error en vez de cambiarlo silenciosamente. Si cambias puertos, actualiza también las variables de entorno y el comando correspondiente.

## Configuración

| Variable | Archivo | Valor predeterminado |
| --- | --- | --- |
| `CORS_ORIGINS` | `backend/.env` | `["http://localhost:5173","http://127.0.0.1:5173"]` |
| `DATABASE_URL` | `backend/.env` | SQLite en `backend/fraudguard.db`, ruta absoluta calculada |
| `MODEL_PATH` | `backend/.env` | `backend/artifacts/isolation_forest.joblib` |
| `MAX_UPLOAD_BYTES` | `backend/.env` | `5242880` (5 MiB) |
| `MAX_CSV_ROWS` | `backend/.env` | `10000` |
| `VITE_API_BASE_URL` | `frontend/.env` | `http://127.0.0.1:8000` |

`CORS_ORIGINS` debe ser una lista JSON de orígenes exactos, sin rutas ni barra final. No se aceptan comodines. Reiniciar el servidor correspondiente al cambiar variables. Las variables `VITE_*` son públicas en el navegador: nunca guardar secretos en ellas. Los `.env` locales están excluidos de Git.

## Verificación

Desde la raíz:

```powershell
.\.venv\Scripts\python.exe -m pytest -c .\backend\pytest.ini .\backend\tests
Push-Location .\frontend
npm test
npm run build
Pop-Location
```

Con el backend iniciado:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Respuesta esperada:

```json
{"status":"ok","service":"FraudGuard AI","version":"0.1.0"}
```

Prueba manual de integración: abre el dashboard y comprueba los registros consultados. Detén el backend y pulsa «Actualizar»: debe aparecer un error con «Reintentar carga». Inícialo y reintenta para recuperar los datos. Las consultas del dashboard tienen un límite de 60 segundos. Los controles antiguos de salud se conservan solo como componente probado y no son la página principal.

El build estático se escribe en `frontend/dist/`. `npm run preview` lo sirve en el puerto 4173; si quieres comprobar la conexión desde esa vista previa, añade explícitamente `http://127.0.0.1:4173` a `CORS_ORIGINS` y reinicia el backend. La configuración predeterminada permite solo el servidor de desarrollo.

## Organización y siguientes fases

```text
backend/       API FastAPI, configuración, contratos y pruebas
frontend/      React, TypeScript, Tailwind y pruebas Vitest
datasets/      Ejemplos CSV sintéticos documentados
docs/          Arquitectura, backlog, plan y progreso
```

- [Arquitectura y decisiones](docs/ARCHITECTURE.md).
- [Backlog de tres semanas](docs/BACKLOG.md).
- [Plan de implementación de la fase 1](docs/superpowers/plans/2026-11-12-phase-1.md).
- [Progreso y evidencia de verificación](docs/PROGRESS.md).

La persistencia crea `backend/fraudguard.db` al iniciar FastAPI. SQLAlchemy y python-multipart están incluidos en los requisitos y el lock actualizado. El pipeline ML incluye pandas, NumPy, scikit-learn y joblib. Recharts y los endpoints ML/dashboard ya están integrados; los resultados se guardan en la tabla AnalysisResult.

## Interpretación y límites

Una anomalía es una observación atípica y requiere revisión. Las puntuaciones no son probabilidades de fraude y no proporcionan explicaciones causales. Solo se utilizarán datos sintéticos identificados como tales. No subir ni almacenar información bancaria real.

`/health` indica que el proceso responde; no comprueba un modelo ni una base de datos. Esta entrega está destinada a desarrollo local. No incluye autenticación. La carga CSV aplica límites de tamaño/filas y validación estricta; está destinada exclusivamente a datos sintéticos en desarrollo local.

## Referencias técnicas

Configuración contrastada con las guías oficiales de [Vite](https://vite.dev/guide/), [Tailwind CSS con Vite](https://tailwindcss.com/docs/installation/using-vite), [CORS en FastAPI](https://fastapi.tiangolo.com/tutorial/cors/) y [configuración de FastAPI](https://fastapi.tiangolo.com/advanced/settings/).

## API de transacciones

Reinicia el backend tras actualizar dependencias. Usa `/docs` o los comandos de [CSV_IMPORT.md](docs/CSV_IMPORT.md) para cargar el ejemplo sintético, listar páginas y consultar detalles. `DATABASE_URL`, `MAX_UPLOAD_BYTES` y `MAX_CSV_ROWS` están documentadas en `backend/.env.example`.

## Entrenamiento e inferencia

Consulta [ML_MODEL.md](docs/ML_MODEL.md) para entrenar y guardar un modelo, analizar un CSV separado y reproducir el ejemplo sintético. La puntuación es un percentil de anomalía respecto de una referencia temporal separada, no una probabilidad de fraude. Los niveles de riesgo solo orientan la revisión.

## Dashboard

Sigue el [recorrido CSV → entrenamiento → análisis → dashboard](docs/DASHBOARD.md). Reinicia FastAPI para registrar las rutas nuevas. El porcentaje de anomalías usa solo transacciones analizadas, y las pendientes se identifican por separado.

## Auditoría y evaluación

Verificación del 13 de noviembre de 2026: **64 pruebas backend, 13 frontend y build correctos**, más recorrido HTTP real aislado con reinicio y persistencia. Las cifras describen esta ejecución; no garantizan ausencia de defectos.

```powershell
.\.venv\Scripts\python.exe scripts/audit_http.py
Push-Location backend
..\.venv\Scripts\python.exe -m app.ml.evaluation --reference ../datasets/ml_training_synthetic.csv --test ../datasets/ml_inference_synthetic.csv --output ../docs/evaluation/results.json
Pop-Location
```

Isolation Forest obtuvo recall 0.10 y F1 0.1818 en los 30 ejemplos sintéticos disponibles; la línea base de monto obtuvo recall/F1 1.0. No se ajustó el umbral con esas etiquetas y no se extrapolan resultados a datos bancarios. Consultar el contexto antes de citar métricas.

- [Informe de auditoría y evidencia](docs/AUDIT.md).
- [Documentación técnica y contratos actuales](docs/TECHNICAL.md).
- [Evaluación y matrices de confusión](docs/EVALUATION.md).
- [Limitaciones y riesgos](docs/LIMITATIONS.md).
- [Guion de demostración de tres minutos](docs/DEMO_SCRIPT.md).

Los agregados monetarios de resumen ahora viajan como cadenas de centavos para conservar exactitud en JavaScript. Reinicia backend y frontend juntos tras actualizar. La base y los modelos generados siguen excluidos de Git.

## Demo reproducible de 1,000 transacciones

Dataset completamente ficticio en MXN: [fraudguard_demo_1000.csv](datasets/fraudguard_demo_1000.csv), con 900 normales y 100 anomalías de referencia durante 90 días.

```powershell
.\.venv\Scripts\python.exe datasets/generate_demo.py
.\.venv\Scripts\python.exe datasets/evaluate_demo.py
```

Reinicia el backend actualizado, abre el dashboard y selecciona ese archivo en **Importa tus transacciones → Importar CSV**. Se adapta user_id→account_id e is_anomaly→label sin romper CSV anteriores; tipo/categoría/ubicación se conservan como metadatos. La etiqueta no entra al modelo ni calcula el score.

[Generación, carga, particiones y limitaciones](docs/DATASET_DEMO.md). El corte temporal produce 709 filas de referencia (531 ajuste +178 calibración) y 291 de prueba con 27 anomalías. En esta prueba sintética el bosque obtuvo precision=1.0, recall=0.2222 y F1=0.3636; matriz [[264,0],[21,6]]. [Métricas y errores individuales](docs/evaluation/demo_1000/results.json). Son resultados de esta simulación, no garantía sobre transacciones reales. El CSV completo sirve para explorar; evaluar requiere usar las particiones, sin entrenar sobre la prueba.
