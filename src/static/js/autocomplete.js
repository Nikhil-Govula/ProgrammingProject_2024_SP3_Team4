// src/static/js/autocomplete.js

/**
 * Initializes jQuery UI Autocomplete on the specified selector.
 *
 * @param {string} selector - The jQuery selector for the input element.
 * @param {string} url - The URL to fetch autocomplete suggestions.
 * @param {function} onSelect - Callback function when an item is selected.
 * @param {function} [mapItem] - Optional function to map suggestion items to label and value.
 */
function initializeAutocomplete(selector, url, onSelect, mapItem = null) {
    $(selector).autocomplete({
        source: function(request, response) {
            $.ajax({
                url: url,
                type: 'GET',
                data: { query: request.term },
                success: function(data) {
                    if (mapItem && typeof mapItem === 'function') {
                        // Use the provided mapItem function to transform suggestions
                        response($.map(data.suggestions, mapItem));
                    } else {
                        // Default mapping: assume item has 'label' and 'value' properties
                        response($.map(data.suggestions, function(item) {
                            return {
                                label: item.label || item,
                                value: item.value || item
                            };
                        }));
                    }
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
