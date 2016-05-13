'use strict';

window.addEventListener('DOMContentLoaded', function () {
    var source = new EventSource("/updates?channel=historynum=" + document.cookie.split(";")[0].split("=")[1]);
    source.addEventListener('historynum', function (sse) {
        var data = JSON.parse(sse.data);
        $("#hi_num").text(data.number).show();
    });
    var source2 = new EventSource("/updates?channel=progress");
    source2.addEventListener('progress', function (sse) {
        var data = JSON.parse(sse.data);
        if ($("#progress_bar").length === 0) {
            $("body").append('<div id="progress_bar" class="status_inf">'+
            '<div class="panel panel-info">'+
                '<div class="panel-heading">'+
                    '<h3 class="panel-title"><span class="fa fa-spinner fa-pulse"></span> Searching for albums</h3>'+
                '</div>'+
                '<div class="panel-body">'+
                    '<span id="cur_p">' + data.album + '</span>'+
                        '<span id="cur_q" class="pull-right">' + data.queue_s + '</span>'+
                    '<div class="progress progress-striped active">'+
                        '<div id="cur_per" class="progress-bar" style="width:' + data.percent + '%"></div>'+
                    '</div>'+
                '</div>'+
            '</div>'+
        '</div>');
            $(".status_inf").css('bottom', '-200px');
            $("#progress_bar").animate({bottom: '0'});
        } else {
            if (data.album === undefined || data.album === null) {
                $("#cur_q").text(data.queue_s);
                $("#cur_per").attr('style', 'width: ' + data.percent);
                if (data.queue_s.split(" ")[0] === "0") {
                    $("#cur_p").text("Search complete, closing...");
                    window.timeout_w = setTimeout(function () {
                        $("#progress_bar").animate({bottom: '-200px'}, function () {
                            $("#progress_bar").remove();
                        });
                    }, 3000);
                }
            } else {
                clearTimeout(window.timeout_w);
                $("#cur_p").text(data.album);
                $("#cur_q").text(data.queue_s);
                $("#cur_per").attr('style', 'width: ' + data.percent);
            }
        }
    });
});
