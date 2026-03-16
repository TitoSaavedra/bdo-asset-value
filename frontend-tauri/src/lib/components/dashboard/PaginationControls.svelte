<script lang="ts">
  let {
    currentPage,
    totalItems,
    pageSize,
    onPageChange,
  }: {
    currentPage: number;
    totalItems: number;
    pageSize: number;
    onPageChange: (page: number) => void | Promise<void>;
  } = $props();

  const totalPages = $derived(Math.max(1, Math.ceil(totalItems / Math.max(1, pageSize))));

  const pageNumbers = $derived.by(() => {
    const pages: number[] = [];
    const start = Math.max(1, currentPage - 2);
    const end = Math.min(totalPages, currentPage + 2);

    for (let page = start; page <= end; page += 1) {
      pages.push(page);
    }

    return pages;
  });
</script>

<div class="table-pagination">
  <button class="pagination-btn" onclick={() => onPageChange(currentPage - 1)} disabled={currentPage <= 1}>Anterior</button>

  <div class="pagination-pages" aria-label="Páginas">
    {#if pageNumbers[0] > 1}
      <button class={`pagination-page ${currentPage === 1 ? "active" : ""}`} onclick={() => onPageChange(1)}>1</button>
      {#if pageNumbers[0] > 2}
        <span class="pagination-ellipsis">...</span>
      {/if}
    {/if}

    {#each pageNumbers as page}
      <button class={`pagination-page ${currentPage === page ? "active" : ""}`} onclick={() => onPageChange(page)}>
        {page}
      </button>
    {/each}

    {#if pageNumbers[pageNumbers.length - 1] < totalPages}
      {#if pageNumbers[pageNumbers.length - 1] < totalPages - 1}
        <span class="pagination-ellipsis">...</span>
      {/if}
      <button class={`pagination-page ${currentPage === totalPages ? "active" : ""}`} onclick={() => onPageChange(totalPages)}>
        {totalPages}
      </button>
    {/if}
  </div>

  <span class="pagination-info">Página {currentPage} / {totalPages} · {totalItems} items</span>
  <button class="pagination-btn" onclick={() => onPageChange(currentPage + 1)} disabled={currentPage >= totalPages}>Siguiente</button>
</div>

<style>
  .table-pagination {
    margin-top: 10px;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 8px;
    flex-wrap: wrap;
  }

  .pagination-pages {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    max-width: 100%;
    overflow-x: auto;
    overflow-y: hidden;
    scrollbar-width: thin;
    padding-bottom: 2px;
  }

  .pagination-btn,
  .pagination-page {
    min-width: 34px;
    border: 1px solid var(--border);
    background: linear-gradient(180deg, var(--button-grad-start), var(--button-grad-end));
    color: var(--text);
    border-radius: 10px;
    padding: 6px 10px;
    font-size: 12px;
    font-weight: 800;
    cursor: pointer;
  }

  .pagination-btn {
    white-space: nowrap;
  }

  .pagination-page.active {
    background: linear-gradient(180deg, var(--button-active-start), var(--button-active-end));
    color: var(--button-active-text);
    border-color: rgba(255, 255, 255, 0.2);
  }

  .pagination-info {
    font-size: 12px;
    color: var(--muted);
    font-weight: 700;
    white-space: nowrap;
  }

  .pagination-ellipsis {
    color: var(--muted);
    font-size: 12px;
    font-weight: 700;
    padding: 0 2px;
  }

  @media (max-width: 980px) {
    .table-pagination {
      justify-content: center;
    }

    .pagination-pages {
      order: 3;
      width: 100%;
      justify-content: center;
    }

    .pagination-info {
      order: 2;
      width: 100%;
      text-align: center;
      white-space: normal;
    }
  }
</style>
