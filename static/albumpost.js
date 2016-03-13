function addtoev() {
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

window.addEventListener("load",function() {
  addtoev();
});