document.addEventListener('DOMContentLoaded', () => {
    const userMenu = document.querySelector('.user-menu');
    const toggle = document.querySelector('.user-menu-toggle');
    const panel = document.querySelector('.user-menu-panel');

    if (!userMenu || !toggle || !panel) {
        return;
    }

    const closeMenu = () => {
        panel.hidden = true;
        toggle.setAttribute('aria-expanded', 'false');
    };

    const openMenu = () => {
        panel.hidden = false;
        toggle.setAttribute('aria-expanded', 'true');
    };

    toggle.addEventListener('click', () => {
        const isExpanded = toggle.getAttribute('aria-expanded') === 'true';

        if (isExpanded) {
            closeMenu();
        } else {
            openMenu();
        }
    });

    document.addEventListener('click', event => {
        if (!userMenu.contains(event.target)) {
            closeMenu();
        }
    });

    document.addEventListener('keydown', event => {
        if (event.key === 'Escape') {
            closeMenu();
            toggle.focus();
        }
    });
});
