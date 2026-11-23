# Progreso de FraudGuard AI

## 2026-11-12 — Fase 1 completada y verificada

- Inspección: carpeta vacía, sin repositorio Git ni instrucciones AGENTS.md en la ruta.
- Herramientas detectadas: Python 3.12.10, Node.js 24.14.1, npm 11.11.0; `py` no encuentra Python, se usa `python`.
- Arquitectura y backlog documentados; alcance limitado a estructura, configuración, `/health` y página inicial.
- Decisión: aprovechar la carpeta actual como raíz, sin subcarpeta redundante.
- Decisión: reservar las carpetas de SQLite y ML; implementar sus dependencias y comportamiento en las fases correspondientes.

### Implementación

- [x] Monorepositorio y paquetes/carpetas solicitados.
- [x] Entorno virtual local, requisitos de Python y lockfile completo; frontend con `package-lock.json`.
- [x] Configuración Pydantic Settings y ejemplos `.env`; orígenes CORS exactos, sin comodines.
- [x] FastAPI con factoría de aplicación y `GET /health` tipado.
- [x] React + Vite + TypeScript + Tailwind CSS; fuente alojada localmente e iconos consistentes.
- [x] Página inicial en español, navegación lateral, adaptación móvil y avisos de alcance académico.
- [x] Conexión real desde React, carga, errores de red/HTTP/contrato, tiempo de espera de cinco segundos, cancelación y reintento.
- [x] README con instalación, dos terminales de ejecución, configuración y pruebas en PowerShell.
- [x] Arquitectura, backlog y plan de implementación documentados.

### Evidencia de verificación

| Comprobación | Resultado observado |
| --- | --- |
| `python -m pytest -c backend/pytest.ini backend/tests -q` usando `.venv` | **11 pruebas aprobadas**, sin advertencias en la ejecución final. |
| `npm test` desde `frontend` | **8 pruebas aprobadas** en 2 archivos. |
| `npm run build` desde `frontend` | TypeScript y Vite correctos; build final generado en `frontend/dist/`, salida 0. |
| `python -m pip check` usando `.venv` | `No broken requirements found.` |
| Instalación npm | Completada; auditoría de instalación: 0 vulnerabilidades reportadas. |
| HTTP real a `/health` | `200`, JSON `{"status":"ok","service":"FraudGuard AI","version":"0.1.0"}`. |
| HTTP real al frontend | `200`. |
| Navegador con API iniciada | «API disponible», versión 0.1.0. |
| Navegador con API detenida y reintento | «Sin conexión con la API» e instrucciones para iniciar backend. |
| Navegador tras reiniciar la API | Reintento recupera «API disponible». |
| Responsive | Revisados 1440 × 1000 y 390 × 844; comprobado que el documento no desborda horizontalmente también a 320 px. |
| Teclado | El enlace «Saltar al contenido» activado con Enter mueve el foco al contenido principal. |
| Consola tras recargar y recuperar conexión | Sin errores registrados en la comprobación final. |
| Revisión de código | Corregido el único hallazgo: desplazamiento vertical de la sidebar en ventanas de poca altura. Build final correcto después del ajuste. |

Capturas: [escritorio](images/phase-1-desktop.jpg) y [móvil](images/phase-1-mobile.jpg). Se guardaron antes del ajuste final de desplazamiento de sidebar; el contenido y la composición de esas vistas se conservan.

Las pruebas se ejecutaron primero contra comportamiento ausente: `/health` devolvía 404 y las pruebas del frontend fallaban al no existir la conexión. Después se implementó y se verificaron las suites completas.

### Incidencias del entorno y decisiones

