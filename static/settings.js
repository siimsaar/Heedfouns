'use strict';

window.addEventListener('DOMContentLoaded', function () {
    $("#recalc").click(function () {
        var _this = $(this);
        $(this).text("Generating...");
        $(this).prop('disabled', 'true');
        jQuery.get("/admin/sugg").done(function () {
            $(_this).text("Generate again");
            $(_this).removeAttr('disabled');
        }).fail(function () {
            $(_this).text("Regenerate suggestions for all users");
            $(_this).removeAttr('disabled');
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
        });
    });
});