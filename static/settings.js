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
            $(this).text("Regenerate suggestions for all users");
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
            var _this = $(this);
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