- Las descargas iniciales fallaron por restricciones de red. Se completaron con acceso autorizado a los registros oficiales de paquetes.
- El cliente de pruebas FastAPI se detenía creando el `socketpair` interno del bucle de eventos de Windows. El diagnóstico de pila lo identificó; con acceso autorizado a red local las pruebas terminaron normalmente. No se modificó el código para ocultar esa restricción del entorno.
- La versión instalada de Starlette recomendó migrar el cliente de pruebas a `httpx2`; se añadió `httpx2==2.16.0` y se verificó de nuevo sin la advertencia.
- La herramienta auxiliar de contexto visual no pudo escribir su caché externa. Se continuó con el brief del usuario y revisión directa en navegador.
- Versiones verificadas de backend: FastAPI 0.162.5, Pydantic 2.14.3, Pydantic Settings 2.16.2, Uvicorn 0.54.0 y pytest 9.2.0. Frontend: Vite 7.3.8 y Vitest 4.1.12; versiones completas en los locks.
- No se creó repositorio Git, rama ni remoto; la carpeta inicial estaba vacía y se trabajó directamente en la raíz autorizada.

### Alcance pendiente

**No se avanzó a la fase 2.** CSV, validación de archivos, SQLite/SQLAlchemy, generador/dataset sintético, Isolation Forest, persistencia joblib, evaluación, endpoints de transacciones/ML, Recharts y dashboard de resultados siguen pendientes. No hay métricas de modelo ni datos de demostración ficticios presentados como reales.


## Continuación — Ingesta CSV y persistencia SQLite

Alcance solicitado implementado; la sección anterior conserva el registro histórico de fase 1.

- [x] Entidades SQLAlchemy ImportBatch y Transaction, clave foránea, unicidad por lote, restricciones e índices.
- [x] SQLite local configurable, tablas al iniciar, sesiones por petición y cierre del engine al detener.
- [x] POST /api/transactions/upload con multipart, extensión y nombre saneados, parser CSV estricto UTF-8, validación de columnas/valores/fechas, límites de archivo/cuerpo/filas y guardado atómico.
- [x] Previsualización de hasta cinco filas guardadas y metadatos del lote.
- [x] GET /api/transactions con paginación, búsqueda literal y filtro por lote.
- [x] GET /api/transactions/{id}, 404 y manejo seguro de errores SQLite con 503.
- [x] Pruebas aisladas con bases temporales; persistencia comprobada entre instancias de aplicación.
- [x] Requisitos y requirements.lock.txt actualizados: SQLAlchemy 2.1.8 y python-multipart 0.0.33.
- [x] Contrato y comandos en CSV_IMPORT.md; README, arquitectura y .env.example actualizados. Ejemplo de dos filas explícitamente sintéticas.

Verificación ejecutada: `.\.venv\Scripts\python.exe -m pytest -c backend/pytest.ini backend/tests -q`: **36 pruebas aprobadas**, incluyendo las 11 previas. `pip check`: **No broken requirements found**. Se observó primero un fallo 404 del endpoint inexistente y un fallo al provocar un error SQLite; ambos se corrigieron y se verificó la suite completa. Las pruebas HTTP usan TestClient sobre la aplicación completa con lifespan; requieren acceso autorizado a conexiones internas de Windows. No se repitieron pruebas del frontend, cuyo código no cambió.

Decisiones y límites: importación de todo o nada; monto en centavos de una sola moneda por dataset; fecha normalizada a UTC; identificadores únicos por lote, sin deduplicación entre lotes. La previsualización es posterior al guardado. No se guarda CSV original. `label` es etiqueta externa y no salida del modelo. Se añaden tablas con create_all, sin migraciones de esquemas anteriores. La interfaz de carga, generador sintético, modelo, métricas, resultados de análisis y dashboard siguen pendientes. Reiniciar el backend e instalar el lock actualizado para usar las rutas nuevas.


## Continuación — Pipeline de preprocesamiento e Isolation Forest

