

function preview_layout() {
    // Updates the preview with values in the form
    // Currently only layout
    $("#layout_container").html($("#id_contents").val());

    $("#content_container").css('padding', $("#id_margins").val());
}


function reset_layout() {
    document.getElementById("layout_form").reset();
    preview_layout()
}