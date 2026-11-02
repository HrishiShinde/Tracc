function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie("csrftoken");

async function autoSaveSetting(payload, {successMessage = "Settings saved."} = {}) {
    let success = false;
    let errorMessage = "";
    try {
        const response = await fetch("/settings/", {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrftoken,
            },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || "Could not save setting.");
        success = true;
    } catch (error) {
        console.error("Error saving setting:", error);
        errorMessage = error.message || "Could not save settings.";
    }
    if (success) window.appAlert(successMessage, {variant: "success"});
    else window.appAlert(errorMessage, {variant: "error"});
    return success;
}
