const settingsRoot = document.documentElement;
const toggleBtn = document.getElementById("theme-toggle");
const themeSelect = document.getElementById("themeSelect");
const radioLight = document.getElementById("light");
const radioDark = document.getElementById("dark");
const canSavePreferences = Boolean(document.body?.dataset.settingsUrl);

let localFamily = settingsRoot.dataset.themeFamily || localStorage.getItem("themeFamily") || "classic";
let localMode = settingsRoot.dataset.bsTheme || localStorage.getItem("themeMode") || "light";
setTheme(localFamily, localMode);
if (themeSelect) themeSelect.value = localFamily;

async function persistTheme(payload, previousFamily, previousMode) {
    if (!canSavePreferences || typeof autoSaveSetting !== "function") return;
    const saved = await autoSaveSetting(payload);
    if (saved) return;

    localFamily = previousFamily;
    localMode = previousMode;
    localStorage.setItem("themeFamily", localFamily);
    localStorage.setItem("themeMode", localMode);
    setTheme(localFamily, localMode);
    if (themeSelect) themeSelect.value = localFamily;
}

if (themeSelect) {
    themeSelect.addEventListener("change", async event => {
        const previousFamily = localFamily;
        const previousMode = localMode;
        localFamily = event.target.value;
        localStorage.setItem("themeFamily", localFamily);
        setTheme(localFamily, localMode);
        await persistTheme({ theme_family: localFamily }, previousFamily, previousMode);
    });
}

function setMode(mode) {
    const previousFamily = localFamily;
    const previousMode = localMode;
    localMode = mode;
    localStorage.setItem("themeMode", localMode);
    setTheme(localFamily, localMode);
    persistTheme({ theme_mode: localMode }, previousFamily, previousMode);
}

if (toggleBtn) {
    toggleBtn.addEventListener("click", () => setMode(localMode === "light" ? "dark" : "light"));
}
radioLight?.addEventListener("change", () => { if (radioLight.checked) setMode("light"); });
radioDark?.addEventListener("change", () => { if (radioDark.checked) setMode("dark"); });

function setTheme(family, mode) {
    settingsRoot.setAttribute("data-theme-family", family);
    settingsRoot.setAttribute("data-bs-theme", mode);
    if (toggleBtn) {
        toggleBtn.innerHTML = mode === "light"
            ? '<i class="bi bi-moon"></i>'
            : '<i class="bi bi-sun"></i>';
    }
    if (radioLight) radioLight.checked = mode === "light";
    if (radioDark) radioDark.checked = mode === "dark";
}
