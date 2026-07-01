// main.js — Theme toggle and client-side page enhancement logic

document.addEventListener("DOMContentLoaded", () => {
    // Theme toggle initialization and event handling
    const toggleBtn = document.getElementById("theme-toggle");
    if (toggleBtn) {
        // Update toggle icon visually on load according to active theme
        const updateIconState = () => {
            const currentIcon = toggleBtn.querySelector("[data-lucide]");
            if (!currentIcon) return;

            const isDark = document.documentElement.getAttribute("data-theme") === "dark";
            if (isDark) {
                currentIcon.setAttribute("data-lucide", "sun");
            } else {
                currentIcon.setAttribute("data-lucide", "moon");
            }
            if (window.lucide) {
                window.lucide.createIcons();
            }
        };

        // Sync initial state
        updateIconState();

        // Listen for user click to toggle theme
        toggleBtn.addEventListener("click", () => {
            const isDark = document.documentElement.getAttribute("data-theme") === "dark";
            if (isDark) {
                document.documentElement.removeAttribute("data-theme");
                localStorage.setItem("theme", "light");
            } else {
                document.documentElement.setAttribute("data-theme", "dark");
                localStorage.setItem("theme", "dark");
            }
            updateIconState();
        });
    }
});
