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
                url: './del',
                type: "POST",
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
                var names = {"oldn": oldName, "newn": newName};
                $.ajax({
                    url: './rename',
                    dataType: "json",
                    contentType: "application/json; charset=utf-8",
                    type: "POST",
                    success: $(this).text('Edit'),
                    data: JSON.stringify(names)
                });
                $(newNameobj).attr('readonly', 'readonly');
            }
        });
    }
}

function deleteRow(val) {
    var row = document.getElementById(val);
    row.parentNode.removeChild(row);
}

window.addEventListener("load",function() {
    retryButtons();
    deleteButtons();
    editButtons();
});