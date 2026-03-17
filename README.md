# Black Desert Asset Tracker

Sistema de captura OCR y seguimiento de activos para Black Desert Online.

## Arquitectura

- `python-api-service/`: API FastAPI, persistencia principal en MongoDB, WebSocket, métricas y compactación de historial.
- `python-ocr-worker/`: hotkeys globales, captura de pantalla, OCR y envío de datos a la API por HTTP.
- `frontend-tauri/`: cliente Svelte/Tauri; también se usa para build web servido por Docker.
- `data/asset_history.json`: historial legado usado solo para migración a MongoDB.

## Runtime

- Docker: `api`, `frontend`, `mongodb`
- Host Windows: `ocr-worker`

Flujo:

1. `ocr-worker` captura pantalla y procesa OCR.
2. `ocr-worker` envía resultados a la API.
3. La API persiste en MongoDB.
4. La API publica actualizaciones por WebSocket.

## Requisitos

- Python 3.10+
- Docker + Docker Compose
- Tesseract OCR instalado en Windows
- Node.js/pnpm solo si vas a trabajar fuera de Docker con el frontend

## Configuración

Archivo de entorno base: `.env`

Variables principales:

- `API_HOST`
- `API_PORT`
- `MONGODB_URL`
- `DATABASE_NAME`
- `MONGO_PORT`
- `FRONTEND_PORT`
- `API_BASE_URL`
- `API_TIMEOUT_SECONDS`

Puedes partir desde `.env.example`.

## Puesta en marcha

### 1. Levantar servicios Docker

```bash
docker compose up -d --build
```

Servicios expuestos:

- API: `http://localhost:${API_PORT}`
- Frontend web: `http://localhost:${FRONTEND_PORT}`
- MongoDB: `mongodb://localhost:${MONGO_PORT}`

`docker compose` lee `.env` automáticamente desde la raíz del proyecto.

### 2. Migrar historial legado a MongoDB

Ejecutar una vez si quieres importar `data/asset_history.json`:

```bash
python migrate_to_mongodb.py
```

Colecciones utilizadas:

- `records`
- `warehouse_snapshots`
- `settings`
- `storage_names`

### 3. Ejecutar OCR worker en host

```powershell
.\load-env.ps1
.\start-ocr.ps1
```

`start-ocr.ps1` abre el proceso OCR en otra terminal con las variables cargadas.

## Scripts

- `load-env.ps1`: carga variables desde `.env` en la sesión actual.
- `start-ocr.ps1`: inicia `python-ocr-worker/main.py` en host.
- `migrate_to_mongodb.py`: migra el historial legado JSON a MongoDB.

## API

Endpoints principales:

- `GET /api/dashboard`
- `GET /api/history`
- `GET /api/snapshots`
- `GET /api/metrics`
- `GET /api/logs/recent`
- `POST /api/manual-record`
- `POST /api/manual-warehouse-value`
- `POST /api/ocr/storage`
- `POST /api/ocr/inventory`
- `POST /api/ocr/market-inventory`
- `POST /api/preorders`
- `POST /api/history/compact`
- `POST /api/settings/include-warehouses/{value}`
- `WS /ws/updates`

## Persistencia

MongoDB es el backend principal de runtime.

Colecciones:

- `records`: historial de registros consolidados.
- `warehouse_snapshots`: snapshots de bodegas.
- `settings`: configuración de aplicación.
- `storage_names`: catálogo de nombres de storage mantenido por la API.

`data/asset_history.json` se conserva únicamente como fuente histórica para migración.

## Estructura

```text
bdo-asset-value/
├── python-api-service/
├── python-ocr-worker/
├── frontend-tauri/
├── data/
│   └── asset_history.json
├── docker-compose.yml
├── load-env.ps1
├── start-ocr.ps1
└── migrate_to_mongodb.py
```

## Notas

- Hotkeys actuales: `ALT+1`, `ALT+2`, `ESC`.
- El OCR worker debe correr en Windows host; no está soportado dentro de Docker para captura global/hotkeys.
- El roadmap técnico está en `TODO.md`.
