// Filename: src/static/js/account_detail.js

$(document).ready(function() {
    // Initialize autocomplete for Location if not an employer
    if (CONFIG.accountType !== 'employer') {
        // Initialize autocomplete for Location with custom mapping
        initializeAutocomplete(
            '#location-input',
            CONFIG.citySuggestionsUrl,
            function(item) {
                console.log("Selected location: " + item.value);
            },
            function(item) {
                // Custom mapping: combine city and country for label and value
                return {
                    label: item.city + ', ' + item.country,
                    value: item.city + ', ' + item.country
                };
            }
        );
    }

    /**
     * Function to handle account updates via AJAX
     * @param {string} action - The action to perform ('lock_account', 'unlock_account', 'deactivate_account', 'activate_account')
     */
    function updateAccount(action) {
        $.ajax({
            url: CONFIG.accountDetailUrl + '/update_field', // Ensure this points to the correct endpoint
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                field: action === 'toggle_account_lock' || action === 'toggle_account_activation' ? action : null,
                value: null
            }),
            success: function(response) {
                if (response.success) {
                    showNotification(response.message, 'success');
                    // Optionally, you can reload the page to reflect changes
                    setTimeout(function() {
                        location.reload();
                    }, 1500);
                } else {
                    showNotification("Error: " + response.message, 'error');
                }
            },
            error: function(xhr, status, error) {
                console.error("AJAX Error:", status, error);
                showNotification("An error occurred. Please try again.", 'error');
            }
        });
    }

    /**
     * Event handler for toggling account lock status
     */
    $('#toggle-lock-btn').click(function(e) {
        e.preventDefault();
        var action = $(this).text().includes('Unlock') ? 'unlock_account' : 'lock_account';
        updateAccount(action);
    });

    /**
     * Event handler for toggling account activation status
     */
    $('#toggle-deactivation-btn').click(function(e) {
        e.preventDefault();
        var action = $(this).text().includes('Deactivate') ? 'deactivate_account' : 'activate_account';
        updateAccount(action);
    });

    /**
     * Event handler for updating individual account fields (e.g., first name, last name, email)
     */
    $('.update-field-button').click(function(e) {
        e.preventDefault();
        var field = $(this).data('field');
        var value = $('#' + field).val().trim();

        // Basic Validation
        if (value === "") {
            showNotification(`${capitalizeWords(field.replace('_', ' '))} cannot be empty.`, 'error');
            return;
        }

        // Additional Validation for Email
        if (field === 'email') {
            var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                showNotification('Please enter a valid email address.', 'error');
                return;
            }
        }

        // Additional Validation for Location (e.g., contains a comma)
        if (field === 'location') {
            if (!value.includes(',')) {
                showNotification("Please enter both city and country, separated by a comma.", 'error');
                return;
            }
            var parts = value.split(',');
            if (parts.length !== 2 || !parts[0].trim() || !parts[1].trim()) {
                showNotification("Please ensure both city and country are provided.", 'error');
                return;
            }
        }

        // Prepare data for AJAX in the expected format
        var data = {
            field: field,
            value: value
        };

        $.ajax({
            url: CONFIG.updateFieldUrl, // Ensure this points to the correct endpoint
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function(response) {
                if (response.success) {
                    showNotification(`${capitalizeWords(field.replace('_', ' '))} updated successfully.`, 'success');
                } else {
                    showNotification("Error: " + response.message, 'error');
                }
            },
            error: function(xhr, status, error) {
                console.error(`Error updating ${field}:`, error);
                showNotification(`An error occurred while updating ${capitalizeWords(field.replace('_', ' '))}. Please try again.`, 'error');
            }
        });
    });

    /**
     * Utility function to capitalize words
     * @param {string} str - The string to capitalize
     * @returns {string} - The capitalized string
     */
    function capitalizeWords(str) {
        return str.replace(/\b\w/g, function(char) { return char.toUpperCase(); });
    }
});
