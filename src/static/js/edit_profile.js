// src/static/js/edit_profile.js

$(document).ready(function() {
    // Initialize Autocomplete for Location with custom mapping
    initializeAutocomplete(
        '#location-input',
        CONFIG.citySuggestionsUrl,
        function(item) {
            console.log("Selected location: " + item.value);
        },
        function(item) {
            // Custom mapping: transform city and country into label and value
            return {
                label: item.city + ', ' + item.country,
                value: item.city + ', ' + item.country
            };
        }
    );

    // Initialize Autocomplete for Certification Type (assuming it returns strings)
    initializeAutocomplete(
        '#cert_type',
        CONFIG.certificationSuggestionsUrl,
        function(item) {
            console.log("Selected certification type: " + item.value);
        }
        // No mapItem function needed if suggestions are strings
    );

    // Initialize Autocomplete for Skill Inputs (assuming they return strings)
    initializeAutocomplete(
        '#skill-input',
        CONFIG.skillSuggestionsUrl,
        function(item) {
            console.log("Selected skill: " + item.value);
        }
        // No mapItem function needed if suggestions are strings
    );

    // Initialize Datepickers
    initializeDatePickers('.date-picker');

    // Handle Profile Picture Upload
    $('#profile-picture-input').on('change', function() {
        var formData = new FormData();
        var file = this.files[0];
        formData.append('profile_picture', file);

        $.ajax({
            url: CONFIG.uploadProfilePictureUrl,
            type: 'POST',
            data: formData,
            contentType: false,
            processData: false,
            success: function(response) {
                if(response.success) {
                    $('#profile-picture').attr('src', response.profile_picture_url);
                    showNotification('Profile picture updated successfully.', 'success');
                } else {
                    showNotification(response.message, 'error');
                }
            },
            error: handleAjaxError
        });
    });

    // Handle Adding a New Certification
    $('#add-certification-form').on('submit', function(e) {
        e.preventDefault();
        var formData = new FormData(this);

        $.ajax({
            url: CONFIG.uploadCertificationUrl,
            type: 'POST',
            data: formData,
            contentType: false,
            processData: false,
            success: function(response) {
                if(response.success) {
                    // Append the new certification to the list
                    $('#certifications-list').append(`
                        <li id="cert-${response.certifications[0].id}">
                            <a href="${response.certifications[0].url}" target="_blank">${response.certifications[0].filename}</a> (${response.certifications[0].type})
                            <button type="button" class="delete-cert-button" data-id="${response.certifications[0].id}">Delete</button>
                        </li>
                    `);
                    // Clear the form
                    $('#add-certification-form')[0].reset();
                    showNotification('Certification added successfully.', 'success');
                } else {
                    showNotification(response.message, 'error');
                }
            },
            error: handleAjaxError
        });
    });

    // Handle Certification Deletion
    $(document).on('click', '.delete-cert-button', function() {
        var certId = $(this).data('id');
        if(confirm('Are you sure you want to delete this certification?')) {
            $.ajax({
                url: CONFIG.deleteCertificationUrl,
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ cert_id: certId }),
                success: function(response) {
                    if(response.success) {
                        $(`#cert-${certId}`).remove();
                        showNotification('Certification deleted successfully.', 'success');
                    } else {
                        showNotification(response.message, 'error');
                    }
                },
                error: handleAjaxError
            });
        }
    });

    // Handle Individual Field Updates (First Name, Last Name, Email, Phone Number, Location)
    $('.update-field-button').on('click', function() {
        var field = $(this).data('field');
        var value = $(`#${field}-input`).val();

        // Basic Validation
        if(value.trim() === "") {
            showNotification(`${field.replace('_', ' ').capitalize()} cannot be empty.`, 'error');
            return;
        }

        // Additional Validation for Email
        if(field === 'email') {
            var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if(!emailRegex.test(value)) {
                showNotification('Please enter a valid email address.', 'error');
                return;
            }
        }

        // Additional Validation for Location (e.g., contains a comma)
        if(field === 'location') {
            if(!value.includes(',')) {
                showNotification("Please enter both city and country, separated by a comma.", 'error');
                return;
            }
            var parts = value.split(',');
            if(parts.length !== 2 || !parts[0].trim() || !parts[1].trim()) {
                showNotification("Please ensure both city and country are provided.", 'error');
                return;
            }
        }

        $.ajax({
            url: CONFIG.updateProfileFieldUrl,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ field: field, value: value }),
            success: function(response) {
                if(response.success) {
                    showNotification(`${field.replace('_', ' ').capitalize()} updated successfully.`, 'success');
                } else {
                    showNotification(response.message, 'error');
                }
            },
            error: handleAjaxError
        });
    });

    // Handle Adding a New Skill
    $('#add-skill-form').on('submit', function(e) {
        e.preventDefault();
        var skill = $('#skill-input').val().trim();

        if(skill === "") {
            showNotification('Skill cannot be empty.', 'error');
            return;
        }

        $.ajax({
            url: CONFIG.addSkillUrl,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ skill: skill }),
            success: function(response) {
                if(response.success) {
                    // Append the new skill to the list
                    $('#skills-list').append(`
                        <li id="skill-${response.skill.id}">
                            ${response.skill.skill}
                            <button type="button" class="delete-skill-button" data-id="${response.skill.id}">Delete</button>
                        </li>
                    `);
                    // Clear the input
                    $('#skill-input').val('');
                    showNotification('Skill added successfully.', 'success');
                } else {
                    showNotification(response.message, 'error');
                }
            },
            error: function(xhr, status, error) {
                console.error("Error adding skill:", error);
                showNotification("An error occurred while adding the skill. Please try again.", 'error');
            }
        });
    });

    // Handle Skill Deletion
    $(document).on('click', '.delete-skill-button', function() {
        var skillId = $(this).data('id');
        if(confirm('Are you sure you want to delete this skill?')) {
            $.ajax({
                url: CONFIG.deleteSkillUrl,
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ skill_id: skillId }),
                success: function(response) {
                    if(response.success) {
                        $(`#skill-${skillId}`).remove();
                        showNotification('Skill deleted successfully.', 'success');
                    } else {
                        showNotification(response.message, 'error');
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Error deleting skill:", error);
                    showNotification('An error occurred while deleting the skill.', 'error');
                }
            });
        }
    });
});

// Function to initialize datepickers (could be centralized in main.js or similar)
function initializeDatePickers(selector) {
    $(selector).datepicker({
        dateFormat: 'yy-mm-dd'
    });
}
