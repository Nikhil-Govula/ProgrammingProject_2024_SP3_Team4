// main.js
$(document).ready(function() {
    // Notification Function
    window.showNotification = function(message, type = 'success') {
        const notificationContainer = $('#notification-container');
        const notification = $('<div>').addClass(`notification ${type}`).text(message);
        notificationContainer.append(notification);

        // Trigger a reflow before adding the opacity to ensure the transition works
        notification[0].offsetHeight;
        notification.css('opacity', '1');

        setTimeout(() => {
            notification.css('opacity', '0');
            setTimeout(() => {
                notification.remove();
            }, 500); // Wait for fade out transition to complete before removing
        }, 3000); // Show for 3 seconds
    }

    // Capitalize function for alert messages
    String.prototype.capitalize = function() {
        return this.charAt(0).toUpperCase() + this.slice(1);
    }

    // Common AJAX Error Handler
    window.handleAjaxError = function() {
        showNotification('An unexpected error occurred. Please try again later.', 'error');
    }
});