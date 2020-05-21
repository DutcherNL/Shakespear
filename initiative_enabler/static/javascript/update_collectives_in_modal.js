$('#collectives_modal').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget); // Button that triggered the modal
    var modal = $(this);
    var invites = button.find('.invite_content').html();
    console.log(invites);
    modal.find('#modal-collectives-content').html(invites);
});
