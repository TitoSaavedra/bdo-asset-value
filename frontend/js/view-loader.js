export async function loadScreenViews() {
    const screens = Array.from(document.querySelectorAll('.screen[data-view]'));

    await Promise.all(screens.map(async (screen) => {
        const viewPath = screen.dataset.view;
        if (!viewPath) {
            return;
        }

        try {
            const response = await fetch(viewPath, { cache: 'no-cache' });
            if (!response.ok) {
                screen.innerHTML = `<section class="card panel"><div class="status">No se pudo cargar la vista: ${viewPath}</div></section>`;
                return;
            }

            screen.innerHTML = await response.text();
        } catch (error) {
            screen.innerHTML = `<section class="card panel"><div class="status">Error cargando vista: ${error?.message || 'desconocido'}</div></section>`;
        }
    }));
}
