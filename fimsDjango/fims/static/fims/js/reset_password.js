$(document).ready(function() {
    var $form = $('form');
    var $password = $('#reset-password');
    var $confirmPassword = $('#reset-confirm-password');
    var $passwordError = $('#passwordError');
    var $confirmPasswordError = $('#confirmPasswordError');

    $form.on('submit', function(e) {
        var valid = true;
        $password.removeClass('input-error');
        $confirmPassword.removeClass('input-error');
        $passwordError.text('');
        $confirmPasswordError.text('');

        var password = $password.val();
        var confirmPassword = $confirmPassword.val();

        if (!password) {
            $passwordError.text('Password is required');
            $password.addClass('input-error');
            valid = false;
        } else if (password.length < 5) {
            $passwordError.text('Password must be at least 5 characters');
            $password.addClass('input-error');
            valid = false;
        }

        if (!confirmPassword) {
            $confirmPasswordError.text('Confirm password is required');
            $confirmPassword.addClass('input-error');
            valid = false;
        } else if (password !== confirmPassword) {
            $confirmPasswordError.text('Passwords do not match');
            $confirmPassword.addClass('input-error');
            valid = false;
        }

        if (!valid) {
            e.preventDefault();
        }
    });
});
