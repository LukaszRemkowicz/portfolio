(function() {
    const cropperRoot = document.querySelector("[data-admin-image-cropper-root]");
    if (!cropperRoot) {
        return;
    }

    const visibleTabPanelId = cropperRoot.dataset.visibleTabPanel || "media-tab";
    const visibleTabPanel = document.getElementById(visibleTabPanelId);
    const tabsContainer = document.getElementById("jazzy-tabs");

    function updateVisibility() {
        if (!visibleTabPanel) {
            cropperRoot.style.display = "none";
            return;
        }

        const isVisible = visibleTabPanel.classList.contains("active")
            && visibleTabPanel.classList.contains("show");
        cropperRoot.style.display = isVisible ? "" : "none";
    }

    if (tabsContainer) {
        tabsContainer.querySelectorAll("[data-bs-toggle='pill']").forEach(function(tabTrigger) {
            tabTrigger.addEventListener("shown.bs.tab", updateVisibility);
            tabTrigger.addEventListener("click", function() {
                window.setTimeout(updateVisibility, 0);
            });
        });
    }

    if (visibleTabPanel && "MutationObserver" in window) {
        const observer = new MutationObserver(updateVisibility);
        observer.observe(visibleTabPanel, {
            attributes: true,
            attributeFilter: ["class"],
        });
    }

    window.addEventListener("pageshow", updateVisibility);
    window.addEventListener("load", updateVisibility);
    updateVisibility();
})();
