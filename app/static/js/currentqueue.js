// Legacy file - functionality moved to template scripts
// Keeping for compatibility in case other code references it

document.getElementById('resolve-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const jsonData = {};
    
    for (let [key, value] of formData.entries()) {
        jsonData[key] = value;
    }
    
    try {
        const response = await fetch(this.action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(jsonData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Ticket resolved successfully!');
            window.location.href = '/hardware_list';
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