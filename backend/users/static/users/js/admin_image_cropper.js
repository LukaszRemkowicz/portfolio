(function() {
    const cropperRoot = document.querySelector("[data-admin-image-cropper-root]");
    if (!cropperRoot) {
        return;
    }

    const visibleTabPanelId = cropperRoot.dataset.visibleTabPanel || "media-tab";
    const visibleTabPanel = document.getElementById(visibleTabPanelId);
    const tabsContainer = document.getElementById("jazzy-tabs");
    const visibleTabTrigger = tabsContainer
        ? tabsContainer.querySelector('[href="#' + visibleTabPanelId + '"]')
        : null;
    const fieldsNode = document.getElementById("admin-image-cropper-fields");
    const fieldConfigs = fieldsNode ? JSON.parse(fieldsNode.textContent || "[]") : [];
    const fieldConfigMap = new Map(fieldConfigs.map(function(config) {
        return [config.field_name, config];
    }));
    const defaultFieldName = cropperRoot.dataset.defaultFieldName || "avatar";

    const canvas = cropperRoot.querySelector("[data-admin-image-cropper-canvas]");
    const viewportWrap = cropperRoot.querySelector(".admin-image-cropper__viewport-wrap");
    const overlay = cropperRoot.querySelector("[data-admin-image-cropper-overlay]");
    const zoomInput = cropperRoot.querySelector("[data-admin-image-cropper-zoom]");
    const resetButton = cropperRoot.querySelector("[data-admin-image-cropper-reset]");
    const applyButton = cropperRoot.querySelector("[data-admin-image-cropper-apply]");
    const fieldLabelNode = cropperRoot.querySelector("[data-admin-image-cropper-field-label]");
    const sourceLabelNode = cropperRoot.querySelector("[data-admin-image-cropper-source-label]");
    const statusNode = cropperRoot.querySelector("[data-admin-image-cropper-status]");
    const context = canvas ? canvas.getContext("2d") : null;

    if (
        !canvas || !zoomInput || !viewportWrap || !overlay || !resetButton || !applyButton
        || !fieldLabelNode || !sourceLabelNode || !statusNode || !context || !fieldConfigs.length
    ) {
        return;
    }

    const PREVIEW_LONGEST_SIDE = 800;
    const state = {
        currentFieldName: defaultFieldName,
        image: null,
        imageName: "",
        objectUrl: null,
        loadRequestId: 0,
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
        previewWidth: canvas.width,
        previewHeight: canvas.height,
        outputWidth: canvas.width,
        outputHeight: canvas.height,
    };

    function getCurrentFieldConfig() {
        return fieldConfigMap.get(state.currentFieldName) || fieldConfigs[0];
    }

    function getFieldSelect() {
        return cropperRoot.querySelector("[data-admin-image-cropper-field-select]");
    }

    function getCurrentSourceInput() {
        const config = getCurrentFieldConfig();
        return document.getElementById(config.input_id);
    }

    function getCurrentSourceClearCheckbox() {
        const config = getCurrentFieldConfig();
        return document.querySelector('input[name="' + config.field_name + '-clear"]');
    }

    function getCurrentTargetInput() {
        const config = getCurrentFieldConfig();
        return document.getElementById(config.target_input_id);
    }

    function getCurrentTargetClearCheckbox() {
        const config = getCurrentFieldConfig();
        return document.querySelector('input[name="' + config.target_field_name + '-clear"]');
    }

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
        const maxOffsetX = Math.max(0, (renderedWidth - state.previewWidth) / 2);
        const maxOffsetY = Math.max(0, (renderedHeight - state.previewHeight) / 2);
        state.offsetX = Math.min(maxOffsetX, Math.max(-maxOffsetX, state.offsetX));
        state.offsetY = Math.min(maxOffsetY, Math.max(-maxOffsetY, state.offsetY));
    }

    function drawPreview() {
        context.clearRect(0, 0, state.previewWidth, state.previewHeight);
        context.fillStyle = "#111722";
        context.fillRect(0, 0, state.previewWidth, state.previewHeight);

        if (!state.image) {
            context.fillStyle = "rgba(237, 242, 247, 0.72)";
            context.font = "16px sans-serif";
            context.textAlign = "center";
            context.textBaseline = "middle";
            context.fillText(
                "Choose or adjust an image",
                state.previewWidth / 2,
                state.previewHeight / 2
            );
            return;
        }

        const renderedWidth = state.image.width * state.baseScale * state.zoom;
        const renderedHeight = state.image.height * state.baseScale * state.zoom;
        const x = (state.previewWidth - renderedWidth) / 2 + state.offsetX;
        const y = (state.previewHeight - renderedHeight) / 2 + state.offsetY;

        context.drawImage(state.image, x, y, renderedWidth, renderedHeight);
    }

    function computeBaseScale(image) {
        return Math.max(state.previewWidth / image.width, state.previewHeight / image.height);
    }

    function updateFieldGeometry(config) {
        const aspectRatio = Number.parseFloat(String(config.crop_aspect_ratio || 1));
        if (aspectRatio >= 1) {
            state.previewWidth = PREVIEW_LONGEST_SIDE;
            state.previewHeight = Math.round(PREVIEW_LONGEST_SIDE / aspectRatio);
        } else {
            state.previewWidth = Math.round(PREVIEW_LONGEST_SIDE * aspectRatio);
            state.previewHeight = PREVIEW_LONGEST_SIDE;
        }

        state.outputWidth = Number.parseInt(String(config.output_width || state.previewWidth), 10);
        state.outputHeight = Number.parseInt(String(config.output_height || state.previewHeight), 10);
        canvas.width = state.previewWidth;
        canvas.height = state.previewHeight;
        viewportWrap.style.setProperty(
            "--admin-image-cropper-aspect-ratio",
            String(state.previewWidth) + " / " + String(state.previewHeight)
        );
        overlay.dataset.previewShape = config.preview_shape || "rounded-square";
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

    function loadImageFromUrl(url, imageName, markDirty, fieldName) {
        state.loadRequestId += 1;
        const requestId = state.loadRequestId;
        const image = new Image();
        image.onload = function() {
            if (requestId !== state.loadRequestId || fieldName !== state.currentFieldName) {
                return;
            }
            state.image = image;
            state.imageName = imageName;
            state.dirty = Boolean(markDirty);
            resetTransform();
            setSourceLabel(imageName);
            setStatus(markDirty ? "Crop ready to apply" : "Ready");
        };
        image.onerror = function() {
            if (requestId !== state.loadRequestId || fieldName !== state.currentFieldName) {
                return;
            }
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
        loadImageFromUrl(objectUrl, file.name, true, state.currentFieldName);
    }

    function renderCurrentFieldMeta() {
        const config = getCurrentFieldConfig();
        fieldLabelNode.textContent = "";
        const codeElement = document.createElement("code");
        codeElement.textContent = config.field_name;
        fieldLabelNode.appendChild(codeElement);
        const sourceInput = getCurrentSourceInput();
        if (sourceInput && sourceInput.files && sourceInput.files[0]) {
            setSourceLabel(sourceInput.files[0].name);
            return;
        }
        setSourceLabel(config.current_image_name || "");
    }

    function switchField(fieldName) {
        state.currentFieldName = fieldName;
        const fieldSelect = getFieldSelect();
        if (fieldSelect) {
            fieldSelect.value = fieldName;
        }
        const config = getCurrentFieldConfig();
        updateFieldGeometry(config);
        const sourceInput = getCurrentSourceInput();
        const sourceClearCheckbox = getCurrentSourceClearCheckbox();
        state.loadRequestId += 1;
        state.image = null;
        state.imageName = "";
        state.dirty = false;
        revokeObjectUrl();
        renderCurrentFieldMeta();
        drawPreview();

        if (sourceClearCheckbox && sourceClearCheckbox.checked) {
            setStatus("Image will be cleared on save");
            return;
        }

        if (sourceInput && sourceInput.files && sourceInput.files[0]) {
            readSelectedFile(sourceInput.files[0]);
            return;
        }

        if (config.current_image_url) {
            setStatus("Loading " + config.label);
            loadImageFromUrl(
                config.current_image_url,
                config.current_image_name || "",
                false,
                config.field_name
            );
            return;
        }

        setStatus("Ready");
        drawPreview();
    }

    function syncSelectedField() {
        const fieldSelect = getFieldSelect();
        if (fieldSelect && fieldSelect.value && fieldSelect.value !== state.currentFieldName) {
            switchField(fieldSelect.value);
        }
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
        cropperRoot.style.display = panelVisible || triggerVisible ? "" : "none";
    }

    function exportCroppedFile() {
        return new Promise(function(resolve, reject) {
            if (!state.image) {
                resolve(null);
                return;
            }

            const exportCanvas = document.createElement("canvas");
            exportCanvas.width = state.outputWidth;
            exportCanvas.height = state.outputHeight;
            const exportContext = exportCanvas.getContext("2d");
            if (!exportContext) {
                reject(new Error("Canvas export is unavailable"));
                return;
            }

            const scaleX = state.outputWidth / state.previewWidth;
            const scaleY = state.outputHeight / state.previewHeight;
            const renderedWidth = state.image.width * state.baseScale * state.zoom * scaleX;
            const renderedHeight = state.image.height * state.baseScale * state.zoom * scaleY;
            const x = ((state.previewWidth - state.image.width * state.baseScale * state.zoom) / 2 + state.offsetX) * scaleX;
            const y = ((state.previewHeight - state.image.height * state.baseScale * state.zoom) / 2 + state.offsetY) * scaleY;

            exportContext.drawImage(state.image, x, y, renderedWidth, renderedHeight);

            exportCanvas.toBlob(function(blob) {
                if (!blob) {
                    reject(new Error("Crop export failed"));
                    return;
                }
                const stem = (state.imageName || getCurrentFieldConfig().field_name).replace(/\.[^.]+$/, "");
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
        setStatus("Crop ready to apply");
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

    fieldConfigs.forEach(function(config) {
        const sourceInput = document.getElementById(config.input_id);
        if (sourceInput) {
            sourceInput.addEventListener("change", function() {
                const sourceClearCheckbox = getCurrentSourceClearCheckbox();
                const targetInput = getCurrentTargetInput();
                const targetClearCheckbox = getCurrentTargetClearCheckbox();
                if (sourceClearCheckbox && sourceClearCheckbox.checked) {
                    sourceClearCheckbox.checked = false;
                }
                if (targetInput) {
                    targetInput.value = "";
                }
                if (targetClearCheckbox && targetClearCheckbox.checked) {
                    targetClearCheckbox.checked = false;
                }
                if (state.currentFieldName !== config.field_name) {
                    return;
                }
                const file = sourceInput.files && sourceInput.files[0];
                if (!file) {
                    switchField(config.field_name);
                    return;
                }
                readSelectedFile(file);
            });
        }

        const clearCheckbox = document.querySelector('input[name="' + config.field_name + '-clear"]');
        if (clearCheckbox) {
            clearCheckbox.addEventListener("change", function() {
                if (state.currentFieldName !== config.field_name) {
                    return;
                }
                if (clearCheckbox.checked) {
                    state.dirty = false;
                    state.image = null;
                    state.imageName = "";
                    revokeObjectUrl();
                    setSourceLabel("");
                    setStatus("Image will be cleared on save");
                    drawPreview();
                } else {
                    switchField(config.field_name);
                }
            });
        }
    });

    cropperRoot.addEventListener("change", function(event) {
        if (event.target && event.target.matches("[data-admin-image-cropper-field-select]")) {
            syncSelectedField();
        }
    });
    cropperRoot.addEventListener("input", function(event) {
        if (event.target && event.target.matches("[data-admin-image-cropper-field-select]")) {
            syncSelectedField();
        }
    });

    zoomInput.addEventListener("input", function() {
        state.zoom = Number.parseFloat(zoomInput.value || "1");
        clampOffsets();
        drawPreview();
        if (state.image) {
            state.dirty = true;
            setStatus("Crop ready to apply");
        }
    });

    resetButton.addEventListener("click", function() {
        if (!state.image) {
            return;
        }
        resetTransform();
        const sourceInput = getCurrentSourceInput();
        state.dirty = Boolean(sourceInput && sourceInput.files && sourceInput.files.length);
        setStatus(state.dirty ? "Crop ready to apply" : "Ready");
    });

    applyButton.addEventListener("click", function() {
        const targetInput = getCurrentTargetInput();
        const sourceClearCheckbox = getCurrentSourceClearCheckbox();
        const targetClearCheckbox = getCurrentTargetClearCheckbox();
        if (!targetInput || !state.image) {
            setStatus("Nothing to apply");
            return;
        }

        exportCroppedFile().then(function(file) {
            const transfer = new DataTransfer();
            transfer.items.add(file);
            targetInput.files = transfer.files;
            if (sourceClearCheckbox) {
                sourceClearCheckbox.checked = false;
            }
            if (targetClearCheckbox) {
                targetClearCheckbox.checked = false;
            }
            const config = getCurrentFieldConfig();
            state.imageName = file.name;
            state.dirty = false;
            setStatus("Applied to " + config.label);
        }).catch(function() {
            setStatus("Crop export failed");
        });
    });

    canvas.addEventListener("pointerdown", handlePointerDown);
    canvas.addEventListener("pointermove", handlePointerMove);
    canvas.addEventListener("pointerup", handlePointerUp);
    canvas.addEventListener("pointercancel", handlePointerUp);
    canvas.addEventListener("pointerleave", handlePointerUp);

    switchField(defaultFieldName);
    window.setInterval(syncSelectedField, 250);

    window.addEventListener("pageshow", updateVisibility);
    window.addEventListener("load", updateVisibility);
    updateVisibility();
})();
