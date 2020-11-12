from .models import Inquirer


def get_inquiry_from_request(request):
    """ Retrieves the active inquiry from the request data """
    if request:
        try:
            inquirer_id = request.session.get('inquirer_id', None)
            if inquirer_id:
                return Inquirer.objects.get(id=inquirer_id).active_inquiry
        except Inquirer.DoesNotExist:
            pass

    return None