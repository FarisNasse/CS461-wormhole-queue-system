document.addEventListener('DOMContentLoaded', function() {
    const confirmationForms = document.querySelectorAll('[data-confirm-message]');

    confirmationForms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            const message = form.dataset.confirmMessage;

            if (message && !window.confirm(message)) {
                event.preventDefault();
            }
        });
    });
});