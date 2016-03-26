function getDlBttns() {
    var bttns = document.getElementsByClassName("btn btn-primary btn-xs");
    for (i = 0; i < bttns.length; i++) {
        bttns[i].addEventListener("click", function () {
            var val = $(this).val();
            $.ajax({
                url: '/dl',
                type: "POST",
                success: $(this).prop('disabled', 'true').text('Added'),
                data: {alname: val}
            })
        });
    }
}

function getInfoBttns() {
    var bttns = document.getElementsByClassName("btn btn-info btn-xs");
    for (i = 0; i < bttns.length; i++) {
        bttns[i].addEventListener("click", function () {
            artist = $(this).val().split("-")[0];
            album = $(this).val().split("-")[1];
            artist = artist.substring(0, artist.length - 1);
            album = album.substring(1, album.length);
            moreinfo(this, artist, album);
        });
    }
}

function moreinfo(bttn, artist, album) {
    var id = $(bttn).attr('id').split("-")[0];
    var row = document.getElementById(id);
    if ($(bttn).text().split(" ")[0] == "More") {
        $(bttn).text('Less info');
        row.removeAttribute('style');
        if ($(bttn).attr('id').split("-")[2] == "used") {
            return
        }
        bttn.setAttribute('class', 'btn btn-info btn-xs active');
        var mrinf = $.getJSON("/more_info/" + artist + "/" + album, function (data) {
                var cover = document.getElementById(id + "-cover");
                var release = document.getElementById(id + "-release");
                var tag = document.getElementById(id + "-tags");
                var similar = document.getElementById(id + "-similar");
                var tracks = document.getElementById(id + "-tracks");
                cover.setAttribute('src', data.cover);
                $(release).append(data.release);
                for (i = 0; i < data.tags.length; i++) {
                    if (i == data.tags.length - 1) {
                        $(tag).append(data.tags[i]);
                    } else {
                        $(tag).append(data.tags[i] + ", ");
                    }
                }
                for (i = 0; i < data.similar_artists.length; i++) {
                    if (i == data.similar_artists.length - 1) {
                        $(similar).append('<a href="/results/' + data.similar_artists[i] + '">' + data.similar_artists[i] + '</a>');
                    } else {
                        $(similar).append('<a href="/results/' + data.similar_artists[i] + '">' + data.similar_artists[i] + "</a>, ");
                    }
                }
                for (i = 0; i < data.track_list.length; i++) {
                    $(tracks).append("<tr><td>" + data.track_list[i] + "</td></tr>");
                }
                $(bttn).prop('id', id + "-button-used")
            })
            .fail(function () {
                console.log("error");
            })
    } else {
        $(bttn).text('More info');
        bttn.setAttribute('class', 'btn btn-info btn-xs');
        row.setAttribute('style', 'display: none;');
    }
}

window.addEventListener("load", function () {
    getDlBttns();
    getInfoBttns()
});