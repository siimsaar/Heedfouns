'use strict';

window.addEventListener('load', function () {
    var source = new EventSource("/updates?channel=historynum");
    source.addEventListener('historynum', function (sse) {
        var data = JSON.parse(sse.data);
        $("#hi_num").text(data).show();
    });
});