(() => {
            const unitNode = document.getElementById('global-weight-unit');
            if (!unitNode) return;
            const unit = JSON.parse(unitNode.textContent) === 'lbs' ? 'lbs' : 'kg';
            document.querySelectorAll('[data-weight-kg]').forEach(el => {
                const value = Number(el.dataset.weightKg);
                if (Number.isFinite(value)) el.textContent = (unit === 'lbs' ? value * 2.20462 : value).toFixed(1);
            });
            document.querySelectorAll('.weight-unit-label').forEach(el => el.textContent = unit);
            const weightInput = document.getElementById('modalWeight');
            if (weightInput) {
                const modalForm = document.getElementById('addEditForm');
                modalForm.addEventListener('submit', () => {
                    if (unit === 'lbs' && weightInput.value) weightInput.value = (Number(weightInput.value) / 2.20462).toFixed(2);
                });
                window.displayWeightValue = value => unit === 'lbs' ? (Number(value) * 2.20462).toFixed(1) : value;
            }
        })();


window.appAlert = function(message, {variant = 'info', duration = 5000} = {}) {
            const region = document.getElementById('app-alerts');
            if (!region) return;
            const item = document.createElement('div');
            item.className = 'app-alert d-flex align-items-start justify-content-between gap-3';
            item.dataset.variant = variant;
            item.setAttribute('role', variant === 'error' ? 'alert' : 'status');
            const text = document.createElement('span');
            text.textContent = message;
            const close = document.createElement('button');
            close.type = 'button';
            close.setAttribute('aria-label', 'Dismiss notification');
            close.innerHTML = '&times;';
            close.addEventListener('click', () => item.remove());
            item.append(text, close);
            region.append(item);
            if (duration > 0) window.setTimeout(() => item.remove(), duration);
        };

        window.appAlertAfterNavigation = function(message, options = {}) {
            try {
                sessionStorage.setItem('tracc-next-toast', JSON.stringify({message, options}));
            } catch (error) {
                window.appAlert(message, options);
            }
        };

        try {
            const queuedToast = sessionStorage.getItem('tracc-next-toast');
            if (queuedToast) {
                sessionStorage.removeItem('tracc-next-toast');
                const {message, options} = JSON.parse(queuedToast);
                window.appAlert(message, options);
            }
        } catch (error) {
            try { sessionStorage.removeItem('tracc-next-toast'); } catch (storageError) {}
        }

        window.appConfirm = function(message, {title = 'Please confirm', confirmLabel = 'Continue', danger = false} = {}) {
            const dialog = document.getElementById('app-confirm-dialog');
            const cancel = document.getElementById('app-confirm-cancel');
            const accept = document.getElementById('app-confirm-accept');
            document.getElementById('app-confirm-title').textContent = title;
            document.getElementById('app-confirm-message').textContent = message;
            accept.textContent = confirmLabel;
            accept.className = danger ? 'btn btn-danger' : 'btn btn-primary';
            return new Promise(resolve => {
                const finish = value => { dialog.close(); resolve(value); };
                cancel.onclick = () => finish(false);
                accept.onclick = () => finish(true);
                dialog.oncancel = event => { event.preventDefault(); finish(false); };
                dialog.onclick = event => { if (event.target === dialog) finish(false); };
                dialog.showModal();
                cancel.focus();
            });
        };

        document.querySelectorAll('[data-app-message]').forEach(item => {
            const variant = item.classList.contains('alert-success') ? 'success'
                : item.classList.contains('alert-warning') ? 'warning'
                : item.classList.contains('alert-danger') || item.classList.contains('alert-error') ? 'error' : 'info';
            const message = item.cloneNode(true);
            message.querySelectorAll('button').forEach(button => button.remove());
            window.appAlert(message.textContent.trim(), {variant});
            item.remove();
        });

        document.querySelectorAll('[data-logout-link]').forEach(link => {
            link.addEventListener('click', () => {
                window.appAlertAfterNavigation('You have been signed out.', {variant: 'success'});
            });
        });

        document.querySelectorAll('[data-export-logs]').forEach(link => {
            link.addEventListener('click', () => {
                window.appAlert('Your CSV export is downloading.', {variant: 'success'});
            });
        });


