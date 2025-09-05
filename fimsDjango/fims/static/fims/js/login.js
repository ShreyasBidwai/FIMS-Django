document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('loginForm');
    const username = document.getElementById('first');
    const password = document.getElementById('password');
    const usernameError = document.getElementById('usernameError');
    const passwordError = document.getElementById('passwordError');

    form.addEventListener('submit', function (e) {
        let valid = true;
        usernameError.textContent = '';
        passwordError.textContent = '';
        username.classList.remove('input-error');
        password.classList.remove('input-error');

        if (!username.value.trim()) {
            usernameError.textContent = 'Username is required';
            username.classList.add('input-error');
            valid = false;
        }
        if (!password.value.trim()) {
            passwordError.textContent = 'Password is required';
            password.classList.add('input-error');
            valid = false;
        }

        if (!valid) {
            e.preventDefault();
            return;
        }
    });

    // Django error handling
    {% if error_message %}
    passwordError.textContent = '{{ error_message }}';
    password.classList.add('input-error');
    {% endif %}
});
