/* jshint -W097 */
/* jshint -W040 */
'use strict';

function enableButton() {
    var enable_bttn = document.getElementById("enbttn");
    enable_bttn.addEventListener("click", e_button);
}


function e_button() {
    var intf = document.getElementById('interval_in');
    if ($(this).text() === "Enable") {
        $(this).attr('class', 'btn btn-danger btn-xs');
        $.ajax({
            url: './auto/conf',
            type: "POST",
            success: $(this).text("Disable"),
            data: {enable_b: 1}
        });
    } else {
        $(this).attr('class', 'btn btn-primary btn-xs');
        $.ajax({
            url: './auto/conf',
            type: "POST",
            success: $(this).text("Enable"),
            data: {enable_b: 0}
        });
    }
}

function saveButton() {
    var enable_bttn = document.getElementById("save_bttn");
    enable_bttn.addEventListener("click", function () {
        var field = document.getElementById('inter_field');
        var field_value = $(field).val();
        if (field_value.length === 0) {
            return;
        }
        $(this).text('Saving');
        $.ajax({
            url: './auto/conf',
            type: "POST",
            success: $(this).text('Saved'),
            data: {interval: field_value}
        });
    });
}

function addButton() {
    var enable_bttn = document.getElementById("add_bttn");
    enable_bttn.addEventListener("click", function () {
        var adf = document.getElementById("add_field");
        var adf_val = WordtoUpper($(adf).val());
        try {
            var elem_id = parseInt($("#tr_art tr:first").attr('id').split("-")[0]) + 1;
        } catch (err) {
            var elem_id = 0;
        }
        if (adf_val.length === 0) {
            return;
        }
        var table = document.getElementById('tr_art');
        var table_elem = $(table).find('td');
        for (var i = 0; i < table_elem.length; i++) {
            if ($(table_elem[i]).text() === adf_val) {
                alert("Artist already exists in table");
                return;
            }
        }
        $.ajax({
            url: './auto',
            type: "POST",
            success: $(table).prepend("<tr id='" + elem_id + "-tr'><td>" + adf_val + "" +
                "</td>" +
                "<td class='text-right'><button value='" + adf_val + "' id='" + elem_id + "-td' name='del' class='btn btn-danger btn-xs'>Delete</button>" +
                "</td>" +
                "</tr>"),
            data: {art_name: adf_val}
        });
        deleteButtons();
        $(adf).val("");
    });
}

function deleteButtons() {
    var bttns = document.getElementsByName('del');
    for (var i = 0; i < bttns.length; i++) {
        bttns[i].addEventListener("click", function () {
            var id = $(this).attr('id');
            var val = $(this).attr('value');
            $.ajax({
                url: './auto',
                type: "DELETE",
                success: function () {
                    id = id.split("-")[0] + "-tr";
                    var row = document.getElementById(id);
                    row.parentNode.removeChild(row);
                    var sch_table = document.getElementById('sc_alb');
                    var sch_td = $(sch_table).find('td');
                    for (var i = 0; i < sch_td.length; i++) {
                        if (String($(sch_td[i]).text()).split(" - ")[0].toLowerCase() === val.toLowerCase()) {
                            $(sch_td[i]).parent('tr').remove();
                        }
                    }
                },
                data: {tbdeleted: $(this).val()}
            });
        });
    }
}

function runAlbumCheck() {
    var run_bttn = document.getElementById('album_check');
    run_bttn.addEventListener("click", function () {
        event.preventDefault();
        var this_bttn = $(this);
        if ($(this).text() === "RUNNING") {
            return;
        }
        $(this_bttn).text("RUNNING");
        $.ajax({
            url: './auto/run',
            type: "POST",
            data: {run_type: "album_check"},
            success: function () {
                var date = new Date();
                var date_s = date.toLocaleString('en-GB');
                var run = $.ajax({
                    url: './auto/conf',
                    type: "PUT",
                    success: function () {
                        $("#a_check_date").text(date_s + " - Last check for albums");
                    },
                    data: {a_date: date_s}
                });
                run.fail(function () {
                    $(this_bttn).text("FAIL");
                });
            }
        });
    });
}

function runTorrentCheck() {
    var run_bttn = document.getElementById('torrent_check');
    run_bttn.addEventListener("click", function () {
        event.preventDefault();
        var this_bttn = $(this);
        if ($(this).text() === "RUNNING") {
            return;
        }
        $(this_bttn).text("RUNNING");
        $.ajax({
            url: './auto/run',
            type: "POST",
            data: {run_type: "torrent_check"},
            success: function () {
                var date = new Date();
                var date_s = date.toLocaleString('en-GB');
                var run = $.ajax({
                    url: './auto/conf',
                    type: "PUT",
                    success: function () {
                        $("#t_check_date").text(date_s + " - Last check for torrents")
                    },
                    data: {t_date: date_s}
                });
                run.fail(function () {
                    $(this_bttn).text("FAIL");
                });
            }
        });
    });
}

function updateListener() {
    var source = new EventSource("/updates?channel=sched");
    source.addEventListener('scheduled', function (sse) {
        var data = JSON.parse(sse.data);
        if (data.album === "C_A" || data.date === "C_A") {
            $("#album_check").text("[RUN]");
            return;
        }
        if (data.album === "C_T" || data.date === "C_T") {
            $("#torrent_check").text("[RUN]");
            return;
        }
        $("#sc_alb").prepend("<tr><td>" + data.album + "</td><td class='text-right'>" + data.date + "</td></tr>");
    });
}

function WordtoUpper(string) {
    return string.substr(0, 1).toUpperCase() + string.substr(1);
}

window.addEventListener("load", function () {
    enableButton();
    addButton();
    saveButton();
    deleteButtons();
    runAlbumCheck();
    runTorrentCheck();
    updateListener();
});