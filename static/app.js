$(document).ready(function () {
    // Attach an event listener to the form submission
    $('#translate-form').submit(function (event) {
        // Prevent the default form submission
        event.preventDefault();

        // Get the word and direction from the form
        let word = $('#word').val();
        let direction = $('input[name="direction"]:checked').val();

        console.log('Form data:', { 'word': word, 'direction': direction });

        // Send an AJAX request to the server
        $.ajax({
            type: 'POST',
            url: '/translate',
            contentType: 'application/json',
            data: JSON.stringify({
                'word': word,
                'direction': direction
            }),
            success: function (response) {
                console.log('Raw AJAX Response:', response);

                if (response.error) {
                    console.error('Error:', response.error);
                    // Optionally display an error message on the page
                    return;
                }

                // Update the DOM with the translation and pinyin
                $('#translation').text(response.translation);
                $('#pinyin').text(response.pinyin);

                // Log the AJAX response
                console.log('Processed AJAX Response:', response);
            },
        });
    });
});
