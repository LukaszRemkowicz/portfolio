'use strict';

{
    const widgetSelector = '[data-themed-date-widget="true"]';

    function startOfDay(date) {
        const result = new Date(date);
        result.setHours(0, 0, 0, 0);
        return result;
    }

    function datesForWeek(locale, width) {
        const formatter = new Intl.DateTimeFormat(locale, { weekday: width });
        const sunday = new Date(2024, 0, 7);
        return Array.from({ length: 7 }, (_, index) => {
            const date = new Date(sunday);
            date.setDate(sunday.getDate() + index);
            return formatter.format(date);
        });
    }

    function monthsForYear(locale, width) {
        const formatter = new Intl.DateTimeFormat(locale, { month: width });
        return Array.from({ length: 12 }, (_, month) =>
            formatter.format(new Date(2024, month, 1))
        );
    }

    function firstDayOfWeek(locale) {
        try {
            return new Intl.Locale(locale).weekInfo.firstDay % 7;
        } catch {
            return 0;
        }
    }

    function buildLocale(root, locale) {
        return {
            days: datesForWeek(locale, 'long'),
            daysShort: datesForWeek(locale, 'short'),
            daysMin: datesForWeek(locale, 'narrow'),
            months: monthsForYear(locale, 'long'),
            monthsShort: monthsForYear(locale, 'short'),
            today: root.dataset.dateTodayLabel,
            clear: root.dataset.dateCancelLabel,
            dateFormat: 'yyyy-MM-dd',
            timeFormat: '',
            firstDay: firstDayOfWeek(locale),
        };
    }

    function shortcutButton(root, offset, modifier) {
        const labels = {
            '-1': root.dataset.dateYesterdayLabel,
            0: root.dataset.dateTodayLabel,
            1: root.dataset.dateTomorrowLabel,
        };

        return {
            content: labels[String(offset)],
            className: `themed-date-shortcut themed-date-shortcut--${modifier}`,
            onClick(datepicker) {
                const date = startOfDay(new Date());
                date.setDate(date.getDate() + offset);
                datepicker.selectDate(date);
            },
        };
    }

    function initialiseWidget(root) {
        const input = root.querySelector('[data-air-datepicker]');
        const trigger = root.querySelector('[data-date-action="toggle"]');

        if (!input || !trigger || input.themedDatepicker) {
            return;
        }

        const localeName = document.documentElement.lang || navigator.language || 'en';
        const datepicker = new AirDatepicker(input, {
            autoClose: true,
            classes: 'themed-air-datepicker',
            dateFormat: 'yyyy-MM-dd',
            isMobile: false,
            keyboardNav: true,
            locale: buildLocale(root, localeName),
            position: 'bottom left',
            toggleSelected: false,
            buttons: [
                shortcutButton(root, -1, 'yesterday'),
                shortcutButton(root, 0, 'today'),
                shortcutButton(root, 1, 'tomorrow'),
                {
                    content: root.dataset.dateCancelLabel,
                    className: 'themed-date-shortcut themed-date-shortcut--cancel',
                    onClick(instance) {
                        instance.hide();
                    },
                },
            ],
            onSelect({ formattedDate }) {
                input.value = formattedDate;
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
            },
            onShow() {
                trigger.setAttribute('aria-expanded', 'true');
            },
            onHide() {
                trigger.setAttribute('aria-expanded', 'false');
            },
        });

        datepicker.$datepicker.id = root.dataset.dateCalendarId;
        trigger.setAttribute('aria-controls', datepicker.$datepicker.id);
        input.themedDatepicker = datepicker;

        trigger.addEventListener('click', () => {
            if (datepicker.visible) {
                datepicker.hide();
            } else {
                datepicker.show();
            }
        });
    }

    function initialiseDateWidgets() {
        document.querySelectorAll(widgetSelector).forEach(initialiseWidget);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialiseDateWidgets);
    } else {
        initialiseDateWidgets();
    }
}
