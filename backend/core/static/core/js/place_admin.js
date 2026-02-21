// core/static/core/js/place_admin.js
// Pure vanilla JS — Select2 listens to native change events via dispatchEvent.

document.addEventListener('DOMContentLoaded', () => {
    const isRegionCheckbox = document.getElementById('id_is_region');
    const countrySelect = document.getElementById('id_country');

    if (!isRegionCheckbox || !countrySelect) return;

    // Django Admin wraps each field in div.form-row.field-<name>
    const subPlacesRow = document.querySelector('.field-sub_places');
    const countryRow = document.querySelector('.field-country');

    let savedCountry = '';

    function notify() {
        countrySelect.dispatchEvent(new Event('change', { bubbles: true }));
    }

    function applyToggle() {
        const isRegion = isRegionCheckbox.checked;

        if (isRegion) {
            // Region mode: capture country, clear it, disable it, and hide the row.
            // Show the sub-places row.
            savedCountry = countrySelect.value;
            countrySelect.value = '';
            countrySelect.disabled = true;
            notify();

            if (countryRow) countryRow.style.display = 'none';
            if (subPlacesRow) subPlacesRow.style.display = '';
        } else {
            // Regular place mode: enable country, restore value, and show the row.
            // Hide the sub-places row.
            countrySelect.disabled = false;
            if (subPlacesRow) subPlacesRow.style.display = 'none';
            if (countryRow) countryRow.style.display = '';

            // Restore value in next tick so Select2 has processed the re-enable first
            setTimeout(() => {
                if (savedCountry) {
                    countrySelect.value = savedCountry;
                    notify();
                } else {
                    notify();
                }
            }, 20);
        }
    }

    isRegionCheckbox.addEventListener('change', applyToggle);
    // Defer initial run so Select2 has finished rendering its UI
    setTimeout(applyToggle, 150);
});
