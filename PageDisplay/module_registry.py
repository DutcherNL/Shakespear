
class AlreadyRegistered(Exception):
    pass


class ModuleRegister:
    """ This class registers the various modules and allows hooking onto those modules
    Similarly to the admin register, this registry registers all modules.
    Unlike the admin register however, this register needs to be aware of all modules possible in order for the system
    to work.
    In a future version the system will be adjusted to incorporate django.content_types so it doesn't have to know
    all kinds of modules any more.


    """

    _modules = {}

    class RegisteredModule:
        def __init__(self, module, selectable_by_default=True):
            self.module = module
            self.selectable_by_default = selectable_by_default

        @property
        def __name__(self):
            return self.module.__name__

    def register(self, module, in_default=True):
        """
        Register a given module class
        :param module: The module class registered. Note that the _type_id should be unique
        """
        if module._type_id in self._modules:
            msg = 'The model type_id %s is already registered ' % module.__name__
            raise AlreadyRegistered(msg)

        # Store the module locally
        self._modules[module._type_id] = ModuleRegister.RegisteredModule(module, selectable_by_default=in_default)

    def get_module_list(self, include=None, exclude=None):
        """
        :return: Returns all registered modules (class)
        """
        if include and exclude:
            raise AssertionError("get_module_list in module registry can not have both an include and exclude list")

        # Set exclude as default list
        exclude = exclude or []

        modules = []
        for key, registered_module in self._modules.items():
            if include:
                if registered_module.__name__ in include:
                    modules.append(registered_module.module)
            elif registered_module.__name__ not in exclude:
                if registered_module.selectable_by_default:
                    modules.append(registered_module.module)

        return modules

    def get_module(self, type_id):
        """ Returns a single module class that can be identified with the given type_id """
        registered_module = self._modules.get(type_id, None)
        if registered_module:
            return registered_module.module
        else:
            return None


# Create the registry instance
registry = ModuleRegister()
