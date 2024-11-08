// src/static/js/create_job.js

$(document).ready(function() {
    // Initialize Autocomplete for City with custom mapping
    initializeAutocomplete(
        '#city',
        CONFIG.citySuggestionsUrl,
        function(item) {
            console.log("Selected city: " + item.value);
        },
        function(item) {
            // Custom mapping: combine city and country for label and value
            return {
                label: item.city + ', ' + item.country,
                value: item.city + ', ' + item.country
            };
        }
    );

    // Initialize Autocomplete for Certifications (assuming they return strings)
    initializeAutocomplete(
        '.certification-input',
        CONFIG.certificationSuggestionsUrl,
        function(item) {
            console.log("Selected certification: " + item.value);
        }
        // No mapItem function needed if suggestions are simple strings
    );

    // Initialize Autocomplete for Skills (assuming they return strings)
    initializeAutocomplete(
        '.skill-input',
        CONFIG.skillSuggestionsUrl,
        function(item) {
            console.log("Selected skill: " + item.value);
        }
        // No mapItem function needed if suggestions are simple strings
    );

    // Initialize Autocomplete for Occupation (assuming they return strings)
    initializeAutocomplete(
        '.occupation-input',
        CONFIG.occupationSuggestionsUrl,
        function(item) {
            console.log("Selected occupation: " + item.value);
        }
        // No mapItem function needed if suggestions are simple strings
    );

    // Function to add a new certification input
    $('#add-certification').on('click', function(e) {
        e.preventDefault();
        var certificationInput = `
            <div class="dynamic-input-group">
                <input type="text" name="certifications[]" class="certification-input" placeholder="Add a certification" required>
                <button type="button" class="remove-input-button">Remove</button>
            </div>
        `;
        $('#certifications-container').append(certificationInput);
        initializeAutocomplete('.certification-input', CONFIG.certificationSuggestionsUrl, function(item) {
            console.log("Selected certification: " + item.value);
        });
    });

    // Function to add a new skill input
    $('#add-skill').on('click', function(e) {
        e.preventDefault();
        var skillInput = `
            <div class="dynamic-input-group">
                <input type="text" name="skills[]" class="skill-input" placeholder="Add a skill" required>
                <button type="button" class="remove-input-button">Remove</button>
            </div>
        `;
        $('#skills-container').append(skillInput);
        initializeAutocomplete('.skill-input', CONFIG.skillSuggestionsUrl, function(item) {
            console.log("Selected skill: " + item.value);
        });
    });

    // Function to add a new work history entry
    $('#add-work-history').on('click', function(e) {
        e.preventDefault();
        var workHistoryEntry = `
            <div class="dynamic-input-group">
                <input type="text" name="work_history[occupations][]" class="occupation-input" placeholder="Occupation" required>
                <input type="number" name="work_history[durations][]" class="duration-input" placeholder="Duration (months)" min="1" required>
                <button type="button" class="remove-input-button">Remove</button>
            </div>
        `;
        $('#work-history-container').append(workHistoryEntry);
        initializeAutocomplete('.occupation-input', CONFIG.occupationSuggestionsUrl, function(item) {
            console.log("Selected occupation: " + item.value);
        });
    });

    // Function to remove an input field
    $(document).on('click', '.remove-input-button', function() {
        $(this).parent('.dynamic-input-group').remove();
    });

    // Handle form submission to ensure multiple certifications, skills, and work history are captured
    $('#create-job-form').on('submit', function(e) {
        // Prevent default form submission
        e.preventDefault();

        // Gather form data
        var formData = $(this).serializeArray();
        var data = {};
        $.each(formData, function(index, field) {
            if (field.name.includes('work_history')) {
                // Handle nested work_history fields
                var match = field.name.match(/work_history\[(occupations|durations)\]\[\]/);
                if (match) {
                    var key = match[1];
                    if (!data['work_history']) {
                        data['work_history'] = [];
                    }
                    var lastIndex = data['work_history'].length - 1;
                    if (data['work_history'][lastIndex] && !data['work_history'][lastIndex][key]) {
                        data['work_history'][lastIndex][key] = field.value;
                    } else {
                        data['work_history'].push({ [key]: field.value });
                    }
                }
            } else {
                var fieldName = field.name.replace(/\[\]$/, '');
                if (data[fieldName]) {
                    if (Array.isArray(data[fieldName])) {
                        data[fieldName].push(field.value);
                    } else {
                        data[fieldName] = [data[fieldName], field.value];
                    }
                } else {
                    data[fieldName] = field.value;
                }
            }
        });

        // Process work_history to merge occupation and duration
        if (data.work_history) {
            var mergedWorkHistory = [];
            var occupations = [];
            var durations = [];
            // Separate occupations and durations
            $.each(data.work_history, function(index, entry) {
                if (entry.occupations) {
                    occupations.push(entry.occupations);
                }
                if (entry.durations) {
                    durations.push(entry.durations);
                }
            });
            // Merge them
            for (var i = 0; i < occupations.length; i++) {
                mergedWorkHistory.push({
                    occupation: occupations[i],
                    duration: parseInt(durations[i], 10)
                });
            }
            data.work_history = mergedWorkHistory;
        }

        console.log("Form Data to be sent:", data);

        // Submit the form via AJAX
        $.ajax({
            url: CONFIG.createJobUrl,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function(response) {
                if (response.success) {
                    showNotification('Job created successfully!', 'success');
                    // Redirect on success after a short delay
                    setTimeout(function() {
                        window.location.href = CONFIG.viewJobsUrl;
                    }, 2000);
                } else {
                    showNotification(response.message || 'Failed to create job.', 'error');
                }
            },
            error: function(xhr, status, error) {
                console.error("Error creating job:", error);
                showNotification("An error occurred while creating the job. Please try again.", 'error');
            }
        });
    });
});
