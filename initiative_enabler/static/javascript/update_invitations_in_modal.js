$('#invitation_modal').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget); // Button that triggered the modal
    var modal = $(this);

    modal.find('#modal-invite-count').text(button.data('num_invites'));
    var invites = button.find('.invite_content').html();
    modal.find('#modal-invite-list').html(invites);
});
