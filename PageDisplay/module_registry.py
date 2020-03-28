
class AlreadyRegistered(Exception):
    pass


class ModuleRegister:
    """ This class registers the various modules and allows hooking onto those modules """

    _modules = {}

    def register(self, module):
        """
        Register a given module class
        :param module: The module class registered. Note that the _type_id should be unique
        """
        if module._type_id in self._modules:
            msg = 'The model type_id %s is already registered ' % module.__name__
            raise AlreadyRegistered(msg)

        # Store the module locally
        self._modules[module._type_id] = module

    def get_module_list(self, include=None, exclude=None):
        """
        :return: Returns all registered modules (class)
        """
        if include and exclude:
            raise AssertionError("get_module_list in module registry can not have both an include and exclude list")

        # Set exclude as default list
        exclude = exclude or []

        modules = []
        for key, module in self._modules.items():
            if include:
                if module.__name__ in include:
                    modules.append(module)
            elif module.__name__ not in exclude:
                modules.append(module)

        return modules

    def get_module(self, type_id):
        """ Returns a single module class that can be identified with the given type_id """
        return self._modules.get(type_id, None)


# Create the registry instance
registry = ModuleRegister()
