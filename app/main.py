from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.models import ManualRecordIn, StorageCaptureIn, InventoryCaptureIn, PreorderIn
from app.service import AssetService
from app.config import FRONTEND_DIR

app = FastAPI(title='bdo-asset-value')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.mount('/static', StaticFiles(directory=str(FRONTEND_DIR)), name='static')
service = AssetService()


@app.get('/')
def index():
    return FileResponse(FRONTEND_DIR / 'index.html')


@app.get('/api/dashboard')
def get_dashboard():
    return service.dashboard()


@app.post('/api/manual-record')
def create_manual_record(payload: ManualRecordIn):
    return service.add_manual_record(payload.market_silver, payload.inventory_silver, payload.preorder_silver or 0)


@app.post('/api/ocr/storage')
def capture_storage(payload: StorageCaptureIn):
    snapshot, record = service.add_storage_capture(payload.warehouse, payload.market_silver)
    return {'snapshot': snapshot, 'record': record}


@app.post('/api/ocr/inventory')
def capture_inventory(payload: InventoryCaptureIn):
    return service.add_inventory_capture(payload.inventory_silver)


@app.post('/api/preorders')
def receive_preorder(payload: PreorderIn):
    return service.add_preorder(payload.preorder_silver, payload.source or 'browser-extension')


@app.post('/api/settings/include-warehouses/{value}')
def set_include_warehouses(value: int):
    return service.toggle_include_warehouses(bool(value))