- [x] Transformador scikit-learn validado: log1p de monto y componentes cíclicos de hora/día UTC. Sin etiquetas ni identificadores como variables.
- [x] Ajuste reproducible con 200 árboles, semilla 42, un hilo y max_samples acotado a 256.
- [x] Partición temporal: primer 75% para ajuste y tramo final para calibración; timestamps iguales no cruzan el corte. Mínimo 80 filas totales, 40 de ajuste y 20 de referencia.
- [x] Inferencia sin fit ni recalibración; resultados independientes de la composición del lote.
- [x] Score 0–100 por rango medio empírico de -score_samples respecto de referencia reservada. Bajo <95, medio [95,99), alto >=99; is_anomaly a partir de 99. No es probabilidad de fraude.
- [x] Guardado joblib atómico con metadatos y versiones; carga local de confianza con validación de esquema/referencia/entorno.
- [x] Comandos separados `python -m app.ml train` y `python -m app.ml analyze`, validación CSV compartida y salida JSON con aviso de interpretación.
- [x] Pruebas de normales/atípicos, reproducibilidad, roundtrip joblib, exclusión de etiquetas, ausencia de fuga desde calibración, invariancia por lote, datos inválidos, timestamps repetidos, empates y comandos reales en directorios temporales.
- [x] Ejemplos CSV explícitamente sintéticos, documentación ML_MODEL.md y ML_PLAN.md; README, arquitectura y lock actualizados.

Verificación: suite completa **52 pruebas aprobadas en 36.85 s**, sin advertencias; `pip check`: **No broken requirements found**. Se observó primero la ausencia del módulo, luego se implementó. La primera ejecución encontró una expectativa incorrecta de detección de todos los montos extremos; se corrigió para comprobar mayor puntuación y detección de algunos atípicos, sin garantía universal. Se sustituyó dayofweek por day_of_week para resolver una advertencia de pandas.

Versiones instaladas y registradas: scikit-learn 1.9.1, pandas 3.1.1, NumPy 2.5.4, joblib 1.6.0 (dependencias transitivas en requirements.lock.txt). No se modificó frontend ni se repitieron sus pruebas.

Ejemplo documentado ejecutado correctamente: entrenamiento con 180 filas de ajuste y 60 de calibración, artefacto local `backend/artifacts/isolation_forest.joblib` y análisis de 30 filas sintéticas en `backend/artifacts/demo_results.json`. Puntuaciones observadas dentro de [0,100] (mínimo 1.6667 y máximo 100); no se interpretan como métricas de calidad. Ambos archivos generados quedan excluidos de Git mediante la carpeta artifacts.

Decisiones: frecuencia pendiente hasta definir historial causal por cuenta; no usar conteos de todo un lote que consultarían el futuro. La referencia de calibración no se presenta como evaluación. No se reportan precision/recall/F1 ni explicaciones causales. Evaluación independiente con línea base, endpoints ML, persistencia de análisis y dashboard quedan pendientes. La etiqueta de los ejemplos es sintética, nunca fraude confirmado. Joblib no debe cargar archivos subidos ni de origen desconocido.


## Continuación — Dashboard React conectado a API real

- [x] Dashboard React + TypeScript en español con sidebar funcional y adaptación responsive, conservando la identidad azul marino/eléctrico.
- [x] KPI de analizadas, anomalías, porcentaje sobre analizadas y monto importado; pendientes separados. Sin denominador aparece «—».
- [x] Recharts: actividad diaria UTC, distribución de montos y distribución de niveles; tooltips y datos textuales expandibles. Carga diferida para separar gráficas del paquete inicial.
- [x] Importación CSV multipart desde interfaz, límites, estados de carga, errores del servidor y confirmación de lote guardado.
- [x] Tabla con 10 filas/página y búsqueda, lote y nivel (bajo/medio/alto/pendiente) en servidor. KPI y gráficas representan el lote completo, como aclara la interfaz.
- [x] Selección de lotes y acciones explícitas para entrenar y analizar, con modelo local real y controles de disponibilidad.
- [x] Nueva tabla AnalysisResult sin alterar tablas anteriores: resultado actual por transacción, score/nivel y fechas de modelo/análisis. Reanálisis atómico sin duplicar filas.
- [x] GET /api/transactions/batches, GET /api/dashboard/summary, GET /api/ml/status y POST /api/ml/train y /api/ml/analyze. Filtro risk_level añadido a transacciones; detalle/listado incluyen resultado y fecha del modelo.
- [x] MODEL_PATH configurable y operaciones ML serializadas en el proceso local del MVP. No admite subir artefactos joblib.
- [x] Cliente HTTP con errores legibles, cancelación de consultas obsoletas, límite de espera y reintento. No hay fixtures ni respuestas simuladas en el código de producción.
- [x] Documentación DASHBOARD.md, plan DASHBOARD_PLAN.md, README, arquitectura y ejemplo de entorno actualizados; Recharts registrado en package-lock.json.

