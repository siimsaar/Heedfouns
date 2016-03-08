function addtoev() {
    var bns = document.getElementsByName("apibttn");
    for (i = 0; i < bns.length; i++) {
        bns[i].addEventListener("click", function () {
            var val = $(this).val();
            $.ajax({
                url: './api',
                type: "POST",
                data: { apiselec: val }
            })
        });
    }
}

window.addEventListener("load",function() {
  addtoev();
});