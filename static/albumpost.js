/* jshint -W097 */
/* jshint -W040 */
'use strict';

function getDlBttns() {
    var bttns = document.getElementsByClassName("btn btn-primary btn-xs");
    for (var i = 0; i < bttns.length; i++) {
        bttns[i].addEventListener("click", dlbttns);
    }
}

function dlbttns() {
    var val = $(this).val();
    $.ajax({
        url: '/dl',
        type: "POST",
        success: $(this).prop('disabled', 'true').text('Added'),
        data: {alname: val, id_sse: document.cookie.split(";")[0].split("=")[1]}
    });
}

function getInfoBttns() {
    var bttns = document.getElementsByClassName("btn btn-info btn-xs");
    for (var i = 0; i < bttns.length; i++) {
        bttns[i].addEventListener("click", moreInfoBttn);
    }
}

function moreInfoBttn() {
    var artist = $(this).val().split("-")[0];
    var album = $(this).val().split("-")[1];
    artist = artist.substring(0, artist.length - 1);
    album = album.substring(1, album.length);
    moreinfo(this, artist, album);
}

function moreinfo(bttn, artist, album) {
    var id = $(bttn).attr('id').split("-")[0];
    var row = document.getElementById(id);
    if ($(bttn).text().split(" ")[0] === "More") {
        $(bttn).text('Less info');
        row.removeAttribute('style');
        if ($(bttn).attr('id').split("-")[2] === "used") {
            return;
        }
        bttn.setAttribute('class', 'btn btn-info btn-xs active');
        var mrinf = $.getJSON("/more_info/" + artist + "/" + album, function (data) {
                var cover = document.getElementById(id + "-cover");
                var release = document.getElementById(id + "-release");
                var tag = document.getElementById(id + "-tags");
                var similar = document.getElementById(id + "-similar");
                var tracks = document.getElementById(id + "-tracks");
                $(release).find('i').remove();
                $(tag).find('i').remove();
                $(similar).find('i').remove();
                cover.setAttribute('src', data.cover);
                $(release).append(data.release);
                for (i = 0; i < data.tags.length; i++) {
                    if (i === data.tags.length - 1) {
                        $(tag).append(data.tags[i]);
                    } else {
                        $(tag).append(data.tags[i] + ", ");
                    }
                }
                for (i = 0; i < data.similar_artists.length; i++) {
                    if (i === 3) {
                        $(similar).append('<br/>');
                    }
                    if (i === data.similar_artists.length - 1) {
                        $(similar).append('<a href="/results/' + data.similar_artists[i] + '">' + data.similar_artists[i] + '</a>');
                    } else {
                        $(similar).append('<a href="/results/' + data.similar_artists[i] + '">' + data.similar_artists[i] + "</a>, ");
                    }
                }
                for (var i = 0; i < data.track_list.length; i++) {
                    $(tracks).append("<tr><td>" + data.track_list[i] + "</td></tr>");
                }
                $(bttn).prop('id', id + "-button-used");
            })
            .fail(function () {
                console.log("error");
            });
    } else {
        $(bttn).text('More info');
        bttn.setAttribute('class', 'btn btn-info btn-xs');
        row.setAttribute('style', 'display: none;');
    }
}

function search() {
    $("#search_ex").keyup(function () {
        for (var i = 0; i < 25; i++) {
            if ($('#' + String(i) + '-min-row td:first').text().toLowerCase().indexOf($(this).val().toLowerCase()) === -1) {
                $('#' + String(i) + '-min-row').hide();
                $('#' + String(i)).hide();
                var button = $('#' + String(i) + '-button-used');
                $(button).text("More info");
                $(button).attr('class', 'btn btn-info btn-xs');
            } else {
                $('#' + String(i) + '-min-row').show();
            }
        }
    });
}


window.addEventListener("DOMContentLoaded", function () {
    getDlBttns();
    getInfoBttns();
    search();
});