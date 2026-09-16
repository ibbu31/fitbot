/*
 * responsive-fix.js
 * A defensive runtime safety net: on load, resize, and orientation change,
 * this finds any element rendering wider than the actual visible screen
 * and forces it to fit -- regardless of what's causing the overflow on a
 * given device (an unsupported CSS feature, an unusual browser, a stray
 * fixed width, etc). This guarantees a correctly-sized page even on
 * devices we can't individually test against.
 */
(function () {
    function clampOverflow() {
        var docWidth = document.documentElement.clientWidth;
        if (!docWidth) return;

        var all = document.body.querySelectorAll('*');
        for (var i = 0; i < all.length; i++) {
            var el = all[i];
            if (el.scrollWidth > docWidth + 2) {
                el.style.maxWidth = '100%';
                el.style.boxSizing = 'border-box';
                var overflowX = window.getComputedStyle(el).overflowX;
                if (overflowX === 'visible') {
                    el.style.overflowX = 'hidden';
                }
            }
        }

        // Belt-and-suspenders: if the whole page is still somehow wider
        // than the screen, clip it at the root level too.
        if (document.documentElement.scrollWidth > docWidth + 2) {
            document.documentElement.style.overflowX = 'hidden';
            document.body.style.overflowX = 'hidden';
        }
    }

    window.addEventListener('load', clampOverflow);
    window.addEventListener('resize', clampOverflow);
    window.addEventListener('orientationchange', function () {
        setTimeout(clampOverflow, 300);
    });

    // Run once immediately too, in case the page is already fully parsed
    if (document.readyState === 'complete') {
        clampOverflow();
    }
})();