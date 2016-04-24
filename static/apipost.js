/* jshint -W097 */
/* jshint -W040 */
'use strict';

function getApiBttns() {
    var bttns = document.getElementsByName("apibttn");
    for (var i = 0; i < bttns.length; i++) {
        bttns[i].addEventListener("click", function () {
            var val = $(this).val();
            $.ajax({
                url: './api',
                type: "POST",
                success: setActive(this),
                data: {apiselec: val}
            });
        });
    }
}

window.addEventListener("load", function () {
    getApiBttns();
    noEmptySearch();
    $.ajax({
        url: './api',
        type: "POST",
        data: {apiselec: "getactive"},
        success: function (data) {
            initial(data);
        }
    });
});

function setActive(button) {
    if (button.value === "discogs") {
        var otherbutton = document.getElementById("lastfm");
        otherbutton.setAttribute('class', 'btn btn-primary');
    } else {
        var otherbutton = document.getElementById("discogs");
        otherbutton.setAttribute('class', 'btn btn-primary');
    }
    button.setAttribute('class', 'btn btn-primary active');

}

function initial(id) {
    if (id === "discogs") {
        var otherbutton = document.getElementById("lastfm");
        otherbutton.setAttribute('class', 'btn btn-primary');
    } else {
        var otherbutton = document.getElementById("discogs");
        otherbutton.setAttribute('class', 'btn btn-primary');
    }
    document.getElementById(id).setAttribute('class', 'btn btn-primary active');
}

function noEmptySearch() {
    $('#index_search').submit(function (e) {
        if ($("#src_box").val() === "") {
            e.preventDefault();
            $('#nav_bar').after('<div class="container"><div class="row"><div class="alert alert-warning"><button type="button" class="close" data-dismiss="alert">&times;</button>Empty search, enter an artist!</div></div></div>')
        }
    });
}