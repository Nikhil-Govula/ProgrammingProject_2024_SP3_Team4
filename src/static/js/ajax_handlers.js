$(document).ready(function() {
    // Example: Common AJAX form submission handler
    window.submitForm = function(formSelector, successCallback) {
        $(formSelector).on('submit', function(e) {
            e.preventDefault();
            var formData = new FormData(this);

            $.ajax({
                url: $(this).attr('action'),
                type: 'POST',
                data: formData,
                contentType: false,
                processData: false,
                success: function(response) {
                    if(response.success) {
                        successCallback(response);
                    } else {
                        showNotification(response.message, 'error');
                    }
                },
                error: handleAjaxError
            });
        });
    }
});