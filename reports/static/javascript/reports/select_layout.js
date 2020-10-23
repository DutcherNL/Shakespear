// This function is used on the Layout overview page of the reports to display the info of the selected Layout
// object in the top of the page. Including a (simplified) preview


$("[name='layout-info-btn']").on('click', function (event) {
    // Set the selected layout as the active element
    $("[name='layout-info-btn']").removeClass('active');
    $(this).addClass('active');

    var metadata = $(this).find('metadata'); // Metadata of the selected layout

    metadata.children().each(function( index ) {
        var new_el_id = "#"+$( this ).attr("name");
        var content_type = $( this ).attr("data-content-type")
        if (content_type == "txt") {
            $(new_el_id).text($(this).text());
        }else if (content_type == "html"){
            $(new_el_id).html($(this).text());
        }else if (content_type == "url"){
            $(new_el_id).attr('href', $(this).text());
        }
    });
});