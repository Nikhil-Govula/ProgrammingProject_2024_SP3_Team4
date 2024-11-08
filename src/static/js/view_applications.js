// src/static/js/view_applications.js

function updateStatus(applicationId, status) {
    // Show loading state
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = 'Updating...';
    button.disabled = true;

    fetch(`/employer/jobs/applications/${applicationId}/update-status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            status: status
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Show success message
            showNotification('success', 'Status updated successfully');
            // Reload the page after a short delay
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            throw new Error(data.message || 'Failed to update status');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('error', error.message);
        // Reset button state
        button.textContent = originalText;
        button.disabled = false;
    });
}

// Initialize any event handlers when the document is ready
$(document).ready(function() {
    // Add any additional initialization code here if needed
});