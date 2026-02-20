// app/static/js/currentticket.js
// JavaScript for handling ticket resolution actions on the current ticket page

document.getElementById('resolve-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    
    try {
        const response = await fetch(this.action, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Ticket resolved successfully!');
            window.location.href = '/tickets';  // Adjust to your queue/list page
        } else {
            // Display validation errors if any
            if (data.errors) {
                alert('Validation errors: ' + JSON.stringify(data.errors));
            } else {
                alert('Error: ' + (data.error || 'Failed to resolve ticket'));
            }
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while resolving the ticket');
    }
});
