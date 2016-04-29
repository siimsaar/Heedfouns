'use strict';

window.addEventListener('DOMContentLoaded', function () {
$("#s_serv").click(function () {
    jQuery.get("/admin/shutdown").done(function () {

    }).fail(function () {
        $("#adminmodal").modal('show');
    });
});
$("#d_reg").click(function () {
  jQuery.get("/admin/reg").done(function () {
      var _this = $("#d_reg");
          if($(_this).text() === "Disable registration") {
        $(_this).text("Enable registration");
    } else {
        $(_this).text("Disable registration");
    }
  }).fail(function () {
      $("#adminmodal").modal('show');
  })
})
});