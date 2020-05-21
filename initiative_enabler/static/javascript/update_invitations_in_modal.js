$('#invitation_modal').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget) // Button that triggered the modal
    var num_invites = button.data('num_invites') // Extract info from data-* attributes

    // If necessary, you could initiate an AJAX request here (and then do the updating in a callback).
    // Update the modal's content. We'll use jQuery here, but you could use a data binding library or other methods instead.
    var modal = $(this)
    modal.find('#modal-invite-count').text(num_invites)

    var invites = button.find('.invite_content').html()
    console.log(invites)
    modal.find('#modal-invite-list').html(invites)

})
