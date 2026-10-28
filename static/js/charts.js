/**
 * Amazon E-Commerce Data Warehouse - Chart.js Helper Service
 * Configures theme-aware defaults and factory methods for line, bar, doughnut, and scatter charts.
 */

const ChartFactory = {
    // Generate base options with active theme colors
    getBaseOptions: function (title = "") {
        const colors = window.getChartThemeColors();
        return {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 600,
                easing: "easeOutQuart"
            },
            plugins: {
                legend: {
                    display: true,
                    position: "top",
                    labels: {
                        color: colors.text,
                        font: {
                            family: "'Plus Jakarta Sans', sans-serif",
                            weight: 600,
                            size: 12
                        },
                        boxWidth: 14,
                        padding: 15
                    }
                },
                tooltip: {
                    backgroundColor: colors.tooltipBg,
                    titleColor: colors.tooltipText,
                    bodyColor: colors.tooltipText,
                    borderColor: colors.grid,
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8,
                    titleFont: { family: "'Plus Jakarta Sans', sans-serif", weight: 700, size: 13 },
                    bodyFont: { family: "'JetBrains Mono', monospace", size: 12 }
                },
                title: {
                    display: !!title,
                    text: title,
                    color: colors.text,
                    font: { family: "'Plus Jakarta Sans', sans-serif", weight: 700, size: 14 }
                }
            },
            scales: {
                x: {
                    grid: { color: colors.grid, drawBorder: false },
                    ticks: {
                        color: colors.ticks,
                        font: { family: "'Plus Jakarta Sans', sans-serif", size: 11, weight: 500 }
                    }
                },
                y: {
                    grid: { color: colors.grid, drawBorder: false },
                    ticks: {
                        color: colors.ticks,
                        font: { family: "'Plus Jakarta Sans', sans-serif", size: 11, weight: 500 }
                    }
                }
            }
        };
    },

    // Build or update a Line Chart
    createLineChart: function (canvas, labels, datasets, customOptions = {}) {
        const base = this.getBaseOptions();
        const options = Object.assign({}, base, customOptions);

        if (canvas.chartInstance) {
            window.unregisterChartInstance(canvas.chartInstance);
            canvas.chartInstance.destroy();
        }

        const chart = new Chart(canvas, {
            type: "line",
            data: { labels: labels, datasets: datasets },
            options: options
        });

        canvas.chartInstance = chart;
        window.registerChartInstance(chart);
        return chart;
    },

    // Build or update a Bar Chart
    createBarChart: function (canvas, labels, datasets, customOptions = {}) {
        const base = this.getBaseOptions();
        const options = Object.assign({}, base, customOptions);

        if (canvas.chartInstance) {
            window.unregisterChartInstance(canvas.chartInstance);
            canvas.chartInstance.destroy();
        }

        const chart = new Chart(canvas, {
            type: "bar",
            data: { labels: labels, datasets: datasets },
            options: options
        });

        canvas.chartInstance = chart;
        window.registerChartInstance(chart);
        return chart;
    },

    // Build or update a Doughnut Chart
    createDoughnutChart: function (canvas, labels, data, bgColors, customOptions = {}) {
        const colors = window.getChartThemeColors();
        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "right",
                    labels: {
                        color: colors.text,
                        font: { family: "'Plus Jakarta Sans', sans-serif", weight: 600, size: 12 },
                        padding: 12
                    }
                },
                tooltip: {
                    backgroundColor: colors.tooltipBg,
                    titleColor: colors.tooltipText,
                    bodyColor: colors.tooltipText,
                    padding: 12,
                    cornerRadius: 8
                }
            },
            cutout: "68%"
        };

        const options = Object.assign({}, defaultOptions, customOptions);

        if (canvas.chartInstance) {
            window.unregisterChartInstance(canvas.chartInstance);
            canvas.chartInstance.destroy();
        }

        const chart = new Chart(canvas, {
            type: "doughnut",
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: bgColors,
                    borderWidth: 2,
                    borderColor: colors.grid
                }]
            },
            options: options
        });

        canvas.chartInstance = chart;
        window.registerChartInstance(chart);
        return chart;
    },

    // Build or update a 2D Scatter Chart
    createScatterChart: function (canvas, datasets, customOptions = {}) {
        const base = this.getBaseOptions();
        const options = Object.assign({}, base, customOptions);

        if (canvas.chartInstance) {
            window.unregisterChartInstance(canvas.chartInstance);
            canvas.chartInstance.destroy();
        }

        const chart = new Chart(canvas, {
            type: "scatter",
            data: { datasets: datasets },
            options: options
        });

        canvas.chartInstance = chart;
        window.registerChartInstance(chart);
        return chart;
    }
};
