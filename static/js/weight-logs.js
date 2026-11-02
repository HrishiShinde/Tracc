function openEditModal(id, weight, notes) {
    document.getElementById('modalTitle').innerText = "Edit Weight Log";
    document.getElementById('addEditForm').action = `/logs/${id}/edit/`;
    document.getElementById('modalWeight').value = window.displayWeightValue ? window.displayWeightValue(weight) : weight;
    document.getElementById('modalNotes').value = notes;
}

function openDeleteModal(id, weight) {
    document.getElementById('deleteForm').action = `/logs/${id}/delete/`;
    document.getElementById('deleteLogInfo').innerText = weight + " kg";
}

function showEditLog(element) {
    openEditModal(element.dataset.logId, element.dataset.logWeight, element.dataset.logNotes || "");
    bootstrap.Modal.getOrCreateInstance(document.getElementById("addEditModal")).show();
}

document.querySelectorAll("[data-edit-log]").forEach(row => {
    row.addEventListener("click", () => showEditLog(row));
});
document.querySelectorAll("[data-log-edit]").forEach(button => {
    button.addEventListener("click", event => {
        event.stopPropagation();
        showEditLog(button);
    });
});
document.querySelectorAll("[data-log-delete]").forEach(button => {
    button.addEventListener("click", event => {
        event.stopPropagation();
        openDeleteModal(button.dataset.logId, button.dataset.logWeight);
        bootstrap.Modal.getOrCreateInstance(document.getElementById("deleteModal")).show();
    });
});
