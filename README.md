# Black Desert Asset Tracker

![Black Desert Asset Tracker](https://img.shields.io/badge/Black%20Desert%20Online-Asset%20Tracker-blue?style=for-the-badge&logo=game&logoColor=white)
[![Black Desert Market Scanner](https://img.shields.io/badge/Black%20Desert%20Market-Scanner-blue?style=for-the-badge&logo=github)](https://github.com/TitoSaavedra/bdo-market-buyer-ext)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135.1-green?style=flat-square&logo=fastapi)
![Tesseract OCR](https://img.shields.io/badge/Tesseract-OCR-orange?style=flat-square)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow?style=flat-square&logo=javascript)

Herramienta para registrar y consultar activos de Black Desert Online usando OCR y una API FastAPI (backend-only).

## Descripción General

La aplicación captura valores de plata (mercado, inventario y almacenes), ejecuta OCR y guarda los resultados como historial.

Objetivos:

- Registrar activos desde hotkeys.
- Mantener historial y snapshots de almacenes.
- Consultar evolución, métricas y estado del sistema.
- Permitir operación local sin infraestructura adicional (JSON local), con base preparada para MongoDB.

## Cambios Recientes

- OCR desacoplado del manejo de hotkeys mediante cola de tareas.
- Nuevo módulo dedicado: `app/ocr/queue_processor.py`.
- Captura rápida y procesamiento diferido (OCR y guardado en JSON) en segundo plano.
- Frontend con estado de conexión API/WebSocket.
- Overlay de arranque con reintentos al iniciar frontend.
- Endpoint de logs recientes: `/api/logs/recent`.

## Arquitectura

### Backend

- `app/main.py`: App FastAPI, rutas REST, WebSocket y ciclo de vida.
- `app/service.py`: Lógica de negocio, caché de dashboard, métricas y compactación de historial.
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

- `frontend-tauri/`: Cliente desktop actual (Svelte + Tauri).
- `frontend-legacy/`: Frontend legacy (solo referencia histórica, no servido por FastAPI).

## Flujo OCR en Cola (actual)

1. Hotkey captura imágenes (rápido).
2. Se encola una tarea (`market_inventory` o `storage_snapshot`).
3. Worker de `queue_processor` procesa OCR en segundo plano.
4. El resultado se guarda mediante `AssetService` en `data/asset_history.json`.
5. El backend emite actualización para refresco de UI.

Este flujo reduce bloqueos cuando se disparan muchas capturas seguidas.

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
- Listener global de hotkeys

### Levantar API + Frontend Tauri con 1 comando

Desde la raíz del proyecto:

```powershell
.\start-dev.ps1
```

Este script abre dos terminales:

- Backend: `python run.py` usando `.venv\Scripts\python.exe`
- Frontend: `pnpm tauri dev` en `frontend-tauri/`

## Frontend Separado (Tauri)

Se agregó una carpeta independiente para migrar el frontend a desktop app:

- `frontend-tauri/`

Guía rápida:

1. Instalar Rust, Node.js y Build Tools (Windows) siguiendo:
	- `frontend-tauri/docs/RUST_WINDOWS_SETUP.md`
2. Inicializar el proyecto Tauri dentro de `frontend-tauri/`.
3. Mantener backend y frontend en procesos separados:
	- Terminal A: `python run.py` (API/hotkeys)
	- Terminal B: `pnpm tauri dev` (UI desktop)

Variables frontend sugeridas:

- `VITE_API_BASE_URL=http://127.0.0.1:8000`
- `VITE_WS_URL=ws://127.0.0.1:8000/ws/updates`

## Hotkeys Vigentes

- `ALT + 1`: monitoreo de almacenes (captura nombre y valor, luego encola).
- `ALT + 2`: captura mercado e inventario (encolado inmediato).
- `ESC`: cancela monitoreo activo de almacén.

## Integración con Extensión de Navegador

Este proyecto se puede usar junto con la extensión `bdo-market-buyer-ext`  para sincronizar datos.

Flujo de integración:

1. La extensión lee datos de precompra del market web de BDO.
2. La extensión calcula el total de `preorder_silver`.
3. La extensión envía el total al backend de este proyecto.
4. El backend registra el valor como entrada de preorders en el historial.

Endpoint utilizado por la extensión:

- `POST /api/preorders`

Requisitos para que funcione:

- Tener este backend corriendo en `http://127.0.0.1:8000`.
- Abrir la web del market de BDO en el navegador.
- Cargar/usar la extensión `bdo-market-buyer-ext` y ejecutar la sincronización de precompra.

## API Principal

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/` | Estado del backend/API |
| GET | `/api/dashboard` | Datos agregados del dashboard |
| GET | `/api/history` | Historial paginado |
| GET | `/api/snapshots` | Snapshots de almacenes paginados |
| GET | `/api/metrics` | Métricas internas de ejecución |
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
- Limitación: requiere lectura/escritura completa del archivo.

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
├── frontend-legacy/         # Legacy (no servido por FastAPI)
├── frontend-tauri/          # Cliente desktop actual
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

- [ ] Migrar persistencia principal a MongoDB (o repositorio en memoria con flush por lotes).
- [ ] Reducir recálculo completo del dashboard en broadcasts de actualización.
- [ ] Añadir sincronización más robusta de escritura entre entradas concurrentes.

### Prioridad Media

- [ ] Reutilizar instancia de captura (`mss`) para bajar overhead.
- [ ] Mejorar gestión de conexiones WebSocket caídas.
- [ ] Exponer métricas de cola OCR (`enqueued`, `processed`, `dropped`, `queue_size`).

### Quick Wins

- [ ] Eventos WS livianos y refresco de dashboard con debounce en frontend.
- [ ] Ajustar TTL de cache de dashboard según carga real.
- [ ] Separar proceso OCR/hotkeys del proceso API en producción.

## Contribución

1. Haz un fork del repositorio.
2. Crea una rama de trabajo.
3. Implementa cambios con foco en módulos y responsabilidad única.
4. Abre Pull Request con contexto técnico claro.

## Licencia

Este proyecto está bajo licencia MIT.

## Descargo de Responsabilidad

Proyecto para uso personal y educativo. No está afiliado con Pearl Abyss ni con Black Desert Online. Usa la herramienta bajo tu responsabilidad y revisa los términos del juego.
