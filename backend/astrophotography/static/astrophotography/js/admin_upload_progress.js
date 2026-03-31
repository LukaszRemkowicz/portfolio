(function () {
    function formatBytes(size) {
        if (!Number.isFinite(size) || size <= 0) {
            return "";
        }

        const units = ["B", "KB", "MB", "GB"];
        let unitIndex = 0;
        let value = size;

        while (value >= 1024 && unitIndex < units.length - 1) {
            value /= 1024;
            unitIndex += 1;
        }

        const precision = unitIndex === 0 ? 0 : 1;
        return value.toFixed(precision) + " " + units[unitIndex];
    }

    function createProgressPanel() {
        const panel = document.createElement("section");
        panel.className = "astro-upload-progress";
        panel.setAttribute("aria-live", "polite");
        panel.innerHTML = [
            '<div class="astro-upload-progress__title">',
            '<span data-astro-upload-title>Preparing upload</span>',
            '<span data-astro-upload-percent>0%</span>',
            "</div>",
            '<div class="astro-upload-progress__meta" data-astro-upload-meta></div>',
            '<div class="astro-upload-progress__track">',
            '<div class="astro-upload-progress__bar" data-astro-upload-bar></div>',
            "</div>",
            '<div class="astro-upload-progress__status" data-astro-upload-status></div>',
        ].join("");

        document.body.appendChild(panel);
        return {
            panel: panel,
            title: panel.querySelector("[data-astro-upload-title]"),
            percent: panel.querySelector("[data-astro-upload-percent]"),
            meta: panel.querySelector("[data-astro-upload-meta]"),
            bar: panel.querySelector("[data-astro-upload-bar]"),
            status: panel.querySelector("[data-astro-upload-status]"),
        };
    }

    function setPanelVisible(ui, isVisible) {
        ui.panel.classList.toggle("is-visible", isVisible);
    }

    function setProgress(ui, percent) {
        const safePercent = Math.max(0, Math.min(100, percent));
        ui.percent.textContent = Math.round(safePercent) + "%";
        ui.bar.classList.remove("is-indeterminate");
        ui.bar.style.width = safePercent + "%";
    }

    function setIndeterminate(ui) {
        ui.percent.textContent = "";
        ui.bar.style.width = "";
        ui.bar.classList.add("is-indeterminate");
    }

    function setErrorState(ui, message) {
        ui.panel.classList.add("is-error");
        ui.title.textContent = "Upload failed";
        ui.status.textContent = message;
        ui.percent.textContent = "";
        ui.bar.classList.remove("is-indeterminate");
        ui.bar.style.width = "100%";
    }

    function replaceDocument(xhr) {
        const responseUrl = xhr.responseURL || window.location.href;
        const responseText = xhr.responseText;

        if (!responseText) {
            window.location.assign(responseUrl);
            return;
        }

        if (responseUrl && responseUrl !== window.location.href) {
            window.history.replaceState({}, "", responseUrl);
        }

        const parser = new DOMParser();
        const parsedDocument = parser.parseFromString(responseText, "text/html");
        const newDocumentElement = parsedDocument.documentElement;
        const currentDocumentElement = document.documentElement;

        if (!newDocumentElement || !currentDocumentElement || !currentDocumentElement.parentNode) {
            window.location.assign(responseUrl);
            return;
        }

        currentDocumentElement.parentNode.replaceChild(newDocumentElement, currentDocumentElement);
    }

    document.addEventListener("DOMContentLoaded", function () {
        const form = document.querySelector("#content-main form[enctype='multipart/form-data']");
        if (!(form instanceof HTMLFormElement)) {
            return;
        }

        const fileInput = form.querySelector("input[type='file'][name='path']");
        if (!(fileInput instanceof HTMLInputElement)) {
            return;
        }

        const submitButtons = Array.from(
            form.querySelectorAll("button[type='submit'], input[type='submit']")
        );
        const ui = createProgressPanel();
        let activeSubmitter = null;
        let requestInFlight = false;

        submitButtons.forEach(function (button) {
            button.addEventListener("click", function () {
                activeSubmitter = button;
            });
        });

        form.addEventListener("submit", function (event) {
            if (requestInFlight) {
                event.preventDefault();
                return;
            }

            if (!fileInput.files || fileInput.files.length === 0) {
                return;
            }

            event.preventDefault();
            requestInFlight = true;

            const file = fileInput.files[0];
            const formData = new FormData(form);
            if (activeSubmitter && activeSubmitter.name && !formData.has(activeSubmitter.name)) {
                formData.append(activeSubmitter.name, activeSubmitter.value || "");
            }

            submitButtons.forEach(function (button) {
                button.disabled = true;
            });

            ui.panel.classList.remove("is-error");
            ui.title.textContent = "Uploading AstroImage";
            ui.meta.textContent = file.name + (file.size ? " • " + formatBytes(file.size) : "");
            ui.status.textContent = "Uploading file to the server...";
            setProgress(ui, 0);
            setPanelVisible(ui, true);

            const xhr = new XMLHttpRequest();
            xhr.open(form.method || "POST", form.action || window.location.href, true);
            xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");

            xhr.upload.addEventListener("progress", function (progressEvent) {
                if (!progressEvent.lengthComputable) {
                    ui.status.textContent = "Uploading file to the server...";
                    return;
                }

                const percent = (progressEvent.loaded / progressEvent.total) * 100;
                setProgress(ui, percent);
                ui.status.textContent = "Uploading file to the server...";
            });

            xhr.upload.addEventListener("load", function () {
                ui.title.textContent = "Saving AstroImage";
                ui.status.textContent = "Upload complete. Waiting for the server response...";
                setIndeterminate(ui);
            });

            xhr.addEventListener("load", function () {
                if (xhr.status >= 200 && xhr.status < 400) {
                    replaceDocument(xhr);
                    return;
                }

                requestInFlight = false;
                submitButtons.forEach(function (button) {
                    button.disabled = false;
                });
                setErrorState(ui, "The server returned an unexpected response. Please try again.");
            });

            xhr.addEventListener("error", function () {
                requestInFlight = false;
                submitButtons.forEach(function (button) {
                    button.disabled = false;
                });
                setErrorState(ui, "The upload was interrupted. Please try again.");
            });

            xhr.addEventListener("abort", function () {
                requestInFlight = false;
                submitButtons.forEach(function (button) {
                    button.disabled = false;
                });
                setErrorState(ui, "The upload was cancelled.");
            });

            xhr.send(formData);
        });
    });
})();
