const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const script = fs.readFileSync(path.join(__dirname, '../../static/core/js/place_admin.js'), 'utf8');

function openForm(kind, country) {
    const elements = {
        id_location_type: Object.assign(new EventTarget(), { value: kind }),
        id_is_region: Object.assign(new EventTarget(), { checked: kind === 'region' }),
        id_country: Object.assign(new EventTarget(), { value: country, disabled: false }),
        id_name: { value: 'Bieszczady', disabled: false },
    };
    const rows = Object.fromEntries(['country', 'name', 'sub_places'].map(
        name => [`.field-${name}`, { style: {} }]
    ));
    const document = Object.assign(new EventTarget(), {
        getElementById: id => elements[id],
        querySelector: selector => rows[selector],
    });
    vm.runInNewContext(script, { document, Event, setTimeout: callback => callback() });
    document.dispatchEvent(new Event('DOMContentLoaded'));
    return { elements, rows };
}

test('opening and toggling a region keeps its country enabled and intact', () => {
    const { elements, rows } = openForm('region', 'PL');
    assert.equal(elements.id_country.value, 'PL');
    assert.equal(elements.id_country.disabled, false);
    assert.notEqual(rows['.field-country'].style.display, 'none');
    assert.equal(rows['.field-sub_places'].style.display, '');
    elements.id_location_type.value = 'place';
    elements.id_location_type.dispatchEvent(new Event('change'));
    assert.equal(elements.id_is_region.checked, false);
    assert.equal(rows['.field-sub_places'].style.display, 'none');
    assert.equal(elements.id_country.value, 'PL');
});

test('country mode hides the place name and keeps the country selector available', () => {
    const { elements, rows } = openForm('country', 'ES');
    assert.equal(rows['.field-name'].style.display, 'none');
    assert.equal(elements.id_name.disabled, true);
    assert.equal(elements.id_country.value, 'ES');
    assert.equal(elements.id_country.disabled, false);
});
