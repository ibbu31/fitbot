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

/*
 * DEBUG PANEL -- only appears when the URL has ?debug=1
 * Shows the real numbers from the actual device so we can see what is
 * happening instead of guessing. Remove once the zoom bug is solved.
 */
(function () {
    if (location.search.indexOf('debug=1') === -1) return;

    var panel;

    function render() {
        var de = document.documentElement;
        var vv = window.visualViewport;
        var meta = document.querySelector('meta[name="viewport"]');
        var cw = de.clientWidth;

        var wide = [];
        document.body.querySelectorAll('*').forEach(function (el) {
            var r = el.getBoundingClientRect();
            if (r.right > cw + 1) {
                var cls = (typeof el.className === 'string' && el.className) ? '.' + el.className.split(' ')[0] : '';
                wide.push({
                    name: el.tagName.toLowerCase() + cls,
                    right: Math.round(r.right),
                    pos: window.getComputedStyle(el).position
                });
            }
        });
        wide.sort(function (a, b) { return b.right - a.right; });

        var lines = [
            'DEBUG (' + new Date().toLocaleTimeString() + ')',
            'meta viewport: ' + (meta ? meta.getAttribute('content') : 'MISSING'),
            'innerWidth: ' + window.innerWidth + '  innerHeight: ' + window.innerHeight,
            'screen.width: ' + screen.width + '  DPR: ' + window.devicePixelRatio,
            'docEl clientWidth: ' + cw + '  scrollWidth: ' + de.scrollWidth,
            'body scrollWidth: ' + document.body.scrollWidth,
            'visualViewport scale: ' + (vv ? vv.scale.toFixed(2) : 'n/a') + '  width: ' + (vv ? Math.round(vv.width) : 'n/a'),
            'elements past right edge: ' + wide.length
        ];
        wide.slice(0, 6).forEach(function (w) {
            lines.push('  ' + w.name + ' right=' + w.right + ' pos=' + w.pos);
        });
        lines.push('UA: ' + navigator.userAgent);

        if (!panel) {
            panel = document.createElement('pre');
            panel.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:99999;margin:0;padding:8px;' +
                'background:rgba(0,0,0,0.92);color:#3f3;font:11px/1.35 monospace;white-space:pre-wrap;' +
                'word-break:break-all;max-height:55vh;overflow:auto;border-bottom:2px solid #3f3;';
            document.body.appendChild(panel);
        }
        panel.textContent = lines.join('\n');
    }

    window.addEventListener('load', function () { setTimeout(render, 800); });
    if (window.visualViewport) {
        window.visualViewport.addEventListener('resize', render);
    }
})();