### Verificación realizada

- Suite completa backend: **54 pruebas aprobadas en 24.98 s**. Incluye prueba HTTP del recorrido upload → train → analyze → summary → filtros/detalle, modelo y SQLite temporales, y reanálisis sin duplicación.
- Suite completa frontend final: **12 pruebas aprobadas en 5.65 s**, incluyendo errores de CSV/red, consultas de paginación/nivel y regresión tras análisis. Las simulaciones de red se limitan a los tests; la interfaz de producción consulta API real.
- Build final: TypeScript y Vite correctos. Gráficas separadas en carga diferida; ya no aparece la advertencia inicial de fragmento >500 kB.
- Navegador contra servidores locales reales: estado vacío sin indicadores inventados; importación de ml_inference_synthetic.csv como lote 1 con **30 registros**; ejecución del modelo local y persistencia de resultados; segunda página con synthetic-10; filtro alto con synthetic-24, puntuación 100 y 1 resultado. KPI observados: 30 analizadas y 1 anomalía, 3.3%; son valores del ejemplo, no métricas de calidad del modelo.
- Responsive revisado a 1440×1000 y 390×844; comprobado sin desbordamiento horizontal del documento también a 320 px. La tabla tiene desplazamiento horizontal propio en pantallas pequeñas.
- Evidencia: docs/images/dashboard-desktop.jpg, dashboard-mobile.jpg y dashboard-preview.jpg. Datos de las capturas **sintéticos**, importados por API y guardados en SQLite.
- Revisión de código: único hallazgo, página fuera de rango al analizar con filtros activos. Se reprodujo en prueba fallida y se corrigió reiniciando página tras la acción. También se evita un reinicio tardío de página por búsqueda inicial vacía. La suite final queda verde.
- Durante desarrollo se corrigió un cierre de etiqueta en la sidebar y se recargó la aplicación tras actualizar dependencias de un efecto React (advertencia transitoria de HMR, anterior a la recarga final).

### Decisiones y límites actuales

No se añadió un modo que reemplace datos reales por valores simulados. La demostración utiliza CSV sintéticos identificados y las mismas rutas reales de producción local. El artefacto existente se usó en la prueba del navegador; entrenamiento vía API también se verificó con modelo temporal.

Los resultados conservan procedencia de modelo pero no historial de versiones por transacción: reanalizar reemplaza su resultado anterior. Entrenar no invalida ni recalcula resultados ya guardados. Los resúmenes entre modelos no son evaluación de rendimiento. Agregación en memoria para alcance académico local, un solo worker para operaciones ML. Las operaciones no confirman fraudes y las puntuaciones no representan probabilidades.

Pendiente: evaluación formal temporal con línea base, precision/recall/F1 y matriz de confusión cuando existan etiquetas válidas, ampliación de pruebas end-to-end y guion académico final. No se implementaron bancos, pagos ni autenticación compleja.


## 2026-11-13 — Auditoría funcional, evaluación y documentación

