const handleToggleInput = (e) => {

    if (showPasswordToggle.textContent === 'SHOW') {
        showPasswordToggle.textContent = "HIDE";

        passwordField.setAttribute("type", "text");
    } else {
        showPasswordToggle.textContent = "SHOW";

        passwordField.setAttribute("type", "password");
    }
};

showPasswordToggle.addEventListener('click', handleToggleInput);

$(document).ready(function() {

    // TODO: ADDED
    // Common ancestor for all fields (replace with the appropriate selector)
    var form = $('#registerForm');

    // Event delegation for blur events on input fields within the form
    form.on('blur', 'input[type="text"]', function(event) {
        var field = event.target.id;
        var value = $(this).val();
        var messageDivId = `#${field}-validation-message`;

        validateField(field, value, messageDivId);
    });

    // Reusable function for field validation
    function validateField(field, value, messageDivId) {
        $.ajax({
            url: `/auth/validation/${field}`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ [field]: value }),
            success: function(response) {
                // Handle success response (e.g., show success message)
                showAlert(response.message, messageDivId, 'success');
                console.log(response.message);
            },
            error: function(error) {
                // Handle error response (e.g., show error message)
                showAlert(error.responseJSON.message, messageDivId, 'error');
                console.error(error.responseJSON.message);
            }
        });
    }

    // Event binding for each field
    $('#first_name').on('blur', function() {
        validateField('first_name', $(this).val(), '#first_name-validation-message');
    });

    $('#last_name').on('blur', function() {
        validateField('last_name', $(this).val(), '#last_name-validation-message');
    });

    $('#phone_number').on('blur', function() {
        validateField('phone_number', $(this).val(), '#phone_number-validation-message');
    });

    $('#email').on('blur', function() {
        validateField('email', $(this).val(), '#email-validation-message');
    });

    $('#username').on('blur', function() {
        validateField('username', $(this).val(), '#username-validation-message');
    });

    $('#password').on('blur', function() {
        validateField('password', $(this).val(), '#password-validation-message');
    });

    // Add confirm field...

//    // Function to show alerts
//    function showAlert(message, elementId, className) {
//        alert(message);
//        $(elementId).text(message).removeClass('error success').addClass(className);
//    }

    // Function to show alerts within the page
    function showAlert(message, elementId, className) {
        // Display messages within the page
        $(elementId).text(message).removeClass('error success').addClass(className);

        // Optionally, you can add a delay and then hide the message
        setTimeout(function () {
            $(elementId).text('').removeClass('error success');
        }, 5000); // 5000 milliseconds (5 seconds) delay, adjust as needed
    }
});
