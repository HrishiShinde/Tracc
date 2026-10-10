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

function autoSaveSetting(payload) {
    const saveStatus = document.getElementById("settings-save-status");
    if (saveStatus) saveStatus.textContent = "Saving…";
    fetch("/settings/", {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify(payload)
    })
    .then(async res => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Could not save setting.");
        return data;
    })
    .then(data => {
        if (data.success) {
            if (saveStatus) saveStatus.textContent = "All changes saved.";
        }
    })
    .catch(error => {
        console.error("Error saving setting:", error);
        if (saveStatus) saveStatus.textContent = error.message;
    });
}
