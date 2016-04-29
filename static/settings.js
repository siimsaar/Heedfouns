'use strict';

window.addEventListener('DOMContentLoaded', function () {
    $("#recalc").click(function () {
        $(this).text("Generating...");
        $(this).prop('disabled', 'true');
        jQuery.get("/admin/sugg").done(function () {
            $(this).text("Generate again");
            $(this).prop('disabled', 'false')
        }).fail(function () {
            $(this).text("Generate suggestions");
            $(this).prop('disabled', 'false');
            $("#adminmodal").modal('show');
        });
    });
    $("#s_serv").click(function () {
        jQuery.get("/admin/shutdown").done(function () {

        }).fail(function () {
            $("#adminmodal").modal('show');
        });
    });
    $("#d_reg").click(function () {
        jQuery.get("/admin/reg").done(function () {
            var _this = $("#d_reg");
            if ($(_this).text() === "Disable registration") {
                $(_this).text("Enable registration");
            } else {
                $(_this).text("Disable registration");
            }
        }).fail(function () {
            $("#adminmodal").modal('show');
        })
    })
});