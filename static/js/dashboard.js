function markChecked(summaryId) {
    fetch(`/weekly-summary-check/${summaryId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(async response => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Could not update the summary.");
        return data;
    })
    .then(data => {
        if (data.status === "success") {
            document.querySelector('.dashboard-summary-card')?.remove();
            window.appAlert("Weekly summary marked as viewed.", {variant: "success"});
        }
    })
    .catch(error => window.appAlert(error.message || "Could not update the summary.", {variant: "error"}));
}

document.querySelectorAll("[data-mark-summary]").forEach(card => {
    card.addEventListener("click", () => markChecked(card.dataset.summaryId));
});
        document.addEventListener("DOMContentLoaded", () => {
            // Clock in time localization.
            const el = document.getElementById("clock-in-time");
            if (el) {
                const utcString = el.dataset.utc;
                if (utcString) {
                    const localDate = new Date(utcString);
                    if (!isNaN(localDate)) {
                        el.textContent = localDate.toLocaleString([], { 
                            hour: "2-digit", 
                            minute: "2-digit" 
                        });
                    }
                }
            }

            // Progress Circle Animation.
            const progressCircle = document.getElementById('progressIndicator');
            const offsetInput = document.getElementById('progress_offset');
            
            if (progressCircle && offsetInput) {
                const offset = parseFloat(offsetInput.value);
                // Trigger smooth animation
                progressCircle.setAttribute('stroke-dashoffset', offset);
            }

            // Greeting
            const h = new Date().getHours();
            let g = "Hello";
            let icon = '<i class="bi bi-stars"></i>';
            if (h < 12) g = "Good Morning";
            else if (h < 17) g = "Good Afternoon";
            else g = "Good Evening";

            const userName = document.getElementById("greet").dataset.userName;
            document.getElementById("greet").textContent = `${g}, ${userName}!`;

            // Line Graph.
            const progress_ctx = document.getElementById('progressChart').getContext('2d');
            const lineData = JSON.parse(document.getElementById('line-data').textContent);

            let weights = lineData.weights || [];
            let minWeight = weights.length ? Math.min(...weights) : 0;
            let maxWeight = weights.length ? Math.max(...weights) : 0;

            new Chart(progress_ctx, {
                type: 'line',
                data: {
                    labels: lineData.labels || [], 
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
                                display: true,
                                text: 'Date'
                            },
                            ticks: {
                                autoSkip: false,
                                maxRotation: 45,
                                minRotation: 45
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Weight (kg)'
                            },
                            beginAtZero: false,
                            suggestedMin: minWeight - 2,
                            suggestedMax: maxWeight + 2
                        }
                    }
                }
            });
        });