(function () {
            const loader = document.getElementById("page-loader");

            // Hide loader when page fully loads
            window.addEventListener("load", function () {
                loader.style.opacity = "0";
                setTimeout(() => {
                    loader.style.display = "none";
                }, 300);
            });

            // Browsers may restore the prior page from the back-forward cache,
            // including its visible loader overlay.
            window.addEventListener("pageshow", function () {
                loader.style.opacity = "0";
                loader.style.display = "none";
            });

            function shouldIgnoreLink(link) {
                const href = link.getAttribute("href");

                return (
                    !href ||
                    href.startsWith("#") ||
                    link.protocol !== "http:" && link.protocol !== "https:" ||
                    link.origin !== window.location.origin ||
                    link.target && link.target !== "_self" ||
                    link.hasAttribute("download") ||
                    link.hasAttribute("data-bs-toggle")
                );
            }

            // Show loader on valid link click
            document.addEventListener("click", function (e) {
                if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
                const link = e.target.closest("a");
                if (link && !shouldIgnoreLink(link)) {
                    loader.style.display = "flex";
                    loader.style.opacity = "1";
                }
            });

            // Show loader on form submit
            document.addEventListener("submit", function (event) {
                if (event.defaultPrevented || event.target.target === "_blank" || event.target.method === "dialog") return;
                loader.style.display = "flex";
                loader.style.opacity = "1";
            });
        })();


function openAddModal() {
            document.getElementById('modalTitle').innerText = "Add Weight Log";
            document.getElementById('addEditForm').action = document.body.dataset.addWeightUrl;
            document.getElementById('modalWeight').value = "";
            document.getElementById('modalNotes').value = "";
        }

document.querySelectorAll("[data-open-add-log]").forEach(button => {
    button.addEventListener("click", openAddModal);
});

        if ("serviceWorker" in navigator) {
            navigator.serviceWorker.register(document.body.dataset.serviceWorkerUrl, {scope: "/"}).catch(console.error);
        }

        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
        const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

        const root = document.documentElement;

        // Load saved theme family + mode
        let savedFamily = localStorage.getItem("themeFamily") || "classic";
        let savedMode = localStorage.getItem("themeMode") || "light";

        root.setAttribute("data-theme-family", savedFamily);
        root.setAttribute("data-bs-theme", savedMode);

        const navLinks = document.querySelectorAll('.bottom-navbar a');
        navLinks.forEach(link => {
            if (link.href === window.location.href) {
                link.classList.add('active');
            }
        });
    
        // Summary Line Graph (only when this page has a summary and Chart.js).
        const summaryCanvas = document.getElementById('summChart');
        const summaryDataElement = document.getElementById('summ-line-data');
        if (summaryCanvas && summaryDataElement && window.Chart) {
            const summary_ctx = summaryCanvas.getContext('2d');
            const summlineData = JSON.parse(summaryDataElement.textContent);
            const weights = summlineData.weights || [];
            const minWeight = weights.length ? Math.min(...weights) : 0;
            const maxWeight = weights.length ? Math.max(...weights) : 0;

            new Chart(summary_ctx, {
            type: 'line',
            data: {
                labels: summlineData.labels || [], 
                datasets: [{
                    label: 'Weight',
                    data: weights,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: false,
                        },
                        grid: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--border-bottom-color') || '#cccccc'
                        },
                        ticks: {
                            autoSkip: true,
                            maxRotation: 45,
                            minRotation: 0,
                        },
                    },
                    y: {
                        title: {
                            display: false,
                        },
                        grid: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--border-bottom-color') || '#cccccc'
                        },
                        beginAtZero: false,
                        suggestedMin: minWeight - 2,
                        suggestedMax: maxWeight + 2
                    }
                }
            }
            });
        }
        
        // Weekly Summary.
        let currPage = 1;

        const prevBtn = document.getElementById("summ-btn-prev");
        const nextBtn = document.getElementById("summ-btn-next");
        const gtaBtn  = document.getElementById("summ-btn-gta");
        const page1Div = document.getElementById("page-1");
        const page2Div = document.getElementById("page-2");

        function toggleVisibility(el, show) {
            el.classList.toggle("d-block", show);
            el.classList.toggle("d-none", !show);
        }

        function changePage(incr = 0) {
            currPage = incr === 0 ? 1 : currPage + incr;

            // page 1
            if (currPage === 1) {
                toggleVisibility(prevBtn, false);
                toggleVisibility(gtaBtn, false);
                toggleVisibility(nextBtn, true);
                toggleVisibility(page1Div, true);
                toggleVisibility(page2Div, false);
            }

            // page 2
            else if (currPage === 2) {
                toggleVisibility(prevBtn, true);
                toggleVisibility(gtaBtn, true);
                toggleVisibility(nextBtn, false);
                toggleVisibility(page1Div, false);
                toggleVisibility(page2Div, true);
            }
        }

        document.querySelectorAll("[data-summary-page]").forEach(button => {
            button.addEventListener("click", () => changePage(Number(button.dataset.summaryPage)));
        });
