// root declared in base.html.
const settings_root = document.documentElement;
const toggleBtn = document.getElementById("theme-toggle"); // navbar one
const themeSelect = document.getElementById("themeSelect");
const radioLight = document.getElementById("light");
const radioDark = document.getElementById("dark");

// Load saved theme family + mode
let localFamily = localStorage.getItem("themeFamily") || "classic";
let localMode = localStorage.getItem("themeMode") || "light";

setTheme(localFamily, localMode);
themeSelect.value = localFamily;

// Handle theme select change
themeSelect.addEventListener("change", (e) => {
    localFamily = e.target.value;
    localStorage.setItem("themeFamily", localFamily);
    setTheme(localFamily, localMode);
});

// Handle navbar toggle (icon button)
if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
        localMode = localMode === "light" ? "dark" : "light";
        localStorage.setItem("themeMode", localMode);
        setTheme(localFamily, localMode);
        updateRadio(localMode);
    });
}

// Handle settings page radios
radioLight.addEventListener("change", () => {
    if (radioLight.checked) {
        localMode = "light";
        localStorage.setItem("themeMode", localMode);
        setTheme(localFamily, localMode);
    }
});

radioDark.addEventListener("change", () => {
    if (radioDark.checked) {
        localMode = "dark";
        localStorage.setItem("themeMode", localMode);
        setTheme(localFamily, localMode);
    }
});

function setTheme(family, mode) {
    settings_root.setAttribute("data-theme-family", family);
    settings_root.setAttribute("data-bs-theme", mode);

    // update navbar toggle icon
    if (toggleBtn) {
        toggleBtn.innerHTML = mode === "light"
            ? '<i class="bi bi-moon"></i>'
            : '<i class="bi bi-sun"></i>';
    }

    // update settings page radios
    updateRadio(mode);
}

function updateRadio(mode) {
    if (mode === "light") {
        radioLight.checked = true;
        radioDark.checked = false;
    } else {
        radioLight.checked = false;
        radioDark.checked = true;
    }
}