<script lang="ts">
  import type { ScreenName, ThemeName } from "$lib/dashboard/types";

  type DensityMode = "normal" | "compact";
  type ThemeOption = { value: ThemeName; label: string; accent: string };

  const themeOptions: ThemeOption[] = [
    { value: "desert", label: "Desierto", accent: "#c8a96a" },
    { value: "midnight", label: "Nocturno", accent: "#63c3ff" },
    { value: "light", label: "Claro", accent: "#4e78d8" },
    { value: "darcula", label: "Darcula", accent: "#ffc66d" },
    { value: "onedark", label: "One Dark Pro", accent: "#e5c07b" },
    { value: "monokai", label: "Monokai", accent: "#e6db74" },
    { value: "solarized", label: "Solarized Dark", accent: "#b58900" },
    { value: "draculanight", label: "Dracula At Night", accent: "#bb9af7" },
    { value: "tokyonight", label: "Tokyo Night", accent: "#7aa2f7" },
    { value: "githubdark", label: "GitHub Dark", accent: "#58a6ff" },
    { value: "nord", label: "Nord", accent: "#81a1c1" },
    { value: "palenight", label: "Palenight", accent: "#c792ea" },
    { value: "materialocean", label: "Material Ocean", accent: "#89ddff" },
    { value: "catppuccinmocha", label: "Catppuccin Mocha", accent: "#cba6f7" },
  ];

  let isThemeOpen = $state(false);

  let {
    activeScreen,
    theme,
    density,
    apiConnected,
    wsConnected,
    connectionUpdatedAt,
    onScreenChange,
    onThemeChange,
    onThemePreview,
    onDensityChange,
    onRefresh,
    formatConnectionTime,
  }: {
    activeScreen: ScreenName;
    theme: ThemeName;
    density: DensityMode;
    apiConnected: boolean;
    wsConnected: boolean;
    connectionUpdatedAt: string | null;
    onScreenChange: (screen: ScreenName) => void;
    onThemeChange: (theme: string) => void;
    onThemePreview: (theme: string | null) => void;
    onDensityChange: (density: DensityMode) => void;
    onRefresh: () => void | Promise<void>;
    formatConnectionTime: (value: string | null) => string;
  } = $props();

  function currentThemeLabel(): string {
    return themeOptions.find((option) => option.value === theme)?.label ?? "Desierto";
  }

  function currentThemeOption(): ThemeOption {
    return themeOptions.find((option) => option.value === theme) ?? themeOptions[0];
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
          onThemePreview(null);
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
        style={`--theme-accent: ${currentThemeOption().accent};`}
        onclick={() => (isThemeOpen = !isThemeOpen)}
      >
        <span class="theme-trigger-content">
          <span class="theme-trigger-labels">
            <span class="theme-trigger-kicker">Tema activo</span>
            <span id="themeSelectValue">{currentThemeLabel()}</span>
          </span>
        </span>
        <span class={`theme-select-caret ${isThemeOpen ? "open" : ""}`} aria-hidden="true"></span>
      </button>

      {#if isThemeOpen}
        <div
          class="theme-select-menu"
          role="listbox"
          aria-labelledby="themePickerLabel"
          tabindex="-1"
          onmouseleave={() => onThemePreview(null)}
        >
          {#each themeOptions as option}
            <button
              class={`theme-select-option ${theme === option.value ? "active" : ""}`}
              type="button"
              role="option"
              aria-selected={theme === option.value}
              style={`--theme-accent: ${option.accent};`}
              onmouseenter={() => onThemePreview(option.value)}
              onfocus={() => onThemePreview(option.value)}
              onclick={() => {
                onThemeChange(option.value);
                isThemeOpen = false;
              }}
            >
              <span class="theme-option-accent" style={`background: var(--theme-accent);`}></span>
              <span class="theme-option-main">
                <span class="theme-option-labels">
                  <span class="theme-option-label">{option.label}</span>
                  <span class="theme-option-value">{option.value}</span>
                </span>
              </span>
            </button>
          {/each}
        </div>
      {/if}
    </div>
  </div>

  <div class="density-picker">
    <div class="theme-picker-label">Vista</div>
    <div class="density-toggle" role="group" aria-label="Densidad visual">
      <button
        type="button"
        class={`density-option ${density === "normal" ? "active" : ""}`}
        aria-pressed={density === "normal"}
        onclick={() => onDensityChange("normal")}
      >Normal</button>
      <button
        type="button"
        class={`density-option ${density === "compact" ? "active" : ""}`}
        aria-pressed={density === "compact"}
        onclick={() => onDensityChange("compact")}
      >Compacto</button>
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
