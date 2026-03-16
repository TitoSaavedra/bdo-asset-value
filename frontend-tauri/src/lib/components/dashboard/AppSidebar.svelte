<script lang="ts">
  import type { ScreenName, ThemeName } from "$lib/dashboard/types";

  const themeOptions: Array<{ value: ThemeName; label: string }> = [
    { value: "desert", label: "Desierto" },
    { value: "midnight", label: "Nocturno" },
    { value: "light", label: "Claro" },
  ];

  let isThemeOpen = $state(false);

  let {
    activeScreen,
    theme,
    apiConnected,
    wsConnected,
    connectionUpdatedAt,
    onScreenChange,
    onThemeChange,
    onRefresh,
    formatConnectionTime,
  }: {
    activeScreen: ScreenName;
    theme: ThemeName;
    apiConnected: boolean;
    wsConnected: boolean;
    connectionUpdatedAt: string | null;
    onScreenChange: (screen: ScreenName) => void;
    onThemeChange: (theme: string) => void;
    onRefresh: () => void | Promise<void>;
    formatConnectionTime: (value: string | null) => string;
  } = $props();

  function currentThemeLabel(): string {
    return themeOptions.find((option) => option.value === theme)?.label ?? "Desierto";
  }
</script>

<aside class="card sidebar">
  <div class="brand">
    <span class="brand-spirit" aria-hidden="true">
      <img class="brand-spirit-fill" src="/blackspirit.svg" alt="" />
      <img class="brand-spirit-outline" src="/blackspirit-outline.svg" alt="" />
    </span>
    <div>
      <h1 class="logo">BDO Asset Value</h1>
    </div>
  </div>

  <div class="menu">
    <button class:active={activeScreen === "dashboard"} onclick={() => onScreenChange("dashboard")}>Dashboard</button>
    {#if false}
    <button class:active={activeScreen === "manual"} onclick={() => onScreenChange("manual")}>Registro manual</button>
    {/if}
    <button class:active={activeScreen === "warehouses"} onclick={() => onScreenChange("warehouses")}>Activos por almacén</button>
    <button class:active={activeScreen === "metrics"} onclick={() => onScreenChange("metrics")}>Métricas</button>
  </div>

  <div class="theme-picker">
    <div id="themePickerLabel" class="theme-picker-label">Tema</div>
    <div
      class="theme-select"
      onfocusout={(event) => {
        const nextTarget = event.relatedTarget as Node | null;
        if (!nextTarget || !(event.currentTarget as HTMLDivElement).contains(nextTarget)) {
          isThemeOpen = false;
        }
      }}
    >
      <button
        class="theme-select-trigger"
        type="button"
        aria-haspopup="listbox"
        aria-expanded={isThemeOpen}
        aria-labelledby="themePickerLabel themeSelectValue"
        onclick={() => (isThemeOpen = !isThemeOpen)}
      >
        <span id="themeSelectValue">{currentThemeLabel()}</span>
        <span class={`theme-select-caret ${isThemeOpen ? "open" : ""}`} aria-hidden="true"></span>
      </button>

      {#if isThemeOpen}
        <div class="theme-select-menu" role="listbox" aria-labelledby="themePickerLabel">
          {#each themeOptions as option}
            <button
              class={`theme-select-option ${theme === option.value ? "active" : ""}`}
              type="button"
              role="option"
              aria-selected={theme === option.value}
              onclick={() => {
                onThemeChange(option.value);
                isThemeOpen = false;
              }}
            >{option.label}</button>
          {/each}
        </div>
      {/if}
    </div>
  </div>

  <div class="connection-card" aria-live="polite">
    <div class="connection-card-title">Conexión</div>
    <div class="connection-grid">
      <span class="connection-label">API</span>
      <span class={`connection-pill ${apiConnected ? "connection-online" : "connection-offline"}`}>
        {apiConnected ? "Conectada" : "Desconectada"}
      </span>
      <span class="connection-label">WebSocket</span>
      <span class={`connection-pill ${wsConnected ? "connection-online" : "connection-offline"}`}>
        {wsConnected ? "Conectado" : "Desconectado"}
      </span>
    </div>
    <div class="connection-updated">{formatConnectionTime(connectionUpdatedAt)}</div>
  </div>
</aside>
