function addtoev() {
    var bns = document.getElementsByName("apibttn");
    for (i = 0; i < bns.length; i++) {
        bns[i].addEventListener("click", function () {
            var val = $(this).val();
            $.ajax({
                url: './api',
                type: "POST",
                success: setActive(this),
                data: { apiselec: val }
            })
        });
    }
}

window.addEventListener("load",function() {
  addtoev();
                $.ajax({
                url: './api',
                type: "POST",
                data: { apiselec: "getactive" },
               success: function(data) {
                   initial(data)
               }
            })
});

function setActive(button) {
    if (button.value == "discogs") {
        otherbutton = document.getElementById("lastfm");
        otherbutton.setAttribute('class', 'btn btn-primary');
    } else {
        otherbutton = document.getElementById("discogs");
        otherbutton.setAttribute('class', 'btn btn-primary');
    }
    button.setAttribute('class', 'btn btn-primary active')

}

function initial(id) {
    if (id == "discogs") {
        otherbutton = document.getElementById("lastfm");
        otherbutton.setAttribute('class', 'btn btn-primary');
    } else {
        otherbutton = document.getElementById("discogs");
        otherbutton.setAttribute('class', 'btn btn-primary');
    }
    document.getElementById(id).setAttribute('class', 'btn btn-primary active')

}