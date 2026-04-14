(function() {
    const cropperRoot = document.querySelector("[data-admin-fk-image-cropper-root]");
    if (!cropperRoot) {
        return;
    }

    const visibleTabPanelId = cropperRoot.dataset.visibleTabPanel || "media-tab";
    const visibleTabPanel = document.getElementById(visibleTabPanelId);
    const tabsContainer = document.getElementById("jazzy-tabs");
    const visibleTabTrigger = tabsContainer
        ? tabsContainer.querySelector('[href="#' + visibleTabPanelId + '"]')
        : null;

    const configNode = document.getElementById("admin-fk-image-cropper-config");
    const config = configNode ? JSON.parse(configNode.textContent || "null") : null;
    if (!config) {
        return;
    }

    const canvas = cropperRoot.querySelector("[data-admin-fk-image-cropper-canvas]");
    const viewportWrap = cropperRoot.querySelector(".admin-image-cropper__viewport-wrap");
    const overlay = cropperRoot.querySelector("[data-admin-fk-image-cropper-overlay]");
    const zoomInput = cropperRoot.querySelector("[data-admin-fk-image-cropper-zoom]");
    const resetButton = cropperRoot.querySelector("[data-admin-fk-image-cropper-reset]");
    const applyButton = cropperRoot.querySelector("[data-admin-fk-image-cropper-apply]");
    const fieldLabelNode = cropperRoot.querySelector("[data-admin-fk-image-cropper-field-label]");
    const sourceLabelNode = cropperRoot.querySelector("[data-admin-fk-image-cropper-source-label]");
    const statusNode = cropperRoot.querySelector("[data-admin-fk-image-cropper-status]");
    const context = canvas ? canvas.getContext("2d") : null;

    if (
        !canvas || !zoomInput || !viewportWrap || !overlay || !resetButton || !applyButton
        || !fieldLabelNode || !sourceLabelNode || !statusNode || !context
    ) {
        return;
    }

    const PREVIEW_LONGEST_SIDE = 800;
    const state = {
        image: null,
        imageName: "",
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
        fkCache: new Map(),
        lastSourceValue: "",
    };

    function getSourceSelect() {
        return document.getElementById(config.input_id);
    }

    function getTargetInput() {
        return document.getElementById(config.target_input_id);
    }

    function getTargetClearCheckbox() {
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
            fallback.textContent = "No remote image selected.";
            sourceLabelNode.appendChild(fallback);
            return;
        }
        sourceLabelNode.textContent = text;
    }

    // Clamp the current drag offsets against the rendered image bounds.
    // Step by step:
    // 1. Measure how large the loaded image is after base scaling and user zoom.
    // 2. Compare that rendered size to the fixed preview viewport size.
    // 3. Compute how far the image may move left/right and up/down while still covering
    //    the whole crop area.
    // 4. Restrict the current offsets to that safe range so the user cannot drag the
    //    image far enough to expose empty canvas background inside the final crop.
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

    // Render the cropper preview canvas from the current state.
    // Step by step:
    // 1. Clear the previous frame from the canvas.
    // 2. Paint the dark cropper background so the viewport has a stable base color.
    // 3. If no image is currently loaded, draw the empty-state helper text and stop.
    // 4. If an image exists, calculate its rendered width and height using the base scale
    //    and the current zoom level.
    // 5. Center the image in the viewport, then apply the user drag offsets.
    // 6. Draw that transformed image into the preview canvas so the user sees exactly
    //    what will be exported when they click Apply.
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
                "Select an AstroImage source to load",
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

    // Compute the minimum scale required for the source image to fully cover the viewport.
    // Step by step:
    // 1. Compare the viewport width to the source image width.
    // 2. Compare the viewport height to the source image height.
    // 3. Use the larger ratio, because the image must cover both dimensions of the crop
    //    area before any manual zooming happens.
    // 4. Return that scale so resetTransform() can establish the default "cover" view.
    function computeBaseScale(image) {
        return Math.max(state.previewWidth / image.width, state.previewHeight / image.height);
    }

    // Recalculate preview and output geometry from the backend cropper configuration.
    // Step by step:
    // 1. Read the configured crop aspect ratio that came from Django admin.
    // 2. Build a preview canvas size whose longest side is fixed, so the widget stays
    //    visually consistent while still respecting the requested aspect ratio.
    // 3. Read the final exported output width and height from the same config.
    // 4. Resize the canvas element to those preview dimensions.
    // 5. Update the CSS custom property used by the wrapper so layout and overlay match
    //    the same ratio.
    // 6. Update the overlay shape metadata so the preview mask reflects the configured
    //    crop style.
    function updateGeometry() {
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

    // Reset the crop transform back to the default centered state.
    // Step by step:
    // 1. Exit immediately if there is no image loaded.
    // 2. Recompute the base scale so the image once again fully covers the crop viewport.
    // 3. Reset zoom to 1, meaning "use only the base cover scale".
    // 4. Clear both drag offsets so the image is centered again.
    // 5. Sync the range input UI back to "1".
    // 6. Repaint the preview so the user sees the reset state immediately.
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

    // Load a remote image URL into the cropper preview.
    // Step by step:
    // 1. Increment the load request id so older async image responses can be ignored.
    // 2. Create a browser Image object for the requested URL.
    // 3. On successful load, confirm this response still belongs to the latest request.
    // 4. Store the image and its label in local state.
    // 5. Mark the cropper as not dirty, because merely loading a source is not yet a
    //    crop change applied by the user.
    // 6. Reset the transform so the newly loaded source starts centered and properly scaled.
    // 7. Update the source label and status text.
    // 8. On error, clear the image-related state and show a user-facing failure status.
    function loadImageFromUrl(url, imageName) {
        state.loadRequestId += 1;
        const requestId = state.loadRequestId;
        const image = new Image();
        image.onload = function() {
            if (requestId !== state.loadRequestId) {
                return;
            }
            state.image = image;
            state.imageName = imageName;
            state.dirty = false;
            resetTransform();
            setSourceLabel(imageName);
            setStatus("Ready to crop");
        };
        image.onerror = function() {
            if (requestId !== state.loadRequestId) {
                return;
            }
            state.image = null;
            state.imageName = "";
            state.dirty = false;
            setStatus("Unable to load remote image");
            drawPreview();
        };
        image.src = url;
    }

    // Resolve the currently selected AstroImage foreign key into a browser-loadable image URL.
    // Step by step:
    // 1. If no FK value is selected, clear the cropper preview and revert to the empty state.
    // 2. If we have already resolved this image id before, reuse the cached URL and skip
    //    another network request.
    // 3. Otherwise build the lookup endpoint URL, including the selected AstroImage id.
    // 4. Call the dedicated shop lookup API to ask the backend for the best source URL
    //    for cropping.
    // 5. If the response contains a usable URL, cache it locally for future re-selection.
    // 6. Load that URL into the preview canvas.
    // 7. If the API fails or returns unusable data, keep the cropper in a safe state and
    //    surface a status message instead of throwing.
    function resolveForeignKeySelection(pk, name) {
        if (!pk) {
            state.image = null;
            state.imageName = "";
            state.dirty = false;
            setStatus("Ready");
            setSourceLabel("");
            drawPreview();
            return;
        }

        if (state.fkCache.has(pk)) {
            setStatus("Loading from cache...");
            loadImageFromUrl(state.fkCache.get(pk), name);
            return;
        }

        setStatus("Resolving AstroImage source...");
        const baseUrl = config.lookup_url || "/image-urls/";
        const fetchUrl = baseUrl + (baseUrl.includes("?") ? "&" : "?") + "id=" + encodeURIComponent(pk);

        fetch(fetchUrl)
            .then(res => {
                if (!res.ok) {
                    throw new Error("HTTP " + res.status);
                }
                return res.json();
            })
            .then(data => {
                if (data && data.url) {
                    state.fkCache.set(pk, data.url);
                    setStatus("Loading source...");
                    loadImageFromUrl(data.url, name);
                } else {
                    setStatus("Failed to resolve AstroImage URL.");
                }
            })
            .catch(() => {
                setStatus("API error fetching image.");
            });
    }

    // Synchronize the cropper with the live Django admin FK select element.
    // Step by step:
    // 1. Re-query the source select from the DOM instead of trusting an old reference,
    //    because the admin/select2 stack can replace or mutate the live element.
    // 2. Read the currently selected value from that field.
    // 3. If the selected value is unchanged and an image is already loaded, do nothing to
    //    avoid unnecessary re-fetches and redraws.
    // 4. Store the latest selected FK value in state.
    // 5. Derive a human-readable label from the selected option text when available.
    // 6. Hand both the FK id and label to resolveForeignKeySelection(), which will either
    //    clear the preview, reuse a cached URL, or fetch a fresh lookup result.
    function syncSourceSelection() {
        const sourceSelect = getSourceSelect();
        if (!sourceSelect) {
            return;
        }

        const currentValue = sourceSelect.value || "";
        if (currentValue === state.lastSourceValue && state.image) {
            return;
        }

        state.lastSourceValue = currentValue;
        const selectedOption = sourceSelect.options[sourceSelect.selectedIndex];
        const name = selectedOption ? selectedOption.text : "Remote Image #" + currentValue;
        resolveForeignKeySelection(currentValue, name);
    }

    // Toggle cropper visibility based on the currently active admin tab.
    // Step by step:
    // 1. If neither the tab panel nor the tab trigger can be found, hide the component
    //    entirely because the page layout is not what the cropper expects.
    // 2. Inspect the tab panel classes to see whether the Media tab content is active.
    // 3. Inspect the tab trigger classes/ARIA state as a second signal, because different
    //    admin interactions can update one before the other.
    // 4. Show the cropper only when one of those visibility signals confirms that the
    //    Media tab is the active context.
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

    // Export the currently visible crop area to a PNG file object.
    // Step by step:
    // 1. If there is no image loaded, resolve with null because there is nothing to export.
    // 2. Create an off-screen canvas sized to the backend-requested output dimensions.
    // 3. Paint the export background so the result always has deterministic pixels.
    // 4. Convert the preview-space transform into export-space coordinates by scaling the
    //    rendered width, height, and offsets.
    // 5. Draw the same visible image region into the export canvas at full output size.
    // 6. Convert that canvas into a PNG blob.
    // 7. Wrap the blob in a File object with a stable generated name so it can be assigned
    //    to the hidden file input used by Django admin.
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

            exportContext.fillStyle = "#000000";
            exportContext.fillRect(0, 0, state.outputWidth, state.outputHeight);

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
                const stem = (state.imageName || config.field_name).replace(/\.[^.]+$/, "");
                resolve(new File([blob], stem + "-cropped.png", { type: "image/png" }));
            }, "image/png");
        });
    }

    // Begin a drag interaction for the crop preview.
    // Step by step:
    // 1. Ignore pointer input entirely if no image is loaded.
    // 2. Store the active pointer id so only that pointer may continue the drag.
    // 3. Remember the pointer's starting screen coordinates.
    // 4. Remember the image offsets at drag start.
    // 5. Add the dragging class for cursor/visual feedback.
    // 6. Capture the pointer on the canvas so movement stays coherent even if the cursor
    //    briefly leaves the element during the drag.
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

    // Update image pan while the active drag is in progress.
    // Step by step:
    // 1. Ignore the event unless it belongs to the active pointer and an image exists.
    // 2. Calculate how far the pointer moved from the drag origin.
    // 3. Apply that movement to the stored starting offsets.
    // 4. Clamp the result so the image still covers the crop area.
    // 5. Redraw the preview with the new offsets.
    // 6. Mark the crop as dirty and update the status to show that the current framing is
    //    ready to be applied.
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

    // End the current drag interaction and clean up pointer state.
    // Step by step:
    // 1. Ignore events from non-active pointers.
    // 2. Clear the stored active pointer id.
    // 3. Remove the dragging CSS class.
    // 4. Release pointer capture if the canvas still owns it.
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

    // Register all listeners needed to keep the cropper synchronized with the FK source field.
    // Step by step:
    // 1. Create a tiny sync helper that defers to the next tick, giving select2/admin DOM
    //    updates time to settle before we read the field value.
    // 2. Attach direct listeners to the current select element when it exists.
    // 3. Attach delegated document-level listeners keyed by the source field id, so sync
    //    still works even if the original select node is replaced later.
    // 4. Find the surrounding field row/container for the source widget.
    // 5. Observe that container for DOM mutations, because admin/select2 can mutate the
    //    field structure without firing every event path we want.
    // 6. Whenever any of those signals fire, resync the cropper from the live DOM state.
    function registerSourceListeners() {
        const sync = function() {
            window.setTimeout(syncSourceSelection, 0);
        };

        const sourceSelect = getSourceSelect();
        if (sourceSelect) {
            sourceSelect.addEventListener("change", sync);
            sourceSelect.addEventListener("input", sync);
        }

        document.addEventListener("change", function(event) {
            if (event.target && event.target.id === config.input_id) {
                sync();
            }
        }, true);

        document.addEventListener("input", function(event) {
            if (event.target && event.target.id === config.input_id) {
                sync();
            }
        }, true);

        const sourceFieldRow = document.getElementById(config.input_id)
            ? document.getElementById(config.input_id).closest(".form-group, .field-image, .related-widget-wrapper")
            : null;

        if (sourceFieldRow && "MutationObserver" in window) {
            const observer = new MutationObserver(sync);
            observer.observe(sourceFieldRow, {
                childList: true,
                subtree: true,
                attributes: true,
            });
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
        setStatus("Ready");
    });

    applyButton.addEventListener("click", function() {
        const targetInput = getTargetInput();
        const targetClearCheckbox = getTargetClearCheckbox();
        if (!targetInput || !state.image) {
            setStatus("Nothing to apply");
            return;
        }

        exportCroppedFile().then(function(file) {
            const transfer = new DataTransfer();
            transfer.items.add(file);
            targetInput.files = transfer.files;
            if (targetClearCheckbox) {
                targetClearCheckbox.checked = false;
            }
            state.imageName = file.name;
            state.dirty = false;
            setStatus("Applied to " + config.target_field_name);
        }).catch(function() {
            setStatus("Crop export failed");
        });
    });

    canvas.addEventListener("pointerdown", handlePointerDown);
    canvas.addEventListener("pointermove", handlePointerMove);
    canvas.addEventListener("pointerup", handlePointerUp);
    canvas.addEventListener("pointercancel", handlePointerUp);
    canvas.addEventListener("pointerleave", handlePointerUp);

    updateGeometry();
    fieldLabelNode.textContent = config.target_field_name;
    registerSourceListeners();
    syncSourceSelection();
    window.setInterval(syncSourceSelection, 250);
    window.addEventListener("pageshow", updateVisibility);
    window.addEventListener("load", updateVisibility);
    updateVisibility();
})();
