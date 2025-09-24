
$(document).ready(function() {
    const $form = $('#loginForm');
    const $username = $('#first');
    const $password = $('#password');
    const $usernameError = $('#usernameError');
    const $passwordError = $('#passwordError');

    $form.on('submit', function(e) {
        let valid = true;
        $usernameError.text('');
        $passwordError.text('');
        $username.removeClass('input-error');
        $password.removeClass('input-error');

        if (!$username.val().trim()) {
            $usernameError.text('Username is required');
            $username.addClass('input-error');
            valid = false;
        }
        if (!$password.val().trim()) {
            $passwordError.text('Password is required');
            $password.addClass('input-error');
            valid = false;
        }

        if (!valid) {
            e.preventDefault();
        }
    });

// Django error handling for incorrect credentials
    var incorrectMsg = $('.main').data('incorrect');
    if (incorrectMsg) {
        $passwordError.text(incorrectMsg);
        $password.addClass('input-error');
    }
});
