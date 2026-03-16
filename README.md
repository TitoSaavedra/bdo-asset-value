# Black Desert Asset Tracker

![Black Desert Asset Tracker](https://img.shields.io/badge/Black%20Desert%20Online-Asset%20Tracker-blue?style=for-the-badge&logo=game&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135.1-green?style=flat-square&logo=fastapi)
![Tesseract OCR](https://img.shields.io/badge/Tesseract-OCR-orange?style=flat-square)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow?style=flat-square&logo=javascript)

Sistema de seguimiento de activos para Black Desert Online con OCR, API FastAPI y dashboard web con historial, métricas y estado de conexión.

## Descripción General

Esta aplicación captura valores de plata (mercado, inventario y almacenes), los procesa con OCR y los persiste como historial para análisis en tiempo real.

Principales objetivos:

- Registrar activos con baja fricción desde hotkeys.
- Mantener historial y snapshots de almacenes.
- Visualizar evolución, métricas y estado del sistema.
- Permitir operación local sin infraestructura adicional (JSON local), con base preparada para MongoDB.

## Novedades Recientes

- OCR desacoplado de hotkeys mediante cola de tareas.
- Nuevo módulo dedicado: `app/ocr/queue_processor.py`.
- Captura rápida + procesamiento diferido (OCR y guardado en JSON) en segundo plano.
- Frontend con estado de conexión API/WebSocket.
- Overlay de arranque con reintentos al iniciar frontend.
- Endpoint de logs recientes: `/api/logs/recent`.

## Arquitectura

### Backend

- `app/main.py`: App FastAPI, rutas REST, WebSocket y ciclo de vida.
- `app/service.py`: Lógica de negocio, cache de dashboard, métricas y compacción de historial.
- `app/storage.py`: Persistencia actual en JSON (`data/asset_history.json`) y opción MongoDB.
- `app/database.py`: Cliente y creación de índices MongoDB.
- `app/hotkeys.py`: Captura de imágenes desde atajos y encolado de tareas OCR.
- `app/models.py`: Modelos Pydantic de entrada/salida y estado.

### OCR

- `app/ocr/capture.py`: Captura de regiones de pantalla con `mss`.
- `app/ocr/image.py`: Preprocesamiento de imagen para OCR.
- `app/ocr/reader.py`: Lectura OCR y limpieza de valores/nombres.
- `app/ocr/queue_processor.py`: Cola, workers OCR y guardado diferido.
- `app/ocr/config/`: Regiones, calibración y catálogos de almacenes.

### Frontend

- `frontend/index.html`: Shell principal + overlay de inicio.
- `frontend/js/main.js`: Estado UI, render y sincronización.
- `frontend/js/api.js`: Cliente API + observador de conexión.
- `frontend/views/`: Pantallas (`dashboard`, `manual`, `metrics`, `warehouses`).

## Flujo OCR en Cola (actual)

1. Hotkey captura imágenes (rápido).
2. Se encola una tarea (`market_inventory` o `storage_snapshot`).
3. Worker de `queue_processor` procesa OCR en segundo plano.
4. El resultado se guarda vía `AssetService` en `data/asset_history.json`.
5. El backend emite actualización para refresco de UI.

Esto reduce bloqueos en la entrada de hotkeys cuando se disparan muchas capturas seguidas.

## Requisitos

- Python 3.8+
- Tesseract OCR instalado
- Windows 10/11 (flujo de captura actual pensado para Windows)

## Instalación

```bash
cd bdo-asset-value
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Instala Tesseract OCR (UB Mannheim recomendado en Windows):

- https://github.com/UB-Mannheim/tesseract/wiki

Si hace falta, ajusta ruta de Tesseract en `app/config.py` (`TESSERACT_CMD`).

## Ejecución

```bash
python run.py
```

Esto inicia:

- API en `http://127.0.0.1:8000`
- Listener de hotkeys globales

## Hotkeys Vigentes

- `ALT + 1`: monitoreo de almacenes (captura nombre + valor y encola).
- `ALT + 2`: captura mercado + inventario (encolado inmediato).
- `ESC`: cancela monitoreo activo de almacén.

## API Principal

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/` | Frontend principal |
| GET | `/api/dashboard` | Datos agregados de dashboard |
| GET | `/api/history` | Historial paginado |
| GET | `/api/snapshots` | Snapshots de almacenes paginados |
| GET | `/api/metrics` | Métricas internas de runtime |
| GET | `/api/logs/recent` | Acciones recientes para monitoreo |
| POST | `/api/manual-record` | Alta manual de registro |
| POST | `/api/manual-warehouse-value` | Corrección manual de almacén |
| POST | `/api/ocr/storage` | Alta de snapshot de almacén por API |
| POST | `/api/ocr/inventory` | Alta de inventario por API |
| POST | `/api/preorders` | Alta de preorders |
| POST | `/api/settings/include-warehouses/{value}` | Toggle de inclusión de almacenes |
| POST | `/api/history/compact` | Compacción manual de historial |
| WS | `/ws/updates` | Actualizaciones en tiempo real |

## Persistencia

### Actual (por defecto)

- Archivo: `data/asset_history.json`
- Ventaja: simple y portable.
- Limitación: lectura/escritura completa del archivo.

### Preparado para MongoDB

- Variables: `MONGODB_URL`, `DATABASE_NAME`.
- Script de migración: `migrate_to_mongodb.py`.
- Índices automáticos en startup (`app/database.py`).

## Variables de Entorno

Variables útiles en backend (`app/config.py`):

- `MONGODB_URL`
- `DATABASE_NAME`
- `DASHBOARD_CACHE_TTL_SECONDS`
- `HISTORY_COMPACTOR_INTERVAL_SECONDS`
- `HISTORY_RETENTION_DAYS`

Variables de logging (`app/logs/logger.py`):

- `ENABLE_BACKEND_CONSOLE_LOGS=true|false`
- `LOG_LEVEL=DEBUG|INFO|WARNING|ERROR`

## Estructura del Proyecto

```text
bdo-asset-value/
├── app/
│   ├── config.py
│   ├── database.py
│   ├── hotkeys.py
│   ├── main.py
│   ├── models.py
│   ├── service.py
│   ├── storage.py
│   ├── logs/
│   └── ocr/
│       ├── capture.py
│       ├── image.py
│       ├── queue_processor.py
│       ├── reader.py
│       ├── utils.py
│       └── config/
├── data/
│   └── asset_history.json
├── frontend/
│   ├── css/
│   ├── js/
│   └── views/
├── run.py
├── dev.py
└── migrate_to_mongodb.py
```

## Desarrollo

Modo desarrollo (auto-restart por cambios Python):

```bash
python dev.py
```

Notas:

- El proyecto sigue convención PEP 8 y tipado en backend.
- Mantener nombres en inglés para código/variables/modelos.

## Roadmap de Rendimiento (Backend)

### Prioridad Alta

- [ ] Migrar persistencia principal a MongoDB (o repositorio en memoria + flush por lotes).
- [ ] Reducir recálculo completo de dashboard en broadcasts de actualización.
- [ ] Añadir sincronización más robusta de escritura entre entradas concurrentes.

### Prioridad Media

- [ ] Reutilizar instancia de captura (`mss`) para bajar overhead.
- [ ] Endurecer gestión de conexiones WebSocket caídas.
- [ ] Exponer métricas de cola OCR (`enqueued`, `processed`, `dropped`, `queue_size`).

### Quick Wins

- [ ] Eventos WS livianos y refresco de dashboard con debounce en frontend.
- [ ] Ajustar TTL de cache de dashboard según carga real.
- [ ] Separar proceso OCR/hotkeys del proceso API en producción.

## Contribución

1. Haz fork del repositorio.
2. Crea una rama de trabajo.
3. Implementa cambios con foco en módulos y responsabilidad única.
4. Abre Pull Request con contexto técnico claro.

## Licencia

Este proyecto está bajo licencia MIT.

## Descargo de Responsabilidad

Proyecto para uso personal/educativo. No está afiliado con Pearl Abyss ni Black Desert Online. Usa esta herramienta bajo tu responsabilidad y revisa los términos del juego.
