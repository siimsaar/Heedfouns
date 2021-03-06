'use strict';

function retryButtons() {
    var bttns = document.getElementsByClassName("btn btn-primary btn-xs");
    for (var i = 0; i < bttns.length; i++) {
        $(bttns[i]).unbind("click", downloadListener);
        bttns[i].addEventListener("click", downloadListener);
    }
}

function downloadListener() {
    var val = $(this).val();
    $.ajax({
        url: './dl',
        type: "POST",
        success: $(this).prop('disabled', 'true').text('Added'),
        data: {alname: val, id_sse: document.cookie.split(";")[0].split("=")[1]}
    });
}

function deleteButtons() {
    var bttns = document.getElementsByClassName("btn btn-danger btn-xs");
    for (var i = 0; i < bttns.length; i++) {
        $(bttns[i]).unbind("click", deleteListener);
        bttns[i].addEventListener("click", deleteListener);
    }
}

function deleteListener() {
    var val = $(this).val();
    $.ajax({
        url: '/status',
        type: "DELETE",
        success: deleteRow(val),
        data: {alname: val}
    });
}

function editButtons() {
    var bttns = document.getElementsByClassName('btn btn-info btn-xs');
    for (var i = 0; i < bttns.length; i++) {
        $(bttns[i]).unbind("click", editListener);
        bttns[i].addEventListener("click", editListener);
    }
}

function editListener() {
    var val = $(this).val();
    if ($(this).text() === "Edit") {
        if (window.editing === true) {
            alert("You are already editing one entry");
            return;
        }
        window.editing = true;
        var oldNameobj = document.getElementById(val);
        window.oldName = $(oldNameobj).val();
        $(oldNameobj).removeAttr('readonly');
        $(this).text('Save');
    } else {
        var newNameobj = document.getElementById(val);
        var newName = $(newNameobj).val();
        if (newName === "") {
            alert("Input field is empty");
            return;
        }
        if (String(newName).indexOf('-') === -1) {
            alert("Entry doesn't match (Artist - Album)");
            return;
        }
        var names = {"oldn": window.oldName, "newn": newName};
        $.ajax({
            url: '/status',
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            type: "PUT",
            success: $(this).text('Edit'),
            data: JSON.stringify(names)
        });
        window.editing = false;
        $(newNameobj).attr('readonly', 'readonly');
    }
}

function updateListener() {
    var ticker = 0;
    var source = new EventSource("/updates?channel=history");
    source.addEventListener('history', function (sse) {
        var data = JSON.parse(sse.data);
        if (data.type === "update") {
            var escaped_data = data.name.replace(/([ #;&,.+*~\':"!^$[\]()=>|\/@])/g, '\\$1');
            var status_u = $("input[value='" + escaped_data + "']").closest('tr').children('td').eq(1);
            if (String(data.status).split(" ")[0] === "Fail:") {
                var status_td = "<td><span class='label label-danger'>Error</span>" + String(data.status).replace('Fail: ', ' ') + "</td>";
            } else {
                var status_td = "<td><span class='label label-success'>Success</span>" + " " + data.status + "</td>";
            }
            $(status_u).html(status_td);
            return
        }
        if (ticker > 0) {
            var last_item = parseInt($("#statustable tr td input:first").attr('id')) + 1;
        } else {
            var last_item = parseInt($("#statustable tr td input:last").attr('id')) + 1;
        }
        if (String(data.status).split(" ")[0] === "Fail:") {
            var status_td = "<td><span class='label label-danger'>Error</span>" + String(data.status).replace('Fail: ', ' ') + "</td>";
            var button_td = '<td class="text-right">'+
                                    '<button type="button" value="' + data.name + '" class="btn btn-danger btn-xs">Remove</button> '+
                                    '<button type="button" value="' + last_item + '" class="btn btn-info btn-xs">Edit</button> '+
                                    '<button type="button" value="' + data.name + '" class="btn btn-primary btn-xs">Retry</button> '+
                            '</td>';
        } else {
            var status_td = "<td><span class='label label-success'>Success</span>" + " " + data.status + "</td> ";
            var button_td = '<td class="text-right">'+
                                '<button type="button" value="' + data.name + '" class="btn btn-danger btn-xs">Remove</button> '+
                                '<button type="button" value="' + last_item + '" class="btn btn-info btn-xs">Edit</button> '+
                             '</td> ';
        }
        var name_td = '<td>'+
                            '<input class="form-control-custom input-sm" name="src_album" id="' + last_item + '" type="text" value="' + data.name + '" readonly="readonly">'+
                        '</td>';
        var comp_td = '<tr id="' + String(data.name).replace(/ /g, '_') + '">' + name_td + status_td + button_td + '</tr>';
        $("#statustable").prepend(comp_td);
        ticker += 1;
        retryButtons();
        editButtons();
        deleteButtons();
        window.initialTableSize += 1;
        $("#search_ex").trigger('keyup');
    });
}

function deleteRow(val) {
    val = String(val).replace(/ /g, '_');
    var row = document.getElementById(val);
    row.parentNode.removeChild(row);
}

window.addEventListener("DOMContentLoaded", function () {
    retryButtons();
    deleteButtons();
    editButtons();
    updateListener();
    search();
    window.initialTableSize = $('#statustable tr').length;
});

function search() {
    $("#search_ex").keyup(function () {
        for (var i = 0; i < window.initialTableSize; i++) {
            try {
                var curRow = $('#' + String(i));
                if ($(curRow).val().toLowerCase().indexOf($(this).val().toLowerCase()) === -1) {
                    $(curRow).closest("tr").hide();
                } else {
                    $(curRow).closest("tr").show();
                }
            } catch (err) {
            }
        }
    });
}
