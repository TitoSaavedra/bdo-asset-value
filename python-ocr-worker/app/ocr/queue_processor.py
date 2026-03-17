"""Queue processor for deferred OCR and JSON persistence."""

import time
import threading
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from queue import Empty, Full, Queue
from typing import Any, Optional, Literal

from app.api_client import post_market_inventory_capture, post_storage_capture
from app.logs.logger import logger
from app.ocr.reader import read_silver_value, read_storage_name

TASK_QUEUE_MAX_SIZE = 500
TASK_QUEUE_GET_TIMEOUT_SECONDS = 0.5
OCR_MAX_WORKERS = 4


@dataclass
class CaptureTask:
    """Queued capture payload for deferred OCR and persistence."""

    task_type: Literal['market_inventory', 'storage_snapshot']
    captured_at: float
    img_market: Any = None
    img_inventory: Any = None
    img_storage_name: Any = None
    img_storage_value: Any = None


class CaptureQueueProcessor:
    """Background queue processor for OCR and storage writes."""

    def __init__(self) -> None:
        self.task_queue: Queue[CaptureTask] = Queue(maxsize=TASK_QUEUE_MAX_SIZE)
        self._worker_started = False
        self._worker_start_lock = threading.Lock()
        self._ocr_executor = ThreadPoolExecutor(
            max_workers=OCR_MAX_WORKERS,
            thread_name_prefix='ocr-worker'
        )
        self._last_storage_name: Optional[str] = None

    def start(self) -> None:
        """Start queue worker once."""
        with self._worker_start_lock:
            if self._worker_started:
                return

            worker_thread = threading.Thread(
                target=self._worker_loop,
                daemon=True,
                name='capture-queue-worker'
            )
            worker_thread.start()
            self._worker_started = True
            logger.info('Capture queue worker started')

    def enqueue_market_inventory(self, img_market: Any, img_inventory: Any) -> bool:
        """Enqueue a market+inventory OCR task."""
        return self._enqueue(
            CaptureTask(
                task_type='market_inventory',
                captured_at=time.time(),
                img_market=img_market,
                img_inventory=img_inventory,
            )
        )

    def enqueue_storage_snapshot(self, img_storage_name: Any, img_storage_value: Any) -> bool:
        """Enqueue a storage snapshot OCR task."""
        return self._enqueue(
            CaptureTask(
                task_type='storage_snapshot',
                captured_at=time.time(),
                img_storage_name=img_storage_name,
                img_storage_value=img_storage_value,
            )
        )

    def _enqueue(self, task: CaptureTask) -> bool:
        try:
            self.task_queue.put_nowait(task)
            logger.info(
                f"Capture task queued: {task.task_type} | queue_size={self.task_queue.qsize()}"
            )
            return True
        except Full:
            logger.warning(
                f"Capture queue is full ({TASK_QUEUE_MAX_SIZE}). Dropping task: {task.task_type}"
            )
            return False

    def _worker_loop(self) -> None:
        while True:
            try:
                task = self.task_queue.get(timeout=TASK_QUEUE_GET_TIMEOUT_SECONDS)
            except Empty:
                continue

            try:
                if task.task_type == 'market_inventory':
                    self._process_market_inventory_task(task)
                elif task.task_type == 'storage_snapshot':
                    self._process_storage_snapshot_task(task)
            except Exception as error:
                logger.exception(f'Unexpected queue worker error: {error}')
            finally:
                self.task_queue.task_done()

    def _process_market_inventory_task(self, task: CaptureTask) -> None:
        market_future = self._ocr_executor.submit(read_silver_value, task.img_market, 'market')
        inventory_future = self._ocr_executor.submit(read_silver_value, task.img_inventory, 'inventory')

        market_silver = market_future.result()
        inventory_silver = inventory_future.result()

        sent = post_market_inventory_capture(market_silver, inventory_silver)
        if sent:
            logger.info(
                f"Market/Inventory capture saved: market={market_silver} inventory={inventory_silver}"
            )

        logger.info(f'Market/Inventory result → market={market_silver} inventory={inventory_silver}')

    def _process_storage_snapshot_task(self, task: CaptureTask) -> None:
        storage_name = read_storage_name(task.img_storage_name)
        if not storage_name:
            return

        if storage_name == self._last_storage_name:
            return

        silver_value = read_silver_value(task.img_storage_value, source='storage')
        if silver_value is None:
            return

        sent = post_storage_capture(storage_name, silver_value)
        if sent:
            logger.info(f'Storage capture saved: {storage_name} | Silver: {silver_value}')

        logger.info(f'New storage: {storage_name} | Silver: {silver_value}')
        print(f'\nSTORAGE: {storage_name}')
        print(f'SILVER: {silver_value}')
        self._last_storage_name = storage_name
