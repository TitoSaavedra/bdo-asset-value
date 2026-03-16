"""FastAPI application for Black Desert Online Asset Tracker."""

import asyncio
from contextlib import suppress
from typing import Dict, Any, List
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.models import ManualRecordIn, StorageCaptureIn, InventoryCaptureIn, PreorderIn, ManualWarehouseValueIn
from app.service import AssetService
from app.config import FRONTEND_DIR, HISTORY_COMPACTOR_INTERVAL_SECONDS, HISTORY_RETENTION_DAYS

# Initialize FastAPI application
app = FastAPI(
    title='Black Spirit Lens',
    description='OCR-powered asset tracking for Black Desert Online',
    version='1.0.0'
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Mount static files
app.mount('/static', StaticFiles(directory=str(FRONTEND_DIR)), name='static')

# WebSocket connection manager
class ConnectionManager:
    """Manager for WebSocket connections."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                # Remove broken connections
                self.active_connections.remove(connection)

# Global connection manager instance
manager = ConnectionManager()

asset_service = AssetService()
compactor_task: asyncio.Task | None = None

# Dependency injection for service
def get_asset_service() -> AssetService:
    """Dependency injection for AssetService."""
    return asset_service


async def periodic_compactor_loop() -> None:
    """Run periodic history compaction in background."""
    while True:
        await asyncio.sleep(max(60, HISTORY_COMPACTOR_INTERVAL_SECONDS))
        try:
            asset_service.compact_history(retention_days=HISTORY_RETENTION_DAYS)
        except Exception:
            pass


@app.on_event('startup')
async def on_startup() -> None:
    """Initialize startup resources and background jobs."""
    global compactor_task
    try:
        from app.database import ensure_indexes
        await ensure_indexes()
    except Exception:
        pass

    if compactor_task is None or compactor_task.done():
        compactor_task = asyncio.create_task(periodic_compactor_loop())


@app.on_event('shutdown')
async def on_shutdown() -> None:
    """Stop background compactor task gracefully."""
    global compactor_task
    if compactor_task:
        compactor_task.cancel()
        with suppress(asyncio.CancelledError):
            await compactor_task
        compactor_task = None


@app.get('/')
def index() -> FileResponse:
    """Serve the main frontend application."""
    return FileResponse(FRONTEND_DIR / 'index.html')


@app.get('/api/dashboard')
def get_dashboard(
    history_limit: int = 50,
    snapshots_limit: int = 200,
    service: AssetService = Depends(get_asset_service),
) -> Dict[str, Any]:
    """Get dashboard data including latest records and settings.

    Returns:
        Dictionary containing dashboard information.
    """
    return service.dashboard(history_limit=history_limit, snapshots_limit=snapshots_limit)


@app.get('/api/history')
def get_history_page(
    limit: int = 20,
    offset: int = 0,
    range_name: str = 'all',
    service: AssetService = Depends(get_asset_service),
) -> Dict[str, Any]:
    """Get paginated history records."""
    return service.get_history_page(limit=limit, offset=offset, range_name=range_name)


@app.get('/api/snapshots')
def get_snapshots_page(
    limit: int = 20,
    offset: int = 0,
    service: AssetService = Depends(get_asset_service),
) -> Dict[str, Any]:
    """Get paginated warehouse snapshots."""
    return service.get_snapshots_page(limit=limit, offset=offset)


@app.post('/api/history/compact')
def compact_history(service: AssetService = Depends(get_asset_service)) -> Dict[str, Any]:
    """Force a history compaction run."""
    return service.compact_history(retention_days=HISTORY_RETENTION_DAYS)


@app.get('/api/metrics')
def get_metrics(service: AssetService = Depends(get_asset_service)) -> Dict[str, Any]:
    """Get basic runtime metrics for troubleshooting performance."""
    return service.metrics()


@app.get('/api/logs/recent')
def get_recent_logs(
    limit: int = 30,
    service: AssetService = Depends(get_asset_service),
) -> Dict[str, Any]:
    """Get recent action logs for UI monitoring."""
    return service.get_recent_actions(limit=limit)


@app.post('/api/manual-record')
def create_manual_record(
    payload: ManualRecordIn,
    service: AssetService = Depends(get_asset_service)
) -> Dict[str, Any]:
    """Create a manual asset record.

    Args:
        payload: Manual record input data.
        service: Asset service dependency.

    Returns:
        Created record information.
    """
    record = service.add_manual_record(
        payload.market_silver,
        payload.inventory_silver,
        payload.preorder_silver or 0
    )
    return record.model_dump()


@app.post('/api/ocr/storage')
def capture_storage(
    payload: StorageCaptureIn,
    service: AssetService = Depends(get_asset_service)
) -> Dict[str, Any]:
    """Capture warehouse storage data via OCR.

    Args:
        payload: Storage capture input data.
        service: Asset service dependency.

    Returns:
        Dictionary containing snapshot and optional record information.
    """
    snapshot, record = service.add_storage_capture(payload.warehouse, payload.market_silver)
    return {
        'snapshot': snapshot.model_dump(),
        'record': record.model_dump() if record else None
    }


@app.post('/api/manual-warehouse-value')
def create_manual_warehouse_value(
    payload: ManualWarehouseValueIn,
    service: AssetService = Depends(get_asset_service)
) -> Dict[str, Any]:
    """Create a manual warehouse value correction.

    Args:
        payload: Manual warehouse value input data.
        service: Asset service dependency.

    Returns:
        Created record information.
    """
    record = service.add_manual_warehouse_value(
        payload.warehouse,
        payload.market_silver,
    )
    return record.model_dump()


@app.post('/api/ocr/inventory')
def capture_inventory(
    payload: InventoryCaptureIn,
    service: AssetService = Depends(get_asset_service)
) -> Dict[str, Any]:
    """Capture inventory data via OCR.

    Args:
        payload: Inventory capture input data.
        service: Asset service dependency.

    Returns:
        Created record information.
    """
    record = service.add_inventory_capture(payload.inventory_silver)
    return record.model_dump()


@app.post('/api/preorders')
def receive_preorder(
    payload: PreorderIn,
    service: AssetService = Depends(get_asset_service)
) -> Dict[str, Any]:
    """Receive preorder data.

    Args:
        payload: Preorder input data.
        service: Asset service dependency.

    Returns:
        Created record information.
    """
    record = service.add_preorder(
        payload.preorder_silver,
        payload.source or 'browser-extension',
        payload.details
    )
    return record.model_dump()


@app.post('/api/settings/include-warehouses/{value}')
def set_include_warehouses(value: int, service: AssetService = Depends(get_asset_service)) -> Dict[str, Any]:
    """Set whether warehouses are included in total calculations.

    Args:
        value: Integer value (0 or 1) indicating whether to include warehouses.
        service: Asset service dependency.

    Returns:
        Updated settings information.
    """
    updated_state = service.toggle_include_warehouses(bool(value))
    return {'settings': updated_state.settings}


@app.get('/ws/updates')
def websocket_updates_info() -> Dict[str, str]:
    """Explain how to connect to the updates endpoint.

    Returns:
        Informational payload for plain HTTP requests to the WebSocket path.
    """
    return {
        'message': 'This endpoint is a WebSocket. Connect using ws://.../ws/updates.',
    }


@app.websocket('/ws/updates')
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates.

    Clients connect to this endpoint to receive real-time updates
    when asset data is modified.
    """
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)