// main.js

$(document).ready(function () {
    // Handle form submission
    $('#chat-form').submit(function (e) {
        e.preventDefault(); // Prevent the default form submission

        // Get user input from the form
        var userInput = $('#user-input').val();
        let csrfToken = $('input[name=csrf_token]').val(); // csrf token extraction

        // Make an AJAX request to server
        $.ajax({
            url: '/user_input/bot',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ user_input: userInput, csrf_token: csrfToken }),
            success: function (response) {
                // Log the entire response to the console for debugging
                console.log(response);
                // Handle the response from the server
                handleResponse(response.user_input, response.response);
            },
            error: function (error) {
                console.error('Error in AJAX request:', error);
            }
        });

        // Clear the input field after submitting
        $('#user-input').val('');
    });

    // Function to handle the response and update the UI
    function handleResponse(userInput, modelResponse) {
        // Create a new chat bubble for the user input
        var newUserInputBubble = '<div class="chat-bubble me">' + userInput + '</div>';

        // Create a new chat bubble for the model response
        var newChatBubble = '<div class="chat-bubble you">' + modelResponse + '</div>';

        // Append the new chat bubbles to the chat body

        $('.chat-body').append(newUserInputBubble);
        $('.chat-body').append(newChatBubble);

        // Optionally, you can scroll the chat body to the bottom to show the latest message
        var chatBody = $('.chat-body');
        chatBody.scrollTop(chatBody[0].scrollHeight);

        // Call the updateChatUI function
        updateChatUI();
    }

    // Function to update the chat UI
    function updateChatUI() {
        // Customize the code below according to your UI structure
        // Create a new chat bubble with the animated SVG for the bot
        var animatedSVGBubble = '<div class="chat-bubble you">' +
            '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" style="margin: auto;display: block;shape-rendering: auto;width: 43px;height: 20px;" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid">' +
            '<circle cx="0" cy="44.1678" r="15" fill="#ffffff">' +
            '<animate attributeName="cy" calcMode="spline" keySplines="0 0.5 0.5 1;0.5 0 1 0.5;0.5 0.5 0.5 0.5" repeatCount="indefinite" values="57.5;42.5;57.5;57.5" keyTimes="0;0.3;0.6;1" dur="1s" begin="-0.6s"></animate>' +
            '</circle> <circle cx="45" cy="43.0965" r="15" fill="#ffffff">' +
            '<animate attributeName="cy" calcMode="spline" keySplines="0 0.5 0.5 1;0.5 0 1 0.5;0.5 0.5 0.5 0.5" repeatCount="indefinite" values="57.5;42.5;57.5;57.5" keyTimes="0;0.3;0.6;1" dur="1s" begin="-0.39999999999999997s"></animate>' +
            '</circle> <circle cx="90" cy="52.0442" r="15" fill="#ffffff">' +
            '<animate attributeName="cy" calcMode="spline" keySplines="0 0.5 0.5 1;0.5 0 1 0.5;0.5 0.5 0.5 0.5" repeatCount="indefinite" values="57.5;42.5;57.5;57.5" keyTimes="0;0.3;0.6;1" dur="1s" begin="-0.19999999999999998s"></animate>' +
            '</circle></svg>' +
            '</div>';

        if(!$('.chat-body').contains(newChatBubble)){
            // Append the new chat bubble with the animated SVG to the chat body
            $('.chat-body').append(animatedSVGBubble);
        }else{
        // Append the new chat bubble with the animated SVG to the chat body
        $('.chat-body').remove(animatedSVGBubble);
        }

        // Optionally, you can scroll the chat body to the bottom to show the latest message
        var chatBody = $('.chat-body');
        chatBody.scrollTop(chatBody[0].scrollHeight);
    }
});
