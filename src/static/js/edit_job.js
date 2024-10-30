// src/static/js/edit_job.js

$(document).ready(function() {
    // Initialize Autocomplete for City
    initializeAutocomplete('#city', CONFIG.citySuggestionsUrl, function(item) {
        console.log("Selected city: " + item.value);
    });

    // Initialize Autocomplete for Certifications
    initializeAutocomplete('#certification-input', CONFIG.certificationSuggestionsUrl, function(item) {
        console.log("Selected certification: " + item.value);
    });

    // Initialize Autocomplete for Skills
    initializeAutocomplete('#skill-input', CONFIG.skillSuggestionsUrl, function(item) {
        console.log("Selected skill: " + item.value);
    });

    // Initialize Autocomplete for Occupation
    initializeAutocomplete('#occupation-input', CONFIG.occupationSuggestionsUrl, function(item) {
        console.log("Selected occupation: " + item.value);
    });

    // Handle adding a new certification
    $('#add-certification-button').on('click', function (e) {
        e.preventDefault();
        var certification = $('#certification-input').val().trim();

        if (certification === "") {
            showNotification('Certification cannot be empty.', 'error');
            return;
        }

        $.ajax({
            url: CONFIG.addJobCertificationUrl,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({certification: certification}),
            success: function (response) {
                if (response.success) {
                    // Sanitize certification string for use in HTML IDs
                    var safeCertification = certification.replace(/[^a-zA-Z0-9-_]/g, '');
                    $('#certifications-list').append(`
                        <li id="certification-${safeCertification}">
                            ${certification}
                            <button type="button" class="delete-certification-button" data-certification="${certification}">Delete</button>
                        </li>
                    `);
                    $('#certification-input').val('');
                    $('#no-certifications-message').hide();
                    showNotification('Certification added successfully.', 'success');
                } else {
                    showNotification(response.message, 'error');
                }
            },
            error: function () {
                showNotification('An error occurred while adding the certification.', 'error');
            }
        });
    });

    // Handle deleting a certification
    $(document).on('click', '.delete-certification-button', function () {
        var certification = $(this).data('certification');
        var $listItem = $(this).closest('li');

        $.ajax({
            url: CONFIG.deleteJobCertificationUrl,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({certification: certification}),
            success: function (response) {
                if (response.success) {
                    $listItem.remove();
                    if ($('#certifications-list li').length === 0) {
                        $('#no-certifications-message').show();
                    }
                    showNotification('Certification deleted successfully.', 'success');
                } else {
                    showNotification(response.message || 'Failed to delete certification.', 'error');
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.error("Error deleting certification:", textStatus, errorThrown);
                showNotification('An error occurred while deleting the certification.', 'error');
            }
        });
    });

    // Handle skill deletion
    $(document).on('click', '.delete-skill-button', function () {
        var skill = $(this).data('skill');
        var $listItem = $(this).closest('li');

        $.ajax({
            url: CONFIG.deleteJobSkillUrl,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({skill: skill}),
            success: function (response) {
                if (response.success) {
                    $listItem.remove();
                    if ($('#skills-list li').length === 0) {
                        $('#no-skills-message').show();
                    }
                    showNotification('Skill deleted successfully.', 'success');
                } else {
                    showNotification(response.message || 'Failed to delete skill.', 'error');
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.error("Error deleting skill:", textStatus, errorThrown);
                showNotification('An error occurred while deleting the skill.', 'error');
            }
        });
    });

    // Handle adding a new skill
    $('#add-skill-button').on('click', function (e) {
        e.preventDefault();
        var skill = $('#skill-input').val().trim();

        if (skill === "") {
            showNotification('Skill cannot be empty.', 'error');
            return;
        }

        $.ajax({
            url: CONFIG.addJobSkillUrl,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({skill: skill}),
            success: function (response) {
                if (response.success) {
                    // Sanitize skill string for use in HTML IDs
                    var safeSkill = skill.replace(/[^a-zA-Z0-9-_]/g, '');
                    $('#skills-list').append(`
                        <li id="skill-${safeSkill}">
                            ${skill}
                            <button type="button" class="delete-skill-button" data-skill="${skill}">Delete</button>
                        </li>
                    `);
                    $('#skill-input').val('');
                    $('#no-skills-message').hide();
                    showNotification(response.message, 'success');
                } else {
                    showNotification(response.message, 'error');
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                // Use the message from the server's response
                var errorMessage = jqXHR.responseJSON && jqXHR.responseJSON.message
                    ? jqXHR.responseJSON.message
                    : 'An error occurred while adding the skill.';
                console.error("Error adding skill:", errorMessage);
                showNotification(errorMessage, 'error');
            }
        });
    });

    // Handle adding a new work history entry
    $('#add-work-history-button').on('click', function (e) {
        e.preventDefault();
        var occupation = $('#occupation-input').val().trim();
        var duration = $('#duration-input').val().trim();

        if (occupation === "" || duration === "") {
            showNotification('Occupation and duration cannot be empty.', 'error');
            return;
        }

        if (!/^\d+$/.test(duration) || parseInt(duration) <= 0) {
            showNotification('Duration must be a positive integer representing months.', 'error');
            return;
        }

        $.ajax({
            url: CONFIG.addWorkHistoryUrl,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({occupation: occupation, duration: duration}),
            success: function (response) {
                if (response.success) {
                    // Sanitize occupation string for use in HTML IDs
                    var safeOccupation = occupation.replace(/[^a-zA-Z0-9-_]/g, '');
                    var safeDuration = duration.replace(/[^a-zA-Z0-9-_]/g, '');
                    $('#work-history-list').append(`
                        <li id="work-history-${safeOccupation}-${safeDuration}">
                            <strong>${occupation}</strong> - ${duration} month(s)
                            <button type="button" class="delete-work-history-button" data-occupation="${occupation}" data-duration="${duration}">Delete</button>
                        </li>
                    `);
                    $('#occupation-input').val('');
                    $('#duration-input').val('');
                    $('#no-work-history-message').hide();
                    showNotification('Work history entry added successfully.', 'success');
                } else {
                    showNotification(response.message, 'error');
                }
            },
            error: function () {
                showNotification('An error occurred while adding the work history entry.', 'error');
            }
        });
    });

    // Handle deleting a work history entry
    $(document).on('click', '.delete-work-history-button', function () {
        var occupation = $(this).data('occupation');
        var duration = $(this).data('duration');
        var $listItem = $(this).closest('li');

        $.ajax({
            url: CONFIG.deleteWorkHistoryUrl,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({occupation: occupation, duration: duration}),
            success: function (response) {
                if (response.success) {
                    $listItem.remove();
                    if ($('#work-history-list li').length === 0) {
                        $('#no-work-history-message').show();
                    }
                    showNotification('Work history entry deleted successfully.', 'success');
                } else {
                    showNotification(response.message || 'Failed to delete work history entry.', 'error');
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.error("Error deleting work history entry:", textStatus, errorThrown);
                showNotification('An error occurred while deleting the work history entry.', 'error');
            }
        });
    });

    // Handle updating individual fields
    $('.update-field-button').on('click', function(e) {
        e.preventDefault();
        var field = $(this).data('field');
        var value;

        // Determine the type of input (input or textarea)
        if ($('#' + field).is('textarea')) {
            value = $('#' + field).val().trim();
        } else {
            value = $('#' + field).val().trim();
        }

        if(value === "") {
            showNotification(`${field.replace('_', ' ').capitalize()} cannot be empty.`, 'error');
            return;
        }

        // Additional validation for the 'city' field
        if(field === 'city') {
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

        var data = {};
        data[field] = value;

        $.ajax({
            url: CONFIG.editJobUrl,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function(response) {
                if(response.success) {
                    showNotification(`${field.replace('_', ' ').capitalize()} updated successfully.`, 'success');
                } else {
                    showNotification("Error: " + response.message, 'error');
                }
            },
            error: function(xhr, status, error) {
                console.error(`Error updating ${field}:`, error);
                showNotification(`An error occurred while updating ${field.replace('_', ' ')}. Please try again.`, 'error');
            }
        });
    });

    // Handle job deletion
    $('#delete-job-button').on('click', function() {
        if (confirm('Are you sure you want to delete this job? This action cannot be undone.')) {
            $.ajax({
                url: CONFIG.deleteJobUrl,
                type: 'POST',
                success: function(response) {
                    if (response.success) {
                        showNotification('Job deleted successfully.', 'success');
                        // Redirect to the jobs list page after a short delay
                        setTimeout(function() {
                            window.location.href = CONFIG.viewJobsUrl;
                        }, 2000);
                    } else {
                        showNotification(response.message || 'Failed to delete job.', 'error');
                    }
                },
                error: function() {
                    showNotification('An error occurred while deleting the job.', 'error');
                }
            });
        }
    });
});
