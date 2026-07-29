// main.js — Theme toggle and client-side page enhancement logic

document.addEventListener("DOMContentLoaded", () => {
    // Demo Banner logic
    const demoBanner = document.getElementById('demo-banner');
    const closeDemoBtn = document.getElementById('close-demo-banner');

    if (demoBanner) {
        if (sessionStorage.getItem('demoBannerClosed') === 'true') {
            demoBanner.style.display = 'none';
        } else if (closeDemoBtn) {
            closeDemoBtn.addEventListener('click', () => {
                demoBanner.style.display = 'none';
                sessionStorage.setItem('demoBannerClosed', 'true');
            });
        }
    }

    // Auto-dismiss flash messages after 4 seconds
    const flashMessages = document.querySelectorAll('[class*="flash-"]');
    if (flashMessages.length > 0) {
        setTimeout(() => {
            flashMessages.forEach(msg => {
                msg.classList.add('flash-fade-out');
                // Remove from DOM after transition completes
                setTimeout(() => {
                    msg.remove();
                }, 500);
            });
        }, 4000);
    }

    // Mobile menu toggle
    const menuBtn = document.querySelector('.mobile-menu-btn');
    const navMenu = document.getElementById('nav-menu');
    if (menuBtn && navMenu) {
        menuBtn.addEventListener('click', () => {
            navMenu.classList.toggle('is-open');
        });
    }

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
