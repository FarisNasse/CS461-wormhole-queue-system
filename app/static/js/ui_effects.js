// app/static/js/ui_effects.js
// Progressive UI effects for the Wormhole landing page and shared layout.
// This file intentionally avoids inline scripts so it works with a stricter CSP.

(function() {
    const body = document.body;
    const progressBar = document.querySelector('[data-scroll-progress]');
    const revealItems = document.querySelectorAll('[data-reveal]');
    const parallaxItems = document.querySelectorAll('[data-parallax]');
    const hero = document.querySelector('.showcase-hero');
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    body.classList.add('motion-ready');

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function updateScrollEffects() {
        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
        const progress = scrollHeight > 0 ? clamp(scrollTop / scrollHeight, 0, 1) : 0;

        body.classList.toggle('is-scrolled', scrollTop > 8);

        if (progressBar) {
            progressBar.style.transform = `scaleX(${progress})`;
        }

        if (!reducedMotion) {
            parallaxItems.forEach(item => {
                const speed = Number.parseFloat(item.dataset.parallax || '0');
                const shift = clamp(scrollTop * speed, -48, 48);
                item.style.transform = `translate3d(0, ${shift}px, 0)`;
            });
        }
    }

    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            rootMargin: '0px 0px -10% 0px',
            threshold: 0.15
        });

        revealItems.forEach(item => observer.observe(item));
    } else {
        revealItems.forEach(item => item.classList.add('is-visible'));
    }

    if (hero && !reducedMotion) {
        hero.addEventListener('pointermove', event => {
            const bounds = hero.getBoundingClientRect();
            const x = clamp(((event.clientX - bounds.left) / bounds.width) * 100, 0, 100);
            const y = clamp(((event.clientY - bounds.top) / bounds.height) * 100, 0, 100);

            hero.style.setProperty('--spotlight-x', `${x}%`);
            hero.style.setProperty('--spotlight-y', `${y}%`);
        });
    }

    updateScrollEffects();
    window.addEventListener('scroll', updateScrollEffects, { passive: true });
    window.addEventListener('resize', updateScrollEffects);
})();
