'use strict';

function noEmptySearch() {
    $('#index_search').submit(function (e) {
        if ($("#src_box").val() === "") {
            e.preventDefault();
            $('#nav_bar').after('<div class="container"><div class="row"><div class="alert alert-warning"><button type="button" class="close" data-dismiss="alert">&times;</button>Empty search, enter an artist!</div></div></div>');
        }
    });
}

window.addEventListener("DOMContentLoaded", function () {
    $('#discogs').click(function () {
        $.ajax({
            url: './api',
            type: "POST",
            success: function () {
                $("#lastfm").attr('class', 'btn btn-primary');
                $("#discogs").attr('class', 'btn btn-primary active');
            },
            data: {setactive: "discogs"}
        });
    });
    $('#lastfm').click(function () {
        $.ajax({
            url: './api',
            type: "POST",
            success: function () {
                $("#discogs").attr('class', 'btn btn-primary');
                $("#lastfm").attr('class', 'btn btn-primary active');
            },
            data: {setactive: "lastfm"}
        });
    });
    noEmptySearch();
});