# TODO

## Prioridad Alta

- Reducir recálculo completo del dashboard en broadcasts de actualización.
- Añadir sincronización más robusta de escritura entre entradas concurrentes.

## Prioridad Media

- Reutilizar instancia de captura (`mss`) para bajar overhead.
- Mejorar gestión de conexiones WebSocket caídas.
- Exponer métricas de cola OCR (`enqueued`, `processed`, `dropped`, `queue_size`).

## Quick Wins

- Eventos WS livianos y refresco de dashboard con debounce en frontend.
- Ajustar TTL de cache de dashboard según carga real.
- Separar proceso OCR/hotkeys del proceso API en producción.
