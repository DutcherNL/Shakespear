function copyStringToClipboard(source_el, str) {
    // Create new element
    source_el = $(source_el)

    var successful = document.queryCommandSupported('copy');
    if (successful == true) {

        var el = document.createElement('textarea');
        // Set value (string to be copied)
        el.value = str;
        // Set non-editable to avoid focus and move outside of view
        el.setAttribute('readonly', '');
        el.style = {position: 'absolute', left: '-9999px'};
        document.body.appendChild(el);
        // Select text inside element
        el.select();
        // Copy text to clipboard
        successful = document.execCommand('copy');
        // Remove temporary element
        document.body.removeChild(el);
    }

    var original_tooltip = source_el.attr('data-original-title')
    var post_tooltip = successful ? source_el.attr('success-title') : source_el.attr('failed-title')
    source_el.attr('data-original-title', post_tooltip)

    source_el.tooltip('show')
    // Revert original hover tooltip text (will appear on new display)
    source_el.attr('data-original-title', original_tooltip)
}