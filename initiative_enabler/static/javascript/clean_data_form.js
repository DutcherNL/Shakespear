function copy_form_input(form) {
    // Copies all data in the inputs in this form to similarly named input in other forms in accordance with
    // django form prefix layouts

    $('#'+form.id+' input').each(function() {
        var self = $( this )
        var name = self.attr("name").split('-')[1];
        $("[name$='"+name+"']").val(self.val())
    });
}