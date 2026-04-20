(function () {
  "use strict";

  // Shim for django-ckeditor-5 AMD translation bug (en.js calls CKEDITOR.define before editor init).
  window.CKEDITOR = window.CKEDITOR || {};
  window.CKEDITOR.define =
    window.CKEDITOR.define ||
    function () {};

  document.addEventListener("DOMContentLoaded", function () {
    const navbar = document.querySelector(".navbar-nav.ms-auto");
    if (navbar) {
      const timerLi = document.createElement("li");
      timerLi.className = "nav-item d-none d-sm-inline-block";

      const timerSpan = document.createElement("span");
      timerSpan.id = "admin-timer";
      timerSpan.className = "nav-link";
      timerSpan.style.cursor = "default";
      timerSpan.style.color = "inherit";
      timerSpan.style.fontWeight = "500";

      timerLi.appendChild(timerSpan);
      navbar.insertBefore(timerLi, navbar.firstChild);

      function updateAdminTimer() {
        const now = new Date();
        timerSpan.textContent = now.toLocaleString("pl-PL", {
          dateStyle: "short",
          timeStyle: "medium",
        });
      }

      updateAdminTimer();
      setInterval(updateAdminTimer, 1000);
    }

    function applyDynamicSelect2Theme() {
      let isDark = false;

      const wrapper = document.querySelector(".content-wrapper") || document.body;
      let bgColor = window.getComputedStyle(wrapper).backgroundColor;

      if (bgColor === "rgba(0, 0, 0, 0)" || bgColor === "transparent") {
        bgColor = window.getComputedStyle(document.body).backgroundColor;
      }

      const rgb = bgColor.match(/\d+/g);
      if (rgb && rgb.length >= 3) {
        const r = parseInt(rgb[0], 10);
        const g = parseInt(rgb[1], 10);
        const b = parseInt(rgb[2], 10);
        const hsp = Math.sqrt(
          0.299 * (r * r) + 0.587 * (g * g) + 0.114 * (b * b),
        );
        isDark = hsp < 127.5;
      } else {
        isDark =
          document.body.classList.contains("dark-mode") ||
          document.documentElement.getAttribute("data-theme") === "dark";
      }

      const targetBg = isDark ? "#343a40" : "#ffffff";
      const targetBorder = isDark ? "#4b545c" : "#ced4da";
      const targetColor = isDark ? "#ffffff" : "#495057";

      let styleEl = document.getElementById("dynamic-select2-theme");
      const cssString = `
        html body input[type="text"]:not(.vDateField):not(.vTimeField),
        html body input[type="url"],
        html body input[type="email"],
        html body input[type="number"],
        html body input[type="password"],
        html body textarea,
        html body .vTextField,
        html body .vLargeTextField,
        html body input[type="date"],
        html body .select2-container--default .select2-selection--single,
        html body .select2-container--default .select2-selection--multiple,
        html body .themed-select2+.select2-container .select2-selection--single,
        html body .themed-select2+.select2-container .select2-selection--multiple,
        html body .select2-dropdown,
        html body .select2-container--default .select2-search__field {
          background-color: ${targetBg} !important;
          border-color: ${targetBorder} !important;
          color: ${targetColor} !important;
          border-radius: 8px !important;
          border-style: solid !important;
          border-width: 1px !important;
          box-shadow: none !important;
          -webkit-appearance: none !important;
          outline: none !important;
        }

        html body input[type="text"]:not(.select2-search__field):not(.vDateField):not(.vTimeField),
        html body input[type="url"]:not(.select2-search__field),
        html body input[type="email"]:not(.select2-search__field),
        html body input[type="number"]:not(.select2-search__field),
        html body input[type="password"]:not(.select2-search__field),
        html body .vTextField:not(.select2-search__field),
        html body .select2-container--default .select2-selection--single {
          height: 44px !important;
          min-height: 44px !important;
          padding: 0 15px !important;
          width: 100% !important;
          max-width: 100% !important;
        }

        html body textarea {
          padding: 10px 15px !important;
          width: 100% !important;
          max-width: 100% !important;
        }

        .select2-container--default.select2-container--default.select2-container--default .select2-selection--single .select2-selection__rendered {
          line-height: 42px !important;
          padding-left: 0 !important;
        }

        .select2-container--default.select2-container--default.select2-container--default .select2-selection--single .select2-selection__arrow {
          height: 42px !important;
        }

        .select2-results__option.select2-results__option.select2-results__option {
          background-color: ${targetBg} !important;
          color: ${targetColor} !important;
        }

        #content-main .select2-container--default .select2-selection--single .select2-selection__rendered,
        #content-main .select2-container--default .select2-selection--multiple .select2-selection__rendered {
          color: ${targetColor} !important;
        }

        html body .help,
        html body .help-block,
        html body .form-text {
          padding-left: 15px !important;
        }
      `;

      if (!styleEl) {
        styleEl = document.createElement("style");
        styleEl.id = "dynamic-select2-theme";
        styleEl.dataset.currentCss = cssString;
        document.head.appendChild(styleEl);
        styleEl.innerHTML = cssString;
      } else if (styleEl.dataset.currentCss !== cssString) {
        styleEl.innerHTML = cssString;
        styleEl.dataset.currentCss = cssString;
      }
    }

    applyDynamicSelect2Theme();
    setInterval(applyDynamicSelect2Theme, 250);
  });
})();
