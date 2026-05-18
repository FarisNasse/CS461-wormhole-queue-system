(function () {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion) {
        return;
    }

    document.documentElement.classList.add('motion-enabled');

    const revealSections = document.querySelectorAll('.reveal-section');

    if ('IntersectionObserver' in window && revealSections.length > 0) {
        const observer = new IntersectionObserver(
            entries => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('reveal-visible');
                        observer.unobserve(entry.target);
                    }
                });
            },
            { rootMargin: '0px 0px -40px 0px', threshold: 0.12 }
        );

        revealSections.forEach(section => observer.observe(section));
    } else {
        revealSections.forEach(section => section.classList.add('reveal-visible'));
    }

    if (window.matchMedia('(pointer: coarse)').matches) {
        return;
    }

    document.querySelectorAll('.tilt-card').forEach(card => {
        const maxTilt = 4;

        card.addEventListener('mousemove', event => {
            const rect = card.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateY = ((x - centerX) / centerX) * maxTilt;
            const rotateX = -((y - centerY) / centerY) * maxTilt;

            card.style.setProperty('--shine-x', `${(x / rect.width) * 100}%`);
            card.style.setProperty('--shine-y', `${(y / rect.height) * 100}%`);
            card.style.transform =
                `perspective(900px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
            card.style.removeProperty('--shine-x');
            card.style.removeProperty('--shine-y');
        });
    });
})();
