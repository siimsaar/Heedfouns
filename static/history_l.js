'use strict';

window.addEventListener('load', function () {
    var source = new EventSource("/updates?channel=historynum=" + document.cookie.split(";")[0].split("=")[1]);
    source.addEventListener('historynum', function (sse) {
        var data = JSON.parse(sse.data);
            $("#hi_num").text(data.number).show();
    });
});