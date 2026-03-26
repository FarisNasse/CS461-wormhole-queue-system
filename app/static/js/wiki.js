document.addEventListener('DOMContentLoaded', function() {
    const wikiRoot = document.querySelector('.wiki-docs-shell');
    if (!wikiRoot) {
        return;
    }

    const wikiSearch = document.getElementById('wikiSearch');
    const wikiStatus = document.getElementById('wikiSearchStatus');
    const sections = Array.from(document.querySelectorAll('.wiki-section'));
    const navLinks = Array.from(document.querySelectorAll('.wiki-side-link[href^="#"]'));
    const backToTop = document.querySelector('.back-to-top');

    function updateSearchStatus(visibleCount, term) {
        if (!wikiStatus) {
            return;
        }

        if (!term) {
            wikiStatus.textContent = 'Showing all sections.';
            return;
        }

        if (visibleCount === 0) {
            wikiStatus.textContent = `No sections match “${term}”.`;
            return;
        }

        const label = visibleCount === 1 ? 'section' : 'sections';
        wikiStatus.textContent = `Showing ${visibleCount} ${label} for “${term}”.`;
    }

    function filterSections(term) {
        let visibleCount = 0;
        const normalized = term.trim().toLowerCase();

        sections.forEach(function(section) {
            const title = (section.dataset.title || '').toLowerCase();
            const text = section.textContent.toLowerCase();
            const isVisible = !normalized || title.includes(normalized) || text.includes(normalized);

            section.classList.toggle('wiki-section-hidden', !isVisible);
            if (isVisible) {
                visibleCount += 1;
            }
        });

        updateSearchStatus(visibleCount, term.trim());
    }

    function setActiveNavLink(activeId) {
        navLinks.forEach(function(link) {
            const isActive = link.getAttribute('href') === `#${activeId}`;
            link.classList.toggle('is-current', isActive);
            if (isActive) {
                link.setAttribute('aria-current', 'true');
            } else {
                link.removeAttribute('aria-current');
            }
        });
    }

    if (wikiSearch) {
        wikiSearch.addEventListener('input', function(event) {
            filterSections(event.target.value);
        });
    }

    navLinks.forEach(function(link) {
        link.addEventListener('click', function(event) {
            const targetId = this.getAttribute('href');
            if (!targetId || !targetId.startsWith('#')) {
                return;
            }

            const target = document.querySelector(targetId);
            if (!target || target.classList.contains('wiki-section-hidden')) {
                return;
            }

            event.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            setActiveNavLink(target.id);
            history.replaceState(null, '', targetId);
        });
    });

    if (backToTop) {
        backToTop.addEventListener('click', function(event) {
            event.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
            history.replaceState(null, '', window.location.pathname);
        });
    }

    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver(function(entries) {
            const visibleEntries = entries
                .filter(entry => entry.isIntersecting)
                .sort((a, b) => b.intersectionRatio - a.intersectionRatio);

            if (visibleEntries.length > 0) {
                setActiveNavLink(visibleEntries[0].target.id);
            }
        }, {
            rootMargin: '-20% 0px -55% 0px',
            threshold: [0.15, 0.4, 0.7],
        });

        sections.forEach(function(section) {
            observer.observe(section);
        });
    }

    const initialHash = window.location.hash;
    if (initialHash && initialHash.startsWith('#')) {
        const initialTarget = document.querySelector(initialHash);
        if (initialTarget) {
            setTimeout(function() {
                initialTarget.scrollIntoView({ behavior: 'auto', block: 'start' });
                setActiveNavLink(initialTarget.id);
            }, 0);
        }
    } else if (sections.length > 0) {
        setActiveNavLink(sections[0].id);
    }
});