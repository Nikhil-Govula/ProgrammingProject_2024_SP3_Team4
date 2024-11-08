// src/static/js/notifications.js

function showNotification(message, type = 'success') {
    const notificationContainer = $('#notification-container');
    // Clear any existing notifications
    notificationContainer.empty();

    const notification = $(`
        <div class="notification ${type}">
            ${message}
        </div>
    `);
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

// Capitalize function for better message formatting
String.prototype.capitalize = function () {
    return this.charAt(0).toUpperCase() + this.slice(1);
}
