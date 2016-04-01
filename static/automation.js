function enableButton() {
    var enable_bttn = document.getElementById("enbttn");
    enable_bttn.addEventListener("click", function () {
        intf = document.getElementById('interval_in');
        if ($(this).text() == "Enable") {
            $(this).text("Disable");
            $(this).attr('class', 'btn btn-danger btn-xs');
            $.ajax({
                url: './auto/conf',
                type: "POST",
                success: console.log("todo"),
                data: {enable_b: 1}
            })
        } else {
            $(this).text("Enable");
            $(this).attr('class', 'btn btn-info btn-xs');
            $.ajax({
                url: './auto/conf',
                type: "POST",
                success: console.log("todo"),
                data: {enable_b: 0}
            })
        }
    })
}

function saveButton() {
    var enable_bttn = document.getElementById("save_bttn");
    enable_bttn.addEventListener("click", function () {
        var field = document.getElementById('inter_field');
        field_value = $(field).val();
        if (field_value.length == 0) {
            return
        }
        $(this).text('Saving');
        $.ajax({
            url: './auto/conf',
            type: "POST",
            success: $(this).text('Saved'),
            data: {interval: field_value}
        });
    })
}

function addButton() {
    var enable_bttn = document.getElementById("add_bttn");
    enable_bttn.addEventListener("click", function () {
        adf = document.getElementById("add_field");
        adf_val = WordtoUpper($(adf).val());
        try {
            elem_id = parseInt($("#tr_art tr:first").attr('id').split("-")[0]) + 1
        } catch (err) {
            elem_id = 0
        }
        if (adf_val.length == 0) {
            return
        }
        table = document.getElementById('tr_art');
        table_elem = $(table).find('td');
        for (i = 0; i < table_elem.length; i++) {
            if ($(table_elem[i]).text() == adf_val) {
                alert("Artist already exists in table");
                return
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
    })
}

function deleteButtons() {
    var bttns = document.getElementsByName('del');
    for (i = 0; i < bttns.length; i++) {
        bttns[i].addEventListener("click", function () {
            $.ajax({
                url: './auto',
                type: "DELETE",
                success: deleteRow($(this).attr('id')),
                data: {tbdeleted: $(this).val()}
            })
        });
    }
}

function deleteRow(id) {
    id = id.split("-")[0] + "-tr";
    var row = document.getElementById(id);
    row.parentNode.removeChild(row);
}

function runAlbumCheck() {
    run_bttn = document.getElementById('album_check');
    run_bttn.addEventListener("click", function () {
        event.preventDefault();
        $.ajax({
            url: './auto/run',
            type: "POST",
            success: $(this).text("RUNNING"),
            data: {run_type: "album_check"}
        })
    });
}

function runTorrentCheck() {
    run_bttn = document.getElementById('torrent_check');
    run_bttn.addEventListener("click", function () {
        event.preventDefault();
        $.ajax({
            url: './auto/run',
            type: "POST",
            success: $(this).text("RUNNING"),
            data: {run_type: "torrent_check"}
        })
    });
}

function setInitialState() {
    $.getJSON("/auto/conf", function (data) {
        var isEnabled = data.a_enabled;
        var interval = data.a_interval;
        int_field = document.getElementById('inter_field');
        $(int_field).attr('value', interval);
        automationBttn = document.getElementById('enbttn');
        if (isEnabled == 1) {
            $(automationBttn).text("Disable");
            $(automationBttn).attr('class', 'btn btn-danger btn-xs');
        } else {
            $(automationBttn).text("Enable");
            $(automationBttn).attr('class', 'btn btn-primary btn-xs');
        }
    });
}

function WordtoUpper(string) {
    return string.substr(0, 1).toUpperCase() + string.substr(1);
}

window.addEventListener("load", function () {
    setInitialState();
    enableButton();
    addButton();
    saveButton();
    deleteButtons();
    runAlbumCheck();
    runTorrentCheck();
});