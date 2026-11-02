function getCssVar(name) {
        return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    }

    document.addEventListener("DOMContentLoaded", () => {
        const calendarEl = document.getElementById('calendar');
        const eventsNode = document.getElementById("calendar-events");
        if (!window.Chart) return;
        if (calendarEl && eventsNode && window.FullCalendar) {
        const events = JSON.parse(eventsNode.textContent);

        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            height: "auto",
            fixedWeekCount: false,   // disables extra weeks
            // showNonCurrentDates: false, // hides prev/next month leftover days
            headerToolbar: {
                left: 'prev',
                center: 'title',
                right: 'next'
            },
            dateClick: function(info) {
                window.appAlert('Selected date: ' + info.dateStr);
            },
            events: events.map(ev => ({
                start: ev.date,
                allDay: true,
                extendedProps: { type: ev.type }
            })),
            eventContent: function(arg) {
                let iconHtml = '';
                if (arg.event.extendedProps.type === "streak") {
                    iconHtml = `<i class="bi bi-fire streaks-icon front-icon"></i><span class="mini-inner-fire"></span>`;
                } else if (arg.event.extendedProps.type === "checkin") {
                    iconHtml = `<i class="bi bi-check2 check-in-icon"></i>`;
                }
                return { 
                    html: `<div class="fc-event-icon">${iconHtml}</div>` 
                };
            }
        });

        // Render calendar only when modal is shown
        const calendarModal = document.getElementById('calendarModal');
        calendarModal.addEventListener('shown.bs.modal', () => {
            calendar.render();
        });
        }

        // Line Graph (Progress)
        const progress_ctx = document.getElementById('progressChart').getContext('2d');
        const lineData = JSON.parse(document.getElementById('line-data').textContent);

        // Store original data
        const lineLabels = [...lineData.labels];
        const lineWeights = [...lineData.weights];

        const progressChart = new Chart(progress_ctx, {
            type: 'line',
            data: {
                labels: lineData.labels,
                datasets: [{
                    label: 'Weight',
                    data: lineData.weights,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    fill: false,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    pointHitRadius: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'nearest',
                    intersect: false,
                    axis: 'x'
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            title: function(items) {
                                return items.length ? `Date: ${items[0].label}` : '';
                            },
                            label: function(ctx) {
                                return `Weight: ${Number(ctx.parsed.y).toFixed(1)} kg`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            display: false   // hides month labels on X-axis
                        },
                    },
                    y: {
                        ticks: {
                            display: false   // hides month labels on X-axis
                        },
                    },
                }
            }
        });

        // Bar Graph (Daily Changes)
        const weight_change_ctx = document.getElementById('weightChangeChart').getContext('2d');
        const dailyChanges = JSON.parse(document.getElementById('daily-changes-data').textContent);

        // Store original data
        const dcLabels = dailyChanges.map(entry => entry.date);
        const dcWeights = dailyChanges.map(entry => entry.change);
        
        const dailyChangeChart = new Chart(weight_change_ctx, {
            type: 'bar',
            data: {
                labels: dcLabels,
                datasets: [{
                    label: 'Daily Change (kg)',
                    data: dcWeights,
                    backgroundColor: dailyChanges.map(entry => entry.change < 0 ? 'rgba(75, 192, 192, 0.6)' : 'rgba(255, 99, 132, 0.6)'),
                    borderColor: dailyChanges.map(entry => entry.change < 0 ? 'rgba(75, 192, 192, 1)' : 'rgba(255, 99, 132, 1)'),
                    borderWidth: 1
                }]
            },
            options: { 
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'nearest',
                    intersect: false,
                    axis: 'x'
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            title: function(items) {
                                return items.length ? `Date: ${items[0].label}` : '';
                            },
                            label: function(ctx) {
                                const change = Number(ctx.parsed.y);
                                const sign = change > 0 ? '+' : '';
                                return `Change: ${sign}${change.toFixed(1)} kg`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            display: false
                        },
                    },
                }
            }
        });

        // Weight Zones - Donut with BMI in center
        const zone_ctx = document.getElementById('zonesGraph').getContext('2d');
        const weight_zones = JSON.parse(document.getElementById('weight-zones-data').textContent);
        const current_bmi = JSON.parse(document.getElementById('current-bmi').textContent);

        new Chart(zone_ctx, {
            type: 'doughnut',  // donut chart
            data: {
                labels: weight_zones.map(entry => entry.label),
                datasets: [{
                    label: 'BMI Zones',
                    data: weight_zones.map(entry => entry.count),
                    backgroundColor: weight_zones.map(entry => getCssVar(entry.color)),
                    hoverOffset: 6,
                    borderWidth: 2,
                    borderColor: "#fff"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%', // makes it a donut
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            padding: 12,
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) {
                                return `${ctx.label}: ${ctx.parsed} days`;
                            }
                        }
                    }
                }
            },
            plugins: [{
                id: 'bmiCenterText',
                beforeDraw: (chart) => {
                    const { ctx, chartArea: {left, right, top, bottom} } = chart;
                    ctx.save();

                    const centerX = (left + right) / 2;
                    const centerY = (top + bottom) / 2;

                    ctx.font = `${(chart.height / 8).toFixed(0)}px ${getCssVar("--bs-font-sans-serif")}, system-ui, sans-serif`;
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = getCssVar('--text-color');

                    const text = current_bmi ? current_bmi.toFixed(1) : "N/A";
                    ctx.fillText(text, centerX, centerY);
                    ctx.restore();
                }
            }]
        });
        
        // Monthly Avg,
        const monthly_ctx = document.getElementById('monthlyGraph').getContext('2d');
        const monthly_avg = JSON.parse(document.getElementById('monthly-avg-data').textContent);

        new Chart(monthly_ctx, {
            type: 'bar',
            data: {
                labels: monthly_avg.map(entry => entry.month),
                datasets: [
                    {
                        label: 'Avg Weight (kg)',
                        data: monthly_avg.map(entry => entry.avg_weight),
                        borderColor: getCssVar('--text-color'),
                        backgroundColor: getCssVar('--text-color'),
                        tension: 0.3,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Avg BMI',
                        data: monthly_avg.map(entry => entry.avg_bmi),
                        borderColor: getCssVar('--accent-color'),
                        backgroundColor: getCssVar('--accent-color'),
                        borderDash: [5, 5], // dashed line to differentiate
                        tension: 0.3,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) {
                                if (ctx.dataset.label.includes("Weight")) {
                                    return ctx.parsed.y + " kg";
                                }
                                if (ctx.dataset.label.includes("BMI")) {
                                    return ctx.parsed.y;
                                }
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Weight (kg)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false
                        },
                        title: {
                            display: true,
                            text: 'BMI'
                        }
                    }
                }
            }
        });

        window.filterData = function(range, chart) {
            const today = new Date();
            let filteredLabels = [];
            let filteredWeights = [];

            // Update chart data
            let chart_ctx = null;
            if (chart == "p") {
                chart_ctx = progressChart;
                lineLabels.forEach((dateStr, index) => {
                    const [day, month, year] = dateStr.split('-');
                    const date = new Date(`${month}-${day}-${year}`);
                    const diffDays = (today - date) / (1000 * 60 * 60 * 24);

                    if (
                        (range === '1W' && diffDays <= 7) ||
                        (range === '1M' && diffDays <= 30) ||
                        (range === '3M' && diffDays <= 90) ||
                        (range === '6M' && diffDays <= 180) ||
                        range === 'ALL'
                    ) {
                        filteredLabels.push(dateStr);
                        filteredWeights.push(lineWeights[index]);
                    }
                });
            } else if (chart == "d") {
                chart_ctx = dailyChangeChart;
                dcLabels.forEach((dateStr, index) => {
                    const [day, month, year] = dateStr.split('-');
                    const date = new Date(`${month}-${day}-${year}`);
                    const diffDays = (today - date) / (1000 * 60 * 60 * 24);

                    if (
                        (range === '1W' && diffDays <= 7) ||
                        (range === '1M' && diffDays <= 30) ||
                        (range === '3M' && diffDays <= 90) ||
                        (range === '6M' && diffDays <= 180) ||
                        range === 'ALL'
                    ) {
                        filteredLabels.push(dateStr);
                        filteredWeights.push(dcWeights[index]);
                    }
                });
            }
            chart_ctx.data.labels = filteredLabels;
            chart_ctx.data.datasets[0].data = filteredWeights;
            if (chart === 'd') {
                chart_ctx.data.datasets[0].backgroundColor = filteredWeights.map(change => change < 0 ? 'rgba(75, 192, 192, 0.6)' : 'rgba(255, 99, 132, 0.6)');
                chart_ctx.data.datasets[0].borderColor = filteredWeights.map(change => change < 0 ? 'rgba(75, 192, 192, 1)' : 'rgba(255, 99, 132, 1)');
            }
            chart_ctx.update();
        };

        document.querySelectorAll(".line-filters[data-range]").forEach(input => {
            input.addEventListener("change", () => window.filterData(input.dataset.range, input.dataset.chart));
        });

        filterData('1M', 'p');
        filterData('1M', 'd');
    });
