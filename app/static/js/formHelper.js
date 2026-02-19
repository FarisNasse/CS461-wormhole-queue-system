// Form submission helper for JSON-based form submissions
// Prevents default form submission and sends data as JSON

/**
 * Convert FormData to JSON object
 * @param {FormData} formData - Form data to convert
 * @returns {Object} JSON object with form data
 */
function formDataToJSON(formData) {
    const json = {};
    for (let [key, value] of formData.entries()) {
        // Handle multiple values for same key (select multiple, checkboxes)
        if (json.hasOwnProperty(key)) {
            if (!Array.isArray(json[key])) {
                json[key] = [json[key]];
            }
            json[key].push(value);
        } else {
            json[key] = value;
        }
    }
    return json;
}

/**
 * Handle form submission with JSON
 * @param {Event} event - The submit event
 * @param {string} endpoint - The API endpoint to POST to
 * @param {Function} onSuccess - Callback function on success (receives response data)
 * @param {Function} onError - Callback function on error (receives error response)
 */
async function submitFormAsJSON(event, endpoint, onSuccess, onError) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const jsonData = formDataToJSON(formData);

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(jsonData),
        });

        const data = await response.json();

        if (response.ok) {
            if (onSuccess) {
                onSuccess(data, response);
            }
        } else {
            if (onError) {
                onError(data, response);
            } else {
                // Default error handling
                console.error('Form submission error:', data);
                alert('Error: ' + (data.error || 'Form submission failed'));
            }
        }
    } catch (error) {
        console.error('Network error:', error);
        if (onError) {
            onError({ error: error.message }, null);
        } else {
            alert('An error occurred: ' + error.message);
        }
    }
}

/**
 * Display form validation errors
 * @param {Object} errors - Error object from backend
 * @param {HTMLElement} container - Container element to display errors
 */
function displayFormErrors(errors, container) {
    // Clear previous errors
    const existingErrors = container.querySelectorAll('.form-error');
    existingErrors.forEach(el => el.remove());

    // Display new errors
    if (errors && typeof errors === 'object') {
        Object.entries(errors).forEach(([field, messages]) => {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'form-error';
            errorDiv.style.color = 'red';
            errorDiv.style.marginTop = '5px';
            errorDiv.textContent = (Array.isArray(messages) ? messages[0] : messages);
            
            // Try to find the input field and append error after it
            const fieldInput = container.querySelector(`[name="${field}"]`);
            if (fieldInput) {
                fieldInput.parentNode.insertBefore(errorDiv, fieldInput.nextSibling);
            }
        });
    }
}
