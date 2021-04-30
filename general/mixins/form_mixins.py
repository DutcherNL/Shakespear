from django.contrib import messages


class NoFormDataMixin:
    """ A mixin for forms that contain no field data and thus only need to check for limited direct input
    It allows for retrieval of data suitable with the django messages framework """
    success_message = None

    def get_as_error_message(self):
        """ Returns the validation error as set-up for a message in the django messages framework. The message
        returned is an arbitrary one. However, as validation is done in the same order every time, the resulting
        error herre is deterministic (i.e. returns the same error in similar cricumstances) """
        keys = list(self.errors.keys())
        if len(keys) > 0:
            item = self.errors[keys[0]]
            # Make sure that for some reason an empty error was inserted
            if len(item) > 0:
                error = item[0]
            else:
                # For some reason the error did not have a description
                error = "Een onbekende error heeft plaats gevonden bij verwerken"
        return messages.ERROR, error

    def get_as_success_message(self):
        return messages.SUCCESS, self.success_message

    def save(self, commit=True):
        if hasattr(super(NoFormDataMixin, self), 'save'):
            super(NoFormDataMixin, self).save()
        return self.get_as_success_message()