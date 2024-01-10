const left = document.getElementById('left-side');

const handleOnMove = e => {
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const p = clientX / window.innerWidth * 100;

    left.style.width = `${p}%`;
}

document.onmousemove = e => handleOnMove(e);
document.ontouchmove = e => handleOnMove(e);

$(document).ready(function () {
    // Initialize the default direction
    let direction = 'en_to_zh';

    // Attach an event listener to the switch icon
    $('#switch-direction').click(function () {
        // Toggle the direction
        direction = direction === 'en_to_zh' ? 'zh_to_en' : 'en_to_zh';

        // Update the placeholder text for the input field
        const placeholder = direction === 'en_to_zh' ? 'Enter English text...' : '输入中文...';
        $('#word').attr('placeholder', placeholder);

        // Update the translation direction on the page
        updateTranslationDirection(direction);
    });

    // Function to update the translation direction on the page
    function updateTranslationDirection(newDirection) {
        // Update the direction in the form data
        $('input[name="direction"]').val(newDirection);

        // Update the source and target language labels
        const sourceLanguage = newDirection === 'en_to_zh' ? 'English' : 'Chinese';
        const targetLanguage = newDirection === 'en_to_zh' ? 'Chinese' : 'English';
        $('#source-language').text(sourceLanguage);
        $('#target-language').text(targetLanguage);

        // Optionally, update other elements on the page based on the direction
    }

    $('#word').on('keydown', function (event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault(); // Prevents adding a new line in the textarea
            $('#translate-form').submit(); // Trigger the form submission
        }
    });

    // Attach an event listener to the form submission
    $('#translate-form').submit(function (event) {
        // Prevent the default form submission
        event.preventDefault();

        // Get the word from the form
        let word = $('#word').val();

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
