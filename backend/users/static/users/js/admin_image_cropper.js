(function() {
    const cropperRoot = document.querySelector("[data-admin-image-cropper-root]");
    if (!cropperRoot) {
        return;
    }

    const sourceInput = document.getElementById(cropperRoot.dataset.sourceInputId || "");
    const visibleTabPanelId = cropperRoot.dataset.visibleTabPanel || "media-tab";
    const visibleTabPanel = document.getElementById(visibleTabPanelId);
    const tabsContainer = document.getElementById("jazzy-tabs");
    const visibleTabTrigger = tabsContainer
        ? tabsContainer.querySelector('[href="#' + visibleTabPanelId + '"]')
        : null;
    const form = cropperRoot.closest("form");
    const canvas = cropperRoot.querySelector("[data-admin-image-cropper-canvas]");
    const zoomInput = cropperRoot.querySelector("[data-admin-image-cropper-zoom]");
    const resetButton = cropperRoot.querySelector("[data-admin-image-cropper-reset]");
    const statusNode = cropperRoot.querySelector("[data-admin-image-cropper-status]");
    const sourceLabelNode = cropperRoot.querySelector("[data-admin-image-cropper-source-label]");
    const clearCheckbox = document.querySelector('input[name="' + cropperRoot.dataset.fieldName + '-clear"]');
    const outputSize = Number.parseInt(cropperRoot.dataset.outputSize || "280", 10);
    const currentImageUrl = cropperRoot.dataset.currentImageUrl || "";
    const currentImageName = cropperRoot.dataset.currentImageName || "";
    const context = canvas ? canvas.getContext("2d") : null;

    if (!sourceInput || !form || !canvas || !zoomInput || !resetButton || !statusNode || !sourceLabelNode || !context) {
        return;
    }

    const state = {
        image: null,
        objectUrl: null,
        imageName: "",
        dirty: false,
        pointerId: null,
        dragStartX: 0,
        dragStartY: 0,
        startOffsetX: 0,
        startOffsetY: 0,
        offsetX: 0,
        offsetY: 0,
        baseScale: 1,
        zoom: 1,
        outputSize,
        previewSize: canvas.width,
        submitting: false,
    };

    function setStatus(message) {
        statusNode.textContent = message;
    }

    function setSourceLabel(text) {
        sourceLabelNode.innerHTML = "";
        if (!text) {
            const fallback = document.createElement("span");
            fallback.className = "text-muted";
            fallback.textContent = "No image selected yet.";
            sourceLabelNode.appendChild(fallback);
            return;
        }
        sourceLabelNode.textContent = text;
    }

    function revokeObjectUrl() {
        if (state.objectUrl) {
            URL.revokeObjectURL(state.objectUrl);
            state.objectUrl = null;
        }
    }

    function clampOffsets() {
        if (!state.image) {
            return;
        }
        const renderedWidth = state.image.width * state.baseScale * state.zoom;
        const renderedHeight = state.image.height * state.baseScale * state.zoom;
        const maxOffsetX = Math.max(0, (renderedWidth - state.previewSize) / 2);
        const maxOffsetY = Math.max(0, (renderedHeight - state.previewSize) / 2);
        state.offsetX = Math.min(maxOffsetX, Math.max(-maxOffsetX, state.offsetX));
        state.offsetY = Math.min(maxOffsetY, Math.max(-maxOffsetY, state.offsetY));
    }

    function drawPreview() {
        context.clearRect(0, 0, state.previewSize, state.previewSize);
        context.fillStyle = "#111722";
        context.fillRect(0, 0, state.previewSize, state.previewSize);

        if (!state.image) {
            context.fillStyle = "rgba(237, 242, 247, 0.72)";
            context.font = "16px sans-serif";
            context.textAlign = "center";
            context.textBaseline = "middle";
            context.fillText("Choose or adjust an avatar", state.previewSize / 2, state.previewSize / 2);
            return;
        }

        const renderedWidth = state.image.width * state.baseScale * state.zoom;
        const renderedHeight = state.image.height * state.baseScale * state.zoom;
        const x = (state.previewSize - renderedWidth) / 2 + state.offsetX;
        const y = (state.previewSize - renderedHeight) / 2 + state.offsetY;

        context.drawImage(state.image, x, y, renderedWidth, renderedHeight);
    }

    function computeBaseScale(image) {
        return Math.max(state.previewSize / image.width, state.previewSize / image.height);
    }

    function resetTransform() {
        if (!state.image) {
            return;
        }
        state.baseScale = computeBaseScale(state.image);
        state.zoom = 1;
        state.offsetX = 0;
        state.offsetY = 0;
        zoomInput.value = "1";
        drawPreview();
    }

    function loadImageFromUrl(url, imageName, markDirty) {
        const image = new Image();
        image.onload = function() {
            state.image = image;
            state.imageName = imageName;
            state.dirty = Boolean(markDirty);
            state.previewSize = canvas.width;
            resetTransform();
            setSourceLabel(imageName);
            setStatus(markDirty ? "Crop ready to save" : "Ready");
        };
        image.onerror = function() {
            state.image = null;
            state.imageName = "";
            state.dirty = false;
            setStatus("Unable to load the selected image");
            drawPreview();
        };
        image.src = url;
    }

    function readSelectedFile(file) {
        revokeObjectUrl();
        const objectUrl = URL.createObjectURL(file);
        state.objectUrl = objectUrl;
        loadImageFromUrl(objectUrl, file.name, true);
    }

    function updateVisibility() {
        if (!visibleTabPanel && !visibleTabTrigger) {
            cropperRoot.style.display = "none";
            return;
        }

        const panelVisible = visibleTabPanel
            ? visibleTabPanel.classList.contains("active") && visibleTabPanel.classList.contains("show")
            : false;
        const triggerVisible = visibleTabTrigger
            ? visibleTabTrigger.classList.contains("active") || visibleTabTrigger.getAttribute("aria-selected") === "true"
            : false;
        const isVisible = panelVisible || triggerVisible;
        cropperRoot.style.display = isVisible ? "" : "none";
    }

    function exportCroppedFile() {
        return new Promise(function(resolve, reject) {
            if (!state.image) {
                resolve(null);
                return;
            }

            const exportCanvas = document.createElement("canvas");
            exportCanvas.width = state.outputSize;
            exportCanvas.height = state.outputSize;
            const exportContext = exportCanvas.getContext("2d");
            if (!exportContext) {
                reject(new Error("Canvas export is unavailable"));
                return;
            }

            const scaleRatio = state.outputSize / state.previewSize;
            const renderedWidth = state.image.width * state.baseScale * state.zoom * scaleRatio;
            const renderedHeight = state.image.height * state.baseScale * state.zoom * scaleRatio;
            const x = ((state.previewSize - state.image.width * state.baseScale * state.zoom) / 2 + state.offsetX) * scaleRatio;
            const y = ((state.previewSize - state.image.height * state.baseScale * state.zoom) / 2 + state.offsetY) * scaleRatio;

            exportContext.drawImage(state.image, x, y, renderedWidth, renderedHeight);

            exportCanvas.toBlob(function(blob) {
                if (!blob) {
                    reject(new Error("Crop export failed"));
                    return;
                }

                const stem = (state.imageName || "avatar").replace(/\.[^.]+$/, "");
                resolve(new File([blob], stem + "-cropped.png", { type: "image/png" }));
            }, "image/png");
        });
    }

    function handlePointerDown(event) {
        if (!state.image) {
            return;
        }
        state.pointerId = event.pointerId;
        state.dragStartX = event.clientX;
        state.dragStartY = event.clientY;
        state.startOffsetX = state.offsetX;
        state.startOffsetY = state.offsetY;
        canvas.classList.add("is-dragging");
        canvas.setPointerCapture(event.pointerId);
    }

    function handlePointerMove(event) {
        if (state.pointerId !== event.pointerId || !state.image) {
            return;
        }
        state.offsetX = state.startOffsetX + (event.clientX - state.dragStartX);
        state.offsetY = state.startOffsetY + (event.clientY - state.dragStartY);
        clampOffsets();
        drawPreview();
        state.dirty = true;
        setStatus("Crop ready to save");
    }

    function handlePointerUp(event) {
        if (state.pointerId !== event.pointerId) {
            return;
        }
        state.pointerId = null;
        canvas.classList.remove("is-dragging");
        if (canvas.hasPointerCapture(event.pointerId)) {
            canvas.releasePointerCapture(event.pointerId);
        }
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

    sourceInput.addEventListener("change", function() {
        if (clearCheckbox && clearCheckbox.checked) {
            clearCheckbox.checked = false;
        }

        const file = sourceInput.files && sourceInput.files[0];
        if (!file) {
            if (currentImageUrl) {
                loadImageFromUrl(currentImageUrl, currentImageName, false);
            } else {
                revokeObjectUrl();
                state.image = null;
                state.imageName = "";
                state.dirty = false;
                setSourceLabel("");
                setStatus("Ready");
                drawPreview();
            }
            return;
        }

        readSelectedFile(file);
    });

    if (clearCheckbox) {
        clearCheckbox.addEventListener("change", function() {
            if (clearCheckbox.checked) {
                state.dirty = false;
                state.image = null;
                state.imageName = "";
                revokeObjectUrl();
                setSourceLabel("");
                setStatus("Image will be cleared on save");
                drawPreview();
            } else if (currentImageUrl) {
                loadImageFromUrl(currentImageUrl, currentImageName, false);
            }
        });
    }

    zoomInput.addEventListener("input", function() {
        state.zoom = Number.parseFloat(zoomInput.value || "1");
        clampOffsets();
        drawPreview();
        if (state.image) {
            state.dirty = true;
            setStatus("Crop ready to save");
        }
    });

    resetButton.addEventListener("click", function() {
        if (!state.image) {
            return;
        }
        resetTransform();
        state.dirty = Boolean(sourceInput.files && sourceInput.files.length);
        setStatus(state.dirty ? "Crop ready to save" : "Ready");
    });

    canvas.addEventListener("pointerdown", handlePointerDown);
    canvas.addEventListener("pointermove", handlePointerMove);
    canvas.addEventListener("pointerup", handlePointerUp);
    canvas.addEventListener("pointercancel", handlePointerUp);
    canvas.addEventListener("pointerleave", handlePointerUp);

    form.addEventListener("submit", function(event) {
        if (state.submitting || !state.image || !state.dirty || (clearCheckbox && clearCheckbox.checked)) {
            return;
        }

        event.preventDefault();
        state.submitting = true;
        setStatus("Preparing cropped avatar...");

        exportCroppedFile().then(function(file) {
            if (!file) {
                state.submitting = false;
                form.submit();
                return;
            }

            const transfer = new DataTransfer();
            transfer.items.add(file);
            sourceInput.files = transfer.files;
            setSourceLabel(file.name);
            setStatus("Cropped avatar ready");
            state.dirty = false;
            form.submit();
        }).catch(function() {
            state.submitting = false;
            setStatus("Crop export failed");
        });
    });

    if (currentImageUrl) {
        loadImageFromUrl(currentImageUrl, currentImageName, false);
    } else {
        drawPreview();
    }

    window.addEventListener("pageshow", updateVisibility);
    window.addEventListener("load", updateVisibility);
    updateVisibility();
})();
