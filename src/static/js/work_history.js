// src/static/js/work_history.js

$(document).ready(function() {
    // Initialize Autocomplete for Occupation
    initializeAutocomplete('#job_title', CONFIG.occupationSuggestionsUrl, function(item) {
        console.log("Selected occupation: " + item.value);
    });

    // Initialize Datepickers
    initializeDatePickers('.date-picker');

    // Handle Adding Work History
    $('#add-work-history-form').on('submit', function(e) {
        e.preventDefault();
        var formData = {
            job_title: $('#job_title').val(),
            company: $('#company').val(),
            description: $('#description').val(),
            date_from: $('#date_from').val(),
            date_to: $('#date_to').val()
        };

        $.ajax({
            url: CONFIG.addWorkHistoryUrl,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                if(response.success) {
                    // Append the new work history entry to the list
                    $('#work-history-list').append(`
                        <li id="work-${response.work_history.id}">
                            <strong>${response.work_history.job_title}</strong> at <em>${response.work_history.company}</em><br>
                            ${response.work_history.description}<br>
                            <small>${response.work_history.date_from} - ${response.work_history.date_to || 'Present'}</small>
                            <button type="button" class="delete-work-button" data-id="${response.work_history.id}">Delete</button>
                        </li>
                    `);
                    // Clear the form
                    $('#add-work-history-form')[0].reset();
                    showNotification('Work history entry added successfully.', 'success');
                } else {
                    showNotification(response.message || 'Failed to add work history entry.', 'error');
                }
            },
            error: function(xhr, status, error) {
                console.error("Error adding work history:", error);
                showNotification('An error occurred while adding work history.', 'error');
            }
        });
    });

    // Handle Deleting Work History
    $(document).on('click', '.delete-work-button', function() {
        var workId = $(this).data('id');
        if(confirm('Are you sure you want to delete this work history entry?')) {
            $.ajax({
                url: CONFIG.deleteWorkHistoryUrl,
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ work_id: workId }),
                success: function(response) {
                    if(response.success) {
                        $(`#work-${workId}`).remove();
                        showNotification('Work history entry deleted successfully.', 'success');
                    } else {
                        showNotification(response.message || 'Failed to delete work history entry.', 'error');
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Error deleting work history:", error);
                    showNotification('An error occurred while deleting work history.', 'error');
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
