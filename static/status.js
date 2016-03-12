function retryButtons() {
    var bns = document.getElementsByClassName("btn btn-primary btn-xs");
    for (i = 0; i < bns.length; i++) {
        bns[i].addEventListener("click", function () {
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
    var bns = document.getElementsByClassName("btn btn-danger btn-xs");
    for (i = 0; i < bns.length; i++) {
        bns[i].addEventListener("click", function () {
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

function deleteRow(val) {
    var row = document.getElementById(val);
    row.parentNode.removeChild(row);
}

window.addEventListener("load",function() {
  retryButtons();
    deleteButtons();
});