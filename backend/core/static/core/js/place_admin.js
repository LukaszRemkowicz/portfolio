// The location type controls name/sub-place inputs, never the country value.
document.addEventListener('DOMContentLoaded', () => {
    const typeSelect = document.getElementById('id_location_type');
    const isRegionInput = document.getElementById('id_is_region');
    const nameInput = document.getElementById('id_name');
    if (!typeSelect || !isRegionInput) return;

    const nameRow = document.querySelector('.field-name');
    const subPlacesRow = document.querySelector('.field-sub_places');

    function applyType() {
        const isCountry = typeSelect.value === 'country';
        const isRegion = typeSelect.value === 'region';
        isRegionInput.checked = isRegion;
        isRegionInput.value = isRegion ? 'True' : 'False';
        if (nameRow) nameRow.style.display = isCountry ? 'none' : '';
        if (nameInput) nameInput.disabled = isCountry;
        if (subPlacesRow) subPlacesRow.style.display = isRegion ? '' : 'none';
    }

    typeSelect.addEventListener('change', applyType);
    applyType();
});
