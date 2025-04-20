// This file contains JavaScript code for client-side functionality, such as form validation or dynamic content updates.

document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const passwordInput = document.getElementById('password');
    const expirationInput = document.getElementById('expiration');

    uploadForm.addEventListener('submit', function(event) {
        if (passwordInput.value.length < 6) {
            alert('Password must be at least 6 characters long.');
            event.preventDefault();
        }
    });

    expirationInput.addEventListener('change', function() {
        const selectedValue = expirationInput.value;
        if (selectedValue) {
            alert(`You have selected an expiration time of ${selectedValue} hours.`);
        }
    });
});