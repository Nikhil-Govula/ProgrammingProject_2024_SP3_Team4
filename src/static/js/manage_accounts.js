// src/static/js/manage_accounts.js

$(document).ready(function() {
    /**
     * Function to update the accounts table based on filters
     * @param {string} accountType - The type of account to filter (e.g., 'user', 'employer', 'admin')
     * @param {array} accountStatuses - Array of account statuses to filter (e.g., ['active', 'locked'])
     * @param {string} searchQuery - The search query string
     */
    function updateTable(accountType, accountStatuses, searchQuery) {
        $.ajax({
            url: CONFIG.manageAccountsUrl,
            type: 'GET',
            data: {
                account_type: accountType,
                account_status: accountStatuses.join(','),
                search: searchQuery
            },
            success: function(data) {
                // Replace the table body with the new data
                $('#accounts-table-body').html($(data).find('#accounts-table-body').html());
            },
            error: function(xhr, status, error) {
                console.error("Error fetching accounts:", error);
                showNotification("An error occurred while fetching accounts. Please try again.", 'error');
            }
        });
    }

    // Event handler for filters
    $('#account_type').change(function() {
        applyFilters();
    });

    $('#search_query').on('input', function() {
        applyFilters();
    });

    $('input[name="status"]').change(function() {
        applyFilters();
    });

    /**
     * Function to collect filter values and update the table
     */
    function applyFilters() {
        var accountType = $('#account_type').val();
        var searchQuery = $('#search_query').val();
        var selectedStatuses = [];
        $('input[name="status"]:checked').each(function() {
            selectedStatuses.push($(this).val());
        });

        updateTable(accountType, selectedStatuses, searchQuery);
    }

    // Initialize filter values from server-side variables
    var defaultAccountType = CONFIG.defaultAccountType || "user";
    $('#account_type').val(defaultAccountType);
    $('#search_query').val(CONFIG.defaultSearchQuery || "");

    // Set initial checkbox states based on account_status
    var initialStatuses = CONFIG.defaultAccountStatus ? CONFIG.defaultAccountStatus.split(',') : ['active'];
    initialStatuses.forEach(function(status) {
        $('#status_' + status).prop('checked', true);
    });

    // Initial table load
    updateTable(defaultAccountType, initialStatuses, CONFIG.defaultSearchQuery || "");
});
