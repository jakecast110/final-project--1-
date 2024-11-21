document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const usernameInput = document.getElementById('id_username');
    const passwordInput = document.getElementById('id_password');

    form.addEventListener('submit', function(event) {
        if (!validateForm()) {
            event.preventDefault();
        }
    });

    function validateForm() {
        let isValid = true;

        if (usernameInput.value.trim() === '') {
            showError(usernameInput, 'Username is required');
            isValid = false;
        } else {
            removeError(usernameInput);
        }

        if (passwordInput.value.trim() === '') {
            showError(passwordInput, 'Password is required');
            isValid = false;
        } else {
            removeError(passwordInput);
        }

        return isValid;
    }

    function showError(input, message) {
        const errorElement = input.nextElementSibling;
        if (errorElement && errorElement.classList.contains('error-message')) {
            errorElement.textContent = message;
        } else {
            const error = document.createElement('div');
            error.className = 'error-message';
            error.textContent = message;
            error.style.color = 'red';
            error.style.fontSize = '0.8em';
            error.style.marginTop = '5px';
            input.parentNode.insertBefore(error, input.nextSibling);
        }
        input.style.borderColor = 'red';
    }

    function removeError(input) {
        const errorElement = input.nextElementSibling;
        if (errorElement && errorElement.classList.contains('error-message')) {
            errorElement.remove();
        }
        input.style.borderColor = '';
    }
});