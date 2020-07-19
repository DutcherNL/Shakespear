/*
This method plots all charts in the class chart_js_chart on the page.
Data is retrieved through ajax and the objects data-url parameter
*/
$(function () {

    var $chart_canvases = $(".chart_js_chart");

    $chart_canvases.each( function () {
        var canvas_obj = $(this);
        $.ajax({
            url: canvas_obj.data("url"),
            success: function (data) {
                var ctx = canvas_obj[0].getContext("2d");

                new Chart(ctx, {
                    type: data.chart_type,
                    data: data.data,
                    options: data.options,
                });

            }
        });
    });


});