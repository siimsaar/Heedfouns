function retryButtons() {
    var bttns = document.getElementsByClassName("btn btn-primary btn-xs");
    for (i = 0; i < bttns.length; i++) {
        bttns[i].addEventListener("click", function () {
            var val = $(this).val();
            $.ajax({
                url: './dl',
                type: "POST",
                success: $(this).prop('disabled', 'true').text('Added'),
                data: { alname: val }
            })
        });
    }
}

function deleteButtons() {
    var bttns = document.getElementsByClassName("btn btn-danger btn-xs");
    for (i = 0; i < bttns.length; i++) {
        bttns[i].addEventListener("click", function () {
            var val = $(this).val();
            $.ajax({
                url: '/status',
                type: "DELETE",
                success: deleteRow(val),
                data: { alname: val }
            })
        });
    }
}

function editButtons() {
    var bttns = document.getElementsByClassName('btn btn-info btn-xs');
    for (i = 0; i < bttns.length; i++) {
        bttns[i].addEventListener("click", function () {
            var val = $(this).val();
            if ($(this).text() == "Edit") {
                oldNameobj = document.getElementById(val);
                oldName = $(oldNameobj).val();
                $(oldNameobj).removeAttr('readonly');
                $(this).text('Save');
            } else {
                newNameobj = document.getElementById(val);
                newName = $(newNameobj).val();
                if(newName == "") {
                    alert("Input field is empty");
                    return
                }
                if(String(newName).indexOf('-') == -1) {
                    alert("Entry doesn't match (Artist - Album)");
                    return
                }
                var names = {"oldn": oldName, "newn": newName};
                $.ajax({
                    url: '/status',
                    dataType: "json",
                    contentType: "application/json; charset=utf-8",
                    type: "PUT",
                    success: $(this).text('Edit'),
                    data: JSON.stringify(names)
                });
                $(newNameobj).attr('readonly', 'readonly');
            }
        });
    }
}

function updateListener() {
    var ticker = 0;
    var source = new EventSource("/updates?channel=history");
    source.addEventListener('history', function (sse) {
        var data = JSON.parse(sse.data);
        if (ticker > 0) {
            last_item = parseInt($("#statustable tr td input:first").attr('id')) + 1;
        } else {
            last_item = parseInt($("#statustable tr td input:last").attr('id')) + 1;
        }
        if (String(data.status).split(" ")[0] == "Fail:") {
            status_td = "<td><span class='label label-danger'>Error</span>" + String(data.status).replace('Fail: ', ' ') + "</td>";
            button_td = '<td class="text-right"><button type="button" value="' + data.name + '" class="btn btn-danger btn-xs">Remove</button> <button type="button" value="' + last_item + '" class="btn btn-info btn-xs">Edit</button> <button type="button" value="' + data.name + '" class="btn btn-primary btn-xs">Retry</button></td> ';
        } else {
            status_td = "<td><span class='label label-success'>Success</span>" + " " + data.status + "</td>";
            button_td = '<td class="text-right"><button type="button" value="' + data.name + '" class="btn btn-danger btn-xs">Remove</button> <button type="button" value="' + last_item + '" class="btn btn-info btn-xs">Edit</button></td> ';
        }
        name_td = '<td><input class="form-control-custom input-sm" name="src_album" id="' + last_item + '" type="text" value="' + data.name + '" readonly="readonly"></td>';
        comp_td = '<tr id="' + String(data.name).replace(/ /g, '_') + '">'
            + name_td
            + status_td
            + button_td
            + '</tr>';
        $("#statustable").prepend(comp_td);
        ticker += 1;
        retryButtons();
        editButtons();
        deleteButtons();
    });
}

function deleteRow(val) {
    val = String(val).replace(/ /g, '_');
    var row = document.getElementById(val);
    row.parentNode.removeChild(row);
}

window.addEventListener("load",function() {
    retryButtons();
    deleteButtons();
    editButtons();
    updateListener();
});