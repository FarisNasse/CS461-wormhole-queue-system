document.addEventListener('DOMContentLoaded', function() {
    const wikiSearch = document.getElementById('wikiSearch');
    const sections = document.querySelectorAll('.wiki-section');
    const navLinks = document.querySelectorAll('.wiki-nav .nav-link[href^="#"]');
    const backToTop = document.querySelector('.back-to-top');

    if (wikiSearch) {
        wikiSearch.addEventListener('keyup', function(event) {
            const searchTerm = event.target.value.toLowerCase();

            sections.forEach(function(section) {
                const text = section.textContent.toLowerCase();
                section.classList.toggle(
                    'wiki-section-hidden',
                    !text.includes(searchTerm)
                );
            });
        });
    }

    navLinks.forEach(function(link) {
        link.addEventListener('click', function(event) {
            const targetId = this.getAttribute('href');

            if (!targetId || !targetId.startsWith('#')) {
                return;
            }

            const target = document.querySelector(targetId);

            if (!target) {
                return;
            }

            event.preventDefault();
            target.scrollIntoView({ behavior: 'smooth' });
        });
    });

    if (backToTop) {
        backToTop.addEventListener('click', function(event) {
            event.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
});