# Frontend Tauri (SvelteKit)

Cliente desktop para `bdo-asset-value`.

## Desarrollo

Desde `frontend-tauri/`:

```bash
pnpm install
pnpm tauri dev
```

Variables de entorno opcionales:

- `VITE_API_BASE_URL` (default: `http://127.0.0.1:8000`)
- `VITE_WS_URL` (default derivado de `VITE_API_BASE_URL`)

## Build

```bash
pnpm build
pnpm tauri build
```
