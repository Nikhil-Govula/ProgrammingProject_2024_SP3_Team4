// src/static/js/login.js

document.addEventListener('DOMContentLoaded', function() {
    const forgotPasswordLink = document.getElementById('forgot-password-link');
    const forgotPasswordPopup = document.getElementById('forgot-password-popup');
    const closePopup = document.getElementById('close-popup');
    const overlay = document.getElementById('overlay');

    // Check if all necessary elements exist to avoid errors
    if (forgotPasswordLink && forgotPasswordPopup && closePopup && overlay) {
        // Open the popup when the "Forgot password?" link is clicked
        forgotPasswordLink.addEventListener('click', function(event) {
            event.preventDefault();
            forgotPasswordPopup.style.display = 'block';
            overlay.style.display = 'block';
        });

        // Close the popup when the close button is clicked
        closePopup.addEventListener('click', function() {
            forgotPasswordPopup.style.display = 'none';
            overlay.style.display = 'none';
        });

        // Close the popup when clicking outside the popup content
        overlay.addEventListener('click', function() {
            forgotPasswordPopup.style.display = 'none';
            overlay.style.display = 'none';
        });
    }
});
