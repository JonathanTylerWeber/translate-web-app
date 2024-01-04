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

    $('.delete-search').click(function () {
        // Get the search ID from the data attribute
        let searchId = $(this).data('search-id');
        // Send an AJAX request to the server to delete the search
        $.ajax({
            type: 'DELETE',
            url: `/history/${searchId}/delete`,
            success: function () {
                // Remove the deleted search from the DOM
                $(`.delete-search[data-search-id="${searchId}"]`).closest('li').remove();
                console.log('Search deleted successfully.');
            },
            error: function (error) {
                console.error('Error deleting search:', error);
                // Optionally display an error message on the page
            },
        });

    });

    $('.save-search').click(function () {
        const searchId = $(this).data('search-id');
        const saved = $(this).data('saved') === 'fas';

        // Store a reference to 'this' for later use
        const $this = $(this);

        // Send an AJAX request to update save state
        $.ajax({
            type: 'POST',
            url: `/history/${searchId}/save`,
            contentType: 'application/json',
            success: function (response) {
                if (response.error) {
                    console.error('Error:', response.error);
                    // Optionally display an error message on the page
                    return;
                }

                // Toggle the saved state and update the icon
                const newClass = !saved ? 'fas' : 'far';
                $this.data('saved', newClass);
                $this.removeClass('far fas').addClass(newClass);
            },
        });
    });
});
