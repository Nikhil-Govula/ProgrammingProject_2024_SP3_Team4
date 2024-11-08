// src/static/js/view_jobs.js

$(document).ready(function() {
    let selectedJobId = null;

    // Initialize DataTables with responsive option
    var table = $('#jobsTable').DataTable({
        "paging": true,
        "searching": true,
        "info": false,
        "lengthChange": false,
        "pageLength": 10,
        "autoWidth": true,
        "responsive": true,
        "columns": [
            { "width": "20%", "responsivePriority": 1 },
            { "width": "40%", "responsivePriority": 2 },
            { "width": "10%", "responsivePriority": 3 },
            { "width": "10%", "responsivePriority": 4 },
            { "width": "10%", "responsivePriority": 5 },
            { "width": "10%", "responsivePriority": 6 }
        ]
    });

    $(window).on('resize', function () {
        table.columns.adjust().draw();
    });

    // Handle row selection
    $('#jobsTable tbody').on('click', 'tr', function () {
        if ($(this).hasClass('selected')) {
            $(this).removeClass('selected');
            selectedJobId = null;
            $('#editSelectedJob').addClass('btn-edit-disabled').prop('disabled', true);
            $('#viewApplications').addClass('btn-edit-disabled').prop('disabled', true);
        } else {
            table.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
            selectedJobId = $(this).data('job-id');
            $('#editSelectedJob').removeClass('btn-edit-disabled').prop('disabled', false);
            $('#viewApplications').removeClass('btn-edit-disabled').prop('disabled', false);
        }
    });

    // Handle edit button click
    $('#editSelectedJob').click(function() {
        if (selectedJobId) {
            window.location.href = `/employer/jobs/edit/${selectedJobId}`;
        }
    });

    // Handle view applications button click
    $('#viewApplications').click(function() {
        if (selectedJobId) {
            window.location.href = `/employer/jobs/${selectedJobId}/applications`;
        }
    });

    // Flash Message Fade Out
    window.onload = function() {
        var notifications = document.querySelectorAll('.notification');
        notifications.forEach(function(notification) {
            setTimeout(function() {
                notification.classList.add('fade-out');
            }, 3000); // 3 seconds
        });
    };
});