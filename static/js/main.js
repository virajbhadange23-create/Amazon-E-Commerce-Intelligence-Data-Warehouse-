/**
 * Amazon E-Commerce Data Warehouse - Global UI Utilities
 */

const App = {
    // Format numeric value into Indian Rupee currency (₹24,990)
    formatCurrency: function (num, decimals = 0) {
        if (num === null || num === undefined || isNaN(num)) return "₹0";
        return new Intl.NumberFormat("en-IN", {
            style: "currency",
            currency: "INR",
            maximumFractionDigits: decimals,
            minimumFractionDigits: decimals
        }).format(num);
    },

    // Format numbers with commas (e.g. 45,890)
    formatNumber: function (num) {
        if (num === null || num === undefined || isNaN(num)) return "0";
        return new Intl.NumberFormat("en-IN").format(num);
    },

    // Format percentages (e.g. 24.5%)
    formatPercent: function (num) {
        if (num === null || num === undefined || isNaN(num)) return "0%";
        return `${Number(num).toFixed(1)}%`;
    },

    // Toast alert notifications
    showToast: function (message, type = "info") {
        let container = document.getElementById("toast-container");
        if (!container) {
            container = document.createElement("div");
            container.id = "toast-container";
            document.body.appendChild(container);
        }

        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        toast.textContent = message;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateY(10px)";
            setTimeout(() => toast.remove(), 250);
        }, 3500);
    },

    // Centralized API fetch wrapper with JSON parsing and error handling
    fetchAPI: async function (url, options = {}) {
        try {
            const response = await fetch(url, options);
            const data = await response.json();
            if (!response.ok || data.success === false) {
                const err = data.error || `HTTP error ${response.status}`;
                throw new Error(err);
            }
            return data;
        } catch (error) {
            App.showToast(error.message || "Network request failed", "danger");
            throw error;
        }
    },

    // Update live warehouse status pill in the sidebar/topbar
    updateWarehouseStatus: async function () {
        try {
            const data = await fetch("/api/warehouse/counts").then(r => r.json());
            if (data.success && data.counts) {
                const countBadge = document.getElementById("header-warehouse-count");
                if (countBadge) {
                    countBadge.textContent = `${App.formatNumber(data.counts.fact_sales)} Records`;
                }
            }
        } catch (e) {
            // Silently ignore telemetry refresh errors
        }
    }
};

document.addEventListener("DOMContentLoaded", () => {
    App.updateWarehouseStatus();
});