- Reejecutadas suites iniciales: 54 backend y 12 frontend; build correcto.
- Corregido desbordamiento de enteros SQLite con ids/páginas enormes; observado OverflowError antes del cambio y añadidos seis casos con respuesta 422.
- Corregida pérdida de centavos en agregados monetarios grandes: summary.amount_cents y daily[].amount_cents ahora son cadenas, formateadas mediante BigInt/Intl en React. Pruebas de regresión fallaron antes y pasan después.
- Declarados modelos Pydantic explícitos para respuestas de lotes, resumen y ML; OpenAPI verificado mediante solicitudes HTTP.
- Añadido app.ml.evaluation: ajuste/calibración temporal sin etiquetas, comparación con percentil 99 de monto aprendido solo en ajuste, evaluación posterior, métricas condicionadas a disponibilidad/clases, matrices y hashes de archivos. No reemplaza el modelo local del dashboard.
- Evaluación ejecutada sobre 240 filas de referencia (180 fit +60 calibración) y 30 posteriores etiquetadas (20 normales/10 atípicas). Bosque: precision=1.0, recall=0.10, F1=0.181818, ROC-AUC=0.915, AP=0.832634; matriz [[20,0],[9,1]]. Línea base: métricas 1.0, matriz [[20,0],[0,10]]. Resultado exploratorio sobre ejemplos sintéticos ya inspeccionados, no benchmark ciego ni validez bancaria.
- Verificación final: **64 pruebas backend aprobadas en 25.10 s; 13 frontend aprobadas en 10.37 s; build salida 0; pip check sin conflictos**. Las pruebas nuevas cubren etiquetas ausentes/invalidas/una clase y rechazo de solapamiento temporal.
- Ejecutado scripts/audit_http.py con Uvicorn real, DB/modelo temporales y reinicio de proceso: health/OpenAPI, CSV inválidos/grandes, CSV válido/train/analyze/resumen/CORS, filtros/paginación/detalle/límites enteros y persistencia tras reiniciar aprobados. Evidencia docs/audit/http_checks.json.
- API/frontend reiniciados en localhost. Dashboard revisado en navegador: datos previos recuperados, filtro alto y retirada del filtro correctos. Captura docs/audit/dashboard.jpg. No se repitió importación por navegador en esta auditoría; sí por HTTP real.
- README y contratos actualizados; documentación vigente en TECHNICAL.md, LIMITATIONS.md, EVALUATION.md y AUDIT.md. Guion de exposición de tres minutos en DEMO_SCRIPT.md; no se ha cronometrado una exposición oral.

Las notas anteriores que indicaban evaluación pendiente son historia de fases previas. Sigue pendiente validación externa, datos sintéticos más diversos, intervalos y múltiples cortes temporales, carga/concurrencia multiproceso, migraciones/historial, seguridad de producción y accesibilidad exhaustiva. No hay fraudes confirmados ni probabilidades de fraude en las salidas.


## 2026-11-13 — Dataset sintético reproducible de 1,000 transacciones

