// src/static/js/autocomplete.js

function initializeAutocomplete(selector, url, onSelect) {
    $(selector).autocomplete({
        source: function(request, response) {
            $.ajax({
                url: url,
                type: 'GET',
                data: { query: request.term },
                success: function(data) {
                    response($.map(data.suggestions, function(item) {
                        return {
                            label: item.label || item, // Adjust based on your data structure
                            value: item.value || item
                        };
                    }));
                },
                error: function(xhr, status, error) {
                    console.error("Autocomplete request failed:", error);
                    response([]);
                }
            });
        },
        minLength: 2,
        select: function(event, ui) {
            if (onSelect && typeof onSelect === 'function') {
                onSelect(ui.item);
            }
        }
    });
}
