/**
 * Amazon E-Commerce Data Warehouse - Theme Manager
 * Handles dual light/dark mode with no-flash initial render, localStorage persistence,
 * system preference fallbacks, and real-time Chart.js theme updating without reload.
 */

(function () {
    const THEME_KEY = "amazon_dw_theme";
    const activeCharts = new Set();

    // 1. Initial theme resolution
    function getPreferredTheme() {
        const stored = localStorage.getItem(THEME_KEY);
        if (stored === "light" || stored === "dark") {
            return stored;
        }
        return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }

    // Apply immediately to prevent flash
    const currentTheme = getPreferredTheme();
    document.documentElement.setAttribute("data-theme", currentTheme);

    // 2. Register active Chart.js instances for dynamic re-coloring
    window.registerChartInstance = function (chartInstance) {
        if (chartInstance) {
            activeCharts.add(chartInstance);
        }
    };

    window.unregisterChartInstance = function (chartInstance) {
        activeCharts.delete(chartInstance);
    };

    // 3. Theme color definitions for Chart.js
    window.getChartThemeColors = function () {
        const isDark = document.documentElement.getAttribute("data-theme") === "dark";
        return {
            grid: isDark ? "rgba(51, 65, 85, 0.5)" : "rgba(226, 232, 240, 0.8)",
            ticks: isDark ? "#94a3b8" : "#64748b",
            text: isDark ? "#f8fafc" : "#0f172a",
            tooltipBg: isDark ? "#1f2937" : "#0f172a",
            tooltipText: "#ffffff",
            primary: isDark ? "#818cf8" : "#4f46e5",
            secondary: isDark ? "#38bdf8" : "#0284c7",
            accent: isDark ? "#34d399" : "#10b981",
            warning: isDark ? "#fbbf24" : "#f59e0b",
            danger: isDark ? "#f87171" : "#ef4444"
        };
    };

    // 4. Update all active charts without page reload
    function updateChartsTheme() {
        const colors = window.getChartThemeColors();
        activeCharts.forEach((chart) => {
            if (!chart || !chart.options) return;

            // Update Scales
            if (chart.options.scales) {
                Object.keys(chart.options.scales).forEach((axisKey) => {
                    const axis = chart.options.scales[axisKey];
                    if (axis.grid) axis.grid.color = colors.grid;
                    if (axis.ticks) axis.ticks.color = colors.ticks;
                    if (axis.title) axis.title.color = colors.ticks;
                });
            }

            // Update Plugins (Legend & Tooltips)
            if (chart.options.plugins) {
                if (chart.options.plugins.legend && chart.options.plugins.legend.labels) {
                    chart.options.plugins.legend.labels.color = colors.text;
                }
                if (chart.options.plugins.tooltip) {
                    chart.options.plugins.tooltip.backgroundColor = colors.tooltipBg;
                    chart.options.plugins.tooltip.titleColor = colors.tooltipText;
                    chart.options.plugins.tooltip.bodyColor = colors.tooltipText;
                    chart.options.plugins.tooltip.borderColor = colors.grid;
                }
            }

            chart.update("none"); // Smooth update without jarring re-animation
        });
    }

    // 5. Toggle theme function
    window.toggleTheme = function () {
        const current = document.documentElement.getAttribute("data-theme") || "light";
        const next = current === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", next);
        localStorage.setItem(THEME_KEY, next);
        updateChartsTheme();
    };

    // Listen for OS scheme changes if user hasn't explicitly set preference
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
        if (!localStorage.getItem(THEME_KEY)) {
            const newTheme = e.matches ? "dark" : "light";
            document.documentElement.setAttribute("data-theme", newTheme);
            updateChartsTheme();
        }
    });

    // Wire up toggle button on DOM ready
    document.addEventListener("DOMContentLoaded", () => {
        const btn = document.getElementById("theme-toggle-btn");
        if (btn) {
            btn.addEventListener("click", window.toggleTheme);
        }
    });
})();
