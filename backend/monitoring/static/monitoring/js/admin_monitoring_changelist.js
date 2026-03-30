(function () {
  function parseJsonConfig(node) {
    if (!node) {
      return null;
    }

    const rawConfig = node.getAttribute("data-monitoring-config");
    if (!rawConfig) {
      return null;
    }

    try {
      return JSON.parse(rawConfig);
    } catch (_error) {
      return null;
    }
  }

  function buildUrlWithFilters(config) {
    const url = new URL(window.location.href);
    const filterParams = config.filterParamNames || [];
    filterParams.forEach((paramName) => url.searchParams.delete(paramName));
    url.searchParams.delete("p");

    if (config.preserveOrderingOnFilterChange) {
      const ordering = url.searchParams.get("o");
      if (ordering) {
        url.searchParams.set("o", ordering);
      } else {
        url.searchParams.delete("o");
      }
    } else {
      url.searchParams.delete("o");
    }

    config.filters.forEach((filterConfig) => {
      const selectElement = document.getElementById(filterConfig.id);
      if (selectElement && selectElement.value) {
        url.searchParams.set(filterConfig.param, selectElement.value);
      }
    });

    return url;
  }

  function initializeFilters(config) {
    const selectIds = config.filters.map((filterConfig) => filterConfig.id);
    const selectElements = selectIds
      .map((selectId) => document.getElementById(selectId))
      .filter(Boolean);

    if (selectElements.length === 0) {
      return;
    }

    function navigateWithFilters() {
      const url = buildUrlWithFilters(config);
      window.location.assign(url.toString());
    }

    function navigateWithSort(orderValue) {
      const url = buildUrlWithFilters(config);
      if (orderValue) {
        url.searchParams.set("o", orderValue);
      } else {
        url.searchParams.delete("o");
      }
      window.location.assign(url.toString());
    }

    selectElements.forEach((selectElement) => {
      selectElement.addEventListener("change", navigateWithFilters);
    });

    if (config.sortOldestId) {
      const sortOldestButton = document.getElementById(config.sortOldestId);
      if (sortOldestButton) {
        sortOldestButton.addEventListener("click", function (event) {
          event.preventDefault();
          navigateWithSort("1");
        });
      }
    }

    if (config.sortNewestId) {
      const sortNewestButton = document.getElementById(config.sortNewestId);
      if (sortNewestButton) {
        sortNewestButton.addEventListener("click", function (event) {
          event.preventDefault();
          navigateWithSort("-1");
        });
      }
    }
  }

  function initializeTaskStatus(config) {
    if (!config.statusRootId || !config.statusButtonSelector) {
      return;
    }

    const root = document.getElementById(config.statusRootId);
    if (!root) {
      return;
    }

    const taskId = root.dataset.taskId || "";
    const statusUrlTemplate = root.dataset.statusUrlTemplate || "";
    if (!taskId || !statusUrlTemplate) {
      return;
    }

    const label = document.getElementById(config.statusLabelId);
    const percent = document.getElementById(config.statusPercentId);
    const bar = document.getElementById(config.statusBarId);
    const button = document.querySelector(config.statusButtonSelector);
    if (!label || !percent || !bar || !button) {
      return;
    }

    const initialVisibilityDelayMs = 5000;
    const pollIntervalMs = 500;
    let stopped = false;

    function setStatus(status, progress, text) {
      const normalizedProgress = Math.max(0, Math.min(100, Math.round(progress)));
      root.hidden = false;
      root.dataset.status = status;
      label.textContent = text;
      percent.textContent = `${normalizedProgress}%`;
      bar.style.width = `${normalizedProgress}%`;
    }

    async function pollStatus() {
      if (stopped) {
        return;
      }

      try {
        const response = await fetch(statusUrlTemplate.replace("__TASK_ID__", taskId), {
          credentials: "same-origin",
          headers: {
            Accept: "application/json",
          },
        });
        if (!response.ok) {
          throw new Error(`Status request failed: ${response.status}`);
        }

        const payload = await response.json();
        const progress = Number(payload.progress_percent || 0);

        if (payload.status === "success") {
          setStatus("success", 100, root.dataset.completeText || "Completed");
          button.disabled = false;
          stopped = true;
          return;
        }

        if (payload.status === "failed") {
          const failedText = root.dataset.failedText || "Failed";
          const message = payload.error ? `${failedText}: ${payload.error}` : failedText;
          setStatus("failed", 100, message);
          button.disabled = false;
          stopped = true;
          return;
        }

        if (payload.status === "running") {
          setStatus("running", progress || 70, root.dataset.runningText || "Running...");
        } else {
          setStatus("queued", progress || 25, root.dataset.queuedText || "Queued...");
        }

        button.disabled = true;
        window.setTimeout(pollStatus, pollIntervalMs);
      } catch (_error) {
        setStatus("failed", 100, root.dataset.failedText || "Failed");
        button.disabled = false;
        stopped = true;
      }
    }

    setStatus("queued", 0, root.dataset.queuedText || "Queued...");
    button.disabled = true;
    window.setTimeout(pollStatus, initialVisibilityDelayMs);
  }

  const root = document.getElementById("monitoring-admin-changelist");
  const config = parseJsonConfig(root);
  if (!config) {
    return;
  }

  initializeFilters(config);
  initializeTaskStatus(config);
})();