- Inspección previa del contrato CSV, entidades y evaluación existentes; no se reconstruyó la arquitectura ni se eliminaron datos/funciones.
- Creado datasets/generate_demo.py con Python/pandas/NumPy y random_state=42. CSV principal datasets/fraudguard_demo_1000.csv: exactamente **1,000 filas, 900 normales y 100 anomalías**, IDs únicos permutados y montos positivos MXN, entre 2026-08-01 y 2026-10-30 exclusivo (-06:00).
- 18 perfiles ficticios, montos lognormales, categorías/zonas preferidas, horarios comerciales variables y menor actividad de fin de semana. Cinco familias de 20 anomalías: monto alto, madrugada, ráfaga (4 grupos de 5), cambio de patrón y combinación. Muchas mantienen montos habituales.
- Esquema de ocho columnas solicitado; adaptador compatible user_id→account_id e is_anomaly→label. Alias contradictorios se rechazan. Tipo/categoría/ubicación validados y guardados en nueva TransactionContext 1:1 opcional; no se alteraron tablas existentes. Respuestas API añaden contexto/referencia como campos opcionales. Ayuda del formulario CSV actualizada.
- La etiqueta de referencia no se utiliza para generar features ni scores. Se verificó igualdad del transformador después de invertir etiquetas. Las variables reales del modelo no cambian: monto/hora/día UTC; usuario/tipo/categoría/ubicación/frecuencia todavía no son features. Es una limitación explícita, no una explicación causal del bosque.
- Regeneración con un comando produce principal, manifiesto de semilla/hash/familias y dos particiones temporales: 709 referencia/291 prueba, corte fijo al día 63 sin mirar etiquetas. Reproducibilidad byte a byte verificada mediante dos ejecuciones de CLI en directorios temporales.
- Creado datasets/evaluate_demo.py; ejecución correcta sin modificar el modelo/DB de la plataforma. Ajuste 531 filas, calibración 178; prueba 291 con 27 positivos sintéticos. La referencia incluye 73 anomalías, sin filtrarlas mediante etiquetas. Score umbral99 sin ajustes usando la prueba.
- Resultado Isolation Forest: precision1.0, recall0.222222, F1=0.363636, ROC-AUC0.812991 y AP0.570058. Matriz [[264,0],[21,6]]. FP=0, FN=21 con IDs y detalle en docs/evaluation/demo_1000/. Línea base de monto: precision1.0, recall0.111111 y F1=0.2, matriz [[264,0],[24,3]]. No se modificaron etiquetas para favorecer resultados. Son métricas sintéticas, no rendimiento garantizado real.
- Predicciones/errores exportados con reference_is_anomaly y predicted_is_anomaly separados. Manifiesto comprobado por hash antes de evaluar; no se sobrescribe el CSV etiquetado.
- Suite completa final: **71 pruebas backend aprobadas en 31.81s**, incluidas 7 nuevas para esquema, cantidades, fechas, montos, familias, aliases, exclusión de etiquetas, reproducibilidad, importación completa y flujo train/analyze/dashboard de la partición. **13 pruebas frontend aprobadas en 11.05s; build salida0 (7.54s)**. pip check comprobado sin conflictos en la ejecución anterior de esta etapa.
- Corregidos textos previamente mal codificados de errores API y descripción de aplicación; ningún comportamiento previo eliminado.
- README, datasets/README.md, CSV_IMPORT.md, TECHNICAL.md y EVALUATION.md actualizados; guía completa en DATASET_DEMO.md. Informes anteriores se conservan y se identifican como experimentos distintos.

Para cargar las 1,000 filas: reiniciar backend actualizado (crea tabla aditiva), abrir dashboard, elegir datasets/fraudguard_demo_1000.csv e Importar CSV. Se guardan como un lote de 1,000 registros inicialmente pendientes. No usar resultados de las mismas filas de entrenamiento como evaluación; el evaluador y las particiones reference/test evitan ese solapamiento. Importar principal y particiones crea lotes distintos y aumenta el total global; no hay deduplicación entre lotes.


## 2026-11-23 — Preparación de publicación en GitHub

- Inicializado Git local y configurado origin como https://github.com/ManuLandin/FraudGuard-AI.git, conservando como padre el commit inicial existente del repositorio.
- Revisados los archivos seleccionados: sin .env locales, bases SQLite, artefactos joblib, entornos virtuales ni node_modules. No se encontraron patrones de credenciales en la revisión acotada.
- Añadido .gitattributes para conservar LF y los bytes reproducibles de CSV al clonar en Windows. Excluidos también archivos auxiliares de SQLite.
- Verificación previa al envío: 71 pruebas backend aprobadas en 83.06s, 13 frontend aprobadas y compilación de producción correcta. Solo se normalizó un espacio final en la sidebar, sin cambios de comportamiento.
