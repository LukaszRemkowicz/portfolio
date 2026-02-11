document.addEventListener('DOMContentLoaded', function () {
    // Select inputs starting with id_highlight_name or id_highlight_title
    // This covers standard IDs and potentially suffixed ones
    const inputs = document.querySelectorAll('input[id^="id_highlight_name"], input[id^="id_highlight_title"]');

    function resizeInput(input) {
        // Create/Reuse a hidden span to measure text width
        let span = document.getElementById('input-measurer');
        if (!span) {
            span = document.createElement('span');
            span.id = 'input-measurer';
            document.body.appendChild(span);
            Object.assign(span.style, {
                visibility: 'hidden',
                position: 'absolute',
                whiteSpace: 'pre',
                top: '-9999px',
                left: '-9999px'
            });
        }

        // Copy critical font styles
        const styles = window.getComputedStyle(input);
        span.style.fontFamily = styles.fontFamily;
        span.style.fontSize = styles.fontSize;
        span.style.fontWeight = styles.fontWeight;
        span.style.letterSpacing = styles.letterSpacing;
        span.style.textTransform = styles.textTransform; // Just in case

        let text = input.value;
        if (!text) {
            // Calculate width of placeholder if needed, or just default min width
            // User said: "If not text dont expand" -> keep small.
            span.textContent = '';
        } else {
            // Replace spaces with non-breaking spaces for accurate width measurement
            // because HTML collapses spaces
            span.textContent = text;
        }

        // Measure
        const width = span.offsetWidth;
        const MIN_WIDTH = 100; // Minimum width to show some context/placeholder
        const PADDING = 20; // Extra padding

        // Calculate new width
        const newWidth = Math.max(MIN_WIDTH, width + PADDING);

        // Apply with transition (handled by CSS)
        input.style.width = newWidth + 'px';
    }

    inputs.forEach(function (input) {
        // Initialize with a slight delay to ensure fonts/CSS are loaded
        setTimeout(() => resizeInput(input), 100);

        // Bind events for live resizing
        ['input', 'change', 'focus', 'blur'].forEach(evt => {
            input.addEventListener(evt, function () {
                resizeInput(input);
            });
        });

        // Also handle window resize for potential responsive changes
        window.addEventListener('resize', () => resizeInput(input));
    });
});
